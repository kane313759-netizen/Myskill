"""Evidence integrity and real-CLI regressions for local declared-check coverage."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/local_score.py'

GUARDED_RUN = r'''
import argparse, hashlib, json, math, os, pathlib, pkgutil, re, runpy, stat, sys
write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
mutations = {'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.symlink',
             'os.link', 'os.chmod', 'os.truncate', 'os.utime', 'shutil.copyfile'}
executions = {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.fork'}
def audit(event, args):
    forbidden = event in mutations or event in executions or event.startswith('socket.')
    if event == 'open':
        mode, flags = args[1], args[2]
        forbidden = forbidden or (isinstance(mode, str) and any(c in mode for c in 'wax+'))
        forbidden = forbidden or (isinstance(flags, int) and bool(flags & write_flags))
    if event in {'os.listdir', 'os.scandir'}:
        forbidden = True
    if forbidden:
        raise AssertionError('PROHIBITED_SCORE_SIDE_EFFECT: ' + event)
sys.addaudithook(audit)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


class LocalScoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='local score 한글 ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.rubric = self.root / 'rubric.json'
        self.results = self.root / 'results.json'
        self.evaluator = self.root / 'independent checker.py'
        self.evaluator.write_text('raise RuntimeError("must never execute")\n', encoding='utf-8')
        self.rubric_value = dict(version=1, unknowns=['Hidden grading weights unavailable'], criteria=[
            dict(id=identifier, description='Check ' + identifier, source='original-task.txt:1',
                 oracle='Original schema requires ' + identifier)
            for identifier in ('schema', 'boundary', 'invalid', 'budget')])
        self.result_value = dict(version=1, label='baseline', evaluated_version='dirty-source-sha:before',
                                 evaluation_scope='fixture-sha256:abc; policy:v1; max-rows:100', checks=[])
        self.save()

    def write_json(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def save(self):
        self.write_json(self.rubric, self.rubric_value)
        self.write_json(self.results, self.result_value)

    def checks(self, statuses):
        self.result_value['checks'] = [dict(id=identifier, status=status, evidence='raw.log:12; ' + status)
                                       for identifier, status in zip(('schema', 'boundary', 'invalid', 'budget'), statuses)]
        self.save()

    def run_cli(self, expected, extra=(), guarded=False, evaluators=None):
        invocation = [sys.executable, '-I', '-S', '-B']
        if guarded:
            invocation += ['-c', GUARDED_RUN]
        invocation += [str(SCRIPT), '--rubric', str(self.rubric), '--results', str(self.results)]
        for evaluator in ([self.evaluator] if evaluators is None else evaluators):
            invocation += ['--evaluator', str(evaluator)]
        result = subprocess.run(invocation + list(extra), cwd=str(self.root), capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.last_stdout = result.stdout
        if expected == 2:
            self.assertEqual(result.stdout, '')
            self.assertIn('Invalid local score input:', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            return None
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def baseline(self):
        report = self.run_cli(0 if len(self.result_value['checks']) == 4 and
                              all(c['status'] == 'PASS' for c in self.result_value['checks']) else 1)
        path = self.root / 'before-generated.json'
        self.write_json(path, report)
        return path, report

    def test_mixed_missing_and_skipped_checks_keep_fixed_denominator(self):
        self.checks(['PASS', 'FAIL', 'SKIP'])
        report = self.run_cli(1)
        self.assertEqual(report['score'], dict(earned=1, total=4, percent=25.0))
        self.assertEqual(report['counts'], dict(PASS=1, FAIL=1, ERROR=0, SKIP=1, UNVERIFIED=1))
        self.assertEqual(report['checks'][-1], dict(id='budget', status='UNVERIFIED', evidence=''))
        self.assertEqual(report['evaluated_version'], 'dirty-source-sha:before')
        self.assertEqual(report['evaluation_scope'], self.result_value['evaluation_scope'])
        self.assertIn('not an official score', report['notice'])
        self.assertIn('independent review', report['notice'])
        self.assertEqual(report['unknowns'], self.rubric_value['unknowns'])

    def test_all_pass_success_uses_actual_evaluator_bytes_and_path(self):
        self.checks(['PASS'] * 4)
        report = self.run_cli(0)
        self.assertEqual(report['score']['percent'], 100.0)
        self.assertEqual(report['evaluators'], {os.path.normcase(str(self.evaluator.resolve())):
                                              hashlib.sha256(self.evaluator.read_bytes()).hexdigest()})
        self.assertEqual(report['rubric_sha256'], hashlib.sha256(self.rubric.read_bytes()).hexdigest())

    def test_all_skipped_and_no_results_never_pass(self):
        for statuses in (['SKIP'] * 4, [], ['ERROR'] * 4):
            with self.subTest(statuses=statuses):
                self.checks(statuses)
                report = self.run_cli(1)
                self.assertEqual(report['score'], dict(earned=0, total=4, percent=0.0))

    def test_empty_rubric_is_unavailable_even_with_no_evaluators(self):
        self.rubric_value['criteria'] = []
        self.save()
        report = self.run_cli(1, evaluators=[])
        self.assertEqual(report['score'], dict(earned=0, total=0, percent=None))

    def test_nonempty_rubric_requires_explicit_evaluator(self):
        self.run_cli(2, evaluators=[])

    def test_progress_keeps_code_versions_and_reports_lost_pass_separately(self):
        self.checks(['PASS', 'FAIL', 'SKIP', 'UNVERIFIED'])
        path, old_report = self.baseline()
        old_bytes = path.read_bytes()
        self.checks(['UNVERIFIED', 'PASS', 'PASS', 'PASS'])
        self.result_value.update(label='final', evaluated_version='dirty-source-sha:after')
        self.save()
        report = self.run_cli(1, ['--compare', str(path)])
        self.assertEqual(report['score']['percent'], 75.0)
        self.assertTrue(report['comparison']['comparable'])
        self.assertEqual(report['comparison']['delta'], dict(earned=2, percentage_points=50.0))
        self.assertEqual(report['comparison']['lost_pass'], ['schema'])
        self.assertEqual(report['comparison']['baseline_evaluated_version'], old_report['evaluated_version'])
        self.assertEqual(report['evaluated_version'], 'dirty-source-sha:after')
        self.assertEqual(path.read_bytes(), old_bytes)

    def test_same_rubric_final_all_pass_and_comparable_returns_zero(self):
        self.checks(['FAIL'] * 4)
        path, _ = self.baseline()
        self.checks(['PASS'] * 4)
        report = self.run_cli(0, ['--compare', str(path)])
        self.assertEqual(report['comparison']['delta'], dict(earned=4, percentage_points=100.0))

    def test_changed_checker_or_raw_rubric_bytes_suppress_delta(self):
        self.checks(['PASS'] * 4)
        path, _ = self.baseline()
        original_checker = self.evaluator.read_bytes()
        self.evaluator.write_bytes(original_checker + b'# changed oracle\n')
        report = self.run_cli(1, ['--compare', str(path)])
        self.assertFalse(report['comparison']['comparable'])
        self.assertIsNone(report['comparison']['delta'])
        self.assertEqual(report['score']['percent'], 100.0)
        self.evaluator.write_bytes(original_checker)
        self.rubric.write_bytes(self.rubric.read_bytes() + b'\n')
        report = self.run_cli(1, ['--compare', str(path)])
        self.assertIsNone(report['comparison']['delta'])
        self.assertIsNone(report['comparison']['lost_pass'])

    def test_changed_or_unknown_evaluation_scope_is_not_comparable(self):
        self.checks(['PASS'] * 4)
        path, _ = self.baseline()
        for scope in ('full-data; max-rows:10000', 'UNKNOWN', ' unknown '):
            with self.subTest(scope=scope):
                self.result_value['evaluation_scope'] = scope
                self.save()
                report = self.run_cli(1, ['--compare', str(path)])
                self.assertFalse(report['comparison']['comparable'])
                self.assertIsNone(report['comparison']['delta'])
        # Matching UNKNOWN is also not established comparable evidence.
        self.result_value['evaluation_scope'] = 'UNKNOWN'
        self.save()
        self.write_json(path, self.run_cli(0))
        self.assertFalse(self.run_cli(1, ['--compare', str(path)])['comparison']['comparable'])

    def test_unknown_candidate_version_is_honest_but_needs_known_scope_for_delta(self):
        self.result_value['evaluated_version'] = 'UNKNOWN'
        self.checks(['PASS'] * 4)
        self.assertEqual(self.run_cli(0)['evaluated_version'], 'UNKNOWN')

    def test_expected_application_exit_two_can_be_a_pass(self):
        self.checks(['PASS'] * 4)
        self.result_value['checks'][2]['evidence'] = 'invalid-input.log:1; oracle expected application exit 2, observed 2'
        self.save()
        self.assertEqual(self.run_cli(0)['counts']['PASS'], 4)

    def test_duplicate_unknown_and_missing_evidence_are_invalid(self):
        variants = [
            [dict(id='schema', status='PASS', evidence='')],
            [dict(id='schema', status='FAIL')],
            [dict(id='schema', status='ERROR', evidence='  ')],
            [dict(id='unknown', status='PASS', evidence='log')],
            [dict(id='schema', status='SKIP'), dict(id='schema', status='UNVERIFIED')],
        ]
        for checks in variants:
            with self.subTest(checks=checks):
                self.result_value['checks'] = checks
                self.save()
                self.run_cli(2)

    def test_blank_oracle_source_description_and_duplicate_criteria_are_invalid(self):
        original = copy.deepcopy(self.rubric_value)
        for field in ('id', 'description', 'source', 'oracle'):
            self.rubric_value = copy.deepcopy(original)
            self.rubric_value['criteria'][0][field] = ' '
            self.save()
            self.run_cli(2)
        self.rubric_value = original
        self.rubric_value['criteria'].append(copy.deepcopy(original['criteria'][0]))
        self.save()
        self.run_cli(2)

    def test_strict_schema_rejects_bool_wrong_types_and_invented_weights(self):
        cases = [dict(version=True), dict(label=' '), dict(evaluated_version=False),
                 dict(evaluation_scope=''), dict(checks={}), dict(checks=[True]),
                 dict(checks=[dict(id='schema', status=True, evidence='log')]),
                 dict(checks=[dict(id='schema', status='PASS', evidence=1)])]
        original = copy.deepcopy(self.result_value)
        for changes in cases:
            with self.subTest(changes=changes):
                self.result_value = dict(original, **changes)
                self.save()
                self.run_cli(2)
        self.result_value = original
        self.rubric_value['criteria'][0]['weight'] = 100
        self.save()
        self.run_cli(2)

    def test_duplicate_json_keys_nonfinite_and_invalid_utf8_fail_cleanly(self):
        for payload in (b'{"version":1,"version":1}', b'{"x":NaN}', b'{"x":Infinity}',
                        b'{"x":1e999}', b'\xff', b'{"x":{"same":1,"same":2}}'):
            with self.subTest(payload=payload):
                self.results.write_bytes(payload)
                self.run_cli(2)

    def test_utf8_bom_supported_without_rewriting_input(self):
        self.checks(['PASS'] * 4)
        self.rubric.write_bytes(b'\xef\xbb\xbf' + self.rubric.read_bytes())
        before = self.rubric.read_bytes()
        self.run_cli(0)
        self.assertEqual(self.rubric.read_bytes(), before)

    def test_deep_json_and_json_byte_limit_fail_cleanly(self):
        for payload in (b'[' * 2000 + b'0' + b']' * 2000, b' ' * (1024 * 1024 + 1)):
            self.results.write_bytes(payload)
            self.run_cli(2)

    def test_criterion_and_result_count_limits(self):
        self.rubric_value['criteria'] = [dict(id=str(index), description='requirement',
                                             source='task.txt:1', oracle='exact schema')
                                          for index in range(1001)]
        self.save()
        self.run_cli(2)
        self.rubric_value['criteria'] = self.rubric_value['criteria'][:1]
        self.result_value['checks'] = [dict(id=str(index), status='UNVERIFIED') for index in range(1001)]
        self.save()
        self.run_cli(2)

    def test_exact_thousand_criterion_boundary_still_keeps_unrun_denominator(self):
        self.rubric_value['criteria'] = [dict(id=str(index), description='requirement',
                                             source='task.txt:1', oracle='exact schema')
                                          for index in range(1000)]
        self.result_value['checks'] = [dict(id='0', status='PASS', evidence='native.log:1')]
        self.save()
        self.assertEqual(self.run_cli(1)['score'], dict(earned=1, total=1000, percent=0.1))

    def test_evaluator_byte_limits_and_duplicates(self):
        with self.evaluator.open('wb') as handle:
            handle.truncate(16 * 1024 * 1024 + 1)
        self.run_cli(2)
        self.evaluator.write_bytes(b'checker')
        self.run_cli(2, evaluators=[self.evaluator, self.evaluator])
        evaluators = []
        for index in range(5):
            path = self.root / ('checker-%d' % index)
            with path.open('wb') as handle:
                handle.truncate(16 * 1024 * 1024 if index < 4 else 1)
            evaluators.append(path)
        self.assertEqual(self.run_cli(1, evaluators=evaluators[:4])['score']['total'], 4)
        self.run_cli(2, evaluators=evaluators)

    def test_regular_file_and_missing_file_checks(self):
        self.run_cli(2, evaluators=[self.root])
        self.run_cli(2, evaluators=[self.root / 'missing'])

    def test_target_symlinks_are_rejected_for_every_input(self):
        link = self.root / 'input-link'
        try:
            link.symlink_to(self.evaluator)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        self.run_cli(2, evaluators=[link])
        original = self.results
        link.unlink()
        link.symlink_to(original)
        self.results = link
        self.run_cli(2)
        self.results = original
        self.run_cli(2, ['--compare', str(link)])
        link.unlink()
        original_rubric = self.rubric
        link.symlink_to(original_rubric)
        self.rubric = link
        self.run_cli(2)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'named pipes unavailable')
    def test_fifo_rejected_without_opening_or_blocking(self):
        fifo = self.root / 'pipe'
        os.mkfifo(str(fifo))
        self.run_cli(2, evaluators=[fifo])
        self.results = fifo
        self.run_cli(2)

    def test_comparison_requires_consistent_generated_report(self):
        self.checks(['PASS'] * 4)
        path, original = self.baseline()
        for field, value in (('score', dict(earned=True, total=4, percent=100.0)),
                             ('score', dict(earned=1, total=4, percent=25.0)),
                             ('counts', dict(PASS=4, FAIL=0, ERROR=0, SKIP=0, UNVERIFIED=True)),
                             ('scope', 'OFFICIAL_SCORE'), ('evaluation_scope', ''),
                             ('rubric_sha256', 'fake'), ('evaluators', {})):
            with self.subTest(field=field, value=value):
                self.write_json(path, dict(original, **{field: value}))
                self.run_cli(2, ['--compare', str(path)])

    def test_guarded_cli_treats_malicious_commands_as_data_and_preserves_files(self):
        marker = self.root / 'EXECUTED'
        attack = '__import__("pathlib").Path(%r).touch(); $(touch EXECUTED)' % str(marker)
        self.evaluator.write_text(attack, encoding='utf-8')
        self.checks(['PASS'] * 4)
        self.result_value['checks'][0]['evidence'] = attack
        self.rubric_value['criteria'][0]['oracle'] = attack
        self.save()
        baseline_path, _ = self.baseline()
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in self.root.iterdir() if path.is_file()}
        self.run_cli(0, ['--compare', str(baseline_path)], guarded=True)
        after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                 for path in self.root.iterdir() if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(marker.exists())
        self.assertFalse(list(self.root.rglob('__pycache__')))

    def test_large_korean_and_non_bmp_reports_round_trip_as_comparison_inputs(self):
        self.rubric_value['criteria'] = self.rubric_value['criteria'][:1]
        for character, count in (('가', 180000), ('😀', 150000)):
            with self.subTest(character=character):
                self.checks(['PASS'])
                self.result_value['checks'][0]['evidence'] = character * count
                self.save()
                self.assertLess(self.results.stat().st_size, 1024 * 1024)
                self.run_cli(0)
                baseline_bytes = self.last_stdout.encode('ascii')
                self.assertGreater(len(baseline_bytes), 1024 * 1024)
                path = self.root / 'large-baseline.json'
                path.write_bytes(baseline_bytes)
                report = self.run_cli(0, ['--compare', str(path)])
                self.assertTrue(report['comparison']['comparable'])
                self.assertEqual(report['comparison']['delta']['earned'], 0)
                self.assertEqual(path.read_bytes(), baseline_bytes)

    def test_report_input_and_serialized_output_have_separate_eight_mib_bound(self):
        self.checks(['PASS'] * 4)
        path, previous = self.baseline()
        # A schema-valid historical record may contain a much larger label than
        # current results allow. Combining it with current evidence must fail
        # before any oversized, unusable report is printed.
        previous['label'] = '😀' * 650000
        self.write_json(path, previous)
        self.assertLess(path.stat().st_size, 8 * 1024 * 1024)
        self.result_value['checks'][0]['evidence'] = '가' * 180000
        self.save()
        self.run_cli(2, ['--compare', str(path)])
        path.write_bytes(b' ' * (8 * 1024 * 1024 + 1))
        self.run_cli(2, ['--compare', str(path)])

    def test_symlink_parent_dotdot_hashes_actual_checker_and_detects_changes(self):
        directory = self.root / 'external'
        (directory / 'subdir').mkdir(parents=True)
        actual = directory / 'checker.py'
        actual.write_bytes(b'real checker v1')
        decoy = self.root / 'checker.py'
        decoy.write_bytes(b'lexically normalized decoy')
        alias = self.root / 'alias'
        try:
            alias.symlink_to(directory / 'subdir', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('directory symlinks unavailable')
        supplied = alias / '..' / 'checker.py'
        if not os.path.samefile(supplied, actual):
            self.skipTest('platform collapses dotdot before following directory aliases')
        self.checks(['PASS'] * 4)
        report = self.run_cli(0, evaluators=[supplied])
        self.assertEqual(report['evaluators'], {os.path.normcase(str(actual.resolve())):
                                              hashlib.sha256(actual.read_bytes()).hexdigest()})
        path = self.root / 'aliased-baseline.json'
        self.write_json(path, report)
        actual.write_bytes(b'real checker v2')
        report = self.run_cli(1, ['--compare', str(path)], evaluators=[supplied])
        self.assertFalse(report['comparison']['comparable'])
        self.assertIsNone(report['comparison']['delta'])
        self.assertEqual(report['score']['percent'], 100.0)
        # Resolving parent aliases must not turn an originally supplied final
        # symlink into an accepted evaluator target.
        actual.unlink()
        actual.symlink_to(decoy)
        self.run_cli(2, evaluators=[supplied])

    def test_historical_missing_evaluator_is_not_opened_during_comparison(self):
        self.checks(['PASS'] * 4)
        path, _ = self.baseline()
        replacement = self.root / 'replacement-checker.py'
        self.evaluator.rename(replacement)
        report = self.run_cli(1, ['--compare', str(path)], evaluators=[replacement])
        self.assertFalse(report['comparison']['comparable'])
        self.assertIsNone(report['comparison']['delta'])


if __name__ == '__main__':
    unittest.main()
