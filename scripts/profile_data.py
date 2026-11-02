#!/usr/bin/env python3
"""Generic local data profiler for hackathon inputs. No network use."""
from __future__ import annotations
import argparse, csv, json, math
from collections import Counter
from pathlib import Path

def is_blank(v):
    return v is None or (isinstance(v, str) and not v.strip())

def as_num(v):
    if v is None or isinstance(v, bool): return None
    try:
        s=str(v).strip().replace(",","")
        if not s: return None
        x=float(s)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def rows_from(path: Path):
    ext=path.suffix.lower()
    if ext==".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    if ext==".json":
        data=json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [x if isinstance(x,dict) else {"value":x} for x in data]
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v,list) and all(isinstance(x,dict) for x in v):
                    return v
            return [data]
    if ext in {".xlsx",".xlsm"}:
        try:
            import openpyxl
        except ImportError:
            raise SystemExit("XLSX needs openpyxl in this environment.")
        wb=openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws=wb.active
        it=ws.iter_rows(values_only=True)
        headers=[str(x) if x is not None else "" for x in next(it)]
        return [dict(zip(headers,row)) for row in it]
    raise SystemExit(f"Unsupported: {path}")

def profile(path: Path):
    rows=rows_from(path)
    cols=[]
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    print(f"FILE\t{path}")
    print(f"ROWS\t{len(rows)}")
    print(f"COLUMNS\t{len(cols)}\t" + " | ".join(cols))
    for c in cols:
        vals=[r.get(c) for r in rows]
        non=[v for v in vals if not is_blank(v)]
        uniq=Counter(str(v) for v in non)
        nums=[n for v in non if (n:=as_num(v)) is not None]
        parts=[f"blank={len(vals)-len(non)}", f"distinct={len(uniq)}"]
        if nums:
            parts += [f"min={min(nums):g}", f"max={max(nums):g}", f"avg={sum(nums)/len(nums):g}"]
        common=uniq.most_common(3)
        if common: parts.append("top="+repr(common))
        print("COL\t"+c+"\t"+"\t".join(parts))
    exact=[json.dumps(r,sort_keys=True,ensure_ascii=False,default=str) for r in rows]
    dups=len(exact)-len(set(exact))
    print(f"EXACT_DUPLICATE_ROWS\t{dups}")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    args=ap.parse_args()
    for name in args.files:
        profile(Path(name))
