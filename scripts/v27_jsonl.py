"""Bounded streaming JSONL conversion for the additive auditor."""
import csv
import gzip
import hashlib
import json
import tempfile
import time
from pathlib import Path

def scan_jsonl(path, plan, spec, io, scan_csv):
    started=time.monotonic(); budget=plan.get('max_scan_seconds',300)
    byte_limit=plan.get('max_scan_bytes',plan.get('max_file_bytes',2*1024**3))
    if type(budget) not in (int,float) or not 0<budget<=900: raise ValueError('max_scan_seconds must be 0..900')
    if type(byte_limit) is not int or not 0<byte_limit<=2*1024**3: raise ValueError('max_scan_bytes must be 1..2GiB')
    initial=path.stat(); digest=hashlib.sha256()
    full_hash=None
    if initial.st_size<=byte_limit:
        with path.open('rb') as raw:
            for block in iter(lambda:raw.read(1024*1024),b''):
                digest.update(block)
                if time.monotonic()-started>budget: break
            else: full_hash=digest.hexdigest()
    opener=gzip.open if path.name.lower().endswith('.gz') else open
    columns={}; broken=0; size=0; complete=True; reason=None
    def reject_constant(value): raise ValueError('nonfinite JSON value')
    with tempfile.TemporaryDirectory(prefix='v27-jsonl-') as directory:
        spool=Path(directory)/'rows.jsonl'; table=Path(directory)/'rows.csv'
        with opener(path,'rb') as source, spool.open('w',encoding='utf8') as target:
            while True:
                line=source.readline(4*1024**2+1)
                if not line: break
                size+=len(line)
                if len(line)>4*1024**2 or size>byte_limit or time.monotonic()-started>budget:
                    complete=False;reason='JSONL byte, line or time budget exceeded';break
                try:
                    row=json.loads(line.decode(spec.get('encoding','utf-8-sig')),parse_constant=reject_constant)
                    if not isinstance(row,dict): raise ValueError('JSONL row must be an object')
                    columns.update(dict.fromkeys(row))
                    target.write(json.dumps(row,ensure_ascii=True,allow_nan=False)+'\n')
                except (ValueError,UnicodeError): broken+=1
        if not columns:
            return {'rows':0,'sample':[],'bytes':size,'sha256':full_hash,'complete':complete and not broken,
                    'reason':reason or ('malformed JSONL lines' if broken else None),'broken_lines':broken,
                    'profile':{},'analysis_limits':[]}
        with spool.open(encoding='utf8') as source, table.open('w',encoding='utf8',newline='') as target:
            writer=csv.DictWriter(target,fieldnames=list(columns));writer.writeheader()
            for line in source:
                row=json.loads(line)
                writer.writerow({k:json.dumps(v,ensure_ascii=True,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()})
        remaining=budget-(time.monotonic()-started)
        if remaining<=0: complete=False;reason='JSONL time budget exceeded'
        result=scan_csv(table,dict(plan,max_scan_seconds=max(.001,remaining)),dict(spec,encoding='utf8'),io)
        result.update(sha256=full_hash,bytes=size,broken_lines=broken)
        result['complete']=result['complete'] and complete and not broken
        result['reason']=reason or ('malformed JSONL lines' if broken else result['reason'])
        result['profile']['complete_rows']=result['complete']
        if (initial.st_size,initial.st_mtime_ns)!=(path.stat().st_size,path.stat().st_mtime_ns): raise ValueError('provided file changed during audit')
        return result
