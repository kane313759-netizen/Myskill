"""Bounded regressions for malformed inventory metadata and streamed test logs."""

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("test_summary_helper", SCRIPTS / "test_summary.py")
test_summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_summary)


class InventoryEdgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="inventory-edges-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_scan(self, *options):
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-B", str(SCRIPTS / "env_scan.py"),
             "--root", str(self.root), *options], capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        return result.stdout.decode("ascii")

    def test_deep_bounded_manifest_reports_unreadable_and_retains_inventory(self):
        (self.root / "package.json").write_text(
            '{"x":' + "[" * 15000 + "0" + "]" * 15000 + "}", encoding="ascii",
        )
        (self.root / "Cargo.toml").write_text("", encoding="ascii")
        output = self.run_scan()
        self.assertIn('FOUND\t"Cargo.toml"', output)
        self.assertIn('FOUND\t"package.json"', output)
        self.assertIn("cannot inspect script names: RecursionError", output)
        self.assertIn("SCANNED\t", output)

    def test_surrogate_script_key_is_escaped_without_losing_the_inventory(self):
        (self.root / "package.json").write_text(
            '{"scripts":{"\\ud800":"SECRET_COMMAND"}}', encoding="ascii",
        )
        output = self.run_scan()
        names = next(line.split("\t", 1)[1] for line in output.splitlines()
                     if line.startswith("SCRIPT_NAMES\t"))
        self.assertEqual(json.loads(names), ["\ud800"])
        self.assertNotIn("SECRET_COMMAND", output)
        self.assertIn("SCANNED\t", output)
        bounded = self.run_scan("--max-output-bytes", "320")
        self.assertLessEqual(len(bounded.encode("ascii")), 320)
        self.assertIn("TRUNCATED", bounded)

    @unittest.skipIf(os.name == "nt", "undecodable POSIX filename bytes")
    def test_undecodable_directory_name_is_preserved_as_json_escape(self):
        dirname = os.fsdecode(b"directory-\xff")
        directory = self.root / dirname
        directory.mkdir()
        (directory / "README.md").write_text("", encoding="ascii")
        output = self.run_scan()
        found = [json.loads(line.split("\t", 1)[1]) for line in output.splitlines()
                 if line.startswith("FOUND\t")]
        self.assertIn(dirname + "/README.md", found)


class TestSummaryEdgeTests(unittest.TestCase):
    def summary(self, content):
        return list(test_summary.failure_like_lines(io.StringIO(content)))

    def test_zero_failure_phrase_split_at_each_boundary_position(self):
        phrase = " Failed: 0"
        for split in range(1, len(phrase)):
            with self.subTest(split=split):
                content = "x" * (65536 - split) + phrase + "\n"
                self.assertEqual(self.summary(content), [])
        self.assertEqual(self.summary("x" * (65536 - 7) + " Failed" + ": 0"), [])
        self.assertEqual(self.summary("Failed:" + " " * 200000 + "0\n"), [])

    def test_long_whitespace_preserves_physical_line_start_only(self):
        for failure in ("not ok 1 - example", "FAIL: example", "--- FAIL: example"):
            with self.subTest(failure=failure):
                self.assertEqual(len(self.summary(" " * 200000 + failure + "\n")), 1)
                self.assertEqual(self.summary("x" * 200000 + " " + failure + "\n"), [])

    def test_streamed_mixed_counts_boundary_tokens_and_eof(self):
        content = ("x" * (65536 - 7) + " AssertionError " + "x" * 100000 + "\n"
                   + "Failed:" + " " * 200000 + "0, Errors: 1\n"
                   + "not ok 3 - final record")
        excerpts = self.summary(content)
        self.assertEqual(len(excerpts), 3)
        self.assertTrue(all(len(excerpt) <= 1000 for excerpt in excerpts))

    def test_reader_requests_only_bounded_chunks(self):
        class BoundedReader(io.StringIO):
            def readline(self, size=-1):
                self.assert_size = size
                if size != 65536:
                    raise AssertionError("unbounded test-log read")
                return super().readline(size)

        handle = BoundedReader(" " * 1000000 + "not ok 1 - example\n")
        self.assertEqual(len(list(test_summary.failure_like_lines(handle))), 1)
        self.assertEqual(handle.assert_size, 65536)


if __name__ == "__main__":
    unittest.main()
