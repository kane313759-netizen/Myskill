#!/usr/bin/env python3
"""Offline environment/project inventory."""
from pathlib import Path
import json, re

root=Path(".")
names=[
 "Dockerfile","docker-compose.yml","docker-compose.yaml","compose.yml","compose.yaml",
 "package.json","requirements.txt","pyproject.toml","Pipfile","poetry.lock",
 ".env.example",".env.sample","Makefile","README.md"
]
print("PROJECT", root.resolve())
for n in names:
    p=root/n
    if not p.exists(): continue
    print("\nFOUND", n)
    try:
        text=p.read_text(encoding="utf-8",errors="replace")
    except Exception:
        continue
    if n=="package.json":
        try:
            j=json.loads(text)
            print("scripts:", j.get("scripts",{}))
            print("dependencies:", sorted((j.get("dependencies") or {}).keys()))
        except Exception: pass
    elif n.startswith("Dockerfile"):
        for line in text.splitlines():
            if re.match(r"^(FROM|EXPOSE|CMD|ENTRYPOINT|VOLUME|WORKDIR)\b",line.strip(),re.I):
                print(line.strip())
    elif "compose" in n:
        for line in text.splitlines():
            if re.search(r"services:|ports:|volumes:|image:|build:",line):
                print(line.rstrip())
    else:
        print(text[:3000])

print("\nBOUNDARY QUESTIONS")
print("- What starts the application?")
print("- Which port/process serves it?")
print("- Where is persistent data stored?")
print("- Which environment variables are secrets/config?")
print("- Which external systems are called?")
print("- What disappears when the process/container restarts?")
