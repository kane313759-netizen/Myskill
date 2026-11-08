#!/usr/bin/env python3
"""Replay an explicitly authorized allowlist in a new local directory, without setup/network calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import threading
import time


def common():
    return runpy.run_path(str(Path(__file__).with_name('v27_common.py')), run_name='v27_clean_common')


def _equivalent(actual, expected, absolute, relative):
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        try:
            return math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual, expected, abs_tol=absolute, rel_tol=relative)
        except OverflowError:
            return actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return set(actual) == set(expected) and all(_equivalent(actual[k], expected[k], absolute, relative) for k in actual)
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(_equivalent(a, b, absolute, relative) for a, b in zip(actual, expected))
    return actual == expected


def clean_run(root, plan, scratch):
    helper = common()
    root = Path(root).absolute()
    scratch = Path(scratch).absolute()
    if not isinstance(plan, dict):
        raise ValueError('clean-run plan must be an object')
    if plan.get('execution_authorized') is not True or plan.get('network_allowed') is not False:
        raise ValueError('explicit execution_authorized=true and network_allowed=false are required')
    if plan.get('allow_setup', False) is not False:
        raise ValueError('automatic setup/dependency installation is not supported')
    timeout = plan.get('timeout_seconds')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError('timeout_seconds must be finite, positive and <=3600')
    command = plan.get('command')
    if not isinstance(command, list) or not command or not all(isinstance(v, str) and v for v in command):
        raise ValueError('command must be an explicit nonempty argv list')
    if any(token in command for token in ('-c', '--eval', '/c', '-Command', '-EncodedCommand')):
        raise ValueError('inline shell/eval commands are not a clean product replay')
    executable = sys.executable if command[0] == '{python}' else command[0]
    if Path(executable).resolve() != Path(sys.executable).resolve():
        allowed = plan.get('allowed_executables', [])
        if not isinstance(allowed, list) or executable not in allowed or not Path(executable).is_absolute():
            raise ValueError('non-Python executable needs an explicit absolute allowlist entry')
    if Path(executable).stem.lower() in {'sh', 'bash', 'cmd', 'powershell', 'pwsh', 'curl', 'wget', 'pip', 'npm'}:
        raise ValueError('shell, network and setup executables are not supported replay commands')
    sources, names, total = [], set(), 0
    for group in ('files', 'data_files'):
        selected = plan.get(group, [])
        if not isinstance(selected, list) or not all(isinstance(v, str) for v in selected):
            raise ValueError(group + ' must be an explicit relative file list')
        for name in selected:
            if Path(name).as_posix().lower() in ('.v27-stdout.log', '.v27-stderr.log'):
                raise ValueError('reserved replay log names cannot be inputs')
            source = helper['safe_path'](root, name)
            key = str(source.resolve())
            if key in names:
                raise ValueError('duplicate input file')
            names.add(key)
            content = helper['read_bytes'](source, 32 * 1024 * 1024)
            total += len(content)
            if total > 128 * 1024 * 1024 or len(sources) >= 2048:
                raise ValueError('clean replay copy budget exceeded')
            sources.append((name, content, group == 'data_files'))
    if not sources:
        raise ValueError('explicit product files are required')
    outputs = plan.get('outputs')
    if not isinstance(outputs, list) or not outputs or not all(isinstance(v, str) for v in outputs):
        raise ValueError('outputs must explicitly name generated files')
    if len(outputs) > 2048 or len(set(outputs)) != len(outputs) or any(Path(name).as_posix().lower() in ('.v27-stdout.log', '.v27-stderr.log') for name in outputs):
        raise ValueError('outputs must be unique and cannot use reserved log names')
    if not scratch.is_dir() or scratch.is_symlink():
        raise ValueError('scratch must be an existing authorized directory')
    for part in (scratch,) + tuple(scratch.parents):
        if part.is_symlink() or getattr(part.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('scratch cannot traverse links/reparse points')
    replay = Path(tempfile.mkdtemp(prefix='v27-clean-', dir=str(scratch)))
    try:
        source_hashes = {}
        for name, content, readonly in sources:
            target = helper['safe_path'](replay, name, must_exist=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            if readonly:
                target.chmod(0o444)
            source_hashes[name] = hashlib.sha256(content).hexdigest()
        for name in outputs:
            output = helper['safe_path'](replay, name, must_exist=False)
            if output.exists():
                raise ValueError('an output was copied as an input; replay must generate it')
        argv = [executable] + [value.replace('{python}', sys.executable) for value in command[1:]]
        if Path(executable).resolve() == Path(sys.executable).resolve():
            if '-I' not in argv[1:]:
                argv.insert(1, '-I')
            script_index = 1
            while script_index < len(argv) and argv[script_index] in ('-I', '-B', '-u', '-O', '-OO'):
                script_index += 1
            if script_index == len(argv) or argv[script_index].startswith('-'):
                raise ValueError('Python replay needs an allowlisted copied script, without inline/module execution')
            script = helper['safe_path'](replay, argv[script_index])
            if str(script.resolve()) not in {str(helper['safe_path'](replay, name).resolve()) for name, _, _ in sources}:
                raise ValueError('Python command script was not explicitly copied')
        expected_hashes = plan.get('expected_hashes', {})
        tolerances = plan.get('json_tolerances', {})
        if not isinstance(expected_hashes, dict) or not isinstance(tolerances, dict):
            raise ValueError('expected_hashes/json_tolerances must be objects')
        if not set(expected_hashes).union(tolerances).issubset(outputs):
            raise ValueError('comparison rules must name declared outputs')
        if any(not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value)
               for value in expected_hashes.values()):
            raise ValueError('expected_hashes requires lowercase SHA256 values')
        log_limit = plan.get('max_log_bytes', 1024 * 1024)
        if type(log_limit) is not int or not 0 < log_limit <= 16 * 1024 * 1024:
            raise ValueError('invalid max_log_bytes')
        start = time.monotonic()
        exceeded = threading.Event()
        try:
            # Drain both streams concurrently, retaining only the declared byte cap.
            stdout_path, stderr_path = replay / '.v27-stdout.log', replay / '.v27-stderr.log'
            process = subprocess.Popen(argv, cwd=str(replay), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            def drain(stream, destination):
                written = 0
                with destination.open('wb') as handle:
                    while True:
                        block = stream.read(65536)
                        if not block:
                            break
                        remaining = log_limit - written
                        handle.write(block[:remaining])
                        written += min(len(block), remaining)
                        if len(block) > remaining:
                            exceeded.set()
                            try:
                                process.kill()
                            except OSError:
                                pass
                            break
                stream.close()
            readers = [threading.Thread(target=drain, args=(stream, destination), daemon=True)
                       for stream, destination in ((process.stdout, stdout_path), (process.stderr, stderr_path))]
            for reader in readers:
                reader.start()
            exit_code = process.wait(timeout=timeout)
            for reader in readers:
                reader.join(timeout=1)
            if any(reader.is_alive() for reader in readers):
                exceeded.set()
            elapsed = time.monotonic() - start
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
            for reader in readers:
                reader.join(timeout=1)
            return {'status': 'FAIL', 'errors': ['replay timed out'], 'replay_dir': str(replay),
                    'command': argv, 'exit_code': process.returncode, 'input_sha256': source_hashes,
                    'elapsed_seconds': time.monotonic() - start,
                    'notice': 'Owned top-level process timed out; this is not OS isolation or descendant-process containment.'}
        errors = []
        if exit_code != 0:
            errors.append('product command exited %s' % exit_code)
        if exceeded.is_set():
            errors.append('replay log budget exceeded or output stream remained open')
        artifacts = []
        for name in outputs:
            try:
                output = helper['safe_path'](replay, name)
                content = helper['read_bytes'](output, 32 * 1024 * 1024)
                digest = hashlib.sha256(content).hexdigest()
                if name in expected_hashes and digest != expected_hashes[name]:
                    errors.append('deterministic output hash differs: ' + name)
                if name in tolerances:
                    compare = tolerances[name]
                    if not isinstance(compare, dict) or 'expected' not in compare:
                        raise ValueError('JSON tolerance requires explicit expected value')
                    absolute, relative = compare.get('abs', 0), compare.get('rel', 0)
                    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in (absolute, relative)):
                        raise ValueError('invalid JSON numeric tolerance')
                    actual = helper['read_json'](output)
                    if not _equivalent(actual, compare['expected'], absolute, relative):
                        errors.append('JSON output differs beyond declared tolerance: ' + name)
                artifacts.append({'path': name, 'bytes': len(content), 'sha256': digest})
            except (OSError, UnicodeError, ValueError, TypeError) as error:
                errors.append('%s: %s' % (name, error))
        submit = None
        if 'submission_rules' in plan:
            checker = runpy.run_path(str(Path(__file__).with_name('submit_check.py')), run_name='v27_clean_submit')
            submit = checker['check_submission'](replay, plan['submission_rules'])
            if submit['status'] != 'PASS':
                errors.append('declared submission checks failed')
        for name, _, readonly in sources:
            if readonly:
                try:
                    target = helper['safe_path'](replay, name)
                    if hashlib.sha256(helper['read_bytes'](target, 32 * 1024 * 1024)).hexdigest() != source_hashes[name]:
                        errors.append('copied input data changed: ' + name)
                except (OSError, ValueError):
                    errors.append('copied input data missing or no longer a bounded file: ' + name)
        return {'status': 'FAIL' if errors else 'PASS', 'errors': errors, 'replay_dir': str(replay),
                'command': argv, 'exit_code': exit_code, 'elapsed_seconds': elapsed,
                'input_sha256': source_hashes, 'artifacts': artifacts, 'submission_check': submit,
                'stdout_bytes': stdout_path.stat().st_size, 'stderr_bytes': stderr_path.stat().st_size,
                'notice': 'Authorized local replay only. No setup/network calls are made by this helper; the child is not OS-sandboxed and its supplied code must be inspected. No submission receipt or universal reproducibility proof.'}
    except Exception:
        # Preserve the owned replay for diagnosis; never delete original/source state.
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    helper = common()
    try:
        result = clean_run(args.root, helper['read_json'](args.plan), args.scratch)
        if args.output:
            helper['atomic_json'](args.output, result)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0 if result['status'] == 'PASS' else 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(json.dumps({'status': 'FAIL', 'errors': [str(error)]}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
