"""Run declared calibration fakes and public smoke; never inspect old candidates.

Run as `python -m harness.selftest` from organizer. Positive native evidence is
reused explicitly so the full independent reference is not rerun silently.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from .controls import ROOT,MODES,write_candidates
from .core import *

def source_hashes(root):
    files=[root/'organizer'/'grade.py',root/'organizer'/'harness'/'core.py',root/'organizer'/'harness'/'process.py',root/'organizer'/'harness'/'controls.py',root/'organizer'/'harness'/'selftest.py',root/'task'/'tools'/'public_smoke.py']
    return {p.relative_to(root).as_posix():file_info(p)['sha256'] for p in files}

def invoke(argv,cwd,log):
    log.mkdir(parents=True,exist_ok=False)
    with (log/'stdout.log').open('wb') as out,(log/'stderr.log').open('wb') as err:
        process=subprocess.run([sys.executable,*map(str,argv)],cwd=cwd,stdout=out,stderr=err,timeout=1200)
    return {'argv':[sys.executable,*map(str,argv)],'returncode':process.returncode,'stdout':str(log/'stdout.log'),'stderr':str(log/'stderr.log')}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(ROOT));p.add_argument('--work');p.add_argument('--positive-grade');args=p.parse_args()
    root=Path(args.root).absolute()
    if root!=ROOT:raise ContractError('control module is fixed to its own declared release root')
    work=Path(args.work or root/'organizer'/'selftest-controls').absolute()
    if work.exists():raise ContractError('selftest work exists; preserve raw evidence and select a new work path')
    work.mkdir(parents=True);candidates=write_candidates(work/'candidates')
    positive_path=Path(args.positive_grade or root/'organizer'/'selftest-native-positive'/'GRADE.json')
    positive=parse_json(read_regular(positive_path));current_hashes=source_hashes(root)
    preparation=parse_json(read_regular(root/'organizer'/'reference_truth'/'PREPARATION.json'))
    report={'schema_version':1,'scope':'new KB-TRIAL-1 release calibration only','status':'PENDING_ROOT_REVIEW','source_hashes':current_hashes,'positive':{'report':str(positive_path),'automatic_score':positive['automatic_score'],'automatic_max':positive['automatic_max'],'candidate':positive['candidate'],'grader_sources':positive['grader_sources'],'same_current_grader_sources':all(current_hashes.get(k)==v for k,v in positive['grader_sources'].items()),'explanation':positive['explanation']},'independent_truth_preparation':preparation,'controls':{},'public_smoke':{},'assertions':[]}
    def assertion(name,ok,detail=''):
        report['assertions'].append({'id':name,'passed':bool(ok),'detail':detail})
    assertion('positive_native_96',positive['automatic_score']==96 and positive['automatic_max']==96)
    assertion('positive_explanation_pending',positive['explanation']['status']=='PENDING' and positive['explanation']['max']==4)
    assertion('positive_is_declared_reference',Path(positive['candidate'])==root/'organizer'/'reference.py')
    assertion('construction_truth_agrees',all(all(v['comparisons'].values()) for v in preparation.values()))
    for mode in MODES:
        grade_work=work/f'grade-{mode}'
        execution=invoke([root/'organizer'/'grade.py','--candidate',candidates[mode],'--task',root/'task','--truth',root/'organizer'/'reference_truth','--work',grade_work],work,work/f'logs-grade-{mode}')
        grade=parse_json(read_regular(grade_work/'GRADE.json')) if (grade_work/'GRADE.json').is_file() else None
        entry={'execution':execution,'report':str(grade_work/'GRADE.json'),'grade':grade};report['controls'][mode]=entry
        assertion(mode+'.grader_completed',execution['returncode']==0 and grade is not None)
        if grade is None:continue
        assertion(mode+'.fixed_max',grade['automatic_max']==96)
        if mode in ('empty','noop','alwaysreject'):
            assertion(mode+'.zero',grade['automatic_score']==0,grade['automatic_score'])
        else:
            rows=[c for c in grade['checks'] if c['id'].endswith('.query_rows')]
            assertion(mode+'.meaningful_query_failure',len(rows)==2 and sum(c['earned'] for c in rows)<sum(c['max'] for c in rows),[{'id':c['id'],'detail':c['detail'],'earned':c['earned']} for c in rows])
            if mode=='alwaysNO_MATCH':
                assertion(mode+'.all_allowed_positives_wrong',all('allowed positives 0/' in c['detail'] for c in rows),[c['detail'] for c in rows])
                assertion(mode+'.published_partial_credit_retained',grade['automatic_score']>0,grade['automatic_score'])
    for mode,candidate in [('positive',root/'organizer'/'reference.py'),('empty',candidates['empty']),('noop',candidates['noop'])]:
        smoke_work=work/f'smoke-{mode}'
        execution=invoke([root/'task'/'tools'/'public_smoke.py','--candidate',candidate,'--task',root/'task','--work',smoke_work],work,work/f'logs-smoke-{mode}')
        stdout=read_regular(Path(execution['stdout']))
        smoke=parse_json(stdout)
        report['public_smoke'][mode]={'execution':execution,'result':smoke}
        assertion('public_smoke.'+mode+'.fixed10',smoke['denominator']==10)
        assertion('public_smoke.'+mode+'.expected_score',smoke['passed']==(10 if mode=='positive' else 0),smoke['passed'])
    scopes={value['result']['scope'] for value in report['public_smoke'].values()}
    assertion('public_smoke.same_scope',len(scopes)==1)
    report['all_calibration_assertions_passed']=all(x['passed'] for x in report['assertions'])
    report['status']='CALIBRATION_COMPLETE_PENDING_ROOT_REVIEW' if report['all_calibration_assertions_passed'] else 'CALIBRATION_FAILURE'
    write_json(work/'SELFTEST.json',report);write_json(root/'organizer'/'SELFTEST.json',report)
    print(canonical({'status':report['status'],'assertions':len(report['assertions']),'passed':sum(x['passed'] for x in report['assertions']),'report':str(root/'organizer'/'SELFTEST.json')}).decode())
    return 0 if report['all_calibration_assertions_passed'] else 1

if __name__=='__main__':sys.exit(main())
