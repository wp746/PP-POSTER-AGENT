from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


class PosterError(Exception):
    """Safe, user-visible errors. Never include provider bodies or credentials."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def fingerprint(value: Any) -> str:
    return digest(canonical(value))


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PosterError("JSON file is missing or invalid") from exc


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise PosterError("Refusing symlink output")
    fd, temp = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2).encode() + b"\n")


def within(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise PosterError("Expected a project-relative path")
    path = root / relative
    if ".." in Path(relative).parts:
        raise PosterError("Parent traversal is forbidden")
    current = root
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise PosterError("Symlink project paths are forbidden")
    if not path.resolve().is_relative_to(root.resolve()):
        raise PosterError("Path leaves project")
    return path


def identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", value):
        raise PosterError("IDs must contain 1-64 letters, numbers, underscores or hyphens")
    return value


def require(ok: bool, message: str) -> None:
    if not ok:
        raise PosterError(message)


def object_result(value: Any, required: dict[str, type]) -> dict:
    require(isinstance(value, dict), "Model must return a JSON object")
    for key, kind in required.items():
        require(key in value and isinstance(value[key], kind), f"Invalid model field: {key}")
    return value
