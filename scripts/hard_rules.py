#!/usr/bin/env python3
"""Hard-rule table checks (r4-3.16): void, zero-point and rejection conditions, and penalty limits.

The table lives at .hackathon-kit/run/HARD_RULES.json and is recorded in V27_EVIDENCE as `hard_rules`.
`check` validates it; `scan` lists every place a rule term appears so that every reading becomes a candidate.

Why: in practice runs a void rule's term had two readings in the materials and the team kept one
because a document said how a field is *recorded* or which document takes precedence, even after the
stakeholder had answered "not in the documents". Another team saw its own stress replay exceed a void
limit and filed it as a limitation. Elsewhere teams paid large penalty-limit costs for margin nobody asked for.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import unicodedata

HARD = ('VOID', 'ZERO', 'REJECT')
OTHER = ('PENALTY', 'SOFT')
DECISIONS = ('ALL_MEANINGS', 'OFFICIAL_ANSWER', 'SINGLE_MEANING', 'COST_EXCEPTION')
# Replies that hand the decision back to the team are not an official reading.
NOT_OFFICIAL = ('문서에 없음', '정해진 적이 없', '정해지지 않', '확인할 수 없', '알 수 없', '팀이 판단', '가정을 보고서',
                'not in the document', 'not documented', 'no official', 'not specified', 'unknown', 'your judgment', 'your judgement')
TEXT_SUFFIXES = ('.md', '.txt', '.json', '.yaml', '.yml', '.html', '.xml')
TABLE_SUFFIXES = ('.csv', '.tsv')
HEADER_LINES = 3  # header row plus a possible second header or unit row
OUTCOME_WORDS = ('무효', '0점', '영점 처리', '반려', '감점', '실격', '불합격', '인정하지 않', '탈락',
                 'is void', 'voided', 'zero points', 'scored zero', 'disqualif')
SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', 'site-packages', '__pycache__', '.tox', '.mypy_cache', '.pytest_cache'}
SKIP_PREFIXES = ('.hackathon-kit/', '.agents/', '.git/', '__pycache__/')
MAX_TEXT_BYTES = 8 * 1024 * 1024


def meaningful(value):
    return isinstance(value, str) and value.strip().upper() not in ('', 'UNKNOWN', 'TODO', 'NOT_RUN', 'N/A', 'NONE')


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and abs(value) != float('inf')


def _normal(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def _decode(data):
    """Task files may be UTF-8 (with or without BOM) or Korean legacy CP949; never fail on a stray byte."""
    for encoding in ('utf-8-sig', 'cp949'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode('utf-8', errors='replace')


def _read_text(path, head=None):
    with open(path, 'rb') as handle:
        data = handle.read() if head is None else handle.read(head)
    if head is not None and len(data) == head and b'\n' in data:
        data = data[:data.rindex(b'\n')]
    return _decode(data)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def _inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ValueError('path outside the task folder: ' + str(relative))
    return path


def default_bound(root):
    def bound(ref):
        if not isinstance(ref, dict) or not meaningful(ref.get('path')) or not meaningful(ref.get('sha256')):
            raise ValueError('evidence {path, sha256} required')
        path = _inside(root, ref['path'])
        if not path.is_file() or _sha256(path) != ref['sha256']:
            raise ValueError('stale or missing SHA256: ' + ref['path'])
        return path
    return bound


def _hard(rule, label, root, phase, bound):
    errors = []
    candidates = rule.get('candidates')
    if (not isinstance(candidates, list) or not candidates or
            any(not isinstance(c, dict) or not meaningful(c.get('meaning')) or not meaningful(c.get('source')) for c in candidates)):
        return [label + ': candidates need a meaning and a source for every reading of the rule term (use hard_rules.py scan)']
    meanings = [c['meaning'].strip() for c in candidates]
    if len(set(meanings)) != len(meanings):
        errors.append(label + ': candidate meanings must be distinct')
    if not meaningful(rule.get('term')):
        errors.append(label + ': term required (the word of the rule that decides what is checked)')
    decision = rule.get('decision')
    keep = set(meanings)
    if decision not in DECISIONS:
        return errors + [label + ': decision must be ALL_MEANINGS, OFFICIAL_ANSWER, SINGLE_MEANING or COST_EXCEPTION']
    if decision == 'SINGLE_MEANING':
        if len(meanings) > 1:
            errors.append(label + ': the term has more than one candidate meaning; keep every meaning (ALL_MEANINGS), '
                          'record an official answer, or justify a COST_EXCEPTION. A document that says how a field is '
                          'recorded, or which document takes precedence, does not decide what the rule refers to')
    elif decision == 'OFFICIAL_ANSWER':
        answer = rule.get('official_answer') if isinstance(rule.get('official_answer'), dict) else {}
        quote, source, chosen = answer.get('quote'), answer.get('source'), answer.get('meaning')
        if not meaningful(quote) or not meaningful(source) or chosen not in meanings:
            errors.append(label + ': an official answer needs its quote, its source file and the candidate meaning it names')
        elif any(marker.lower() in quote.lower() for marker in NOT_OFFICIAL):
            errors.append(label + ': a reply that leaves the reading to the team ("not in the documents") is not an official answer; keep every meaning')
        else:
            try:
                path = _inside(root, source)
                text = _read_text(path) if path.is_file() else ''
            except (OSError, ValueError) as exc:
                text = ''
                errors.append(label + ': official answer source: ' + str(exc))
            if text and _normal(quote) not in _normal(text):
                errors.append(label + ': official answer quote is not in its source file')
            elif not text and not any('official answer source' in e for e in errors):
                errors.append(label + ': official answer source file is missing or empty')
            keep = {chosen}
    elif decision == 'COST_EXCEPTION':
        exception = rule.get('exception') if isinstance(rule.get('exception'), dict) else {}
        kept = exception.get('meanings_kept')
        loss_all, loss_wrong, chance = exception.get('loss_all_meanings'), exception.get('loss_if_wrong'), exception.get('probability_wrong')
        if (not isinstance(kept, list) or not kept or any(k not in meanings for k in kept) or not number(loss_all) or not number(loss_wrong)
                or not number(chance) or not 0 < chance <= 1 or loss_all <= 0 or loss_wrong < 0 or not meaningful(exception.get('basis'))):
            errors.append(label + ': a cost exception needs meanings_kept, loss_all_meanings > 0, loss_if_wrong >= 0, '
                          'probability_wrong in (0, 1] and a basis, all in the task\'s own score or cost units')
        else:
            if loss_all <= chance * loss_wrong:
                errors.append(label + ': keeping every meaning costs less than the expected loss of a wrong guess; keep every meaning')
            keep = set(kept)
    if phase == 'final':
        checks = rule.get('checks')
        if not isinstance(checks, list) or not checks:
            errors.append(label + ': final needs the team\'s own check of every kept meaning (public replay and every stress scenario run)')
            return errors
        covered = set()
        for item in checks:
            if (not isinstance(item, dict) or item.get('meaning') not in meanings or not meaningful(item.get('scenario'))
                    or type(item.get('violations')) is not int or item['violations'] < 0):
                errors.append(label + ': each check needs a candidate meaning, a scenario and an integer violation count')
                continue
            try:
                bound(item.get('evidence'))
            except (OSError, ValueError, TypeError) as exc:
                errors.append(label + ': check evidence: ' + str(exc))
            if item['violations']:
                errors.append('%s: own check finds %d violation(s) of "%s" in %s; a hard-rule violation in the team\'s own replay '
                              'or stress scenario must be fixed (margin or plan) before submission, not recorded as a limitation'
                              % (label, item['violations'], item['meaning'], item['scenario']))
            covered.add(item['meaning'])
        missing = sorted(keep - covered)
        if missing:
            errors.append(label + ': final has no own check for kept meaning(s): ' + ', '.join(missing))
    return errors


def _penalty(rule, label, phase):
    if phase != 'final':
        return []
    tradeoff = rule.get('tradeoff') if isinstance(rule.get('tradeoff'), dict) else None
    alternatives = (tradeoff or {}).get('alternatives')
    if (not tradeoff or not meaningful(tradeoff.get('chosen')) or not number(tradeoff.get('chosen_expected_loss'))
            or not isinstance(alternatives, list) or not alternatives
            or any(not isinstance(a, dict) or not meaningful(a.get('label')) or not number(a.get('expected_loss')) for a in alternatives)):
        return [label + ': a penalty limit needs its chosen setting compared with at least one alternative by expected loss '
                '(points or cost); a margin on a penalty limit is paid for, not free']
    best = min(a['expected_loss'] for a in alternatives)
    if tradeoff['chosen_expected_loss'] > best + 1e-9 and not meaningful(tradeoff.get('reason')):
        return [label + ': an alternative has a lower expected loss; choose it or give the reason']
    return []


def validate(doc, root, phase='cp1', bound=None):
    """Errors for the hard-rule table at `phase` ('cp1' or 'final')."""
    bound = bound or default_bound(root)
    if not isinstance(doc, dict) or doc.get('version') != 1 or not isinstance(doc.get('rules'), list):
        return ['hard_rules: version 1 object with a rules list required']
    rules = doc['rules']
    if not rules:
        if not meaningful(doc.get('no_hard_rules_reason')):
            return ['hard_rules: list every void, zero-point, rejection and penalty rule, or give no_hard_rules_reason']
        found = scan(root, OUTCOME_WORDS, limit=5)['hits'] if root is not None else []
        if found:
            shown = '; '.join('%s:%s "%s"' % (hit['file'], hit['at'], hit['text'][:80]) for hit in found[:3])
            return ['hard_rules: the table is empty but the materials state outcome words (%s); add each as a rule '
                    '(SOFT if it does not decide this task\'s score or acceptance)' % shown]
        return []
    errors, ids = [], set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append('hard_rules %d: rule object required' % index)
            continue
        label = 'hard_rules ' + (rule['id'] if meaningful(rule.get('id')) else str(index))
        if not meaningful(rule.get('id')) or rule.get('id') in ids:
            errors.append(label + ': unique id required')
        ids.add(rule.get('id'))
        for key in ('rule', 'source'):
            if not meaningful(rule.get(key)):
                errors.append(label + ': ' + key + ' required')
        consequence = rule.get('consequence')
        if consequence in HARD:
            errors.extend(_hard(rule, label, root, phase, bound))
        elif consequence == 'PENALTY':
            errors.extend(_penalty(rule, label, phase))
        elif consequence != 'SOFT':
            errors.append(label + ': consequence must be VOID, ZERO, REJECT, PENALTY or SOFT')
    return errors


def _xlsx_rows(path, rows=6):
    try:
        import openpyxl  # optional
    except ImportError:
        return []
    out = []
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for sheet in book.worksheets:
            for number_, row in enumerate(sheet.iter_rows(max_row=rows, values_only=True), 1):
                cells = [str(v) for v in row if v is not None]
                if cells:
                    out.append(('%s!%d' % (sheet.title, number_), ' | '.join(cells)))
    finally:
        book.close()
    return out


def _files(root):
    """Task files in a stable order; the kit, agent skills, VCS data, environments and licence texts are skipped."""
    found = []
    for folder, dirs, files in os.walk(str(root)):
        base = Path(folder)
        rel_dir = base.relative_to(root).as_posix()
        prefix = '' if rel_dir == '.' else rel_dir + '/'
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and (prefix + d + '/') not in SKIP_PREFIXES
                         and not (base / d).is_symlink())
        for name in files:
            path = base / name
            if name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE')) or path.is_symlink() or not path.is_file():
                continue
            found.append(path)
    return sorted(found)


def scan(root, terms, limit=300):
    """Every line (text), header row (CSV/TSV) or top rows (XLSX) that contains a term."""
    root = Path(root).resolve()
    hits, truncated = [], False
    terms = [unicodedata.normalize('NFC', term) for term in terms if term]
    for path in _files(root):
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        try:
            if suffix in TABLE_SUFFIXES:
                lines = [(str(n), line) for n, line in enumerate(_read_text(path, 1 << 16).splitlines()[:HEADER_LINES], 1)]
            elif suffix in TEXT_SUFFIXES:
                if path.stat().st_size > MAX_TEXT_BYTES:
                    continue
                lines = [(str(n), line) for n, line in enumerate(_read_text(path).splitlines(), 1)]
            elif suffix == '.xlsx':
                lines = _xlsx_rows(path)
            else:
                continue
        except (OSError, ValueError, KeyError):
            continue
        for where, line in lines:
            line = unicodedata.normalize('NFC', line)
            for term in terms:
                if term and term in line:
                    hits.append(dict(term=term, file=rel, at=where, text=' '.join(line.split())[:240]))
                    if len(hits) >= limit:
                        return dict(hits=hits, truncated=True)
    return dict(hits=hits, truncated=truncated)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    check_p = sub.add_parser('check', help='validate the hard-rule table')
    check_p.add_argument('--root', type=Path, required=True, help='task folder (paths in the table are relative to it)')
    check_p.add_argument('--file', default='.hackathon-kit/run/HARD_RULES.json')
    check_p.add_argument('--phase', choices=('cp1', 'final'), default='cp1')
    scan_p = sub.add_parser('scan', help='list every place a rule term appears')
    scan_p.add_argument('--root', type=Path, required=True)
    scan_p.add_argument('--term', action='append', required=True)
    scan_p.add_argument('--limit', type=int, default=300)
    args = parser.parse_args(argv)
    if args.command == 'scan':
        print(json.dumps(scan(args.root, args.term, args.limit), ensure_ascii=False, indent=1))
        return 0
    try:
        doc = json.loads(_inside(args.root, args.file).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        print(json.dumps(dict(status='FAIL', errors=['hard_rules: ' + str(exc)]), ensure_ascii=False))
        return 1
    errors = validate(doc, args.root, args.phase)
    print(json.dumps(dict(status='FAIL' if errors else 'PASS', errors=errors), ensure_ascii=False, indent=1))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
