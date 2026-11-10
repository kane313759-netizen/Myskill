#!/usr/bin/env python3
"""Read-only v2.7 evidence checks. Never advances STATE, a gate or a submission."""
import argparse
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import runpy
import sys
import unicodedata


SWITCHES = ('FOLLOWUP', 'T_SUB', 'WINDOW_END', 'LUNCH_POLICY', 'WORK_ENV',
            'AI_SCOPE', 'MODELS', 'EXTERNAL_TRANSFER', 'GIT_PUSH', 'COMPUTER_USE',
            'SUBMISSION', 'S', 'PITCH_STUDY_WINDOW', 'EXECUTION_TOOLS')
CORE = {'independent_reviews', 'submission_constraints', 'clean_replay',
        'security_and_transfer', 'safe_fallback'}


class UnverifiedExecution(Exception):
    """A retained platform observation needs an available reviewed adapter."""


def module(name):
    return runpy.run_path(str(Path(__file__).with_name(name + '.py')))


def meaningful(value):
    return isinstance(value, str) and value.strip().upper() not in (
        '', 'UNKNOWN', 'TODO', 'NOT_RUN', 'N/A', 'NONE')


def utf8_warning(is_windows, utf8_mode):
    return ('Windows Python UTF-8 mode is off; run kit checks as <actual python.exe> -X utf8 -I <script> '
            '(-I ignores PYTHONUTF8)') if is_windows and not utf8_mode else None


# A retained native command is accepted only when its meaning does not depend on which shell ran it:
# every shell that could have received it (PowerShell, cmd.exe, bash) either reads exactly argv or cannot run it.
# Environment assignments allowed in front: -I already makes Python ignore PYTHON* variables, and the thread
# counts only size numeric libraries.
SAFE_COMMAND_ENV = frozenset(('PYTHONUTF8', 'PYTHONIOENCODING', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                              'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'))
_ENV_VALUE = r"[A-Za-z0-9_.:-]{0,64}"
_PS_ENV = re.compile(r"\$env:([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*(?:'(%s)'|\"(%s)\"|(%s))[ \t]*;[ \t]*" % ((_ENV_VALUE,) * 3))
_SH_ENV = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(?:'(%s)'|\"(%s)\"|(%s))[ \t]+" % ((_ENV_VALUE,) * 3))
_RAW_TOKEN = re.compile(r"'([^']*)'|\"([^\"]*)\"|([^\s'\"]+)")
_BARE_PUNCT = frozenset('_-./:=+')
_QUOTED_PUNCT = frozenset('_-./:=+,()@# ')


def _letter(ch):
    return (ch.isascii() and ch.isalnum()) or (not ch.isascii() and unicodedata.category(ch)[0] in 'LNM')


def _plain(text, punct, backslash):
    """Letters, digits and marks of any script plus an explicit punctuation set; nothing any shell treats specially.

    `~` is allowed only right after a letter or digit (Windows short names such as RUNNER~1): bash expands it
    only at the start of a word or after `=`/`:`, and PowerShell and cmd.exe never expand it inside a word."""
    for index, ch in enumerate(text):
        if ch == '\\':
            if not backslash:
                return False
        elif ch == '~':
            if index == 0 or not _letter(text[index - 1]):
                return False
        elif ch not in punct and not _letter(ch):
            return False
    return True


def command_tokens(command):
    """argv of a retained command whose meaning is the same in every shell that could run it, else None.

    PowerShell shape: `[$env:NAME='v'; ...] & 'python.exe' '-I' ...`. bash rejects the line as a syntax error;
      cmd.exe either rejects it or fails on the single-quoted interpreter, so only PowerShell can run it.
    POSIX shape: `NAME=v ... python -I ...` or a single-quoted interpreter without `&`. PowerShell and cmd.exe
      cannot run either form, so only a POSIX shell can.
    Neutral shape: bare and double-quoted words only. PowerShell, cmd.exe and bash split these identically.
    Words hold only letters, digits, marks and plain punctuation, so no shell expands, joins, splits or redirects them."""
    if not isinstance(command, str) or not command or command != command.strip(' \t') or '\n' in command or '\r' in command:
        return None
    position, ps_env, posix_env = 0, False, False
    while True:
        match = _PS_ENV.match(command, position)
        if not match:
            break
        if match.group(1) not in SAFE_COMMAND_ENV:
            return None
        ps_env, position = True, match.end()
    while not ps_env:
        match = _SH_ENV.match(command, position)
        if not match:
            break
        if match.group(1) not in SAFE_COMMAND_ENV:
            return None
        posix_env, position = True, match.end()
    call = not posix_env and command.startswith('& ', position)
    if call:
        position += 2
        while position < len(command) and command[position] in ' \t':
            position += 1
    elif ps_env:
        return None  # without the call operator PowerShell would only print the strings
    words = []
    while position < len(command):
        match = _RAW_TOKEN.match(command, position)
        if not match:
            return None
        kind = 'single' if match.group(1) is not None else 'double' if match.group(2) is not None else 'bare'
        words.append((kind, match.group(match.lastindex)))
        position = match.end()
        if position < len(command):
            if command[position] not in ' \t':
                return None
            while command[position] in ' \t':
                position += 1
    if not words:
        return None
    first_kind, first = words[0]
    if call:
        mode = 'powershell'
        if first_kind != 'single' and any(kind == 'single' for kind, _ in words):
            return None  # cmd.exe could run an unquoted interpreter after `&` and keep the single quotes
    elif posix_env or first_kind == 'single':
        mode = 'posix'
    else:
        mode = 'neutral'
    if '=' in first:
        return None
    # bash reads backslashes differently; allow them only where bash cannot run the command at all.
    backslash = mode == 'powershell' or (mode == 'neutral' and '\\' in first and '/' not in first)
    for kind, text in words:
        if kind == 'bare':
            if not text or text.endswith('\\') or not _plain(text, _BARE_PUNCT, backslash):
                return None
            if text[0] in '+=:' or text[0].isdigit() or (text[0] == '.' and text[1:2].isdigit()):
                return None  # PowerShell reads numbers, signs and these leading marks in its own way
            if text.startswith('-') and (not any(ch.isascii() and ch.isalnum() for ch in text) or text[1:2].isdigit()
                                         or not all(ch in '-_' or (ch.isascii() and ch.isalnum()) for ch in text)):
                return None  # PowerShell splits -name.part / -name:value, and may consume -- or read -5 as a number
        else:
            if kind == 'single' and mode == 'neutral':
                return None
            if not text or text.endswith('\\') or not _plain(text, _QUOTED_PUNCT, backslash):
                return None
    return [text for _, text in words]


def command_matches(command, argv):
    """True when the retained tool command is, in any shell that could run it, exactly the retained argv."""
    return isinstance(argv, list) and command_tokens(command) == argv


def interpreter_flags_ok(flags):
    """Only isolation/buffering flags and UTF-8 mode may sit between the interpreter and the kit script."""
    index = 0
    while index < len(flags):
        if flags[index] in ('-I', '-B', '-u', '-Xutf8'):
            index += 1
        elif flags[index] == '-X' and index + 1 < len(flags) and flags[index + 1] == 'utf8':
            index += 2
        else:
            return False
    return True


def audit_limit_warnings(audit):
    messages=list(audit.get('warnings',[]))
    for artifact in audit.get('files', []):
        for limit in artifact.get('analysis_limits', []):
            messages.append('data_audit analysis limited: %s / %s / %s / dropped=%s' %
                            (artifact.get('path'),limit.get('check'),limit.get('column'),limit.get('dropped')))
    return messages


def r3_policy(findings=(), impacts=(), gates=(), assumptions=(), keep_baseline=False,
              type_a=(), type_b=(), requests=(), comparison_verified=False):
    errors, pending, warnings = [], [], []
    allowed = {'response_shape', 'missing_reference_join', 'progress_variable', 'operating_shift'}
    for finding in findings:
        match = next((x for x in impacts if x.get('item_id') == finding.get('item_id') and
                      (x.get('finding_ref') == finding.get('finding_ref') or meaningful(x.get('unmeasurable_reason')))), None)
        if match is None:
            errors.append('audit FINDING missing impact record')
        elif meaningful(match.get('unmeasurable_reason')):
            warnings.append('audit FINDING impact cannot be measured: ' + match['unmeasurable_reason'])
        elif not all(meaningful(match.get(k)) for k in ('finding_ref','action','metric','split','grader_sha256')) or any(type(match.get(k)) not in (int,float) or not math.isfinite(match[k]) for k in ('before','after')) or len(match['grader_sha256']) != 64:
            errors.append('audit FINDING requires metric before/after split and grader hash')
    for gate in gates:
        a,b = gate.get('baseline_value'), gate.get('candidate_value')
        direction=gate.get('direction')
        if not meaningful(gate.get('metric')) or direction not in ('HIGHER_IS_BETTER','LOWER_IS_BETTER') or any(type(x) not in (int,float) or not math.isfinite(x) for x in (a,b)) or not isinstance(gate.get('evidence'),dict):
            errors.append('gate metric, finite values, direction and evidence required')
    policy = module('v27_comparison')['comparison_policy']({'gates':list(gates)})
    warnings.extend(policy['warnings'])
    if keep_baseline:
        names=[x.get('check') for x in assumptions if isinstance(x,dict)] if isinstance(assumptions,list) else []
        if not isinstance(assumptions,list) or len(names) != len(assumptions) or len(set(names)) < 3 or not set(names) <= allowed or len(names) != len(set(names)) or any(not meaningful(x.get('method')) or not meaningful(x.get('result')) for x in assumptions if isinstance(x,dict)):
            pending.append('baseline assumptions require three distinct documented allowed checks')
    topics={'problem_choice','miss_vs_overkill','speed_vs_precision','risk_tolerance','final_study_minutes','emergency_no_review'}
    for choice in type_a:
        if choice.get('topic_key') not in topics or not isinstance(choice.get('question_ref'),dict) or not isinstance(choice.get('answer_ref'),dict):
            errors.append('type A topic or question/answer reference invalid')
    for card in type_b:
        evidence=card.get('evidence_score')
        if not isinstance(evidence,dict) or not meaningful(evidence.get('metric')) or any(type(evidence.get(k)) not in (int,float) or not math.isfinite(evidence[k]) for k in ('score','alternative_difference')):
            errors.append('type B evidence_score needs tuning score and alternative difference')
    for request in requests:
        fields=('hypothesis','target','expected_if_true','expected_if_false','layer_check')
        if any(not meaningful(request.get(k)) for k in fields) or type(request.get('budget_left')) is not int or request['budget_left'] < 0:
            errors.append('external request requires hypothesis, target, both expected outcomes, budget and layer check')
        if request.get('state') == 'PENDING':
            if request.get('deadline_fallback') is True and comparison_verified:
                warnings.append('pending external response: verified submission used deadline fallback')
            else:
                pending.append('external request pending: do not lock before response')
    return {'errors':errors,'pending':pending,'warnings':warnings}


MILESTONES = ('cp3_start', 'work_lock', 'submission_start', 'confirmation_deadline')


def exact(value):
    """Type-strict canonical text: 1, 1.0 and true differ; key order does not."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def observed_plans(calculate, env, calculated):
    """Every result deadline.py can print for this ENV: the plan and each --observe-now outcome.

    The clock only changes which milestones are `passed` (and the matching warning/status), so
    one observation per milestone boundary enumerates all outcomes. A recorded deadline must
    equal one of them exactly; nothing is stripped or tolerated. --observe-now replaces any
    NOW/now already written in ENV, so the outcomes are built without that stale value.
    """
    def with_now(now):
        observed = json.loads(json.dumps(env))
        target = observed['switches'] if isinstance(observed.get('switches'), dict) else observed
        target.pop('NOW', None)
        target.pop('now', None)
        if now is not None:
            target['NOW'] = now.isoformat()
        return calculate(observed)

    plans = [calculated]
    try:
        plans.append(with_now(None))
        instants = sorted({datetime.fromisoformat(calculated[name]) for name in MILESTONES})
    except (KeyError, TypeError, ValueError):
        return plans
    for now in instants[1:] + [instants[-1] + timedelta(seconds=1)]:
        plans.append(with_now(now))
    return plans


def path_index(argv, expected):
    """Locate the actual absolute path token using host filesystem semantics."""
    normalized = os.path.normcase(str(Path(expected).resolve()))
    for index, value in enumerate(argv):
        candidate = Path(value)
        if candidate.is_absolute() and os.path.normcase(str(candidate.resolve())) == normalized:
            return index
    return None


def _check(plan, root, kit, phase='final', source=None):
    """Validate retained task evidence; hashes are integrity checks, not authentication."""
    h = module('v27_common')
    root, kit = Path(root), Path(kit)
    errors, pending, warnings = [], [], []
    window_warning = utf8_warning(os.name == 'nt', sys.flags.utf8_mode)
    if window_warning:
        warnings.append(window_warning)
    execution_tools = ['exec_command']
    records = plan.get('records', {}) if isinstance(plan, dict) else {}
    if not isinstance(plan, dict) or plan.get('version') != 1 or not isinstance(records, dict):
        return dict(status='FAIL', errors=['version 1 evidence plan with records required'], unverified=[], warnings=[])

    def bound(ref):
        if not isinstance(ref, dict):
            raise ValueError('path and sha256 evidence reference required')
        path = h['safe_path'](root, ref.get('path'))
        if h['sha256_file'](path) != ref.get('sha256'):
            raise ValueError('stale or missing SHA256: ' + str(ref.get('path')))
        return path

    def record(name, required=True):
        if name not in records:
            if required:
                pending.append(name + ': retained record missing')
            return None
        try:
            value = h['extract_json_document'](bound(records[name]))
            if not isinstance(value, dict) or not value:
                raise ValueError('record must be a nonempty evidence object')
            return value
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(name + ': ' + str(exc))
            return None

    def hashes(value, label):
        if not isinstance(value, dict) or not value:
            errors.append(label + ': actual source hashes required')
            return
        for path, digest in value.items():
            try:
                bound(dict(path=path, sha256=digest))
            except (OSError, ValueError, TypeError) as exc:
                errors.append(label + ': ' + str(exc))

    def native(proof):
        tool = proof.get('tool')
        if tool == 'MANUAL_TRANSCRIPT' or tool not in execution_tools:
            raise UnverifiedExecution('실행 도구를 확인할 수 없음: ' + str(tool) + '; retained observation remains UNVERIFIED')
        request, result = proof.get('request', {}), proof.get('result', {})
        command, argv = request.get('cmd', ''), proof.get('argv', [])
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
            raise ValueError('actual argv required alongside native command')
        if not command_matches(command, argv):
            raise ValueError('native command is not the exact retained argv')
        if '-I' not in argv or any(x in argv for x in ('-c', '-m', '--eval')):
            raise ValueError('actual isolated native command/result required')
        if Path(argv[0]).resolve() != Path(sys.executable).resolve() or result.get('exit_code') != 0:
            raise ValueError('unexpected interpreter or unsuccessful native result')
        return argv, json.loads(result['output'])

    def review_context(receipt):
        launch = h['read_json'](bound(receipt.get('observations', {}).get('LAUNCHED')))
        queue = [launch]
        while queue:
            item = queue.pop()
            if isinstance(item, dict):
                if item.get('context_mode') in ('SAME_CONVERSATION', 'INHERITED', 'SHARED') or item.get('fork_turns') == 'all':
                    errors.append('independent review contradicts retained inherited-context launch evidence')
                queue.extend(item.values())
            elif isinstance(item, list):
                queue.extend(item)

    def execution(name, value, script):
        try:
            ref = records[name].get('execution')
            if not ref:
                pending.append(name + ': native execution evidence missing')
                return
            proof = h['read_json'](bound(ref))
            argv, output = native(proof)
            script_index = path_index(argv, Path(__file__).with_name(script))
            if script_index is None or not interpreter_flags_ok(argv[1:script_index]):
                raise ValueError('actual isolated native command/result required')
            if argv.index('-I') > script_index:
                raise ValueError('unexpected interpreter or isolation flag placement')
            def option(name):
                if argv.count(name) != 1:
                    raise ValueError('exactly one ' + name + ' required')
                return argv[argv.index(name) + 1]
            if Path(option('--root')).resolve() != root.resolve():
                raise ValueError('native execution selected a different task root')
            key, flag = {'submission': ('submission_rules', '--rules'), 'security': ('security_plan', '--plan'), 'clean_run': ('clean_run_plan', '--plan')}[name]
            selected = Path(option(flag)).absolute()
            relative = selected.relative_to(root.absolute()).as_posix()
            if h['read_json'](h['safe_path'](root, relative)) != plan.get(key):
                raise ValueError('native execution used different or changed rules/plan')
            if output != value:
                raise ValueError('native stdout does not match retained result')
        except UnverifiedExecution as exc:
            pending.append(name + ': execution: ' + str(exc))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(name + ': execution: ' + str(exc))

    try:
        env = h['extract_json_document'](h['safe_path'](root, plan.get('env_path')))
        switches = env.get('switches', {})
        if not isinstance(switches, dict):
            raise ValueError('ENV switches must be an object')
        for name in set(SWITCHES) | set(switches):
            item = switches.get(name)
            if not isinstance(item, dict) or 'value' not in item or item.get('classification') not in ('CONFIRMED', 'PLAN_DEFAULT', 'UNKNOWN'):
                errors.append('ENV ' + name + ': classified value required')
                continue
            if item['classification'] == 'CONFIRMED':
                text = h['read_bytes'](bound(dict(path=item.get('source_path'), sha256=item.get('source_sha256')))).decode('utf-8-sig')
                if not meaningful(item.get('source_excerpt')) or item['source_excerpt'] not in text:
                    errors.append('ENV ' + name + ': exact source excerpt missing')
            elif not meaningful(item.get('reason')):
                errors.append('ENV ' + name + ': default/unknown needs a reason')
            if name in ('EXTERNAL_TRANSFER', 'GIT_PUSH', 'COMPUTER_USE') and item.get('value') in ('ALLOWED', 'PERMITTED') and item.get('classification') != 'CONFIRMED':
                errors.append('ENV ' + name + ': permission needs current official evidence')
            enums = {'LUNCH_POLICY': ('PAUSE', 'CONTINUOUS', 'UNKNOWN'), 'WORK_ENV': ('LOCAL', 'PROVIDED', 'CLOUD', 'UNKNOWN'),
                     'EXTERNAL_TRANSFER': ('PROHIBITED', 'ALLOWED', 'UNKNOWN'), 'GIT_PUSH': ('PROHIBITED', 'ALLOWED', 'UNKNOWN'),
                     'COMPUTER_USE': ('PROHIBITED', 'ALLOWED', 'UNKNOWN'), 'PITCH_STUDY_WINDOW': ('YES', 'NO', 'UNKNOWN')}
            if name in enums and item['value'] not in enums[name]:
                errors.append('ENV ' + name + ': invalid explicit switch value')
            if name == 'AI_SCOPE' and (not isinstance(item['value'], list) or not item['value'] or not all(meaningful(x) for x in item['value'])):
                errors.append('AI_SCOPE needs an explicit nonempty permitted/preparation list')
        execution_tools = switches.get('EXECUTION_TOOLS', {}).get('value')
        if not isinstance(execution_tools, list) or not execution_tools or not all(meaningful(value) for value in execution_tools) or len(set(execution_tools)) != len(execution_tools):
            errors.append('EXECUTION_TOOLS needs an explicit nonempty distinct list of platform tool names')
            execution_tools = []
        models = switches.get('MODELS', {}).get('value', {})
        if not isinstance(models, dict):
            raise ValueError('MODELS value must be an object')
        for key in ('AVAILABLE', 'RECOMMENDED', 'RESTRICTED'):
            if not isinstance(models.get(key), list):
                errors.append('MODELS ' + key + ': explicit actual list required')
        if not isinstance(env.get('assignments'), dict):
            raise ValueError('explicit actual model assignments required')
        required_roles = {'MAIN', 'CONSTRAINT_RED', 'DATA_EVAL_RED', 'ALGORITHM_RED', 'CODE_RED', 'EDGE_RED', 'SUBMISSION_RED'}
        if not required_roles <= set(env['assignments']):
            errors.append('actual role assignments must be explicit, using UNKNOWN when unverified')
        for role, selected in env['assignments'].items():
            if selected == 'UNKNOWN':
                warnings.append(role + ': actual model selection UNKNOWN')
            elif selected in models.get('RESTRICTED', []):
                errors.append(role + ': RESTRICTED model assigned')
            elif selected not in models.get('AVAILABLE', []):
                errors.append(role + ': model was not actually available')
        state = record('state')
        calculated = module('deadline')['calculate'](env)
        if calculated.get('status') == 'PAST_CONFIRMATION':
            pending.append('deadline: confirmation deadline has passed; submission is not established')
        elif calculated.get('status') != 'KNOWN':
            pending.append('deadline: official usable cutoff is UNKNOWN')
        else:
            followup = switches.get('FOLLOWUP', {}).get('value')
            required_time = ('WINDOW_END',) if followup == 'AFTER_CONFIRM' else ('T_SUB',)
            if followup == 'FIXED_TIME':
                required_time += ('T_FU',)
            if any(switches.get(key, {}).get('classification') != 'CONFIRMED' for key in required_time):
                pending.append('deadline: computed planning target is not an official confirmed cutoff')
        if state and calculated.get('status') in ('KNOWN', 'PAST_CONFIRMATION'):
            if exact(state.get('deadline')) not in {exact(item) for item in observed_plans(module('deadline')['calculate'], env, calculated)}:
                errors.append('V27_STATE deadline differs from recalculation')
            elif calculated['status'] == 'KNOWN' and state['deadline'].get('status') == 'PAST_CONFIRMATION':
                pending.append('deadline: confirmation deadline has passed; submission is not established')
        if source:
            errors.extend(h['check_protected'](source))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append('ENV/deadline: ' + str(exc))
    if phase == 'intake':
        return dict(status='FAIL' if errors else 'UNVERIFIED' if pending else 'PASS', errors=errors, unverified=pending, warnings=warnings)

    audit = record('data_audit')
    if audit:
        warnings.extend(audit_limit_warnings(audit))
        try:
            fresh = module('data_audit')['audit'](root, plan.get('data_audit_plan', {}))
            if fresh != audit:
                errors.append('data_audit: retained result differs from current bounded audit')
            if not audit.get('scope', {}).get('all_provided_rows_examined'):
                pending.append('data_audit: full scan of explicitly provided rows is incomplete')
            items = audit.get('items', [])
            if {item.get('id') for item in items} != set(range(1, 11)) or len(items) != 10:
                errors.append('data_audit: exactly ten distinct items required')
            resolution = record('data_audit_resolution', required=False)
            resolved = {item.get('id'): item for item in (resolution or {}).get('items', [])}
            for item in items:
                if item.get('status') == 'UNVERIFIED':
                    reviewed = resolved.get(item.get('id'), {})
                    if reviewed.get('status') not in ('RECORDED', 'FINDING') or not meaningful(reviewed.get('method')) or not meaningful(reviewed.get('finding')):
                        pending.append('data_audit item %s remains UNVERIFIED' % item.get('id'))
                    else:
                        bound(reviewed.get('evidence'))
                        hashes(reviewed.get('source_hashes'), 'audit resolution sources')
                        expected = {value['path']: value['sha256'] for value in audit.get('files', []) if value.get('sha256')}
                        expected.update({records['data_audit']['path']: records['data_audit']['sha256'], plan['spec_draft']['path']: plan['spec_draft']['sha256']})
                        if reviewed.get('data_audit_sha256') != records['data_audit']['sha256'] or any(reviewed.get('source_hashes', {}).get(path) != value for path, value in expected.items()):
                            errors.append('audit resolution is stale or does not cover current audit, inputs and SPEC_DRAFT')
            errors.extend('data_audit: ' + error for error in audit.get('errors', []))
            spec = h['read_bytes'](bound(plan.get('spec_draft'))).decode('utf-8-sig')
            ref = records['data_audit']
            if ref['path'] not in spec or ref['sha256'] not in spec:
                errors.append('SPEC_DRAFT must bind DATA_AUDIT path and SHA256')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append('data_audit: ' + str(exc))

    grading = record('grading')
    if grading:
        baseline = grading.get('baseline', {})
        if baseline.get('status') not in ('AVAILABLE', 'UNAVAILABLE_WITH_REASON'):
            pending.append('baseline: observed availability/reason not recorded')
        if baseline.get('status') == 'UNAVAILABLE_WITH_REASON' and not meaningful(baseline.get('reason')):
            errors.append('baseline unavailable needs an actual reason')
        if grading.get('local_grader_used') is True:
            hashes(grading.get('evaluator_hashes'), 'grader evaluators')
            hashes(grading.get('input_scope'), 'grader input scope')
            controls = grading.get('controls', [])
            positives = [x for x in controls if x.get('kind') == 'POSITIVE']
            negatives = [x for x in controls if x.get('kind') == 'NEGATIVE']
            if not 1 <= len(positives) <= 3 or not negatives:
                errors.append('grader needs 1-3 independent known answers and justified negative controls')
            ids, cases = set(), set()
            for control in controls:
                try:
                    fingerprint = (control.get('input', {}).get('sha256'), control.get('output', {}).get('sha256'), control.get('oracle', {}).get('sha256'), json.dumps(control.get('expected_metrics'), sort_keys=True))
                    if not meaningful(control.get('id')) or control['id'] in ids or fingerprint in cases:
                        raise ValueError('controls require distinct IDs and independent case fingerprints')
                    ids.add(control['id']); cases.add(fingerprint)
                    oracle = control.get('oracle', {})
                    text = h['read_bytes'](bound(oracle)).decode('utf-8-sig')
                    if oracle.get('origin') != 'REQUIREMENT_DERIVED' or not meaningful(oracle.get('excerpt')) or oracle['excerpt'] not in text:
                        raise ValueError('independent requirement-derived oracle required; candidate output is not an oracle')
                    bound(control.get('input')); bound(control.get('output'))
                    observed = h['read_json'](bound(control.get('execution')))
                    argv, output = native(observed)
                    selected = next((index for index in (path_index(argv, root / name) for name in grading.get('evaluator_hashes', {})) if index is not None), None)
                    if selected is None or argv.index('-I') > selected or not interpreter_flags_ok(argv[1:selected]):
                        raise ValueError('control native command did not invoke its bound evaluator')
                    if observed.get('input') != control.get('input') or observed.get('output') != control.get('output') or any(path_index(argv, root / control[key]['path']) is None for key in ('input', 'output')):
                        raise ValueError('control native invocation does not bind its input and candidate output')
                    if observed.get('evaluator_hashes') != grading.get('evaluator_hashes') or observed.get('input_scope') != grading.get('input_scope'):
                        raise ValueError('control execution evaluator/data scope differs from current grader')
                    if output.get('metrics') != control.get('actual_metrics') or output.get('rejected', False) != control.get('rejected', False):
                        raise ValueError('actual metrics/rejection differ from native evaluator output')
                    if control.get('kind') == 'POSITIVE' and control.get('actual_metrics') != control.get('expected_metrics'):
                        raise ValueError('known-answer exact expected metrics did not match')
                    if control.get('kind') == 'POSITIVE' and not control.get('expected_metrics'):
                        raise ValueError('known-answer expected metrics missing')
                    if control.get('kind') == 'NEGATIVE' and not (control.get('rejected') is True or control.get('relation') == 'LOWER_THAN_KNOWN_ANSWER'):
                        raise ValueError('negative control must be rejected or score lower under the declared contract')
                    if control.get('kind') == 'NEGATIVE' and not meaningful(control.get('contract_reason')):
                        raise ValueError('negative control needs a contract-specific reason')
                    if control.get('kind') == 'NEGATIVE' and control.get('rejected') is not True:
                        positive = next((x for x in positives if x.get('id') == control.get('known_answer_id')), {})
                        metric, direction = control.get('metric'), control.get('direction')
                        actual, known = control.get('actual_metrics', {}).get(metric), positive.get('actual_metrics', {}).get(metric)
                        if type(actual) not in (int, float) or type(known) not in (int, float) or direction not in ('HIGHER_IS_BETTER', 'LOWER_IS_BETTER') or not (actual < known if direction == 'HIGHER_IS_BETTER' else actual > known):
                            raise ValueError('negative metric must actually be worse than its independent known answer')
                except UnverifiedExecution as exc:
                    pending.append('grader control: ' + str(exc))
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    errors.append('grader control: ' + str(exc))
        elif grading.get('local_grader_used') is not False:
            pending.append('whether a local grader was used is UNKNOWN')
        holdout = grading.get('holdout', {})
        if holdout.get('applicable'):
            looks = holdout.get('looks')
            if type(looks) is not int or looks < 0 or not meaningful(holdout.get('purpose')) or type(holdout.get('adaptive_selection')) is not bool:
                errors.append('holdout requires nonnegative looks, purpose and adaptive_selection')
            elif looks >= 4 or holdout['adaptive_selection']:
                warnings.append('holdout used for selection/repeated looks: TUNING, not independent final evidence')
                if holdout.get('label') != 'TUNING' or holdout.get('independent_final_claim') is not False:
                    errors.append('adaptive/repeated holdout must be TUNING with no independent final-test claim')

    decisions = record('decisions')
    if decisions:
        choice_policy = r3_policy(type_a=decisions.get('type_a_choices', []), type_b=decisions.get('type_b_cards', []))
        errors.extend(choice_policy['errors'])
        for choice in decisions.get('type_a_choices', []):
            try:
                bound(choice.get('question_ref')); bound(choice.get('answer_ref'))
            except (OSError, ValueError, TypeError) as exc:
                errors.append('type A question/answer evidence: ' + str(exc))
        for card in decisions.get('type_b_cards', []):
            if not all(meaningful(card.get(key)) for key in ('decision', 'chosen', 'why', 'alternative', 'limitations', 'change_location')):
                errors.append('type B card needs decision, explanation, alternative, limitations and change_location')
            if card.get('selection_by') == 'PARTICIPANT' or card.get('participant_approval_required') is True:
                errors.append('technical Type B choices must not be delegated as participant A/B approval')
            elif card.get('selection_by') != 'AI':
                pending.append('type B: AI ownership of technical selection is not recorded')
        # Participant acknowledgement is deliberately not a gate.
    safety = record('safety')
    if safety:
        required = CORE | ({'agent_instruction_boundary', 'irreversible_action_approval', 'current_document_only'} if safety.get('agent_or_interactive') else set())
        if not required <= set(safety.get('enabled_core', [])):
            errors.append('shrink mode cannot disable required safety core')
        if phase == 'final':
            for name in required:
                proof = safety.get('results', {}).get(name)
                if not isinstance(proof, dict) or proof.get('status') != 'PASS':
                    pending.append('safety ' + name + ': actual successful test missing')
                else:
                    try:
                        observed = h['read_json'](bound(proof.get('evidence')))
                        hashes(proof.get('scope'), 'safety ' + name)
                        replay = record('clean_run', required=False) or {}
                        required_scope = dict(replay.get('input_sha256', {}))
                        required_scope.update({x['path']: x['sha256'] for x in replay.get('artifacts', [])})
                        if not required_scope or any(proof.get('scope', {}).get(path) != digest for path, digest in required_scope.items()):
                            raise ValueError('safety scope does not cover current replay inputs and final artifacts')
                        argv, outcome = native(observed)
                        if outcome.get('tests', {}).get(name) != 'PASS' or outcome.get('scope') != proof.get('scope') or not any(path_index(argv, root / path) is not None for path in proof.get('scope', {})):
                            raise ValueError('safety verdict is not bound to an actual current test command/result')
                    except UnverifiedExecution as exc:
                        pending.append('safety ' + name + ': ' + str(exc))
                    except (OSError, ValueError, TypeError) as exc:
                        errors.append('safety ' + name + ': ' + str(exc))
    study = record('study', required=phase == 'final')
    if study:
        if study.get('final_minutes', 60) < 60 and not study.get('participant_choice'):
            errors.append('reduced study time requires actual participant choice')
        if phase == 'final' and study.get('delivery') != 'DELIVERED':
            pending.append('study: prepared notes do not prove actual delivery')
        elif phase == 'final':
            try:
                bound(study.get('actual_delivery_evidence'))
            except (OSError, ValueError, TypeError):
                pending.append('study: actual delivery evidence missing or stale')
        if study.get('participant_choice'):
            try:
                bound(study['participant_choice'])
            except (OSError, ValueError, TypeError) as exc:
                errors.append('study participant choice: ' + str(exc))

    reviews = record('finals_reviews' if phase == 'final' else 'cp1_reviews')
    if reviews:
        try:
            if phase == 'final':
                replay = record('clean_run', required=False) or {}
                current = dict(replay.get('input_sha256', {}))
                current.update({x['path']: x['sha256'] for x in replay.get('artifacts', [])})
                current.update({x['path']: x['sha256'] for x in (audit or {}).get('files', []) if x.get('sha256')})
                for ref in (records.get('data_audit'), plan.get('spec_draft'), records.get('data_audit_resolution')):
                    if ref:
                        current[ref['path']] = ref['sha256']
                if not current or any(reviews.get('required_scope', {}).get(path) != digest for path, digest in current.items()):
                    errors.append('CP3 independent scope must cover current replay inputs/artifacts, audited sources, SPEC_DRAFT and DATA_AUDIT evidence')
                errors.extend(module('finals_review_check')['check_reviews'](reviews, kit, 'FINAL'))
            else:
                policy = module('review_execution')
                base = module('finals_review_check')
                errors.extend(base['check_hashes'](reviews.get('required_scope'), root, policy, 'CP1 required_scope'))
                for ref in (records.get('data_audit'), plan.get('spec_draft'), records.get('data_audit_resolution')):
                    if ref and reviews.get('required_scope', {}).get(ref['path']) != ref['sha256']:
                        errors.append('CP1 independent scope must contain current DATA_AUDIT, SPEC_DRAFT and any semantic resolution')
                workers, reports = set(), set()
                for role in ('CONSTRAINT_RED', 'DATA_EVAL_RED'):
                    entry = reviews.get('reviews', {}).get(role, {})
                    if entry.get('status') != 'ACCEPTED':
                        errors.append(role + ': actual independent review is not ACCEPTED')
                    errors.extend(base['findings_errors'](entry.get('findings'), policy['meaningful']))
                    receipt = h['read_json'](bound(entry.get('execution_receipt')))
                    errors.extend(policy['execution_errors'](receipt, kit, role, 'CP1'))
                    review_context(receipt)
                    if receipt.get('worker_id') in workers or receipt.get('report', {}).get('sha256') in reports:
                        errors.append('CP1 independent roles reused a worker or identical report')
                    workers.add(receipt.get('worker_id')); reports.add(receipt.get('report', {}).get('sha256'))
                    if any(receipt.get('reviewed_files', {}).get(path) != digest for path, digest in reviews.get('required_scope', {}).items()):
                        errors.append(role + ': required current scope is absent')
            if phase == 'final':
                for entry in reviews.get('reviews', {}).values():
                    if entry.get('execution_receipt'):
                        review_context(h['read_json'](bound(entry['execution_receipt'])))
                previous = record('previous_reviews')
                if previous:
                    previous_entries = previous.get('reviews', {})
                    if previous.get('version') != 1 or previous.get('checkpoint') != 'CP2' or not isinstance(previous_entries, dict) or not previous_entries.get('CODE_RED', {}).get('execution_receipt'):
                        errors.append('previous reviews need the actual CP2 CODE_RED execution receipt')
                    else:
                        policy = module('review_execution')
                        for role, entry in previous_entries.items():
                            if not entry.get('execution_receipt'):
                                if entry.get('status') != 'NOT_APPLICABLE':
                                    errors.append('previous ' + role + ': completed historical receipt missing')
                                continue
                            historical = h['read_json'](bound(entry['execution_receipt']))
                            # Historical product bytes may have changed after CP2.
                            # Reuse the original lifecycle/report checks, validating
                            # historical path/hash declarations separately below.
                            errors.extend('previous ' + error for error in policy['execution_errors'](historical, kit, role, 'CP2') if not error.startswith('review scope:'))
                            for path, digest in historical.get('reviewed_files', {}).items():
                                h['safe_path'](root, path, must_exist=False)
                                if not isinstance(digest, str) or not policy['HASH'].fullmatch(digest):
                                    raise ValueError('invalid historical scope SHA256')
                            review_context(historical)
                    def workers(value):
                        return {h['read_json'](bound(x['execution_receipt'])).get('worker_id') for x in value.get('reviews', {}).values() if x.get('execution_receipt')}
                    if workers(previous) & workers(reviews):
                        errors.append('CP3 cannot reuse a previous review worker/session')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append('reviews: ' + str(exc))

    for ref in plan.get('snapshots', []):
        try:
            result = module('snapshot')['verify_snapshot'](bound(ref))
            if result.get('status') not in ('PASS', 'VERIFIED'):
                errors.append('snapshot: ' + str(result.get('errors', result)))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append('snapshot: ' + str(exc))
    if phase == 'final':
        resolved_findings = [dict(x, item_id=x.get('item_id', x.get('id'))) for x in (record('data_audit_resolution', required=False) or {}).get('items', []) if x.get('status') == 'FINDING']
        declared_findings = [dict(x, item_id=x.get('item_id', x.get('id'))) for x in (audit or {}).get('items', []) if x.get('status') == 'FINDING']
        effect_policy = r3_policy(findings=resolved_findings + declared_findings, impacts=(grading or {}).get('finding_impacts', []))
        errors.extend(effect_policy['errors']); warnings.extend(effect_policy['warnings'])
        for impact in (grading or {}).get('finding_impacts', []):
            if not meaningful(impact.get('unmeasurable_reason')):
                known = (grading or {}).get('evaluator_hashes', {})
                if impact.get('grader_sha256') not in known.values():
                    errors.append('audit FINDING impact grader hash is not a retained current evaluator')
                else:
                    hashes(known, 'finding impact grader')
        comparison = record('baseline_comparison')
        comparison_error_start = len(errors)
        comparison_pending_start = len(pending)
        if comparison:
            if comparison.get('status') == 'UNAVAILABLE_WITH_REASON':
                if not meaningful(comparison.get('reason')):
                    errors.append('baseline comparison: unavailable needs a reason')
                pending.append('baseline comparison: no comparable score; no improvement claim or automatic freeze')
            elif comparison.get('status') == 'AVAILABLE':
                primary=dict(comparison)
                if isinstance(comparison.get('primary'),dict): primary.update(comparison['primary'])
                metric, direction = primary.get('metric'), primary.get('direction')
                left, right = primary.get('baseline_value'), primary.get('candidate_value')
                if not meaningful(metric) or direction not in ('HIGHER_IS_BETTER', 'LOWER_IS_BETTER') or any(type(x) not in (int, float) or not math.isfinite(x) for x in (left, right)):
                    errors.append('baseline comparison: finite comparable metric and direction required')
                else:
                    original, candidate = {}, {}
                    try:
                        original = h['read_json'](bound(comparison.get('baseline_evidence')))
                        candidate = h['read_json'](bound(comparison.get('candidate_evidence')))
                        scope = h['read_json'](bound(comparison.get('shared_scope_evidence')))
                        if not isinstance(scope, dict) or not scope or any(item.get('metric') != metric or item.get('scope') != scope or item.get('value') != expected for item, expected in ((original, left), (candidate, right))):
                            raise ValueError('both metric results must bind identical nonempty evaluation scope and recorded values')
                        bound(original.get('artifact')); bound(candidate.get('artifact'))
                        replay = record('clean_run', required=False) or {}
                        if not any(item.get('path') == candidate['artifact'].get('path') and item.get('sha256') == candidate['artifact'].get('sha256') for item in replay.get('artifacts', [])):
                            raise ValueError('candidate score must bind a current clean-run artifact')
                    except (OSError, ValueError, TypeError) as exc:
                        errors.append('baseline comparison evidence: ' + str(exc))
                    if comparison.get('selection') == 'CURRENT_BASELINE':
                        if right != left:
                            errors.append('current baseline selection must score the same as the baseline under identical evaluation')
                        if original.get('artifact', {}).get('sha256') != candidate.get('artifact', {}).get('sha256'):
                            errors.append('current baseline selection must preserve the evaluated baseline artifact')
                        pending.extend(r3_policy(assumptions=comparison.get('baseline_assumptions_check', []),keep_baseline=True)['pending'])
                    elif comparison.get('selection') != 'CANDIDATE':
                        errors.append('baseline comparison: selection must be CANDIDATE or CURRENT_BASELINE')
            else:
                pending.append('baseline comparison: availability and decision not recorded')

            policy = module('v27_comparison')['comparison_policy'](comparison)
            errors.extend(policy['errors']); pending.extend(policy['pending']); warnings.extend(policy['warnings'])
            errors.extend(r3_policy(gates=comparison.get('gates',[]))['errors'])
            alternative=comparison.get('best_alternative')
            if comparison.get('selection')=='CURRENT_BASELINE' and isinstance(alternative,dict):
                ref=alternative.get('evidence')
                if isinstance(ref,dict) and all(isinstance(ref.get(k),str) and ref[k].strip() for k in ('path','sha256')):
                    try:
                        path=h['safe_path'](root,ref['path'],must_exist=False)
                        if not path.is_file():
                            pending.append('best_alternative evidence file missing')
                        else:
                            observed=h['read_json'](bound(ref))
                            metrics=observed.get('metric_values',observed) if isinstance(observed,dict) else None
                            expected=alternative.get('metric_values')
                            if not isinstance(metrics,dict) or not isinstance(expected,dict) or any(k not in metrics or metrics[k]!=v for k,v in expected.items()):
                                raise ValueError('metric_values do not match result file')
                    except (OSError,ValueError,TypeError,AttributeError) as exc:
                        errors.append('best_alternative evidence: '+str(exc))
            for limit in comparison.get('hard_limits', []):
                try:
                    text = h['read_bytes'](bound(limit.get('evidence'))).decode('utf-8-sig')
                    if not meaningful(limit.get('source_quote')) or limit['source_quote'] not in text:
                        raise ValueError('hard limit source_quote must occur in task evidence')
                except (OSError, ValueError, TypeError, AttributeError) as exc:
                    errors.append('hard limit evidence: '+str(exc))
            for gate in comparison.get('gates', []):
                try:
                    observed = h['read_json'](bound(gate.get('evidence')))
                    expected_scope = h['read_json'](bound(comparison.get('shared_scope_evidence')))
                    if any(observed.get(k) != gate.get(k) for k in ('metric','baseline_value','candidate_value')) or observed.get('scope') != expected_scope:
                        raise ValueError('gate metric evidence does not match values and common evaluation scope')
                    baseline_score = h['read_json'](bound(comparison.get('baseline_evidence')))
                    candidate_score = h['read_json'](bound(comparison.get('candidate_evidence')))
                    if observed.get('baseline_artifact') != baseline_score.get('artifact') or observed.get('candidate_artifact') != candidate_score.get('artifact'):
                        raise ValueError('gate metric evidence must bind the same baseline and candidate artifacts')
                except (OSError, ValueError, TypeError, AttributeError) as exc:
                    errors.append('gate evidence: ' + str(exc))
        comparison_ok = bool(comparison and comparison.get('status') == 'AVAILABLE' and len(errors) == comparison_error_start and len(pending) == comparison_pending_start)

        requests = record('external_requests')
        if requests:
            if requests.get('status') not in ('NONE', 'TRACKED'):
                pending.append('external requests: explicit NONE or TRACKED status required')
            elif requests['status'] == 'TRACKED':
                entries = requests.get('requests')
                if not isinstance(entries, list) or not entries:
                    errors.append('external requests: tracked list required')
                else:
                    for item in entries:
                        if item.get('state') == 'RECEIVED':
                            try:
                                bound(item.get('response_evidence'))
                            except (OSError, ValueError, TypeError) as exc:
                                errors.append('external request response: ' + str(exc))
                        elif item.get('state') != 'PENDING':
                            pending.append('external request: state unresolved')

        maintenance = record('maintenance')
        if maintenance:
            runs = maintenance.get('runs', [])
            if not isinstance(runs, list) or len(runs) < 2:
                pending.append('maintenance: two actual change executions required')
            else:
                ids, configurations = set(), set()
                for run in runs:
                    try:
                        if not meaningful(run.get('id')) or run['id'] in ids or not meaningful(run.get('change')):
                            raise ValueError('distinct change and run id required')
                        ids.add(run['id'])
                        before = bound(run.get('before_config')); after = bound(run.get('after_config'))
                        if before.read_bytes() == after.read_bytes():
                            raise ValueError('changed configuration is identical to baseline')
                        if run['after_config']['sha256'] in configurations:
                            raise ValueError('maintenance scenarios must use distinct changed configurations')
                        configurations.add(run['after_config']['sha256'])
                        proof = h['read_json'](bound(run.get('execution')))
                        argv, output = native(proof)
                        product = bound(run.get('program'))
                        if path_index(argv, product) is None or path_index(argv, after) is None or output != h['read_json'](bound(run.get('observed_output'))):
                            raise ValueError('execution must bind program, changed configuration and observed JSON output')
                        if run.get('status') != 'PASS' or not meaningful(run.get('verification')):
                            raise ValueError('actual outcome and verification required')
                    except UnverifiedExecution as exc:
                        pending.append('maintenance: ' + str(exc))
                    except (OSError, ValueError, TypeError, KeyError) as exc:
                        errors.append('maintenance: ' + str(exc))
        for name, script, api, arg in (
                ('submission', 'submit_check', 'check_submission', 'submission_rules'),
                ('security', 'security_check', 'check_security', 'security_plan')):
            value = record(name)
            if value:
                try:
                    fresh = module(script)[api](root, plan.get(arg, {}))
                    if fresh != value or value.get('status') != 'PASS':
                        errors.append(name + ': current check is not the retained PASS result')
                    execution(name, value, script + '.py')
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    errors.append(name + ': ' + str(exc))
        replay = record('clean_run')
        if replay:
            if replay.get('status') != 'PASS' or replay.get('exit_code') != 0:
                errors.append('clean_run: successful actual replay required')
            hashes(replay.get('input_sha256'), 'clean_run original selected inputs')
            for artifact in replay.get('artifacts', []):
                try:
                    bound(artifact)
                except (OSError, ValueError, TypeError) as exc:
                    errors.append('clean_run output: ' + str(exc))
            if not replay.get('artifacts'):
                pending.append('clean_run: current final artifacts not bound')
            execution('clean_run', replay, 'clean_run.py')
        request_items = (requests or {}).get('requests', [])
        submission_verified = bool(comparison_ok and (records.get('submission') or {}).get('execution') and
            (records.get('clean_run') or {}).get('execution') and
            not any(x.startswith(('submission:', 'clean_run:')) for x in errors + pending))
        request_policy = r3_policy(requests=request_items, comparison_verified=submission_verified)
        errors.extend(request_policy['errors']); pending.extend(request_policy['pending']); warnings.extend(request_policy['warnings'])
    return dict(status='FAIL' if errors else 'UNVERIFIED' if pending else 'PASS', errors=errors, unverified=pending, warnings=warnings,
                notice='Retained local evidence only; no authenticated identity, official score, gate transition or submission receipt.')


def check(plan, root, kit, phase='final', source=None):
    try:
        return _check(plan, root, kit, phase, source)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as exc:
        return dict(status='FAIL', errors=['malformed or incomplete evidence: ' + str(exc)], unverified=[], warnings=[])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--root', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--phase', choices=('intake', 'cp1', 'final'), default='final')
    parser.add_argument('--plan', default='.hackathon-kit/run/V27_EVIDENCE.json')
    parser.add_argument('--output', type=Path, help='Also write the result JSON to this new file (an existing file is not overwritten)')
    args = parser.parse_args()
    try:
        h = module('v27_common')
        root = args.root or args.kit.absolute().parent
        result = check(h['read_json'](h['safe_path'](root, args.plan)), root, args.kit, args.phase, args.source)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = dict(status='FAIL', errors=[str(exc)], unverified=[], warnings=[])
    text = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)
    print(text)
    if args.output:
        try:
            with open(str(args.output), 'x', encoding='utf-8', newline='\n') as handle:
                handle.write(text + '\n')
        except OSError as exc:
            print('V27 CHECK OUTPUT NOT WRITTEN: ' + str(exc))
            return 2
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
