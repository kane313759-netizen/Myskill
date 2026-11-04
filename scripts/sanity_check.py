#!/usr/bin/env python3
"""Bounded numeric sanity summary. Reports scale without inventing thresholds."""
from __future__ import annotations

import argparse
import sys

# Installed helper use must not create files outside the runtime-note area.
sys.dont_write_bytecode = True
from pathlib import Path

from data_io import (add_read_options, as_num, choose_encoding, id_like, is_blank,
                     leading_zero_id, list_sheets, mean, read_options, tables)

# Preserve the small helper interface used by existing local callers.
num = as_num


def load(path, max_rows, max_json_bytes, **options):
    selected = list(tables(path, max_rows, max_json_bytes, **options))
    if len(selected) != 1:
        raise ValueError("load() requires one table; choose --sheet NAME")
    return selected[0][1]


def pct(sorted_values, fraction):
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * fraction)))
    return sorted_values[index]


def summarize(rows, args, sheet=None):
    if sheet is not None:
        print(f"SHEET\t{sheet}")
    print(f"SAMPLED_ROWS\t{len(rows)}\tMAX_ROWS={args.max_rows}")
    for column in sorted({key for row in rows for key in row}):
        values = [row.get(column) for row in rows if not is_blank(row.get(column), args.null_token)]
        if not args.include_id_like and (id_like(column) or any(leading_zero_id(value) for value in values)):
            print(f"SKIP_ID_LIKE\t{column}")
            continue
        numbers = sorted(number for value in values if (number := num(value)) is not None)
        if not numbers or len(numbers) / max(1, len(values)) < 0.8:
            continue
        print(f"NUM\t{column}\tcount={len(numbers)}\tmin={numbers[0]:g}\tp50={pct(numbers,.5):g}"
              f"\tp95={pct(numbers,.95):g}\tmax={numbers[-1]:g}\tavg={mean(numbers):g}")
    if len(rows) >= args.max_rows:
        print("NOTE\trow cap reached; this is a bounded sample")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    add_read_options(parser)
    args = parser.parse_args()
    try:
        if args.list_sheets:
            for sheet in list_sheets(Path(args.file)):
                print(f"SHEET\t{sheet}")
            return 0
        for sheet, rows in tables(Path(args.file), args.max_rows, args.max_json_bytes, **read_options(args)):
            summarize(rows, args, sheet)
    except Exception as error:
        parser.exit(1, f"{type(error).__name__}: {error}\n")
    print("\nINTERPRETATION RULES")
    print("- Numeric scale summaries use approximate finite floating-point values.")
    print("- These are scale summaries, not automatic anomaly verdicts.")
    print("- Apply only task-relevant metrics from the selected playbook.")
    print("- Check worst-case values when the grading/contract makes them relevant.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
