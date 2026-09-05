from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
import zipfile
from pathlib import Path

from . import __version__, prompts
from .config import PRESETS, load_config, save_config
from .contracts import validate_plan, validate_brief
from .core import PosterError, atomic_write, digest, fingerprint, identifier, object_result, read_json, require, within, write_json
from .engine import Engine, verify_delivery
from .provider import Gateway
from .store import Store, create_job, exclusive, process_running


def show(value):
    print(json.dumps(value,ensure_ascii=False,indent=2))


def setup(args):
    image_url = args.base_url or PRESETS.get(args.provider)
    require(bool(image_url), "Custom provider requires --base-url")
    vision_url = args.vision_base_url or PRESETS.get(args.vision_provider) or image_url
    split = args.vision_provider is not None or args.vision_base_url is not None
    if args.from_env:
        image_key = os.environ.get("PP_IMAGE_KEY", "")
        vision_key = os.environ.get("PP_VISION_KEY", "") if split else image_key
    else:
        require(sys.stdin.isatty(), "Configure in a private terminal, or use explicit PP_IMAGE_KEY/PP_VISION_KEY with --from-env")
        image_key = getpass.getpass("Image provider API key (hidden): ")
        vision_key = getpass.getpass("Vision provider API key (hidden): ") if split else image_key
    require(bool(image_key.strip()) and bool(vision_key.strip()), "Empty key")
    save_config(args.root,
        {"base_url":image_url,"model":args.image_model,"key_ref":"image"},
        {"base_url":vision_url,"model":args.vision_model,"key_ref":"vision"},
        {"image":image_key,"vision":vision_key},args.allow_fake_dns)
    show({"configured":True,"network_verified":False,"path":".local/config.json"})


def doctor(args):
    from PIL import __version__ as pillow_version
    info = {"version":__version__,"python":sys.version.split()[0],"pillow":pillow_version,
            "local_runtime":"READY", "provider_declared":False,"provider_verified":False,
            "host_compatibility":"Requires file read/write, command execution, private secret entry and image viewing"}
    try:
        config = load_config(args.root)
        info["provider_declared"] = True
        info["roles"] = {r:{"model":config[r]["model"],"configured":True} for r in ("image","vision")}
        if args.probe:
            info["probe"] = Gateway(config).probe()
    except PosterError as exc:
        info["configuration_issue"] = str(exc)
        if args.probe:
            info["probe_failed"] = True
    show(info)
    return 2 if not info["provider_declared"] or info.get("probe_failed") else 0


def recover(args):
    require(args.acknowledge, "Recovery requires --acknowledge after verifying old process stopped")
    lock = args.job / ".running.lock"
    if lock.exists():
        try:
            pid = int(lock.read_text())
            running=process_running(pid)
        except (ValueError, OSError):
            raise PosterError("Cannot establish old process is stopped; inspect the lock manually") from None
        else:
            require(not running,"Recorded worker process is still alive; do not unlock it")
            lock.unlink()
    with exclusive(args.job), Store(args.job) as s:
        s.snapshot()
        s.db.execute("UPDATE attempts SET status='UNKNOWN',error='PROCESS_INTERRUPTED' WHERE status='IN_FLIGHT'")
        s.db.commit()
        if args.resolve:
            require(bool(args.reason), "Resolution requires a non-secret reason from provider inspection")
            row = s.db.execute("SELECT status FROM attempts WHERE id=?",(args.resolve,)).fetchone()
            require(row is not None and row[0] == "UNKNOWN", "Attempt is not unresolved")
            s.db.execute("UPDATE attempts SET status='RESOLVED_RETRY_ALLOWED',error=? WHERE id=?",
                         (args.reason,args.resolve))
            s.db.commit()
        unknown = s.db.execute("SELECT 1 FROM attempts WHERE status='UNKNOWN'").fetchone()
        s.set("control","")
        s.set("status","UNKNOWN_PROVIDER_OUTCOME" if unknown else "READY_TO_RESUME")
        show(s.status())


def review(args):
    with exclusive(args.job), Store(args.job) as s:
        require(s.get("status") in {"AWAITING_REVIEW","COMPLETED"}, "Only fully QC-passed live work can be accepted")
        delivery = verify_delivery(s)
        require(delivery["provenance"] == "live", "Test evidence cannot be accepted as live work")
        require(args.accept and bool(args.reviewer), "Visually inspect files, then provide --accept --reviewer")
        snapshot = s.snapshot()
        if any(d["visual_review_required"] for d in snapshot["documents"]):
            require(args.sources_reviewed, "Office/PDF text extraction needs separate page/image review; use --sources-reviewed only after doing it")
        write_json(args.job / "human-review.json", {"reviewer":args.reviewer,"accepted":True,"time":time.time(),
                   "delivery_sha256":s.get("delivery_hash"),"sources_reviewed":args.sources_reviewed})
        s.set("status","COMPLETED")
        show({"status":"COMPLETED","stable_production_verified":False})


def export(args):
    with exclusive(args.job), Store(args.job) as s:
        require(s.get("status") == "COMPLETED", "Final export requires QC and visual acceptance")
        delivery = verify_delivery(s)
        review_record = read_json(args.job / "human-review.json")
        require(review_record["delivery_sha256"] == s.get("delivery_hash"), "Review is stale")
        require(not args.output.exists(), "Export destination exists; choose a new file")
        snapshot = s.snapshot()
        paths = {"delivery.json","input.json","human-review.json"}
        for item in delivery["items"]:
            paths.update(item[x] for x in ("image","base","layers","qc"))
        # Font files are not redistributed without a separate license decision.
        paths.update(x for x in snapshot["asset_hashes"] if x != snapshot["brief"]["font"])
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(args.output,"x",zipfile.ZIP_DEFLATED) as z:
            for relative in sorted(paths):
                z.write(within(args.job,relative), relative)
            z.writestr("FONT-NOTICE.txt","Font file omitted. Reinstall the original licensed font; its hash and project reference are preserved.\n")
        show({"export":str(args.output.resolve()),"sha256":digest(args.output.read_bytes())})


def adopt_plan(args):
    plan = read_json(args.plan)
    with exclusive(args.job), Store(args.job) as s:
        b = s.snapshot()["brief"]
        require(0 <= args.canvas < len(b["canvases"]), "Invalid canvas index")
        validate_plan(plan,b)
        relative = f"plans/{args.canvas}-{fingerprint(plan)}.json"
        write_json(args.job / relative,plan)
        s.set(f"adopted_plan_{args.canvas}",json.dumps([relative,digest((args.job/relative).read_bytes())]))
        s.set("status","PLAN_REVISED")
        s.set("delivery_hash","")
        show({"plan_adopted":relative,"final_review_invalidated":True})


def learn_style(args):
    require(args.execute, "Style analysis uses a model; add --execute to authorize this call")
    identifier(args.id)
    source = args.source.read_text(encoding="utf-8")
    require(0 < len(source) <= 24000, "Style source must be 1-24000 characters")
    folder = args.root / ".local" / "styles" / args.id
    require(not folder.exists(), "Style ID exists; choose a new immutable version ID")
    folder.mkdir(parents=True,mode=0o700)
    atomic_write(folder/"source.txt",source.encode())
    write_json(folder/"attempt.json",{"status":"IN_FLIGHT","source_sha256":digest(source.encode())})
    try:
        result, meta = Gateway(load_config(args.root)).vision(prompts.learn(source),[])
    except PosterError:
        write_json(folder/"attempt.json",{"status":"FAILED_OR_UNKNOWN","source_sha256":digest(source.encode()),
                   "action":"Inspect provider outcome before creating another paid attempt"})
        raise
    object_result(result,{"name":str,"rules":list,"source_case_tokens":list,"domains":list,"limits":list,"evidence":str})
    for key in ("rules","source_case_tokens","domains","limits"):
        require(all(isinstance(x,str) for x in result[key]),"Style lists must contain strings")
    result.update({"id":args.id,"version":"0.1.0","status":"draft","source_sha256":digest(source.encode()),"meta":meta})
    write_json(folder/"style.json",result)
    write_json(folder/"attempt.json",{"status":"DONE","provenance":"live","meta":meta})
    show({"style":str(folder/"style.json"),"status":"draft","image_validation":False})


def attach_style(args):
    style = read_json(args.style)
    object_result(style,{"id":str,"version":str,"rules":list,"source_case_tokens":list,"domains":list})
    require(all(isinstance(x,str) for k in ("rules","source_case_tokens","domains") for x in style[k]), "Invalid style rules")
    with exclusive(args.job), Store(args.job) as s:
        require(s.calls() == 0,"Attach style before running; create a new project for later style changes")
        snapshot=s.snapshot()
        require(snapshot["brief"]["kind"] in style["domains"],"Style not designed for this domain")
        # No shared statuses inherited from another computer; all imports remain experimental.
        style["status"]="draft"
        snapshot["style"]=style
        write_json(args.job/"input.json",snapshot)
        s.set("input_hash",fingerprint(snapshot))
        show({"style_attached":style["id"],"requires_experimental_flag":True})


def revise_copy(args):
    require(args.keep_design,"Use --keep-design only when the current concept/background remains appropriate")
    with exclusive(args.job), Store(args.job) as s:
        snapshot=s.snapshot()
        before=fingerprint(snapshot)
        updated=read_json(args.copy)
        require(isinstance(updated,list),"Copy file must be a list")
        old=snapshot["brief"]["copy"]
        require([(x.get("id"),x.get("role")) for x in updated] == [(x["id"],x["role"]) for x in old],
                "Text-only revision must retain IDs and roles; create a new project for structural changes")
        snapshot["brief"]["copy"]=updated
        snapshot["brief"]["facts"]=read_json(args.facts)
        validate_brief(snapshot["brief"])
        a=s.db.execute("SELECT * FROM checkpoints WHERE step='analysis'").fetchone()
        require(a is not None,"Text revision needs an existing analyzed design")
        require(digest(within(args.job,a["output"]).read_bytes())==a["output_hash"],"Prior analysis corrupted")
        plans=[]
        for i in range(len(snapshot["brief"]["canvases"])):
            adopted=s.get(f"adopted_plan_{i}")
            if adopted:
                relative,expected=json.loads(adopted)
            else:
                p=s.db.execute("SELECT * FROM checkpoints WHERE step=?",(f"plan_{i}",)).fetchone()
                require(p is not None,"All layouts must exist before text revision")
                relative,expected=p["output"],p["output_hash"]
            require(digest(within(args.job,relative).read_bytes())==expected,"Prior plan corrupted")
            plans.append([relative,expected])
        write_json(args.job/"revisions"/(before+".input.json"),read_json(args.job/"input.json"))
        if (args.job/"delivery.json").exists():
            write_json(args.job/"revisions"/(before+".delivery.json"),read_json(args.job/"delivery.json"))
        snapshot["previous_input_hash"]=before
        write_json(args.job/"input.json",snapshot)
        s.set("input_hash",fingerprint(snapshot))
        s.set("analysis_override",json.dumps([a["output"],a["output_hash"]]))
        for i,entry in enumerate(plans): s.set(f"adopted_plan_{i}",json.dumps(entry))
        s.set("delivery_hash",""); s.set("status","COPY_REVISED")
        show({"copy_revised":True,"old_input_hash":before,"images_reused_if_dependencies_unchanged":True,
              "final_qc_and_review_required":True})


def parser():
    p=argparse.ArgumentParser(prog="poster",description="PP Poster Agent: explicit inputs, recoverable calls, evidence-gated export")
    p.add_argument("--version",action="version",version=__version__)
    p.add_argument("--root",type=Path,default=Path.cwd(),help="Clone-local configuration root; never auto-read other agents' config")
    sub=p.add_subparsers(dest="command",required=True)
    c=sub.add_parser("configure")
    c.add_argument("--provider",choices=[*PRESETS,"custom"],default="yunwu")
    c.add_argument("--base-url")
    c.add_argument("--image-model",default="gpt-image-2")
    c.add_argument("--vision-model",required=True)
    c.add_argument("--vision-provider",choices=list(PRESETS))
    c.add_argument("--vision-base-url")
    c.add_argument("--from-env",action="store_true")
    c.add_argument("--allow-fake-dns",action="store_true",help="Allow proxy 198.18.0.0/15 only for configured provider domains; TLS checks remain")
    c=sub.add_parser("doctor"); c.add_argument("--probe",action="store_true")
    c=sub.add_parser("init"); c.add_argument("--brief",type=Path,required=True); c.add_argument("--workspace",type=Path,default=Path("projects"))
    for name in ("plan","run"):
        c=sub.add_parser(name); c.add_argument("job",type=Path); c.add_argument("--execute",action="store_true")
        c.add_argument("--max-calls",type=int,required=True,help="Absolute total billable request limit, not a price estimate")
        c.add_argument("--experimental-style",action="store_true")
    for name in ("status","pause","cancel"):
        c=sub.add_parser(name); c.add_argument("job",type=Path)
    c=sub.add_parser("recover"); c.add_argument("job",type=Path); c.add_argument("--acknowledge",action="store_true")
    c.add_argument("--resolve"); c.add_argument("--reason")
    c=sub.add_parser("review"); c.add_argument("job",type=Path); c.add_argument("--accept",action="store_true")
    c.add_argument("--reviewer"); c.add_argument("--sources-reviewed",action="store_true")
    c=sub.add_parser("export"); c.add_argument("job",type=Path); c.add_argument("--output",type=Path,required=True)
    c=sub.add_parser("adopt-plan"); c.add_argument("job",type=Path); c.add_argument("--canvas",type=int,required=True); c.add_argument("--plan",type=Path,required=True)
    c=sub.add_parser("repair"); c.add_argument("job",type=Path); c.add_argument("--step",required=True); c.add_argument("--feedback",type=Path,required=True)
    c=sub.add_parser("learn-style"); c.add_argument("--source",type=Path,required=True); c.add_argument("--id",required=True); c.add_argument("--execute",action="store_true")
    c=sub.add_parser("attach-style"); c.add_argument("job",type=Path); c.add_argument("--style",type=Path,required=True)
    c=sub.add_parser("revise-copy"); c.add_argument("job",type=Path); c.add_argument("--copy",type=Path,required=True)
    c.add_argument("--facts",type=Path,required=True); c.add_argument("--keep-design",action="store_true")
    return p


def dispatch(a):
    a.root=a.root.resolve()
    if hasattr(a,"job"):
        require(a.job.is_dir() and not a.job.is_symlink(),"Job directory missing or symlink")
        a.job=a.job.resolve()
    if a.command=="configure": setup(a)
    elif a.command=="doctor": return doctor(a)
    elif a.command=="init": show({"job":str(create_job(a.brief.resolve(),a.workspace.resolve())),"status":"DRAFT"})
    elif a.command in {"run","plan"}:
        require(a.execute,"This command calls paid APIs; add --execute within the user's authorization")
        show(Engine(a.job,Gateway(load_config(a.root)),a.max_calls).run(a.command=="plan",a.experimental_style))
    elif a.command=="status":
        with Store(a.job) as s: show(s.status())
    elif a.command in {"pause","cancel"}:
        with Store(a.job) as s:
            s.set("control","PAUSED" if a.command=="pause" else "CANCELLED")
            show({"requested":s.get("control"),"effective":"Before next step; current provider call may finish and charge"})
    elif a.command=="recover": recover(a)
    elif a.command=="review": review(a)
    elif a.command=="export": export(a)
    elif a.command=="adopt-plan": adopt_plan(a)
    elif a.command=="learn-style": learn_style(a)
    elif a.command=="attach-style": attach_style(a)
    elif a.command=="revise-copy": revise_copy(a)
    elif a.command=="repair":
        with exclusive(a.job), Store(a.job) as s:
            b=s.snapshot()["brief"]
            allowed={"subject","subject_qc"}|{f"{stage}_{i}" for stage in ("base","base_qc","final_qc") for i in range(len(b["canvases"]))}
            require(a.step in allowed,"Repair subject/base_N or recheck subject_qc/base_qc_N/final_qc_N; use adopt-plan for layout")
            feedback=a.feedback.read_text(encoding="utf-8")
            require(0<len(feedback)<=2000,"Feedback must be 1-2000 characters")
            s.set("repair_"+a.step,"\n定向修复要求（不得突破主体/事实规则）："+feedback)
            s.set("status","REPAIR_PLANNED"); s.set("delivery_hash","")
            show({"repair_planned":a.step,"requires_run":True})
    return 0


def main():
    try:
        code=dispatch(parser().parse_args())
    except PosterError as exc:
        show({"error":str(exc),"status":"NOT_COMPLETED"}); code=2
    except KeyboardInterrupt:
        show({"error":"Interrupted; inspect status and recover before retrying","status":"NOT_COMPLETED"}); code=130
    except Exception:
        show({"error":"LOCAL_FAILURE: no success claimed; inspect project state. Provider bodies and secrets are not printed.","status":"NOT_COMPLETED"}); code=2
    raise SystemExit(code)
