from __future__ import annotations

import contextlib
import os
import sqlite3
import time
import uuid
from pathlib import Path

from .core import PosterError, atomic_write, digest, fingerprint, read_json, require, within, write_json
from .contracts import validate_brief
from .render import normalize_image, font_check
from .sources import extract


def create_job(brief_path: Path, workspace: Path) -> Path:
    b = read_json(brief_path)
    validate_brief(b)
    identifier = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:10]
    workspace.mkdir(parents=True, exist_ok=True)
    require(not workspace.is_symlink(), "Workspace cannot be a symlink")
    job = workspace / identifier
    job.mkdir(mode=0o700)
    hashes = {}
    def copy(source: str, picture=False) -> str:
        p = Path(source).expanduser()
        if not p.is_absolute():
            p = brief_path.parent / p
        require(p.is_file() and not p.is_symlink(), "Missing or symlink input asset")
        require(p.stat().st_size <= 60*1024*1024, "Asset exceeds 60 MiB")
        content = normalize_image(p) if picture else p.read_bytes()
        suffix = ".png" if picture else p.suffix.lower()
        relative = "assets/" + digest(content) + suffix
        atomic_write(job / relative, content)
        hashes[relative] = digest(content)
        return relative
    try:
        b["font"] = copy(b["font"])
        font_check(job / b["font"], [x["text"] for x in b["copy"]])
        if b.get("subject"):
            b["subject"] = copy(b["subject"], True)
        if b.get("mask"):
            b["mask"] = copy(b["mask"], True)
        for a in b.get("assets", []):
            a["path"] = copy(a["path"], True)
        docs = []
        document_paths = []
        for p in b.get("documents", []):
            relative = copy(p)
            document_paths.append(relative)
            docs.append({"asset": relative, **extract(job / relative)})
        b["documents"] = document_paths
        snapshot = {"schema_version": 1, "job_id": identifier, "brief": b, "asset_hashes": hashes, "documents": docs}
        write_json(job / "input.json", snapshot)
        with Store(job) as store:
            store.set("input_hash", fingerprint(snapshot))
            store.set("status", "DRAFT")
        return job
    except Exception:
        write_json(job / "IMPORT_FAILED.json", {"status": "IMPORT_FAILED", "message": "Correct inputs and create a new job"})
        raise


class Store:
    def __init__(self, path: Path):
        require((path/"input.json").is_file(), "Not an initialized poster job")
        require(not path.is_symlink() and not (path/"job.sqlite").is_symlink(), "Symlink database forbidden")
        self.path = path.resolve()
        self.db = sqlite3.connect(self.path / "job.sqlite", timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, step TEXT, input_hash TEXT, role TEXT,
            status TEXT, output TEXT, output_hash TEXT, meta TEXT, error TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS checkpoints(step TEXT PRIMARY KEY, input_hash TEXT, output TEXT, output_hash TEXT);
        """)
        self.db.commit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def get(self, key: str, default="") -> str:
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, str(value)))
        self.db.commit()

    def snapshot(self) -> dict:
        value = read_json(self.path / "input.json")
        require(fingerprint(value) == self.get("input_hash"), "Input snapshot was modified; create a revision")
        for relative, expected in value["asset_hashes"].items():
            p = within(self.path, relative)
            require(p.is_file() and digest(p.read_bytes()) == expected, "Input asset changed or missing")
        return value

    def cached(self, step: str, key: str) -> Path | None:
        row = self.db.execute("SELECT * FROM checkpoints WHERE step=? AND input_hash=?", (step,key)).fetchone()
        if row:
            path = within(self.path, row["output"])
            require(path.is_file() and digest(path.read_bytes()) == row["output_hash"], "Checkpoint corrupted; no silent regeneration")
            return path
        return None

    def checkpoint(self, step: str, key: str, path: Path):
        relative = str(path.relative_to(self.path))
        self.db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?,?,?,?)", (step, key, relative, digest(path.read_bytes())))
        self.db.commit()

    def calls(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]

    def status(self) -> dict:
        return {"job_id": self.path.name, "status": self.get("status"), "provenance": self.get("provenance", "not_run"),
                "calls": self.calls(), "attempts": [dict(x) for x in self.db.execute(
                    "SELECT id,step,role,status,error,meta FROM attempts ORDER BY created")],
                "has_final": (self.path / "delivery.json").exists()}


@contextlib.contextmanager
def exclusive(job: Path):
    path = job / ".running.lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise PosterError("Job is locked. If process crashed, use recover --acknowledge after confirming it stopped") from None
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def process_running(pid: int) -> bool:
    require(pid>0,"Invalid worker PID")
    if os.name=="nt":
        # os.kill(pid, 0) is not a safe Windows liveness probe.
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:
            require(ctypes.get_last_error()==87,"Cannot inspect worker process safely")
            return False
        try:
            code=wintypes.DWORD()
            require(bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))),"Cannot read worker status")
            return code.value==259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid,0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        raise PosterError("Cannot inspect worker process safely") from None
