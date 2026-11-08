#!/usr/bin/env python3
"""Check only the explicit submission contract; no hidden score or upload claim."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import runpy


def common():
    return runpy.run_path(str(Path(__file__).with_name('v27_common.py')), run_name='v27_submission_common')


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('non-finite JSON number')


def _number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError('expected a finite number')
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('expected a finite number')
    if not number.is_finite():
        raise ValueError('expected a finite number')
    return number


def _identity(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def _records(content, rule):
    encoding = rule.get('encoding', 'utf-8-sig')
    text = content.decode(encoding)
    kind = rule.get('format')
    if kind == 'text':
        return None, text
    if kind == 'json':
        value = json.loads(text, object_pairs_hook=_unique, parse_constant=_constant)
        selected = value
        key = rule.get('records_key')
        if key is not None:
            if not isinstance(key, str) or not isinstance(value, dict) or key not in value:
                raise ValueError('records_key must name an existing top-level array')
            selected = value[key]
        return selected if isinstance(selected, list) else [selected], value
    if kind == 'csv':
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        headers = next(reader, None)
        if headers is None:
            raise ValueError('CSV header missing')
        if not all(isinstance(h, str) and h.strip() for h in headers) or len(set(headers)) != len(headers):
            raise ValueError('CSV headers must be nonempty and unique')
        rows = []
        for values in reader:
            if not values:
                continue
            if len(values) != len(headers):
                raise ValueError('CSV row width differs from header')
            rows.append(dict(zip(headers, values)))
        return rows, {'columns': headers}
    raise ValueError('format must be json, csv or text')


def check_submission(root, rules):
    helper = common()
    root = Path(root).absolute()
    errors, checks, artifacts, rows_by_path = [], [], [], {}
    if not isinstance(rules, dict) or not isinstance(rules.get('files'), list) or not rules['files']:
        return {'status': 'FAIL', 'errors': ['rules need an explicit nonempty files list'], 'checks': [], 'artifacts': []}
    if len(rules['files']) > 2048:
        return {'status': 'FAIL', 'errors': ['local checker file-count budget exceeded'], 'checks': [], 'artifacts': []}
    limit = rules.get('max_file_bytes', 16 * 1024 * 1024)
    if type(limit) is not int or limit <= 0 or limit > 128 * 1024 * 1024:
        return {'status': 'FAIL', 'errors': ['invalid max_file_bytes'], 'checks': [], 'artifacts': []}
    seen, total = set(), 0
    for entry in rules['files']:
        label = entry.get('path') if isinstance(entry, dict) else '<invalid>'
        try:
            if not isinstance(entry, dict) or not isinstance(label, str):
                raise ValueError('file rule must have a relative path')
            path = helper['safe_path'](root, label)
            identity = str(path.resolve())
            if identity in seen:
                raise ValueError('duplicate declared file')
            seen.add(identity)
            content = helper['read_bytes'](path, limit)
            total += len(content)
            if total > 256 * 1024 * 1024:
                raise ValueError('local checker total-byte budget exceeded')
            rule = dict(entry)
            rule.setdefault('format', path.suffix.lower().lstrip('.') if path.suffix.lower() in ('.json', '.csv') else 'text')
            rows, original = _records(content, rule)
            if rows is not None:
                rows_by_path[label] = rows
                count = len(rows)
                for key in ('row_count', 'min_rows', 'max_rows'):
                    if key in rule:
                        bound = rule[key]
                        if type(bound) is not int or bound < 0:
                            raise ValueError(key + ' must be a nonnegative integer')
                        if ((key == 'row_count' and count != bound) or
                                (key == 'min_rows' and count < bound) or
                                (key == 'max_rows' and count > bound)):
                            raise ValueError(key + ' violated')
                required = rule.get('required_fields', rule.get('columns', []))
                if not isinstance(required, list) or not all(isinstance(v, str) for v in required):
                    raise ValueError('required_fields/columns must be a string list')
                if 'columns' in rule and rule['format'] == 'csv':
                    if original['columns'] != rule['columns']:
                        raise ValueError('CSV columns/order do not match declared contract')
                for index, row in enumerate(rows):
                    if required and (not isinstance(row, dict) or any(key not in row for key in required)):
                        raise ValueError('required field absent at row %d' % index)
                allowed = rule.get('allowed_values', {})
                ranges = rule.get('ranges', {})
                if not isinstance(allowed, dict) or not isinstance(ranges, dict):
                    raise ValueError('allowed_values/ranges must be objects')
                for index, row in enumerate(rows):
                    if (allowed or ranges) and not isinstance(row, dict):
                        raise ValueError('field constraints require object records')
                    for column, values in allowed.items():
                        if not isinstance(values, list) or column not in row or _identity(row[column]) not in [_identity(v) for v in values]:
                            raise ValueError('allowed value violated at row %d column %s' % (index, column))
                    for column, bounds in ranges.items():
                        if not isinstance(bounds, dict) or column not in row or not set(bounds).issubset({'min', 'max'}):
                            raise ValueError('invalid range definition or missing column')
                        value = _number(row[column])
                        if ('min' in bounds and value < _number(bounds['min'])) or ('max' in bounds and value > _number(bounds['max'])):
                            raise ValueError('range violated at row %d column %s' % (index, column))
                keys = rule.get('unique_keys', [])
                if not isinstance(keys, list) or not all(isinstance(v, str) for v in keys):
                    raise ValueError('unique_keys must be a string list')
                if keys:
                    identities = set()
                    for row in rows:
                        if not isinstance(row, dict) or any(key not in row for key in keys):
                            raise ValueError('unique key field missing')
                        value = tuple(_identity(row[key]) for key in keys)
                        if value in identities:
                            raise ValueError('duplicate key')
                        identities.add(value)
            elif any(key in rule for key in ('row_count', 'min_rows', 'max_rows', 'required_fields', 'columns', 'ranges', 'allowed_values', 'unique_keys')):
                raise ValueError('record constraints are not supported for text')
            import hashlib
            artifacts.append({'path': label, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'rows': None if rows is None else len(rows)})
            checks.append({'path': label, 'status': 'PASS'})
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError, csv.Error) as error:
            errors.append('%s: %s' % (label, error))
            checks.append({'path': label, 'status': 'FAIL'})
    maximum = rules.get('max_total_bytes')
    if maximum is not None and (type(maximum) is not int or maximum < 0 or total > maximum):
        errors.append('max_total_bytes invalid or exceeded')
    aggregates = rules.get('aggregate_constraints', [])
    if not isinstance(aggregates, list):
        errors.append('aggregate_constraints must be a list')
        aggregates = []
    for rule in aggregates:
        try:
            if not isinstance(rule, dict) or rule.get('op') not in ('sum_le', 'sum_ge'):
                raise ValueError('aggregate op must be sum_le or sum_ge')
            rows = rows_by_path.get(rule.get('path'))
            if rows is None:
                raise ValueError('aggregate path must name a parsed declared file')
            column = rule.get('column')
            if not isinstance(column, str):
                raise ValueError('aggregate column missing')
            if not all(isinstance(row, dict) and column in row for row in rows):
                raise ValueError('aggregate column absent from an object record')
            total_value = sum((_number(row[column]) for row in rows), Decimal(0))
            bound = _number(rule.get('value'))
            if (rule['op'] == 'sum_le' and total_value > bound) or (rule['op'] == 'sum_ge' and total_value < bound):
                raise ValueError('aggregate constraint violated')
        except (ValueError, TypeError, KeyError) as error:
            errors.append('aggregate: ' + str(error))
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors, 'checks': checks,
            'artifacts': artifacts, 'total_bytes': total, 'notice': 'Declared local contract only; no official score, full collection inventory or submission receipt.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--rules', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    helper = common()
    try:
        result = check_submission(args.root, helper['read_json'](args.rules))
        if args.output:
            helper['atomic_json'](args.output, result)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0 if result['status'] == 'PASS' else 2
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        print(json.dumps({'status': 'FAIL', 'errors': [str(error)]}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
