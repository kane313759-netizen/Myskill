"""Aggregate review checks use synthetic fixtures, never actual agent execution evidence."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from review_fixture import make_execution

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('finals_review_check', ROOT / 'scripts/finals_review_check.py')
aggregate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aggregate)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FinalsReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='finals-review-fixture-')
        self.addCleanup(temp.cleanup)
        self.task = Path(temp.name)
        self.kit = self.task / '.hackathon-kit'
        (self.kit / 'run').mkdir(parents=True)
        files = {'source.py': 'print(1)\n', 'config.json': '{"capacity": 700}\n',
                 'evaluator.py': '# synthetic exact-output evaluator fixture\n',
                 'result.json': '{"selected": [1]}\n',
                 'TASK.md': 'Synthetic local file calculation. No external service or authentication.\n'}
        for name, value in files.items():
            (self.task / name).write_text(value, encoding='utf-8')
        self.plan = {'version': 1, 'checkpoint': 'FINAL',
                     'required_scope': {name: digest(self.task / name)
                                        for name in files if name != 'TASK.md'},
                     'security': {'decision': 'NOT_TRIGGERED',
                                  'reason': 'Inspected synthetic local calculation task and code.',
                                  'inspected_sources': {'TASK.md': digest(self.task / 'TASK.md')},
                                  'triggers': []},
                     'reviews': {'SECURITY_RED': {'status': 'NOT_APPLICABLE',
                                                 'reason': 'No material security surface in this synthetic fixture.'}}}
        for role in aggregate.CORE_ROLES:
            self.add_review(role)
        self.path = self.kit / 'run/FINALS_REVIEWS.json'

    def add_review(self, role, worker=None):
        report_path = '.hackathon-kit/run/reviews/FINAL-' + role + '/report.md'
        report = self.task / report_path
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text('Synthetic ' + role + ' FINAL report: required current scope checked.', encoding='utf-8')
        receipt = make_execution(self.task, role, 'FINAL', report_path,
                                 dict(self.plan['required_scope']))
        if role == 'SECURITY_RED':
            receipt['reviewed_files'].update(self.plan['security']['inspected_sources'])
        # Every synthetic reviewer must have its own native/wrapper identity.
        worker = worker or '/synthetic-final-fixture/' + role
        receipt['worker_id'] = worker
        for record in receipt['observations'].values():
            path = self.task / record['path']
            event = json.loads(path.read_text(encoding='utf-8'))
            event['worker_id'] = worker
            event['raw']['worker_id'] = worker
            path.write_text(json.dumps(event), encoding='utf-8')
            record['sha256'] = digest(path)
        receipt_path = report.parent / 'execution.json'
        receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
        self.plan['reviews'][role] = {'status': 'ACCEPTED', 'findings': [],
                                     'execution_receipt': {'path': receipt_path.relative_to(self.task).as_posix(),
                                                           'sha256': digest(receipt_path)}}

    def errors(self):
        return aggregate.check_reviews(self.plan, self.kit, 'FINAL')

    def change_receipt(self, role, change):
        record = self.plan['reviews'][role]['execution_receipt']
        path = self.task / record['path']
        receipt = json.loads(path.read_text(encoding='utf-8'))
        change(receipt)
        path.write_text(json.dumps(receipt), encoding='utf-8')
        record['sha256'] = digest(path)

    def trigger_security(self):
        task = self.task / 'TASK.md'
        task.write_text('AUTH: this synthetic endpoint requires authenticated access.\n', encoding='utf-8')
        self.plan['security'] = {
            'decision': 'TRIGGERED', 'reason': 'Task explicitly requires authenticated access.',
            'inspected_sources': {'TASK.md': digest(task)},
            'triggers': [{'kind': 'AUTH', 'source': 'TASK.md',
                          'evidence': 'requires authenticated access'}]}
        self.add_review('SECURITY_RED')

    def test_six_unique_completed_accepted_roles_pass_read_only_without_security(self):
        before = {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()}
        self.assertEqual(self.errors(), [])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()})

    def test_source_backed_security_trigger_requires_seventh_review(self):
        self.trigger_security()
        self.assertEqual(self.errors(), [])
        self.plan['reviews']['SECURITY_RED']['status'] = 'NOT_APPLICABLE'
        self.assertTrue(any('SECURITY_RED' in error for error in self.errors()))

    def test_security_receipt_must_bind_trigger_sources_beyond_common_candidate(self):
        self.trigger_security()
        self.change_receipt('SECURITY_RED', lambda receipt: receipt['reviewed_files'].pop('TASK.md'))
        self.assertTrue(any('current security inspection sources' in error for error in self.errors()))

    def test_missing_pending_and_self_check_core_roles_are_incomplete(self):
        original = copy.deepcopy(self.plan)
        for role in aggregate.CORE_ROLES:
            for value in (None, {'status': 'NOT_RUN'}, {'status': 'SELF_CHECK'}, {'status': 'COMPLETE'}):
                with self.subTest(role=role, value=value):
                    self.plan = copy.deepcopy(original)
                    self.plan['reviews'][role] = value
                    self.assertTrue(any(role in error for error in self.errors()))

    def test_one_worker_cannot_supply_two_independent_roles(self):
        self.add_review('ALGORITHM_RED', worker='/synthetic-final-fixture/CODE_RED')
        self.assertTrue(any('reused this worker_id' in error for error in self.errors()))

    def test_distinct_workers_cannot_relabel_one_report_or_copy_its_content(self):
        source_record = self.plan['reviews']['CODE_RED']['execution_receipt']
        source_receipt = json.loads((self.task / source_record['path']).read_text(encoding='utf-8'))
        original = copy.deepcopy(self.plan)
        self.change_receipt('ALGORITHM_RED', lambda receipt: receipt.update(report=source_receipt['report']))
        self.assertTrue(any('reused this review report path' in error for error in self.errors()))
        self.plan = original
        # Restore a separate target path after the first negative test's receipt edit.
        target_report = self.kit / 'run/reviews/FINAL-ALGORITHM_RED/report.md'
        target_report.write_bytes((self.task / source_receipt['report']['path']).read_bytes())
        self.change_receipt('ALGORITHM_RED', lambda receipt: receipt.update(report={
            'path': target_report.relative_to(self.task).as_posix(), 'sha256': digest(target_report)}))
        self.assertTrue(any('reused identical review report content' in error for error in self.errors()))

    def test_changed_config_and_stale_receipt_fail(self):
        config = self.task / 'config.json'
        before = config.read_bytes()
        config.write_text('{"capacity":900}', encoding='utf-8')
        self.assertTrue(any('file changed: config.json' in error for error in self.errors()))
        config.write_bytes(before)
        record = self.plan['reviews']['CODE_RED']['execution_receipt']
        path = self.task / record['path']
        path.write_text(path.read_text(encoding='utf-8') + '\n', encoding='utf-8')
        self.assertTrue(any('evidence bytes changed' in error for error in self.errors()))

    def test_algorithm_receipt_must_cover_current_config_even_if_other_files_match(self):
        self.change_receipt('ALGORITHM_RED', lambda receipt: receipt['reviewed_files'].pop('config.json'))
        self.assertTrue(any('ALGORITHM_RED: execution receipt does not cover' in error for error in self.errors()))

    def test_role_and_checkpoint_replay_are_rejected(self):
        self.change_receipt('CODE_RED', lambda receipt: receipt.update(role='EDGE_RED', checkpoint='FIRST_OUTPUT'))
        errors = self.errors()
        self.assertTrue(any('role does not match' in error for error in errors))
        self.assertTrue(any('checkpoint does not match' in error for error in errors))

    def test_security_unknown_contradiction_and_bad_source_evidence_fail(self):
        original = copy.deepcopy(self.plan)
        variants = [dict(decision='UNKNOWN'), dict(reason=''), dict(inspected_sources={}),
                    dict(decision='TRIGGERED'), dict(triggers=[{'kind': 'AUTH', 'source': 'TASK.md', 'evidence': 'No external'}])]
        for change in variants:
            with self.subTest(change=change):
                self.plan = copy.deepcopy(original)
                self.plan['security'].update(change)
                self.assertTrue(self.errors())
        self.plan = original
        self.trigger_security()
        triggered = copy.deepcopy(self.plan)
        for change in (dict(source='source.py'), dict(evidence=''),
                       dict(evidence='not actually in source'), dict(kind='BOGUS')):
            with self.subTest(trigger=change):
                self.plan = copy.deepcopy(triggered)
                self.plan['security']['triggers'][0].update(change)
                self.assertTrue(any('security trigger' in error for error in self.errors()))

    def test_security_not_applicable_must_be_explicit_and_cannot_hide_findings(self):
        del self.plan['reviews']['SECURITY_RED']
        self.assertTrue(any('explicitly be NOT_APPLICABLE' in error for error in self.errors()))
        self.plan['reviews']['SECURITY_RED'] = {'status': 'NOT_APPLICABLE', 'reason': 'Inspected.',
                                                'findings': [{'severity': 'P1'}]}
        self.assertTrue(any('cannot hide' in error for error in self.errors()))

    def test_p1_findings_and_duplicate_ids_block_acceptance_until_verified(self):
        finding = {'id': 'R1', 'severity': 'P1', 'status': 'OPEN',
                   'evidence': 'TASK.md requires a valid result.', 'verification': ''}
        entry = self.plan['reviews']['CODE_RED']
        entry['findings'] = [finding]
        self.assertTrue(any('P0/P1' in error for error in self.errors()))
        finding.update(status='FIXED', verification='Rechecked corrected result against original task.')
        self.assertEqual(self.errors(), [])
        entry['findings'].append(copy.deepcopy(finding))
        self.assertTrue(any('unique' in error for error in self.errors()))

    def test_cli_rejects_duplicate_json_and_is_read_only_on_valid_plan(self):
        self.path.write_text(json.dumps(self.plan), encoding='utf-8')
        command = [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'scripts/finals_review_check.py'),
                   '--kit', str(self.kit), '--checkpoint', 'FINAL']
        before = {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()}
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('not official score, submission or authenticated identity', result.stdout)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()})
        self.path.write_text(self.path.read_text(encoding='utf-8').replace('"version": 1', '"version": 0, "version": 1'), encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('duplicate JSON key', result.stdout)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_malformed_plan_and_nested_fields_fail_without_exception(self):
        for value in (None, [], 0, 'bad'):
            with self.subTest(plan=value):
                self.assertTrue(aggregate.check_reviews(value, self.kit, 'FINAL'))
        original = copy.deepcopy(self.plan)
        for key, value in (('required_scope', []), ('security', []), ('reviews', []), ('checkpoint', [])):
            with self.subTest(key=key):
                self.plan = copy.deepcopy(original)
                self.plan[key] = value
                self.assertTrue(self.errors())


if __name__ == '__main__':
    unittest.main()
