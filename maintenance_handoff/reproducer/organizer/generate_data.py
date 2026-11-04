#!/usr/bin/env python3
"""Private deterministic input factory; construction ledger, never a submission solver.

No arbitrary-input parsing, version-resolution algorithm or general query oracle lives
here. Expected winners are assigned directly by the staged construction recipe.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASOF = '2026-11-02T00:00:00Z'
POLICY = {'policy_id': 'KB-BASE-1', 'max_results': 5,
          'effective_at': '2026-11-01T00:00:00+09:00'}
COUNTS = ['OVERSIZE', 'BAD_JSON', 'BAD_SCHEMA', 'FUTURE', 'DUPLICATE_RECORD_ID']


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value) + b'\n')


def tenants(count):
    initial = ['001', '1', '고객A', '고객B', '지원팀', 'Ｔ１', ' 01 ', '０１']
    return initial + [f'고객사-{i:03d}' for i in range(len(initial), count)]


def weights():
    out = {'배송': 7, '반품': 11, '결제': 13, '계정': 5, 'Ａ': 17, 'A': 3,
           'café': 19, 'cafe\u0301': 23, ' 01 ': 29, '01': 2,
           '정책/변경': 31, '<공지&안내>': 37}
    out.update({f'업무:{i:02d}': (i * 7 % 43) + 1 for i in range(48)})
    out.update({'검증:배송': 7, '검증:반품': 11, '검증:Ａ': 17, '검증:A': 3,
                '검증:빈본문': 41, '검증:café': 19, '검증:cafe\u0301': 23})
    return out


CURATED = [
    ('001', '동일', ['검증:배송', '검증:배송']),
    ('__public__', '동일', ['검증:배송']),
    ('__public__', '01', ['검증:배송', '검증:반품']),
    ('__public__', '1', ['검증:배송']),
    ('__public__', 'Ａ', ['검증:배송']),
    ('__public__', 'A', ['검증:배송']),
    ('__public__', 'café', ['검증:café']),
    ('__public__', 'cafe\u0301', ['검증:cafe\u0301']),
    ('001', '빈본문', ['검증:빈본문']),
    ('001', '철회문서', ['검증:배송']),
    ('1', '비공개', ['검증:반품']),
    ('__public__', '가', ['검증:Ａ', '검증:A']),
    ('__public__', '나', ['검증:A']),
    ('__public__', '다', ['검증:Ａ']),
]


def definition(i, tenant_ids, tags):
    if i < len(CURATED):
        return CURATED[i]
    tenant = '__public__' if i % 9 == 0 else tenant_ids[i % len(tenant_ids)]
    endings = ['안내', 'é', 'e\u0301', 'Ａ', 'A', '００１', '001', '🙂', '가', '가']
    doc = f'문서-{i:06d}-{endings[i % len(endings)]}'
    picked = [tags[(i * 7) % len(tags)], tags[(i * 17 + 3) % len(tags)]]
    if i % 5 == 0:
        picked.append(tags[(i + 11) % len(tags)])
    if i % 19 == 0:
        picked.append(picked[0])
    if i % 101 == 0:
        picked = []
    return tenant, doc, picked


def row(i, event, spec):
    tenant, doc, tags = spec
    body = (f'상담 운영 문서 {i:06d}의 처리 기준입니다. 고객 문의를 확인한 뒤 '
            '접수 번호와 적용 시각을 검토하세요. <안내> & "확인" 문자를 그대로 보존합니다.\n'
            '두 번째 줄: 배송 지연·환불·계정 요청은 문서에 기재된 범위에서 처리합니다. '
            'Unicode 예시 café / cafe\u0301 / Ａ / A / 🙂.\n'
            '담당자는 원문과 이력을 함께 확인하고 최신 공지의 적용 범위를 확인합니다.')
    if i == 8 or i % 97 == 0 and i >= len(CURATED):
        body = ''
    return {'record_id': f'r-{i:06d}-{event}', 'tenant_id': tenant, 'doc_id': doc,
            'revision': 2, 'updated_at': '2026-11-01T00:00:00Z',
            'published_at': '2026-10-25T09:00:00+09:00', 'state': 'PUBLISHED',
            'title': f'운영안내 {doc} <{event}> & 확인', 'body': body, 'tags': list(tags)}


class DocumentWriter:
    def __init__(self, directory, target, shards):
        self.directory, self.target, self.shards = directory, target, shards
        self.index = 0
        self.handles = []
        self.nonblank = [0] * shards
        self.blank = [0] * shards
        for s in range(shards):
            self.handles.append((directory / f'documents-{s:03d}.jsonl').open('wb'))

    def add(self, value):
        payload = canonical(value) if isinstance(value, dict) else value
        shard = min(self.index * self.shards // self.target, self.shards - 1)
        stream = self.handles[shard]
        if self.nonblank[shard] == 0:
            stream.write(b'\xef\xbb\xbf')
        stream.write(payload + (b'\r\n' if self.index % 7 == 0 else b'\n'))
        self.nonblank[shard] += 1
        self.index += 1
        if self.index % 211 == 0:
            stream.write(('\u2003\t ' if self.index % 2 else '').encode() + b'\r\n')
            self.blank[shard] += 1

    def close(self):
        for stream in self.handles:
            stream.close()
        assert self.index == self.target


def curated_queries(name):
    definitions = [
        ('001', ['검증:배송'], None),
        ('미등록-고객사', ['검증:배송'], None),
        ('001', [], None),
        ('001', ['존재하지 않는 태그'], None),
        ('001', ['검증:배송', '검증:반품'], 2),
        ('1', ['검증:반품'], None),
        ('001', ['검증:배송', '검증:배송'], 2),
        ('001', ['검증:빈본문'], None),
        ('001', ['검증:café'], None),
        ('001', ['검증:cafe\u0301'], None),
        ('001', ['검증:A', '검증:Ａ'], None),
        ('001', ['검증:배송'], 1),
    ]
    out = []
    for n, (tenant, terms, limit) in enumerate(definitions, 1):
        item = {'qid': f'{name}-q{n:04d}', 'tenant_id': tenant, 'terms': terms}
        if limit is not None:
            item['limit'] = limit
        out.append(item)
    return out


def first12_expected(queries, winners):
    # Hand-authored expected source order and scores for the isolated curated cases.
    layouts = [([(2, 7), (3, 7), (5, 7), (0, 7), (1, 7)], 'OK'),
               ([], 'FORBIDDEN'), ([], 'NO_MATCH'), ([], 'NO_MATCH'),
               ([(2, 18), (3, 7)], 'OK'), ([(2, 11), (10, 11)], 'OK'),
               ([(2, 7), (3, 7)], 'OK'), ([(8, 41)], 'OK'),
               ([(6, 19)], 'OK'), ([(7, 23)], 'OK'),
               ([(11, 20), (13, 17), (12, 3)], 'OK'), ([(2, 7)], 'OK')]
    results = []
    for query, (items, status) in zip(queries, layouts):
        sources = []
        for index, score in items:
            record = winners[index]
            sources.append({key: record[key] for key in ['tenant_id', 'doc_id', 'revision', 'title']}
                           | {'score': score, 'snippet': record['body'][:80]})
        results.append({'qid': query['qid'], 'status': status,
                        'policy_id': POLICY['policy_id'], 'sources': sources})
    return results


def generate(name, keys, count, query_count, tenant_count, shards):
    directory = ROOT / 'task' / 'data' / name
    directory.mkdir(parents=True, exist_ok=True)
    tenant_ids, tag_weights = tenants(tenant_count), weights()
    regular_tags = [tag for tag in tag_weights if not tag.startswith('검증:')]
    text = io.StringIO(newline='')
    writer = csv.writer(text, lineterminator='\r\n')
    writer.writerow(['tenant_id', 'label'])
    for i, tenant in enumerate(tenant_ids):
        writer.writerow([tenant, '' if i % 4 == 0 else f'고객지원 {i:03d}'])
    (directory / 'tenants.csv').write_bytes(text.getvalue().encode('cp949'))
    text = io.StringIO(newline='')
    writer = csv.writer(text, lineterminator='\n')
    writer.writerow(['tag', 'weight'])
    writer.writerows(tag_weights.items())
    (directory / 'tag_weights.csv').write_bytes(text.getvalue().encode('utf-8'))
    dump(directory / 'META.json', {'schema_version': 1, 'as_of_utc': ASOF,
                                   'expected_nonblank_document_rows': count})
    dump(directory / 'policy.json', POLICY)
    stream = DocumentWriter(directory, count, shards)
    winners = []
    rejection = {key: 0 for key in COUNTS}
    retained = 0
    for i in range(keys):
        spec = definition(i, tenant_ids, regular_tags)
        old = row(i, 'old', spec)
        old.update(revision=0, updated_at='2026-10-31T20:00:00Z')
        chosen = row(i, 'selected', spec)
        chosen['state'] = 'WITHDRAWN' if (i == 9 or i >= len(CURATED) and i % 11 == 0) else 'PUBLISHED'
        lower = row(i, 'lower', spec)
        lower.update(revision=1, updated_at='2026-11-01T23:59:59Z')
        for record in [old, chosen, lower]:
            stream.add(record)
            retained += 1
        winners.append(chosen)
    extra = count - keys * 3
    assert extra % 20 == 0
    for n in range(extra):
        block, case = divmod(n, 20)
        # Four independent final outcomes: physical tie, actual-instant winner,
        # final withdrawal, and a record_id recovered after future rejection.
        role = 1 if case == 1 else 2 if case == 2 else 3 if case in (3, 14) else 0
        i = len(CURATED) + (block * 4 + role) % (keys - len(CURATED))
        record = row(i, f'extra-{block:06d}-{case:02d}',
                     definition(i, tenant_ids, regular_tags))
        category = None
        if case == 0:  # Exact instant tie, later physical row must lose.
            record['updated_at'] = '2026-11-01T09:00:00+09:00'
        elif case == 1:  # Lexical date ordering gives the wrong answer.
            record['updated_at'] = '2026-10-31T23:30:00-02:00'
            winners[i] = record
        elif case == 2:
            record.update(revision=3, state='WITHDRAWN')
            winners[i] = record
        elif case == 3:
            record.update(record_id=f'recover-{block:06d}', revision=4,
                          published_at='2026-11-02T00:00:01Z')
            category = 'FUTURE'
        elif case == 4:
            record['updated_at'] = '2026-11-02T09:00:01+09:00'
            category = 'FUTURE'
        elif case == 5:
            record['record_id'] = f'r-{i:06d}-old'
            category = 'DUPLICATE_RECORD_ID'
        elif case == 6:
            record['revision'] = True
            category = 'BAD_SCHEMA'
        elif case == 7:
            record['tenant_id'] = '미등록-고객사'
            record['updated_at'] = '2028-01-01T00:00:00Z'
            category = 'BAD_SCHEMA'
        elif case == 8:
            record['tags'] = ['알 수 없는 태그']
            category = 'BAD_SCHEMA'
        elif case == 9:
            record = b'{"record_id":"first","record_id":"second"}'
            category = 'BAD_JSON'
        elif case == 10:
            record = b'{"revision":NaN}' if block % 2 else b'{"revision":Infinity}'
            category = 'BAD_JSON'
        elif case == 11:
            record = b'{"broken": [1,}'
            category = 'BAD_JSON'
        elif case == 12:
            record = b'{"body":"\xff"}'
            category = 'BAD_JSON'
        elif case == 13:
            if block < 20:
                record = b'\xff' + b'x' * 65536
                category = 'OVERSIZE'
            else:
                record['published_at'] = '2026-11-01T12:00:00'
                category = 'BAD_SCHEMA'
        elif case == 14:
            record.update(record_id=f'recover-{block:06d}', revision=4)
            winners[i] = record
        elif case == 15:
            record.update(revision=1, updated_at='2026-11-02T00:00:00Z')
        elif case == 16:
            record['record_id'] = f'r-{i:06d}-selected'
            record['revision'] = True  # Schema must precede record_id dedup.
            category = 'BAD_SCHEMA'
        elif case == 17:
            record['tags'] = [regular_tags[block % len(regular_tags)]] * 2
        elif case == 18:
            record['updated_at'] = '2026-02-30T09:00:00+09:00'
            category = 'BAD_SCHEMA'
        elif case == 19:
            record['state'] = 'draft'
            category = 'BAD_SCHEMA'
        stream.add(record)
        if category:
            rejection[category] += 1
        else:
            retained += 1
    stream.close()
    rng = random.Random(7210401 if name == 'sample' else 7210402)
    queries = curated_queries(name)
    while len(queries) < query_count:
        n = len(queries)
        tenant = tenant_ids[rng.randrange(len(tenant_ids))]
        if n % 23 == 0:
            tenant = '미등록-고객사'
        elif n % 71 == 0:
            tenant = '__public__'
        terms = [regular_tags[rng.randrange(len(regular_tags))]
                 for _ in range(1 + n % 4)]
        if n % 13 == 0:
            terms.append(terms[0])
        if n % 29 == 0:
            terms = []
        elif n % 31 == 0:
            terms = ['unknown-term']
        elif n % 37 == 0:
            terms += ['unknown-term', '']
        query = {'qid': f'{name}-q{n + 1:04d}', 'tenant_id': tenant, 'terms': terms}
        if n % 3:
            query['limit'] = [1, 2, 3, 5, 9][n % 5]
        queries.append(query)
    query_path = ROOT / 'task' / 'queries' / f'{name}.jsonl'
    query_path.parent.mkdir(parents=True, exist_ok=True)
    query_path.write_bytes(b''.join(canonical(query) + b'\n' for query in queries))
    if name == 'sample':
        expected = ROOT / 'task' / 'expected' / 'sample-first12.jsonl'
        expected.parent.mkdir(parents=True, exist_ok=True)
        expected.write_bytes(b''.join(canonical(result) + b'\n'
                                      for result in first12_expected(queries, winners)))
    published = [record for record in winners if record['state'] == 'PUBLISHED']
    truth = {'construction_version': '721.1', 'dataset': name,
             'actual_nonblank_document_rows': count,
             'stats': {'schema_version': 1, 'status': 'COMPLETE', 'as_of_utc': ASOF,
                       'policy_id': POLICY['policy_id'], 'max_results': POLICY['max_results'],
                       'doc_count': len(published), 'selected_keys': keys,
                       'withdrawn_count': keys - len(published), 'tenant_count': tenant_count},
             'rejections': {'schema_version': 1, 'counts': rejection,
                            'retained_records': retained},
             'selected_records': winners,
             'note': 'Construction ledger assigned by declared event stage, not parsed from the generated files.'}
    assert retained + sum(rejection.values()) == count
    dump(ROOT / 'organizer' / 'truth' / f'{name}.json', truth)
    inventory = []
    for path in sorted(directory.rglob('*'), key=lambda p: p.relative_to(directory).as_posix().encode()):
        if path.is_file():
            content = path.read_bytes()
            entry = {'path': path.relative_to(directory).as_posix(), 'size': len(content),
                     'sha256': hashlib.sha256(content).hexdigest()}
            if path.name.startswith('documents-'):
                s = int(path.stem.split('-')[-1])
                entry.update(nonblank_lines=stream.nonblank[s], blank_lines=stream.blank[s])
            inventory.append(entry)
    return {'actual_nonblank_document_rows': count, 'query_count': query_count,
            'files': inventory,
            'queries': {'path': f'queries/{name}.jsonl', 'size': query_path.stat().st_size,
                        'sha256': hashlib.sha256(query_path.read_bytes()).hexdigest()}}


def main():
    inventory = {'schema_version': 1, 'sample': generate('sample', 1800, 6000, 80, 16, 3),
                 'full': generate('full', 60000, 240000, 1500, 48, 12)}
    dump(ROOT / 'task' / 'DATA_INVENTORY.json', inventory)
    dump(ROOT / 'organizer' / 'GENERATION_RECORD.json', {
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'construction_version': '721.1', 'public_inventory_sha256': hashlib.sha256(
            (ROOT / 'task' / 'DATA_INVENTORY.json').read_bytes()).hexdigest(),
        'deterministic_seeds': {'sample': 7210401, 'full': 7210402}})
    print('Generated sample=6000/full=240000 nonblank lines; queries=80/1500.')


if __name__ == '__main__':
    main()
