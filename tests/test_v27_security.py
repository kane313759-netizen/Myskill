import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'security_check.py'
CHECK = runpy.run_path(str(SCRIPT), run_name='test_security')['check_security']


class SecurityChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_secret_pii_and_alias_calls_without_value_disclosure(self):
        secret = 'ghp_' + 'A' * 36
        (self.root / 'product.py').write_text('import subprocess as sp\nfrom pickle import loads as load\n'
                                           'token = "' + secret + '"\nidentifier="900101-1234567"\n'
                                           'sp.run(["echo"], shell=True)\nload(data)\n')
        report = CHECK(self.root, {'files': ['product.py']})
        categories = {item['category'] for item in report['findings']}
        self.assertTrue({'secret_token', 'personal_id', 'subprocess_shell_true', 'untrusted_deserialization_review'} <= categories)
        self.assertEqual(report['status'], 'FAIL')
        self.assertNotIn(secret, json.dumps(report))
        self.assertNotIn('900101-1234567', json.dumps(report))

    def test_explicit_scope_and_evidenced_disposition(self):
        (self.root / 'safe.py').write_text('print("ok")\n')
        (self.root / 'other.py').write_text('eval(input())\n')
        self.assertEqual(CHECK(self.root, {'files': ['safe.py']})['status'], 'PASS')
        plan = {'files': ['other.py'], 'dispositions': [{'path': 'other.py', 'line': 1,
                'category': 'dynamic_code_execution', 'reason': 'explicitly reviewed fixture',
                'evidence': 'fixture is isolated and never imported'}]}
        report = CHECK(self.root, plan)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['findings'][0]['status'], 'DISPOSITIONED')
        plan['dispositions'][0]['line'] = 2
        self.assertEqual(CHECK(self.root, plan)['status'], 'FAIL')

    def test_quoted_configuration_keys_and_prefixed_names(self):
        (self.root / 'config.json').write_text('{"OPENAI_API_KEY":"sensitive-example-12345"}')
        report = CHECK(self.root, {'files': ['config.json']})
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['findings'][0]['category'], 'hardcoded_credential_review')
        self.assertNotIn('sensitive-example-12345', json.dumps(report))

    def test_bounds_paths_and_syntax_triage(self):
        (self.root / 'broken.py').write_text('print(\n')
        self.assertEqual(CHECK(self.root, {'files': ['broken.py']})['status'], 'FAIL')
        self.assertEqual(CHECK(self.root, {'files': ['../outside.py']})['status'], 'FAIL')
        self.assertEqual(CHECK(self.root, {'files': ['broken.py'], 'max_file_bytes': 1})['status'], 'FAIL')
        with self.assertRaises(ValueError):
            CHECK(self.root, {'files': ['broken.py'], 'dispositions': [{'path': 'broken.py'}]})

    def test_isolated_cli(self):
        (self.root / 'safe.py').write_text('print(1)\n')
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps({'files': ['safe.py']}))
        result = subprocess.run([sys.executable, '-I', str(SCRIPT), '--root', str(self.root), '--plan', str(plan)],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
