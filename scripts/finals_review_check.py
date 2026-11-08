#!/usr/bin/env python3
"""Read-only aggregate finals review evidence; not official score or submission approval."""
import argparse
import hashlib
from pathlib import Path
import runpy

CORE_ROLES = ('CONSTRAINT_RED', 'DATA_EVAL_RED', 'ALGORITHM_RED',
              'CODE_RED', 'EDGE_RED', 'SUBMISSION_RED')
SECURITY_KINDS = {'AUTH', 'EXTERNAL_ROUTE', 'SECRETS', 'PRIVILEGED_TOOLS', 'SENSITIVE_DATA'}


def policy():
    return runpy.run_path(str(Path(__file__).with_name('review_execution.py')),
                          run_name='finals_review_execution_policy')


def check_hashes(value, root, helper, label):
    errors = []
    if not isinstance(value, dict) or not value:
        return [label + ' must contain current task-relative file hashes']
    for path, digest in value.items():
        try:
            if not isinstance(digest, str) or not helper['HASH'].fullmatch(digest):
                raise ValueError('invalid SHA256')
            content = helper['read_local'](root, path, helper['SCOPE_LIMIT'])
            if hashlib.sha256(content).hexdigest() != digest:
                raise ValueError('file changed: ' + path)
        except (OSError, ValueError, TypeError) as error:
            errors.append('%s: %s' % (label, error))
    return errors


def findings_errors(findings, meaningful):
    if not isinstance(findings, list):
        return ['findings must be a list, even when empty']
    errors, seen = [], set()
    for item in findings:
        if not isinstance(item, dict):
            errors.append('finding must be an object')
            continue
        identifier, severity, status = item.get('id'), item.get('severity'), item.get('status')
        if not meaningful(identifier) or identifier in seen:
            errors.append('finding IDs must be meaningful and unique within the role')
        if isinstance(identifier, str):
            seen.add(identifier)
        if not isinstance(severity, str) or severity not in ('P0', 'P1', 'P2', 'P3'):
            errors.append('finding has invalid severity')
        if not isinstance(status, str) or status not in ('OPEN', 'FIXED', 'DISPROVED', 'ACCEPTED_RISK'):
            errors.append('finding has invalid disposition')
        if not meaningful(item.get('evidence')):
            errors.append('finding needs original evidence')
        if severity in ('P0', 'P1') and status not in ('FIXED', 'DISPROVED'):
            errors.append('P0/P1 finding remains unresolved')
        if status in ('FIXED', 'DISPROVED', 'ACCEPTED_RISK') and not meaningful(item.get('verification')):
            errors.append('finding disposition needs verification or risk rationale')
    return errors


def check_reviews(plan, kit, expected_checkpoint, helper=None):
    helper = helper if helper is not None else policy()
    meaningful = helper['meaningful']
    root = Path(kit).absolute().parent
    if not isinstance(plan, dict):
        return ['finals review plan must be an object']
    errors = []
    if type(plan.get('version')) is not int or plan['version'] != 1:
        errors.append('finals review plan must be version 1')
    if not meaningful(expected_checkpoint) or plan.get('checkpoint') != expected_checkpoint:
        errors.append('finals review plan checkpoint does not match the requested checkpoint')
    required = plan.get('required_scope')
    errors.extend(check_hashes(required, root, helper, 'required_scope'))
    required = required if isinstance(required, dict) else {}
    security = plan.get('security')
    security = security if isinstance(security, dict) else {}
    decision = security.get('decision')
    if decision not in ('TRIGGERED', 'NOT_TRIGGERED'):
        errors.append('security trigger decision is unknown or invalid; quality review is incomplete')
    if not meaningful(security.get('reason')):
        errors.append('security decision needs its actual inspection rationale')
    inspected = security.get('inspected_sources')
    errors.extend(check_hashes(inspected, root, helper, 'security inspected_sources'))
    inspected = inspected if isinstance(inspected, dict) else {}
    triggers = security.get('triggers')
    if not isinstance(triggers, list):
        errors.append('security triggers must be an explicit list')
        triggers = []
    if decision == 'TRIGGERED' and not triggers:
        errors.append('TRIGGERED security decision needs source-backed triggers')
    if decision == 'NOT_TRIGGERED' and triggers:
        errors.append('NOT_TRIGGERED contradicts recorded security triggers')
    for trigger in triggers:
        try:
            if not isinstance(trigger, dict):
                raise ValueError('trigger must be an object')
            kind, source, evidence = trigger.get('kind'), trigger.get('source'), trigger.get('evidence')
            if not isinstance(kind, str) or kind not in SECURITY_KINDS:
                raise ValueError('unknown security trigger kind')
            if not isinstance(source, str) or source not in inspected:
                raise ValueError('trigger source was not inspected and hash-bound')
            if not meaningful(evidence):
                raise ValueError('trigger needs an exact source excerpt')
            content = helper['read_local'](root, source, helper['SCOPE_LIMIT']).decode('utf-8-sig')
            if evidence not in content:
                raise ValueError('trigger excerpt is absent from its source')
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            errors.append('security trigger: ' + str(error))
    reviews = plan.get('reviews')
    if not isinstance(reviews, dict):
        return errors + ['reviews must contain the six core roles and the SECURITY_RED decision']
    allowed_roles = set(CORE_ROLES) | {'SECURITY_RED'}
    if any(role not in allowed_roles for role in reviews):
        errors.append('reviews contains an unknown role')
    workers, report_paths, report_hashes = set(), set(), set()
    roles = CORE_ROLES + (('SECURITY_RED',) if decision == 'TRIGGERED' else ())
    for role in roles:
        entry = reviews.get(role)
        if not isinstance(entry, dict):
            errors.append(role + ': review entry missing')
            continue
        if entry.get('status') != 'ACCEPTED':
            errors.append(role + ': review must be ACCEPTED; NOT_RUN/SELF_CHECK/COMPLETE is insufficient')
        errors.extend(role + ': ' + error for error in findings_errors(entry.get('findings'), meaningful))
        try:
            content = helper['verified_file'](root, entry.get('execution_receipt'), notes_only=True)
            receipt = helper['load_json'](content.decode('utf-8-sig'))
            errors.extend(role + ': ' + error for error in
                          helper['execution_errors'](receipt, kit, role, expected_checkpoint))
            if not isinstance(receipt, dict):
                continue
            worker = receipt.get('worker_id')
            if meaningful(worker):
                if worker in workers:
                    errors.append(role + ': another review role reused this worker_id')
                workers.add(worker)
            report = receipt.get('report')
            if isinstance(report, dict) and meaningful(report.get('path')) and isinstance(report.get('sha256'), str):
                helper['verified_file'](root, report, notes_only=True)
                report_path = (root / report['path']).resolve()
                if report_path in report_paths:
                    errors.append(role + ': another role reused this review report path')
                if report['sha256'] in report_hashes:
                    errors.append(role + ': another role reused identical review report content')
                report_paths.add(report_path)
                report_hashes.add(report['sha256'])
            scope = receipt.get('reviewed_files')
            if not isinstance(scope, dict) or any(scope.get(path) != digest for path, digest in required.items()):
                errors.append(role + ': execution receipt does not cover the required current candidate scope')
            if role == 'SECURITY_RED' and (not isinstance(scope, dict) or
                    any(scope.get(path) != digest for path, digest in inspected.items())):
                errors.append(role + ': execution receipt does not cover current security inspection sources')
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError) as error:
            errors.append(role + ': execution receipt: ' + str(error))
    if decision == 'NOT_TRIGGERED':
        entry = reviews.get('SECURITY_RED')
        if not isinstance(entry, dict) or entry.get('status') != 'NOT_APPLICABLE' or not meaningful(entry.get('reason')):
            errors.append('SECURITY_RED must explicitly be NOT_APPLICABLE with a reason when not triggered')
        elif entry.get('execution_receipt') or entry.get('findings'):
            errors.append('SECURITY_RED NOT_APPLICABLE cannot hide a receipt or findings')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--plan', default='.hackathon-kit/run/FINALS_REVIEWS.json',
                        help='Plan path relative to the task root, under kit/run')
    parser.add_argument('--checkpoint', required=True)
    args = parser.parse_args()
    try:
        helper = policy()
        content = helper['read_local'](args.kit.absolute().parent, args.plan, notes_only=True)
        plan = helper['load_json'](content.decode('utf-8-sig'))
        errors = check_reviews(plan, args.kit, args.checkpoint, helper)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, SyntaxError, RecursionError) as error:
        errors = [str(error)]
    if errors:
        print('FINALS REVIEW EVIDENCE FAIL')
        for error in errors:
            print('-', error)
        return 2
    print('FINALS REVIEW EVIDENCE OK: retained quality evidence only; not official score, submission or authenticated identity')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
