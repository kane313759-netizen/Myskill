"""Missing/stale/wrong-worker observations must not masquerade as completed review."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from review_fixture import make_execution

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_execution', ROOT / 'scripts/review_execution.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewExecutionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='review-execution-')
        self.addCleanup(temp.cleanup)
        self.task = Path(temp.name)
        self.kit = self.task / '.hackathon-kit'
        (self.kit / 'run').mkdir(parents=True)
        self.report_path = '.hackathon-kit/run/EDGE_REPORT.md'
        (self.task / self.report_path).write_text('Actual test report fixture: limit checked.', encoding='utf-8')
        (self.task / 'source.py').write_text('print(1)\n', encoding='utf-8')
        self.receipt = make_execution(self.task, 'EDGE_RED', 'FINAL', self.report_path,
                                     {'source.py': hashlib.sha256((self.task / 'source.py').read_bytes()).hexdigest()})

    def errors(self):
        return review.execution_errors(self.receipt, self.kit, 'EDGE_RED', 'FINAL')

    def change_event(self, phase, change):
        record = self.receipt['observations'][phase]
        path = self.task / record['path']
        data = json.loads(path.read_text(encoding='utf-8'))
        change(data)
        path.write_text(json.dumps(data), encoding='utf-8')
        record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_complete_record_passes_read_only_and_changed_source_fails(self):
        before = {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()}
        self.assertEqual(self.errors(), [])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()})
        (self.task / 'source.py').write_text('print(2)\n', encoding='utf-8')
        self.assertTrue(any('reviewed file changed' in e for e in self.errors()))

    def test_missing_phase_wrong_worker_and_empty_raw_fail(self):
        original = copy.deepcopy(self.receipt)
        for phase in review.PHASES:
            self.receipt = copy.deepcopy(original)
            self.receipt['observations'].pop(phase)
            self.assertTrue(self.errors())
        self.receipt = original
        self.change_event('COMPLETED', lambda e: e.update(worker_id='/different/worker'))
        self.assertTrue(any('worker does not match' in e for e in self.errors()))
        self.change_event('COMPLETED', lambda e: e.update(worker_id=self.receipt['worker_id'], raw={}))
        self.assertTrue(any('actual tool response' in e for e in self.errors()))

    def test_raw_response_must_identify_worker(self):
        self.change_event('RUNNING', lambda e: e.update(raw={'worker_id': '/another/worker'}))
        self.assertTrue(any('does not identify' in e for e in self.errors()))

    def test_time_order_timezone_and_malformed_time_fail(self):
        for value in ('2026-11-08T00:00:00', 123, 'bad-time', '2026-11-07T00:00:00+00:00'):
            with self.subTest(value=value):
                self.change_event('COMPLETED', lambda e: e.update(observed_at=value))
                self.assertTrue(self.errors())

    def test_report_change_and_duplicate_observation_fail(self):
        (self.task / self.report_path).write_text('Changed report without a recheck.', encoding='utf-8')
        self.assertTrue(any('evidence bytes changed' in e for e in self.errors()))
        self.receipt['observations']['RUNNING'] = self.receipt['observations']['LAUNCHED']
        self.assertTrue(any('own retained record' in e for e in self.errors()))

    def test_self_check_pending_and_checkpoint_replay_fail(self):
        original = copy.deepcopy(self.receipt)
        for key, value in (('status', 'LAUNCHED'), ('context_mode', 'SELF_CHECK'),
                           ('checkpoint', 'CP1'), ('role', 'CODE_RED'), ('worker_id', 'UNKNOWN')):
            with self.subTest(key=key):
                self.receipt = copy.deepcopy(original)
                self.receipt[key] = value
                self.assertTrue(self.errors())

    def test_external_paths_rejected(self):
        for path in ('../private.json', str(self.task / 'source.py'), 'C:\\private.json'):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    review.read_local(self.task, path)

    def test_symlink_paths_rejected_when_supported(self):
        source, link = self.task / 'source.py', self.task / 'link.py'
        try:
            link.symlink_to(source)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            review.read_local(self.task, 'link.py')

    def test_native_exact_identity_rejects_prefix_and_incidental_mentions(self):
        worker = self.receipt['worker_id']
        for raw in ({'worker_id': worker + '-other', 'status': 'completed'},
                    {'worker_id': '/different', 'message': worker, 'status': 'completed'},
                    {'worker_id': worker, 'agent_name': '/different', 'status': 'completed'},
                    {'worker_id': '/different', 'agents': [{'agent_name': worker, 'agent_status': 'running'}]},
                    {'message': worker + ' completed'}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                review.native_state(raw, worker, 'status_tool')

    def test_failed_pending_and_unknown_native_states_cannot_prove_completion(self):
        for status in ('FAILED', 'cancelled', 'NOT_RUN', 'queued', 'pending', 'unknown'):
            with self.subTest(status=status):
                self.change_event('COMPLETED', lambda e: e.update(raw={
                    'worker_id': self.receipt['worker_id'], 'status': status}))
                self.assertTrue(any('cannot establish COMPLETED' in e for e in self.errors()))

    def test_real_shaped_launch_running_and_fast_completion_are_supported(self):
        worker = self.receipt['worker_id']
        self.assertEqual(review.native_state({'task_name': worker}, worker, 'collaboration.spawn_agent'), 'launched')
        self.assertEqual(review.native_state({'agents': [{'agent_name': worker, 'agent_status': 'running'}]}, worker, 'collaboration.list_agents'), 'running')
        self.assertEqual(review.native_state({'agent_name': worker, 'agent_status': {'completed': 'Review finished.'}}, worker, 'collaboration.list_agents'), 'completed')
        for phase in ('RUNNING', 'COMPLETED'):
            self.change_event(phase, lambda e: e.update(raw={
                'task_name': worker, 'message_type': 'FINAL_ANSWER', 'text': 'Actual final message fixture.'}))
        self.assertEqual(self.errors(), [])

    def test_native_failure_cannot_be_hidden_by_final_message_marker(self):
        worker = self.receipt['worker_id']
        with self.assertRaises(ValueError):
            review.native_state({'worker_id': worker, 'message_type': 'FINAL_ANSWER',
                                 'text': 'failed', 'status': 'FAILED'}, worker, 'status_tool')

    def test_duplicate_json_is_rejected_at_every_nested_depth(self):
        for text in ('{"status":"NOT_RUN","status":"COMPLETE"}',
                     '{"execution":null,"execution":{}}',
                     '{"event":{"phase":"NOT_RUN","phase":"RUNNING"}}'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                review.load_json(text)

    @unittest.skipUnless(os.name == 'nt', 'Windows junction check')
    def test_windows_junction_cannot_escape_physical_notes_scope(self):
        outside = self.task / 'outside-run'
        outside.mkdir()
        (outside / 'event.json').write_text('{}', encoding='utf-8')
        link = self.kit / 'run/junction'
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
        if result.returncode:
            self.skipTest('junction creation unavailable')
        try:
            with self.assertRaisesRegex(ValueError, 'physical kit run|reparse/junction'):
                review.read_local(self.task, '.hackathon-kit/run/junction/event.json', notes_only=True)
        finally:
            link.rmdir()

    def test_cli_rejects_launch_only_and_accepts_complete_record_without_writes(self):
        receipt = self.kit / 'run/execution.json'
        receipt.write_text(json.dumps(self.receipt), encoding='utf-8')
        cmd = [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'scripts/review_execution.py'),
               '--kit', str(self.kit), '--receipt', '.hackathon-kit/run/execution.json',
               '--role', 'EDGE_RED', '--checkpoint', 'FINAL']
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('not authenticated identity', result.stdout)
        self.receipt['observations'].pop('COMPLETED')
        receipt.write_text(json.dumps(self.receipt), encoding='utf-8')
        before = {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()}
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.task.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
