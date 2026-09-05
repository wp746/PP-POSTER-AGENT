import io
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from poster_agent.core import write_json
from poster_agent.contracts import QC_RULES
from poster_agent.store import create_job


def available_font():
    candidates = ["/System/Library/Fonts/Supplemental/Arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "C:/Windows/Fonts/arial.ttf"]
    for path in candidates:
        if Path(path).is_file(): return path
    try: return ImageFont.truetype("DejaVuSans.ttf",20).path
    except OSError: pytest.fail("Install a test font; render tests must not silently skip")


def plan_for(brief):
    texts=[]
    for i,item in enumerate(brief["copy"]):
        texts.append({"id":item["id"],"region":[0.05,0.04+i*.11,0.90,.09],
                      "size":.035,"color":"#272727","align":"left"})
    return {"theme":"TEST fixture only","background_prompt":"Neutral empty TEST background, no food or lettering",
            "hero":[.05,.45,.6,.45] if brief["kind"]=="food" else [],"texts":texts,
            "assets":[{"id":a["id"],"region":[.80,.80,.15,.15]} for a in brief.get("assets",[])]}


class FakeGateway:
    provenance="test"
    config={r:{"base_url":"https://example.com/v1","model":"fixture"} for r in ("image","vision")}
    def __init__(self,brief):
        self.brief=brief
        self.image_calls=0
        self.vision_calls=0
        self.references=[]
        self.fail_stage=None
        self.raise_image=None
        self.prompts=[]
    def vision(self,prompt,images):
        self.vision_calls+=1
        self.prompts.append(prompt)
        if "逐项返回 JSON" in prompt:
            stage="subject" if '"geometry"' in prompt else "final" if '"copy_accuracy"' in prompt else "base"
            return {"checks":[{"rule":r,"result":"fail" if self.fail_stage==stage else "pass",
                               "evidence":"SYNTHETIC TEST ORACLE ONLY"} for r in QC_RULES[stage]]},{"provenance":"test"}
        if "设计一个具体" in prompt:
            return plan_for(self.brief),{"provenance":"test"}
        return {"summary":"fixture","dna":["visible synthetic marker"],"issues":[],"category":"fixture"},{"provenance":"test"}
    def image(self,prompt,size,references):
        self.image_calls+=1
        self.references.append([p.read_bytes() for p in references])
        self.prompts.append(prompt)
        if self.raise_image: raise self.raise_image
        img=Image.new("RGB",size,"#eee9df")
        out=io.BytesIO(); img.save(out,"PNG")
        return out.getvalue(),{"provenance":"test","usage":None}


@pytest.fixture
def brief(tmp_path):
    im=Image.new("RGB",(400,300),"#cd9368")
    draw=ImageDraw.Draw(im); draw.rectangle((40,40,360,260),outline="black",width=5)
    draw.text((60,130),"SYNTHETIC INPUT",fill="black")
    im.save(tmp_path/"subject.png")
    return {"schema_version":1,"kind":"food","subject":str(tmp_path/"subject.png"),"subject_mode":"protected",
            "font":available_font(),"goal":"TEST ONLY identity preservation", "canvases":[[1024,1024]],
            "copy":[{"id":"title","role":"headline","text":"TEST ONLY"},
                    {"id":"contact","role":"contact","text":"Phone 123"}],
            "facts":[{"field":"contact","value":"123","status":"provided","source":"test fixture"}]}


@pytest.fixture
def job(tmp_path,brief):
    p=tmp_path/"brief.json"; write_json(p,brief)
    return create_job(p,tmp_path/"projects")
