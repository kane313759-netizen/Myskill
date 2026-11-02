#!/usr/bin/env python3
"""Offline test-log triage; the real test command exit status remains authoritative."""
from pathlib import Path
import argparse
import re

ZERO_FAILURE = re.compile(r"\b(?:0\s+(?:failed|failures?|errors?)|(?:failed|failures?|errors?)\s*[:=]\s*0)\b", re.I)
FAILURES = [
    re.compile(r"^\s*not ok\b", re.I),
    re.compile(r"\bAssertionError\b"),
    re.compile(r"\bTraceback \(most recent call last\)", re.I),
    re.compile(r"\bpanic\b", re.I),
    re.compile(r"\bFAILED\b", re.I),
    re.compile(r"\b[1-9]\d*\s+(?:failed|failures?|errors?)\b", re.I),
    re.compile(r"\b(?:failed|failures?|errors?)\s*[:=]\s*[1-9]\d*\b", re.I),
    re.compile(r"^\s*(?:---\s+)?FAIL(?:[\s:]|$)"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log")
    args = parser.parse_args()
    path = Path(args.log)
    if not path.is_file():
        parser.exit(1, f"Not a file: {path}\n")
    failures = []
    total = 0
    tail = ""
    continuing = False
    line_failed = False
    # readline(size) also bounds memory for a log containing one enormous line.
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for chunk in iter(lambda: handle.readline(65536), ""):
                joined = tail + chunk
                # Keep short failure tokens split at a chunk boundary visible;
                # a continuation must not invent a new physical line start.
                candidate = ZERO_FAILURE.sub("", ("_" if continuing else "") + joined)
                if not line_failed and any(pattern.search(candidate) for pattern in FAILURES):
                    total += 1
                    line_failed = True
                    if len(failures) < 40:
                        failures.append(joined.strip()[:1000])
                if chunk.endswith("\n"):
                    tail, continuing, line_failed = "", False, False
                else:
                    tail, continuing = joined[-256:], True
    except OSError as error:
        parser.exit(1, f"Cannot read log: {error}\n")
    print(f"FAILURE_LIKE_LINES\t{len(failures)}")
    for line in failures:
        print("-", line)
    if total > len(failures):
        print(f"NOTE\tadditional failure-like lines omitted: {total-len(failures)}")
    print("\nNOTE")
    print("- This helper is triage only; long physical lines are inspected in 65536-character chunks.")
    print("- Use the real test command exit status and framework summary as the baseline/pass-fail source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
