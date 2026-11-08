#!/usr/bin/env python3
"""Bounded static triage of an explicit product-file allowlist, without disclosure of values."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import runpy


def common():
    return runpy.run_path(str(Path(__file__).with_name('v27_common.py')), run_name='v27_security_common')


def _call_name(node, aliases):
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return _call_name(node.value, aliases) + '.' + node.attr
    return ''


def _python_findings(text):
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return [(error.lineno or 1, 'python_parse_error')]
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split('.')[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = node.module + '.' + alias.name
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func, aliases)
        if name in ('eval', 'exec', 'builtins.eval', 'builtins.exec'):
            findings.append((node.lineno, 'dynamic_code_execution'))
        elif name in ('pickle.load', 'pickle.loads', 'dill.load', 'dill.loads'):
            findings.append((node.lineno, 'untrusted_deserialization_review'))
        elif name in ('os.system', 'os.popen', 'subprocess.getoutput', 'subprocess.getstatusoutput'):
            findings.append((node.lineno, 'shell_execution'))
        elif name.startswith('subprocess.') and any(
                kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in node.keywords):
            findings.append((node.lineno, 'subprocess_shell_true'))
    return findings


def check_security(root, plan):
    helper = common()
    if not isinstance(plan, dict) or not isinstance(plan.get('files'), list) or not plan['files']:
        raise ValueError('an explicit nonempty product file allowlist is required')
    if len(plan['files']) > 128:
        raise ValueError('file count exceeds static scan budget')
    limit = plan.get('max_file_bytes', 1024 * 1024)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 0 < limit <= 16 * 1024 * 1024:
        raise ValueError('invalid max_file_bytes')
    dispositions = plan.get('dispositions', [])
    if not isinstance(dispositions, list):
        raise ValueError('dispositions must be a list')
    approved = {}
    for item in dispositions:
        if not isinstance(item, dict) or not all(item.get(k) for k in ('path', 'line', 'category', 'reason', 'evidence')):
            raise ValueError('a disposition requires path, line, category, reason and evidence')
        approved[(item['path'], item['line'], item['category'])] = {
            'reason': str(item['reason']), 'evidence': str(item['evidence'])}
    patterns = [
        ('secret_token', re.compile(r'\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b')),
        ('private_key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
        ('personal_id', re.compile(r'(?<!\d)\d{6}[- ]?[1-8]\d{6}(?!\d)')),
    ]
    assignment = re.compile(r'''(?i)\b[A-Za-z_]*(?:password|passwd|api_?key|access_token|client_secret|secret_key)\b["']?\s*[:=]\s*["']([^"'\r\n]{8,})["']''')
    placeholders = {'placeholder', 'changeme', 'your_api_key', 'your_password', 'example', 'redacted'}
    findings, artifacts, errors, seen, total = [], [], [], set(), 0
    for name in plan['files']:
        try:
            path = helper['safe_path'](root, name)
            if str(path.resolve()) in seen:
                raise ValueError('duplicate allowlist path')
            seen.add(str(path.resolve()))
            content = helper['read_bytes'](path, limit)
            total += len(content)
            if total > 32 * 1024 * 1024:
                raise ValueError('total static scan budget exceeded')
            text = content.decode(plan.get('encoding', 'utf-8-sig'))
            locations = set()
            for category, pattern in patterns:
                for match in pattern.finditer(text):
                    locations.add((text.count('\n', 0, match.start()) + 1, category))
            for match in assignment.finditer(text):
                value = match.group(1)
                if value.lower() not in placeholders and not value.startswith(('${', '<')):
                    locations.add((text.count('\n', 0, match.start()) + 1, 'hardcoded_credential_review'))
            if path.suffix.lower() == '.py':
                locations.update(_python_findings(text))
            for line, category in sorted(locations):
                disposition = approved.pop((name, line, category), None)
                finding = {'path': name, 'line': line, 'category': category,
                           'status': 'DISPOSITIONED' if disposition else 'UNRESOLVED'}
                # Do not copy matched values or source lines into evidence.
                if disposition:
                    finding['disposition'] = disposition
                findings.append(finding)
            artifacts.append({'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            errors.append({'path': name, 'error': str(error)})
    if approved:
        errors.append({'error': 'dispositions did not match findings in the declared scope'})
    unresolved = sum(item['status'] == 'UNRESOLVED' for item in findings)
    return {'status': 'FAIL' if errors or unresolved else 'PASS', 'findings': findings,
            'unresolved_count': unresolved, 'errors': errors, 'artifacts': artifacts,
            'notice': 'Static triage of the declared product files only. No matched values are printed. PASS means no unresolved findings in this scan; it is not security certification or dynamic exploit testing.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    helper = common()
    try:
        result = check_security(args.root, helper['read_json'](args.plan))
        if args.output:
            helper['atomic_json'](args.output, result)
        print(json.dumps(result, ensure_ascii=True))
        return 0 if result['status'] == 'PASS' else 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'status': 'FAIL', 'errors': [str(error)]}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
