"""Local, bounded readers shared by the data helpers. No network access."""
from __future__ import annotations

import argparse
import codecs
import csv
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path

ENCODINGS = ("utf-8-sig", "cp949")
SAMPLE_BYTES = 131072
THOUSANDS = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
LEADING_ZERO = re.compile(r"^[+-]?0\d+$")
ID_TOKENS = {"id", "ids", "code", "zip", "postal", "phone", "account", "customer", "employee", "invoice", "order", "번호", "코드"}


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def is_blank(value, null_tokens=()):
    return value is None or (isinstance(value, str) and (not value.strip() or value.strip() in null_tokens))


def as_num(value):
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if "," in text:
        if not THOUSANDS.fullmatch(text):
            return None
        text = text.replace(",", "")
    try:
        number = float(text)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError, OverflowError):
        return None


def id_like(name):
    """Match identifier suffixes, never substrings in metric names."""
    tokens = re.split(r"[_\-\s]+", name.casefold())
    return tokens[-1] in ID_TOKENS or name.endswith(("번호", "코드"))


def leading_zero_id(value):
    return isinstance(value, str) and bool(LEADING_ZERO.fullmatch(value.strip()))


def mean(numbers):
    """Keep finite input averages finite even when their unscaled sum overflows."""
    scale = max(abs(number) for number in numbers)
    return (math.fsum(number / scale for number in numbers) / len(numbers)) * scale if scale else 0.0


def choose_encoding(path, encoding=None):
    if encoding:
        codecs.lookup(encoding)
        return encoding
    with Path(path).open("rb") as handle:
        sample = handle.read(SAMPLE_BYTES)
    for candidate in ENCODINGS:
        try:
            # A multibyte character may continue beyond the sample boundary.
            codecs.getincrementaldecoder(candidate)(errors="strict").decode(sample, final=False)
            return candidate
        except UnicodeDecodeError:
            continue
    raise UnicodeError("Cannot detect encoding; pass --encoding explicitly")


def _encodings(path, encoding):
    if encoding:
        return [choose_encoding(path, encoding)]
    preferred = choose_encoding(path)
    return [preferred] + [candidate for candidate in ENCODINGS if candidate != preferred]


def _headers(values):
    headers = [str(value) if value is not None else "" for value in values]
    if any(not header.strip() for header in headers):
        raise ValueError("Empty column header; provide a table with explicit column names")
    duplicates = [key for key, count in Counter(headers).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate column headers: {duplicates}")
    return headers


def _csv_rows(path, max_rows, encoding):
    failure = None
    for candidate in _encodings(path, encoding):
        try:
            with path.open("r", encoding=candidate, newline="") as handle:
                reader = csv.reader(handle, strict=True)
                first = next(reader, None)
                if first is None:
                    return []
                headers = _headers(first)
                rows = []
                for values in reader:
                    if not values:
                        continue
                    if len(values) != len(headers):
                        raise ValueError(f"CSV line {reader.line_num}: expected {len(headers)} fields, got {len(values)}")
                    rows.append(dict(zip(headers, values)))
                    if len(rows) >= max_rows:
                        break
                return rows
        except UnicodeDecodeError as error:
            # Retry the entire bounded sample; never mix or duplicate rows.
            failure = error
    raise UnicodeError(f"Cannot decode sampled CSV; pass --encoding explicitly ({failure})")


def _json_path(data, selection):
    if selection == "":
        return data
    parts = (selection[1:].split("/") if selection.startswith("/") else selection.split("."))
    current = data
    for part in parts:
        if selection.startswith("/"):
            part = part.replace("~1", "/").replace("~0", "~")
        try:
            current = current[int(part)] if isinstance(current, list) else current[part]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ValueError(f"JSON records path not found: {selection!r}") from error
    return current


def _json_rows(path, max_rows, max_json_bytes, encoding, records_key):
    if path.stat().st_size > max_json_bytes:
        raise ValueError(f"JSON exceeds safe size limit ({max_json_bytes} bytes)")
    with path.open("rb") as handle:
        raw = handle.read(max_json_bytes + 1)
    if len(raw) > max_json_bytes:
        raise ValueError(f"JSON exceeds safe size limit ({max_json_bytes} bytes)")
    for candidate in _encodings(path, encoding):
        try:
            data = json.loads(raw.decode(candidate))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeError("Cannot decode JSON; pass --encoding explicitly")
    if records_key is not None:
        data = _json_path(data, records_key)
    elif isinstance(data, dict):
        candidates = [(key, value) for key, value in data.items()
                      if isinstance(value, list) and value and all(isinstance(item, dict) for item in value)]
        if len(candidates) > 1:
            paths = ["/" + key.replace("~", "~0").replace("/", "~1") for key, _ in candidates]
            raise ValueError(f"Ambiguous JSON record arrays {paths}; choose --records-key PATH")
        if candidates:
            data = candidates[0][1]
    sequence = data if isinstance(data, list) else [data]
    return [item if isinstance(item, dict) else {"value": item} for item in itertools.islice(sequence, max_rows)]


def _open_workbook(path):
    try:
        import openpyxl
    except ImportError as error:
        raise RuntimeError("XLSX requires openpyxl in this environment") from error
    return openpyxl.load_workbook(path, read_only=True, data_only=True)


def list_sheets(path):
    workbook = _open_workbook(path)
    try:
        return workbook.sheetnames
    finally:
        workbook.close()


def tables(path, max_rows, max_json_bytes, *, encoding=None, records_key=None, sheet=None, all_sheets=False):
    """Yield (sheet name or None, bounded list of rows), closing file handles."""
    path = Path(path)
    if max_rows <= 0 or max_json_bytes <= 0:
        raise ValueError("row and JSON byte limits must be positive")
    if not path.is_file():
        raise ValueError(f"Pass an explicit existing data file: {path}")
    extension = path.suffix.lower()
    if extension == ".csv":
        yield None, _csv_rows(path, max_rows, encoding)
    elif extension == ".json":
        yield None, _json_rows(path, max_rows, max_json_bytes, encoding, records_key)
    elif extension in {".xlsx", ".xlsm"}:
        workbook = _open_workbook(path)
        try:
            if sheet is not None:
                if sheet not in workbook.sheetnames:
                    raise ValueError(f"Unknown sheet {sheet!r}; available: {workbook.sheetnames}")
                selected = [sheet]
            elif all_sheets or len(workbook.sheetnames) == 1:
                selected = workbook.sheetnames
            else:
                raise ValueError(f"Multiple sheets {workbook.sheetnames}; use --sheet NAME, --all-sheets, or --list-sheets")
            for name in selected:
                iterator = workbook[name].iter_rows(values_only=True)
                first = next(iterator, None)
                if first is None:
                    yield name, []
                    continue
                headers = _headers(first)
                rows = [dict(zip(headers, values)) for values in itertools.islice(iterator, max_rows)]
                yield name, rows
        finally:
            workbook.close()
    else:
        raise ValueError(f"Unsupported extension: {path}")


def add_read_options(parser):
    parser.add_argument("--max-rows", type=positive_int, default=50000)
    parser.add_argument("--max-json-bytes", type=positive_int, default=50 * 1024 * 1024)
    parser.add_argument("--encoding", help="Explicit text encoding; otherwise UTF-8/CP949 fallback")
    parser.add_argument("--records-key", help="JSON records path: dot-separated keys or JSON Pointer (/data/items)")
    parser.add_argument("--null-token", action="append", default=[], help="Additional exact, case-sensitive missing-value token (repeatable)")
    parser.add_argument("--include-id-like", action="store_true", help="Include numeric summaries for identifier-like columns")
    sheets = parser.add_mutually_exclusive_group()
    sheets.add_argument("--sheet", help="Explicit workbook sheet name")
    sheets.add_argument("--all-sheets", action="store_true", help="Summarize workbook sheets separately")
    sheets.add_argument("--list-sheets", action="store_true", help="List workbook sheet names without profiling")


def read_options(args):
    return dict(encoding=args.encoding, records_key=args.records_key, sheet=args.sheet, all_sheets=args.all_sheets)
