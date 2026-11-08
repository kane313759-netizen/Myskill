#!/usr/bin/env python3
"""Compute a source-supplied planning schedule; never establish official rules."""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import stat


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON key: ' + key)
        value[key] = item
    return value


def _read_input(path):
    path = Path(path)
    info = path.lstat()
    linked = path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) &
                                      getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
    limit = 2 * 1024 * 1024
    if not stat.S_ISREG(info.st_mode) or linked or info.st_size > limit:
        raise ValueError('input must be a bounded regular non-symlink file')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(str(path), flags), 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('opened input must be a regular file')
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError('input exceeds byte limit')
    text = data.decode('utf-8-sig')
    blocks, current = [], None
    for line in text.splitlines(keepends=True):
        if line.strip() == '```json':
            if current is not None:
                raise ValueError('nested JSON fences are not allowed')
            current = []
        elif current is not None and line.strip() == '```':
            blocks.append(''.join(current))
            current = None
        elif current is not None:
            current.append(line)
    if current is not None:
        raise ValueError('JSON input block is not closed')
    if blocks:
        if len(blocks) != 1:
            raise ValueError('input document must contain exactly one JSON block')
        text = blocks[0]
    return json.loads(text, object_pairs_hook=_unique)


def _known(value):
    return value is not None and value not in ('', 'UNKNOWN', 'UNKNOWN_AFTER_INSPECTION')


def _instant(value, name):
    if not isinstance(value, str):
        raise ValueError(name + ' must be an ISO date/time with an explicit timezone')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(name + ' must be an ISO date/time with an explicit timezone')
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(name + ' timezone is missing')
    return result


def _minutes(values, names, default, minimum=0):
    value = next((values[name] for name in names if name in values), default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum or value > 1440:
        raise ValueError(names[0] + ' must be a finite minute count between %s and 1440' % minimum)
    if value != value or value in (float('inf'), float('-inf')):
        raise ValueError(names[0] + ' must be finite')
    return value


def calculate(values):
    """Return KNOWN planning bounds or UNKNOWN; input source truth stays external."""
    if not isinstance(values, dict):
        raise ValueError('deadline input must be an object')
    if 'switches' in values:
        if not isinstance(values['switches'], dict):
            raise ValueError('switches must be an object')
        values = dict(values['switches'])
    values = {key: item.get('value') if isinstance(item, dict) and 'value' in item else item
              for key, item in values.items()}
    followup = values.get('FOLLOWUP', 'UNKNOWN')
    missing = []
    if followup not in ('NONE', 'AFTER_CONFIRM', 'FIXED_TIME'):
        if followup in ('UNKNOWN', None, ''):
            return {'status': 'UNKNOWN', 'missing': ['FOLLOWUP'],
                    'notice': 'Obtain current official timing; no deadline was inferred.'}
        raise ValueError('FOLLOWUP must be NONE, AFTER_CONFIRM, FIXED_TIME or UNKNOWN')
    study = _minutes(values, ('S', 'STUDY_FINAL'), 60)
    study_pre = _minutes(values, ('S_pre', 'STUDY_PRE'), study)
    reserve = _minutes(values, ('R', 'SUBMISSION_RESERVE'), 10, 10)
    review = _minutes(values, ('C', 'REVIEW_RESERVE'), 40, 0.000001)
    choice = values.get('participant_study_choice', values.get('PARTICIPANT_STUDY_CHOICE'))
    chosen_study = study_pre if followup == 'NONE' else study
    if chosen_study != 60 and not (choice is True or
            (isinstance(choice, (int, float)) and not isinstance(choice, bool) and choice == chosen_study)):
        raise ValueError('non-default study time needs the actual participant study choice')
    if followup == 'NONE' and study_pre == 0 and values.get('PITCH_STUDY_WINDOW') != 'YES':
        raise ValueError('S_pre=0 requires confirmed PITCH_STUDY_WINDOW=YES')
    required = {'NONE': ('T_SUB',), 'AFTER_CONFIRM': ('WINDOW_END',),
                'FIXED_TIME': ('T_SUB', 'T_FU')}[followup]
    for name in required:
        if not _known(values.get(name)):
            missing.append(name)
    if missing:
        return {'status': 'UNKNOWN', 'missing': missing,
                'notice': 'Obtain current official timing; no deadline was inferred.'}
    times = {name: _instant(values[name], name) for name in ('T_SUB', 'WINDOW_END', 'T_FU')
             if _known(values.get(name))}
    if followup == 'FIXED_TIME':
        confirmation = min(times['T_SUB'], times['T_FU'] - timedelta(minutes=study))
        lock = confirmation - timedelta(minutes=reserve)
    elif followup == 'AFTER_CONFIRM':
        duration = _minutes(values, ('followup_minutes', 'FOLLOWUP_MINUTES'), 30, 0.000001)
        transition = _minutes(values, ('transition_minutes', 'TRANSITION_MINUTES'), 5)
        confirmation = times['WINDOW_END'] - timedelta(minutes=duration + transition)
        if 'T_SUB' in times:
            confirmation = min(confirmation, times['T_SUB'])
        lock = confirmation - timedelta(minutes=reserve + study)
    else:
        confirmation = times['T_SUB']
        lock = confirmation - timedelta(minutes=reserve + study_pre)
    start = confirmation - timedelta(minutes=reserve)
    cp3 = lock - timedelta(minutes=review)
    now = values.get('NOW', values.get('now'))
    if _known(now) and _instant(now, 'NOW') > cp3:
        raise ValueError('planned CP3 start is already past the observed NOW; replan explicitly')
    return {'status': 'KNOWN', 'followup': followup,
            'confirmation_deadline': confirmation.isoformat(), 'submission_start': start.isoformat(),
            'work_lock': lock.isoformat(), 'cp3_start': cp3.isoformat(),
            'study_minutes': chosen_study, 'submission_reserve_minutes': reserve,
            'review_reserve_minutes': review,
            'notice': 'Planning calculation only; inputs do not establish official rules or a live clock.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='JSON or Markdown with one JSON block')
    parser.add_argument('--output', type=Path, help='Optional new planning record; existing files are preserved')
    parser.add_argument('--observe-now', action='store_true', help='Use an actual local system-clock observation')
    args = parser.parse_args()
    try:
        values = _read_input(args.input)
        if args.observe_now:
            if not isinstance(values, dict):
                raise ValueError('input must be an object')
            values = dict(values)
            key = 'switches' if 'switches' in values else None
            if key:
                if not isinstance(values[key], dict):
                    raise ValueError('switches must be an object')
                values[key] = dict(values[key])
                values[key]['NOW'] = datetime.now().astimezone().isoformat()
            else:
                values['NOW'] = datetime.now().astimezone().isoformat()
        result = calculate(values)
        rendered = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
        if args.output:
            # A named output is explicit authorization to create a new record, not overwrite it.
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(rendered)
        print(rendered, end='')
        return 0 if result['status'] == 'KNOWN' else 1
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        print('DEADLINE FAIL: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
