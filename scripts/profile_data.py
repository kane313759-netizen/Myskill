#!/usr/bin/env python3
"""Bounded offline profiler for explicit CSV/JSON/XLSX files. No network."""
from __future__ import annotations

import argparse
import sys

# Installed helper use must not create files outside the runtime-note area.
sys.dont_write_bytecode = True
import hashlib
import json
from collections import Counter
from pathlib import Path

from data_io import (add_read_options, as_num, choose_encoding, id_like, is_blank,
                     leading_zero_id, list_sheets, mean, positive_int, read_options, tables)


def iter_rows(path, max_rows, max_json_bytes, **options):
    for _, rows in tables(path, max_rows, max_json_bytes, **options):
        yield from rows


def _profile_rows(path, rows, max_rows, *, sheet=None, null_tokens=(), include_id_like=False):
    count = 0
    cols = []
    blank, nonblank = Counter(), Counter()
    nums, values, zero_ids = {}, {}, set()
    row_hashes = set()
    dup = 0
    distinct_capped = set()
    for row in rows:
        count += 1
        for key in row:
            if key not in nums:
                cols.append(key)
                nums[key], values[key] = [], Counter()
                blank[key] = count - 1
        canonical = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
        digest = hashlib.sha256(canonical.encode("utf-8")).digest()
        if digest in row_hashes:
            dup += 1
        else:
            row_hashes.add(digest)
        for column in cols:
            value = row.get(column)
            if is_blank(value, null_tokens):
                blank[column] += 1
                continue
            nonblank[column] += 1
            text = str(value)
            if len(values[column]) < 20000 or text in values[column]:
                values[column][text] += 1
            else:
                distinct_capped.add(column)
            if leading_zero_id(value):
                zero_ids.add(column)
            number = as_num(value)
            if number is not None:
                nums[column].append(number)
    print(f"FILE\t{path}")
    if sheet is not None:
        print(f"SHEET\t{sheet}")
    print(f"SAMPLED_ROWS\t{count}\tMAX_ROWS={max_rows}")
    print(f"COLUMNS\t{len(cols)}\t" + " | ".join(cols))
    for column in cols:
        parts = [f"blank={blank[column]}", f"nonblank={nonblank[column]}", f"distinct_sample={len(values[column])}"]
        numbers = nums[column]
        if not include_id_like and (id_like(column) or column in zero_ids):
            parts.append("numeric_skipped=id_like")
        elif numbers:
            parts += [f"numeric_ratio={len(numbers)/max(1,nonblank[column]):.3f}",
                      f"min={min(numbers):g}", f"max={max(numbers):g}", f"avg={mean(numbers):g}"]
        if values[column]:
            top = [(text if len(text) <= 160 else text[:157] + "...", n) for text, n in values[column].most_common(3)]
            parts.append("top=" + repr(top))
        if column in distinct_capped:
            parts.append("distinct_cap_reached=true; top counts cover retained values only")
        print("COL\t" + column + "\t" + "\t".join(parts))
    print(f"EXACT_DUPLICATE_ROWS_IN_SAMPLE\t{dup}")
    if count >= max_rows:
        print("NOTE\trow cap reached; statistics are a bounded sample")


def profile(path, max_rows, max_json_bytes, *, null_tokens=(), include_id_like=False, **options):
    for sheet, rows in tables(path, max_rows, max_json_bytes, **options):
        _profile_rows(path, rows, max_rows, sheet=sheet, null_tokens=null_tokens, include_id_like=include_id_like)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Explicit data files only; directories are rejected")
    parser.add_argument("--max-files", type=positive_int, default=32)
    add_read_options(parser)
    args = parser.parse_args()
    if len(args.files) > args.max_files:
        parser.error(f"file count exceeds --max-files {args.max_files}")
    failed = False
    for name in args.files:
        try:
            if args.list_sheets:
                for sheet in list_sheets(Path(name)):
                    print(f"FILE\t{name}\tSHEET\t{sheet}")
            else:
                profile(Path(name), args.max_rows, args.max_json_bytes, null_tokens=args.null_token,
                        include_id_like=args.include_id_like, **read_options(args))
        except Exception as error:
            failed = True
            print(f"ERROR\t{name}\t{type(error).__name__}: {error}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
