#!/usr/bin/env python3
"""Read-only coverage of explicitly declared local checks; never an official score."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

JSON_LIMIT = 1024 * 1024
REPORT_LIMIT = 8 * 1024 * 1024
EVALUATOR_LIMIT = 16 * 1024 * 1024
TOTAL_EVALUATOR_LIMIT = 64 * 1024 * 1024
CHECK_LIMIT = 1000
STATUSES = ('PASS', 'FAIL', 'ERROR', 'SKIP', 'UNVERIFIED')
SCOPE = 'LOCAL_DECLARED_CHECK_COVERAGE'
NOTICE = ('Unweighted local declared-check coverage only; not an official score, '
          'hidden-test prediction, or product approval. Records and digests do not '
          'prove tests ran or that an oracle is correct; independent review is required. '
          'Lost PASS records show evidence changes, not proof of product bugs. '
          'Official visible metrics belong separately in the evidence notes.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_value(value, name):
    require(isinstance(value, str) and bool(value.strip()), name + ' must be nonblank text')
    return value


def fields(value, required, optional=()):
    require(isinstance(value, dict), 'expected an object')
    require(set(required) <= set(value) <= set(required) | set(optional),
            'missing or unsupported object fields: ' + ', '.join(required))


def version(value):
    require(type(value.get('version')) is int and value['version'] == 1, 'version must be integer 1')


def string_list(value, name):
    require(isinstance(value, list) and len(value) <= CHECK_LIMIT, name + ' must be a bounded list')
    for item in value:
        text_value(item, name + ' entry')


def normalized(path):
    return os.path.normcase(os.path.abspath(path))


def read_file(path, limit, digest_only=False):
    """Reject special files before opening; recheck the opened descriptor against races."""
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode), 'not a regular local file: ' + str(path))
    require(info.st_size <= limit, 'file exceeds byte limit: ' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(str(path), flags)
    with os.fdopen(descriptor, 'rb') as handle:
        require(stat.S_ISREG(os.fstat(handle.fileno()).st_mode), 'opened file is not regular')
        digest, chunks, size = hashlib.sha256(), [], 0
        while True:
            chunk = handle.read(min(65536, limit - size + 1))
            if not chunk:
                break
            size += len(chunk)
            require(size <= limit, 'file exceeds byte limit: ' + str(path))
            digest.update(chunk)
            if not digest_only:
                chunks.append(chunk)
    return digest.hexdigest(), size, b''.join(chunks)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('nonfinite JSON number: ' + value)


def read_json(path, limit=JSON_LIMIT):
    digest, _, data = read_file(path, limit)
    value = json.loads(data.decode('utf-8-sig'), object_pairs_hook=unique_object,
                       parse_constant=invalid_constant)
    # Overflowed JSON exponents (e.g. 1e999) also produce nonfinite floats.
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, float):
            require(math.isfinite(item), 'nonfinite JSON number')
        elif isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return value, digest


def rubric_data(value):
    fields(value, ('version', 'unknowns', 'criteria'))
    version(value)
    string_list(value['unknowns'], 'unknowns')
    criteria = value['criteria']
    require(isinstance(criteria, list) and len(criteria) <= CHECK_LIMIT, 'criteria exceed list limit')
    ids = []
    for criterion in criteria:
        fields(criterion, ('id', 'description', 'source', 'oracle'))
        for key in ('id', 'description', 'source', 'oracle'):
            text_value(criterion[key], 'criterion ' + key)
        require(criterion['id'] not in ids, 'duplicate criterion ID')
        ids.append(criterion['id'])
    return ids


def check_data(checks):
    require(isinstance(checks, list) and len(checks) <= CHECK_LIMIT, 'checks exceed list limit')
    result = {}
    for check in checks:
        fields(check, ('id', 'status'), ('evidence',))
        identifier = text_value(check['id'], 'check ID')
        require(identifier not in result, 'duplicate check ID: ' + identifier)
        require(isinstance(check['status'], str) and check['status'] in STATUSES, 'invalid check status')
        evidence = check.get('evidence', '')
        require(isinstance(evidence, str), 'evidence must be text')
        if check['status'] in ('PASS', 'FAIL', 'ERROR'):
            text_value(evidence, 'executed-check evidence')
        result[identifier] = dict(id=identifier, status=check['status'], evidence=evidence)
    return result


def summary(checks):
    counts = {status: 0 for status in STATUSES}
    for check in checks:
        counts[check['status']] += 1
    total = len(checks)
    return dict(earned=counts['PASS'], total=total,
                percent=round(100.0 * counts['PASS'] / total, 6) if total else None), counts


def previous_data(value):
    fields(value, ('version', 'scope', 'rubric_sha256', 'evaluators', 'label',
                   'evaluated_version', 'evaluation_scope', 'score', 'counts', 'checks', 'unknowns',
                   'comparison', 'notice'))
    version(value)
    require(value['scope'] == SCOPE, 'comparison scope is not local declared-check coverage')
    text_value(value['label'], 'comparison label')
    text_value(value['evaluated_version'], 'comparison evaluated_version')
    text_value(value['evaluation_scope'], 'comparison evaluation_scope')
    text_value(value['notice'], 'comparison notice')
    string_list(value['unknowns'], 'comparison unknowns')
    require(isinstance(value['comparison'], (dict, type(None))), 'invalid prior comparison')
    require(isinstance(value['rubric_sha256'], str) and
            re.fullmatch('[0-9a-f]{64}', value['rubric_sha256']), 'invalid rubric digest')
    evaluators = value['evaluators']
    require(isinstance(evaluators, dict) and len(evaluators) <= CHECK_LIMIT, 'invalid evaluator digests')
    for path, digest in evaluators.items():
        require(path == normalized(path), 'evaluator path must be absolute and normalized')
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'invalid evaluator digest')
    checks = check_data(value['checks'])
    require(not checks or evaluators, 'nonempty comparison requires evaluator digests')
    expected_score, expected_counts = summary(list(checks.values()))
    fields(value['score'], ('earned', 'total', 'percent'))
    fields(value['counts'], STATUSES)
    require(all(type(value['score'][key]) is int for key in ('earned', 'total')), 'invalid score counts')
    percent = value['score']['percent']
    require(percent is None or type(percent) in (int, float), 'invalid percentage type')
    require(all(type(count) is int for count in value['counts'].values()), 'invalid status counts')
    require(value['score'] == expected_score and value['counts'] == expected_counts,
            'comparison score/counts disagree with its checks')
    return checks


def generate(args):
    rubric, rubric_hash = read_json(args.rubric)
    ids = rubric_data(rubric)
    results, _ = read_json(args.results)
    fields(results, ('version', 'label', 'evaluated_version', 'evaluation_scope', 'checks'))
    version(results)
    text_value(results['label'], 'label')
    text_value(results['evaluated_version'], 'evaluated_version')
    text_value(results['evaluation_scope'], 'evaluation_scope')
    supplied = check_data(results['checks'])
    require(set(supplied) <= set(ids), 'unknown result criterion ID')
    checks = [supplied.get(identifier, dict(id=identifier, status='UNVERIFIED', evidence=''))
              for identifier in ids]
    require(not ids or args.evaluator, 'nonempty rubric requires --evaluator')
    require(len(args.evaluator) <= CHECK_LIMIT, 'too many evaluator files')
    evaluators, total_bytes = {}, 0
    for filename in args.evaluator:
        # Check the supplied final component before resolving parent aliases.
        # Lexical abspath first would incorrectly collapse symlink/.. paths.
        require(stat.S_ISREG(Path(filename).lstat().st_mode), 'not a regular local file: ' + filename)
        path = normalized(Path(filename).resolve(strict=True))
        require(path not in evaluators, 'duplicate evaluator path')
        digest, size, _ = read_file(path, min(EVALUATOR_LIMIT, TOTAL_EVALUATOR_LIMIT - total_bytes), True)
        total_bytes += size
        evaluators[path] = digest
    score, counts = summary(checks)
    report = dict(version=1, scope=SCOPE, rubric_sha256=rubric_hash, evaluators=evaluators,
                  label=results['label'], evaluated_version=results['evaluated_version'],
                  evaluation_scope=results['evaluation_scope'],
                  score=score, counts=counts, checks=checks, unknowns=rubric['unknowns'],
                  comparison=None, notice=NOTICE)
    comparable = True
    if args.compare:
        previous, _ = read_json(args.compare, REPORT_LIMIT)
        old_checks = previous_data(previous)
        comparable = (previous['rubric_sha256'] == rubric_hash and
                      previous['evaluators'] == evaluators and set(old_checks) == set(ids) and
                      previous['evaluation_scope'] == results['evaluation_scope'] and
                      results['evaluation_scope'].strip().upper() != 'UNKNOWN')
        report['comparison'] = dict(
            comparable=comparable, baseline_label=previous['label'],
            baseline_evaluated_version=previous['evaluated_version'],
            reason=('Same rubric, evaluators, and known evaluation scope' if comparable else
                    'Rubric, evaluator, criterion set, or evaluation scope changed/unknown'),
            delta=(dict(earned=score['earned'] - previous['score']['earned'],
                        percentage_points=round(score['percent'] - previous['score']['percent'], 6))
                   if comparable and ids else None),
            lost_pass=([identifier for identifier in ids if old_checks[identifier]['status'] == 'PASS'
                        and supplied.get(identifier, {}).get('status') != 'PASS'] if comparable else None))
    return report, 0 if ids and counts['PASS'] == len(ids) and comparable else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rubric', required=True)
    parser.add_argument('--results', required=True)
    parser.add_argument('--evaluator', action='append', default=[])
    parser.add_argument('--compare')
    args = parser.parse_args()
    try:
        report, status = generate(args)
        rendered = json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2)
        # Include print's newline and platform newline translation in the cap.
        require(len((rendered + '\n').replace('\n', os.linesep).encode('ascii')) <= REPORT_LIMIT,
                'generated report exceeds byte limit')
        print(rendered)
        return status
    except (ValueError, OSError, RecursionError) as error:
        print('Invalid local score input: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
