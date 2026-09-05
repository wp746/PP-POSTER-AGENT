import argparse
import json
from pathlib import Path

import pytest
from PIL import Image

from poster_agent.core import PosterError, read_json, write_json, digest
from poster_agent.engine import Engine, verify_delivery
from poster_agent.provider import ProviderFailure
from poster_agent.store import Store, exclusive
from poster_agent.cli import review, export, parser
from poster_agent.cli import adopt_plan, revise_copy, recover, attach_style, dispatch
from conftest import FakeGateway, plan_for


def test_protected_full_chain_and_resume(job,brief):
    gateway=FakeGateway(brief)
    state=Engine(job,gateway,20).run()
    assert state["status"]=="TEST_COMPLETED"
    assert gateway.image_calls==1 and gateway.references==[[]]
    with Store(job) as s:
        delivery=verify_delivery(s)
        layers=read_json(job/delivery["items"][0]["layers"])
        assert layers["layers"][0]["kind"]=="protected_subject"
        assert [x["exact_text"] for x in layers["layers"] if x["kind"]=="text"]==["TEST ONLY","Phone 123"]
        before=s.calls()
    Engine(job,gateway,20).run()
    with Store(job) as s: assert s.calls()==before
    assert gateway.image_calls==1


def test_plan_does_not_generate(job,brief):
    g=FakeGateway(brief)
    assert Engine(job,g,5).run(stop_after_plan=True)["status"]=="PLANNED"
    assert g.image_calls==0


def test_test_results_cannot_be_reviewed_or_exported(job,brief,tmp_path):
    Engine(job,FakeGateway(brief),20).run()
    with pytest.raises(PosterError): review(argparse.Namespace(job=job,accept=True,reviewer="test",sources_reviewed=True))
    with pytest.raises(PosterError): export(argparse.Namespace(job=job,output=tmp_path/"out.zip"))
    assert not (tmp_path/"out.zip").exists()


@pytest.mark.parametrize("stage",["subject","final"])
def test_qc_failure_blocks_completion(job,brief,stage):
    g=FakeGateway(brief); g.fail_stage=stage
    with pytest.raises(PosterError,match="QC_NOT_PASSED"): Engine(job,g,20).run()
    with Store(job) as s: assert s.get("status")=="NEEDS_REVIEW"
    assert not (job/"delivery.json").exists()
    if stage=="subject": assert g.image_calls==0


def test_unknown_outcome_not_automatically_retried(job,brief):
    g=FakeGateway(brief); g.raise_image=ProviderFailure("timeout",True)
    with pytest.raises(ProviderFailure): Engine(job,g,20).run()
    assert g.image_calls==1
    g.raise_image=None
    with pytest.raises(PosterError,match="UNKNOWN_PROVIDER_OUTCOME"): Engine(job,g,20).run()
    assert g.image_calls==1


def test_explicit_resolution_allows_retry(job,brief):
    g=FakeGateway(brief);g.raise_image=ProviderFailure("timeout",True)
    with pytest.raises(ProviderFailure): Engine(job,g,20).run()
    with Store(job) as s: attempt=s.db.execute("SELECT id FROM attempts WHERE status='UNKNOWN'").fetchone()[0]
    recover(argparse.Namespace(job=job,acknowledge=True,resolve=attempt,reason="Operator accepts duplicate-charge risk after provider review"))
    g.raise_image=None
    assert Engine(job,g,20).run()["status"]=="TEST_COMPLETED"
    assert g.image_calls==2


def test_budget_is_absolute(job,brief):
    g=FakeGateway(brief)
    with pytest.raises(PosterError,match="BUDGET"): Engine(job,g,1).run()
    with Store(job) as s: assert s.calls()==1
    with pytest.raises(PosterError,match="BUDGET"): Engine(job,g,1).run()
    assert g.vision_calls==1


def test_snapshot_and_asset_tamper_blocked(job,brief):
    b=read_json(job/"input.json")
    (job/b["brief"]["subject"]).write_bytes(b"tampered")
    g=FakeGateway(brief)
    with pytest.raises(PosterError,match="asset changed"): Engine(job,g,20).run()
    assert not g.image_calls and not g.vision_calls


def test_checkpoint_tamper_does_not_regenerate(job,brief):
    g=FakeGateway(brief);Engine(job,g,20).run(stop_after_plan=True)
    with Store(job) as s: p=s.db.execute("SELECT output FROM checkpoints WHERE step='analysis'").fetchone()[0]
    (job/p).write_text("{}")
    with pytest.raises(PosterError,match="corrupted"): Engine(job,g,20).run()
    assert g.vision_calls==2


def test_exclusive_lock(job):
    with exclusive(job):
        with pytest.raises(PosterError,match="locked"):
            with exclusive(job): pass


def test_pause_blocks_new_requests(job,brief):
    with Store(job) as s: s.set("control","PAUSED")
    g=FakeGateway(brief)
    with pytest.raises(PosterError,match="paused"): Engine(job,g,20).run()
    assert g.image_calls==g.vision_calls==0


def test_bad_layout_stops_before_images(job,brief,tmp_path):
    g=FakeGateway(brief);Engine(job,g,20).run(stop_after_plan=True)
    plan=plan_for(brief);plan["texts"][0]["region"]=[.05,.45,.6,.4]
    p=tmp_path/"plan.json";write_json(p,plan)
    adopt_plan(argparse.Namespace(job=job,canvas=0,plan=p))
    with pytest.raises(PosterError,match="intersects"): Engine(job,g,20).run()
    assert g.image_calls==0
    assert not (job/"delivery.json").exists()


def test_text_only_revision_reuses_images(job,brief,tmp_path):
    g=FakeGateway(brief);Engine(job,g,30).run()
    copy=[dict(x) for x in brief["copy"]];copy[1]["text"]="Phone 456"
    facts=[{"field":"contact","value":"456","status":"provided","source":"current explicit user update"}]
    write_json(tmp_path/"copy.json",copy);write_json(tmp_path/"facts.json",facts)
    revise_copy(argparse.Namespace(job=job,copy=tmp_path/"copy.json",facts=tmp_path/"facts.json",keep_design=True))
    Engine(job,g,30).run()
    assert g.image_calls==1
    with Store(job) as s:
        d=verify_delivery(s)
        layers=read_json(job/d["items"][0]["layers"])
        assert any(x.get("exact_text")=="Phone 456" for x in layers["layers"])


def test_style_requires_explicit_experimental(job,brief,tmp_path):
    p=tmp_path/"style.json";write_json(p,{"id":"demo","version":"0.1","rules":["soft light"],
        "source_case_tokens":["OLD_BRAND"],"domains":["food"],"status":"validated"})
    attach_style(argparse.Namespace(job=job,style=p))
    assert read_json(job/"input.json")["style"]["status"]=="draft"
    with pytest.raises(PosterError,match="experimental"): Engine(job,FakeGateway(brief),20).run()


def test_reference_edit_passes_current_master_to_b(tmp_path,brief):
    from poster_agent.store import create_job
    brief.update({"subject_mode":"reference_edit","allow_reference_edit":True})
    p=tmp_path/"edit.json";write_json(p,brief);job=create_job(p,tmp_path/"editjobs")
    g=FakeGateway(brief);Engine(job,g,20).run()
    assert g.image_calls==2
    with Store(job) as s: master=s.db.execute("SELECT output FROM checkpoints WHERE step='subject'").fetchone()[0]
    assert g.references[1]==[(job/master).read_bytes()]


def test_event_multi_canvas(tmp_path,brief):
    from poster_agent.store import create_job
    brief["kind"]="event";brief.pop("subject");brief["canvases"]=[[1024,1024],[1152,2048]]
    p=tmp_path/"event.json";write_json(p,brief);job=create_job(p,tmp_path/"eventjobs")
    g=FakeGateway(brief);Engine(job,g,20).run()
    with Store(job) as s:
        d=verify_delivery(s)
        assert len(d["items"])==2
        assert [list(Image.open(job/x["image"]).size) for x in d["items"]]==brief["canvases"]


def test_output_tamper_blocks_verification(job,brief):
    Engine(job,FakeGateway(brief),20).run()
    d=read_json(job/"delivery.json");(job/d["items"][0]["image"]).write_bytes(b"corrupt")
    with Store(job) as s:
        with pytest.raises(PosterError,match="artifact changed"):verify_delivery(s)


def test_export_lifecycle_with_synthetic_evidence(job,brief,tmp_path):
    # Deliberately simulates the live label to exercise export gates; never a live API test.
    g=FakeGateway(brief);g.provenance="live"
    Engine(job,g,20).run()
    with pytest.raises(PosterError):export(argparse.Namespace(job=job,output=tmp_path/"early.zip"))
    review(argparse.Namespace(job=job,accept=True,reviewer="SYNTHETIC UNIT TEST",sources_reviewed=False))
    export(argparse.Namespace(job=job,output=tmp_path/"unit-test-only.zip"))
    import zipfile
    with zipfile.ZipFile(tmp_path/"unit-test-only.zip") as z:
        assert "delivery.json" in z.namelist() and "FONT-NOTICE.txt" in z.namelist()
        assert all(not x.endswith((".ttf",".ttc",".otf")) for x in z.namelist())


def test_retry_cap_does_not_reset_with_feedback(job,brief):
    g=FakeGateway(brief);g.raise_image=ProviderFailure("HTTP_400",False)
    for i in range(3):
        with Store(job) as s:s.set("repair_base_0",str(i))
        with pytest.raises(ProviderFailure):Engine(job,g,30).run()
    with Store(job) as s:s.set("repair_base_0","fourth variation")
    with pytest.raises(PosterError,match="attempt limit"):Engine(job,g,30).run()
    assert g.image_calls==3


def test_crash_marker_blocks_new_calls(job,brief):
    g=FakeGateway(brief)
    with Store(job) as s:
        s.db.execute("INSERT INTO attempts(id,step,status) VALUES ('interrupted','base_0','IN_FLIGHT')");s.db.commit()
    with pytest.raises(PosterError,match="UNKNOWN"):Engine(job,g,20).run()
    assert g.vision_calls==0


def test_liveness_probe_never_terminates_current_process():
    import os
    from poster_agent.store import process_running
    assert process_running(os.getpid())
    with pytest.raises(PosterError):process_running(0)


def test_status_does_not_create_database_in_arbitrary_directory(tmp_path):
    with pytest.raises(PosterError):Store(tmp_path)
    assert not (tmp_path/"job.sqlite").exists()
