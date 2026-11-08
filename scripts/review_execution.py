#!/usr/bin/env python3
"""Read-only review execution receipt checks; retained observations are not authenticated."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import stat

LIMIT = 2 * 1024 * 1024
SCOPE_LIMIT = 16 * 1024 * 1024
PHASES = ('LAUNCHED', 'RUNNING', 'COMPLETED')
HASH = re.compile(r'^[0-9a-f]{64}$')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def load_json(text):
    return json.loads(text, object_pairs_hook=unique_object)


def native_state(raw, worker, tool):
    """Supported native response shapes only; summaries/incidental ID mentions do not count."""
    if isinstance(raw, dict) and raw.get('error'):
        raise ValueError('native response records an error, not successful execution')
    if isinstance(raw, dict) and 'agents' in raw:
        if any(raw[key] != worker for key in ('worker_id', 'task_name', 'agent_name', 'agent_id', 'session_id') if key in raw):
            raise ValueError('native agents envelope identity conflicts with this worker')
        if any(key in raw for key in ('status', 'state', 'agent_status')):
            raise ValueError('ambiguous native agents envelope status')
        if not isinstance(raw['agents'], list):
            raise ValueError('native agents response must be a list')
        matches = [row for row in raw['agents'] if isinstance(row, dict) and
                   row.get('agent_name') == worker]
        if len(matches) != 1:
            raise ValueError('native response must identify exactly this worker')
        return native_state(matches[0], worker, tool)
    if not isinstance(raw, dict):
        raise ValueError('unsupported native response shape; execution remains unverified')
    identities = [raw[key] for key in ('worker_id', 'task_name', 'agent_name', 'agent_id', 'session_id')
                  if key in raw]
    if not identities or any(value != worker for value in identities):
        raise ValueError('native response does not identify exactly this worker')
    final_message = raw.get('message_type') == 'FINAL_ANSWER' and meaningful(raw.get('text'))
    statuses = [raw[key] for key in ('agent_status', 'status', 'state') if key in raw]
    if statuses:
        normalized = []
        for status in statuses:
            if isinstance(status, dict) and set(status) == {'completed'} and meaningful(status['completed']):
                normalized.append('completed')
            elif isinstance(status, str):
                normalized.append(status.lower())
            else:
                raise ValueError('unsupported native status; execution remains unverified')
        if len(set(normalized)) != 1:
            raise ValueError('native status fields conflict')
        if final_message and normalized[0] != 'completed':
            raise ValueError('native final message and status conflict')
        return normalized[0]
    if final_message:
        return 'completed'
    if tool == 'collaboration.spawn_agent' and set(raw) == {'task_name'}:
        return 'launched'
    raise ValueError('native status unavailable; execution remains unverified')


def meaningful(value):
    return (isinstance(value, str) and bool(value.strip()) and
            value.strip().upper() not in {'UNKNOWN', 'NOT_RUN', 'TODO', 'NONE', 'N/A'})


def read_local(root, relative, limit=LIMIT, notes_only=False):
    if not meaningful(relative):
        raise ValueError('missing evidence path')
    rel = Path(relative)
    if rel.is_absolute() or PureWindowsPath(relative).drive or '..' in rel.parts:
        raise ValueError('evidence paths must stay relative to the task root')
    path = root / rel
    if root.resolve() not in path.resolve().parents:
        raise ValueError('evidence resolves outside the task root')
    if notes_only and (root / '.hackathon-kit' / 'run') not in path.parents:
        raise ValueError('execution observations/reports must be under .hackathon-kit/run')
    if notes_only and (root / '.hackathon-kit' / 'run').resolve() not in path.resolve().parents:
        raise ValueError('execution evidence resolves outside the physical kit run directory')
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink evidence is not allowed')
        if getattr(current.lstat(), 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400):
            raise ValueError('reparse/junction evidence is not allowed')
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError('evidence must be a bounded regular file')
    with path.open('rb') as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError('evidence exceeds byte limit')
    return data


def verified_file(root, record, notes_only=False):
    if not isinstance(record, dict) or not isinstance(record.get('sha256'), str) or not HASH.fullmatch(record['sha256']):
        raise ValueError('evidence needs path and SHA256')
    data = read_local(root, record.get('path'), notes_only=notes_only)
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('evidence bytes changed: ' + record['path'])
    return data


def execution_errors(execution, kit, expected_role=None, expected_checkpoint=None,
                     expected_report=None, expected_scope=None):
    """Check recorded lifecycle and current scope, never infer a real launch from prose."""
    if not isinstance(execution, dict):
        return ['review execution receipt missing; dispatch is not completion']
    root = Path(kit).absolute().parent
    errors = []
    if execution.get('version') != 1 or execution.get('status') != 'COMPLETE':
        errors.append('review execution must be version 1 COMPLETE, not merely requested/launched')
    worker = execution.get('worker_id')
    if not meaningful(worker):
        errors.append('review execution needs the actual worker_id')
    for key, expected in (('role', expected_role), ('checkpoint', expected_checkpoint)):
        value = execution.get(key)
        if not meaningful(value) or (expected is not None and value != expected):
            errors.append('review execution %s does not match this review' % key)
    if execution.get('context_mode') not in ('NO_HISTORY', 'CLEAN_SESSION'):
        errors.append('review execution needs an observed clean context, not SELF_CHECK')
    observations = execution.get('observations')
    observations = observations if isinstance(observations, dict) else {}
    paths, times = set(), []
    for phase in PHASES:
        try:
            entry = observations.get(phase)
            data = verified_file(root, entry, notes_only=True)
            identity = str((root / entry['path']).resolve())
            if identity in paths:
                raise ValueError('each lifecycle observation needs its own retained record')
            paths.add(identity)
            event = load_json(data.decode('utf-8-sig'))
            if not isinstance(event, dict) or event.get('phase') != phase or event.get('worker_id') != worker:
                raise ValueError('observation phase/worker does not match')
            if not meaningful(event.get('tool')) or not event.get('raw'):
                raise ValueError('observation needs actual tool response, not a role summary')
            state = native_state(event['raw'], worker, event['tool'])
            allowed = {'LAUNCHED': {'launched', 'accepted', 'queued', 'pending', 'running', 'completed'},
                       'RUNNING': {'running', 'acknowledged', 'completed'},
                       'COMPLETED': {'completed'}}
            if state not in allowed[phase]:
                raise ValueError('native status %s cannot establish %s' % (state, phase))
            timestamp = event.get('observed_at')
            if not isinstance(timestamp, str):
                raise ValueError('observation time must be an ISO timestamp')
            instant = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if instant.tzinfo is None or instant.utcoffset() is None:
                raise ValueError('observation time needs a timezone')
            times.append(instant)
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError) as error:
            errors.append('%s observation: %s' % (phase, error))
    if len(times) == 3 and times != sorted(times):
        errors.append('review lifecycle observations are out of order')
    try:
        report = execution.get('report')
        data = verified_file(root, report, notes_only=True)
        if not data.strip():
            raise ValueError('empty review report')
        if expected_report is not None and report.get('path') != expected_report:
            raise ValueError('report is not the expected checkpoint report')
    except (OSError, ValueError, TypeError, KeyError) as error:
        errors.append('review report: %s' % error)
    scope = execution.get('reviewed_files')
    if not isinstance(scope, dict) or not scope:
        errors.append('review execution needs exact reviewed_files hashes')
    else:
        if expected_scope is not None and scope != expected_scope:
            errors.append('review execution scope does not match the reviewed checkpoint artifacts')
        for relative, digest in scope.items():
            try:
                if not isinstance(digest, str) or not HASH.fullmatch(digest):
                    raise ValueError('invalid scope SHA256')
                data = read_local(root, relative, SCOPE_LIMIT)
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError('reviewed file changed: ' + relative)
            except (OSError, ValueError, TypeError) as error:
                errors.append('review scope: %s' % error)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--receipt', required=True, help='Receipt path relative to the task root')
    parser.add_argument('--role', required=True)
    parser.add_argument('--checkpoint', required=True)
    args = parser.parse_args()
    try:
        value = load_json(read_local(args.kit.absolute().parent, args.receipt, notes_only=True).decode('utf-8-sig'))
        errors = execution_errors(value, args.kit, args.role, args.checkpoint)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        errors = [str(error)]
    if errors:
        print('REVIEW EXECUTION FAIL')
        for error in errors:
            print('-', error)
        return 2
    print('REVIEW EXECUTION RECORD OK: retained lifecycle/scope only; not authenticated identity or review acceptance')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
