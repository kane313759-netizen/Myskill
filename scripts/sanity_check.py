#!/usr/bin/env python3
"""Bounded numeric sanity summary for explicit result files. It reports scale; it does not invent thresholds."""
from __future__ import annotations
import argparse, csv, json, math, re
from pathlib import Path

ENCODINGS=("utf-8-sig","utf-8","cp949")
THOUSANDS=re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
ID_HINT=re.compile(r"(^id$|(^|[_\- ])id($|[_\- ])|code|zip|postal|phone|account|customer|employee|invoice|order|번호|코드)",re.I)

def choose_encoding(path):
    sample=path.read_bytes()[:131072]
    for enc in ENCODINGS:
        try: sample.decode(enc); return enc
        except UnicodeDecodeError: pass
    raise UnicodeError(f"Could not decode with {ENCODINGS}")

def num(v):
    if v is None or isinstance(v,bool): return None
    s=str(v).strip()
    if not s: return None
    if "," in s:
        if THOUSANDS.fullmatch(s): s=s.replace(",","")
        else: return None
    try:
        x=float(s); return x if math.isfinite(x) else None
    except Exception: return None

def load(path,max_rows,max_json_bytes):
    if path.is_dir(): raise IsADirectoryError("Pass one explicit CSV/JSON result file, not a directory")
    ext=path.suffix.lower()
    if ext==".csv":
        enc=choose_encoding(path); out=[]
        with path.open("r",encoding=enc,newline="") as f:
            for i,row in enumerate(csv.DictReader(f)):
                if i>=max_rows: break
                out.append(row)
        return out
    if ext==".json":
        if path.stat().st_size>max_json_bytes: raise ValueError("JSON exceeds safe size limit")
        data=json.loads(path.read_text(encoding=choose_encoding(path)))
        if isinstance(data,list): seq=[x for x in data if isinstance(x,dict)]
        elif isinstance(data,dict):
            seq=next((v for v in data.values() if isinstance(v,list) and all(isinstance(x,dict) for x in v)),[data])
        else: seq=[]
        return seq[:max_rows]
    raise ValueError("sanity_check supports CSV/JSON result files")

def pct(xs,p):
    ys=sorted(xs); idx=min(len(ys)-1,max(0,round((len(ys)-1)*p))); return ys[idx]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--max-rows",type=int,default=50000)
    ap.add_argument("--max-json-bytes",type=int,default=50*1024*1024)
    ap.add_argument("--include-id-like",action="store_true")
    args=ap.parse_args()
    path=Path(args.file)
    try: rows=load(path,args.max_rows,args.max_json_bytes)
    except Exception as e: raise SystemExit(f"{type(e).__name__}: {e}")
    cols=sorted({k for r in rows for k in r})
    print(f"SAMPLED_ROWS\t{len(rows)}\tMAX_ROWS={args.max_rows}")
    for c in cols:
        if ID_HINT.search(c) and not args.include_id_like:
            print(f"SKIP_ID_LIKE\t{c}")
            continue
        nonblank=[r.get(c) for r in rows if r.get(c) not in (None,"")]
        xs=[n for v in nonblank if (n:=num(v)) is not None]
        if not xs or len(xs)/max(1,len(nonblank))<0.8: continue
        print(f"NUM\t{c}\tcount={len(xs)}\tmin={min(xs):g}\tp50={pct(xs,.5):g}\tp95={pct(xs,.95):g}\tmax={max(xs):g}\tavg={sum(xs)/len(xs):g}")
    print("\nINTERPRETATION RULES")
    print("- These are scale summaries, not automatic anomaly verdicts.")
    print("- Apply only task-relevant metrics from the selected playbook.")
    print("- Check worst-case values when the grading/contract makes them relevant.")
    if len(rows)>=args.max_rows: print("- Row cap reached; this is a bounded sample.")

if __name__=="__main__": main()
