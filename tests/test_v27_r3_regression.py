import csv, gzip, json, os, pathlib, runpy, tempfile, unittest

ROOT=pathlib.Path(os.environ.get('V27_TEST_SOURCE', pathlib.Path(__file__).resolve().parents[1]))
AUDIT=runpy.run_path(str(ROOT/'scripts/data_audit.py'))['audit']
CHECK=runpy.run_path(str(ROOT/'scripts/v27_check.py'))

class SyntheticStreamingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root=pathlib.Path(self.tmp.name)
 def write(self,name,fields,rows):
  path=self.root/name
  op=gzip.open if name.endswith('.gz') else open
  with op(path,'wt',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 def test_f1_auto_and_explicit_sequence_offset(self):
  from datetime import datetime,timedelta
  data=[]; origin=datetime(2031,1,1)
  for i in range(40):
   for step in range(3):
    t=origin+timedelta(days=i,hours=step*12-(9 if step==1 else 0))
    data.append({'lot_id':str(i),'step':step,'tool':'slow' if step==1 else 'normal','start_time':t.isoformat(),'end_time':(t+timedelta(hours=4)).isoformat()})
  self.write('a.csv',list(data[0]),data)
  report=AUDIT(self.root,{'files':['a.csv']})
  info=report['files'][0]['tables'][0]['sequence_reversals'][0]
  self.assertEqual(info['roles']['mode'],'auto')
  source={x['source']:x for x in info['sources']}
  self.assertEqual(source['normal']['reversed_pairs'],0)
  self.assertAlmostEqual(source['slow']['suggested_offset_hours'],9,delta=.5)
  rename={'lot_id':'LOT','step':'OPER','tool':'TOOL','start_time':'TIN','end_time':'TOUT'}
  self.write('b.csv',list(rename.values()),[{rename[k]:v for k,v in row.items()} for row in data])
  plan={'files':['b.csv'],'time_order':{'id':'LOT','sequence':'OPER','start':'TIN','end':'TOUT','source':'TOOL'}}
  info=AUDIT(self.root,plan)['files'][0]['tables'][0]['sequence_reversals'][0]
  self.assertEqual(info['roles']['mode'],'explicit')
  self.assertAlmostEqual(next(x for x in info['sources'] if x['source']=='slow')['suggested_offset_hours'],9,delta=.5)
  symbolic=[dict(row,step='P'+str(int(row['step'])+1)) for row in data]
  self.write('symbolic.csv',list(symbolic[0]),symbolic)
  info=AUDIT(self.root,{'files':['symbolic.csv']})['files'][0]['tables'][0]['sequence_reversals'][0]
  self.assertAlmostEqual(next(x for x in info['sources'] if x['source']=='slow')['suggested_offset_hours'],9,delta=.5)
 def test_f2_multiple_files_stream_independently(self):
  for n in range(3): self.write('f%d.csv.gz'%n,['value'],({'value':i} for i in range(75)))
  r=AUDIT(self.root,{'files':['f0.csv.gz','f1.csv.gz','f2.csv.gz'],'max_rows':5})
  self.assertEqual(len(r['files']),3)
  self.assertTrue(all(x['rows_scanned']==75 and x['complete_rows'] for x in r['files']))
 def test_f2_partial_one_file_does_not_stop_others(self):
  self.write('large.csv',['x'],({'x':'x'*80} for _ in range(100)))
  self.write('small.csv',['x'],[{'x':'ok'}])
  r=AUDIT(self.root,{'files':['large.csv','small.csv'],'max_scan_bytes':1000})
  self.assertEqual(r['status'],'UNVERIFIED')
  self.assertFalse(r['files'][0]['complete_rows']);self.assertTrue(r['files'][1]['complete_rows'])
 def test_f2_partial_multiline_row_is_unverified(self):
  (self.root/'multi.csv').write_text('id,text\n1,"first line\n'+'x'*300+'\nlast"\n',encoding='utf8')
  r=AUDIT(self.root,{'files':['multi.csv'],'max_scan_bytes':80})
  self.assertEqual(r['status'],'UNVERIFIED');self.assertFalse(r['files'][0]['complete_rows'])
 def test_f2_oversized_json_does_not_block_next_csv(self):
  (self.root/'large.json').write_text(json.dumps({'text':'a'*500}),encoding='utf8')
  self.write('small.csv',['x'],[{'x':1}])
  r=AUDIT(self.root,{'files':['large.json','small.csv'],'max_file_bytes':80})
  self.assertEqual(r['status'],'UNVERIFIED');self.assertFalse(r['files'][0]['complete_rows']);self.assertTrue(r['files'][1]['complete_rows'])
 def test_f2_source_reservoir_overflow_is_warning(self):
  rows=[]
  for n in range(2100):
   rows.extend([{'lot_id':str(n),'step':1,'tool':'shared','start':'2031-01-01T00:00:00','end':'2031-01-01T01:00:00'},
                {'lot_id':str(n),'step':2,'tool':'S'+str(n),'start':'2031-01-01T02:00:00','end':'2031-01-01T03:00:00'}])
  self.write('many.csv',list(rows[0]),rows);r=AUDIT(self.root,{'files':['many.csv']})
  self.assertEqual(r['status'],'RECORDED');self.assertTrue(r['files'][0]['analysis_limits'])
 def test_f3_source_mixed_and_dates(self):
  rows=[]
  for day in range(1,25):
   for machine in ['A','B','C']:
    rows.append({'date':'2031-01-%02d'%day,'tool':machine,'measurement':10 if machine=='B' else 100,'step_seq':day})
  self.write('mixed.csv',list(rows[0]),rows)
  p=AUDIT(self.root,{'files':['mixed.csv']})['files'][0]['tables'][0]
  suspects=p['scale_suspects']
  self.assertTrue(any(x.get('kind')=='SOURCE' and x.get('source_value')=='B' and x.get('column')=='measurement' for x in suspects))
  self.assertFalse(any(x.get('column')=='step_seq' for x in suspects))
  ordered=[{'date':'2031-01-%02d'%d,'tool':t,'value':10 if d>=15 else 100} for t in ['A','B'] for d in range(1,29)]
  self.write('ordered.csv',list(ordered[0]),ordered)
  s=AUDIT(self.root,{'files':['ordered.csv'],'period':'week'})['files'][0]['tables'][0]['scale_suspects']
  self.assertTrue(any(x.get('kind')=='PERIOD' and x.get('column')=='value' for x in s))
 def test_f3_sixfold_and_small_drift_not_flagged(self):
  rows=[{'date':'2031-01-%02d'%(1+i//10),'product':'A' if i<100 else 'B','value':100 if i<100 else 600,'step_seq':i} for i in range(200)]
  self.write('drift.csv',list(rows[0]),rows)
  s=AUDIT(self.root,{'files':['drift.csv']})['files'][0]['tables'][0]['scale_suspects']
  self.assertFalse(any(x.get('column') in ('value','step_seq') for x in s))
  drift=[{'date':'2032-01-%02d'%(1+i//10),'value':100*(1+.2*i/199)} for i in range(200)]
  self.write('incremental.csv',list(drift[0]),drift)
  s=AUDIT(self.root,{'files':['incremental.csv']})['files'][0]['tables'][0]['scale_suspects']
  self.assertFalse(any(x.get('column')=='value' for x in s))
 def test_f3_report_is_stable_across_fresh_processes(self):
  import subprocess,sys
  rows=[{'source':c,'v1':n,'v2':n*10} for c,n in [('A',1),('B',10),('C',10)] for _ in range(10)]
  self.write('source.csv',list(rows[0]),rows)
  plan=self.root/'plan.json';plan.write_text(json.dumps({'files':['source.csv']}),encoding='utf8')
  argv=[sys.executable,'-I',str(ROOT/'scripts/data_audit.py'),'--root',str(self.root),'--plan',str(plan)]
  a=subprocess.run(argv,capture_output=True,text=True,encoding='utf8');b=subprocess.run(argv,capture_output=True,text=True,encoding='utf8')
  self.assertEqual(a.returncode,0,a.stdout);self.assertEqual(json.loads(a.stdout),json.loads(b.stdout))
 def test_f3_integer_indices_excluded_but_noninteger_measurement_kept(self):
  rows=[{'source':source,'processIndex':n,'step_size':size} for source,size in [('A',1.1),('B',11.0),('C',11.0)] for n in range(20)]
  self.write('measurements.csv',list(rows[0]),rows)
  result=AUDIT(self.root,{'files':['measurements.csv']})['files'][0]['tables'][0]['scale_suspects']
  self.assertTrue(any(x['column']=='step_size' for x in result))
  self.assertFalse(any(x['column']=='processIndex' for x in result))

class SyntheticPolicyTests(unittest.TestCase):
 def apply(self,**kw): return CHECK['r3_policy'](**kw)
 def test_f4_finding_without_effect(self):
  r=self.apply(findings=[{'item_id':2,'finding_ref':'f1'}],impacts=[])
  self.assertTrue(r['errors'])
  r=self.apply(findings=[{'item_id':2,'finding_ref':'f1'}],impacts=[{'item_id':2,'finding_ref':'f1','action':'check','metric':'x','before':1,'after':2,'split':'holdout','grader_sha256':'a'*64}]);self.assertFalse(r['errors'])
  r=self.apply(findings=[{'item_id':2,'finding_ref':'f1'}],impacts=[{'item_id':2,'unmeasurable_reason':'no outcome labels'}]);self.assertFalse(r['errors']);self.assertTrue(r['warnings'])
 def test_f5_worse_gate_blocks(self):
  r=self.apply(gates=[{'metric':'violations','direction':'LOWER_IS_BETTER','baseline_value':2,'candidate_value':3,'evidence':{'path':'synthetic','sha256':'a'*64}}]);self.assertTrue(r['errors'])
  r=self.apply(gates=[{'metric':'violations','direction':'LOWER_IS_BETTER','baseline_value':2,'candidate_value':1,'evidence':{'path':'synthetic','sha256':'a'*64}}]);self.assertFalse(r['errors'])
 def test_f6_assumptions_are_distinct_known_checks(self):
  valid=[{'check':x,'method':'observed comparison','result':'reviewed'} for x in ('response_shape','progress_variable','operating_shift')]
  self.assertTrue(self.apply(assumptions=valid[:2],keep_baseline=True)['pending'])
  self.assertFalse(self.apply(assumptions=valid,keep_baseline=True)['pending'])
  valid[-1]['check']='invented';self.assertTrue(self.apply(assumptions=valid,keep_baseline=True)['pending'])
 def test_f7_type_a_list_and_type_b_score(self):
  self.assertTrue(self.apply(type_a=[{'topic_key':'experiment_design'}])['errors'])
  self.assertFalse(self.apply(type_a=[{'topic_key':'risk_tolerance','question_ref':{'path':'q','sha256':'a'*64},'answer_ref':{'path':'a','sha256':'b'*64}}])['errors'])
  self.assertTrue(self.apply(type_b=[{'evidence_score':''}])['errors'])
 def test_f8_request_details_and_fallback(self):
  q={'state':'PENDING','hypothesis':'h','target':'x','expected_if_true':'yes','expected_if_false':'no','budget_left':1,'layer_check':'checked','deadline_fallback':True}
  self.assertTrue(self.apply(requests=[dict(q,hypothesis='')])['errors'])
  self.assertTrue(self.apply(requests=[q],comparison_verified=True)['warnings'])
  self.assertTrue(self.apply(requests=[q],comparison_verified=False)['pending'])
 def test_f9_windows_utf8_warning(self):
  self.assertTrue(CHECK['utf8_warning'](True,0));self.assertFalse(CHECK['utf8_warning'](True,1));self.assertFalse(CHECK['utf8_warning'](False,0))

class IntegrationR3Tests(unittest.TestCase):
 def fixture(self):
  import test_v27_check as fixture_module
  fixture_module.ROOT=ROOT
  fixture_module.CHECK=CHECK
  fixture_module.COMMON=runpy.run_path(str(ROOT/'scripts/v27_common.py'))
  fixture_module.DEADLINE=runpy.run_path(str(ROOT/'scripts/deadline.py'))
  fixture_module.AUDIT=runpy.run_path(str(ROOT/'scripts/data_audit.py'))
  EvidenceTests=fixture_module.EvidenceTests
  t=EvidenceTests('runTest');t.setUp();self.addCleanup(t.doCleanups);t.complete_final_records();return t
 def test_final_gate_metric_and_deadline_fallback_are_enforced(self):
  t=self.fixture(); comp=json.loads((t.root/t.plan['records']['baseline_comparison']['path']).read_text(encoding='utf8'))
  scope=json.loads((t.root/comp['shared_scope_evidence']['path']).read_text(encoding='utf8'))
  gate={'metric':'failure_count','direction':'LOWER_IS_BETTER','baseline_value':1,'candidate_value':2}
  baseline=json.loads((t.root/comp['baseline_evidence']['path']).read_text(encoding='utf8')); candidate=json.loads((t.root/comp['candidate_evidence']['path']).read_text(encoding='utf8'))
  evidence=dict(gate,scope=scope,baseline_artifact=baseline['artifact'],candidate_artifact=candidate['artifact'])
  gate['evidence']=t.write('gate.json',json.dumps(evidence));comp['gates']=[gate];t.record('baseline_comparison',comp)
  self.assertTrue(any('gate metric is worse' in x for x in t.result('final')['errors']))
  req={'state':'PENDING','hypothesis':'h','target':'local','expected_if_true':'yes','expected_if_false':'no','budget_left':1,'layer_check':'checked','deadline_fallback':True}
  t.record('external_requests',{'status':'TRACKED','requests':[req]})
  self.assertTrue(any('external request pending' in x for x in t.result('final')['unverified']))
  gate['candidate_value']=0;evidence['candidate_value']=0;gate['evidence']=t.write('gate.json',json.dumps(evidence));comp['gates']=[gate];t.record('baseline_comparison',comp)
  result=t.result('final');self.assertTrue(any('deadline fallback' in x for x in result['warnings']),result)
 def test_final_finding_requires_impact_record(self):
  t=self.fixture(); ref=t.plan['records']['data_audit_resolution']; res=json.loads((t.root/ref['path']).read_text(encoding='utf8'))
  res['items'][0]['status']='FINDING';res['items'][0]['finding_ref']='synthetic-finding';t.record('data_audit_resolution',res)
  self.assertTrue(any('FINDING missing impact' in x for x in t.result('final')['errors']))
  grading=json.loads((t.root/t.plan['records']['grading']['path']).read_text(encoding='utf8'))
  grading['finding_impacts']=[{'item_id':res['items'][0]['id'],'unmeasurable_reason':'No independent outcome is available.'}];t.record('grading',grading)
  result=t.result('final');self.assertFalse(any('FINDING missing impact' in x for x in result['errors']));self.assertTrue(any('cannot be measured' in x for x in result['warnings']))
  grader=t.write('synthetic-grader.py','print(1)\n');grading['evaluator_hashes']={grader['path']:grader['sha256']}
  grading['finding_impacts']=[{'item_id':res['items'][0]['id'],'finding_ref':'synthetic-finding','action':'review','metric':'loss','before':5,'after':4,'split':'later','grader_sha256':grader['sha256']}]
  t.record('grading',grading);result=t.result('final')
  self.assertFalse(any('FINDING missing impact' in x or 'impact grader' in x for x in result['errors']))
 def test_type_b_evidence_is_checked_at_cp1(self):
  t=self.fixture();card={'decision':'fit','chosen':'one','why':'known','alternative':'two','limitations':'bounded','change_location':'config','selection_by':'AI'}
  t.record('decisions',{'type_b_cards':[card]});self.assertTrue(any('evidence_score' in x for x in t.result('cp1')['errors']))
  card['evidence_score']={'metric':'score','score':1,'alternative_difference':.1};t.record('decisions',{'type_b_cards':[card]})
  self.assertFalse(any('evidence_score' in x for x in t.result('cp1')['errors']))
 def test_type_a_closed_list_is_checked_at_cp1(self):
  t=self.fixture();q=t.write('question.json','{}');a=t.write('answer.json','{}')
  t.record('decisions',{'type_b_cards':[],'type_a_choices':[{'topic_key':'experiment_design','question_ref':q,'answer_ref':a}]})
  self.assertTrue(any('type A topic' in x for x in t.result('cp1')['errors']))
  t.record('decisions',{'type_b_cards':[],'type_a_choices':[{'topic_key':'risk_tolerance','question_ref':q,'answer_ref':a}]})
  self.assertFalse(any('type A topic' in x for x in t.result('cp1')['errors']))
 def test_pending_fallback_requires_verified_submission_at_final(self):
  t=self.fixture();req={'state':'PENDING','hypothesis':'h','target':'local','expected_if_true':'yes','expected_if_false':'no','budget_left':1,'layer_check':'checked','deadline_fallback':True}
  t.record('external_requests',{'status':'TRACKED','requests':[req]})
  result=t.result('final');self.assertTrue(any('deadline fallback' in x for x in result['warnings']),result)
  t.record('baseline_comparison',{'status':'UNAVAILABLE_WITH_REASON','reason':'No comparable metric.'})
  result=t.result('final');self.assertTrue(any('external request pending' in x for x in result['unverified']),result)
 def test_baseline_assumptions_checked_at_final(self):
  t=self.fixture();comp=json.loads((t.root/t.plan['records']['baseline_comparison']['path']).read_text(encoding='utf8'))
  scope=json.loads((t.root/comp['shared_scope_evidence']['path']).read_text(encoding='utf8'))
  comp['selection']='CURRENT_BASELINE';comp['candidate_value']=comp['baseline_value']
  comp['candidate_evidence']=t.write('equal.json',json.dumps({'metric':comp['metric'],'value':comp['baseline_value'],'scope':scope,'artifact':{'path':'result.txt','sha256':__import__('hashlib').sha256((t.root/'result.txt').read_bytes()).hexdigest()}}))
  comp['alternatives']=[{'name':n,'assumptions':'checked','result':'not better','evidence':comp['baseline_evidence']} for n in ('first','second')]
  checks=[{'check':n,'method':'comparison','result':'reviewed'} for n in ('response_shape','progress_variable','operating_shift')]
  comp['baseline_assumptions_check']=checks[:2];t.record('baseline_comparison',comp)
  self.assertTrue(any('three distinct' in x for x in t.result('final')['unverified']))
  comp['baseline_assumptions_check']=checks;t.record('baseline_comparison',comp)
  self.assertFalse(any('three distinct' in x for x in t.result('final')['unverified']))
 def test_intake_windows_utf8_warning_is_runtime_wired(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  import sys,os
  from test_v27_check import EvidenceTests
  t=EvidenceTests('runTest');t.setUp();self.addCleanup(t.doCleanups)
  glob=CHECK['_check'].__globals__
  with patch.dict(glob,{'os':SimpleNamespace(name='nt',path=os.path),'sys':SimpleNamespace(flags=SimpleNamespace(utf8_mode=0),executable=sys.executable)}):
   self.assertTrue(any('UTF-8 mode is off' in x for x in CHECK['check'](t.plan,t.root,t.kit,'intake')['warnings']))
  with patch.dict(glob,{'os':SimpleNamespace(name='nt',path=os.path),'sys':SimpleNamespace(flags=SimpleNamespace(utf8_mode=1),executable=sys.executable)}):
   self.assertFalse(any('UTF-8 mode is off' in x for x in CHECK['check'](t.plan,t.root,t.kit,'intake')['warnings']))

if __name__=='__main__':
 unittest.main()
