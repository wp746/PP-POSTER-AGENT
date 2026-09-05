import copy
import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image
from poster_agent.contracts import validate_brief,validate_plan,validate_qc,QC_RULES
from poster_agent.core import PosterError,within,write_json
from poster_agent.config import save_config,load_config,endpoint
from poster_agent.sources import extract
from poster_agent.render import font_check,compose
from conftest import plan_for


@pytest.mark.parametrize("size",[[1000,1000],[0,1024],[4096,4096],[512,2560],[1024.0,1024]])
def test_bad_canvas_rejected(brief,size):
    brief["canvases"]=[size]
    with pytest.raises(PosterError):validate_brief(brief)


def test_reference_edit_needs_authorization(brief):
    brief["subject_mode"]="reference_edit"
    with pytest.raises(PosterError,match="authorization"):validate_brief(brief)


@pytest.mark.parametrize("state",["inferred","conflicted","missing"])
def test_unresolved_fact_blocked(brief,state):
    brief["facts"][0]["status"]=state
    with pytest.raises(PosterError):validate_brief(brief)


def test_incomplete_qc_cannot_pass():
    with pytest.raises(PosterError):validate_qc({"checks":[]},"final")
    full={"checks":[{"rule":r,"result":"unknown","evidence":"unreadable"} for r in QC_RULES["final"]]}
    assert not validate_qc(full,"final")


def test_layout_dropped_text_and_bad_coordinate(brief):
    p=plan_for(brief);p["texts"].pop()
    with pytest.raises(PosterError):validate_plan(p,brief)
    p=plan_for(brief);p["hero"][0]=float("nan")
    with pytest.raises(PosterError):validate_plan(p,brief)


@pytest.mark.parametrize("relative",["../secret","/etc/passwd","a/../../bad"])
def test_path_escape_blocked(tmp_path,relative):
    with pytest.raises(PosterError):within(tmp_path,relative)


def test_symlink_blocked(tmp_path):
    (tmp_path/"link").symlink_to(tmp_path.parent,target_is_directory=True)
    with pytest.raises(PosterError):within(tmp_path,"link/file")


def test_no_ambient_credential_fallback(tmp_path,monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","not-a-real-key")
    monkeypatch.setenv("PP_IMAGE_KEY","also-not-configured")
    with pytest.raises(PosterError):load_config(tmp_path)


def test_single_key_two_roles_private(tmp_path):
    spec={"base_url":"https://example.com/v1","model":"fixture","key_ref":"shared"}
    save_config(tmp_path,dict(spec),dict(spec),{"shared":"fixture-not-a-real-key"})
    c=load_config(tmp_path)
    assert c["image"]["api_key"]==c["vision"]["api_key"]
    import os
    if os.name!="nt":assert (tmp_path/".local/secrets.json").stat().st_mode & 0o077 == 0


@pytest.mark.parametrize("url",["http://example.com/v1","https://u:p@example.com/v1","https://example.com/v1?key=bad"])
def test_bad_config_url(url):
    with pytest.raises(PosterError):endpoint(url)


def test_pptx_preserves_slide_locations(tmp_path):
    p=tmp_path/"a.pptx"
    with zipfile.ZipFile(p,"w") as z:
        for n in (12,2):
            z.writestr(f"ppt/slides/slide{n}.xml",f'<p xmlns:a="x"><a:t>Slide {n}</a:t></p>')
    d=extract(p)
    assert d["pages"][0]["location"]=="ppt/slides/slide2.xml"
    assert d["visual_review_required"]


def test_missing_glyph_fails(brief):
    with pytest.raises(PosterError,match="glyph"):font_check(Path(brief["font"]),["\U0010FFFF"])


def test_overflow_does_not_truncate(tmp_path,brief):
    p=plan_for(brief);brief["copy"][0]["text"]="LONG TEXT "*200
    Image.new("RGB",(1024,1024),"white").save(tmp_path/"base.png")
    with pytest.raises(PosterError,match="overflow"):
        compose(tmp_path/"base.png",tmp_path/"final.png",brief,p,Path(brief["font"]),None,None,{})
    assert not (tmp_path/"final.png").exists()
