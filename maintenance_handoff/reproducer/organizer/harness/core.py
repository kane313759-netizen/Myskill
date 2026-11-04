"""Independent KB trial reference. Standard library only; no candidate imports."""
import csv
import hashlib
import io
import json
import math
import os
import re
import sqlite3
import stat
import time
from datetime import datetime
from fractions import Fraction
from pathlib import Path

class ContractError(ValueError):
    pass

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def pairs(items):
    result={}
    for key,value in items:
        if key in result: raise ContractError('duplicate JSON key')
        result[key]=value
    return result

def parse_json(data):
    def bad(value): raise ContractError('non-finite JSON')
    def floating(value):
        result=float(value)
        if not math.isfinite(result):raise ContractError('non-finite JSON number')
        return result
    try:
        if isinstance(data,bytes):data=data.decode('utf-8')
        return json.loads(data,object_pairs_hook=pairs,parse_constant=bad,parse_float=floating)
    except (ValueError,UnicodeError,TypeError) as exc: raise ContractError('invalid JSON') from exc

class _Instant(Fraction):
    def __new__(cls, seconds, precision=6):
        result=super().__new__(cls,seconds);result.precision=max(6,precision)
        return result
    def isoformat(self):
        whole=self.numerator//self.denominator;day,second=divmod(whole,86400)
        stamp=datetime.fromordinal(day).replace(hour=second//3600,minute=second//60%60,second=second%60)
        text=stamp.isoformat()
        if self.denominator!=1:
            digits=str((self.numerator%self.denominator)*10**self.precision//self.denominator).zfill(self.precision)
            text+='.'+digits[:6]+digits[6:].rstrip('0')
        return text+'+00:00'

def aware(value):
    if not isinstance(value,str) or value!=value.strip(): raise ContractError('timestamp must be exact string')
    try: result=datetime.fromisoformat(value[:-1]+'+00:00' if value.endswith('Z') else value)
    except (ValueError,TypeError): raise ContractError('invalid timestamp')
    if result.utcoffset() is None: raise ContractError('timestamp is not timezone aware')
    date=re.match(r'^[0-9]{4}(?:-[0-9]{2}-[0-9]{2}|[0-9]{4}|-?W[0-9]{2}(?:-?[0-9])?)',value)
    if not date or len(value)<=date.end(): raise ContractError('date only')
    clock=value[date.end()+1:];offset_at=re.search(r'[+-]',clock)
    local=clock[:offset_at.start()] if offset_at else clock
    offset=clock[offset_at.start():] if offset_at else ''
    def fraction(text):
        match=re.search(r'[.,]([0-9]+)',text)
        return (Fraction(int(match[1]),10**len(match[1])),len(match[1])) if match else (Fraction(0),0)
    local_fraction,local_precision=fraction(local);offset_fraction,offset_precision=fraction(offset)
    delta=result.utcoffset();offset_whole=int((delta.days*86400+delta.seconds)+Fraction(delta.microseconds,1000000))
    if offset.startswith('-'):offset_fraction=-offset_fraction
    seconds=(result.toordinal()*86400+result.hour*3600+result.minute*60+result.second+local_fraction-offset_whole-offset_fraction)
    return _Instant(seconds,max(local_precision,offset_precision))

def integer(value): return type(value) is int and value>=0
def textid(value): return isinstance(value,str) and bool(value)
def exact(obj,fields): return isinstance(obj,dict) and set(obj)==set(fields)

def regular(path,max_bytes=2*1024**3):
    path=Path(path)
    try: info=path.lstat()
    except OSError as exc: raise ContractError('missing regular file') from exc
    if not stat.S_ISREG(info.st_mode) or info.st_size>max_bytes: raise ContractError('unsafe or oversized file')
    return info

def read_regular(path,max_bytes=64*1024**2):
    info=regular(path,max_bytes)
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode): raise ContractError('not regular')
        with os.fdopen(fd,'rb',closefd=False) as stream: data=stream.read(max_bytes+1)
    finally: os.close(fd)
    if len(data)>max_bytes: raise ContractError('oversized file')
    return data

def file_info(path):
    regular(path);h=hashlib.sha256();size=0
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk);size+=len(chunk)
    return {'size':size,'sha256':h.hexdigest()}

def inventory(data):
    data=Path(data);items=[]
    if data.is_symlink() or not data.is_dir():raise ContractError('unsafe input directory')
    for base,dirs,files in os.walk(data,followlinks=False):
        for name in dirs:
            if Path(base,name).is_symlink():raise ContractError('symlink input directory')
        for name in files:
            p=Path(base,name);info=file_info(p)
            items.append({'path':p.relative_to(data).as_posix(),**info})
    return sorted(items,key=lambda x:x['path'].encode('utf-8'))

def policy_value(value,as_of):
    if not exact(value,('policy_id','max_results','effective_at')) or not textid(value['policy_id']) or not integer(value['max_results']) or value['max_results']==0:raise ContractError('bad policy')
    if aware(value['effective_at'])>aware(as_of):raise ContractError('future policy')
    return value

def load_csv(path,encoding):
    raw=read_regular(path).decode(encoding)
    physical=raw.replace('\r\n','\n').replace('\r','\n').split('\n')
    if physical and physical[-1]=='':physical.pop()
    if not raw or any(not line for line in physical):raise ContractError('empty CSV or physical blank row')
    try:
        reader=csv.DictReader(io.StringIO(raw,newline=''),strict=True)
        expected=['tenant_id','label'] if encoding=='cp949' else ['tag','weight']
        if reader.fieldnames!=expected:raise ContractError('bad CSV header')
        rows=list(reader)
        if any(set(row)!=set(expected) or any(v is None for v in row.values()) for row in rows):raise ContractError('CSV columns')
        return rows
    except csv.Error as exc:raise ContractError('invalid CSV') from exc

def load_source(data,policy_path=None):
    data=Path(data);inv=inventory(data)
    meta=parse_json(read_regular(data/'META.json'))
    if not exact(meta,('schema_version','as_of_utc','expected_nonblank_document_rows')) or type(meta['schema_version']) is not int or meta['schema_version']!=1 or not integer(meta['expected_nonblank_document_rows']):raise ContractError('bad META')
    as_of=aware(meta['as_of_utc'])
    policy=policy_value(parse_json(read_regular(policy_path or data/'policy.json')),meta['as_of_utc'])
    tenant_rows=load_csv(data/'tenants.csv','cp949')
    tenants=set()
    for row in tenant_rows:
        if set(row)!= {'tenant_id','label'} or not textid(row['tenant_id']) or row['tenant_id']=='__public__' or row['tenant_id'] in tenants or row['label'] is None:raise ContractError('bad tenant CSV')
        tenants.add(row['tenant_id'])
    weights={}
    for row in load_csv(data/'tag_weights.csv','utf-8'):
        if set(row)!= {'tag','weight'} or not textid(row['tag']) or row['tag'] in weights or not re.fullmatch(r'[1-9][0-9]*',row['weight'] or ''):raise ContractError('bad weight CSV')
        weights[row['tag']]=int(row['weight'])
    counts={key:0 for key in ('OVERSIZE','BAD_JSON','BAD_SCHEMA','FUTURE','DUPLICATE_RECORD_ID')}
    selected={};seen=set();retained=0;nonblank=0
    fields={'record_id','tenant_id','doc_id','revision','updated_at','published_at','state','title','body','tags'}
    for item in inv:
        p=Path(item['path'])
        if not (p.name.startswith('documents-') and p.suffix=='.jsonl'):continue
        with (data/p).open('rb') as stream:
            for line_no,line in enumerate(stream):
                payload=line[:-1] if line.endswith(b'\n') else line
                if line.endswith(b'\n') and payload.endswith(b'\r'):payload=payload[:-1]
                if line_no==0 and payload.startswith(b'\xef\xbb\xbf'):payload=payload[3:]
                try:blank=not payload or payload.decode('utf-8').isspace()
                except UnicodeError:blank=False
                if blank:continue
                nonblank+=1
                if len(payload)>65536:counts['OVERSIZE']+=1;continue
                try:record=parse_json(payload)
                except ContractError:counts['BAD_JSON']+=1;continue
                try:
                    if not exact(record,fields):raise ContractError('fields')
                    if not all(textid(record[k]) for k in ('record_id','tenant_id','doc_id')) or record['tenant_id'] not in tenants|{'__public__'}:raise ContractError('IDs')
                    if not integer(record['revision']) or record['revision']>9223372036854775807 or record['state'] not in ('PUBLISHED','WITHDRAWN'):raise ContractError('version')
                    if not isinstance(record['title'],str) or not record['title'].strip() or not isinstance(record['body'],str):raise ContractError('content')
                    if not isinstance(record['tags'],list) or any(not textid(t) or t not in weights for t in record['tags']):raise ContractError('tags')
                    updated=aware(record['updated_at']);published=aware(record['published_at'])
                except (ContractError,TypeError):counts['BAD_SCHEMA']+=1;continue
                if updated>as_of or published>as_of:counts['FUTURE']+=1;continue
                if record['record_id'] in seen:counts['DUPLICATE_RECORD_ID']+=1;continue
                seen.add(record['record_id']);retained+=1
                key=(record['tenant_id'],record['doc_id']);order=(record['revision'],updated)
                if key not in selected or order>selected[key][0]:selected[key]=(order,record)
    docs=[rec for _,rec in selected.values() if rec['state']=='PUBLISHED']
    docs.sort(key=lambda r:(r['tenant_id'].encode(),r['doc_id'].encode()))
    stats={'schema_version':1,'status':'COMPLETE','as_of_utc':meta['as_of_utc'],'policy_id':policy['policy_id'],'max_results':policy['max_results'],'doc_count':len(docs),'selected_keys':len(selected),'withdrawn_count':len(selected)-len(docs),'tenant_count':len(tenants)}
    rejections={'schema_version':1,'counts':counts,'retained_records':retained}
    return {'meta':meta,'inventory':inv,'policy':policy,'tenants':tenants,'weights':weights,'docs':docs,'stats':stats,'rejections':rejections,'input_root':str(data.absolute())}

def query_value(query):
    if not isinstance(query,dict) or set(query) not in ({'qid','tenant_id','terms'},{'qid','tenant_id','terms','limit'}):raise ContractError('bad query fields')
    if not textid(query['qid']) or not textid(query['tenant_id']) or not isinstance(query['terms'],list) or any(not isinstance(t,str) for t in query['terms']):raise ContractError('bad query')
    if 'limit' in query and (not integer(query['limit']) or query['limit']==0):raise ContractError('bad limit')
    return query

class Engine:
    def __init__(self,docs,tenants,weights,policy):
        self.docs=docs;self.tenants=set(tenants);self.weights=weights;self.policy=policy;self.postings={}
        for i,doc in enumerate(docs):
            for tag in set(doc['tags']):self.postings.setdefault(tag,[]).append(i)
    def search(self,query):
        query_value(query);result={'qid':query['qid'],'status':'NO_MATCH','policy_id':self.policy['policy_id'],'sources':[]}
        tenant=query['tenant_id']
        if tenant not in self.tenants:result['status']='FORBIDDEN';return result
        scores={}
        for term in set(query['terms']):
            for i in self.postings.get(term,()):
                if self.docs[i]['tenant_id'] in (tenant,'__public__'):scores[i]=scores.get(i,0)+self.weights[term]
        ranked=sorted(scores,key=lambda i:(-scores[i],self.docs[i]['doc_id'].encode('utf-8'),self.docs[i]['tenant_id'].encode('utf-8')))
        for i in ranked[:min(query.get('limit',self.policy['max_results']),self.policy['max_results'])]:
            doc=self.docs[i];result['sources'].append({k:doc[k] for k in ('tenant_id','doc_id','revision','title') }|{'score':scores[i],'snippet':doc['body'][:80]})
        if result['sources']:result['status']='OK'
        return result

def write_json(path,value):Path(path).write_bytes(canonical(value)+b'\n')

def write_bundle(source,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(out/'index.sqlite')
    try:
        db.executescript('CREATE TABLE docs(tenant_id TEXT,doc_id TEXT,revision INTEGER,title TEXT,body TEXT,tags TEXT,PRIMARY KEY(tenant_id,doc_id));CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);')
        db.executemany('INSERT INTO docs VALUES(?,?,?,?,?,?)',[(d['tenant_id'],d['doc_id'],d['revision'],d['title'],d['body'],canonical(d['tags']).decode()) for d in source['docs']])
        meta={'schema_version':'1','as_of_utc':source['meta']['as_of_utc'],'policy_fingerprint':digest(canonical(source['policy'])),'registered_tenants':canonical(sorted(source['tenants'],key=lambda x:x.encode())).decode(),'tag_weights':canonical(source['weights']).decode()}
        if source.get('input_root'):meta['source_root']=source['input_root']
        db.executemany('INSERT INTO meta VALUES(?,?)',meta.items());db.commit()
    finally:db.close()
    write_json(out/'stats.json',source['stats']);write_json(out/'rejections.json',source['rejections'])
    manifest={'schema_version':1,'as_of_utc':source['meta']['as_of_utc'],'source_inventory':source['inventory'],'source_fingerprint':digest(canonical(source['inventory'])),'effective_policy':source['policy'],'policy_fingerprint':digest(canonical(source['policy'])),'artifacts':{name:file_info(out/name)['sha256'] for name in ('index.sqlite','stats.json','rejections.json')}}
    write_json(out/'manifest.json',manifest)
    return manifest

def bundle_engine(out):
    out=Path(out);manifest=parse_json(read_regular(out/'manifest.json'));policy=manifest['effective_policy']
    regular(out/'index.sqlite');db=sqlite3.connect((out/'index.sqlite').absolute().as_uri()+'?mode=ro',uri=True)
    try:
        meta=dict(db.execute('SELECT key,value FROM meta'))
        docs=[dict(zip(('tenant_id','doc_id','revision','title','body','tags'),row)) for row in db.execute('SELECT tenant_id,doc_id,revision,title,body,tags FROM docs')]
        for doc in docs:doc['tags']=parse_json(doc['tags'])
    finally:db.close()
    return Engine(docs,parse_json(meta['registered_tenants']),parse_json(meta['tag_weights']),policy)

def verify_bundle(out,max_docs=None):
    out=Path(out);art={}
    for name in ('manifest.json','stats.json','rejections.json'):
        raw=read_regular(out/name,4*1024**2);value=parse_json(raw)
        if raw!=canonical(value)+b'\n':raise ContractError('noncanonical artifact')
        art[name]=value
    manifest=art['manifest.json'];stats=art['stats.json'];reject=art['rejections.json']
    if not exact(manifest,('schema_version','as_of_utc','source_inventory','source_fingerprint','effective_policy','policy_fingerprint','artifacts')) or type(manifest['schema_version']) is not int or manifest['schema_version']!=1:raise ContractError('manifest schema')
    aware(manifest['as_of_utc']);policy=policy_value(manifest['effective_policy'],manifest['as_of_utc'])
    if manifest['policy_fingerprint']!=digest(canonical(policy)):raise ContractError('policy fingerprint')
    inv=manifest['source_inventory']
    if not isinstance(inv,list):raise ContractError('source inventory')
    paths=[]
    for item in inv:
        if not exact(item,('path','size','sha256')) or not textid(item['path']) or not integer(item['size']) or not isinstance(item['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',item['sha256']):raise ContractError('inventory item')
        p=Path(item['path'])
        if p.is_absolute() or '..' in p.parts or p.as_posix()!=item['path']:raise ContractError('inventory path')
        paths.append(item['path'])
    if paths!=sorted(set(paths),key=lambda s:s.encode('utf-8')) or manifest['source_fingerprint']!=digest(canonical(inv)):raise ContractError('source fingerprint')
    if not exact(manifest['artifacts'],('index.sqlite','stats.json','rejections.json')):raise ContractError('artifact hashes')
    for name,sha in manifest['artifacts'].items():
        if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha) or file_info(out/name)['sha256']!=sha:raise ContractError('artifact hash mismatch')
    fields=('schema_version','status','as_of_utc','policy_id','max_results','doc_count','selected_keys','withdrawn_count','tenant_count')
    if not exact(stats,fields) or type(stats['schema_version']) is not int or stats['schema_version']!=1 or stats['status']!='COMPLETE' or stats['as_of_utc']!=manifest['as_of_utc'] or stats['policy_id']!=policy['policy_id'] or stats['max_results']!=policy['max_results']:raise ContractError('stats shape/agreement')
    if any(not integer(stats[k]) for k in ('doc_count','selected_keys','withdrawn_count','tenant_count','max_results')) or stats['selected_keys']!=stats['doc_count']+stats['withdrawn_count']:raise ContractError('stats count')
    reasons=('OVERSIZE','BAD_JSON','BAD_SCHEMA','FUTURE','DUPLICATE_RECORD_ID')
    if not exact(reject,('schema_version','counts','retained_records')) or type(reject['schema_version']) is not int or reject['schema_version']!=1 or not exact(reject['counts'],reasons) or not integer(reject['retained_records']) or any(not integer(v) for v in reject['counts'].values()):raise ContractError('rejections')
    regular(out/'index.sqlite');db=sqlite3.connect((out/'index.sqlite').absolute().as_uri()+'?mode=ro',uri=True)
    try:
        started=time.monotonic();steps=[0]
        def progress():
            steps[0]+=1
            return int(steps[0]>2000 or time.monotonic()-started>8)
        db.set_progress_handler(progress,10000)
        if hasattr(db,'setlimit'):db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,1024*1024)
        for table in ('docs','meta'):
            if db.execute('SELECT type FROM sqlite_master WHERE name=?',(table,)).fetchone()!=('table',):raise ContractError('required base table')
        if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ContractError('SQLite integrity')
        for table,cols in {'docs':{'tenant_id':'TEXT','doc_id':'TEXT','revision':'INTEGER','title':'TEXT','body':'TEXT','tags':'TEXT'},'meta':{'key':'TEXT','value':'TEXT'}}.items():
            actual={r[1]:r[2].upper() for r in db.execute('PRAGMA table_info('+table+')')}
            if any(actual.get(k)!=v for k,v in cols.items()):raise ContractError('SQLite schema')
        meta_rows=list(db.execute('SELECT key,value FROM meta'))
        if any(not isinstance(k,str) or not isinstance(v,str) for k,v in meta_rows) or len(dict(meta_rows))!=len(meta_rows):raise ContractError('SQLite meta types')
        meta=dict(meta_rows)
        if any(meta.get(k)!=v for k,v in {'schema_version':'1','as_of_utc':manifest['as_of_utc'],'policy_fingerprint':manifest['policy_fingerprint']}.items()):raise ContractError('SQLite meta agreement')
        tenants=parse_json(meta.get('registered_tenants','null'));weights=parse_json(meta.get('tag_weights','null'))
        if not isinstance(tenants,list) or any(not textid(x) or x=='__public__' for x in tenants) or tenants!=sorted(set(tenants),key=lambda x:x.encode()) or canonical(tenants).decode()!=meta['registered_tenants'] or len(tenants)!=stats['tenant_count']:raise ContractError('tenant registry')
        if not isinstance(weights,dict) or any(not textid(k) or not integer(v) or v==0 for k,v in weights.items()) or canonical(weights).decode()!=meta['tag_weights']:raise ContractError('tag weights')
        count=0;seen=set()
        for tenant,doc,rev,title,body,tags in db.execute('SELECT tenant_id,doc_id,revision,title,body,tags FROM docs'):
            if max_docs is not None and count>=max_docs:raise ContractError('excess rows')
            if not textid(tenant) or tenant not in set(tenants)|{'__public__'} or not textid(doc) or not integer(rev) or not isinstance(title,str) or not title.strip() or not isinstance(body,str) or not isinstance(tags,str):raise ContractError('doc fields')
            key=(tenant,doc)
            if key in seen:raise ContractError('duplicate document key')
            seen.add(key);count+=1;parsed=parse_json(tags)
            if not isinstance(parsed,list) or any(not textid(t) or t not in weights for t in parsed) or canonical(parsed).decode()!=tags:raise ContractError('doc tags')
        if count!=stats['doc_count']:raise ContractError('doc_count')
    except sqlite3.Error as exc:raise ContractError('SQLite error') from exc
    finally:db.close()
    return art
