"""Read-only distribution checks; prints file names, never matched secret values."""
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    problems=[]
    version=(ROOT/"VERSION").read_text().strip()
    pyproject=(ROOT/"pyproject.toml").read_text()
    if f'version = "{version}"' not in pyproject:problems.append("pyproject version mismatch")
    for f in ["README.md","CHANGELOG.md","START_HERE.md","docs/IMPLEMENTATION-STATUS.md"]:
        if version not in (ROOT/f).read_text():problems.append(f+": version missing")
    listed=subprocess.run(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT,
                          check=True,capture_output=True).stdout.decode().split("\0")
    files=sorted(set(x for x in listed if x))
    forbidden=(".local/","projects/","output/",".venv/")
    secret=re.compile(r"(?:sk-[A-Za-z0-9_-]{24,}|ghp_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{30,})")
    links=0
    for name in files:
        if name.startswith(forbidden) or Path(name).name.startswith(".env") or name.endswith((".ttf",".otf",".ttc",".sqlite")):
            problems.append(name+": private/non-distributable file")
        path=ROOT/name
        if path.is_symlink():problems.append(name+": symlink");continue
        if not path.is_file():continue
        try: text=path.read_text()
        except UnicodeError:problems.append(name+": unexpected binary");continue
        if secret.search(text):problems.append(name+": potential secret detected")
        if re.search("/"+r"(?:Users|home)/[a-zA-Z0-9._-]+/",text):problems.append(name+": user-specific absolute path")
        if name.endswith(".json"):
            try:json.loads(text)
            except ValueError:problems.append(name+": invalid JSON")
        if name.endswith(".md"):
            if sum(x.startswith("```") for x in text.splitlines())%2:problems.append(name+": unmatched fence")
            for target in re.findall(r"\]\(([^)]+)\)",text):
                if target.startswith(("http:","https:","#")):continue
                links+=1
                if not (path.parent/target.split("#")[0]).exists():problems.append(name+": broken local link")
    print(json.dumps({"version":version,"files_checked":len(files),"local_links_checked":links,
                      "status":"FAIL" if problems else "PASS","issues":problems},ensure_ascii=False,indent=2))
    return bool(problems)

if __name__=="__main__":raise SystemExit(main())
