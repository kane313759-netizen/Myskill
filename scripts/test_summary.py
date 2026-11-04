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


def failure_like_lines(handle):
    """Inspect bounded windows, delaying suffix matches until their context arrives."""
    tail, from_start, line_failed = "", True, False

    def failed(text, at_start, final):
        candidate = ("" if at_start else "_") + text
        # Preserve match positions while masking zero-count phrases.
        candidate = ZERO_FAILURE.sub(lambda match: " " * len(match.group()), candidate)
        safe_end = len(candidate) if final else max(0, len(candidate) - 256)
        return any(match.end() <= safe_end for pattern in FAILURES
                   for match in pattern.finditer(candidate))

    # readline(size) also bounds memory for a log containing one enormous line.
    for chunk in iter(lambda: handle.readline(65536), ""):
        final = chunk.endswith("\n")
        if not line_failed:
            # Whitespace runs need no unbounded storage. This also preserves a
            # physical line's anchored prefix across any number of blank chunks.
            joined = re.sub(r"\s+", " ", tail + chunk)
            if failed(joined, from_start, final):
                line_failed = True
                yield joined.strip()[:1000]
            if not final:
                from_start = from_start and len(joined) <= 512
                tail = joined[-512:]
        if final:
            tail, from_start, line_failed = "", True, False
    if tail and not line_failed and failed(tail, from_start, True):
        yield tail.strip()[:1000]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log")
    args = parser.parse_args()
    path = Path(args.log)
    if not path.is_file():
        parser.exit(1, f"Not a file: {path}\n")
    failures = []
    total = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for excerpt in failure_like_lines(handle):
                total += 1
                if len(failures) < 40:
                    failures.append(excerpt)
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
