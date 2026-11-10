#!/usr/bin/env python3
"""Hard-rule table checks (r4-3.16, r4-3.17): void, zero-point and rejection conditions, penalty limits,
two-sided targets, simple baselines and the search for the optimum.

The table lives at .hackathon-kit/run/HARD_RULES.json and is recorded in V27_EVIDENCE as `hard_rules`.
CP1 fixes what will be measured and how; the copy the CP1 review saw is recorded as `hard_rules_cp1`, and
final may only add results and widen (more meanings, more stress, more baselines), never narrow the plan.
`check` validates the table; `scan` lists every place a term appears in the task materials.

Why: in practice runs a void rule's term had two readings and the team kept one because a document said how
a field is *recorded* or which document takes precedence, even after the stakeholder had answered "not in
the documents"; a team filed its own stress violation of a void limit as a limitation; teams paid large
penalty-limit costs for margin nobody asked for; hidden evaluations broke numeric limits that the team's own
replay passed (a stress set no harsher than the public data, a point estimate, an estimator that explained
none of the known real cases); a 90% interval target was overshot to 100%; and tuned policies lost to the
current or a pooled rule on later data because they were judged on the period they were tuned on.
"""
import argparse
import datetime
import gzip
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
import zipfile

HARD = ('VOID', 'ZERO', 'REJECT')
CONSEQUENCES = HARD + ('PENALTY', 'TARGET', 'SOFT')
DECISIONS = ('ALL_MEANINGS', 'OFFICIAL_ANSWER', 'SINGLE_MEANING', 'COST_EXCEPTION')
STRESS_TYPES = ('demand_up', 'capacity_down', 'timing_shift', 'mix_shift', 'data_noise', 'other')
BASELINE_KINDS = ('current', 'uniform', 'pooled', 'no_action', 'other')
METRIC_SOURCES = ('evaluator', 'simulator', 'estimated')
MIN_CASES = 5        # fewer known real cases cannot validate an estimator that certifies a void limit
MIN_EXPLAINED = 0.5  # the estimator must explain at least half of them
OPT_GAP = 0.01       # within 1% of a proven bound counts as optimal
PLATEAU_ROUNDS = 2   # otherwise the last two rounds, near the best, must each gain less than min_gain
TOLERANCE_SHARE = 0.05  # a two-sided tolerance wider than 5% of the target needs a quote from the task
# Replies that hand the decision back to the team are not an official reading.
NOT_OFFICIAL = ('문서에 없', '정해진 적이 없', '정해지지 않', '확인할 수 없', '알 수 없', '팀이 판단', '판단에 맡', '재량',
                '가정을 보고서', '특정되지 않', '명시되지 않', '규정되지 않', '정의되지 않', '답할 수 없',
                'not in the document', 'not documented', 'no official', 'not specified', 'not defined', 'unknown',
                'your judgment', 'your judgement', 'up to you', 'your discretion', 'cannot answer')
OUTCOME_WORDS = ('무효', '0점', '영점', '반려', '감점', '실격', '불합격', '인정하지 않', '탈락', '불통과',
                 'void', 'zero points', 'scored zero', 'disqualif', 'rejected', 'penalty')
TARGET_WORDS = ('포함률', '구간 포함', '커버리지', '신뢰구간', '예측구간', '예측 구간', 'coverage', 'calibration')
NUMERIC_RULE = re.compile(r'\d[\d,.]*\s*(?:[을를이가은는]\s*)?(%|퍼센트|ppm|dppm|건|개|회|분|시간|일|kw|kwh|mw|℃|도|원|만원|초과|이상|이하|미만|넘|over|above|below|exceed)', re.I)
ISO_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$')
TEXT_SUFFIXES = ('.md', '.txt', '.json', '.jsonl', '.yaml', '.yml', '.html', '.htm', '.xml', '.py', '.ini', '.cfg', '.toml')
TABLE_SUFFIXES = ('.csv', '.tsv')
ZIP_SUFFIXES = {'.xlsx': ('xl/sharedStrings.xml', 'xl/worksheets/'), '.xlsm': ('xl/sharedStrings.xml', 'xl/worksheets/'),
                '.docx': ('word/document.xml', 'word/header', 'word/footer', 'word/footnotes.xml'),
                '.pptx': ('ppt/slides/', 'ppt/notesSlides/'), '.hwpx': ('Contents/section',)}
UNSCANNED_SUFFIXES = ('.pdf', '.doc', '.xls', '.ppt', '.hwp', '.rtf', '.odt', '.ods', '.odp')
HEADER_LINES = 3  # header row plus a possible second header or unit row
SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', 'site-packages', '__pycache__', '.tox', '.mypy_cache', '.pytest_cache'}
SKIP_PREFIXES = ('.hackathon-kit/', '.agents/', '.git/', '__pycache__/')
MAX_TEXT_BYTES = 8 * 1024 * 1024
PARAGRAPH_END = re.compile(r'</(?:w:p|a:p|si|hp:p|c|row)>')


def _rel(path):
    text = str(path).replace('\\', '/')
    while text.startswith('./'):
        text = text[2:]
    return text


TEAM_PREFIXES = ('.hackathon-kit', '.agents', 'run/', 'submission')


def _dicts(values):
    return [v for v in values if isinstance(v, dict)] if isinstance(values, list) else []


def _strings(values):
    return [v for v in values if isinstance(v, str)] if isinstance(values, list) else []


def meaningful(value):
    return isinstance(value, str) and value.strip().upper() not in ('', 'UNKNOWN', 'TODO', 'NOT_RUN', 'N/A', 'NONE', '없음', '-')


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


def _evidence(bound, ref, label, expected):
    """The evidence file is current and states the same numbers the table states."""
    try:
        path = bound(ref)
        data = json.loads(_read_text(path))
    except (OSError, ValueError, TypeError) as exc:
        return [label + ': evidence: ' + str(exc)]
    if not isinstance(data, dict):
        return [label + ': evidence must be a JSON object holding the recorded numbers']
    wrong = [key for key, value in expected.items() if data.get(key) != value]
    if wrong:
        return [label + ': evidence file does not state the recorded ' + ', '.join(wrong)]
    return []


# --- scanning the task materials ---------------------------------------------------------------------------

def _files(root, paths):
    """Task material files in a stable order; the kit, agent skills, VCS data, environments and licences are skipped."""
    root = Path(root).resolve()
    found = set()
    for item in paths:
        start = _inside(root, item)
        if start.is_file():
            found.add(start)
            continue
        for folder, dirs, files in os.walk(str(start)):
            base = Path(folder)
            rel_dir = base.relative_to(root).as_posix()
            prefix = '' if rel_dir == '.' else rel_dir + '/'
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (prefix + d + '/').startswith(SKIP_PREFIXES)
                             and not (base / d).is_symlink())
            for name in files:
                path = base / name
                if name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE')) or path.is_symlink() or not path.is_file():
                    continue
                found.add(path)
    return sorted(p for p in found if not p.relative_to(root).as_posix().startswith(SKIP_PREFIXES))


def _zip_lines(path, parts):
    out = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.filename.endswith('.xml') or not info.filename.startswith(parts) or info.file_size > MAX_TEXT_BYTES:
                continue
            text = archive.read(info).decode('utf-8', errors='replace')
            for number_, chunk in enumerate(PARAGRAPH_END.split(text), 1):
                line = html.unescape(re.sub(r'<[^>]+>', ' ', chunk))
                if line.strip():
                    out.append(('%s#%d' % (info.filename, number_), line))
    return out


def _lines(path):
    """(location, text) pairs to search; raises on unreadable files."""
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name.endswith(('.csv.gz', '.tsv.gz')):
        with gzip.open(str(path), 'rb') as handle:
            data = handle.read(1 << 16)
        return [(str(n), line) for n, line in enumerate(_decode(data).splitlines()[:HEADER_LINES], 1)]
    if suffix in TABLE_SUFFIXES:
        return [(str(n), line) for n, line in enumerate(_read_text(path, 1 << 16).splitlines()[:HEADER_LINES], 1)]
    if suffix in TEXT_SUFFIXES:
        if path.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError('text file larger than %d bytes' % MAX_TEXT_BYTES)
        return [(str(n), line) for n, line in enumerate(_read_text(path).splitlines(), 1)]
    if suffix in ZIP_SUFFIXES:
        return _zip_lines(path, ZIP_SUFFIXES[suffix])
    return None


def _matches(line, term):
    """Case-insensitive; a term that starts with a digit or a Latin letter must not continue a longer word ('10점' is not '0점')."""
    folded, key = line.casefold(), term.casefold()
    start = folded.find(key)
    while start >= 0:
        before = folded[start - 1] if start else ' '
        if not (key[0].isascii() and key[0].isalnum() and before.isascii() and (before.isalnum() or before in '.,')):
            return True
        start = folded.find(key, start + 1)
    return False


def scan(root, terms, limit=300, paths=('.',)):
    """Every line (text, docx, pptx, hwpx), header rows (CSV/TSV) and cell text (XLSX) containing a term.

    `skipped` lists document files that could not be read (PDF, legacy Office, broken archives) so a person or
    reviewer opens them instead of the scan passing silently.
    """
    root = Path(root).resolve()
    terms = [unicodedata.normalize('NFC', term) for term in terms if term]
    hits, skipped, truncated = [], [], False
    for path in _files(root, paths):
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in UNSCANNED_SUFFIXES:
            skipped.append(dict(file=rel, reason='format not readable by the scan'))
            continue
        try:
            lines = _lines(path)
        except Exception as exc:  # broken workbooks, zip or gzip files must not stop the scan
            skipped.append(dict(file=rel, reason='%s: %s' % (type(exc).__name__, exc)))
            continue
        if lines is None:
            continue
        for where, line in lines:
            line = unicodedata.normalize('NFC', line)
            for term in terms:
                if _matches(line, term):
                    hits.append(dict(term=term, file=rel, at=where, key='%s:%s' % (rel, where), text=' '.join(line.split())[:240]))
                    if len(hits) >= limit:
                        return dict(hits=hits, skipped=skipped, truncated=True)
                    break
    return dict(hits=hits, skipped=skipped, truncated=truncated)


def _materials(doc, root, phase):
    paths = doc.get('materials')
    if not isinstance(paths, list) or not paths or any(not meaningful(p) for p in paths):
        return None, ['hard_rules: materials must list the task files and folders given by the organisers (e.g. README.md, docs/, data/)']
    errors = []
    for item in paths:
        try:
            if not _inside(root, item).exists():
                errors.append('hard_rules: material %s does not exist' % item)
        except ValueError as exc:
            errors.append('hard_rules: material ' + str(exc))
        if _rel(item).startswith(TEAM_PREFIXES):
            errors.append('hard_rules: material %s is team output, not task material' % item)
    return (paths if not errors else None), errors


CITE_BEFORE = r'(?:^|(?<=[\s,;(\[<"\']))'


def _cites(text, hit):
    """True when `text` names the hit as `file:line` (file names may contain spaces; `file:3-7` names lines 3 to 7)."""
    if not isinstance(text, str):
        return False
    text = text.replace('\\', '/')
    if hit['at'].isdigit():
        line = int(hit['at'])
        for match in re.finditer(CITE_BEFORE + r'(?:\./)*' + re.escape(hit['file']) + r':(\d+)(?:-(\d+))?(?![0-9A-Za-z])', text):
            first = int(match.group(1))
            last = int(match.group(2)) if match.group(2) else first
            if first <= line <= last <= first + 500:
                return True
        return False
    return re.search(CITE_BEFORE + r'(?:\./)*' + re.escape(hit['key']) + r'(?![0-9A-Za-z])', text) is not None


def _coverage(doc, root, paths):
    """Every outcome or target sentence in the materials is accounted for by a rule or a not_rules entry."""
    errors = []
    found = scan(root, OUTCOME_WORDS + TARGET_WORDS, limit=2000, paths=paths)
    cited = [text for rule in _dicts(doc.get('rules')) for text in [rule.get('source')] + _strings(rule.get('sources')) if isinstance(text, str)]
    notes = {item.get('at') for item in _dicts(doc.get('not_rules')) if isinstance(item.get('at'), str) and meaningful(item.get('why'))}
    open_hits = [hit for hit in found['hits'] if hit['key'] not in notes and not any(_cites(text, hit) for text in cited)]
    if open_hits:
        shown = '; '.join('%s "%s"' % (hit['key'], hit['text'][:70]) for hit in open_hits[:5])
        errors.append('hard_rules: %d outcome or target sentence(s) in the materials are not in the table (%s%s); add a rule '
                      'whose source names file:line (TARGET for coverage or calibration targets, SOFT if it decides no score '
                      'or acceptance) or list it in not_rules {at, why}' % (len(open_hits), shown, ' ...' if len(open_hits) > 5 else ''))
    reviewed = {item.get('file') for item in _dicts(doc.get('unscanned_reviewed')) if isinstance(item.get('file'), str) and meaningful(item.get('note'))}
    for item in found['skipped']:
        if item['file'] not in reviewed:
            errors.append('hard_rules: %s could not be scanned (%s); open it and record what it says about outcome rules in '
                          'unscanned_reviewed {file, note}' % (item['file'], item['reason']))
    return errors


# --- void, zero-point and rejection rules ------------------------------------------------------------------

def _answer_sources(doc, bound):
    refs = doc.get('answer_sources')
    if not isinstance(refs, list) or not refs:
        return set(), ['hard_rules: OFFICIAL_ANSWER needs answer_sources [{path, sha256}]: the files that hold the replies of the organisers or stakeholders']
    allowed, errors = set(), []
    for ref in refs:
        path = _rel((ref or {}).get('path', '')) if isinstance(ref, dict) else ''
        if path.startswith(TEAM_PREFIXES) or 'HARD_RULES' in path or 'SPEC_DRAFT' in path:
            errors.append('hard_rules: answer source %s is a team file; only recorded replies of the organisers count' % path)
            continue
        try:
            bound(ref)
            allowed.add(path)
        except (OSError, ValueError, TypeError) as exc:
            errors.append('hard_rules: answer source: ' + str(exc))
    return allowed, errors


def _hard(rule, label, root, phase, bound, context):
    errors = []
    candidates = rule.get('candidates')
    if (not isinstance(candidates, list) or not candidates or
            any(not isinstance(c, dict) or not meaningful(c.get('meaning')) or not meaningful(c.get('source')) for c in candidates)):
        return [label + ': candidates need a meaning and a source for every reading of the rule term (use hard_rules.py scan)']
    meanings = [c['meaning'].strip() for c in candidates]
    if len(set(meanings)) != len(meanings):
        errors.append(label + ': candidate meanings must be distinct')
    term = rule.get('term')
    if not meaningful(term):
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
        elif meaningful(term) and context.get('paths'):
            count = len(scan(root, [term], limit=2000, paths=context['paths'])['hits'])
            if rule.get('scan_hits') != count:
                errors.append('%s: SINGLE_MEANING needs scan_hits equal to the scan of "%s" over the materials (%d); read every '
                              'hit before claiming one reading' % (label, term, count))
    elif decision == 'OFFICIAL_ANSWER':
        answer = rule.get('official_answer') if isinstance(rule.get('official_answer'), dict) else {}
        quote, source, chosen = answer.get('quote'), _rel(answer.get('source', '')), answer.get('meaning')
        if not meaningful(quote) or not meaningful(source) or chosen not in meanings:
            errors.append(label + ': an official answer needs its quote, its source file and the candidate meaning it names')
        elif any(marker.casefold() in quote.casefold() for marker in NOT_OFFICIAL):
            errors.append(label + ': a reply that leaves the reading to the team ("not in the documents") is not an official answer; keep every meaning')
        elif meaningful(term) and _normal(term).casefold() not in _normal(quote).casefold():
            errors.append(label + ': the official answer quote must name the rule term "%s" and settle its reading' % term)
        else:
            allowed, source_errors = _answer_sources(context['doc'], bound)
            errors.extend(source_errors)
            if not source_errors and source not in allowed:
                errors.append(label + ': official answer source must be one of answer_sources (recorded replies), not a team file')
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
    errors.extend(_limit_plan(rule, label))
    if phase == 'final':
        checks = rule.get('checks')
        if not isinstance(checks, list) or not checks:
            errors.append(label + ': final needs the team\'s own check of every kept meaning (public replay and every stress scenario run)')
            return errors
        covered = set()
        numeric = rule.get('limit') is not None
        for item in checks:
            if (not isinstance(item, dict) or item.get('meaning') not in meanings or not meaningful(item.get('scenario'))
                    or type(item.get('violations')) is not int or item['violations'] < 0):
                errors.append(label + ': each check needs a candidate meaning, a scenario and an integer violation count')
                continue
            expected = {'violations': item['violations']}
            if numeric and number(item.get('value')):
                expected['value'] = item['value']
            errors.extend(_evidence(bound, item.get('evidence'), '%s: check "%s"' % (label, item['scenario']), expected))
            if item['violations'] and item['meaning'] in keep:
                errors.append('%s: own check finds %d violation(s) of "%s" in %s; a hard-rule violation in the team\'s own replay '
                              'or stress scenario must be fixed (margin or plan) before submission, not recorded as a limitation'
                              % (label, item['violations'], item['meaning'], item['scenario']))
            covered.add(item['meaning'])
        missing = sorted(keep - covered)
        if missing:
            errors.append(label + ': final has no own check for kept meaning(s): ' + ', '.join(missing))
        if numeric:
            errors.extend(_limit(rule, label, [c for c in checks if isinstance(c, dict) and c.get('meaning') in keep], keep))
    return errors


def _limit_plan(rule, label):
    """CP1: a numeric void limit is declared with its unit and statistic, how it is measured and how it will be stressed."""
    if rule.get('limit') is None:
        if not meaningful(rule.get('no_numeric_limit_reason')):
            return [label + ': give the numeric limit (limit, direction, unit) or no_numeric_limit_reason']
        text = str(rule.get('rule', ''))
        match = NUMERIC_RULE.search(text)
        if match:
            return ['%s: the rule text states a numeric threshold ("%s"); record limit, direction and unit' % (label, match.group(0))]
        return []
    errors = []
    if not number(rule.get('limit')) or rule.get('direction') not in ('max', 'min') or type(rule.get('inclusive')) is not bool:
        errors.append(label + ': limit must be a number, direction "max" or "min" and inclusive true/false (is a value equal '
                      'to the limit allowed? "0.1 이상이면 무효" means max 0.1, inclusive false)')
    for key, what in (('unit', 'the unit of the limit as the task states it (%, DPPM, count, hours)'),
                      ('statistic', 'what is compared with the limit (each unit, mean, maximum, 95th percentile, per week)')):
        if not meaningful(rule.get(key)):
            errors.append('%s: %s required: %s' % (label, key, what))
    plan = rule.get('stress_plan')
    if not isinstance(plan, list) or any(not isinstance(item, str) or item not in STRESS_TYPES for item in plan) or len(set(plan)) < 2:
        errors.append(label + ': stress_plan must name at least two different stress types (%s) at CP1' % ', '.join(STRESS_TYPES))
    source = rule.get('metric_source')
    if type(rule.get('uses_model')) is not bool:
        errors.append(label + ': uses_model (true/false) required: is any statistical, ML or fitted model part of measuring this metric?')
    if source not in METRIC_SOURCES:
        errors.append(label + ': metric_source must be evaluator (given scorer), simulator (team replay of the stated rules) or estimated (model of an unseen quantity)')
    elif rule.get('uses_model') is True and source != 'estimated':
        errors.append(label + ': a metric measured with a fitted model is an estimate; metric_source must be estimated')
    elif source == 'estimated':
        cases = rule.get('known_real_cases')
        if type(cases) is not int or cases < 0 or not meaningful(rule.get('explained_definition')):
            errors.append(label + ': an estimated metric needs known_real_cases and explained_definition (what counts as explaining a real case) at CP1')
        elif cases < MIN_CASES:
            errors.append('%s: only %d known real case(s) can check the estimator (fewer than %d); an estimate cannot certify this '
                          'void limit. Plan the protective setting, measured by the evaluator or simulator' % (label, cases, MIN_CASES))
    return errors


def _inside_limit(value, limit, direction, inclusive=True):
    if direction == 'max':
        return value <= limit + 1e-12 if inclusive else value < limit - 1e-12
    return value >= limit - 1e-12 if inclusive else value > limit + 1e-12


def _harsher(a, b, direction):
    """a is at least as close to breaking the limit as b."""
    return a >= b - 1e-12 if direction == 'max' else a <= b + 1e-12


def _limit(rule, label, checks, keep):
    """Final: per kept meaning, a public replay and every planned stress, each harsher, each inside the limit."""
    limit, direction, inclusive = rule.get('limit'), rule.get('direction'), rule.get('inclusive')
    if not number(limit) or direction not in ('max', 'min') or type(inclusive) is not bool:
        return []
    errors = []
    planned = set(_strings(rule.get('stress_plan'))) & set(STRESS_TYPES)
    for meaning in sorted(keep):
        mine = [c for c in checks if c.get('meaning') == meaning]
        public = [c for c in mine if c.get('scenario_kind') == 'public' and number(c.get('value'))]
        stress = [c for c in mine if c.get('scenario_kind') == 'stress']
        if not public:
            errors.append('%s: kept meaning "%s" needs a public replay with its value' % (label, meaning))
        ran = set(_strings([c.get('stress_type') for c in stress]))
        if planned - ran:
            errors.append('%s: kept meaning "%s" has not run planned stress: %s' % (label, meaning, ', '.join(sorted(planned - ran))))
        if len(ran & set(STRESS_TYPES)) < 2:
            errors.append('%s: kept meaning "%s" needs at least two different stress types; a stress set no harsher than the '
                          'public data does not test a hard limit' % (label, meaning))
        if public:
            worst = max(c['value'] for c in public) if direction == 'max' else min(c['value'] for c in public)
            values = [c['value'] for c in stress if number(c.get('value'))]
            milder = [v for v in values if not _harsher(v, worst, direction)]
            if milder:
                errors.append('%s: stress for "%s" is milder than the public replay (%s vs %s); a stress scenario must push the '
                              'metric toward the limit' % (label, meaning, milder[0], worst))
            elif values and not any(abs(v - worst) > 1e-12 for v in values):
                errors.append('%s: no stress scenario for "%s" moves the metric at all; it repeats the public data' % (label, meaning))
    for item in checks:
        where = '%s: check "%s"' % (label, item.get('scenario'))
        kind = item.get('scenario_kind')
        if kind not in ('public', 'stress'):
            errors.append(where + ': scenario_kind must be "public" (replay of the given data) or "stress" (harsher than the given data)')
        elif kind == 'stress':
            if item.get('stress_type') not in STRESS_TYPES:
                errors.append(where + ': stress_type must be one of ' + ', '.join(STRESS_TYPES))
            if not meaningful(item.get('stress_param')):
                errors.append(where + ': stress_param required: how much harsher (e.g. demand +20%, one tool down for 8 h)')
        value = item.get('value')
        if not number(value):
            errors.append(where + ': value of the limited metric required (limit %s %s)' % (limit, rule.get('unit', '')))
            continue
        if not _inside_limit(value, limit, direction, inclusive):
            errors.append('%s: value %s breaks the limit %s (%s)' % (where, value, limit, 'equal allowed' if inclusive else 'equal not allowed'))
        if rule.get('metric_source') == 'estimated' and not item.get('estimated'):
            errors.append(where + ': metric_source is estimated, so every check is an estimate (estimated, risk_bound, estimator_validation)')
        if not item.get('estimated'):
            continue
        bound_value, check = item.get('risk_bound'), item.get('estimator_validation')
        if not number(bound_value) or not (bound_value > value if direction == 'max' else bound_value < value):
            errors.append(where + ': an estimated value needs risk_bound, its one-sided 95% bound on the side of the limit '
                          '(upper bound for a maximum, lower bound for a minimum), strictly beyond the estimate')
        elif not _inside_limit(bound_value, limit, direction, inclusive):
            errors.append('%s: the 95%% bound %s of the estimate breaks the limit %s; judge a hard limit by the bound, '
                          'not the point estimate' % (where, bound_value, limit))
        needed = max(MIN_CASES, rule.get('known_real_cases') if type(rule.get('known_real_cases')) is int else 0)
        if (not isinstance(check, dict) or type(check.get('explained')) is not int or type(check.get('total')) is not int
                or not 0 <= check['explained'] <= check['total']):
            errors.append(where + ': estimator_validation {explained, total} required: how many known real cases of this '
                          'metric (returns, escapes, failures, violations) the estimator explains')
        elif check['total'] < needed:
            errors.append('%s: the estimator was checked on %d real case(s), fewer than the %d planned at CP1 (minimum %d); an '
                          'estimate cannot certify this limit. Keep the protective setting' % (where, check['total'], needed, MIN_CASES))
        elif check['explained'] < MIN_EXPLAINED * check['total']:
            errors.append('%s: the estimator explains only %d of %d known real cases; it is not evidence that the limit '
                          'holds. Keep the protective setting (or fix the estimator) instead of relying on it'
                          % (where, check['explained'], check['total']))
    return errors


# --- penalty limits and two-sided targets ------------------------------------------------------------------

def _penalty(rule, label, phase, bound):
    if phase != 'final':
        return []
    tradeoff = rule.get('tradeoff') if isinstance(rule.get('tradeoff'), dict) else None
    alternatives = (tradeoff or {}).get('alternatives')
    if (not tradeoff or not meaningful(tradeoff.get('chosen')) or not number(tradeoff.get('chosen_expected_loss'))
            or not isinstance(alternatives, list) or len(alternatives) < 2
            or any(not isinstance(a, dict) or not meaningful(a.get('label')) or not number(a.get('expected_loss')) for a in alternatives)):
        return [label + ': a penalty limit needs its chosen setting compared with at least two alternatives by expected loss '
                '(points or cost); a margin on a penalty limit is paid for, not free']
    errors = []
    if not any(a.get('at_limit') is True for a in alternatives):
        errors.append(label + ': one alternative must be the setting that runs right at the penalty limit (at_limit: true)')
    expected = {'chosen_expected_loss': tradeoff['chosen_expected_loss'],
                'alternatives': {a['label']: a['expected_loss'] for a in alternatives}}
    errors.extend(_evidence(bound, tradeoff.get('evidence'), label + ': tradeoff', expected))
    best = min(a['expected_loss'] for a in alternatives)
    if tradeoff['chosen_expected_loss'] > best + 1e-9:
        errors.append(label + ': an alternative has a lower expected loss; choose it (a reason does not make a costlier setting cheaper)')
    return errors


def _target(rule, label, root, phase, bound):
    target, tolerance = rule.get('target'), rule.get('tolerance')
    if not number(target) or not number(tolerance) or tolerance <= 0:
        return [label + ': a two-sided target needs target and tolerance > 0 (e.g. 90% interval coverage, tolerance 2 points)']
    errors = []
    if target and tolerance > TOLERANCE_SHARE * abs(target):
        quote, source = rule.get('tolerance_quote'), rule.get('tolerance_source')
        try:
            text = _read_text(_inside(root, source)) if meaningful(source) else ''
        except (OSError, ValueError):
            text = ''
        if not meaningful(quote) or _normal(quote) not in _normal(text):
            errors.append('%s: tolerance %s is wider than %.0f%% of the target; quote the task sentence that allows it '
                          '(tolerance_quote found in tolerance_source)' % (label, tolerance, 100 * TOLERANCE_SHARE))
    if phase != 'final':
        return errors
    observed = rule.get('observed') if isinstance(rule.get('observed'), dict) else {}
    if not number(observed.get('value')):
        return errors + [label + ': final needs observed {value, evidence} for the two-sided target']
    errors.extend(_evidence(bound, observed.get('evidence'), label + ': observed', {'value': observed['value']}))
    if abs(observed['value'] - target) > tolerance + 1e-12:
        errors.append('%s: observed %s misses the two-sided target %s +/- %s; overshooting (for example 100%% coverage '
                      'for a 90%% target) loses points like undershooting' % (label, observed['value'], target, tolerance))
    return errors


# --- simple baselines and the search for the optimum -------------------------------------------------------

HOLDOUT_KEYS = ('holdout_kind', 'tuning_until', 'evaluated_from', 'holdout_groups')


def _order(value):
    if number(value):
        return ('n', value)
    if isinstance(value, str) and ISO_DATE.match(value.strip()):
        text = value.strip().replace(' ', 'T')
        try:
            datetime.datetime.fromisoformat(text)
        except ValueError:
            return None
        return ('d', text)
    return None


def _holdout(entry, label):
    if entry.get('holdout_kind', 'time') == 'time':
        tuned, evaluated = _order(entry.get('tuning_until')), _order(entry.get('evaluated_from'))
        if tuned is None or evaluated is None or tuned[0] != evaluated[0]:
            return [label + ': tuning_until and evaluated_from required as full ISO dates (YYYY-MM-DD) or numbers of the same kind']
        if tuned[0] == 'd' and len(tuned[1]) == 10 and evaluated[1][:10] <= tuned[1]:
            return ['%s: evaluation from %s overlaps the last tuning day %s; judge the output on a later period it was not '
                    'tuned on' % (label, entry.get('evaluated_from'), entry.get('tuning_until'))]
        if not evaluated[1] > tuned[1]:
            return ['%s: evaluation from %s overlaps the data used for tuning (until %s); judge the output on a '
                    'later period it was not tuned on' % (label, entry.get('evaluated_from'), entry.get('tuning_until'))]
        return []
    groups = entry.get('holdout_groups')
    if entry.get('holdout_kind') != 'group' or not isinstance(groups, list) or not groups or any(not meaningful(g) for g in groups):
        return [label + ': holdout_kind is "time" (with dates) or "group" with holdout_groups naming the held-out groups']
    return []


def _plans(doc):
    """CP1: which outputs will be tuned, the metric the task scores, the simple baselines, the boundary and the search."""
    plans = doc.get('baseline_plan')
    if plans in (None, []):
        if meaningful(doc.get('no_baseline_reason')):
            return {}, []
        return {}, ['hard_rules: CP1 needs baseline_plan (each output that will be tuned: metric, better, the simple '
                    'baselines it must beat, the tuning/evaluation boundary and the search) or no_baseline_reason']
    if not isinstance(plans, list):
        return {}, ['hard_rules: baseline_plan must be a list']
    found, errors = {}, []
    for index, plan in enumerate(plans):
        if not isinstance(plan, dict) or not meaningful(plan.get('output')):
            errors.append('baseline_plan %d: output required' % index)
            continue
        label = 'baseline_plan ' + plan['output']
        if plan['output'] in found:
            errors.append(label + ': duplicate output')
        found[plan['output']] = plan
        if not meaningful(plan.get('metric')) or plan.get('better') not in ('lower', 'higher') or not meaningful(plan.get('unit')):
            errors.append(label + ': metric, unit and better ("lower" or "higher") required')
        if not meaningful(plan.get('metric_quote')) or not meaningful(plan.get('metric_file')):
            errors.append(label + ': metric_quote and metric_file required: the task sentence that defines the scored metric '
                          '(optimise what is scored, not a proxy)')
        kinds = plan.get('baselines')
        if not isinstance(kinds, list) or any(not isinstance(kind, str) or kind not in BASELINE_KINDS for kind in kinds) or not any(kind != 'other' for kind in kinds):
            errors.append(label + ': baselines must list the simple baselines to beat (current, uniform, pooled, no_action)')
        elif type(plan.get('per_group')) is not bool:
            errors.append(label + ': per_group (true/false) required: are settings fitted separately per tool, chamber, product or group?')
        elif plan['per_group'] and 'pooled' not in kinds:
            errors.append(label + ': per-group settings must plan a pooled baseline (one setting for all groups)')
        search = plan.get('search_plan')
        if not isinstance(search, list) or len({m.strip() for m in search if meaningful(m)}) < 2:
            errors.append(label + ': search_plan must name at least two different optimisation methods (for example grid, '
                          'local search, MILP, Bayesian search) so the result is pushed to the optimum, not to a pass')
        if not number(plan.get('min_gain')) or plan['min_gain'] <= 0:
            errors.append(label + ': min_gain (> 0, in the metric\'s own unit) required: the smallest improvement worth another round')
        errors.extend(_holdout(plan, label))
    return found, errors


def _baselines(doc, root, phase, bound, rule_ids):
    """CP1 plan, then the final guard: each tuned output beats simple baselines on data after its tuning period."""
    plans, errors = _plans(doc)
    for output, plan in plans.items():
        if meaningful(plan.get('metric_quote')) and meaningful(plan.get('metric_file')):
            try:
                text = _read_text(_inside(root, plan['metric_file']))
            except (OSError, ValueError):
                text = ''
            if _normal(plan['metric_quote']) not in _normal(text):
                errors.append('baseline_plan %s: metric_quote is not in metric_file' % output)
    if phase != 'final' or errors:
        return errors
    guards = doc.get('baseline_guard')
    if guards in (None, []):
        if not plans:
            return []
        return ['hard_rules: final needs baseline_guard for every output in baseline_plan']
    if not isinstance(guards, list):
        return ['hard_rules: baseline_guard must be a list']
    guarded = {guard.get('output') for guard in _dicts(guards) if isinstance(guard.get('output'), str)}
    for output in sorted(set(plans) - guarded):
        if not meaningful(plans[output].get('dropped_reason')):
            errors.append('baseline_plan %s: planned at CP1 but has no final baseline_guard (or dropped_reason)' % output)
    for index, guard in enumerate(guards):
        if not isinstance(guard, dict):
            errors.append('baseline_guard %d: object required' % index)
            continue
        label = 'baseline_guard ' + (guard['output'] if meaningful(guard.get('output')) else str(index))
        submitted = guard.get('submitted')
        plan = plans.get(guard['output']) if isinstance(guard.get('output'), str) else None
        if plan is None:
            errors.append(label + ': output is not in the CP1 baseline_plan')
            continue
        better = plan.get('better')
        if not number(submitted):
            errors.append(label + ': submitted (the evaluation-period value of the submitted output) required')
            continue
        errors.extend(_holdout(guard, label))
        moved = [key for key in HOLDOUT_KEYS
                 if guard.get(key, 'time' if key == 'holdout_kind' else None) != plan.get(key, 'time' if key == 'holdout_kind' else None)]
        if moved:
            errors.append(label + ': the tuning/evaluation boundary differs from the CP1 plan (%s); keep the boundary fixed at CP1' % ', '.join(moved))
        baselines = guard.get('baselines')
        if not isinstance(baselines, list) or not baselines:
            errors.append(label + ': baselines required (current practice, uniform, pooled single setting or no action)')
            continue
        recorded, usable = [], []
        for item in baselines:
            if (not isinstance(item, dict) or not meaningful(item.get('label')) or not isinstance(item.get('kind'), str) or item['kind'] not in BASELINE_KINDS
                    or not number(item.get('value'))):
                errors.append(label + ': each baseline needs label, kind (%s) and value' % ', '.join(BASELINE_KINDS))
                continue
            recorded.append(item)
            if item.get('admissible', True) is False:
                if not isinstance(item.get('violated_rule'), str) or item['violated_rule'] not in rule_ids:
                    errors.append('%s: baseline "%s" can be set aside only for breaking a rule in this table (violated_rule)' % (label, item['label']))
                else:
                    try:
                        data = json.loads(_read_text(bound(item.get('violation_evidence'))))
                        if not isinstance(data, dict) or type(data.get('violations')) is not int or data['violations'] < 1:
                            raise ValueError('violation evidence must state violations >= 1')
                    except (OSError, ValueError, TypeError) as exc:
                        errors.append('%s: baseline "%s" violation_evidence: %s' % (label, item['label'], exc))
                continue
            usable.append(item)
        dropped = sorted(set(_strings(plan.get('baselines'))) - {item['kind'] for item in recorded})
        if dropped:
            errors.append(label + ': baselines planned at CP1 are missing at final: ' + ', '.join(dropped))
        for item in usable:
            worse = submitted > item['value'] + 1e-12 if better == 'lower' else submitted < item['value'] - 1e-12
            if worse:
                errors.append('%s: submitted %s is worse than baseline "%s" (%s) on the held-out data; submit the better '
                              'baseline or move toward it. A tuned output that loses to a simple rule is overfitted'
                              % (label, submitted, item['label'], item['value']))
        errors.extend(_evidence(bound, guard.get('evidence'), label, {'submitted': submitted,
                                'baselines': {item['label']: item['value'] for item in recorded}}))
        errors.extend(_optimum(guard, label, better, plan, bound))
    return errors


def _gain(old, new, better):
    return (old - new) if better == 'lower' else (new - old)


def _optimum(guard, label, better, plan, bound):
    """Final: the search, scored on the tuning period only, submitted its best round and reached the optimum.

    Each round names the candidate it scored (candidate_sha256 of the output file); the submitted artifact must be
    the chosen round's candidate. A proven bound ends the search at once; otherwise the search stops on a plateau
    near the best (gains below min_gain) or, recorded as such, when less than one round of time is left.
    """
    search = guard.get('optimization') if isinstance(guard.get('optimization'), dict) else {}
    rounds = search.get('rounds')
    if (not isinstance(rounds, list) or not rounds
            or any(not isinstance(r, dict) or not meaningful(r.get('method')) or not number(r.get('value'))
                   or not meaningful(r.get('candidate_sha256')) for r in rounds)):
        return [label + ': optimization.rounds needs the search rounds in order, each {method, value (tuning-period score), '
                'candidate_sha256 (hash of the candidate output), admissible?}']
    errors = _evidence(bound, search.get('evidence'), label + ': optimization', {'rounds': [r['value'] for r in rounds]})
    usable = [r for r in rounds if r.get('admissible', True) is not False]
    if not usable:
        return errors + [label + ': no admissible search round']
    hashes = [r['candidate_sha256'] for r in usable]
    if len(set(hashes)) != len(hashes):
        errors.append(label + ': rounds repeat the same candidate; a repeated candidate is not a new search round')
    best, gains = usable[0]['value'], [None]
    for item in usable[1:]:
        gain = max(0.0, _gain(best, item['value'], better))
        if gain > 0:
            best = item['value']
        gains.append(gain)
    chosen = search.get('chosen')
    artifact = guard.get('artifact')
    if type(chosen) is not int or not 0 <= chosen < len(rounds) or rounds[chosen].get('admissible', True) is False:
        errors.append(label + ': optimization.chosen must be the index of the admissible round that was submitted')
    else:
        if _gain(rounds[chosen]['value'], best, better) > 1e-9 * max(abs(best), 1.0):
            errors.append('%s: round %d was submitted but a better admissible round (%s) exists on the tuning period; submit it'
                          % (label, chosen, best))
        try:
            bound(artifact)
            if artifact.get('sha256') != rounds[chosen]['candidate_sha256']:
                errors.append(label + ': the submitted artifact is not the candidate of the chosen round')
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            errors.append(label + ': artifact (the submitted output file {path, sha256}): ' + str(exc))
    scale = max(abs(best), abs(usable[0]['value']), 1e-9)
    target = search.get('bound')
    if target is not None:
        if not number(target) or not meaningful(search.get('bound_method')):
            errors.append(label + ': bound needs a number and bound_method (oracle with full information, LP/MILP relaxation, ...)')
        else:
            bound_errors = _evidence(bound, search.get('bound_evidence'), label + ': bound', {'bound': target})
            errors.extend(bound_errors)
            if _gain(best, target, better) < -1e-9 * scale:
                errors.append('%s: bound %s is worse than the best round %s, so it is not a bound on the optimum' % (label, target, best))
            elif not bound_errors and abs(target - best) <= OPT_GAP * scale:
                return errors
    stop = search.get('stop') if isinstance(search.get('stop'), dict) else {}
    if stop.get('reason') == 'deadline':
        if number(stop.get('round_minutes')) and number(stop.get('remaining_minutes')) and stop['remaining_minutes'] < stop['round_minutes']:
            return errors
        return errors + [label + ': a deadline stop needs round_minutes and remaining_minutes with less time left than one round']
    if len(usable) < 3:
        return errors + [label + ': without a proven bound or a recorded deadline stop the search needs at least three admissible rounds']
    methods = {r['method'].strip() for r in usable}
    if len(methods) < 2:
        errors.append(label + ': optimization used one method only; try at least two different methods')
    planned = {m.strip() for m in _strings(plan.get('search_plan')) if meaningful(m)}
    if planned - methods:
        errors.append(label + ': methods planned at CP1 but not run: ' + ', '.join(sorted(planned - methods)))
    min_gain = plan.get('min_gain') if number(plan.get('min_gain')) else 0.0
    near = max(2 * min_gain, OPT_GAP * scale)
    recent = list(zip(usable, gains))[-PLATEAU_ROUNDS:]
    if any(g is None or g >= min_gain or abs(r['value'] - best) > near for r, g in recent):
        errors.append('%s: the search has not reached the optimum: the last %d rounds must each gain less than min_gain (%s) '
                      'while staying near the best, or the best must be within %.0f%% of a proven bound; keep optimising '
                      'instead of stopping at a passing result' % (label, PLATEAU_ROUNDS, min_gain, 100 * OPT_GAP))
    return errors


# --- CP1 freeze --------------------------------------------------------------------------------------------

FROZEN_RULE = ('consequence', 'term', 'limit', 'direction', 'inclusive', 'unit', 'statistic', 'metric_source', 'uses_model',
               'explained_definition', 'target', 'tolerance')
FROZEN_PLAN = ('metric', 'better', 'unit', 'per_group', 'metric_quote', 'metric_file') + HOLDOUT_KEYS


def compare_freeze(cp1, final):
    """Errors where the final table narrows or rewrites what the CP1 review saw."""
    if not isinstance(cp1, dict) or not isinstance(cp1.get('rules'), list):
        return ['hard_rules_cp1: CP1 copy must be a version 1 table']
    errors = []
    now = {r.get('id'): r for r in _dicts(final.get('rules')) if isinstance(r.get('id'), str)}
    for old in _dicts(cp1['rules']):
        rule_id = old.get('id')
        new = now.get(rule_id)
        label = 'hard_rules %s' % rule_id
        if new is None:
            errors.append(label + ': rule from the CP1 table was removed')
            continue
        changed = [key for key in FROZEN_RULE if old.get(key) != new.get(key)]
        if changed:
            errors.append(label + ': changed since CP1 (%s); these are fixed at CP1' % ', '.join(changed))
        before = set(_strings([c.get('meaning') for c in _dicts(old.get('candidates'))]))
        after = set(_strings([c.get('meaning') for c in _dicts(new.get('candidates'))]))
        if before - after:
            errors.append(label + ': candidate meaning(s) dropped since CP1: ' + ', '.join(sorted(map(str, before - after))))
        if old.get('decision') != new.get('decision') and not (
                new.get('decision') == 'ALL_MEANINGS' or (old.get('decision') == 'ALL_MEANINGS' and new.get('decision') == 'OFFICIAL_ANSWER')):
            errors.append(label + ': decision changed from %s to %s after CP1; only a move to ALL_MEANINGS, or to an official '
                          'answer received later, is allowed' % (old.get('decision'), new.get('decision')))
        if set(_strings(old.get('stress_plan'))) - set(_strings(new.get('stress_plan'))):
            errors.append(label + ': stress types dropped since CP1')
        if type(old.get('known_real_cases')) is int and (type(new.get('known_real_cases')) is not int or new['known_real_cases'] < old['known_real_cases']):
            errors.append(label + ': known_real_cases lowered since CP1')
    plans = {p.get('output'): p for p in _dicts(final.get('baseline_plan')) if isinstance(p.get('output'), str)}
    for old in _dicts(cp1.get('baseline_plan')):
        new = plans.get(old.get('output'))
        label = 'baseline_plan %s' % old.get('output')
        if new is None:
            errors.append(label + ': planned output removed since CP1')
            continue
        changed = [key for key in FROZEN_PLAN if old.get(key) != new.get(key)]
        if changed:
            errors.append(label + ': changed since CP1 (%s); these are fixed at CP1' % ', '.join(changed))
        if set(_strings(old.get('baselines'))) - set(_strings(new.get('baselines'))):
            errors.append(label + ': baselines dropped since CP1')
        if set(_strings(old.get('search_plan'))) - set(_strings(new.get('search_plan'))):
            errors.append(label + ': search methods dropped since CP1')
        if number(old.get('min_gain')) and (not number(new.get('min_gain')) or new['min_gain'] > old['min_gain']):
            errors.append(label + ': min_gain raised since CP1')
    if set(_strings(cp1.get('materials'))) - set(_strings(final.get('materials'))):
        errors.append('hard_rules: materials dropped since CP1')
    return errors


# --- the table ---------------------------------------------------------------------------------------------

def validate(doc, root, phase='cp1', bound=None, frozen=None):
    """Errors for the hard-rule table at `phase` ('cp1' or 'final'); `frozen` is the CP1 copy at final."""
    try:
        return _validate(doc, root, phase, bound, frozen)
    except Exception as exc:  # a malformed table is a FAIL with a message, never a crash
        return ['hard_rules: malformed table (%s: %s); check field types against templates/HARD_RULES.json' % (type(exc).__name__, exc)]


def _validate(doc, root, phase, bound, frozen):
    bound = bound or default_bound(root)
    if not isinstance(doc, dict) or doc.get('version') != 1 or not isinstance(doc.get('rules'), list):
        return ['hard_rules: version 1 object with a rules list required']
    rules = doc['rules']
    errors = []
    paths, material_errors = _materials(doc, root, phase)
    errors.extend(material_errors)
    if paths:
        errors.extend(_coverage(doc, root, paths))
    if not rules and not meaningful(doc.get('no_hard_rules_reason')):
        errors.append('hard_rules: list every void, zero-point, rejection, penalty and target rule, or give no_hard_rules_reason')
    ids = set()
    context = {'doc': doc, 'paths': paths}
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append('hard_rules %d: rule object required' % index)
            continue
        label = 'hard_rules ' + (rule['id'] if meaningful(rule.get('id')) else str(index))
        if not meaningful(rule.get('id')) or rule.get('id') in ids:
            errors.append(label + ': unique id required')
        else:
            ids.add(rule['id'])
        for key in ('rule', 'source'):
            if not meaningful(rule.get(key)):
                errors.append(label + ': ' + key + ' required')
        consequence = rule.get('consequence')
        if consequence in HARD:
            errors.extend(_hard(rule, label, root, phase, bound, context))
        elif consequence == 'PENALTY':
            errors.extend(_penalty(rule, label, phase, bound))
        elif consequence == 'TARGET':
            errors.extend(_target(rule, label, root, phase, bound))
        elif consequence != 'SOFT':
            errors.append(label + ': consequence must be VOID, ZERO, REJECT, PENALTY, TARGET or SOFT')
    errors.extend(_baselines(doc, root, phase, bound, ids))
    if phase == 'final':
        if frozen is None:
            errors.append('hard_rules: final needs the CP1 copy of the table (V27_EVIDENCE records.hard_rules_cp1) to compare with')
        else:
            errors.extend(compare_freeze(frozen, doc))
    return errors


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
    check_p.add_argument('--cp1', help='the CP1 copy of the table (required for --phase final)')
    scan_p = sub.add_parser('scan', help='list every place a rule term appears')
    scan_p.add_argument('--root', type=Path, required=True)
    scan_p.add_argument('--term', action='append', required=True)
    scan_p.add_argument('--path', action='append', help='task material file or folder (default: the whole task folder)')
    scan_p.add_argument('--limit', type=int, default=300)
    args = parser.parse_args(argv)
    if args.command == 'scan':
        print(json.dumps(scan(args.root, args.term, args.limit, tuple(args.path or ['.'])), ensure_ascii=False, indent=1))
        return 0
    try:
        doc = json.loads(_read_text(_inside(args.root, args.file)))
        frozen = json.loads(_read_text(_inside(args.root, args.cp1))) if args.cp1 else None
    except (OSError, ValueError) as exc:
        print(json.dumps(dict(status='FAIL', errors=['hard_rules: ' + str(exc)]), ensure_ascii=False))
        return 1
    errors = validate(doc, args.root, args.phase, frozen=frozen)
    print(json.dumps(dict(status='FAIL' if errors else 'PASS', errors=errors), ensure_ascii=False, indent=1))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
