"""Regression coverage for real data/helper failure cases; no network or task repo."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import data_io


class DataToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, name, content):
        path = self.root / name
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    def run_tool(self, script, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                              capture_output=True, text=True, timeout=30)

    def rows(self, path, **options):
        return list(data_io.tables(path, 100000, 1024 * 1024, **options))[0][1]

    def test_existing_cp949_ci_case(self):
        path = self.fixture("cp949.csv", "id,대기시간\n001,10\n002,180\n".encode("cp949"))
        for script in ("profile_data.py", "sanity_check.py"):
            result = self.run_tool(script, path, "--max-rows", 10)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("대기시간", result.stdout)
            self.assertIn("180", result.stdout)

    def test_utf8_character_crosses_encoding_sample_boundary(self):
        path = self.fixture("split.csv", b"value\n" + b"a\n" * 65532 + b"x" + "한\n".encode())
        self.assertEqual(data_io.choose_encoding(path), "utf-8-sig")
        self.assertEqual(self.rows(path)[-1], {"value": "x한"})

    def test_ascii_prefix_does_not_prevent_late_cp949_fallback(self):
        path = self.fixture("late.csv", b"value\n" + (b"a" * 99 + b"\n") * 1400 + "한글\n".encode("cp949"))
        rows = self.rows(path)
        self.assertEqual(len(rows), 1401)
        self.assertEqual(rows[-1], {"value": "한글"})

    def test_encoding_sample_read_is_bounded(self):
        opened = mock.mock_open(read_data=b"ascii")
        with mock.patch.object(Path, "open", opened), mock.patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read")):
            self.assertEqual(data_io.choose_encoding(Path("large.csv")), "utf-8-sig")
        opened().read.assert_called_once_with(data_io.SAMPLE_BYTES)

    def test_explicit_encoding_and_incorrect_encoding_error(self):
        path = self.fixture("latin.csv", "city,value\nZürich,12\n".encode("latin-1"))
        self.assertEqual(self.rows(path, encoding="latin-1")[0]["city"], "Zürich")
        result = self.run_tool("profile_data.py", path, "--encoding", "utf-8")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR", result.stdout)

    def test_duplicate_and_ragged_csv_are_diagnosed(self):
        cases = (("a,a\n1,2\n", "Duplicate"), ("a,b\n1,2,3\n", "expected 2 fields"),
                 ("a,b\n1\n", "expected 2 fields"), (",b\n1,2\n", "Empty column"))
        for content, diagnostic in cases:
            path = self.fixture("bad.csv", content)
            for script in ("profile_data.py", "sanity_check.py"):
                result = self.run_tool(script, path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(diagnostic, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_unclosed_csv_quote_is_an_error(self):
        path = self.fixture("quote.csv", 'value\n"unterminated\n')
        for script in ("profile_data.py", "sanity_check.py"):
            result = self.run_tool(script, path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected end of data", result.stdout + result.stderr)

    def test_row_cap_does_not_parse_an_additional_record(self):
        path = self.fixture("cap.csv", "a,b\n1,2\n3,4,5\n")
        rows = list(data_io.tables(path, 1, 1000))[0][1]
        self.assertEqual(rows, [{"a": "1", "b": "2"}])

    def test_limits_must_be_positive(self):
        path = self.fixture("a.csv", "value\n1\n")
        for script in ("profile_data.py", "sanity_check.py"):
            for flag in ("--max-rows", "--max-json-bytes"):
                for value in (0, -1):
                    self.assertNotEqual(self.run_tool(script, path, flag, value).returncode, 0)
        self.assertNotEqual(self.run_tool("profile_data.py", path, "--max-files", 0).returncode, 0)
        self.assertNotEqual(self.run_tool("profile_data.py", path, path, "--max-files", 1).returncode, 0)

    def test_json_size_limit_and_record_cap(self):
        path = self.fixture("rows.json", '[{"a":1},{"a":2}]')
        self.assertEqual(list(data_io.tables(path, 1, 100))[0][1], [{"a": 1}])
        for script in ("profile_data.py", "sanity_check.py"):
            result = self.run_tool(script, path, "--max-json-bytes", 5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("size limit", result.stdout + result.stderr)

    def test_json_empty_metadata_does_not_shadow_records(self):
        path = self.fixture("wrapped.json", '{"metadata":[],"records":[{"score":7}]}')
        self.assertEqual(self.rows(path), [{"score": 7}])
        self.assertEqual(self.rows(path, records_key="metadata"), [])

    def test_ambiguous_record_arrays_require_explicit_path(self):
        path = self.fixture("ambiguous.json", '{"left":[{"a":1}],"right":[{"a":2}]}')
        for script in ("profile_data.py", "sanity_check.py"):
            result = self.run_tool(script, path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--records-key", result.stdout + result.stderr)
            self.assertIn("/left", result.stdout + result.stderr)
        self.assertEqual(self.rows(path, records_key="/right"), [{"a": 2}])

    def test_json_dot_path_pointer_and_escaped_key(self):
        path = self.fixture("nested.json", '{"data":{"items":[{"a":3}]},"a/b":[{"a":4}]}')
        self.assertEqual(self.rows(path, records_key="data.items"), [{"a": 3}])
        self.assertEqual(self.rows(path, records_key="/a~1b"), [{"a": 4}])
        with self.assertRaisesRegex(ValueError, "not found"):
            self.rows(path, records_key="missing")

    def test_json_late_key_backfills_missing_rows(self):
        path = self.fixture("sparse.json", '[{"a":1},{"b":2}]')
        result = self.run_tool("profile_data.py", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("COL\tb\tblank=1\tnonblank=1", result.stdout)

    def test_metric_names_are_not_identifier_substring_matches(self):
        fields = ["customer_wait_time", "employee_utilization", "order_qty", "invoice_amount",
                  "account_balance", "status_code_count", "encode_time"]
        path = self.fixture("metrics.csv", ",".join(fields) + "\n" + ",".join(["10"] * len(fields)) + "\n")
        result = self.run_tool("sanity_check.py", path)
        for name in fields:
            self.assertIn(f"NUM\t{name}\t", result.stdout)
            self.assertFalse(data_io.id_like(name))

    def test_identifiers_preserve_leading_zeros_and_skip_numeric_stats(self):
        path = self.fixture("ids.csv", "customer_id,unknown,value\n001,0002,3\n002,0003,4\n")
        result = self.run_tool("profile_data.py", path)
        for name in ("customer_id", "unknown"):
            line = next(line for line in result.stdout.splitlines() if line.startswith(f"COL\t{name}\t"))
            self.assertIn("numeric_skipped=id_like", line)
            self.assertNotIn("min=", line)
        self.assertIn("001", result.stdout)
        result = self.run_tool("sanity_check.py", path, "--include-id-like")
        self.assertIn("NUM\tcustomer_id\t", result.stdout)

    def test_null_strings_are_only_missing_when_explicit(self):
        path = self.fixture("null.csv", "value\nNULL\n0\n")
        default = self.run_tool("profile_data.py", path)
        configured = self.run_tool("profile_data.py", path, "--null-token", "NULL")
        self.assertIn("blank=0\tnonblank=2", default.stdout)
        self.assertIn("blank=1\tnonblank=1", configured.stdout)
        self.assertFalse(data_io.is_blank("null"))
        self.assertIsNone(data_io.as_num(True))
        self.assertEqual(data_io.as_num("1,234.5"), 1234.5)
        self.assertIsNone(data_io.as_num("1,2"))
        self.assertIsNone(data_io.as_num("NaN"))

    def test_multiple_files_continue_but_aggregate_failure(self):
        bad = self.fixture("bad.csv", "a,a\n1,2\n")
        good = self.fixture("good.csv", "value\n2\n")
        result = self.run_tool("profile_data.py", bad, good)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"FILE\t{good}", result.stdout)
        self.assertNotEqual(self.run_tool("profile_data.py", self.root).returncode, 0)

    def test_finite_numeric_extremes_have_finite_averages(self):
        path = self.fixture("extremes.csv", "value\n1e308\n1e308\n")
        for script in ("profile_data.py", "sanity_check.py"):
            result = self.run_tool(script, path)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("avg=1e+308", result.stdout)
            self.assertNotIn("avg=inf", result.stdout)
        self.assertEqual(data_io.mean([1e308, -1e308]), 0)

    @unittest.skipUnless(importlib.util.find_spec("openpyxl"), "optional openpyxl not installed")
    def test_xlsx_explicit_sheet_all_sheets_and_close(self):
        import openpyxl
        path = self.root / "sheets.xlsx"
        workbook = openpyxl.Workbook()
        workbook.active.title = "empty"
        workbook.active.append(["value"])
        actual = workbook.create_sheet("actual")
        actual.append(["value"])
        actual.append([42])
        workbook.save(path)
        workbook.close()
        for script in ("profile_data.py", "sanity_check.py"):
            result = self.run_tool(script, path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Multiple sheets", result.stdout + result.stderr)
            result = self.run_tool(script, path, "--sheet", "actual")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("42", result.stdout)
            self.assertIn("SHEET\tactual", result.stdout)
            result = self.run_tool(script, path, "--all-sheets")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("SHEET\tempty", result.stdout)
            self.assertIn("SHEET\tactual", result.stdout)
            listing = self.run_tool(script, path, "--list-sheets")
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertIn("actual", listing.stdout)
        fake = mock.MagicMock()
        fake.sheetnames = ["one", "two"]
        with mock.patch.object(data_io, "_open_workbook", return_value=fake):
            with self.assertRaises(ValueError):
                list(data_io.tables(path, 10, 1000))
        fake.close.assert_called_once()

    def test_test_summary_zero_mixed_go_and_output_bounds(self):
        path = self.fixture("test.log", "23 passed, 0 failed, 0 errors\nFailed: 0, Passed: 10\n")
        self.assertIn("FAILURE_LIKE_LINES\t0", self.run_tool("test_summary.py", path).stdout)
        path.write_text("1 failed, 23 passed, 0 errors\n--- FAIL: TestExample (0.00s)\nFAIL\texample/pkg\n", encoding="utf-8")
        result = self.run_tool("test_summary.py", path)
        self.assertEqual(result.returncode, 0)  # triage does not replace the real test command
        self.assertIn("FAILURE_LIKE_LINES\t3", result.stdout)
        path.write_text(("AssertionError " + "x" * 10000 + "\n") * 100, encoding="utf-8")
        result = self.run_tool("test_summary.py", path)
        self.assertIn("FAILURE_LIKE_LINES\t40", result.stdout)
        self.assertLess(len(result.stdout), 42000)
        self.assertIn("omitted", result.stdout)

        path.write_text("Failed: 0, Errors: 1\n", encoding="utf-8")
        self.assertIn("FAILURE_LIKE_LINES\t1", self.run_tool("test_summary.py", path).stdout)

    def test_test_summary_detects_split_failure_token_once_per_line(self):
        path = self.fixture("long.log", "x" * (65536 - 7) + " AssertionError " + "x" * 100000 + "\n"
                            + "AssertionError " * 10000 + "\n")
        result = self.run_tool("test_summary.py", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FAILURE_LIKE_LINES\t2", result.stdout)


if __name__ == "__main__":
    unittest.main()
