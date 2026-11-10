"""r4-3.2 regression: data_audit handles multi-sheet workbooks and multi-array JSON without failing the whole audit."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
try:
    import openpyxl  # noqa: F401
    HAVE_OPENPYXL = True
except ImportError:
    HAVE_OPENPYXL = False


def audit(root, files):
    plan = pathlib.Path(root) / 'plan.json'
    plan.write_text(json.dumps({'files': files}, ensure_ascii=False), encoding='utf-8')
    out = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/data_audit.py'), '--root', str(root), '--plan', str(plan)],
                         capture_output=True, text=True, encoding='utf-8')
    return json.loads(out.stdout)


def artifact(result, path):
    return [a for a in result['files'] if a.get('path') == path][0]


class RegressionR432(unittest.TestCase):
    @unittest.skipUnless(HAVE_OPENPYXL, 'openpyxl not installed')
    def test_01_multi_sheet_workbook_audits_tables_and_skips_layout_sheets(self):
        import openpyxl
        with tempfile.TemporaryDirectory() as td:
            wb = openpyxl.Workbook()
            plain = wb.active
            plain.title = 'plain'
            plain.append(['lot', 'yield'])
            for i in range(5):
                plain.append([f'L{i}', 90 + i])
            second = wb.create_sheet('second')
            second.append(['tool', 'count'])
            second.append(['T1', 3])
            layout = wb.create_sheet('layout')
            layout.append(['주간 보고', None, None])
            layout.merge_cells('A1:C1')
            layout.append(['항목', '값', '비고'])
            wb.save(str(pathlib.Path(td) / 'book.xlsx'))
            result = audit(td, ['book.xlsx'])
            self.assertEqual(result['errors'], [])
            self.assertNotEqual(result['status'], 'FAIL')
            item = artifact(result, 'book.xlsx')
            self.assertEqual(sorted(t['sheet'] for t in item['tables']), ['plain', 'second'])
            self.assertEqual([s['sheet'] for s in item['skipped_sheets']], ['layout'])
            self.assertEqual(item['status'], 'UNVERIFIED')
            explicit = artifact(audit(td, [{'path': 'book.xlsx', 'sheet': 'plain'}]), 'book.xlsx')
            self.assertEqual([t['sheet'] for t in explicit['tables']], ['plain'])
            wrong = audit(td, [{'path': 'book.xlsx', 'sheet': 'missing'}])
            self.assertEqual(wrong['status'], 'FAIL')
            self.assertIn('"sheet": "<sheet name>"', wrong['errors'][0]['error'])

    def test_02_json_with_several_record_arrays_is_audited_per_array(self):
        with tempfile.TemporaryDirectory() as td:
            data = {'products': [{'id': 'P1', 'grade': 'A'}, {'id': 'P2', 'grade': 'B'}],
                    'customers': [{'id': 'C1', 'region': 'X'}]}
            (pathlib.Path(td) / 'info.json').write_text(json.dumps(data), encoding='utf-8')
            result = audit(td, ['info.json'])
            self.assertEqual(result['errors'], [])
            item = artifact(result, 'info.json')
            self.assertEqual(sorted(t['sheet'] for t in item['tables']), ['/customers', '/products'])
            self.assertEqual(item['rows_examined'], 3)
            explicit = artifact(audit(td, [{'path': 'info.json', 'records_key': '/products'}]), 'info.json')
            self.assertEqual(explicit['rows_examined'], 2)


if __name__ == '__main__':
    unittest.main()
