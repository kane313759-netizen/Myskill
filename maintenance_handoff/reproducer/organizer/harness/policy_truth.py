"""Derive overlay expectations from the sealed independent base logical cache."""
import argparse
import shutil
from pathlib import Path
from .core import *

def derive(base,policy_path,out,queries):
    base=Path(base);out=Path(out)
    if out.exists():raise ContractError('overlay truth already exists')
    out.mkdir(parents=True)
    for name in ('sample','full'):
        source=base/name;target=out/name;target.mkdir();bundle=target/'bundle';shutil.copytree(source/'bundle',bundle)
        manifest=parse_json(read_regular(bundle/'manifest.json'));policy=policy_value(parse_json(read_regular(policy_path)),manifest['as_of_utc'])
        manifest['effective_policy']=policy;manifest['policy_fingerprint']=digest(canonical(policy))
        stats=parse_json(read_regular(bundle/'stats.json'));stats['policy_id']=policy['policy_id'];stats['max_results']=policy['max_results'];write_json(bundle/'stats.json',stats)
        db=sqlite3.connect(bundle/'index.sqlite')
        try:db.execute("UPDATE meta SET value=? WHERE key='policy_fingerprint'",(manifest['policy_fingerprint'],));db.commit()
        finally:db.close()
        manifest['artifacts']={n:file_info(bundle/n)['sha256'] for n in manifest['artifacts']};write_json(bundle/'manifest.json',manifest)
        verify_bundle(bundle);engine=bundle_engine(bundle)
        with (Path(queries)/f'{name}.jsonl').open('rb') as inp,(target/'answers.jsonl').open('wb') as dest:
            for line in inp:dest.write(canonical(engine.search(parse_json(line)))+b'\n')
        manifest.pop('artifacts');write_json(target/'expected.json',{'stats.json':stats,'rejections.json':parse_json(read_regular(bundle/'rejections.json')),'manifest':manifest})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--policy',required=True);p.add_argument('--out',required=True);p.add_argument('--queries',required=True);a=p.parse_args();derive(a.base,a.policy,a.out,a.queries)
