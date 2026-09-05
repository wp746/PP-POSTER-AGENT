from __future__ import annotations

import io
import json
import time
import uuid
from pathlib import Path

from PIL import Image

from . import prompts
from .contracts import validate_plan, validate_qc
from .core import PosterError, atomic_write, digest, fingerprint, object_result, read_json, require, within, write_json
from .provider import ProviderFailure
from .render import compose
from .store import Store, exclusive


class Engine:
    def __init__(self, job: Path, gateway, max_calls: int):
        require(1 <= max_calls <= 100, "Call budget must be 1-100 total calls for this job")
        self.job = job.resolve()
        self.gateway = gateway
        self.max_calls = max_calls

    def _control(self):
        value = self.store.get("control")
        if value in {"PAUSED", "CANCELLED"}:
            self.store.set("status", value)
            raise PosterError("Job " + value.lower() + "; completed calls preserved")

    def _call(self, step: str, role: str, payload: dict, operation, validator=None) -> Path:
        self._control()
        key = fingerprint({"payload": payload, "provider": self.profile, "provenance": self.gateway.provenance})
        cached = self.store.cached(step, key)
        if cached:
            return cached
        unknown = self.store.db.execute("SELECT 1 FROM attempts WHERE status IN ('IN_FLIGHT','UNKNOWN')").fetchone()
        require(not unknown, "UNKNOWN_PROVIDER_OUTCOME: resolve request outcome before any new call")
        require(self.store.calls() < self.max_calls, "CALL_BUDGET_EXHAUSTED: explicitly authorize a larger total to continue")
        attempts = self.store.db.execute("SELECT COUNT(*) FROM attempts WHERE step=?", (step,)).fetchone()[0]
        require(attempts < 3, "Step attempt limit reached; revise input or plan")
        attempt_id = uuid.uuid4().hex
        self.store.db.execute("INSERT INTO attempts(id,step,input_hash,role,status,created) VALUES (?,?,?,?,?,?)",
                              (attempt_id,step,key,role,"IN_FLIGHT",time.time()))
        self.store.db.commit()
        suffix = ".png" if role == "image" else ".json"
        output = self.job / "artifacts" / (step + "-" + attempt_id + suffix)
        try:
            result, meta = operation()
            if role == "image":
                atomic_write(output, result)
            else:
                write_json(output, result)
            if validator:
                validator(output)
            self.store.db.execute("UPDATE attempts SET status='DONE',output=?,output_hash=?,meta=? WHERE id=?",
                                  (str(output.relative_to(self.job)), digest(output.read_bytes()), json.dumps(meta), attempt_id))
            self.store.db.commit()
            self.store.checkpoint(step, key, output)
            self._control()
            return output
        except BaseException as exc:
            row = self.store.db.execute("SELECT status FROM attempts WHERE id=?", (attempt_id,)).fetchone()
            if row[0] == "DONE":
                raise
            uncertain = not isinstance(exc, PosterError) or (isinstance(exc, ProviderFailure) and exc.uncertain)
            state = "UNKNOWN" if uncertain else "FAILED"
            code = str(exc) if isinstance(exc, PosterError) else "INTERRUPTED_OR_UNEXPECTED_ERROR"
            self.store.db.execute("UPDATE attempts SET status=?,error=?,output=? WHERE id=?",
                                  (state, code, str(output.relative_to(self.job)) if output.exists() else None, attempt_id))
            self.store.db.commit()
            self.store.set("status", "UNKNOWN_PROVIDER_OUTCOME" if uncertain else "FAILED")
            raise

    def _vision(self, step, prompt, images, validator):
        return self._call(step, "vision", {"prompt": prompt, "images": [digest(p.read_bytes()) for p in images]},
                          lambda: self.gateway.vision(prompt, images), lambda p: validator(read_json(p)))

    def _image(self, step, prompt, size, references):
        def valid(p):
            with Image.open(p) as image:
                require(image.size == tuple(size), "Provider returned wrong dimensions; no silent stretch")
        return self._call(step, "image", {"prompt": prompt, "size": size, "references": [digest(p.read_bytes()) for p in references]},
                          lambda: self.gateway.image(prompt, tuple(size), references), valid)

    def _qc(self, step, stage, target, references, brief, analyzed):
        output = self._vision(step, prompts.qc(brief, analyzed, stage) + self.store.get("repair_"+step), [target] + references,
                              lambda r: validate_qc(r, stage))
        if not validate_qc(read_json(output), stage):
            self.store.set("status", "NEEDS_REVIEW")
            raise PosterError("QC_NOT_PASSED: inspect report; revise affected input/plan, never bypass")
        return output

    def run(self, stop_after_plan=False, experimental_style=False):
        with exclusive(self.job), Store(self.job) as self.store:
            snapshot = self.store.snapshot()
            brief = snapshot["brief"]
            self.profile = {k: {f: self.gateway.config[k][f] for f in ("base_url","model")} for k in ("image","vision")}
            old = self.store.get("provenance")
            require(not old or old == self.gateway.provenance, "Cannot mix test and live evidence")
            self.store.set("provenance", self.gateway.provenance)
            if self.store.get("status") == "COMPLETED":
                verify_delivery(self.store)
                return self.store.status()
            self._control()
            subject = within(self.job, brief["subject"]) if brief.get("subject") else None
            assets = {a["id"]: within(self.job, a["path"]) for a in brief.get("assets", [])}
            refs = ([subject] if subject else []) + list(assets.values())
            style = snapshot.get("style")
            if style:
                require(experimental_style, "V1 learned styles are experimental; use --experimental-style for an authorized trial")
            try:
                self.store.set("status", "ANALYZING")
                override = self.store.get("analysis_override")
                if override:
                    relative, expected = json.loads(override)
                    a = within(self.job,relative)
                    require(digest(a.read_bytes()) == expected,"Reused analysis changed")
                else:
                    a = self._vision("analysis", prompts.analysis(brief,snapshot["documents"]), refs,
                                     lambda v: object_result(v, {"summary":str,"dna":list,"issues":list,"category":str}))
                analyzed = read_json(a)
                if analyzed["issues"]:
                    self.store.set("status", "NEEDS_INPUT")
                    raise PosterError("FACT_ISSUES: see analysis artifact and create corrected input revision")
                plans = []
                self.store.set("status", "PLANNING")
                for i, size in enumerate(brief["canvases"]):
                    adopted = self.store.get(f"adopted_plan_{i}")
                    if adopted:
                        path, expected = json.loads(adopted)
                        p = within(self.job, path)
                        require(digest(p.read_bytes()) == expected, "Adopted plan changed")
                        validate_plan(read_json(p), brief)
                    else:
                        p = self._vision(f"plan_{i}", prompts.planning(brief, analyzed, size, style), refs,
                                         lambda v: validate_plan(v, brief))
                    plans.append((p, read_json(p)))
                    # Fail cheap layout/font checks before any billable image request.
                    blank = self.job / "artifacts" / f"layout-blank-{i}.png"
                    blank.parent.mkdir(parents=True,exist_ok=True)
                    Image.new("RGB",tuple(size),"#eee9df").save(blank)
                    check = self.job / "artifacts" / f"LAYOUT_ONLY_{i}.png"
                    compose(blank,check,brief,read_json(p),within(self.job,brief["font"]),
                            subject if subject and brief.get("subject_mode","protected")=="protected" else None,
                            within(self.job,brief["mask"]) if brief.get("mask") else None,assets)
                if stop_after_plan:
                    self.store.set("status", "PLANNED")
                    return self.store.status()
                master = subject
                if subject:
                    self.store.set("status", "SUBJECT_PREPARING")
                    if brief.get("subject_mode", "protected") == "reference_edit":
                        master = self._image("subject", prompts.image_prompt(brief,analyzed,plans[0][1],"subject") + self.store.get("repair_subject"),
                                             brief["canvases"][0], [subject])
                    self._qc("subject_qc", "subject", master, [subject], brief, analyzed)
                deliveries = []
                for i, (plan_path, plan) in enumerate(plans):
                    self._control()
                    self.store.set("status", f"GENERATING_{i}")
                    prompt = prompts.image_prompt(brief, analyzed, plan, "base", style) + self.store.get(f"repair_base_{i}")
                    if style:
                        approved = json.dumps({"copy":brief["copy"],"facts":brief["facts"],"research":brief.get("research",[])},ensure_ascii=False)
                        for token in style.get("source_case_tokens", []):
                            require(not token or token not in prompt or token in approved, "Source-case information leaked into compiled prompt")
                    edit_refs = [master] if master and brief.get("subject_mode") == "reference_edit" else []
                    base = self._image(f"base_{i}", prompt, brief["canvases"][i], edit_refs)
                    qc_refs = refs + ([master] if master and master != subject else [])
                    # Protected mode checks the composited subject; background-only has no subject to compare.
                    base_target = base
                    protected = subject and brief.get("subject_mode", "protected") == "protected"
                    render_input = {"base":digest(base.read_bytes()), "plan":digest(plan_path.read_bytes()),
                                    "input":self.store.get("input_hash")}
                    key = fingerprint(render_input)
                    final = self.store.cached(f"render_{i}", key)
                    if not final:
                        self.store.set("status", "COMPOSITING")
                        final = self.job / "artifacts" / f"render_{i}-{key[:16]}.png"
                        manifest = compose(base,final,brief,plan,within(self.job,brief["font"]),
                                           subject if protected else None,
                                           within(self.job,brief["mask"]) if protected and brief.get("mask") else None, assets)
                        write_json(final.with_suffix(".layers.json"), manifest)
                        self.store.checkpoint(f"render_{i}",key,final)
                    # For protected composition the final inspection includes exact identity and all added text.
                    if not protected:
                        self._qc(f"base_qc_{i}", "base", base_target, qc_refs, brief, analyzed)
                    final_qc = self._qc(f"final_qc_{i}", "final", final, qc_refs, brief, analyzed)
                    layers = final.with_suffix(".layers.json")
                    require(layers.is_file(), "Missing editable layer manifest")
                    deliveries.append({"canvas":brief["canvases"][i], "image":str(final.relative_to(self.job)),
                                       "image_sha256":digest(final.read_bytes()), "base":str(base.relative_to(self.job)),
                                       "base_sha256":digest(base.read_bytes()), "layers":str(layers.relative_to(self.job)),
                                       "layers_sha256":digest(layers.read_bytes()), "qc":str(final_qc.relative_to(self.job)),
                                       "qc_sha256":digest(final_qc.read_bytes())})
                write_json(self.job / "delivery.json", {"input_hash":self.store.get("input_hash"),
                           "provenance": self.gateway.provenance, "items": deliveries})
                self.store.set("delivery_hash", digest((self.job / "delivery.json").read_bytes()))
                self.store.set("status", "AWAITING_REVIEW" if self.gateway.provenance == "live" else "TEST_COMPLETED")
                return self.store.status()
            except PosterError:
                if self.store.get("status") not in {"FAILED","UNKNOWN_PROVIDER_OUTCOME","NEEDS_INPUT","NEEDS_REVIEW","PAUSED","CANCELLED"}:
                    self.store.set("status", "NEEDS_REVIEW")
                raise


def verify_delivery(store: Store) -> dict:
    store.snapshot()
    p = store.path / "delivery.json"
    require(p.is_file() and digest(p.read_bytes()) == store.get("delivery_hash"), "Delivery manifest changed or missing")
    delivery = read_json(p)
    require(delivery["input_hash"] == store.get("input_hash"), "Delivery belongs to stale input")
    for item in delivery["items"]:
        for field in ("image", "base", "layers", "qc"):
            path = within(store.path,item[field])
            require(path.is_file() and digest(path.read_bytes()) == item[field+"_sha256"], "Delivery artifact changed or missing")
        require(validate_qc(read_json(within(store.path,item["qc"])),"final"), "Final QC has not passed")
    return delivery
