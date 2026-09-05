from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

from .core import PosterError, read_json, require, write_json

PRESETS = {
    "yunwu": "https://yunwu.ai/v1",
    "siliconflow": "https://api.siliconflow.cn/v1",
}


def endpoint(value: str) -> str:
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and bool(parsed.hostname), "Provider URL must use HTTPS")
    require(not parsed.username and not parsed.password and not parsed.query and not parsed.fragment,
            "Provider URL cannot contain credentials, query or fragment")
    return value.rstrip("/")


def load_config(root: Path) -> dict:
    config_path = root / ".local" / "config.json"
    secret_path = root / ".local" / "secrets.json"
    require(not (root / ".local").is_symlink() and not config_path.is_symlink()
            and not secret_path.is_symlink(), "Private config cannot be a symlink")
    data = read_json(config_path)
    secrets = read_json(secret_path)
    require(data.get("schema_version") == 1, "Unsupported config schema")
    if os.name != "nt":
        require(secret_path.stat().st_mode & 0o077 == 0, "Secrets file must be private (chmod 600)")
    for role in ("image", "vision"):
        item = data.get(role, {})
        require(isinstance(item, dict), "Missing provider role")
        item["base_url"] = endpoint(item.get("base_url", ""))
        require(isinstance(item.get("model"), str) and bool(item["model"].strip()), "Explicit model ID required")
        require(not item["model"].startswith(("SELECT_", "YOUR_")), "Replace placeholder with an actual model ID")
        key = secrets.get(item.get("key_ref"))
        require(isinstance(key, str) and bool(key.strip()), f"Missing {role} key")
        item["api_key"] = key
    return data


def save_config(root: Path, image: dict, vision: dict, secrets: dict, allow_fake_dns=False) -> None:
    local = root / ".local"
    require(not local.is_symlink(), "Private directory cannot be a symlink")
    local.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        local.chmod(0o700)
    for role in (image, vision):
        endpoint(role["base_url"])
        require(bool(role.get("model")), "Explicit model ID required")
    write_json(local / "secrets.json", secrets)
    write_json(local / "config.json", {"schema_version": 1, "image": image, "vision": vision,"allow_fake_dns":allow_fake_dns})
