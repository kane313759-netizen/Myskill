import os
import sys
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


env_scan = module("env_scan")
package_release = module("package_release")


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text=""):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_nested_languages_and_grading_commands_are_found_without_secret_contents(self):
        self.write("backend/Cargo.toml", "SECRET_RUST_SOURCE")
        self.write("frontend/package.json", json.dumps({"scripts": {"test": "echo SECRET_COMMAND", "build": "run"}}))
        self.write("grader/check_submission.sh", "SECRET_GRADER_SOURCE")
        self.write("jvm/pom.xml")
        self.write("native/CMakeLists.txt")
        self.write("go/go.mod")
        self.write(".env", "SECRET_ENV")
        self.write(".env.example", "SECRET_EXAMPLE_ENV")
        paths, counts, notices = env_scan.inventory(self.root)
        for name in ["backend/Cargo.toml", "frontend/package.json", "grader/check_submission.sh", "jvm/pom.xml", "native/CMakeLists.txt", "go/go.mod"]:
            self.assertIn(name, paths)
        output = env_scan.render(self.root, paths, counts, notices, 10000)
        self.assertIn('SCRIPT_NAMES\t["build", "test"]', output)
        self.assertNotIn("SECRET", output)
        self.assertNotIn("port/process", output)

    def test_depth_pruning_and_symlinks(self):
        self.write("a/b/Cargo.toml")
        self.write("a/b/c/go.mod")
        self.write("node_modules/pkg/package.json")
        self.write(".hackathon-kit/scripts/run.py")
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        Path(outside.name, "package.json").write_text("{}")
        try:
            (self.root / "linked").symlink_to(outside.name, target_is_directory=True)
        except (OSError, NotImplementedError):
            pass
        paths, _, _ = env_scan.inventory(self.root)
        self.assertEqual(paths, ["a/b/Cargo.toml"])

    def test_scan_and_output_limits(self):
        for index in range(30):
            self.write("folder%02d/package.json" % index, "{}")
        _, counts, notices = env_scan.inventory(self.root, max_dirs=2)
        self.assertLessEqual(counts["directories"], 2)
        self.assertIn("directory budget reached", notices)
        paths, counts, notices = env_scan.inventory(self.root, max_entries=3)
        self.assertLessEqual(counts["entries"], 3)
        self.assertIn("entry budget reached", notices)
        output = env_scan.render(self.root, paths, counts, notices, 128)
        self.assertLessEqual(len(output.encode("utf-8")), 128)
        self.assertIn("TRUNCATED", output)

    def test_large_package_json_is_not_fully_read(self):
        path = self.write("package.json", " " * 70000)
        names, warning = env_scan.script_names(path)
        self.assertIsNone(names)
        self.assertIn("read limit", warning)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "release.zip"
        for name in package_release.REQUIRED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("official policy\n" if name == "EXAM_POLICY.md" else "kit source\n")

    def write(self, name, content="source\n"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_direct_root_and_deterministic_payload_without_runtime_archives_or_secrets(self):
        self.write("scripts/example.py")
        self.write("tests/test_example.py")
        self.write(".github/workflows/validate.yml")
        self.write(".env", "SECRET")
        self.write("scripts/__pycache__/example.pyc", "CACHE")
        self.write(".hackathon-kit/run/HUMAN_JUDGMENT.md", "TASK_DETAILS")
        self.write("Myskill-review.zip", "NESTED_ARCHIVE")
        first = package_release.build(self.root, self.output)
        binary = self.output.read_bytes()
        package_release.build(self.root, self.output)
        self.assertEqual(binary, self.output.read_bytes())
        self.assertGreater(first["files"], 0)
        with zipfile.ZipFile(self.output) as archive:
            names = set(archive.namelist())
            self.assertIn("install.sh", names)
            self.assertIn(".agents/skills/hackathon-orchestrator/SKILL.md", names)
            self.assertIn("tests/test_example.py", names)
            self.assertEqual(archive.read("EXAM_POLICY.md"), (self.root / "EXAM_POLICY.md").read_bytes())
            self.assertFalse(any(name.endswith((".zip", ".pyc")) for name in names))
            self.assertFalse(any(".hackathon-kit" in name or ".env" in name for name in names))

    def test_git_checkout_omits_untracked_files_by_default_and_can_include_new_source(self):
        removed = self.write("scripts/removed.py")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        removed.unlink()
        self.write("scripts/new_tool.py")
        self.write("tests/fixture-secret.txt", "SECRET")
        package_release.build(self.root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertNotIn("scripts/new_tool.py", archive.namelist())
            self.assertNotIn("scripts/removed.py", archive.namelist())
        package_release.build(self.root, self.output, include_untracked=True)
        with zipfile.ZipFile(self.output) as archive:
            self.assertIn("scripts/new_tool.py", archive.namelist())
            self.assertNotIn("tests/fixture-secret.txt", archive.namelist())

    def test_non_ascii_checkout_under_legacy_locale_preserves_tracked_only_policy(self):
        renamed = self.root.with_name("과제")
        self.root.rename(renamed)
        self.root = renamed
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        self.write("scripts/untracked.py", "SECRET_SOURCE")
        environment = dict(os.environ, LC_ALL="C", PYTHONUTF8="0", PYTHONCOERCECLOCALE="0")
        result = subprocess.run([sys.executable, "-B", str(Path(package_release.__file__)), "--source", str(self.root), "--output", str(self.output)], env=environment, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(self.output) as archive:
            self.assertNotIn("scripts/untracked.py", archive.namelist())

    def test_symlink_file_and_size_limits_fail(self):
        outside = Path(self.temp.name) / "private.py"
        outside.write_text("SECRET")
        try:
            (self.root / "scripts/leak.py").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "symlink"):
            package_release.build(self.root, self.output)
        (self.root / "scripts/leak.py").unlink()
        self.write("scripts/large.py", "X" * 100)
        with self.assertRaisesRegex(ValueError, "size limit"):
            package_release.build(self.root, self.output, max_file_bytes=80)

    def test_missing_required_source_fails(self):
        (self.root / "EXAM_POLICY.md").unlink()
        with self.assertRaisesRegex(ValueError, "required kit files"):
            package_release.build(self.root, self.output)

    def test_archive_source_can_be_repacked_without_git(self):
        self.write("data/private.py", "SECRET")
        self.write("scripts/tool.py")
        with mock.patch.object(package_release.shutil, "which", return_value=None):
            package_release.build(self.root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertIn("scripts/tool.py", archive.namelist())
            self.assertNotIn("data/private.py", archive.namelist())


if __name__ == "__main__":
    unittest.main()
