#!/usr/bin/env python3
"""Generic numeric sanity summary. Inspect extremes; it does not invent thresholds."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path

def load(path):
    if path.suffix.lower()==".csv":
        with path.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data,list): return [x for x in data if isinstance(x,dict)]
    if isinstance(data,dict):
        for v in data.values():
            if isinstance(v,list) and all(isinstance(x,dict) for x in v): return v
        return [data]
    return []

def num(v):
    try:
        x=float(str(v).strip().replace(",",""))
        return x if math.isfinite(x) else None
    except Exception: return None

def pct(xs,p):
    if not xs:return None
    ys=sorted(xs)
    i=min(len(ys)-1,max(0,round((len(ys)-1)*p)))
    return ys[i]

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("file")
    args=ap.parse_args()
    path=Path(args.file); rows=load(path)
    cols=sorted({k for r in rows for k in r})
    print(f"ROWS\t{len(rows)}")
    for c in cols:
        xs=[n for r in rows if (n:=num(r.get(c))) is not None]
        if not xs: continue
        print(f"NUM\t{c}\tcount={len(xs)}\tmin={min(xs):g}\tp50={pct(xs,.5):g}\tp95={pct(xs,.95):g}\tmax={max(xs):g}\tavg={sum(xs)/len(xs):g}")
    print("\nREVIEW QUESTIONS")
    print("- Which resource/count can grow without limit?")
    print("- Which max value is operationally absurd even if the average looks fine?")
    print("- Are there zero/negative/impossible values?")
    print("- Is burden concentrated on a small subset?")
    print("- Are unassigned/unprocessed items hidden by aggregate metrics?")
