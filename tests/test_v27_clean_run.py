import copy
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'clean_run.py'
RUN = runpy.run_path(str(SCRIPT), run_name='test_clean')['clean_run']


class CleanReplayChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root, self.scratch = self.base / 'product', self.base / 'scratch'
        self.root.mkdir()
        self.scratch.mkdir()
        (self.root / 'data.txt').write_text('4')
        (self.root / 'main.py').write_text('import json\nfrom pathlib import Path\n'
                                          'value=int(Path("data.txt").read_text()) / 3\n'
                                          'Path("answer.json").write_text(json.dumps({"score":value}))\n')
        self.plan = {'execution_authorized': True, 'network_allowed': False, 'allow_setup': False,
                     'files': ['main.py'], 'data_files': ['data.txt'],
                     'command': ['{python}', 'main.py'], 'outputs': ['answer.json'], 'timeout_seconds': 5,
                     'json_tolerances': {'answer.json': {'expected': {'score': 1.333}, 'abs': 0.001}},
                     'submission_rules': {'files': [{'path': 'answer.json', 'format': 'json',
                                                    'required_fields': ['score'], 'ranges': {'score': {'min': 1}}}]}}

    def tearDown(self):
        for path in self.base.rglob('data.txt'):
            path.chmod(0o666)
        self.temp.cleanup()

    def test_replays_copied_inputs_and_records_actual_outputs(self):
        report = RUN(self.root, self.plan, self.scratch)
        self.assertEqual(report['status'], 'PASS', report)
        self.assertNotEqual(Path(report['replay_dir']), self.root)
        self.assertIn('-I', report['command'])
        self.assertEqual(report['input_sha256']['data.txt'], hashlib.sha256(b'4').hexdigest())
        self.assertEqual(report['exit_code'], 0)
        self.assertFalse((self.root / 'answer.json').exists())
        self.assertEqual((self.root / 'data.txt').read_text(), '4')

    def test_negative_hash_tolerance_and_missing_output(self):
        changed = copy.deepcopy(self.plan)
        changed['expected_hashes'] = {'answer.json': '0' * 64}
        self.assertEqual(RUN(self.root, changed, self.scratch)['status'], 'FAIL')
        changed = copy.deepcopy(self.plan)
        changed['json_tolerances']['answer.json']['abs'] = 0
        self.assertEqual(RUN(self.root, changed, self.scratch)['status'], 'FAIL')
        changed = copy.deepcopy(self.plan)
        changed['outputs'].append('missing.txt')
        self.assertEqual(RUN(self.root, changed, self.scratch)['status'], 'FAIL')

    def test_authorization_paths_and_setup_rejected(self):
        for change in ({'execution_authorized': False}, {'network_allowed': True}, {'allow_setup': True},
                       {'timeout_seconds': 0}, {'command': ['{python}', '-c', 'print(1)']},
                       {'files': ['../outside.py']}, {'command': ['{python}', '-m', 'pip', 'install', 'x']}):
            with self.assertRaises((ValueError, OSError)):
                RUN(self.root, dict(self.plan, **change), self.scratch)

    def test_malformed_csv_submission_returns_failed_replay(self):
        content = 'id,value\n1,"unterminated\n'
        (self.root / 'main.py').write_text('from pathlib import Path\nPath("answer.csv").write_bytes(%r)\n' % content.encode('utf-8'), encoding='utf-8')
        plan = copy.deepcopy(self.plan)
        plan.pop('json_tolerances')
        plan['outputs'] = ['answer.csv']
        plan['expected_hashes'] = {'answer.csv': hashlib.sha256(content.encode('utf-8')).hexdigest()}
        plan['submission_rules'] = {'files': [{'path': 'answer.csv', 'format': 'csv'}]}
        report = RUN(self.root, plan, self.scratch)
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['submission_check']['status'], 'FAIL')

    def test_timeout_and_bounded_logs(self):
        (self.root / 'main.py').write_text('import time\ntime.sleep(2)\n')
        changed = dict(self.plan, timeout_seconds=0.05)
        self.assertEqual(RUN(self.root, changed, self.scratch)['status'], 'FAIL')
        (self.root / 'main.py').write_text('print("x" * 100000)\n')
        report = RUN(self.root, dict(self.plan, max_log_bytes=64), self.scratch)
        self.assertEqual(report['status'], 'FAIL')
        self.assertLessEqual(report['stdout_bytes'], 64)

    def test_isolated_cli(self):
        plan = self.base / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        result = subprocess.run([sys.executable, '-I', str(SCRIPT), '--root', str(self.root),
                                 '--plan', str(plan), '--scratch', str(self.scratch)],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
