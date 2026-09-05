from __future__ import annotations

import io
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, features
from fontTools.ttLib import TTFont

from .core import PosterError, require, write_json, atomic_write, digest


def font_check(path: Path, texts: list[str]) -> None:
    try:
        font = TTFont(path, fontNumber=0)
        cmap = font.getBestCmap() or {}
        font.close()
        chars = {c for t in texts for c in t if not c.isspace()}
        require(all(ord(c) in cmap for c in chars), "Selected font lacks required glyphs")
        if any(unicodedata.bidirectional(c) in {"R", "AL", "AN"} for c in chars):
            require(features.check_feature("raqm"), "This script needs Pillow with RAQM shaping")
    except PosterError:
        raise
    except Exception:
        raise PosterError("Unable to load or validate font") from None


def normalize_image(path: Path) -> bytes:
    with Image.open(path) as im:
        require(im.width * im.height <= 20_000_000, "Input photo exceeds pixel limit")
        im = ImageOps.exif_transpose(im).convert("RGBA")
        out = io.BytesIO()
        im.save(out, "PNG")
        return out.getvalue()


def box(region: list, size: tuple[int, int]) -> tuple[int, int, int, int]:
    x, y, w, h = region
    return round(x*size[0]), round(y*size[1]), round(w*size[0]), round(h*size[1])


def overlap(a, b) -> bool:
    x, y, w, h = a
    xx, yy, ww, hh = b
    return max(x, xx) < min(x+w, xx+ww) and max(y, yy) < min(y+h, yy+hh)


def wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            if font.getlength(current + char) > width:
                require(bool(current), "A glyph exceeds the text region")
                lines.append(current)
                current = char
            else:
                current += char
        lines.append(current)
    return lines


def compose(base: Path, output: Path, brief: dict, plan: dict, font_path: Path,
            subject: Path | None, mask: Path | None, assets: dict[str, Path]) -> dict:
    """Deterministic exact-copy layers; refuse overflow/overlap, never truncate."""
    with Image.open(base) as source:
        canvas = source.convert("RGBA")
    size = canvas.size
    occupied = []
    layers = []
    if subject:
        with Image.open(subject) as im:
            hero = im.convert("RGBA")
        if mask:
            with Image.open(mask) as m:
                require(m.size == hero.size, "Mask must match normalized subject dimensions")
                alpha = m.convert("L")
                require(alpha.getextrema()[1] > 0, "Mask cannot be empty")
                hero.putalpha(alpha)
        x, y, w, h = box(plan["hero"], size)
        fitted = ImageOps.contain(hero, (w, h), Image.Resampling.LANCZOS)
        pos = (x + (w-fitted.width)//2, y+(h-fitted.height)//2)
        canvas.alpha_composite(fitted, pos)
        occupied.append((pos[0], pos[1], fitted.width, fitted.height))
        layers.append({"kind": "protected_subject", "source_sha256": digest(subject.read_bytes()),
                       "region_px": occupied[-1], "mask_sha256": digest(mask.read_bytes()) if mask else None})
    for item in plan["assets"]:
        with Image.open(assets[item["id"]]) as im:
            im = im.convert("RGBA")
            x, y, w, h = box(item["region"], size)
            im = ImageOps.contain(im, (w, h), Image.Resampling.LANCZOS)
            region = (x, y, im.width, im.height)
            require(not any(overlap(region, r) for r in occupied), "Protected assets overlap")
            canvas.alpha_composite(im, (x, y))
            occupied.append(region)
            layers.append({"kind": "asset", "id": item["id"], "region_px": region,
                           "source_sha256": digest(assets[item["id"]].read_bytes())})
    font_check(font_path, [x["text"] for x in brief["copy"]])
    text_map = {x["id"]: x["text"] for x in brief["copy"]}
    draw = ImageDraw.Draw(canvas)
    for item in plan["texts"]:
        x, y, w, h = box(item["region"], size)
        require(not any(overlap((x,y,w,h), r) for r in occupied), "Text intersects a protected/text region; adjust layout")
        font = ImageFont.truetype(str(font_path), max(12, round(item["size"] * min(size))))
        lines = wrap(text_map[item["id"]], font, w)
        ascent, descent = font.getmetrics()
        line_height = round((ascent + descent) * 1.12)
        require(line_height * len(lines) <= h, "Text overflow; adjust region or explicitly revise copy")
        for row, line in enumerate(lines):
            length = font.getlength(line)
            offset = (w-length)/2 if item.get("align") == "center" else w-length if item.get("align") == "right" else 0
            draw.text((x+offset, y+row*line_height), line, font=font, fill=item["color"], anchor="lt")
        occupied.append((x,y,w,h))
        layers.append({"kind": "text", "id": item["id"], "exact_text": text_map[item["id"]],
                       "lines": lines, "region_px": [x,y,w,h], "font_size": font.size,
                       "color": item["color"], "align": item.get("align", "left")})
    out = io.BytesIO()
    canvas.convert("RGB").save(out, "PNG")
    atomic_write(output, out.getvalue())
    return {"layers": layers, "size": list(size), "copy_sha256": digest(str(brief["copy"]).encode()),
            "font_sha256": digest(font_path.read_bytes()), "output_sha256": digest(out.getvalue())}
