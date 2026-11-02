#!/usr/bin/env python3
"""Offline triage of a captured test log; framework-native exit status remains authoritative."""
from pathlib import Path
import argparse, re

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("log")
    args=ap.parse_args()
    path=Path(args.log)
    if not path.is_file(): raise SystemExit(f"Not a file: {path}")
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()

    # Avoid treating normal summaries such as "0 failed" / "0 errors" as failures.
    zero_failure=re.compile(r"\b0\s+(failed|failures?|errors?)\b",re.I)
    definite_fail=[
        re.compile(r"^\s*not ok\b",re.I),
        re.compile(r"\bAssertionError\b"),
        re.compile(r"\bTraceback \(most recent call last\)",re.I),
        re.compile(r"\bpanic\b",re.I),
        re.compile(r"\bFAILED\s+[^=]",re.I),
        re.compile(r"\b[1-9]\d*\s+(failed|failures?|errors?)\b",re.I),
    ]
    fail_lines=[]
    for line in lines:
        if zero_failure.search(line): continue
        if any(p.search(line) for p in definite_fail):
            if len(fail_lines)<40: fail_lines.append(line.strip())

    print(f"FAILURE_LIKE_LINES\t{len(fail_lines)}")
    for x in fail_lines: print("-",x)
    print("\nNOTE")
    print("- This helper is triage only.")
    print("- Use the real test command exit status and framework summary as the baseline/pass-fail source.")

if __name__=="__main__": main()
