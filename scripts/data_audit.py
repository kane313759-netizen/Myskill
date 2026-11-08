#!/usr/bin/env python3
"""Record bounded observations for ten data-audit questions, without certifying domain truth."""
import argparse
from collections import Counter
import csv
import gzip
import statistics
import zlib
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import runpy


def common():
    return runpy.run_path(str(Path(__file__).with_name('v27_common.py')), run_name='v27_audit_common')


NAMES = ['time_timezone_order_delay', 'units_scale', 'code_definition_versions',
         'identifiers_joins_splits_duplicates', 'target_leakage', 'sample_bias',
         'confounding', 'distribution_shift', 'obsolete_docs_data_instructions',
         'missingness_outlier_causes']


def _id_hint(name):
    return bool(re.search(r'(^|[_\W])(id|no)($|[_\W])|seq|step|index', name, re.I))


def _profile(rows, io, declared_columns=()):
    columns = sorted(set(declared_columns) | {str(key) for row in rows for key in row})
    nulls, types, numeric, candidates, temporal, scales = {}, {}, {}, [], [], []
    for column in columns:
        values = [row.get(column) for row in rows]
        present = [value for value in values if not io['is_blank'](value)]
        nulls[column] = len(values) - len(present)
        types[column] = dict(Counter(type(value).__name__ for value in present))
        distinct = len({io['canonical_value'](value) for value in present})
        if present and len(present) == len(rows) and distinct == len(rows):
            candidates.append({'column': column, 'id_name_hint': io['id_like'](column),
                               'sample_unique': True})
        numbers = [io['as_num'](value) for value in present]
        numbers = [value for value in numbers if value is not None]
        if numbers:
            numeric[column] = {'count': len(numbers), 'min': min(numbers), 'max': max(numbers)}
        time_name = re.search(r'(?:^|[_\s-])(?:date|time|timestamp|datetime)(?:$|[_\s-])|[a-z](?:Time|Date)|timestamp|날짜|일시|시간', column, re.I)
        looks_iso = any(isinstance(v, str) and re.match(r'^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}|$)', v.strip()) for v in present)
        if time_name or looks_iso:
            parsed = []
            for value in present:
                try:
                    parsed.append(datetime.fromisoformat(str(value).replace('Z', '+00:00')))
                except (ValueError, TypeError):
                    pass
            aware = sum(value.tzinfo is not None for value in parsed)
            comparable = bool(parsed) and aware in (0, len(parsed))
            temporal.append({'column': column, 'name_hint': bool(time_name), 'iso_value_hint': looks_iso,
                             'parsed_iso_count': len(parsed), 'timezone_explicit_count': aware,
                             'sample_nondecreasing': all(a <= b for a, b in zip(parsed, parsed[1:])) if comparable else None})
    # Compare neighbouring windows, not just the global range: a 10x change
    # can be hidden by perfectly ordinary within-column magnitudes.
    for column in numeric:
        if _id_hint(column) and all(value.is_integer() for value in (io['as_num'](row.get(column)) for row in rows) if value is not None):
            continue
        series = [(idx, io['as_num'](row.get(column))) for idx, row in enumerate(rows)]
        series = [(idx, value) for idx, value in series if value is not None and value > 0]
        window = max(3, min(100, len(series) // 4))
        if len(series) >= 2 * window:
            best = None
            for split in range(window, len(series) - window + 1, max(1, window // 2)):
                left = statistics.median(value for _, value in series[split-window:split])
                right = statistics.median(value for _, value in series[split:split+window])
                if left and right and any(.85*k <= right/left <= 1.15*k or .85/k <= right/left <= 1.15/k for k in (10,100,1000)):
                    ratio = right / left
                    candidate = {'column': column, 'before_row': series[split-1][0] + 1,
                                 'after_row': series[split][0] + 1, 'ratio': round(ratio, 6) if math.isfinite(ratio) else None,
                                 'window': window, 'reason': 'adjacent window median ratio resembles a power of ten; verify units and population'}
                    distance = abs(math.log(right) - math.log(left))
                    if best is None or distance > best_distance:
                        best = candidate
                        best_distance = distance
            if best:
                scales.append(best)
    # Only compare semantically paired timestamps; arbitrary row order is not a
    # process-time reversal. Report counts, never raw identifiers or values.
    reversals = []
    time_columns = [item['column'] for item in temporal]
    for earlier in time_columns:
        for later in time_columns:
            if earlier == later:
                continue
            if not (re.search(r'(start|begin|in|입고|시작)', earlier, re.I) and
                    re.search(r'(end|finish|out|완료|종료)', later, re.I)):
                continue
            comparable = reversed_count = 0
            for row in rows:
                try:
                    a = datetime.fromisoformat(str(row.get(earlier, '')).replace('Z', '+00:00'))
                    b = datetime.fromisoformat(str(row.get(later, '')).replace('Z', '+00:00'))
                    if (a.utcoffset() is None) != (b.utcoffset() is None):
                        continue
                    comparable += 1
                    reversed_count += b < a
                except (ValueError, TypeError, OverflowError):
                    continue
            reversals.append({'earlier_column': earlier, 'later_column': later,
                              'comparable_rows': comparable, 'reversed_rows': reversed_count})
    sequence_reversals = []
    signatures = [io['canonical_value'](row) for row in rows]
    return {'columns': columns, 'types': types, 'null_counts': nulls, 'numeric_ranges': numeric,
            'key_candidates': candidates, 'time_candidates': temporal, 'scale_suspects': scales,
            'timestamp_pair_reversals': reversals, 'sequence_reversals': sequence_reversals,
            'duplicate_rows': len(signatures) - len(set(signatures))}


# Streaming CSV scan. Keep bounded entity and numeric reservoirs in memory;
# never persist or retain the full set of rows.
def _stream_csv(path, plan, spec, io):
    import heapq, random, time
    limit = plan.get('max_scan_bytes', plan.get('max_file_bytes', 2 * 1024 * 1024 * 1024))
    seconds = plan.get('max_scan_seconds', 120)
    reservoir = plan.get('reservoir_size', 2000)
    requested_sample = plan.get('max_rows', 2000)
    sample_limit = min(requested_sample, 10000) if type(requested_sample) is int else requested_sample
    if type(limit) is not int or not 0 < limit <= 2 * 1024 * 1024 * 1024:
        raise ValueError('max_scan_bytes must be 1..2GiB')
    if type(seconds) not in (int, float) or not 0 < seconds <= 120:
        raise ValueError('max_scan_seconds must be 0..120')
    if type(reservoir) is not int or not 1 <= reservoir <= 2000 or type(requested_sample) is not int or not 1 <= requested_sample <= 1000000:
        raise ValueError('reservoir_size and max_rows exceed bounded profile budget')
    threshold = plan.get('time_reversal_threshold', 0.05)
    if type(threshold) not in (int, float) or not 0 <= threshold <= 1:
        raise ValueError('time_reversal_threshold must be between zero and one')
    compressed = path.name.lower().endswith('.gz')
    opener = gzip.open if compressed else open
    encoding = spec.get('encoding')
    if not encoding:
        with opener(path, 'rb') as probe:
            data = probe.read(65536)
        for candidate in ('utf-8-sig', 'cp949'):
            try:
                import codecs
                codecs.getincrementaldecoder(candidate)('strict').decode(data, final=False)
                encoding = candidate; break
            except UnicodeError:
                pass
        if not encoding: raise UnicodeError('Cannot detect CSV encoding')
    rng = random.Random(2941)
    sample, periods, cats, numeric_cols, counts = [], {}, {}, set(), {}
    adjacent, last_time, chronological = {}, None, True
    pair_compared = pair_reversed = 0
    cache_cap = 2000000  # maximum floats in all reservoirs combined
    used = [0]; analysis_limited = [False]; scan_bytes = rows_scanned = sample_bytes = 0; complete = True; reason = None
    start_clock = time.monotonic()
    hash_value = hashlib.sha256()
    # Hash the entire original byte stream only if it fits the per-file budget.
    initial_stat = path.stat()
    raw_bytes = initial_stat.st_size
    full_hash = None
    if raw_bytes <= limit:
        with path.open('rb') as hf:
            while True:
                block = hf.read(1024 * 1024)
                if not block: break
                hash_value.update(block)
                if time.monotonic()-start_clock > seconds:
                    complete=False; reason='time budget exceeded during hashing'; break
        if complete: full_hash = hash_value.hexdigest()
    def keep(group, key, value):
        bucket = group.get(key)
        if bucket is None:
            if len(group) >= 4096:
                analysis_limited[0] = True
                return
            bucket = group[key] = [0, []]
        bucket[0] += 1
        if len(bucket[1]) < reservoir and used[0] < cache_cap:
            bucket[1].append(value); used[0] += 1
        else:
            if len(bucket[1]) < reservoir and used[0] >= cache_cap:
                analysis_limited[0] = True
            n = rng.randrange(bucket[0])
            if n < len(bucket[1]): bucket[1][n] = value
    def parsed(v):
        try: return datetime.fromisoformat(str(v).replace('Z','+00:00'))
        except (ValueError, TypeError, OverflowError): return None
    hints = {'id':['lot_id','wafer_id','lot','wafer','carrier'], 'sequence':['step_seq','step','seq','oper','operation','route_step'],
             'start':['track_in','start','begin','in_time','start_time'], 'end':['track_out','end','finish','out_time','end_time'],
             'source':['eqp_id','tool','equipment','chamber']}
    explicit = plan.get('time_order')
    if explicit is not None and not isinstance(explicit,dict): raise ValueError('time_order must be a role mapping')
    roles = {}; groups = {}; group_heap = []; dropped_events = 0
    try:
        with opener(path, 'rt', encoding=encoding, newline='') as f:
            def lines():
                nonlocal scan_bytes, complete, reason
                while True:
                    line = f.readline(4 * 1024 * 1024 + 1)
                    if not line: break
                    if len(line) > 4 * 1024 * 1024:
                        complete=False;reason='line size budget exceeded';return
                    if time.monotonic()-start_clock > seconds:
                        complete=False;reason='time budget exceeded';return
                    size=len(line.encode(encoding.replace('-sig',''),errors='strict'))
                    if scan_bytes + size > limit:
                        complete=False;reason='byte budget exceeded';return
                    scan_bytes += size
                    yield line
            reader=csv.reader(lines(),strict=True)
            try:
                header=next(reader, None)
            except csv.Error:
                if complete: raise
                header=None
            if header is None:
                if not complete: return {'columns':[], 'sample':[], 'rows':0, 'complete':False, 'reason':reason,'bytes':scan_bytes,'sha256':full_hash,'profile':_profile([],io,[])}
                raise ValueError('CSV header missing')
            header=io['_headers'](header); lookup={x.casefold():x for x in header}
            if len(header)>512:
                return {'columns':header[:512], 'sample':[], 'rows':0, 'complete':False, 'reason':'column budget exceeded',
                        'bytes':scan_bytes,'sha256':full_hash,'profile':_profile([],io,header[:512])}
            for role, opts in hints.items():
                requested=(explicit or {}).get(role)
                if requested is not None:
                    if requested not in header: raise ValueError('time_order column not found: '+str(requested))
                    roles[role]=requested
                else:
                    roles[role]=next((lookup[x] for x in opts if x in lookup),None)
            if explicit and any(not roles[k] for k in ('id','sequence','start','end','source')):
                raise ValueError('time_order needs id, sequence, start, end, source')
            period_col=plan.get('time_column') or roles.get('start') or next((x for x in header if re.search(r'(date|time|날짜|일시)',x,re.I)),None)
            if period_col and period_col not in header: raise ValueError('time_column not found')
            per=plan.get('period','week')
            if per not in ('week','month'): raise ValueError('period must be week or month')
            metric_columns=header
            integer_ids={col:True for col in header if _id_hint(col)}
            has_roles=all(roles.get(k) for k in ('id','sequence','start','end'))
            def safe_rows():
                try:
                    yield from reader
                except csv.Error:
                    if complete: raise
            for values in safe_rows():
                if not values: continue
                if len(values)!=len(header): raise ValueError('CSV line %s: wrong field count'%reader.line_num)
                rows_scanned += 1
                row=dict(zip(header,values))
                if roles.get('start') and roles.get('end'):
                    left_time,right_time=parsed(row.get(roles['start'])),parsed(row.get(roles['end']))
                    if left_time and right_time and (left_time.utcoffset() is None)==(right_time.utcoffset() is None):
                        pair_compared += 1
                        pair_reversed += right_time < left_time
                if len(sample)<sample_limit and sample_bytes<8*1024*1024:
                    row_size=sum(len(value) for value in values)+64*len(values)
                    if sample_bytes+row_size<=8*1024*1024:
                        sample.append(row);sample_bytes+=row_size
                nums={}
                for col in metric_columns:
                    val=row[col]
                    v=io['as_num'](val)
                    if col in integer_ids and v is not None and not v.is_integer(): integer_ids[col]=False
                    if v is not None and v>0: nums[col]=v;numeric_cols.add(col)
                d=parsed(row.get(period_col)) if period_col else None
                if d:
                    if last_time is not None:
                        try:
                            if d < last_time: chronological = False
                        except TypeError:
                            chronological = False
                    last_time=d
                    week=d.isocalendar(); period='%04d-W%02d'%(week[0],week[1]) if per=='week' else '%04d-%02d'%(d.year,d.month)
                    for col,v in nums.items(): keep(periods,(col,period),v)
                for col,v in nums.items():
                    state=adjacent.setdefault(col,[[],[]])
                    state[0].append(v)
                    if len(state[0])==100:
                        if len(state[1])<2048: state[1].append((rows_scanned,statistics.median(state[0])))
                        state[0].clear()
                for col,val in row.items():
                    if col in nums or not val or len(val)>256 or col==period_col or col in (roles.get('id'), roles.get('start'), roles.get('end')): continue
                    if io['as_num'](val) is not None or parsed(val): continue
                    bucket=cats.setdefault(col,set())
                    if len(bucket)<=50: bucket.add(val)
                    if len(bucket)<=50:
                        for key,v in nums.items(): keep(counts,(col,val,key),v)
                if has_roles:
                    raw_seq=row.get(roles['sequence'])
                    number=io['as_num'](raw_seq)
                    if number is not None:
                        seq=(0,number)
                    elif raw_seq and len(raw_seq)<=128:
                        seq=(1,tuple((1,int(piece)) if piece.isdigit() else (0,piece.casefold()) for piece in re.split(r'(\d+)',raw_seq)))
                    else:
                        seq=None
                    ident=row.get(roles['id']); start=row[roles['start']]; end=row[roles['end']]; source=row.get(roles.get('source')) or 'UNKNOWN'
                    if seq is not None and ident and len(ident)<=256 and len(source)<=256 and len(start)<=128 and len(end)<=128:
                        key=hashlib.blake2b(ident.encode('utf8'),digest_size=16).digest()
                        rank=int.from_bytes(key,'big')
                        if key not in groups:
                            if len(groups)<reservoir:
                                groups[key]=[];heapq.heappush(group_heap,(-rank,key))
                            elif rank < -group_heap[0][0]:
                                _,old=heapq.heapreplace(group_heap,(-rank,key)); del groups[old]; groups[key]=[]
                        if key in groups:
                            if len(groups[key])<128: groups[key].append((seq,start,end,source))
                            else: dropped_events += 1;analysis_limited[0] = True
                    elif seq is not None and ident:
                        dropped_events += 1;analysis_limited[0] = True
        profile=_profile(sample,io,header)
        if roles.get('start') and roles.get('end'):
            profile['timestamp_pair_reversals']=[{'earlier_column':roles['start'],'later_column':roles['end'],
                'comparable_rows':pair_compared,'reversed_rows':pair_reversed}]
        # Replace r2's file-order/range heuristic with period/source ratios.
        suspects=[]
        def ratio_ok(a,b):
            if not a or not b: return False
            r=b/a
            return any(.85*k <= r <= 1.15*k or .85/k <= r <= 1.15/k for k in (10,100,1000))
        if chronological:
            for col,(_,blocks) in adjacent.items():
                for (row_a,a),(row_b,b) in zip(blocks,blocks[1:]):
                    if ratio_ok(a,b): suspects.append({'signal':'SCALE_STEP','kind':'ADJACENT','column':col,'before_row':row_a,'after_row':row_b,'ratio':b/a,
                        'limitation':'File ordering is not a confirmed time sequence.' if not period_col else 'Confirm chronology and unit definitions.'})
        by_col={}
        for (col,period),(_,vals) in periods.items():
            if vals: by_col.setdefault(col,[]).append((period,statistics.median(vals)))
        for col,seqs in by_col.items():
            seqs.sort()
            for (p,a),(q,b) in zip(seqs,seqs[1:]):
                if ratio_ok(a,b): suspects.append({'signal':'SCALE_STEP','kind':'PERIOD','column':col,'before_period':p,'after_period':q,'ratio':b/a})
        for category,values in cats.items():
            if not 2<=len(values)<=50: continue
            for col in sorted(numeric_cols):
                medians={v:statistics.median(counts[(category,v,col)][1]) for v in values if (category,v,col) in counts and counts[(category,v,col)][1]}
                if len(medians)<2: continue
                reference=statistics.median(medians.values())
                for val,m in sorted(medians.items()):
                    if ratio_ok(reference,m): suspects.append({'signal':'SCALE_STEP','kind':'SOURCE','column':col,'source_column':category,'source_value':val,'ratio':m/reference})
        profile['scale_suspects']=[item for item in suspects if not integer_ids.get(item['column'],False)]
        profile['sequence_reversals']=[]
        if has_roles:
            buckets={}; prev=None; ambiguous=0
            def source_bucket(source):
                if source not in buckets:
                    if len(buckets) >= 2000:
                        analysis_limited[0] = True
                        return None
                    buckets[source]={'source':source,'comparable_pairs':0,'reversed_pairs':0,
                        'total_reversal_hours':0.0,'offset_samples':[],'outgoing_samples':[],
                        'incoming_count':0,'outgoing_count':0}
                return buckets[source]
            ordered=((ident,seq,start,end,source) for ident in sorted(groups)
                     for seq,start,end,source in sorted(groups[ident],key=lambda x:x[0]))
            for ident,seq,start,end,source in ordered:
                if prev and prev[0]==ident:
                    if prev[1]==seq: ambiguous+=1
                    else:
                        a,b=parsed(prev[3]),parsed(start)
                        if a and b and (a.utcoffset() is None)==(b.utcoffset() is None):
                            hours=(b-a).total_seconds()/3600
                            rec=source_bucket(source)
                            if rec is None:
                                prev=(ident,seq,start,end,source)
                                continue
                            rec['comparable_pairs']+=1
                            if hours<0: rec['reversed_pairs']+=1;rec['total_reversal_hours']-=hours
                            if prev[4] != source:
                                rec['incoming_count'] += 1
                                if len(rec['offset_samples'])<reservoir: rec['offset_samples'].append(hours)
                                else:
                                    pos=rng.randrange(rec['incoming_count'])
                                    if pos<reservoir: rec['offset_samples'][pos]=hours
                                prior=source_bucket(prev[4])
                                if prior is not None:
                                    prior['outgoing_count'] += 1
                                    if len(prior['outgoing_samples'])<reservoir: prior['outgoing_samples'].append(hours)
                                    else:
                                        pos=rng.randrange(prior['outgoing_count'])
                                        if pos<reservoir: prior['outgoing_samples'][pos]=hours
                prev=(ident,seq,start,end,source)
            normals=[v for rec in buckets.values() for v in rec['offset_samples']]
            typical=statistics.median(normals) if normals else 0
            output=[]
            for source,rec in sorted(buckets.items()):
                n=rec['comparable_pairs'];bad=rec['reversed_pairs']; samples=rec.pop('offset_samples'); outgoing=rec.pop('outgoing_samples')
                rec['reversal_rate']=bad/n if n else 0
                rec['mean_reversal_hours']=rec.pop('total_reversal_hours')/bad if bad else 0
                if bad and rec['reversal_rate']>=threshold and samples:
                    # First minimize remaining reversed pairs, then align to the
                    # typical non-reversed inter-step delay; proposals only.
                    options=[i/2 for i in range(-28,29)]
                    rec['suggested_offset_hours']=min(options,key=lambda h:(sum(v+h<0 for v in samples)+sum(v-h<0 for v in outgoing),abs(statistics.median(samples)+h-typical),abs(h)))
                output.append(rec)
            profile['sequence_reversals']=[{'roles':dict(roles,mode='explicit' if explicit else 'auto'),'sources':output,'same_sequence_pairs_skipped':ambiguous,
                'comparable_pairs':sum(x['comparable_pairs'] for x in output), 'reversed_pairs':sum(x['reversed_pairs'] for x in output),
                'sampled_entities':len(groups),'entity_reservoir_size':reservoir,'dropped_events':dropped_events,
                'limitation':'Pair counts use a bounded entity sample. Ordered-step hypotheses are not automatically corrected; confirm parallel/rework/timezones.'}]
        if analysis_limited[0]:
            complete=False; reason=reason or 'analysis group reservoir budget exceeded'
        profile.update(rows_examined=len(sample),rows_scanned=rows_scanned,profile_rows=len(sample),
                       profile_complete_rows=complete and len(sample)==rows_scanned,complete_rows=complete)
        final_stat = path.stat()
        if (initial_stat.st_size, initial_stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
            raise ValueError('provided file changed during audit')
        return {'columns':header,'sample':sample,'rows':rows_scanned,'complete':complete,'reason':reason,'bytes':scan_bytes,'sha256':full_hash,'profile':profile}
    finally:
        pass


def audit(root, plan):
    helper = common()
    io = runpy.run_path(str(Path(__file__).with_name('data_io.py')), run_name='v27_data_io')
    if not isinstance(plan, dict) or not isinstance(plan.get('files'), list) or not plan['files']:
        raise ValueError('explicit provided data/document files are required')
    maximum = plan.get('max_rows', 2000)
    byte_limit = plan.get('max_file_bytes', 8 * 1024 * 1024)
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 0 < maximum <= 1000000:
        raise ValueError('max_rows must be 1..1000000; profile is capped at 10000')
    if isinstance(byte_limit, bool) or not isinstance(byte_limit, int) or not 0 < byte_limit <= 32 * 1024 * 1024:
        raise ValueError('invalid max_file_bytes')
    if len(plan['files']) > 64:
        raise ValueError('audit file budget exceeded')
    requested_na = plan.get('na', [])
    reasons = plan.get('na_reasons', {})
    if not isinstance(requested_na, list) or not all(type(v) is int and 1 <= v <= 10 for v in requested_na) or not isinstance(reasons, dict):
        raise ValueError('na must contain item IDs 1..10; na_reasons must be an object')
    artifacts, errors, profiles, seen = [], [], [], set()
    total_bytes = total_rows = 0
    for supplied in plan['files']:
        spec = {'path': supplied} if isinstance(supplied, str) else supplied
        name = spec.get('path') if isinstance(spec, dict) else None
        try:
            path = helper['safe_path'](root, name)
            if str(path.resolve()) in seen:
                raise ValueError('duplicate provided file')
            seen.add(str(path.resolve()))
            if path.suffix.lower() == '.csv' or path.name.lower().endswith('.csv.gz'):
                scanned = _stream_csv(path, plan, spec, io)
                prof = scanned['profile']
                prof.update(path=name, sheet=None)
                profiles.append(prof)
                artifacts.append({'path':name, 'bytes':path.stat().st_size, 'sha256':scanned['sha256'],
                                  'kind':'table','tables':[prof], 'rows_examined':scanned['rows'],
                                  'rows_scanned':scanned['rows'], 'profile_rows':len(scanned['sample']),
                                  'complete_rows':scanned['complete'], 'partial_reason':scanned['reason'],
                                  'scanned_bytes':scanned['bytes']})
                total_rows += scanned['rows']
                continue
            if path.is_file() and path.stat().st_size > byte_limit:
                artifacts.append({'path':name, 'bytes':path.stat().st_size, 'sha256':None,
                    'kind':'table' if path.suffix.lower() in ('.json','.xlsx','.xlsm') else 'document',
                    'tables':[], 'rows_examined':0, 'rows_scanned':0, 'complete_rows':False,
                    'partial_reason':'non-CSV bounded reader byte budget exceeded'})
                continue
            content = helper['read_bytes'](path, byte_limit)
            total_bytes += len(content)
            artifact = {'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            if path.suffix.lower() in ('.json', '.xlsx', '.xlsm'):
                remaining = min(maximum, 10000)
                artifact.update(kind='table', tables=[], rows_examined=0, complete_rows=True)
                declared_columns = []
                tables = io['tables'](path, remaining + 1, byte_limit,
                                      encoding=spec.get('encoding'), records_key=spec.get('records_key'),
                                      sheet=spec.get('sheet'), all_sheets=False)
                for sheet, rows in tables:
                    partial = len(rows) > remaining
                    sample = rows[:remaining]
                    if not all(isinstance(row, dict) for row in sample):
                        raise ValueError('table records must be objects')
                    prof = _profile(sample, io, declared_columns)
                    prof.update(path=name, sheet=sheet, rows_examined=len(sample), complete_rows=not partial)
                    profiles.append(prof)
                    artifact['tables'].append(prof)
                    artifact['rows_examined'] += len(sample)
                    artifact['complete_rows'] = artifact['complete_rows'] and not partial
                    total_rows += len(sample)
                    remaining -= len(sample)
                if helper['read_bytes'](path, byte_limit) != content:
                    raise ValueError('provided file changed during audit')
            elif path.suffix.lower() in ('.txt', '.md', '.rst', '.pdf', '.docx', '.html'):
                artifact.update(kind='document', extraction='not_performed', rows_examined=0,
                                complete_rows=None, instruction_and_revision_review='UNVERIFIED')
            else:
                raise ValueError('unsupported input type; provide explicit CSV/JSON/workbook or document')
            artifacts.append(artifact)
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, ImportError, RuntimeError, KeyError, csv.Error, zlib.error) as error:
            errors.append({'path': name, 'error': str(error)})
    tables_present = any(item['kind'] == 'table' for item in artifacts)
    complete = not errors and all(item.get('complete_rows') is not False for item in artifacts)
    time_candidates = [entry for prof in profiles for entry in prof['time_candidates']]
    numeric_present = any(prof['numeric_ranges'] for prof in profiles)
    empty_workbook = any(item['path'].lower().endswith(('.xlsx', '.xlsm')) and item['rows_examined'] == 0 for item in artifacts)
    observations = {
        1: [{'path': prof['path'], 'candidates': prof['time_candidates'], 'timestamp_pair_reversals': prof['timestamp_pair_reversals'], 'sequence_reversals': prof['sequence_reversals']} for prof in profiles],
        2: [{'path': prof['path'], 'numeric_ranges': prof['numeric_ranges'], 'scale_suspects': prof['scale_suspects']} for prof in profiles],
        4: [{'path': prof['path'], 'sample_key_candidates': prof['key_candidates'], 'duplicate_rows': prof['duplicate_rows']} for prof in profiles],
        10: [{'path': prof['path'], 'sample_null_counts': prof['null_counts']} for prof in profiles],
    }
    actions = {
        1: 'Confirm event versus arrival time, timezone, permitted sorting and delay with the task owner.',
        2: 'Confirm declared units and scale revisions; do not automatically rescale suspected values.',
        3: 'Compare code dictionaries and definition versions with authoritative task materials.',
        4: 'Confirm true key/cardinality, join and split contracts; sample uniqueness is not a key guarantee.',
        5: 'Identify target, prediction time and feature availability before testing leakage.',
        6: 'Compare sampled and target populations with a sampling frame.',
        7: 'Review alternative causes and intervention assumptions; correlations do not establish causation.',
        8: 'Compare explicitly authorized train/test/time groups using declared splits and metrics.',
        9: 'Review document revisions and instruction-like data as untrusted content against official instructions.',
        10: 'Investigate missingness/outlier mechanisms with domain evidence before imputing or removing data.'}
    items = []
    for index, name in enumerate(NAMES, 1):
        status = 'RECORDED' if index in observations and tables_present else 'UNVERIFIED'
        method = 'bounded descriptive table profiling' if status == 'RECORDED' else 'requires task evidence or a separate substantive review'
        findings = observations.get(index, [])
        if index in requested_na:
            reason = reasons.get(str(index), reasons.get(index, plan.get('reason')))
            # Absence claims need complete readable scope; semantic topics cannot become N/A by assertion alone.
            absent = complete and (index == 1 and not time_candidates and not empty_workbook or index == 2 and not numeric_present and not empty_workbook or
                                   index in (4, 5, 8) and not tables_present)
            if not isinstance(reason, str) or not reason.strip() or not absent:
                errors.append({'item': index, 'error': 'N_A request lacks a reason or substantive absent prerequisites'})
                status = 'UNVERIFIED'
            else:
                status, method = 'N_A', 'prerequisite absence recorded for the explicit provided scope'
                findings = [{'reason': reason, 'complete_provided_scope': True}]
        items.append({'id': index, 'name': name, 'status': status, 'method': method,
                      'findings': findings, 'actions': [actions[index]],
                      'limitations': ['Observations do not validate business definitions, causal truth, hidden evaluation or unprovided files.']})
    return {'status': 'FAIL' if errors else 'RECORDED' if complete else 'UNVERIFIED', 'items': items, 'files': artifacts, 'errors': errors,
            'scope': {'provided_files_only': True, 'max_rows_per_profile': min(maximum,10000), 'requested_profile_rows':maximum, 'rows_examined': total_rows,
                      'max_file_bytes': byte_limit, 'all_provided_rows_examined': complete,
                      'raw_values_in_report': True, 'source_categories_in_report': True},
            'notice': 'Ten audit questions are recorded, not automatically validated. RECORDED means descriptive observations only; unresolved semantic and document-instruction risks remain UNVERIFIED.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    helper = common()
    try:
        result = audit(args.root, helper['read_json'](args.plan))
        if args.output:
            helper['atomic_json'](args.output, result)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0 if result['status'] == 'RECORDED' else 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, ImportError) as error:
        print(json.dumps({'status': 'FAIL', 'errors': [str(error)]}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
