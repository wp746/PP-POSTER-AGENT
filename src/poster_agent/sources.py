from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .core import PosterError, require


def extract(path: Path) -> dict:
    """Text extraction with explicit visual-review limits; no Office execution."""
    require(path.stat().st_size <= 30 * 1024 * 1024, "Document exceeds 30 MiB")
    suffix = path.suffix.lower()
    pages = []
    visual = False
    if suffix in {".txt", ".md"}:
        pages = [{"location": "text", "text": path.read_text(encoding="utf-8")}]
    elif suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        require(not reader.is_encrypted and len(reader.pages) <= 150, "Encrypted or oversized PDF")
        pages = [{"location": f"page {i+1}", "text": p.extract_text() or ""} for i, p in enumerate(reader.pages)]
        visual = True
    elif suffix in {".docx", ".pptx"}:
        with zipfile.ZipFile(path) as z:
            require(sum(x.file_size for x in z.infolist()) <= 100 * 1024 * 1024, "Office archive is too large")
            if suffix == ".docx":
                names = ["word/document.xml"]
            else:
                names = sorted((n for n in z.namelist() if n.startswith("ppt/slides/slide")
                                and n.endswith(".xml") and n.rsplit("slide", 1)[-1][:-4].isdigit()),
                               key=lambda n: int(n.rsplit("slide", 1)[-1][:-4]))
            require(len(names) <= 150, "Too many slides")
            for name in names:
                tree = ET.fromstring(z.read(name))
                text = "\n".join(x.text or "" for x in tree.iter() if x.tag.endswith("}t"))
                pages.append({"location": name, "text": text})
        visual = True
    else:
        raise PosterError("Use TXT, Markdown, PDF, DOCX or PPTX; convert old Office formats first")
    require(sum(len(x["text"]) for x in pages) <= 80_000, "Document text too long; split/select relevant material")
    return {"pages": pages, "visual_review_required": visual,
            "unreadable_pages": [x["location"] for x in pages if not x["text"].strip()]}
