import hashlib,json,pathlib,runpy,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SKILL='.agents/skills/hackathon-orchestrator-universal/SKILL.md'
BASELINE_R2_HASHES=('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '7a13eaf88d769cb63a6e5b4c849674a0b7d11b85bfabae5b66f32a6a9f233a19', '2e506338bb0be39fb3c2c6f9d73511c524b44389180635751c568f255d38a6a5', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '5ab38b57a3d81029cf0e822512df7cff8f093d8991c6125cadbdeb0cb0ce50bd', '4d7b36329069f2bd4cfec0c6146a04e0eef52625a2b9a4a2c72200eaefa18cf7', 'eb13b147ba2a2b9e984b0ffddfa4688cde532f56f085f7704774e6f8206c6d2e', 'ac3e4fb6fc903b7354fefd2151ee5dc68f68f30acd92ad06b3a2e85a2e7d93da', '978e2260abd59795ffe264d745d94a4be38ccb928bbac77447e71588865f7b04', '9a60c8626b522517c50c03e37642f5ccca874924884dd7e44df73c17bf5d4102', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'd994e23a185286b676a6a03988686ef91a1f217b23bfebcc12f1068a9561901d', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '9acb5fc84fb9a2a2f8feac08755eac1d88229bf467360d0b0fa49b89bf2f13bc', 'f959b8ffea460771e87a43b9982f9d814f96221ed5f0f891d848d2ffe20275a0')  # Pinned starting-section line hashes, excluding L1's replaced line.

class RegressionR42(unittest.TestCase):
 def test_01_document_guard_and_original_lines(self):
  text=(ROOT/SKILL).read_text(encoding='utf8')
  self.assertNotIn('숫자·단위·스키마·템플릿 계약이 산문과 충돌하면',text)
  for term in ('데이터 오류 후보','"보정"','"그대로"','자체 검증','`현행 유지`는 자동 기본 답이 아니다','뺀 후보의 과제 지표','평가 조건','대리 라벨','최소 시뮬레이터'):
   self.assertIn(term,text)
  current=iter(hashlib.sha256(line.encode('utf8')).hexdigest() for line in text.split('## r2 시험 결과 반영',1)[1].splitlines())
  for expected in BASELINE_R2_HASHES:
   self.assertTrue(any(actual==expected for actual in current),'starting r2 section line removed or changed: '+expected)
 def fixture(self):
  from test_v27_check import EvidenceTests
  t=EvidenceTests('runTest');t.setUp();self.addCleanup(t.doCleanups);t.complete_final_records()
  c=json.loads((t.root/t.plan['records']['baseline_comparison']['path']).read_text(encoding='utf8'))
  a=json.loads((t.root/c['baseline_evidence']['path']).read_text(encoding='utf8'));b=json.loads((t.root/c['candidate_evidence']['path']).read_text(encoding='utf8'))
  a['artifact']=b['artifact'];b['value']=a['value'];c['baseline_value']=c['candidate_value']=a['value']
  c['baseline_evidence']=t.write('baseline-same.json',json.dumps(a));c['candidate_evidence']=t.write('selected.json',json.dumps(b))
  c['selection']='CURRENT_BASELINE';c['baseline_assumptions_check']=[dict(check=n,method='synthetic check',result='observed') for n in ('response_shape','progress_variable','operating_shift')]
  c['best_alternative']=dict(name='alternative',metric_values={'score':12},rejection_reason='synthetic task limit',rejection_basis='HARD_LIMIT')
  return t,c
 def test_02_best_alternative_result_evidence(self):
  t,c=self.fixture();t.record('baseline_comparison',c);r=t.result('final')
  self.assertEqual(r['errors'],[]);self.assertTrue(any('best_alternative evidence' in x for x in r['unverified']))
  policy=runpy.run_path(str(ROOT/'scripts/v27_comparison.py'))['comparison_policy']
  self.assertTrue(policy(c)['pending'])
  c['best_alternative']['evidence']=t.write('alternative.json',json.dumps({'metric_values':{'score':11}}));t.record('baseline_comparison',c)
  self.assertTrue(any('best_alternative evidence' in x for x in t.result('final')['errors']))
  for result in ({'metric_values':{'score':12},'details':'synthetic'}, {'score':12,'details':'synthetic'}):
   c['best_alternative']['evidence']=t.write('alternative.json',json.dumps(result));t.record('baseline_comparison',c);r=t.result('final')
   self.assertEqual(r['errors'],[]);self.assertEqual(r['unverified'],[])
  c['best_alternative']['evidence']['sha256']='TODO';t.record('baseline_comparison',c)
  self.assertTrue(any('best_alternative evidence' in x for x in t.result('final')['errors']))
  c['best_alternative']['evidence']={'path':'missing-result.json','sha256':'a'*64};t.record('baseline_comparison',c);r=t.result('final')
  self.assertEqual(r['errors'],[]);self.assertTrue(any('best_alternative evidence file missing' in x for x in r['unverified']))
 def test_03_proxy_warning_guidance(self):
  check=runpy.run_path(str(ROOT/'scripts/v27_check.py'))
  gate=dict(metric='synthetic_count',direction='LOWER_IS_BETTER',baseline_value=1,candidate_value=2,evidence={'path':'synthetic','sha256':'a'*64})
  r=check['r3_policy'](gates=[gate]);self.assertFalse(r['errors'])
  self.assertTrue(any('proxy metric is worse than baseline: synthetic_count (if this is a limit stated in the task text, record it under hard_limits with source_quote)'==x for x in r['warnings']))
  p=runpy.run_path(str(ROOT/'scripts/v27_comparison.py'))['comparison_policy']
  for record in ({'proxy_metrics':[gate]},dict(gate)):
   warnings=p(record)['warnings'];self.assertTrue(any('hard_limits with source_quote' in x for x in warnings))
 def test_05_protected_files(self):
  files=json.loads((ROOT/'references/v27-baseline.json').read_text(encoding='utf8'))['files'];self.assertEqual(len(files),112)
  for path,digest in files.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
