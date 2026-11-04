#!/usr/bin/env python3
"""Fixed-denominator native grader. Reads only the explicitly selected candidate."""
import argparse
import hashlib
import http.client
import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from harness.core import *
from harness.process import run

ROOT=Path(__file__).resolve().parents[1]
NAMES=('index.sqlite','stats.json','rejections.json','manifest.json')

def snapshot(path):
    result={}
    for name in NAMES:
        p=Path(path)/name
        try:result[name]=(file_info(p),p.lstat().st_mtime_ns)
        except (OSError,ContractError):result[name]=None
    return result

def json_file(path):
    raw=read_regular(path,4*1024**2);value=parse_json(raw)
    if raw!=canonical(value)+b'\n':raise ContractError('noncanonical')
    return value

def equal(a,b):return canonical(a)==canonical(b)

def preserved(path,wanted):
    try:return read_regular(path,len(wanted))==wanted
    except (OSError,ContractError):return False

def logical_db(path,max_rows=60001):
    regular(path);db=sqlite3.connect(Path(path).absolute().as_uri()+'?mode=ro',uri=True)
    try:
        started=time.monotonic();steps=[0]
        def progress():
            steps[0]+=1
            return int(steps[0]>1000 or time.monotonic()-started>5)
        db.set_progress_handler(progress,10000)
        if hasattr(db,'setlimit'):db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,1024*1024)
        if db.execute('SELECT type FROM sqlite_master WHERE name="docs"').fetchone()!=('table',):raise ContractError('docs is not a base table')
        rows=[]
        for row in db.execute('SELECT tenant_id,doc_id,revision,title,body,tags FROM docs'):
            if len(rows)>=max_rows:raise ContractError('excess docs')
            if any(not isinstance(row[i],str) for i in (0,1,3,4,5)) or not integer(row[2]):raise ContractError('doc types')
            rows.append(row)
        return sorted(rows,key=lambda r:(r[0].encode(),r[1].encode()))
    finally:db.close()

def safe_copy_bundle(source,dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    for name in NAMES:
        regular(Path(source)/name)
        shutil.copy2(Path(source)/name,dest/name)
    return dest

class Grade:
    def __init__(self,candidate,task,work,truth,policy=None):
        self.candidate=Path(candidate).absolute();regular(self.candidate,16*1024**2)
        self.task=Path(task).absolute();self.work=Path(work).absolute();self.work.mkdir(parents=True,exist_ok=False)
        self.truth=Path(truth).absolute();self.policy=Path(policy).absolute() if policy else None
        if self.policy:
            supplied=parse_json(read_regular(self.policy))
            if not equal(supplied,json_file(self.truth/'sample'/'expected.json')['manifest']['effective_policy']):raise ContractError('grader configuration: --truth must match --policy; derive with organizer.harness.policy_truth')
        self.checks=[];self.runs=[];self.safety=[];self.counter=0
    def add(self,id,points,ok,detail=''):
        self.checks.append({'id':id,'max':points,'earned':points if ok else 0.0,'status':'PASS' if ok else 'FAIL','detail':str(detail)[:2000]})
    def fraction(self,id,points,fraction,detail=''):
        self.checks.append({'id':id,'max':points,'earned':points*fraction,'status':'PASS' if fraction==1 else 'FAIL','detail':str(detail)[:2000]})
    def call(self,label,args,timeout=90):
        self.counter+=1;cwd=self.work/f'{self.counter:03d}-{label}';cwd.mkdir()
        result=run([sys.executable,str(self.candidate),*map(str,args)],cwd,timeout,cwd/'logs',observe_root=self.work)
        result['label']=label;self.runs.append(result)
        return result
    def okcall(self,*args,**kwargs):return self.call(*args,**kwargs)['returncode']==0
    def policy_args(self):return ['--policy',str(self.policy)] if self.policy else []
    def data_and_queries(self,name,factor):
        data=self.task/'data'/name;queries=self.task/'queries'/f'{name}.jsonl';expected_dir=self.truth/name
        expected=json_file(expected_dir/'expected.json');bundle=self.work/f'{name}-bundle';answers=self.work/f'{name}-answers.jsonl'
        result=self.call(f'{name}-build',['build','--input',data,'--out',bundle,*self.policy_args()],180 if name=='full' else 90)
        for artifact in ('stats.json','rejections.json'):
            try:ok=equal(json_file(bundle/artifact),expected[artifact])
            except Exception:ok=False
            self.add(f'{name}.{artifact}',6*factor,ok)
        try:
            manifest=json_file(bundle/'manifest.json');want=expected['manifest']
            ok=all(equal(manifest.get(k),v) for k,v in want.items()) and set(manifest)==set(want)|{'artifacts'} and exact(manifest['artifacts'],('index.sqlite','stats.json','rejections.json'))
            if ok:ok=all(manifest['artifacts'][n]==file_info(bundle/n)['sha256'] for n in manifest['artifacts'])
        except Exception:ok=False
        self.add(f'{name}.manifest',6*factor,ok)
        try:ok=logical_db(bundle/'index.sqlite')==logical_db(expected_dir/'bundle'/'index.sqlite')
        except Exception:ok=False
        self.add(f'{name}.database',6*factor,ok)
        search=self.call(f'{name}-search',['search','--index',bundle,'--queries',queries,'--out',answers,*self.policy_args()],180 if name=='full' else 90)
        wanted=[]
        with (expected_dir/'answers.jsonl').open('rb') as stream:
            for line in stream:wanted.append(parse_json(line))
        got=[];canonical_ok=True
        try:
            regular(answers,64*1024**2)
            with answers.open('rb') as stream:
                for n,line in enumerate(stream):
                    if n>=len(wanted):canonical_ok=False;break
                    value=parse_json(line);got.append(value)
                    canonical_ok &= line==canonical(value)+b'\n'
        except Exception:canonical_ok=False
        correct=sum(equal(a,b) for a,b in zip(got,wanted))
        positive_indices=[i for i,value in enumerate(wanted) if value['status']=='OK']
        positive_correct=sum(i<len(got) and equal(got[i],wanted[i]) for i in positive_indices)
        self.fraction(f'{name}.query_rows',40*factor,correct/len(wanted),f'{correct}/{len(wanted)}; allowed positives {positive_correct}/{len(positive_indices)}')
        allowed_keys={(r[0],r[1]) for r in logical_db(expected_dir/'bundle'/'index.sqlite')}
        registered_tenants=bundle_engine(expected_dir/'bundle').tenants
        with queries.open('rb') as stream:query_rows=[parse_json(line) for line in stream if line.strip()]
        for i,value in enumerate(got):
            if not isinstance(value,dict) or not isinstance(value.get('sources'),list):continue
            tenant=query_rows[i]['tenant_id']
            for item in value['sources']:
                if not isinstance(item,dict):continue
                key=(item.get('tenant_id'),item.get('doc_id'))
                if not all(isinstance(x,str) for x in key):continue
                if key[0] not in (tenant,'__public__') or tenant not in registered_tenants:
                    self.safety.append(f'{name} query {i}: unauthorized tenant source {key!r}')
                elif key not in allowed_keys:self.safety.append(f'{name} query {i}: absent/withdrawn source {key!r}')
        self.add(f'{name}.query_format',4*factor,canonical_ok and len(got)==len(wanted) and search['returncode']==0)
        try:verify_bundle(bundle,max_docs=expected['stats.json']['doc_count']+1);result['output_valid']=True
        except Exception:result['output_valid']=False
        search['output_valid']=canonical_ok and len(got)==len(wanted)
        return bundle,queries,result,search
    def integration(self,sample,queries):
        ref=self.truth/'sample'/'bundle';baseline=snapshot(sample)
        try:verify_bundle(sample,max_docs=1801);build_working=True
        except Exception:build_working=False
        # Separate supplied reference bundle keeps verification/API credit independent of build.
        pure=safe_copy_bundle(ref,self.work/'pure-bundle')
        r=self.call('verify-positive',['verify','--index',pure]);verify_working=r['returncode']==0 and snapshot(pure)==snapshot(ref)
        qfirst=next(line for line in queries.open('rb') if line.strip());positive_query=self.work/'positive-query.jsonl';positive_query.write_bytes(qfirst);positive_answer=self.work/'positive-answer.jsonl'
        r=self.call('search-positive',['search','--index',pure,'--queries',positive_query,'--out',positive_answer])
        wanted=canonical(bundle_engine(pure).search(parse_json(qfirst)))+b'\n';search_working=r['returncode']==0 and preserved(positive_answer,wanted)
        r=self.call('existing-output',['build','--input',self.task/'data'/'sample','--out',sample,*self.policy_args()]);self.add('cli.nonempty_refusal',1,build_working and r['returncode']==2 and snapshot(sample)==baseline)
        r=self.call('resume',['build','--input',self.task/'data'/'sample','--out',sample,'--resume',*self.policy_args()]);self.add('cli.resume_unchanged',1,build_working and r['returncode']==0 and snapshot(sample)==baseline)
        fresh=self.work/'fresh-bundle';r=self.call('fresh',['build','--input',self.task/'data'/'sample','--out',fresh,*self.policy_args()])
        try:det=r['returncode']==0 and logical_db(fresh/'index.sqlite')==logical_db(sample/'index.sqlite') and all(json_file(fresh/n)==json_file(sample/n) for n in ('stats.json','rejections.json'))
        except Exception:det=False
        self.add('cli.fresh_logical_determinism',1,build_working and det)
        changed=self.work/'changed-data';shutil.copytree(self.task/'data'/'sample',changed)
        (changed/'inventory-note.txt').write_text('changed\n')
        r=self.call('changed-resume',['build','--input',changed,'--out',sample,'--resume',*self.policy_args()]);self.add('cli.changed_resume_refusal',1,build_working and r['returncode']==2 and snapshot(sample)==baseline)
        corrupt=safe_copy_bundle(ref,self.work/'corrupt-hash');(corrupt/'stats.json').write_bytes(b'{}\n');before=snapshot(corrupt)
        r=self.call('verify-hash',['verify','--index',corrupt]);hash_rejected=r['returncode']==2 and snapshot(corrupt)==before;self.add('cli.verify_hash_rejection',1,verify_working and hash_rejected)
        malformed=safe_copy_bundle(ref,self.work/'corrupt-shape');stats=json_file(malformed/'stats.json');stats['doc_count']=True;write_json(malformed/'stats.json',stats);manifest=json_file(malformed/'manifest.json');manifest['artifacts']['stats.json']=file_info(malformed/'stats.json')['sha256'];write_json(malformed/'manifest.json',manifest);before=snapshot(malformed)
        r=self.call('verify-shape',['verify','--index',malformed]);shape_rejected=r['returncode']==2 and snapshot(malformed)==before;self.add('cli.verify_shape_rejection',1,verify_working and shape_rejected)
        self.add('cli.verify_supplied',1,verify_working and hash_rejected and shape_rejected)
        invalid=self.work/'invalid-query.jsonl';invalid.write_bytes(b'{"qid":"bad","tenant_id":"001","terms":[],"limit":true}\n')
        answers=self.work/'protected-answer';answers.write_bytes(b'PROTECTED\x00original\n');r=self.call('invalid-query',['search','--index',pure,'--queries',invalid,'--out',answers]);self.add('cli.invalid_query_atomic',1,search_working and r['returncode']==2 and preserved(answers,b'PROTECTED\x00original\n'))
        mismatch=self.work/'mismatch-policy.json';policy=json_file(pure/'manifest.json')['effective_policy'];policy['policy_id']+='-mismatch';write_json(mismatch,policy)
        r=self.call('mismatch-search',['search','--index',pure,'--queries',queries,'--out',answers,'--policy',mismatch]);self.add('cli.policy_mismatch_atomic',1,search_working and r['returncode']==2 and preserved(answers,b'PROTECTED\x00original\n'))
        # Source format invalidity never creates partial new output or replaces prior artifacts.
        invalid_data=self.work/'invalid-data';shutil.copytree(self.task/'data'/'sample',invalid_data);(invalid_data/'tag_weights.csv').write_bytes(b'tag,weight\nx,0\n')
        target=self.work/'invalid-build-out'
        r=self.call('invalid-build',['build','--input',invalid_data,'--out',target]);self.add('cli.invalid_source_preservation',1,build_working and r['returncode']==2 and (not target.exists() or (target.is_dir() and not any(target.iterdir()))))
        unsafe=self.work/'unsafe-data';shutil.copytree(self.task/'data'/'sample',unsafe);os.symlink(unsafe/'META.json',unsafe/'extra-link');r=self.call('symlink-source',['build','--input',unsafe,'--out',self.work/'unsafe-source-out']);self.add('cli.symlink_source_rejection',1,build_working and r['returncode']==2 and (unsafe/'extra-link').is_symlink())
        link=self.work/'unsafe-answer';os.symlink(answers,link);r=self.call('symlink-answer',['search','--index',pure,'--queries',queries,'--out',link]);safe=r['returncode']==2 and link.is_symlink() and preserved(answers,b'PROTECTED\x00original\n');self.add('cli.unsafe_output_rejection',1,search_working and safe)
        if not safe:self.safety.append('unsafe output target was accepted or original changed')
        self.http(pure,queries,mismatch)
    def request(self,port,method,path,body=None):
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
        try:
            conn.request(method,path,body=body,headers={'Content-Type':'application/json'} if body is not None else {})
            response=conn.getresponse();raw=response.read(1024*1024+1)
            if len(raw)>1024*1024:raise ContractError('HTTP response exceeds bound')
            return response.status,raw,response.getheader('Content-Type','')
        finally:conn.close()
    def http(self,bundle,queries,mismatch):
        sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
        cwd=self.work/'http';cwd.mkdir();before=snapshot(bundle)
        command=[sys.executable,str(self.candidate),'serve','--index',str(bundle),'--host','127.0.0.1','--port',str(port)]
        outcome={}
        def supervise():outcome.update(run(command,cwd,10,cwd/'logs',observe_root=self.work))
        supervisor=threading.Thread(target=supervise,daemon=True);supervisor.start()
        ready=False
        for _ in range(60):
            if not supervisor.is_alive():break
            try:
                status,raw,_=self.request(port,'GET','/health');ready=status==200
                if ready:break
            except Exception:pass
            time.sleep(.05)
        self.add('http.listen',1,ready)
        policy=json_file(bundle/'manifest.json')['effective_policy'];stats=json_file(bundle/'stats.json')
        expected=json_file(self.truth/'sample'/'expected.json');engine=bundle_engine(bundle)
        with Path(queries).open('rb') as stream:qs=[parse_json(x) for x in stream if x.strip()]
        positive=next((q for q in qs if engine.search(q)['status']=='OK'),qs[0])
        cases=[('health','GET','/health',None,200,{'status':'ok','policy_id':policy['policy_id']}),('stats','GET','/stats',None,200,stats),('positive','POST','/search',canonical(positive),200,engine.search(positive)),('forbidden','POST','/search',canonical({'qid':'public','tenant_id':'__public__','terms':[]}),200,{'qid':'public','tenant_id':'unused'}),('bad_query','POST','/search',canonical({'qid':'bad','tenant_id':'001','terms':[],'limit':True}),400,{'error':'BAD_QUERY'}),('bad_json','POST','/search',b'{',400,{'error':'BAD_QUERY'}),('not_found','GET','/missing',None,404,{'error':'NOT_FOUND'}),('method','PUT','/search',b'{}',405,{'error':'METHOD_NOT_ALLOWED'})]
        cases[3]=(*cases[3][:-1],engine.search({'qid':'public','tenant_id':'__public__','terms':[]}))
        try:
            for label,method,path,body,want_status,want in cases:
                try:status,raw,kind=self.request(port,method,path,body);ok=ready and status==want_status and raw==canonical(want)+b'\n' and 'application/json' in kind
                except Exception:ok=False
                self.add('http.'+label,1,ok)
            try:
                status,raw,kind=self.request(port,'GET','/');html=raw.decode('utf-8');ok=ready and status==200 and 'text/html' in kind and all(str(x) in html for x in (policy['policy_id'],policy['max_results'],stats['as_of_utc'],stats['doc_count'])) and ('근거' in html or 'evidence' in html.lower()) and ('생성' in html or 'generat' in html.lower())
            except Exception:ok=False
            self.add('http.html',1,ok)
        finally:
            supervisor.join(timeout=12)
            outcome['label']='http-server';outcome['grader_stop']='bounded 10-second observation window';self.runs.append(outcome)
        self.add('http.read_only',1,ready and snapshot(bundle)==before)
        r=self.call('serve-policy-mismatch',['serve','--index',bundle,'--host','127.0.0.1','--port',str(port),'--policy',mismatch],5)
        self.add('http.policy_mismatch',1,ready and r['returncode']==2)
    def resource(self,runs):
        for name,build,search in runs:
            for label,result in [('build',build),('search',search)]:
                self.add(f'resource.{name}.{label}',1,result['returncode']==0 and result.get('output_valid',False) and not result['timed_out'] and not result['limit_exceeded'])
    def execute(self):
        sb,sq,br,sr=self.data_and_queries('sample',.4);fb,fq,bf,sf=self.data_and_queries('full',.6)
        self.integration(sb,sq);self.resource([('sample',br,sr),('full',bf,sf)])
        maximum=sum(c['max'] for c in self.checks)
        if abs(maximum-96)>1e-8:raise AssertionError(f'grader denominator {maximum}')
        result={'candidate':str(self.candidate),'candidate_sha256':file_info(self.candidate)['sha256'],'automatic_max':96,'automatic_score':sum(c['earned'] for c in self.checks),'explanation':{'max':4,'status':'PENDING','anchors':['Explain first-eligible record_id reservation versus version selection and withdrawal.','Explain exact-instant order, tenant ACL, distinct-tag score and UTF-8 tie ordering.']},'checks':self.checks,'runs':self.runs,'submission_safety':{'status':'PASS' if not self.safety else 'FAIL','findings':self.safety},'grader_sources':{p.relative_to(ROOT).as_posix():file_info(p)['sha256'] for p in [Path(__file__),ROOT/'organizer'/'harness'/'core.py',ROOT/'organizer'/'harness'/'process.py']}}
        write_json(self.work/'GRADE.json',result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--task',default=str(ROOT/'task'));p.add_argument('--work',required=True);p.add_argument('--truth',default=str(ROOT/'organizer'/'reference_truth'));p.add_argument('--policy');args=p.parse_args()
    result=Grade(args.candidate,args.task,args.work,args.truth,args.policy).execute();print(json.dumps({'automatic_score':result['automatic_score'],'automatic_max':96,'report':str(Path(args.work)/'GRADE.json')}))
if __name__=='__main__':main()
