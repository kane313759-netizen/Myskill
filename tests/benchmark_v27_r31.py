"""Synthetic-only r3.1 benchmarks; writes data only inside a temporary folder."""
import gzip,json,pathlib,runpy,tempfile,time,tracemalloc
ROOT=pathlib.Path(__file__).resolve().parents[1]
audit=runpy.run_path(str(ROOT/'scripts/data_audit.py'))['audit']

def measure(root,name,expected):
 tracemalloc.start();start=time.monotonic();result=audit(root,{'files':[name]})
 elapsed=time.monotonic()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 limits=result['files'][0]['analysis_limits'];summary={}
 for item in limits:
  key=item['check'];entry=summary.setdefault(key,{'entries':0,'dropped':0});entry['entries']+=1;entry['dropped']+=item['dropped']
 print(json.dumps({'fixture':name,'expected_rows':expected,'rows_scanned':result['scope']['rows_examined'],
  'elapsed_seconds':round(elapsed,3),'peak_tracemalloc_bytes':peak,'status':result['status'],
  'complete_rows':result['files'][0]['complete_rows'],'analysis_limits':summary},ensure_ascii=True),flush=True)

with tempfile.TemporaryDirectory(prefix='v27-r31-benchmark-') as td:
 root=pathlib.Path(td);p=root/'narrow.csv.gz'
 with gzip.open(p,'wt',encoding='utf8',newline='') as f:
  f.write('a,b,c,d,e\n');chunk='1,2,3,4,5\n'*10000
  for _ in range(200):f.write(chunk)
 measure(root,p.name,2000000)
 p=root/'wide.csv'
 with p.open('w',encoding='utf8',newline='') as f:
  f.write('entry_key,class_a,class_b,'+','.join('v%d'%i for i in range(200))+'\n')
  line=','.join(str(i+1) for i in range(200))
  for i in range(200000):f.write('K%d,%s,%s,%s\n'%(i,'ABC'[i%3],'XY'[i%2],line))
 measure(root,p.name,200000)
