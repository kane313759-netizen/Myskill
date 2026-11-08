#!/usr/bin/env python3
"""Record bounded observations for ten data-audit questions, without certifying domain truth."""
import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import io as text_io
import json
from pathlib import Path
import re
import runpy


def common():
    return runpy.run_path(str(Path(__file__).with_name('v27_common.py')), run_name='v27_audit_common')


NAMES = ['time_timezone_order_delay', 'units_scale', 'code_definition_versions',
         'identifiers_joins_splits_duplicates', 'target_leakage', 'sample_bias',
         'confounding', 'distribution_shift', 'obsolete_docs_data_instructions',
         'missingness_outlier_causes']


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
            magnitude = [abs(number) for number in numbers if number]
            if magnitude and max(magnitude) / min(magnitude) >= 1000:
                scales.append({'column': column, 'reason': 'sample nonzero magnitudes span >=1000x; units or legitimate spread require review'})
        time_name = re.search(r'(?:^|[_\s-])(?:date|time|timestamp|datetime)(?:$|[_\s-])|[a-z](?:Time|Date)|timestamp|날짜|일시|시간', column, re.I)
        looks_iso = any(isinstance(v, str) and re.match(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}', v) for v in present)
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
    signatures = [io['canonical_value'](row) for row in rows]
    return {'columns': columns, 'types': types, 'null_counts': nulls, 'numeric_ranges': numeric,
            'key_candidates': candidates, 'time_candidates': temporal, 'scale_suspects': scales,
            'duplicate_rows': len(signatures) - len(set(signatures))}


def audit(root, plan):
    helper = common()
    io = runpy.run_path(str(Path(__file__).with_name('data_io.py')), run_name='v27_data_io')
    if not isinstance(plan, dict) or not isinstance(plan.get('files'), list) or not plan['files']:
        raise ValueError('explicit provided data/document files are required')
    maximum = plan.get('max_rows', 1000)
    byte_limit = plan.get('max_file_bytes', 8 * 1024 * 1024)
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 0 < maximum <= 10000:
        raise ValueError('max_rows must be 1..10000')
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
            content = helper['read_bytes'](path, byte_limit)
            total_bytes += len(content)
            if total_bytes > 64 * 1024 * 1024:
                raise ValueError('total audit byte budget exceeded')
            artifact = {'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            if path.suffix.lower() in ('.csv', '.json', '.xlsx', '.xlsm'):
                remaining = maximum - total_rows
                if remaining <= 0:
                    raise ValueError('total audit row budget exhausted before this file')
                artifact.update(kind='table', tables=[], rows_examined=0, complete_rows=True)
                declared_columns = []
                if path.suffix.lower() == '.csv':
                    encoding = io['choose_encoding'](path, spec.get('encoding'))
                    declared_columns = next(csv.reader(text_io.StringIO(content.decode(encoding))), [])
                for sheet, rows in io['tables'](path, remaining + 1, byte_limit,
                                              encoding=spec.get('encoding'), records_key=spec.get('records_key'),
                                              sheet=spec.get('sheet'), all_sheets=False):
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
        except (OSError, UnicodeError, ValueError, TypeError, ImportError, RuntimeError, KeyError) as error:
            errors.append({'path': name, 'error': str(error)})
    tables_present = any(item['kind'] == 'table' for item in artifacts)
    complete = not errors and all(item.get('complete_rows') is not False for item in artifacts)
    time_candidates = [entry for prof in profiles for entry in prof['time_candidates']]
    numeric_present = any(prof['numeric_ranges'] for prof in profiles)
    empty_workbook = any(item['path'].lower().endswith(('.xlsx', '.xlsm')) and item['rows_examined'] == 0 for item in artifacts)
    observations = {
        1: [{'path': prof['path'], 'candidates': prof['time_candidates']} for prof in profiles],
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
    return {'status': 'FAIL' if errors else 'RECORDED', 'items': items, 'files': artifacts, 'errors': errors,
            'scope': {'provided_files_only': True, 'max_rows_total': maximum, 'rows_examined': total_rows,
                      'max_file_bytes': byte_limit, 'all_provided_rows_examined': complete,
                      'raw_values_in_report': False},
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
