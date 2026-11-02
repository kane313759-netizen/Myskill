#!/usr/bin/env python3
"""Small offline test/log summarizer."""
from pathlib import Path
import argparse, re

ap=argparse.ArgumentParser()
ap.add_argument("log")
args=ap.parse_args()
text=Path(args.log).read_text(encoding="utf-8",errors="replace")
lines=text.splitlines()

patterns={
 "pass": re.compile(r"\b(pass|passed|ok)\b",re.I),
 "fail": re.compile(r"\b(fail|failed|error|not ok)\b",re.I),
 "skip": re.compile(r"\b(skip|skipped|xfail)\b",re.I),
}
counts={k:0 for k in patterns}
fail_lines=[]
for line in lines:
    if patterns["fail"].search(line):
        counts["fail"]+=1
        if len(fail_lines)<30: fail_lines.append(line.strip())
    elif patterns["skip"].search(line): counts["skip"]+=1
    elif patterns["pass"].search(line): counts["pass"]+=1

print("SUMMARY", counts)
if fail_lines:
    print("\nFAILURE-LIKE LINES")
    for x in fail_lines: print("-",x)
print("\nNOTE: pattern counts are triage only; inspect the framework's real final summary.")
