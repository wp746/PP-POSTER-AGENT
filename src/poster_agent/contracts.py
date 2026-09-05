from __future__ import annotations

import math
from .core import identifier, require, object_result

FACT_STATES = {"provided", "verified", "inferred", "conflicted", "missing"}
ROLES = {"headline", "subtitle", "slogan", "selling_point", "contact", "action", "legal"}
QC_RULES = {
    "subject": ["identity", "geometry", "plating", "vessel", "surface", "camera"],
    "base": ["identity", "no_extra_subject", "composition", "no_generated_text", "artifacts"],
    "final": ["identity", "no_extra_subject", "copy_accuracy", "readability", "brand", "facts", "artifacts", "design"],
}


def validate_brief(b: dict) -> None:
    object_result(b, {"schema_version": int, "kind": str, "copy": list, "facts": list,
                      "canvases": list, "font": str, "goal": str})
    require(b["schema_version"] == 1, "Unsupported brief schema")
    require(b["kind"] in {"food", "event"}, "kind must be food or event")
    require(0 < len(b["goal"]) <= 2000, "A concise communication goal is required")
    require(1 <= len(b["canvases"]) <= 5, "Choose 1-5 canvases")
    for size in b["canvases"]:
        require(isinstance(size, list) and len(size) == 2 and all(type(n) is int for n in size), "Invalid canvas")
        w, h = size
        require(min(w, h) >= 512 and max(w, h) <= 2560 and w % 16 == h % 16 == 0
                and max(w, h) / min(w, h) <= 3 and 655360 <= w*h <= 3686400, "Canvas outside V1 validated bounds")
    require(len({tuple(x) for x in b["canvases"]}) == len(b["canvases"]), "Duplicate canvases")
    require(1 <= len(b["copy"]) <= 16, "Choose 1-16 exact text blocks")
    ids = set()
    for item in b["copy"]:
        object_result(item, {"id": str, "text": str, "role": str})
        identifier(item["id"])
        require(item["id"] not in ids, "Duplicate text ID")
        ids.add(item["id"])
        require(item["role"] in ROLES and 0 < len(item["text"]) <= 500, "Invalid text block")
    require(any(x["role"] == "headline" for x in b["copy"]), "Headline is required")
    for f in b["facts"]:
        object_result(f, {"field": str, "value": str, "status": str, "source": str})
        require(f["status"] in FACT_STATES, "Invalid fact status")
        require(f["status"] in {"provided", "verified"}, "Resolve missing/inferred/conflicting publication facts first")
        require(bool(f["source"].strip()), "Every publication fact needs a source")
    if b["kind"] == "food":
        require(bool(b.get("subject")), "Food requires its original photo")
        require(b.get("subject_mode", "protected") in {"protected", "reference_edit"}, "Unknown subject mode")
        if b.get("subject_mode") == "reference_edit":
            require(b.get("allow_reference_edit") is True, "Reference editing needs explicit brief authorization")
    require(isinstance(b.get("assets", []), list) and len(b.get("assets", [])) <= 8, "At most 8 protected assets")
    for a in b.get("assets", []):
        object_result(a, {"id": str, "path": str, "role": str})
        identifier(a["id"])
        require(a["id"] not in ids, "Duplicate asset/text ID")
        ids.add(a["id"])
        require(a["role"] in {"logo", "ip", "person"}, "V1 supports logo/IP/person assets; QR needs a separate verified tool")
    for source in b.get("research", []):
        object_result(source, {"claim": str, "url": str, "checked_at": str})
        require(source["url"].startswith("https://"), "Research needs source URL")
    require(len(b.get("documents", [])) <= 12, "At most 12 source documents")


def rect(value: list) -> list:
    require(isinstance(value, list) and len(value) == 4, "Region must be [x,y,w,h]")
    require(all(type(n) in (float, int) and math.isfinite(n) for n in value), "Invalid region coordinate")
    x, y, w, h = value
    require(0 <= x < 1 and 0 <= y < 1 and w > 0 and h > 0 and x+w <= 1.00001 and y+h <= 1.00001,
            "Region is outside canvas")
    return value


def validate_plan(p: dict, brief: dict) -> None:
    object_result(p, {"theme": str, "background_prompt": str, "texts": list, "assets": list, "hero": list})
    require(0 < len(p["background_prompt"]) <= 12000, "Invalid background description")
    if brief["kind"] == "food":
        rect(p["hero"])
    require(len(p["texts"]) == len(brief["copy"]), "Layout dropped or added text")
    require({x.get("id") for x in p["texts"]} == {x["id"] for x in brief["copy"]}, "Text IDs must match exact copy")
    require(len(p["assets"]) == len(brief.get("assets", [])), "Layout dropped protected asset")
    require({x.get("id") for x in p["assets"]} == {x["id"] for x in brief.get("assets", [])}, "Asset IDs mismatch")
    for t in p["texts"]:
        rect(t.get("region"))
        require(type(t.get("size")) in (int, float) and 0.012 <= t["size"] <= 0.25, "Invalid font scale")
        require(isinstance(t.get("color"), str) and len(t["color"]) == 7 and t["color"].startswith("#"), "Use hex text color")
        try:
            int(t["color"][1:], 16)
        except ValueError:
            require(False, "Invalid hex color")
        require(t.get("align", "left") in {"left", "center", "right"}, "Invalid alignment")
    for a in p["assets"]:
        rect(a.get("region"))


def validate_qc(report: dict, stage: str) -> bool:
    object_result(report, {"checks": list})
    expected = QC_RULES[stage]
    require(len(report["checks"]) == len(expected), "Incomplete QC report")
    require({x.get("rule") for x in report["checks"]} == set(expected), "QC rule set mismatch")
    for x in report["checks"]:
        require(x.get("result") in {"pass", "fail", "unknown"}, "Invalid QC result")
        require(isinstance(x.get("evidence"), str) and bool(x["evidence"].strip()), "QC requires observation evidence")
    return all(x["result"] == "pass" for x in report["checks"])
