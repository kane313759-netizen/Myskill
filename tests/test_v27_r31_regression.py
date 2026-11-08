import csv,datetime,json,pathlib,runpy,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
AUDIT=runpy.run_path(str(ROOT/'scripts/data_audit.py'))['audit']
CHECK=runpy.run_path(str(ROOT/'scripts/v27_check.py'))

class RegressionR31(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
 def write(self,name,fields,rows):
  with (self.root/name).open('w',encoding='utf8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 def scan(self,name,**kw):
  plan=dict(files=[name],reservoir_size=5,max_rows=100);plan.update(kw);return AUDIT(self.root,plan)
 def test_01_wide_rows_complete_and_warning_not_pending(self):
  fields=['record_key','kind','group']+['metric_%03d'%i for i in range(200)]
  rows=({'record_key':'X%06d'%n,'kind':'ABC'[n%3],'group':'XY'[n%2],**{'metric_%03d'%i:10+i for i in range(200)}} for n in range(300))
  self.write('wide.csv',fields,rows);r=self.scan('wide.csv')
  self.assertEqual(r['status'],'RECORDED');self.assertTrue(r['files'][0]['complete_rows'])
  self.assertTrue(r['scope']['all_provided_rows_examined']);self.assertIn('analysis_limits',r['files'][0])
  messages=CHECK['audit_limit_warnings'](r);self.assertIsInstance(messages,list)
  from test_v27_check import EvidenceTests,digest
  t=EvidenceTests('runTest');t.setUp();self.addCleanup(t.doCleanups);t.cp1_records()
  t.write('input.csv',(self.root/'wide.csv').read_text(encoding='utf8'))
  value=AUDIT(t.root,t.plan['data_audit_plan']);ref=t.record('data_audit',value)
  t.plan['spec_draft']=t.write('SPEC_DRAFT.md',ref['path']+' '+ref['sha256'])
  sources={x['path']:x['sha256'] for x in value['files']}
  for item in (ref,t.plan['spec_draft']): sources[item['path']]=item['sha256']
  resolution={'items':[dict(id=x['id'],status='RECORDED',method='Synthetic review',finding='Synthetic observation',
      evidence={'path':'TASK.md','sha256':digest(t.root/'TASK.md')},source_hashes=sources,data_audit_sha256=ref['sha256']) for x in value['items'] if x['status']=='UNVERIFIED']}
  t.record('data_audit_resolution',resolution);t.record('cp1_reviews',t.reviews('CP1',('CONSTRAINT_RED','DATA_EVAL_RED')))
  result=t.result('cp1');self.assertEqual(result['status'],'PASS',result)
  self.assertTrue(any('data_audit analysis limited' in x for x in result['warnings']))
 def test_02_most_granular_id_and_offset(self):
  base=datetime.datetime(2030,1,1);rows=[]
  for wafer in range(25):
   for step in range(40):
    t=base+datetime.timedelta(days=wafer,hours=4*step-(9 if step==20 else 0))
    rows.append({'lot_id':'L','wafer_id':'W%03d'%wafer,'step_seq':step,'tool':'odd' if step==20 else 'regular','start':t.isoformat(),'end':(t+datetime.timedelta(hours=2)).isoformat()})
  self.write('routing.csv',list(rows[0]),rows);r=self.scan('routing.csv',reservoir_size=100)
  event=r['files'][0]['tables'][0]['sequence_reversals'][0]
  self.assertEqual(event['roles']['id'],'wafer_id');self.assertEqual(event['dropped_events'],0)
  odd=next(x for x in event['sources'] if x['source']=='odd');self.assertGreaterEqual(odd['reversal_rate'],.05);self.assertAlmostEqual(odd['suggested_offset_hours'],9,delta=.5)
  self.assertTrue(event['roles']['id_candidates'])
 def test_03_two_source_leave_one_out(self):
  rows=[{'tool':x,'value':v} for _ in range(40) for x,v in [('A',10),('B',100)]]
  self.write('two.csv',list(rows[0]),rows);s=self.scan('two.csv')['files'][0]['tables'][0]['scale_suspects']
  self.assertTrue(any(x['kind']=='SOURCE' and x['source_value']=='A' for x in s))
  renamed=[{'source':x['tool'],'value':x['value']} for x in rows]
  self.write('two_generic.csv',list(renamed[0]),renamed);s=self.scan('two_generic.csv')['files'][0]['tables'][0]['scale_suspects']
  self.assertTrue(any(x['kind']=='SOURCE' and x['source_value']=='A' for x in s))
 def test_04_one_source_changes_with_time(self):
  rows=[]
  for month in range(1,7):
   for day in range(1,6):
    for tool in ('A','B','C','D'):
     rows.append({'date':'2031-%02d-%02d'%(month,day),'tool':tool,'value':10 if tool=='A' and month>=4 else 100})
  self.write('source_period.csv',list(rows[0]),rows);s=self.scan('source_period.csv',period='month')['files'][0]['tables'][0]['scale_suspects']
  self.assertTrue(any(x['kind']=='SOURCE_PERIOD' and x.get('source_value')=='A' and x.get('after_period')=='2031-04' for x in s))
 def test_05_timeless_long_format_no_step(self):
  rows=[{'item':name,'value':v} for name,v in [('p',1),('q',10),('r',100),('s',1000)] for _ in range(150)]
  self.write('long.csv',list(rows[0]),rows);s=self.scan('long.csv')['files'][0]['tables'][0]['scale_suspects']
  self.assertFalse(s,s)
 def test_06_timezone_mixed_and_skipped_pairs(self):
  rows=[{'lot':str(i),'step':j,'tool':'one','start':'2031-01-01T0%d:00:00%s'%(j*2,'Z' if j==1 else ''),'end':'2031-01-01T0%d:00:00%s'%(j*2+1,'Z' if j==1 else '')} for i in range(30) for j in range(2)]
  self.write('zones.csv',list(rows[0]),rows);r=self.scan('zones.csv');p=r['files'][0]['tables'][0]
  self.assertTrue(any(t.get('signal')=='TIMEZONE_MIXED' for t in p['time_candidates']))
  self.assertGreater(sum(x['skipped_timezone_mismatch'] for x in p['sequence_reversals'][0]['sources']),0)
 def test_07_missing_roles_explicit_not_run(self):
  self.write('unknown.csv',['alpha','timestamp_a','timestamp_b'],[{'alpha':'x','timestamp_a':'2031-01-01T01:00:00','timestamp_b':'2031-01-01T02:00:00'}])
  item=self.scan('unknown.csv')['items'][0]['findings'][0]
  self.assertTrue(item['sequence_check'].startswith('NOT_RUN'))
 def test_group_budgets_are_warnings_for_several_wide_shapes(self):
  for metrics,categories in ((120,1),(200,0),(30,6)):
   fields=['id_text']+['group_%d'%i for i in range(categories)]+['measure_%d'%i for i in range(metrics)]
   rows=({'id_text':'id%d'%n,**{'group_%d'%j:'g%d'%(n%30) for j in range(categories)},**{'measure_%d'%j:j+1 for j in range(metrics)}} for n in range(300))
   name='shape_%d_%d.csv'%(metrics,categories);self.write(name,fields,rows)
   r=self.scan(name);self.assertEqual(r['status'],'RECORDED');self.assertTrue(r['files'][0]['complete_rows'])
 def test_entity_step_budget_is_warning_not_row_truncation(self):
  rows=[{'lot_id':'L','step_seq':i,'start':'2031-01-01T00:00:00','end':'2031-01-01T01:00:00'} for i in range(150)]
  self.write('entity.csv',list(rows[0]),rows);r=self.scan('entity.csv')
  self.assertEqual(r['status'],'RECORDED');self.assertTrue(r['files'][0]['complete_rows'])
  self.assertTrue(any(x['check']=='time_order' for x in r['files'][0]['analysis_limits']))

class ExistingBehaviorR31(unittest.TestCase):
 setUp=RegressionR31.setUp
 write=RegressionR31.write
 scan=RegressionR31.scan
 def test_existing_01_ordered_scale_step(self):
  rows=[{'date':'2032-01-%02d'%(1+n//20),'v':1 if n<100 else 10} for n in range(200)]
  self.write('ordered.csv',list(rows[0]),rows);s=self.scan('ordered.csv')['files'][0]['tables'][0]['scale_suspects'];self.assertTrue(any(x['column']=='v' for x in s))
 def test_existing_02_shuffled_period_step(self):
  import random
  rows=[{'date':'2032-%02d-%02d'%(month,day),'value':100 if month<4 else 10} for month in range(1,7) for day in range(1,8)]
  random.Random(1).shuffle(rows);self.write('shuffled.csv',list(rows[0]),rows);s=self.scan('shuffled.csv',period='month')['files'][0]['tables'][0]['scale_suspects'];self.assertTrue(any(x['kind']=='PERIOD' for x in s))
 def test_existing_03_small_drift(self):
  rows=[{'date':'2032-01-%02d'%(1+i//10),'value':100*(1+.2*i/199)} for i in range(200)]
  self.write('drift.csv',list(rows[0]),rows);self.assertFalse(self.scan('drift.csv')['files'][0]['tables'][0]['scale_suspects'])
 def test_existing_04_products_sixfold(self):
  rows=[{'product':'A' if i<100 else 'B','value':100 if i<100 else 600} for i in range(200)]
  self.write('product.csv',list(rows[0]),rows);self.assertFalse(self.scan('product.csv')['files'][0]['tables'][0]['scale_suspects'])
 def test_existing_05_integer_counters(self):
  rows=[{'date':'2032-%02d-01'%m,'step_seq':10**(m//2),'total_index':10**(m//2)} for m in range(1,7)]
  self.write('counts.csv',list(rows[0]),rows);self.assertFalse(self.scan('counts.csv',period='month')['files'][0]['tables'][0]['scale_suspects'])
 def test_existing_06_explicit_symbolic_roles(self):
  base=datetime.datetime(2030,1,1);rows=[]
  for entity in range(40):
   for step in range(3):
    t=base+datetime.timedelta(days=entity,hours=step*12-(9 if step==1 else 0))
    rows.append({'LOT':str(entity),'OPER':'S%d'%step,'TOOL':'shifted' if step==1 else 'normal',
                 'TIN':t.isoformat(),'TOUT':(t+datetime.timedelta(hours=4)).isoformat()})
  self.write('explicit.csv',list(rows[0]),rows)
  role={'id':'LOT','sequence':'OPER','source':'TOOL','start':'TIN','end':'TOUT'}
  result=self.scan('explicit.csv',time_order=role)['files'][0]['tables'][0]['sequence_reversals'][0]
  self.assertAlmostEqual(next(x for x in result['sources'] if x['source']=='shifted')['suggested_offset_hours'],9,delta=.5)
 def test_existing_07_midweek_scale_step(self):
  rows=[{'date':'2032-02-%02d'%(1+n//30),'value':10 if n<90 else 100} for n in range(210)]
  self.write('week.csv',list(rows[0]),rows);s=self.scan('week.csv')['files'][0]['tables'][0]['scale_suspects'];self.assertTrue(any(x['column']=='value' for x in s))
