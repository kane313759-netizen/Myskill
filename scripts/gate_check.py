#!/usr/bin/env python3
"""Fail closed until CP1 intake/spec gate is explicitly complete."""
from pathlib import Path
import re, sys

kit=Path(__file__).resolve().parents[1]
state=kit/"run"/"STATE.md"
if not state.is_file():
    raise SystemExit("GATE FAIL: run/STATE.md missing")
text=state.read_text(encoding="utf-8",errors="replace")

required={
    "grader_contract": {"RECORDED","UNKNOWN_AFTER_INSPECTION"},
    "baseline": {"RECORDED","UNAVAILABLE_WITH_REASON"},
    "immutable_inventory": {"RECORDED"},
    "cp1_constraint_red": {"DONE"},
    "constraint_gate": {"CLOSED"},
}
bad=[]
for key,allowed in required.items():
    m=re.search(rf"(?im)^-?\s*{re.escape(key)}\s*:\s*([^\n#]+)",text)
    value=m.group(1).strip() if m else "<missing>"
    if value not in allowed:
        bad.append(f"{key}={value}; expected one of {sorted(allowed)}")
if bad:
    print("GATE FAIL")
    for x in bad: print("-",x)
    sys.exit(2)
print("GATE OK: CP1 intake/spec gate is recorded complete")
