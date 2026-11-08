import gzip, hashlib, json, pathlib, runpy, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
CHECK=runpy.run_path(str(ROOT/'scripts/v27_check.py'))
AUDIT=runpy.run_path(str(ROOT/'scripts/data_audit.py'))['audit']

class RegressionR41(unittest.TestCase):
 def fixture(self):
  from test_v27_check import EvidenceTests
  t=EvidenceTests('runTest');t.setUp();self.addCleanup(t.doCleanups);t.complete_final_records()
  c=json.loads((t.root/t.plan['records']['baseline_comparison']['path']).read_text(encoding='utf8'))
  return t,c
 def gate(self,t,c):
  scope=json.loads((t.root/c['shared_scope_evidence']['path']).read_text(encoding='utf8'))
  a=json.loads((t.root/c['baseline_evidence']['path']).read_text(encoding='utf8'))
  b=json.loads((t.root/c['candidate_evidence']['path']).read_text(encoding='utf8'))
  g=dict(metric='flag_count',direction='LOWER_IS_BETTER',baseline_value=1,candidate_value=4)
  g['evidence']=t.write('gate.json',json.dumps(dict(g,scope=scope,baseline_artifact=a['artifact'],candidate_artifact=b['artifact'])))
  return g
 def test_01_proxy_worse_task_better(self):
  t,c=self.fixture();c['task_metric_ref']='Maximize score.';c['gates']=[self.gate(t,c)];t.record('baseline_comparison',c)
  r=t.result('final');self.assertEqual(r['errors'],[]);self.assertTrue(any('proxy metric is worse' in x for x in r['warnings']))
 def test_02_hard_limit_violation(self):
  t,c=self.fixture();g=self.gate(t,c);quote='The count must not exceed 2.'
  c['hard_limits']=[dict(metric=g['metric'],direction=g['direction'],candidate_value=g['candidate_value'],limit=2,source_quote=quote,evidence=t.write('limit.txt',quote))]
  t.record('baseline_comparison',c);self.assertTrue(any('hard limit violated' in x for x in t.result('final')['errors']))
  policy=runpy.run_path(str(ROOT/'scripts/v27_comparison.py'))['comparison_policy']
  for metric,limit,value in (('violations',2,3),('failure_count',1,2)):
   with self.subTest(metric=metric):
    r=policy({'hard_limits':[dict(metric=metric,limit=limit,candidate_value=value,direction='LOWER_IS_BETTER',evidence={'path':'synthetic','sha256':'a'*64},source_quote='Synthetic task upper limit.')]})
    self.assertTrue(r['errors'])
 def test_03_task_metric_worse(self):
  t,c=self.fixture();c['primary']={'task_metric_ref':'Maximize score.'};c['candidate_value']=9
  old=json.loads((t.root/c['candidate_evidence']['path']).read_text(encoding='utf8'));old['value']=9
  c['candidate_evidence']=t.write('lower.json',json.dumps(old));t.record('baseline_comparison',c)
  self.assertTrue(any('candidate scores lower on the task metric under identical evaluation' in x for x in t.result('final')['errors']))
 def test_04_current_baseline_rejection_basis(self):
  t,c=self.fixture();c['selection']='CURRENT_BASELINE';c['candidate_value']=c['baseline_value']
  a=json.loads((t.root/c['baseline_evidence']['path']).read_text(encoding='utf8'));b=json.loads((t.root/c['candidate_evidence']['path']).read_text(encoding='utf8'));b['value']=a['value'];a['artifact']=b['artifact'];c['baseline_evidence']=t.write('baseline-same.json',json.dumps(a))
  c['candidate_evidence']=t.write('selected.json',json.dumps(b));c['baseline_assumptions_check']=[dict(check=n,method='synthetic check',result='observed') for n in ('response_shape','progress_variable','operating_shift')]
  c['best_alternative']=dict(name='one',metric_values={'score':11},rejection_reason='synthetic reason',rejection_basis='OTHER')
  t.record('baseline_comparison',c);r=t.result('final');self.assertEqual(r['errors'],[]);self.assertTrue(any('NO_OP' in x for x in r['warnings']))
  c['best_alternative']['rejection_basis']='HARD_LIMIT';t.record('baseline_comparison',c);self.assertFalse(any('NO_OP' in x for x in t.result('final')['warnings']))
 def test_05_one_positive_one_negative(self):
  t,c=self.fixture();p=t.plan['records']['grading']['path'];g=json.loads((t.root/p).read_text(encoding='utf8'))
  g=t.grading();g['controls']=[g['controls'][0],g['controls'][-1]];t.record('grading',g)
  self.assertEqual(t.result('cp1')['errors'],[])
 def test_06_jsonl_and_unsupported_isolation(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);text='{"a":1,"nested":{"x":2}}\n{"b":2,"nested":[3]}\n'
   (root/'a.jsonl').write_text(text,encoding='utf8')
   with gzip.open(root/'b.jsonl.gz','wt',encoding='utf8') as f:f.write(text)
   (root/'c.csv').write_text('x\n1\n',encoding='utf8');(root/'d.unknown').write_text('unparsed',encoding='utf8')
   r=AUDIT(root,{'files':['a.jsonl','b.jsonl.gz','c.csv','d.unknown']});self.assertEqual(r['status'],'RECORDED')
   self.assertEqual([x['status'] for x in r['files']],['RECORDED']*3+['UNSUPPORTED']);self.assertTrue(all(x['complete_rows'] for x in r['files'][:3]));self.assertTrue(r['warnings'])
   self.assertEqual(set(r['files'][0]['tables'][0]['columns']),{'a','b','nested'})
   (root/'a.jsonl').write_text(text+'broken\n',encoding='utf8');r=AUDIT(root,{'files':['a.jsonl','c.csv']})
   self.assertEqual(r['files'][0]['broken_lines'],1);self.assertFalse(r['files'][0]['complete_rows']);self.assertTrue(r['files'][1]['complete_rows'])
 def test_07_legacy_gate_warning(self):
  t,c=self.fixture();c['gates']=[self.gate(t,c)];t.record('baseline_comparison',c);r=t.result('final')
  self.assertEqual(r['errors'],[]);self.assertTrue(any('legacy gate treated as proxy' in x for x in r['warnings']))
 def test_08_document_guard(self):
  paths=['.agents/skills/hackathon-orchestrator-universal/SKILL.md','references/v27-contract.md','templates/V27_EVIDENCE.json']
  for p in paths:
   text=(ROOT/p).read_text(encoding='utf8')
   for forbidden in ('현행 기준선을 보존','어느 관문이든 나빠지면 FAIL','a worse candidate fails'):self.assertNotIn(forbidden,text)
  text=(ROOT/paths[0]).read_text(encoding='utf8');self.assertIn('두 해석의 지표 값',text);self.assertIn('보수적인 가정',text)
 def test_09_protected_files(self):
  manifest=json.loads((ROOT/'references/v27-baseline.json').read_text(encoding='utf8'))['files'];self.assertEqual(len(manifest),112)
  for p,digest in manifest.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),digest,p)
