"""Synthetic r3 streaming benchmark; no competition data."""
import gzip,json,pathlib,runpy,tempfile,time,tracemalloc
ROOT=pathlib.Path(__file__).resolve().parents[1]
audit=runpy.run_path(str(ROOT/'scripts/data_audit.py'))['audit']
with tempfile.TemporaryDirectory(prefix='v27-benchmark-') as td:
 p=pathlib.Path(td)/'synthetic.csv.gz'
 with gzip.open(p,'wt',encoding='utf8',newline='') as f:
  f.write('m1,m2,m3,m4,m5\n'); chunk='1,2,3,4,5\n'*10000
  for i in range(200): f.write(chunk)
 tracemalloc.start();start=time.monotonic()
 result=audit(pathlib.Path(td),{'files':[p.name],'max_rows':2000,'max_scan_seconds':120})
 elapsed=time.monotonic()-start; current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 print(json.dumps({'synthetic_rows_expected':2000000,'rows_scanned':result['scope']['rows_examined'],
  'status':result['status'],'elapsed_seconds':round(elapsed,3),'peak_tracemalloc_bytes':peak,
  'complete':result['scope']['all_provided_rows_examined']},ensure_ascii=True))
