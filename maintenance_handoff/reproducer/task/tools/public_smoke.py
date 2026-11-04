#!/usr/bin/env python3
"""Fixed-denominator public sample smoke. Standard library, local CLI only."""
import argparse
import hashlib
import json
import math
import os
import signal
import sqlite3
import stat
import subprocess
import sys
import time
from pathlib import Path

CAP=64*1024*1024
ARTIFACTS=('index.sqlite','stats.json','rejections.json','manifest.json')
CHECKS=('build_complete','manifest_shape','stats_shape','rejections_shape','sqlite_schema','artifact_hashes','search_complete','public_first12','verify_readonly','resume_unchanged')

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def parse(raw):
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError('duplicate JSON key')
            value[key]=item
        return value
    def constant(value):raise ValueError('non-finite JSON')
    def floating(value):
        result=float(value)
        if not math.isfinite(result):raise ValueError('non-finite JSON')
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant,parse_float=floating)

def regular(path,cap=CAP):
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size>cap:raise ValueError('not a bounded regular file: '+str(path))
    return info

def read(path,cap=CAP):
    regular(path,cap);fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('file changed type')
        with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(cap+1)
    finally:os.close(fd)
    if len(raw)>cap:raise ValueError('file exceeds bounded read')
    return raw

def sha(path):
    regular(path,2*1024**3);result=hashlib.sha256()
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()

def snapshot(index):
    return {name:(sha(index/name),regular(index/name,2*1024**3).st_mtime_ns) for name in ARTIFACTS}

def json_file(path):
    raw=read(path);value=parse(raw)
    if raw!=canonical(value)+b'\n':raise ValueError('noncanonical JSON file')
    return value

def integer(value):return type(value) is int and value>=0
def fields(value,keys):return isinstance(value,dict) and set(value)==set(keys)

def run(candidate,args,phase,work):
    cwd=work/'phases'/phase;cwd.mkdir(parents=True)
    tmp=cwd/'tmp';tmp.mkdir();env=os.environ.copy();env['TMPDIR']=str(tmp)
    result={'argv':[sys.executable,str(candidate),*map(str,args)],'cwd':str(cwd),'returncode':None,'timed_out':False,'output_limited':False}
    start=time.monotonic()
    stdout=cwd/'stdout.log';stderr=cwd/'stderr.log'
    with stdout.open('wb') as out,stderr.open('wb') as err:
        process=subprocess.Popen(result['argv'],cwd=cwd,env=env,stdout=out,stderr=err,start_new_session=True)
        while process.poll() is None:
            if time.monotonic()-start>90:
                result['timed_out']=True;os.killpg(process.pid,signal.SIGKILL);break
            if stdout.stat().st_size+stderr.stat().st_size>2*1024**3:
                result['output_limited']=True;os.killpg(process.pid,signal.SIGKILL);break
            time.sleep(.05)
        result['returncode']=process.wait()
        # Clean surviving descendants in the candidate process group.
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    result['seconds']=round(time.monotonic()-start,6)
    result['stdout']=str(stdout);result['stderr']=str(stderr)
    return result

def success(result):return result and result['returncode']==0 and not result['timed_out'] and not result['output_limited']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',required=True);parser.add_argument('--task',required=True);parser.add_argument('--work',required=True)
    args=parser.parse_args();candidate=Path(args.candidate);task=Path(args.task).absolute();work=Path(args.work).absolute()
    checks={key:{'status':'UNRUN','detail':'prerequisite did not complete'} for key in CHECKS};phases={}
    def check(name,fn):
        try:
            if fn() is False:raise ValueError('check returned false')
            checks[name]={'status':'PASS','detail':'observed'};return True
        except (OSError,ValueError,TypeError,KeyError,sqlite3.Error) as exc:
            checks[name]={'status':'FAIL','detail':str(exc)};return False
    try:
        if not candidate.is_absolute():raise ValueError('--candidate must be absolute')
        regular(candidate,4*1024**2)
        if task.is_symlink() or not task.is_dir():raise ValueError('unsafe task root')
        for path in (work,*work.parents):
            if path.is_symlink():raise ValueError('symlink work path')
        if work==task or task in work.parents or work in task.parents or candidate==work or work in candidate.parents:raise ValueError('work must be disjoint from task and candidate')
        if work.exists() and (not work.is_dir() or any(work.iterdir())):raise ValueError('--work must be new or empty')
        work.mkdir(parents=True,exist_ok=True);index=work/'index';answers=work/'answers.jsonl'
        sample=task/'data'/'sample';queries=task/'queries'/'sample.jsonl'
        phases['build']=run(candidate,['build','--input',sample,'--out',index],'build',work)
        def build_complete():
            if not success(phases['build']):raise ValueError('build did not exit 0 within limits')
            for name in ARTIFACTS:regular(index/name,2*1024**3)
        built=check('build_complete',build_complete)
        manifest=stats=rejections=None
        if built:
            def manifest_shape():
                nonlocal manifest
                manifest=json_file(index/'manifest.json')
                if not fields(manifest,('schema_version','as_of_utc','source_inventory','source_fingerprint','effective_policy','policy_fingerprint','artifacts')) or type(manifest['schema_version']) is not int or manifest['schema_version']!=1:raise ValueError('manifest shape')
                if not fields(manifest['artifacts'],('index.sqlite','stats.json','rejections.json')):raise ValueError('manifest artifact names')
                policy=manifest['effective_policy']
                if not fields(policy,('policy_id','max_results','effective_at')) or not isinstance(policy['policy_id'],str) or not policy['policy_id'] or not integer(policy['max_results']) or policy['max_results']==0:raise ValueError('policy shape')
                if manifest['policy_fingerprint']!=hashlib.sha256(canonical(policy)).hexdigest() or manifest['source_fingerprint']!=hashlib.sha256(canonical(manifest['source_inventory'])).hexdigest():raise ValueError('manifest internal fingerprint')
                inv=manifest['source_inventory']
                if not isinstance(inv,list):raise ValueError('inventory is not array')
                paths=[]
                for item in inv:
                    if not fields(item,('path','sha256','size')) or not isinstance(item['path'],str) or not integer(item['size']):raise ValueError('inventory item')
                    paths.append(item['path'])
                if paths!=sorted(set(paths),key=lambda s:s.encode('utf-8')):raise ValueError('inventory order/duplicates')
            check('manifest_shape',manifest_shape)
            def stats_shape():
                nonlocal stats
                stats=json_file(index/'stats.json')
                if not fields(stats,('schema_version','status','as_of_utc','policy_id','max_results','doc_count','selected_keys','withdrawn_count','tenant_count')) or type(stats['schema_version']) is not int or stats['schema_version']!=1 or stats['status']!='COMPLETE':raise ValueError('stats shape')
                if any(not integer(stats[k]) for k in ('max_results','doc_count','selected_keys','withdrawn_count','tenant_count')) or stats['max_results']==0 or stats['selected_keys']!=stats['doc_count']+stats['withdrawn_count']:raise ValueError('stats invariant')
            check('stats_shape',stats_shape)
            def rejections_shape():
                nonlocal rejections
                rejections=json_file(index/'rejections.json')
                if not fields(rejections,('schema_version','counts','retained_records')) or type(rejections['schema_version']) is not int or rejections['schema_version']!=1 or not fields(rejections['counts'],('OVERSIZE','BAD_JSON','BAD_SCHEMA','FUTURE','DUPLICATE_RECORD_ID')) or not integer(rejections['retained_records']) or any(not integer(x) for x in rejections['counts'].values()):raise ValueError('rejections shape')
                meta=json_file(sample/'META.json')
                if sum(rejections['counts'].values())+rejections['retained_records']!=meta['expected_nonblank_document_rows']:raise ValueError('rejections row-count invariant')
            check('rejections_shape',rejections_shape)
            def sqlite_schema():
                regular(index/'index.sqlite',2*1024**3)
                db=sqlite3.connect((index/'index.sqlite').as_uri()+'?mode=ro',uri=True)
                try:
                    for table,expected in {'docs':{'tenant_id':'TEXT','doc_id':'TEXT','revision':'INTEGER','title':'TEXT','body':'TEXT','tags':'TEXT'},'meta':{'key':'TEXT','value':'TEXT'}}.items():
                        actual={row[1]:row[2].upper() for row in db.execute('PRAGMA table_info('+table+')')}
                        if any(actual.get(k)!=v for k,v in expected.items()):raise ValueError('required SQLite columns')
                    meta=dict(db.execute('SELECT key,value FROM meta'))
                    if not {'schema_version','as_of_utc','policy_fingerprint','registered_tenants','tag_weights'}<=set(meta):raise ValueError('required SQLite meta')
                    tenants=parse(meta['registered_tenants']);weights=parse(meta['tag_weights'])
                    if not isinstance(tenants,list) or not isinstance(weights,dict):raise ValueError('SQLite meta JSON')
                    if stats is None or db.execute('SELECT COUNT(*) FROM docs').fetchone()[0]!=stats['doc_count']:raise ValueError('SQLite doc_count')
                finally:db.close()
            check('sqlite_schema',sqlite_schema)
            def artifact_hashes():
                if manifest is None:raise ValueError('manifest unavailable')
                for name in ('index.sqlite','stats.json','rejections.json'):
                    if sha(index/name)!=manifest['artifacts'][name]:raise ValueError('artifact hash '+name)
            check('artifact_hashes',artifact_hashes)
            phases['search']=run(candidate,['search','--index',index,'--queries',queries,'--out',answers],'search',work)
            result_lines=[]
            def search_complete():
                nonlocal result_lines
                if not success(phases['search']):raise ValueError('search did not exit 0 within limits')
                raw=read(answers);lines=raw.splitlines(keepends=True);query_values=[parse(x) for x in read(queries).splitlines() if x.strip()]
                if len(lines)!=len(query_values):raise ValueError('query/answer count')
                result_lines=[]
                for line,query in zip(lines,query_values):
                    value=parse(line)
                    if line!=canonical(value)+b'\n' or not fields(value,('qid','status','policy_id','sources')) or value['qid']!=query['qid'] or value['status'] not in ('OK','NO_MATCH','FORBIDDEN') or not isinstance(value['sources'],list):raise ValueError('answer row shape/serialization')
                    if value['status']!='OK' and value['sources'] or value['status']=='OK' and not value['sources']:raise ValueError('answer status/sources')
                    for source in value['sources']:
                        if not fields(source,('tenant_id','doc_id','revision','title','score','snippet')) or not integer(source['revision']) or not integer(source['score']) or source['score']==0 or any(not isinstance(source[k],str) for k in ('tenant_id','doc_id','title','snippet')):raise ValueError('source shape')
                    result_lines.append(line)
            searched=check('search_complete',search_complete)
            if searched:
                def public_first12():
                    expected=read(task/'expected'/'sample-first12.jsonl')
                    if len(expected.splitlines())!=12 or b''.join(result_lines[:12])!=expected:raise ValueError('public first12 mismatch')
                check('public_first12',public_first12)
            def verify_readonly():
                before=snapshot(index)
                phases['verify']=run(candidate,['verify','--index',index],'verify',work)
                if not success(phases['verify']) or snapshot(index)!=before:raise ValueError('verify failed or changed artifact bytes/mtime')
            check('verify_readonly',verify_readonly)
            def resume_unchanged():
                before=snapshot(index)
                phases['resume']=run(candidate,['build','--input',sample,'--out',index,'--resume'],'resume',work)
                if not success(phases['resume']) or snapshot(index)!=before:raise ValueError('resume failed or changed artifact bytes/mtime')
            check('resume_unchanged',resume_unchanged)
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error) as exc:
        error=str(exc)
    else:error=None
    report={'scope':'KB-TRIAL-1 public sample smoke v1','denominator':len(CHECKS),'passed':sum(x['status']=='PASS' for x in checks.values()),'checks':checks,'phases':phases,'error':error,'claim':'Public smoke only; no full-source truth or hidden-grade claim.'}
    print(canonical(report).decode('utf-8'))
    return 0 if report['passed']==report['denominator'] else 1

if __name__=='__main__':sys.exit(main())
