#!/usr/bin/env python3
"""Read-only CP1 evidence gate; validates records, not business truth or agent identity."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import runpy
import stat
from pathlib import Path

ARTIFACTS = ('GRADER.md', 'BASELINE.md', 'IMMUTABLES.md', 'SPEC_DRAFT.md', 'CONSTRAINTS.md')
REQUIRED_STATE = {
    'grader_contract': {'RECORDED', 'UNKNOWN_AFTER_INSPECTION'},
    'baseline': {'RECORDED', 'UNAVAILABLE_WITH_REASON'},
    'immutable_inventory': {'RECORDED'}, 'cp1_constraint_red': {'DONE'},
    'constraint_gate': {'CLOSED'},
}
SECTIONS = {
    'GRADER.md': ('What is scored', 'Required output / submission path', 'Submission collection', 'Evidence / inspection'),
    'BASELINE.md': ('Before edits',), 'IMMUTABLES.md': ('Inventory',),
    'SPEC_DRAFT.md': ('Grading target', 'Required output / command', 'Input contract', 'Output contract', 'Confirmed constraints with evidence', 'Assumptions / open questions', 'Verification plan'),
    'CONSTRAINTS.md': ('Constraint register',), 'CP1_RED.md': ('Attacks and original evidence',),
    'TASK_EVIDENCE.md': ('Provenance', 'Original task / answer excerpts'),
}
MAX_RECORD_BYTES = 2 * 1024 * 1024
STATE_LINE = re.compile(r'^\s*(?:[-*]\s+)?(?:\*\*(?P<bold>[a-z][a-z0-9_]*)\*\*|__(?P<under>[a-z][a-z0-9_]*)__|(?P<plain>[a-z][a-z0-9_]*))\s*:\s*(?P<value>.*?)\s*$')
STATE_VALUE = re.compile(r'([A-Z_]+)(?:\s+\([^\n]*\))?(?:\s*#[^\n]*)?')


def read_record(path):
    """Read one bounded regular record, rejecting final symlinks and special files."""
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('record is not a regular non-symlink file: %s' % path)
    if info.st_size > MAX_RECORD_BYTES:
        raise ValueError('record exceeds 2 MiB limit')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(str(path), flags)
    with os.fdopen(descriptor, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('opened record is not a regular file')
        data = handle.read(MAX_RECORD_BYTES + 1)
    if len(data) > MAX_RECORD_BYTES:
        raise ValueError('record exceeds 2 MiB limit')
    return data


def read_text(path):
    return read_record(path).decode('utf-8-sig')


def parse_state(text):
    values, errors = {}, []
    for number, line in enumerate(text.splitlines(), 1):
        match = STATE_LINE.fullmatch(line)
        if not match:
            continue
        key = match.group('bold') or match.group('under') or match.group('plain')
        if key not in REQUIRED_STATE:
            continue
        if key in values:
            errors.append('STATE.md duplicate key %s at line %d' % (key, number))
            continue
        value = STATE_VALUE.fullmatch(match.group('value'))
        values[key] = value.group(1) if value else '<invalid syntax>'
    return values, errors


def normalized(text):
    return re.sub(r'\s+', ' ', re.sub(r'<!--[\s\S]*?-->', '', text)).strip()


def sections(text):
    result, current = {}, None
    for line in text.splitlines():
        heading = re.match(r'^##\s+(.+?)\s*$', line)
        if heading:
            current = heading.group(1).casefold()
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return {key: '\n'.join(body) for key, body in result.items()}


def document_errors(kit, name):
    try:
        text = read_text(kit / 'run' / name)
        template = kit / 'templates' / name
        try:
            template.lstat()
        except FileNotFoundError:
            original = ''
        else:
            original = read_text(template)
    except (OSError, UnicodeError, ValueError) as error:
        return ['%s: %s' % (name, error)]
    if not normalized(text) or normalized(text) == normalized(original):
        return ['%s is empty or still its template' % name]
    actual, initial = sections(text), sections(original)
    return ['%s needs evidence in section: %s' % (name, heading)
            for heading in SECTIONS.get(name, ())
            if not normalized(actual.get(heading.casefold(), ''))
            or normalized(actual.get(heading.casefold(), '')) == normalized(initial.get(heading.casefold(), ''))]


def artifact_hashes(kit):
    result = {}
    for name in ARTIFACTS:
        result[name] = hashlib.sha256(read_record(kit / 'run' / name)).hexdigest()
    return result


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def review_errors(kit):
    try:
        validator = runpy.run_path(str(Path(__file__).with_name('review_execution.py')),
                                  run_name='kit_review_execution')
        report = validator['load_json'](read_text(kit / 'run' / 'CP1_REVIEW.json'))
    except (OSError, UnicodeError, ValueError, RecursionError, SyntaxError, KeyError) as error:
        return ['CP1_REVIEW.json: %s' % error]
    if not isinstance(report, dict):
        return ['CP1_REVIEW.json must be an object']
    errors = []
    if report.get('version') != 1 or report.get('status') != 'COMPLETE':
        errors.append('CP1 review must be version 1 with status COMPLETE')
    reviewer = report.get('reviewer')
    reviewer = reviewer if isinstance(reviewer, dict) else {}
    if reviewer.get('role') != 'CONSTRAINT_RED' or not nonempty(reviewer.get('actual_model')):
        errors.append('CP1 CONSTRAINT_RED reviewer and actual model must be recorded honestly')
    if reviewer.get('context_mode') not in ('NO_HISTORY', 'CLEAN_SESSION'):
        errors.append('CP1 reviewer must record NO_HISTORY or CLEAN_SESSION')
    try:
        scope = {kit.name + '/run/' + name: digest
                 for name, digest in artifact_hashes(kit).items()}
        errors.extend(validator['execution_errors'](
            report.get('execution'), kit, 'CONSTRAINT_RED', 'CP1',
            kit.name + '/run/CP1_RED.md', scope))
    except (OSError, UnicodeError, ValueError, SyntaxError, KeyError) as error:
        errors.append('CP1 review execution validation: %s' % error)
    sources = report.get('source_paths')
    if not isinstance(sources, list) or not sources:
        errors.append('CP1 needs original source_paths or provenance-marked TASK_EVIDENCE.md')
    else:
        for value in sources:
            if not nonempty(value):
                errors.append('CP1 source_paths entries must be nonempty paths')
                continue
            path = Path(value)
            path = (kit.parent / path).resolve() if not path.is_absolute() else path.resolve()
            if not path.is_file():
                errors.append('CP1 original source does not exist: %s' % value)
            elif path == (kit / 'run' / 'TASK_EVIDENCE.md').resolve():
                errors.extend(document_errors(kit, 'TASK_EVIDENCE.md'))
            elif kit.resolve() in path.parents:
                errors.append('MAIN/kit records are not original task sources: %s' % value)
    hashes = report.get('artifacts')
    hashes = hashes if isinstance(hashes, dict) else {}
    try:
        for name, digest in artifact_hashes(kit).items():
            if hashes.get(name) != digest:
                errors.append('CP1 reviewed artifact missing or changed: %s; reopen and re-review' % name)
    except (OSError, ValueError) as error:
        errors.append('CP1 artifact hashes: %s' % error)
    attacks = report.get('attempted_attacks')
    if not isinstance(attacks, list) or not attacks or not all(nonempty(x) for x in attacks):
        errors.append('CP1 must record concrete attempted_attacks even if no defect survived')
    findings = report.get('findings')
    if not isinstance(findings, list):
        return errors + ['CP1 findings must be a list (empty is allowed)']
    seen = set()
    for item in findings:
        if not isinstance(item, dict):
            errors.append('CP1 finding must be an object')
            continue
        identifier, severity, status = item.get('id'), item.get('severity'), item.get('status')
        if not nonempty(identifier) or (isinstance(identifier, str) and identifier in seen):
            errors.append('CP1 finding IDs must be nonempty and unique')
        if isinstance(identifier, str):
            seen.add(identifier)
        if not isinstance(severity, str) or severity not in {'P0', 'P1', 'P2', 'P3'}:
            errors.append('CP1 %s has invalid severity' % identifier)
        if not isinstance(status, str) or status not in {'OPEN', 'FIXED', 'DISPROVED', 'ACCEPTED_RISK'}:
            errors.append('CP1 %s has invalid status' % identifier)
        if severity in ('P0', 'P1') and status not in ('FIXED', 'DISPROVED'):
            errors.append('CP1 blocking finding %s remains %s' % (identifier, status))
        if not nonempty(item.get('evidence')):
            errors.append('CP1 %s needs original evidence' % identifier)
        if status in ('FIXED', 'DISPROVED', 'ACCEPTED_RISK') and not nonempty(item.get('verification')):
            errors.append('CP1 %s needs verification or evidence-backed risk disposition' % identifier)
    return errors


def check_gate(kit):
    kit, errors = Path(kit), []
    if not (kit / 'EXAM_POLICY.md').is_file():
        errors.append('EXAM_POLICY.md missing')
    try:
        values, parse_errors = parse_state(read_text(kit / 'run' / 'STATE.md'))
        errors.extend(parse_errors)
        for key, allowed in REQUIRED_STATE.items():
            if values.get(key) not in allowed:
                errors.append('%s=%s; expected %s' % (key, values.get(key, '<missing>'), '/'.join(sorted(allowed))))
    except (OSError, UnicodeError, ValueError) as error:
        errors.append('STATE.md: %s' % error)
    for name in (*ARTIFACTS, 'CP1_RED.md'):
        errors.extend(document_errors(kit, name))
    return errors + review_errors(kit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--artifact-hashes', action='store_true', help='Print current hashes; does not pass or close the gate')
    mode.add_argument('--preflight', action='store_true', help='Check the five intake templates before Red review; never authorizes implementation')
    args = parser.parse_args()
    if args.preflight:
        errors = [error for name in ARTIFACTS for error in document_errors(args.kit, name)]
        if errors:
            print('PREFLIGHT FAIL: preserve the installed template headings and fill their evidence sections')
            for error in errors:
                print('-', error)
            return 2
        print('PREFLIGHT OK: document format only; independent CP1 review and full gate still required')
        return 0
    if args.artifact_hashes:
        try:
            print(json.dumps(artifact_hashes(args.kit), indent=2, sort_keys=True))
        except (OSError, ValueError) as error:
            parser.exit(2, '%s\n' % error)
        return 0
    errors = check_gate(args.kit)
    if errors:
        print('GATE FAIL')
        for error in errors:
            print('-', error)
        return 2
    print('GATE OK: CP1 evidence, reviewed contract and blocking dispositions are recorded')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
