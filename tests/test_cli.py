import os
import subprocess
import sys
from pathlib import Path

from poster_agent.core import read_json


def run(*args,cwd,env=None):
    return subprocess.run([sys.executable,"-m","poster_agent",*args],cwd=cwd,env=env,
                          stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding="utf-8",timeout=20)


def test_clean_cli_doctor_requires_own_config(tmp_path):
    result=run("doctor",cwd=tmp_path)
    assert result.returncode==2 and '"provider_declared": false' in result.stdout
    assert "Traceback" not in result.stderr


def test_hidden_config_env_is_explicit_and_not_echoed(tmp_path):
    env=dict(os.environ,PP_IMAGE_KEY="fixture-not-a-real-key")
    result=run("configure","--provider","custom","--base-url","https://example.com/v1",
               "--vision-model","fixture","--from-env",cwd=tmp_path,env=env)
    assert result.returncode==0
    assert "fixture-not-a-real-key" not in result.stdout+result.stderr
    data=read_json(tmp_path/".local/secrets.json")
    assert data["image"]==data["vision"]
    assert run("doctor",cwd=tmp_path).returncode==0


def test_no_execute_stops_before_provider(job):
    result=run("run",str(job),"--max-calls","5",cwd=job.parent)
    assert result.returncode==2 and "paid APIs" in result.stdout


def test_non_tty_config_does_not_read_visible_key(tmp_path):
    result=run("configure","--vision-model","fixture",cwd=tmp_path)
    assert result.returncode==2 and "private terminal" in result.stdout
    assert not (tmp_path/".local/secrets.json").exists()


def test_chinese_cli_output_is_utf8_with_legacy_encoding(tmp_path):
    env=dict(os.environ,PP_IMAGE_KEY="fixture-not-a-real-key",PYTHONIOENCODING="cp1252")
    result=run("configure","--vision-model","中文视觉模型","--from-env",cwd=tmp_path,env=env)
    assert result.returncode==0
    result=run("doctor",cwd=tmp_path,env=env)
    assert result.returncode==0 and "中文视觉模型" in result.stdout
