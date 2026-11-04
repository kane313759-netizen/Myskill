"""Build one independent reference cache and compare construction truth."""
import sys
import time
from pathlib import Path
from .core import *

def prepare(root):
    root=Path(root);output=root/'organizer'/'reference_truth'
    if output.exists():raise ContractError('truth cache already exists; do not silently rerun')
    output.mkdir();report={}
    for name in ('sample','full'):
        started=time.monotonic();source=load_source(root/'task'/'data'/name)
        ledger=parse_json(read_regular(root/'organizer'/'truth'/f'{name}.json',128*1024**2))
        expected_docs=sorted([r for r in ledger['selected_records'] if r['state']=='PUBLISHED'],key=lambda r:(r['tenant_id'].encode(),r['doc_id'].encode()))
        comparisons={'stats':canonical(source['stats'])==canonical(ledger['stats']),'rejections':canonical(source['rejections'])==canonical(ledger['rejections']),'selected_published_records':canonical(source['docs'])==canonical(expected_docs)}
        if not all(comparisons.values()):raise AssertionError((name,comparisons,source['stats'],source['rejections']))
        target=output/name;target.mkdir();write_bundle(source,target/'bundle')
        engine=Engine(source['docs'],source['tenants'],source['weights'],source['policy']);answers=[]
        with (root/'task'/'queries'/f'{name}.jsonl').open('rb') as stream:
            for line in stream:answers.append(engine.search(parse_json(line)))
        with (target/'answers.jsonl').open('wb') as stream:
            for answer in answers:stream.write(canonical(answer)+b'\n')
        manifest=parse_json(read_regular(target/'bundle'/'manifest.json'));manifest.pop('artifacts')
        write_json(target/'expected.json',{'stats.json':source['stats'],'rejections.json':source['rejections'],'manifest':manifest})
        verify_bundle(target/'bundle')
        if name=='sample':
            raw=read_regular(root/'task'/'expected'/'sample-first12.jsonl');expected=b''.join(canonical(a)+b'\n' for a in answers[:12])
            comparisons['public_first12']=raw==expected
            if raw!=expected:raise AssertionError('public first12 mismatch')
        report[name]={'comparisons':comparisons,'seconds':time.monotonic()-started,'queries':len(answers),'positive_queries':sum(a['status']=='OK' for a in answers),'stats':source['stats'],'rejections':source['rejections']}
    write_json(output/'PREPARATION.json',report);print(canonical(report).decode())

if __name__=='__main__':prepare(sys.argv[1])
