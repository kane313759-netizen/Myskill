import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'submit_check.py'
CHECK = runpy.run_path(str(SCRIPT), run_name='test_submit')['check_submission']


class SubmissionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'answer.csv').write_text('id,kind,cost\na,keep,2\nb,keep,3\n', encoding='utf-8')
        self.rules = {'files': [{'path': 'answer.csv', 'format': 'csv', 'columns': ['id', 'kind', 'cost'],
                                'row_count': 2, 'unique_keys': ['id'], 'allowed_values': {'kind': ['keep']},
                                'ranges': {'cost': {'min': 0, 'max': 3}}}],
                      'aggregate_constraints': [{'path': 'answer.csv', 'column': 'cost', 'op': 'sum_le', 'value': 5}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_contract_and_negative_control(self):
        self.assertEqual(CHECK(self.root, self.rules)['status'], 'PASS')
        changed = copy.deepcopy(self.rules)
        changed['aggregate_constraints'][0]['value'] = 4
        self.assertEqual(CHECK(self.root, changed)['status'], 'FAIL')
        (self.root / 'answer.csv').write_text('id,kind,cost\na,keep,2\na,keep,3\n', encoding='utf-8')
        self.assertEqual(CHECK(self.root, self.rules)['status'], 'FAIL')

    def test_malformed_json_nonfinite_and_duplicate_keys(self):
        rule = {'files': [{'path': 'answer.json', 'format': 'json'}]}
        for content in ('{"x":NaN}', '{"x":1,"x":2}', '{'):
            (self.root / 'answer.json').write_text(content)
            self.assertEqual(CHECK(self.root, rule)['status'], 'FAIL')

    def test_path_budget_and_missing_columns(self):
        for rules in ({'files': [{'path': '../outside.json'}]},
                      dict(self.rules, max_total_bytes=2), dict(self.rules, max_file_bytes=2)):
            self.assertEqual(CHECK(self.root, rules)['status'], 'FAIL')
        (self.root / 'answer.csv').write_text('id,cost\na,2\n', encoding='utf-8')
        self.assertEqual(CHECK(self.root, self.rules)['status'], 'FAIL')

    def test_json_allowed_values_preserve_types(self):
        (self.root / 'answer.json').write_text('[{"value":true}]')
        rule = {'files': [{'path': 'answer.json', 'format': 'json', 'allowed_values': {'value': [1]}}]}
        self.assertEqual(CHECK(self.root, rule)['status'], 'FAIL')

    def test_isolated_cli_and_no_implicit_inventory(self):
        (self.root / 'unrelated.csv').write_text('broken')
        path = self.root / 'rules.json'
        path.write_text(json.dumps(self.rules))
        result = subprocess.run([sys.executable, '-I', str(SCRIPT), '--root', str(self.root), '--rules', str(path)],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual([item['path'] for item in report['artifacts']], ['answer.csv'])


if __name__ == '__main__':
    unittest.main()
