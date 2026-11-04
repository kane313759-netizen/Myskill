"""Deterministic, offline support-document evidence retrieval."""
import argparse
import csv
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import sqlite3
import stat
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath

# Exact task integers have no decimal digit-count cap. The task resource bounds
# still apply; remove Python/CSV convenience limits rather than inventing rules.
if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)
csv.field_size_limit(sys.maxsize)

ROOT = Path(__file__).resolve().parents[1]
# REVISION-RANGE-ERRATUM-1, issued by the mock task director.
MAX_REVISION = 9223372036854775807
ARTIFACTS = ('index.sqlite', 'stats.json', 'rejections.json', 'manifest.json')
REASONS = ('OVERSIZE', 'BAD_JSON', 'BAD_SCHEMA', 'FUTURE', 'DUPLICATE_RECORD_ID')
DOC_FIELDS = {'record_id','tenant_id','doc_id','revision','updated_at','published_at','state','title','body','tags'}
HASH = re.compile(r'[0-9a-f]{64}\Z')
PROTECTION_FORMAT = 'local-kb-source-protection-v1'


class ContractError(ValueError):
    pass


def require(condition, message='contract violation'):
    if not condition:
        raise ContractError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def parse(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate JSON key')
            value[key] = item
        return value
    def constant(_):
        raise ContractError('non-finite JSON number')
    def floating(value):
        number = float(value)
        require(math.isfinite(number), 'non-finite JSON number')
        return number
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=floating)


def exact(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def string(value):
    return isinstance(value, str) and bool(value)


def moment(value):
    require(string(value) and value == value.strip(), 'invalid timestamp')
    result = datetime.fromisoformat(value[:-1] + '+00:00' if value.endswith('Z') else value)
    require(result.tzinfo is not None and result.utcoffset() is not None, 'timestamp needs timezone')
    return result


def safe_path(value):
    raw = Path(value).absolute()
    # Inspect lexical ancestors before normalizing '..', so a link cannot disappear.
    for part in (raw, *raw.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode), 'symlink path is not allowed')
    return Path(os.path.abspath(raw))


def regular(path):
    path = safe_path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode), 'not a regular file: ' + str(path))
    return info


def open_read(path):
    regular(path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'file changed type')
        return os.fdopen(descriptor, 'rb')
    except BaseException:
        os.close(descriptor)
        raise


def read(path):
    with open_read(path) as stream:
        return stream.read()


def sha(path):
    digest = hashlib.sha256()
    with open_read(path) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def json_file(path, canonical_required=False):
    raw = read(path)
    value = parse(raw)
    if canonical_required:
        require(raw == canonical(value) + b'\n', 'noncanonical JSON file: ' + str(path))
    return value


def write_json(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value) + b'\n')


def overlaps(a, b):
    return a == b or a in b.parents or b in a.parents


def protect_output(path, protected=(), source_roots=(), source_ids=(), source_paths=()):
    path = safe_path(path)
    # All supplied task material beside this implementation is protected, even
    # when the command is launched in another working directory.
    protected_roots = [ROOT / x for x in ('data','queries','expected','docs','tools','src','communications','.hackathon-kit','.agents','.git')]
    require(not any(path == p or p in path.parents for p in protected_roots), 'protected output location')
    protected_names = {'kb.py','TASK.md','README.md','ENVIRONMENT.md','TASK_TIMING.json','TEST_CONTROL.md','DATA_INVENTORY.json','ORIGINALS.json','EXPLANATION.md','RUN_EVIDENCE.json'}
    if path.parent == ROOT:
        require(path.name not in protected_names and not path.name.startswith('OFFICIAL_'), 'protected project file')
    require(not any(path == root or root in path.parents for root in source_roots), 'output is inside original DATA')
    require(path not in source_paths, 'output is an original source file')
    for item in protected:
        p = safe_path(item)
        require(path != p and p not in path.parents, 'output aliases protected input')
        if path.exists() and p.exists() and path.is_file() and p.is_file():
            require(not os.path.samefile(path, p), 'output aliases protected input')
    if path.exists():
        info = path.lstat()
        require((info.st_dev, info.st_ino) not in source_ids, 'output aliases an original source file')
        if stat.S_ISREG(info.st_mode):
            require(info.st_nlink == 1, 'hard-linked output is not allowed')
        else:
            require(stat.S_ISDIR(info.st_mode), 'special output is not allowed')
    return path


def inventory(data):
    data = safe_path(data)
    require(data.is_dir(), 'input must be a directory')
    entries = []
    def walk(directory):
        with os.scandir(directory) as scan:
            children = list(scan)
        for entry in children:
            info = entry.stat(follow_symlinks=False)
            path = Path(entry.path)
            if stat.S_ISDIR(info.st_mode):
                walk(path)
            else:
                require(stat.S_ISREG(info.st_mode), 'source symlink or special entry')
                entries.append({'path': path.relative_to(data).as_posix(), 'size': info.st_size, 'sha256': sha(path)})
    walk(data)
    entries.sort(key=lambda item: item['path'].encode('utf-8'))
    return entries


def policy_value(value, as_of):
    require(exact(value, ('policy_id','max_results','effective_at')), 'policy fields')
    require(string(value['policy_id']) and integer(value['max_results'], 1), 'invalid policy')
    require(moment(value['effective_at']) <= as_of, 'policy effective_at is after as_of')
    canonical(value)
    return value


def csv_rows(path, encoding, header):
    raw = read(path)
    lines = raw.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    require(lines and all(line.rstrip(b'\r') != b'' for line in lines), 'empty CSV physical line')
    text = raw.decode(encoding)
    rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    require(rows and rows[0] == list(header), 'CSV header')
    require(all(len(row) == len(header) for row in rows[1:]), 'CSV column count')
    return rows[1:]


def source_settings(data, override):
    meta = json_file(data / 'META.json')
    require(isinstance(meta, dict) and 'as_of_utc' in meta, 'META as_of_utc missing')
    as_of_text = meta['as_of_utc']
    as_of = moment(as_of_text)
    tenants = set()
    for tenant, _ in csv_rows(data / 'tenants.csv', 'cp949', ('tenant_id','label')):
        require(string(tenant) and tenant != '__public__' and tenant not in tenants, 'invalid/duplicate tenant')
        tenants.add(tenant)
    weights = {}
    for tag, weight in csv_rows(data / 'tag_weights.csv', 'utf-8', ('tag','weight')):
        require(string(tag) and tag not in weights and re.fullmatch(r'[1-9][0-9]*', weight, flags=re.ASCII), 'invalid/duplicate tag weight')
        weights[tag] = int(weight)
    # The original policy is still a required source file even with an override.
    original = json_file(data / 'policy.json')
    policy_value(original, as_of)
    policy = policy_value(json_file(override) if override else original, as_of)
    return as_of_text, as_of, tenants, weights, policy


def validate_document(value, tenants, weights):
    require(exact(value, DOC_FIELDS), 'document fields')
    require(all(string(value[k]) for k in ('record_id','tenant_id','doc_id')), 'document identifier')
    require(value['tenant_id'] in tenants or value['tenant_id'] == '__public__', 'document tenant')
    require(integer(value['revision']) and value['revision'] <= MAX_REVISION, 'document revision')
    require(value['state'] in ('PUBLISHED','WITHDRAWN'), 'document state')
    require(isinstance(value['title'],str) and value['title'].strip() != '' and isinstance(value['body'],str), 'document text')
    require(isinstance(value['tags'],list) and all(isinstance(x,str) and x in weights for x in value['tags']), 'document tags')
    updated, published = moment(value['updated_at']), moment(value['published_at'])
    canonical(value)
    return updated, published


def select_documents(data, source_inventory, as_of, tenants, weights):
    counts = {name: 0 for name in REASONS}
    retained = 0
    reserved = set()
    selected = {}
    for item in source_inventory:
        name = PurePosixPath(item['path']).name
        if not (name.startswith('documents-') and name.endswith('.jsonl')):
            continue
        with open_read(data / item['path']) as stream:
            for lineno, raw in enumerate(stream):
                payload = raw[:-1] if raw.endswith(b'\n') else raw
                if raw.endswith(b'\n') and payload.endswith(b'\r'):
                    payload = payload[:-1]
                if lineno == 0 and payload.startswith(b'\xef\xbb\xbf'):
                    payload = payload[3:]
                try:
                    text = payload.decode('utf-8')
                except UnicodeDecodeError:
                    text = None
                if not payload or text is not None and text.isspace():
                    continue
                if len(payload) > 65536:
                    counts['OVERSIZE'] += 1
                    continue
                try:
                    require(text is not None, 'invalid UTF-8')
                    value = parse(text)
                except (ValueError, TypeError, OverflowError, RecursionError):
                    counts['BAD_JSON'] += 1
                    continue
                try:
                    updated, published = validate_document(value, tenants, weights)
                except (ValueError, TypeError, OverflowError, UnicodeError, RecursionError):
                    counts['BAD_SCHEMA'] += 1
                    continue
                if updated > as_of or published > as_of:
                    counts['FUTURE'] += 1
                    continue
                if value['record_id'] in reserved:
                    counts['DUPLICATE_RECORD_ID'] += 1
                    continue
                reserved.add(value['record_id'])
                retained += 1
                key = (value['tenant_id'], value['doc_id'])
                previous = selected.get(key)
                if previous is None or (value['revision'], updated) > (previous[0]['revision'], previous[1]):
                    selected[key] = (value, updated)
    return selected, counts, retained


def build(args):
    data = safe_path(args.input)
    out = protect_output(args.out, [data] + ([args.policy] if args.policy else []))
    require(not overlaps(data, out), 'input and output overlap')
    source_inventory = inventory(data)
    as_of_text, as_of, tenants, weights, policy = source_settings(data, args.policy)
    if args.resume:
        bundle = Bundle(out)
        require(bundle.manifest['source_inventory'] == source_inventory and bundle.policy == policy, 'resume source/policy mismatch')
        return
    require(not out.exists() or out.is_dir() and not any(out.iterdir()), 'output is not empty')
    selected, counts, retained = select_documents(data, source_inventory, as_of, tenants, weights)
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.kb-build-', dir=out.parent))
    try:
        db = sqlite3.connect(stage / 'index.sqlite')
        try:
            db.executescript('CREATE TABLE docs (tenant_id TEXT,doc_id TEXT,revision INTEGER,title TEXT,body TEXT,tags TEXT,PRIMARY KEY (tenant_id,doc_id)); CREATE TABLE meta (key TEXT PRIMARY KEY,value TEXT);')
            meta = {'schema_version':'1','as_of_utc':as_of_text,'policy_fingerprint':fingerprint(policy),'registered_tenants':canonical(sorted(tenants,key=lambda s:s.encode('utf-8'))).decode('utf-8'),'tag_weights':canonical(weights).decode('utf-8')}
            meta['kb_source_protection_format'] = PROTECTION_FORMAT
            db.executemany('INSERT INTO meta VALUES (?,?)', meta.items())
            # Optional local provenance protects sources outside this project too.
            # Detached public-schema bundles remain usable without this table.
            db.execute('CREATE TABLE source_protection (source_root TEXT,source_path TEXT,device INTEGER,inode INTEGER)')
            origins = []
            for item in source_inventory:
                source_path = data / item['path']
                info = source_path.lstat()
                origins.append((str(data),str(source_path),info.st_dev,info.st_ino))
            if args.policy:
                policy_path = safe_path(args.policy)
                info = policy_path.lstat()
                # NULL root denotes one protected file, not its entire parent.
                origins.append((None,str(policy_path),info.st_dev,info.st_ino))
            db.executemany('INSERT INTO source_protection VALUES (?,?,?,?)', origins)
            published = [v for v, _ in selected.values() if v['state'] == 'PUBLISHED']
            published.sort(key=lambda v:(v['tenant_id'].encode('utf-8'),v['doc_id'].encode('utf-8')))
            db.executemany('INSERT INTO docs VALUES (?,?,?,?,?,?)', ((v['tenant_id'],v['doc_id'],v['revision'],v['title'],v['body'],canonical(v['tags']).decode('utf-8')) for v in published))
            db.commit()
        finally:
            db.close()
        stats = {'schema_version':1,'status':'COMPLETE','as_of_utc':as_of_text,'policy_id':policy['policy_id'],'max_results':policy['max_results'],'doc_count':len(published),'selected_keys':len(selected),'withdrawn_count':len(selected)-len(published),'tenant_count':len(tenants)}
        rejections = {'schema_version':1,'counts':counts,'retained_records':retained}
        write_json(stage / 'stats.json', stats)
        write_json(stage / 'rejections.json', rejections)
        manifest = {'schema_version':1,'as_of_utc':as_of_text,'source_inventory':source_inventory,'source_fingerprint':fingerprint(source_inventory),'effective_policy':policy,'policy_fingerprint':fingerprint(policy),'artifacts':{name:sha(stage/name) for name in ARTIFACTS if name != 'manifest.json'}}
        write_json(stage / 'manifest.json', manifest)
        # All validation/serialization finished; only a complete directory is exposed.
        require(not out.exists() or out.is_dir() and not any(out.iterdir()), 'output changed during build')
        os.replace(stage, out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


class Bundle:
    """Validate detached bundle entirely through its public schema, without sources."""
    def __init__(self, directory):
        self.path = safe_path(directory)
        require(self.path.is_dir(), 'index must be a directory')
        for name in ARTIFACTS:
            regular(self.path / name)
        m = self.manifest = json_file(self.path/'manifest.json', True)
        require(exact(m, ('schema_version','as_of_utc','source_inventory','source_fingerprint','effective_policy','policy_fingerprint','artifacts')) and type(m['schema_version']) is int and m['schema_version'] == 1, 'manifest shape')
        as_of = moment(m['as_of_utc'])
        self.policy = policy_value(m['effective_policy'], as_of)
        require(isinstance(m['policy_fingerprint'],str) and HASH.fullmatch(m['policy_fingerprint']) and m['policy_fingerprint'] == fingerprint(self.policy), 'policy fingerprint')
        inv = m['source_inventory']
        require(isinstance(inv,list), 'source inventory')
        paths = []
        for item in inv:
            require(exact(item, ('path','size','sha256')) and string(item['path']) and integer(item['size']) and isinstance(item['sha256'],str) and HASH.fullmatch(item['sha256']), 'source inventory item')
            path = PurePosixPath(item['path'])
            require(bool(path.parts) and not path.is_absolute() and path.as_posix() == item['path'] and all(x not in ('','..','.') for x in path.parts) and '\x00' not in item['path'], 'source inventory path')
            paths.append(item['path'])
        require(paths == sorted(set(paths),key=lambda s:s.encode('utf-8')), 'source inventory order')
        require(m['source_fingerprint'] == fingerprint(inv), 'source fingerprint')
        require(exact(m['artifacts'], ARTIFACTS[:-1]), 'artifact hash fields')
        for name, digest in m['artifacts'].items():
            require(isinstance(digest,str) and HASH.fullmatch(digest) and sha(self.path/name) == digest, 'artifact hash mismatch: ' + name)
        s = self.stats = json_file(self.path/'stats.json', True)
        require(exact(s, ('schema_version','status','as_of_utc','policy_id','max_results','doc_count','selected_keys','withdrawn_count','tenant_count')), 'stats fields')
        require(type(s['schema_version']) is int and s['schema_version'] == 1 and s['status'] == 'COMPLETE', 'stats version/status')
        require(all(integer(s[k]) for k in ('doc_count','selected_keys','withdrawn_count','tenant_count')) and integer(s['max_results'],1), 'stats count types')
        require(s['as_of_utc'] == m['as_of_utc'] and s['policy_id'] == self.policy['policy_id'] and s['max_results'] == self.policy['max_results'], 'stats policy/as_of')
        require(s['selected_keys'] == s['doc_count'] + s['withdrawn_count'], 'selection invariant')
        r = self.rejections = json_file(self.path/'rejections.json', True)
        require(exact(r, ('schema_version','counts','retained_records')) and type(r['schema_version']) is int and r['schema_version'] == 1 and exact(r['counts'], REASONS), 'rejections shape')
        require(integer(r['retained_records']) and all(integer(v) for v in r['counts'].values()) and r['retained_records'] >= s['selected_keys'], 'rejections counts')
        db = sqlite3.connect((self.path/'index.sqlite').as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA trusted_schema=OFF')
            require(db.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'SQLite integrity')
            for table, columns in {'docs':{'tenant_id':'TEXT','doc_id':'TEXT','revision':'INTEGER','title':'TEXT','body':'TEXT','tags':'TEXT'},'meta':{'key':'TEXT','value':'TEXT'}}.items():
                require(db.execute("SELECT type FROM sqlite_master WHERE name=?", (table,)).fetchone() == ('table',), 'required SQLite table')
                actual = {row[1]:row[2].upper() for row in db.execute('PRAGMA table_info('+table+')')}
                require(all(actual.get(k) == t for k,t in columns.items()), 'required SQLite schema')
            meta_rows = list(db.execute('SELECT key,value FROM meta'))
            require(all(isinstance(k,str) and isinstance(v,str) for k,v in meta_rows) and len({k for k,v in meta_rows}) == len(meta_rows), 'SQLite meta types/duplicates')
            meta = dict(meta_rows)
            require({'schema_version','as_of_utc','policy_fingerprint','registered_tenants','tag_weights'} <= set(meta), 'required SQLite meta')
            require(meta['schema_version'] == '1' and meta['as_of_utc'] == m['as_of_utc'] and meta['policy_fingerprint'] == m['policy_fingerprint'], 'SQLite meta agreement')
            tenant_list, self.weights = parse(meta['registered_tenants']), parse(meta['tag_weights'])
            require(isinstance(tenant_list,list) and all(string(x) and x != '__public__' for x in tenant_list), 'registered tenants')
            require(tenant_list == sorted(set(tenant_list),key=lambda x:x.encode('utf-8')) and canonical(tenant_list).decode('utf-8') == meta['registered_tenants'], 'registered tenant canonical/order')
            self.tenants = set(tenant_list)
            require(isinstance(self.weights,dict) and all(string(k) and integer(v,1) for k,v in self.weights.items()) and canonical(self.weights).decode('utf-8') == meta['tag_weights'], 'tag weights')
            require(s['tenant_count'] == len(self.tenants), 'tenant count')
            self.source_roots, self.source_ids, self.source_paths = set(), set(), set()
            # Additional public-schema tables are unrestricted. Only our explicit
            # format marker authorizes interpreting a table as local provenance.
            if meta.get('kb_source_protection_format') == PROTECTION_FORMAT:
                require(db.execute("SELECT type FROM sqlite_master WHERE name='source_protection'").fetchone() == ('table',), 'source provenance table missing')
                actual = {row[1]:row[2].upper() for row in db.execute('PRAGMA table_info(source_protection)')}
                require(all(actual.get(k) == v for k,v in {'source_root':'TEXT','source_path':'TEXT','device':'INTEGER','inode':'INTEGER'}.items()), 'source provenance schema')
                for root, path, device, inode in db.execute('SELECT source_root,source_path,device,inode FROM source_protection'):
                    require((root is None or string(root)) and string(path) and integer(device) and integer(inode), 'source provenance types')
                    file_path = Path(path)
                    require(file_path.is_absolute() and str(file_path) == os.path.abspath(file_path), 'source provenance file path')
                    if root is not None:
                        root_path = Path(root)
                        require(root_path.is_absolute() and root_path in file_path.parents and str(root_path) == os.path.abspath(root_path), 'source provenance root path')
                        self.source_roots.add(root_path)
                    self.source_paths.add(file_path)
                    self.source_ids.add((device,inode))
            self.docs = []
            keys = set()
            for tenant, doc, revision, title, body, tags in db.execute('SELECT tenant_id,doc_id,revision,title,body,tags FROM docs'):
                require(string(tenant) and tenant in self.tenants | {'__public__'} and string(doc) and integer(revision) and revision <= MAX_REVISION, 'SQLite document key/revision')
                require(isinstance(title,str) and title.strip() and isinstance(body,str) and isinstance(tags,str), 'SQLite document text')
                require((tenant,doc) not in keys, 'duplicate document key')
                keys.add((tenant,doc))
                parsed_tags = parse(tags)
                require(isinstance(parsed_tags,list) and all(isinstance(t,str) and t in self.weights for t in parsed_tags) and canonical(parsed_tags).decode('utf-8') == tags, 'SQLite tags')
                self.docs.append((tenant,doc,revision,title,body,parsed_tags))
            require(len(self.docs) == s['doc_count'], 'document count')
        finally:
            db.close()
        self.lookup = defaultdict(lambda: defaultdict(list))
        for i, (tenant, _, _, _, _, tags) in enumerate(self.docs):
            for tag in set(tags):
                self.lookup[tenant][tag].append(i)

    def check_policy(self, path):
        if path:
            p = policy_value(json_file(path), moment(self.manifest['as_of_utc']))
            require(fingerprint(p) == self.manifest['policy_fingerprint'], 'policy mismatch')

    def query(self, value):
        require(isinstance(value,dict) and set(value) in ({'qid','tenant_id','terms'},{'qid','tenant_id','terms','limit'}), 'query fields')
        require(string(value['qid']) and string(value['tenant_id']) and isinstance(value['terms'],list) and all(isinstance(x,str) for x in value['terms']), 'query schema')
        require('limit' not in value or integer(value['limit'],1), 'query limit')
        canonical(value)
        result = {'qid':value['qid'],'policy_id':self.policy['policy_id'],'status':'NO_MATCH','sources':[]}
        tenant = value['tenant_id']
        if tenant not in self.tenants:
            result['status'] = 'FORBIDDEN'
            return result
        scores = defaultdict(int)
        for term in set(value['terms']):
            if term in self.weights:
                for scope in (tenant, '__public__'):
                    for i in self.lookup.get(scope, {}).get(term, ()):
                        scores[i] += self.weights[term]
        order = sorted(scores,key=lambda i:(-scores[i],self.docs[i][1].encode('utf-8'),self.docs[i][0].encode('utf-8')))
        limit = min(value.get('limit', self.policy['max_results']), self.policy['max_results'])
        for i in order[:limit]:
            t, doc, revision, title, body, _ = self.docs[i]
            result['sources'].append({'tenant_id':t,'doc_id':doc,'revision':revision,'title':title,'score':scores[i],'snippet':body[:80]})
        if result['sources']:
            result['status'] = 'OK'
        return result


def search(args):
    index = safe_path(args.index)
    queries = safe_path(args.queries)
    out = protect_output(args.out, [index, queries] + ([args.policy] if args.policy else []))
    require(not out.exists() or stat.S_ISREG(out.lstat().st_mode), 'answer output must be a regular file')
    bundle = Bundle(index)
    bundle.check_policy(args.policy)
    protect_output(out, [index, queries] + ([args.policy] if args.policy else []), bundle.source_roots, bundle.source_ids, bundle.source_paths)
    # Validate query input type before creating any temporary output.
    regular(queries)
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.kb-answers-', dir=out.parent)
    temp = Path(name)
    try:
        with os.fdopen(descriptor,'wb') as target, open_read(queries) as source:
            for raw in source:
                if not raw.strip():
                    continue
                target.write(canonical(bundle.query(parse(raw))) + b'\n')
        protect_output(out, [index, queries] + ([args.policy] if args.policy else []), bundle.source_roots, bundle.source_ids, bundle.source_paths)
        os.replace(temp, out)
    finally:
        if temp.exists():
            temp.unlink()


def serve(args):
    bundle = Bundle(args.index)
    bundle.check_policy(args.policy)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def respond(self, code, value, content_type='application/json; charset=utf-8'):
            body = canonical(value) + b'\n' if content_type.startswith('application/json') else value.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def method(self):
            self.respond(405, {'error':'METHOD_NOT_ALLOWED'})
        def do_GET(self):
            if self.path == '/health':
                self.respond(200, {'policy_id':bundle.policy['policy_id'],'status':'ok'})
            elif self.path == '/stats':
                self.respond(200, bundle.stats)
            elif self.path == '/':
                s = bundle.stats
                page = '<!doctype html><html lang="ko"><meta charset="utf-8"><title>운영문서 근거 검색</title><style>body{font-family:sans-serif;max-width:48rem;margin:3rem auto;padding:1rem;line-height:1.7}dl{background:#eef4fa;padding:1rem}</style><h1>운영문서 근거 검색</h1><p>고객지원 담당자가 질문에 맞는 문서 근거를 찾는 로컬 서비스입니다. 상담 답변을 생성하지 않습니다.</p><dl><dt>유효 정책</dt><dd>'+html.escape(s['policy_id'])+'</dd><dt>최대 결과 수</dt><dd>'+str(s['max_results'])+'</dd><dt>기준 시각</dt><dd>'+html.escape(s['as_of_utc'])+'</dd><dt>문서 수</dt><dd>'+str(s['doc_count'])+'</dd></dl><p>등록 고객사는 자기 고객사와 공개 문서만 볼 수 있습니다. 기준일 이후 정보는 포함하지 않으며 철회된 최신 문서는 제외됩니다. 태그가 정확히 일치하는 문서의 근거를 반환합니다.</p><p>POST /search에 qid, tenant_id, terms와 선택적인 limit을 전달하세요. 상태 확인: /health · 집계: /stats</p></html>'
                self.respond(200, page, 'text/html; charset=utf-8')
            elif self.path == '/search':
                self.method()
            else:
                self.respond(404, {'error':'NOT_FOUND'})
        def do_POST(self):
            if self.path != '/search':
                if self.path in ('/','/health','/stats'):
                    self.method()
                else:
                    self.respond(404, {'error':'NOT_FOUND'})
                return
            try:
                length = self.headers.get('Content-Length')
                require(length is not None and re.fullmatch(r'[0-9]+',length), 'Content-Length required')
                require(self.headers.get('Transfer-Encoding') is None, 'unsupported transfer encoding')
                raw = self.rfile.read(int(length))
                require(len(raw) == int(length), 'incomplete body')
                value = bundle.query(parse(raw))
            except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
                self.respond(400, {'error':'BAD_QUERY'})
                return
            self.respond(200, value)
        do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = do_TRACE = do_CONNECT = method
        def __getattr__(self, name):
            if name.startswith('do_'):
                return self.method
            raise AttributeError(name)
    server = ThreadingHTTPServer((args.host,args.port),Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    b=commands.add_parser('build');b.add_argument('--input',required=True);b.add_argument('--out',required=True);b.add_argument('--policy');b.add_argument('--resume',action='store_true')
    q=commands.add_parser('search');q.add_argument('--index',required=True);q.add_argument('--queries',required=True);q.add_argument('--out',required=True);q.add_argument('--policy')
    v=commands.add_parser('verify');v.add_argument('--index',required=True)
    s=commands.add_parser('serve');s.add_argument('--index',required=True);s.add_argument('--host',default='127.0.0.1');s.add_argument('--port',type=int,default=8000);s.add_argument('--policy')
    args=parser.parse_args()
    try:
        if args.command == 'build':
            build(args)
        elif args.command == 'search':
            search(args)
        elif args.command == 'verify':
            Bundle(args.index)
        else:
            serve(args)
        return 0
    except (OSError,ValueError,TypeError,KeyError,OverflowError,RecursionError,sqlite3.Error,csv.Error) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0
