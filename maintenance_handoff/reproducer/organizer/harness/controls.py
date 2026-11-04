"""Explicit organizer calibration fakes. These are NOT performer implementations.

Positive data comes from the already independently checked reference cache.
Semantic modes deliberately violate one contract rule after that copy.
"""
import argparse
import importlib.util
import os
import shutil
import sys
import tempfile
from pathlib import Path
from .core import *

ROOT=Path(__file__).resolve().parents[2]
MODES=('empty','noop','alwaysreject','alwaysNO_MATCH','wrongrank','ACLleak','resurrectWITHDRAWN')
NAMES=('index.sqlite','stats.json','rejections.json','manifest.json')

def reference_module():
    spec=importlib.util.spec_from_file_location('kb_organizer_reference',ROOT/'organizer'/'reference.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def copied_build(args,mode,ref):
    data=Path(args.input).absolute();out=ref.safe_target(args.out)
    known={ROOT/'task'/'data'/name:name for name in ('sample','full')}
    name=known.get(data)
    # Small integration variants use the native reference's strict handling.
    # The large full dataset is never reparsed by a control.
    if name is None or args.resume or (out.exists() and (not out.is_dir() or any(out.iterdir()))):
        return ref.build(args)
    if out==data or data in out.parents or out in data.parents:raise ContractError('overlapping output')
    source=ROOT/'organizer'/'reference_truth'/name/'bundle'
    verify_bundle(source)
    manifest=parse_json(read_regular(source/'manifest.json'))
    effective=manifest['effective_policy']
    if args.policy:effective=policy_value(parse_json(read_regular(args.policy)),manifest['as_of_utc'])
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.control-bundle-',dir=out.parent))
    try:
        for filename in NAMES:
            regular(source/filename);shutil.copy2(source/filename,tmp/filename)
        stats=parse_json(read_regular(tmp/'stats.json'))
        stats['policy_id']=effective['policy_id'];stats['max_results']=effective['max_results']
        db=sqlite3.connect(tmp/'index.sqlite')
        try:
            db.execute('UPDATE meta SET value=? WHERE key=?',(digest(canonical(effective)),'policy_fingerprint'))
            if mode=='resurrectWITHDRAWN':
                ledger=parse_json(read_regular(ROOT/'organizer'/'truth'/f'{name}.json',128*1024**2))
                withdrawn=[r for r in ledger['selected_records'] if r['state']=='WITHDRAWN']
                db.executemany('INSERT INTO docs VALUES(?,?,?,?,?,?)',[(r['tenant_id'],r['doc_id'],max(0,r['revision']-1),r['title'],r['body'],canonical(r['tags']).decode()) for r in withdrawn])
                stats['doc_count']+=len(withdrawn);stats['withdrawn_count']=0
            db.commit()
        finally:db.close()
        write_json(tmp/'stats.json',stats)
        manifest['effective_policy']=effective;manifest['policy_fingerprint']=digest(canonical(effective))
        manifest['artifacts']={n:file_info(tmp/n)['sha256'] for n in NAMES if n!='manifest.json'}
        write_json(tmp/'manifest.json',manifest)
        if out.exists():out.rmdir()
        os.replace(tmp,out)
    finally:
        if tmp.exists():shutil.rmtree(tmp)

def fake_result(mode,query,engine):
    result=engine.search(query)
    if mode=='alwaysNO_MATCH':
        result['status']='NO_MATCH';result['sources']=[]
    elif mode=='wrongrank':
        result['sources'].reverse()
    elif mode=='ACLleak' and query['tenant_id'] in engine.tenants:
        # Deliberately include a matching document from an unauthorized tenant.
        scores={}
        for term in set(query['terms']):
            for index in engine.postings.get(term,()):
                if engine.docs[index]['tenant_id'] not in (query['tenant_id'],'__public__'):
                    scores[index]=scores.get(index,0)+engine.weights[term]
        if scores:
            index=min(scores,key=lambda i:(-scores[i],engine.docs[i]['doc_id'].encode(),engine.docs[i]['tenant_id'].encode()))
            score,doc=scores[index],engine.docs[index]
            leaked={k:doc[k] for k in ('tenant_id','doc_id','revision','title')}|{'score':score,'snippet':doc['body'][:80]}
            cap=min(query.get('limit',engine.policy['max_results']),engine.policy['max_results'])
            result['sources']=([leaked]+result['sources'])[:cap];result['status']='OK'
    return result

def copied_search(args,mode,ref):
    verify_bundle(args.index);ref.policy_match(args.index,args.policy)
    engine=bundle_engine(args.index);out=ref.safe_target(args.out);index=Path(args.index).resolve()
    if out==index or index in out.parents or out==Path(args.queries).absolute():raise ContractError('colliding answers')
    regular(args.queries);queries=[]
    with open(args.queries,'rb') as stream:
        for line in stream:
            if line.strip():queries.append(query_value(parse_json(line)))
    out.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix='.control-search-',dir=out.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            for query in queries:stream.write(canonical(fake_result(mode,query,engine))+b'\n')
        os.replace(tmp,out)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main(mode,argv=None):
    if mode not in MODES:raise ValueError('unknown calibration mode')
    if mode in ('empty','noop'):return 0
    if mode=='alwaysreject':return 2
    argv=list(sys.argv[1:] if argv is None else argv)
    ref=reference_module()
    if not argv or argv[0] not in ('build','search'):
        original=sys.argv
        try:sys.argv=[str(ROOT/'organizer'/'reference.py'),*argv];return ref.main()
        finally:sys.argv=original
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('build');p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--policy');p.add_argument('--resume',action='store_true')
    p=sub.add_parser('search');p.add_argument('--index',required=True);p.add_argument('--queries',required=True);p.add_argument('--out',required=True);p.add_argument('--policy')
    args=parser.parse_args(argv)
    try:
        if args.command=='build':copied_build(args,mode,ref)
        else:copied_search(args,mode,ref)
    except (ContractError,OSError,ValueError,KeyError,TypeError,sqlite3.Error) as exc:
        print('CONTROL ERROR: '+str(exc),file=sys.stderr);return 2
    return 0

def write_candidates(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False);result={}
    organizer=str(ROOT/'organizer')
    for mode in MODES:
        path=directory/f'{mode}.py'
        if mode=='empty':body=''
        elif mode=='noop':body='raise SystemExit(0)\n'
        elif mode=='alwaysreject':body='raise SystemExit(2)\n'
        else:body='import sys\nsys.path.insert(0, '+repr(organizer)+')\nfrom harness.controls import main\nraise SystemExit(main('+repr(mode)+'))\n'
        path.write_text(body,encoding='utf-8');result[mode]=path.absolute()
    return result
