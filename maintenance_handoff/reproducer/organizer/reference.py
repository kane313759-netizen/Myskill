#!/usr/bin/env python3
"""Organizer-only independent native reference, not performer starter code."""
import argparse
import os
import shutil
import sys
import tempfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from harness.core import *

def safe_target(path):
    path=Path(path).absolute()
    protected=Path(__file__).resolve().parents[1]/'task'
    if path==protected or protected in path.parents:raise ContractError('protected task output')
    for parent in (path,*path.parents):
        if parent.is_symlink():raise ContractError('symlink output')
    if path.exists() and not path.is_dir() and not path.is_file():raise ContractError('nonregular output')
    return path

def policy_match(index,path):
    if path:
        manifest=parse_json(read_regular(Path(index)/'manifest.json'))
        value=policy_value(parse_json(read_regular(path)),manifest['as_of_utc'])
        if digest(canonical(value))!=manifest['policy_fingerprint']:raise ContractError('policy mismatch')

def build(args):
    data=Path(args.input).absolute();out=safe_target(args.out)
    if out==data or data in out.parents or out in data.parents:raise ContractError('overlapping input/output')
    inv=inventory(data);meta=parse_json(read_regular(data/'META.json'))
    policy=policy_value(parse_json(read_regular(args.policy or data/'policy.json')),meta['as_of_utc'])
    if args.resume:
        verify_bundle(out);old=parse_json(read_regular(out/'manifest.json'))
        if inv!=old['source_inventory'] or policy!=old['effective_policy']:raise ContractError('changed resume')
        return
    if out.exists() and (not out.is_dir() or any(out.iterdir())):raise ContractError('nonempty output')
    source=load_source(data,args.policy)
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.kb-build-',dir=out.parent))
    try:
        write_bundle(source,tmp)
        if out.exists():out.rmdir()
        os.replace(tmp,out)
    finally:
        if tmp.exists():shutil.rmtree(tmp)

def search(args):
    verify_bundle(args.index);policy_match(args.index,args.policy)
    engine=bundle_engine(args.index);out=safe_target(args.out);index=Path(args.index).resolve()
    if out==index or index in out.parents:raise ContractError('answer collides with bundle')
    query_path=Path(args.queries).absolute()
    if out==query_path:raise ContractError('answers overwrite queries')
    db=sqlite3.connect((index/'index.sqlite').as_uri()+'?mode=ro',uri=True)
    try:source_row=db.execute("SELECT value FROM meta WHERE key='source_root'").fetchone()
    finally:db.close()
    if source_row:
        original=Path(source_row[0]).absolute()
        if out==original or original in out.parents:raise ContractError('answers overwrite original input')
    # Validate all input before opening the destination.
    regular(query_path);queries=[]
    with query_path.open('rb') as stream:
        for line in stream:
            if line.strip():queries.append(query_value(parse_json(line)))
    out.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.kb-search-',dir=out.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            for query in queries:stream.write(canonical(engine.search(query))+b'\n')
        os.replace(tmp,out)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def serve(args):
    verify_bundle(args.index);policy_match(args.index,args.policy);engine=bundle_engine(args.index)
    stats=parse_json(read_regular(Path(args.index)/'stats.json'))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,value,html=False):
            raw=value.encode('utf-8') if html else canonical(value)+b'\n'
            self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def route(self):
            path=self.path
            if path not in ('/','/health','/stats','/search'):self.send(404,{'error':'NOT_FOUND'});return
            expected='POST' if path=='/search' else 'GET'
            if self.command!=expected:self.send(405,{'error':'METHOD_NOT_ALLOWED'});return
            if path=='/health':self.send(200,{'status':'ok','policy_id':engine.policy['policy_id']})
            elif path=='/stats':self.send(200,stats)
            elif path=='/':self.send(200,'<!doctype html><meta charset="utf-8"><title>Support evidence search</title><h1>고객지원 근거 검색</h1><p>정책 '+str(engine.policy['policy_id'])+' / 최대 '+str(engine.policy['max_results'])+'개 / 기준 '+stats['as_of_utc']+' / 문서 '+str(stats['doc_count'])+'개</p><p>문서 근거를 검색하며 생성된 상담 답변은 제공하지 않습니다.</p>',True)
            else:
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if size<1 or size>1048576:raise ContractError('request size')
                    result=engine.search(parse_json(self.rfile.read(size)))
                except (ValueError,ContractError):self.send(400,{'error':'BAD_QUERY'});return
                self.send(200,result)
        do_GET=route;do_POST=route;do_PUT=route;do_DELETE=route;do_PATCH=route;do_HEAD=route;do_OPTIONS=route
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()

def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('build');p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--policy');p.add_argument('--resume',action='store_true');p.set_defaults(func=build)
    p=sub.add_parser('search');p.add_argument('--index',required=True);p.add_argument('--queries',required=True);p.add_argument('--out',required=True);p.add_argument('--policy');p.set_defaults(func=search)
    p=sub.add_parser('verify');p.add_argument('--index',required=True);p.set_defaults(func=lambda args:verify_bundle(args.index))
    p=sub.add_parser('serve');p.add_argument('--index',required=True);p.add_argument('--host',required=True);p.add_argument('--port',type=int,required=True);p.add_argument('--policy');p.set_defaults(func=serve)
    args=parser.parse_args()
    try:args.func(args)
    except (ContractError,OSError,ValueError,KeyError,TypeError,sqlite3.Error) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 2
    return 0

if __name__=='__main__':sys.exit(main())
