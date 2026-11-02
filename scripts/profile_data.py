#!/usr/bin/env python3
"""Bounded offline profiler for explicit CSV/JSON/XLSX files. No directory recursion, no network."""
from __future__ import annotations
import argparse, csv, json, math, re
from collections import Counter
from pathlib import Path

ENCODINGS=("utf-8-sig","utf-8","cp949")
THOUSANDS=re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")

def is_blank(v):
    return v is None or (isinstance(v,str) and not v.strip())

def as_num(v):
    if v is None or isinstance(v,bool): return None
    s=str(v).strip()
    if not s: return None
    # Only remove commas when they unambiguously look like thousands separators.
    if "," in s:
        if THOUSANDS.fullmatch(s): s=s.replace(",","")
        else: return None
    try:
        x=float(s)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def choose_encoding(path: Path):
    sample=path.read_bytes()[:131072]
    for enc in ENCODINGS:
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError:
            pass
    raise UnicodeError(f"Could not decode {path} with {ENCODINGS}")

def iter_rows(path: Path, max_rows: int, max_json_bytes: int):
    if not path.exists(): raise FileNotFoundError(path)
    if path.is_dir(): raise IsADirectoryError(f"Pass explicit data files, not directories: {path}")
    ext=path.suffix.lower()
    if ext==".csv":
        enc=choose_encoding(path)
        with path.open("r",encoding=enc,newline="") as f:
            for i,row in enumerate(csv.DictReader(f)):
                if i>=max_rows: return
                yield row
        return
    if ext==".json":
        if path.stat().st_size>max_json_bytes:
            raise ValueError(f"JSON exceeds safe size limit ({max_json_bytes} bytes): {path}")
        enc=choose_encoding(path)
        data=json.loads(path.read_text(encoding=enc))
        if isinstance(data,list):
            seq=data
        elif isinstance(data,dict):
            seq=None
            for v in data.values():
                if isinstance(v,list) and all(isinstance(x,dict) for x in v):
                    seq=v; break
            if seq is None: seq=[data]
        else:
            seq=[{"value":data}]
        for i,x in enumerate(seq):
            if i>=max_rows: return
            yield x if isinstance(x,dict) else {"value":x}
        return
    if ext in {".xlsx",".xlsm"}:
        try: import openpyxl
        except ImportError: raise RuntimeError("XLSX requires openpyxl in this environment")
        wb=openpyxl.load_workbook(path,read_only=True,data_only=True)
        ws=wb.active
        it=ws.iter_rows(values_only=True)
        try: header_row=next(it)
        except StopIteration: return
        headers=[str(x) if x is not None else "" for x in header_row]
        for i,row in enumerate(it):
            if i>=max_rows: return
            yield dict(zip(headers,row))
        return
    raise ValueError(f"Unsupported extension: {path}")

def profile(path: Path, max_rows: int, max_json_bytes: int):
    count=0; cols=[]; blank=Counter(); nonblank=Counter(); nums={}; values={}; row_hashes=set(); dup=0
    for row in iter_rows(path,max_rows,max_json_bytes):
        count+=1
        for k in row:
            if k not in cols:
                cols.append(k); nums[k]=[]; values[k]=Counter()
        canonical=json.dumps(row,sort_keys=True,ensure_ascii=False,default=str)
        if canonical in row_hashes: dup+=1
        else: row_hashes.add(canonical)
        for c in cols:
            v=row.get(c)
            if is_blank(v): blank[c]+=1; continue
            nonblank[c]+=1
            if len(values[c])<20000 or str(v) in values[c]:
                values[c][str(v)]+=1
            n=as_num(v)
            if n is not None: nums[c].append(n)
    print(f"FILE\t{path}")
    print(f"SAMPLED_ROWS\t{count}\tMAX_ROWS={max_rows}")
    print(f"COLUMNS\t{len(cols)}\t"+" | ".join(cols))
    for c in cols:
        parts=[f"blank={blank[c]}",f"nonblank={nonblank[c]}",f"distinct_sample={len(values[c])}"]
        xs=nums[c]
        if xs:
            parts += [f"numeric_ratio={len(xs)/max(1,nonblank[c]):.3f}",f"min={min(xs):g}",f"max={max(xs):g}",f"avg={sum(xs)/len(xs):g}"]
        if values[c]: parts.append("top="+repr(values[c].most_common(3)))
        print("COL\t"+c+"\t"+"\t".join(parts))
    print(f"EXACT_DUPLICATE_ROWS_IN_SAMPLE\t{dup}")
    if count>=max_rows: print("NOTE\trow cap reached; statistics are a bounded sample")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("files",nargs="+",help="Explicit data files only; directories are rejected")
    ap.add_argument("--max-rows",type=int,default=50000)
    ap.add_argument("--max-json-bytes",type=int,default=50*1024*1024)
    args=ap.parse_args()
    for name in args.files:
        try: profile(Path(name),args.max_rows,args.max_json_bytes)
        except Exception as e:
            print(f"ERROR\t{name}\t{type(e).__name__}: {e}")

if __name__=="__main__": main()
