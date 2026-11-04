"""Exercise the real read-only helper against untrusted PATH/package fixtures."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tool_inventory.py"

# Run the real CLI in a separate interpreter. Reject attempts before they can
# execute/install, contact a network, mutate files, or walk a task directory.
# Preload its standard-library imports so their own import lookup is not confused
# with a repository walk. Candidate modules remain unimported and on PYTHONPATH.
GUARDED_RUN = r'''
import argparse, json, os, pkgutil, runpy, shutil, sys
script = sys.argv[1]
sys.argv = sys.argv[1:]
task = os.path.abspath(os.environ["INVENTORY_TEST_TASK"])
blocked_modules = {"duckdb", "pdfplumber", "pip", "ensurepip"}
write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
mutations = {"os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.symlink",
             "os.link", "os.chmod", "os.chown", "os.truncate", "os.utime",
             "os.putenv", "os.unsetenv",
             "shutil.copyfile", "shutil.move", "shutil.rmtree"}
executions = {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn",
              "os.fork", "os.forkpty", "os.startfile"}
def audit(event, args):
    forbidden = event in mutations or event in executions or event.startswith("socket.")
    if event == "import":
        forbidden = forbidden or args[0].split(".")[0] in blocked_modules
    if event == "open":
        mode, flags = args[1], args[2]
        forbidden = forbidden or (isinstance(mode, str) and any(c in mode for c in "wax+"))
        forbidden = forbidden or (isinstance(flags, int) and bool(flags & write_flags))
    if event in {"os.listdir", "os.scandir"}:
        path = args[0]
        if isinstance(path, (str, bytes)):
            path = os.path.abspath(os.fsdecode(path))
            forbidden = forbidden or os.path.commonpath((path, task)) == task
    if forbidden:
        raise AssertionError("PROHIBITED_INVENTORY_SIDE_EFFECT: " + event)
sys.addaudithook(audit)
runpy.run_path(script, run_name="__main__")
'''


class ToolInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="inventory space 한글 ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task space 과제"
        self.task.mkdir()
        self.bin = self.root / "external bin 도구"
        self.bin.mkdir()
        self.packages = self.task / "fake packages"
        self.packages.mkdir()

    def command(self, directory, name):
        filename = name + (".EXE" if os.name == "nt" else "")
        path = directory / filename
        marker = self.task / (name + "-EXECUTED")
        path.write_text(
            "#!" + sys.executable + "\n"
            "from pathlib import Path\n"
            "Path(" + repr(str(marker)) + ").write_text('executed')\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def fake_module(self, name):
        marker = self.task / (name + "-IMPORTED")
        path = self.packages / (name + ".py")
        path.write_text(
            "from pathlib import Path\n"
            "Path(" + repr(str(marker)) + ").write_text('imported')\n"
            "raise RuntimeError('candidate package must never be imported')\n",
            encoding="utf-8",
        )
        return path

    def snapshot(self):
        return {
            str(path.relative_to(self.root)): (
                path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns
            )
            for path in self.root.rglob("*") if path.is_file()
        }

    def inventory_environment(self, path):
        environment = dict(os.environ)
        environment.update(
            PATH=str(self.bin) if path is None else path,
            PYTHONPATH=str(self.packages),
            PYTHONDONTWRITEBYTECODE="1",
            INVENTORY_TEST_TASK=str(self.task),
        )
        if os.name == "nt":
            environment["PATHEXT"] = ".EXE"
        return environment

    def native_candidate(self, name, path):
        # Match the helper's interpreter, cwd and environment. In particular,
        # native Windows which may choose cwd before the supplied PATH entry.
        result = subprocess.run(
            [sys.executable, "-B", "-c",
             "import json, os, shutil, sys\n"
             "print(json.dumps(shutil.which(sys.argv[1], path=os.environ['PATH'])))\n",
             name], cwd=str(self.task), env=self.inventory_environment(path),
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def run_inventory(self, *args, path=None, guarded=True, prefix="", isolated=False):
        environment = self.inventory_environment(path)
        if guarded:
            command = [sys.executable, "-B", "-c", prefix + GUARDED_RUN, str(SCRIPT)]
        else:
            flags = ["-I", "-S", "-B"] if isolated else ["-B"]
            command = [sys.executable] + flags + [str(SCRIPT)]
        result = subprocess.run(
            command + list(args), cwd=str(self.task), env=environment,
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def by_name(self, output):
        return {item["name"]: item for item in output["commands"]}

    def test_real_cli_observes_candidates_without_execution_import_or_mutation(self):
        expected = {name: self.command(self.bin, name)
                    for name in ("jq", "gitleaks", "ruff", "duckdb")}
        for name in ("duckdb", "pdfplumber", "pip", "ensurepip"):
            self.fake_module(name)
        # A fake installer/downloader would leave the same execution marker.
        for name in ("pip", "pip3", "curl", "wget"):
            self.command(self.bin, name)
        before = self.snapshot()
        output = self.run_inventory("--task-root", str(self.task))
        after = self.snapshot()
        self.assertEqual(before, after)
        self.assertFalse(any(self.root.rglob("__pycache__")))
        commands = self.by_name(output)
        self.assertEqual(set(commands), set(expected))
        for name, candidate in expected.items():
            with self.subTest(name=name):
                self.assertEqual(commands[name]["status"], "PATH_CANDIDATE")
                self.assertEqual(commands[name]["candidate_path"], str(candidate))
                self.assertFalse(commands[name]["task_local_candidate"])
                self.assertTrue(commands[name]["provenance_review_required"])
        self.assertTrue(output["inventory_only"])
        self.assertFalse(output["selection_performed"])
        self.assertFalse(output["approval_granted"])
        self.assertIn("identity, version, compatibility", output["notice"])
        self.assertEqual({item["name"] for item in output["python_packages"]},
                         {"duckdb", "pdfplumber"})
        self.assertTrue(all(item["status"] == "UNKNOWN"
                            for item in output["python_packages"]))

    def test_direct_cli_handles_relative_path_unicode_and_default_task_root(self):
        local_bin = self.task / "local bin 도구"
        local_bin.mkdir()
        candidate = self.command(local_bin, "jq")
        before = self.snapshot()
        output = self.run_inventory(path=os.path.relpath(str(local_bin), str(self.task)),
                                    guarded=False)
        jq = self.by_name(output)["jq"]
        self.assertEqual(jq["candidate_path"], str(candidate))
        self.assertTrue(jq["task_local_candidate"])
        self.assertTrue(jq["provenance_review_required"])
        self.assertFalse(output["approval_granted"])
        self.assertEqual(output["task_root"], str(self.task))
        self.assertEqual(self.snapshot(), before)

    def test_path_precedence_does_not_trust_a_task_local_candidate(self):
        local_bin = self.task / "bin"
        local_bin.mkdir()
        first = self.command(local_bin, "ruff")
        self.command(self.bin, "ruff")
        output = self.run_inventory(path=os.pathsep.join((str(local_bin), str(self.bin))))
        ruff = self.by_name(output)["ruff"]
        self.assertEqual(ruff["candidate_path"], str(first))
        self.assertTrue(ruff["task_local_candidate"])
        self.assertTrue(ruff["provenance_review_required"])
        self.assertFalse(output["selection_performed"])
        self.assertFalse(output["approval_granted"])

    def test_missing_cli_and_present_python_module_do_not_become_approved(self):
        for name in ("duckdb", "pdfplumber"):
            self.fake_module(name)
        before = self.snapshot()
        output = self.run_inventory()
        for item in output["commands"]:
            self.assertEqual(item["status"], "NOT_FOUND")
            self.assertIsNone(item["candidate_path"])
            self.assertIsNone(item["task_local_candidate"])
        self.assertTrue(all(item["status"] == "UNKNOWN"
                            for item in output["python_packages"]))
        self.assertFalse(output["approval_granted"])
        self.assertEqual(self.snapshot(), before)

    @unittest.skipIf(os.name == "nt", "Windows executable checks use PATHEXT, not mode bits")
    def test_non_executable_command_file_is_not_a_path_candidate(self):
        candidate = self.command(self.bin, "gitleaks")
        candidate.chmod(0o644)
        output = self.run_inventory()
        self.assertEqual(self.by_name(output)["gitleaks"]["status"], "NOT_FOUND")

    def test_lookup_error_is_unknown_and_other_names_are_still_observed(self):
        expected = self.command(self.bin, "jq")
        prefix = '''import shutil
original_which = shutil.which
def unavailable(name, path=None):
    if name == "gitleaks":
        raise OSError("lookup unavailable")
    return original_which(name, path=path)
shutil.which = unavailable
'''
        output = self.run_inventory(prefix=prefix)
        commands = self.by_name(output)
        self.assertEqual(commands["gitleaks"]["status"], "UNKNOWN")
        self.assertIsNone(commands["gitleaks"]["candidate_path"])
        self.assertEqual(commands["jq"]["candidate_path"], str(expected))
        self.assertEqual(commands["duckdb"]["status"], "NOT_FOUND")

    def test_entry_cap_skips_later_candidate_and_reports_unknown(self):
        candidate = self.command(self.bin, "jq")
        entries = [str(self.root / ("absent-%03d" % index)) for index in range(128)]
        entries.append(str(self.bin))
        prefix = '''import os, shutil
original_which, original_access, original_stat = shutil.which, os.access, os.stat
excluded = %r
expected_path = %r
def bounded_which(name, path=None):
    if name not in {"jq", "gitleaks", "ruff", "duckdb"} or path != expected_path:
        raise AssertionError("unbounded or unexpected PATH lookup")
    return original_which(name, path=path)
def guarded_access(path, *args, **kwargs):
    if os.fsdecode(path).startswith(excluded):
        raise AssertionError("excluded PATH entry was accessed")
    return original_access(path, *args, **kwargs)
def guarded_stat(path, *args, **kwargs):
    if os.fsdecode(path).startswith(excluded):
        raise AssertionError("excluded PATH entry was inspected")
    return original_stat(path, *args, **kwargs)
shutil.which, os.access, os.stat = bounded_which, guarded_access, guarded_stat
''' % (str(self.bin), os.pathsep.join(entries[:128]))
        before = self.snapshot()
        output = self.run_inventory(path=os.pathsep.join(entries), prefix=prefix)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(output["path_scope"]["entries_supplied"], 128)
        self.assertTrue(output["path_scope"]["truncated"])
        self.assertNotIn(str(candidate), json.dumps(output))
        self.assertTrue(all(item["status"] == "UNKNOWN" for item in output["commands"]))
        self.assertFalse(output["approval_granted"])

    def test_character_cap_does_not_probe_a_partial_directory_name(self):
        self.command(self.bin, "jq")
        # The real candidate is first, followed by one incomplete overlong entry.
        # The prefix of that entry is deliberately a plausible PATH directory.
        long_entry = str(self.task / "partial") + "x" * 32768
        # Windows cannot reliably start a child with a >32767-character native
        # environment variable (or -c argument). Generate this boundary input
        # after startup and expose a detached, read-only environment view; the
        # real helper must still pass only the bounded prefix to native which.
        prefix = '''import os, shutil, types
original_which = shutil.which
expected_path = %r
long_entry = %r + "x" * 32768
os.environ = types.MappingProxyType(dict(
    os.environ, PATH=os.pathsep.join((expected_path, long_entry))))
def bounded_which(name, path=None):
    if path != expected_path or len(path) > 32768:
        raise AssertionError("partial or unbounded PATH entry supplied")
    return original_which(name, path=path)
shutil.which = bounded_which
''' % (str(self.bin), str(self.task / "partial"))
        output = self.run_inventory(prefix=prefix)
        self.assertTrue(output["path_scope"]["truncated"])
        self.assertEqual(output["path_scope"]["entries_supplied"], 1)
        commands = self.by_name(output)
        self.assertEqual(commands["jq"]["status"], "PATH_CANDIDATE")
        self.assertEqual(commands["gitleaks"]["status"], "UNKNOWN")
        self.assertNotIn(long_entry, json.dumps(output))

    def test_isolated_direct_cli_ignores_startup_hooks_and_pythonpath_packages(self):
        marker = self.task / "STARTUP-EXECUTED"
        startup = "from pathlib import Path\nPath(%r).write_text('startup')\n" % str(marker)
        (self.packages / "sitecustomize.py").write_text(startup, encoding="utf-8")
        (self.packages / "usercustomize.py").write_text(startup, encoding="utf-8")
        for name in ("duckdb", "pdfplumber"):
            self.fake_module(name)
        self.command(self.bin, "duckdb")
        before = self.snapshot()
        output = self.run_inventory(guarded=False, isolated=True)
        self.assertEqual(self.by_name(output)["duckdb"]["status"], "PATH_CANDIDATE")
        self.assertTrue(all(item["status"] == "UNKNOWN"
                            for item in output["python_packages"]))
        self.assertFalse(marker.exists())
        self.assertFalse(any(self.root.rglob("__pycache__")))
        self.assertEqual(self.snapshot(), before)

    def test_oversized_windows_pathext_never_reaches_native_lookup_or_probes(self):
        for suffixes in (";".join(".EXT%03d" % n for n in range(200)),
                         "." + "X" * 2048):
            with self.subTest(suffix_characters=len(suffixes)):
                prefix = '''import os, shutil, sys
sys.platform = "win32"
os.pathsep = ";"
os.environ["PATHEXT"] = %r
def forbidden(*args, **kwargs):
    raise AssertionError("oversized PATHEXT reached native lookup or a probe")
shutil.which = forbidden
shutil._access_check = forbidden
''' % suffixes
                before = self.snapshot()
                output = self.run_inventory(prefix=prefix)
                self.assertTrue(output["windows_pathext_scope"]["limit_exceeded"])
                self.assertTrue(output["windows_pathext_scope"]["native_lookup_skipped"])
                self.assertTrue(output["path_scope"]["native_which_may_add_cwd"])
                self.assertTrue(all(item["status"] == "UNKNOWN"
                                    for item in output["commands"]))
                self.assertFalse(output["approval_granted"])
                self.assertFalse(output["selection_performed"])
                self.assertNotIn(suffixes, json.dumps(output))
                self.assertEqual(self.snapshot(), before)

    def test_bounded_windows_pathext_uses_native_lookup_and_reports_cwd_policy(self):
        expected = self.bin / "jq.EXE"
        prefix = '''import os, shutil, sys
sys.platform = "win32"
os.pathsep = ";"
os.environ["PATHEXT"] = ".EXE;.CMD"
if hasattr(shutil, "_win_path_needs_curdir"):
    shutil._win_path_needs_curdir = lambda *args: True
expected = %r
probes = []
def bounded_probe(path, mode):
    probes.append(path)
    if len(probes) > 24:
        raise AssertionError("native Windows lookup exceeded expected fixed scope")
    if not path.endswith((".EXE", ".CMD")):
        raise AssertionError("unexpected Windows suffix probe")
    return path == expected
shutil._access_check = bounded_probe
''' % str(expected)
        output = self.run_inventory(prefix=prefix)
        jq = self.by_name(output)["jq"]
        self.assertEqual(jq["status"], "PATH_CANDIDATE")
        self.assertEqual(jq["candidate_path"], str(expected))
        self.assertFalse(output["windows_pathext_scope"]["limit_exceeded"])
        self.assertFalse(output["windows_pathext_scope"]["native_lookup_skipped"])
        self.assertTrue(output["path_scope"]["native_which_may_add_cwd"])
        self.assertIn("may also search cwd", output["path_scope"]["cwd_policy"])
        self.assertEqual(self.by_name(output)["ruff"]["status"], "NOT_FOUND")
        self.assertFalse(output["approval_granted"])

    def test_external_symlink_to_task_candidate_is_also_flagged_local(self):
        local_bin = self.task / "bin"
        local_bin.mkdir()
        target = self.command(local_bin, "duckdb")
        link = self.bin / target.name
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        output = self.run_inventory()
        duckdb = self.by_name(output)["duckdb"]
        self.assertEqual(duckdb["candidate_path"], str(link))
        self.assertTrue(duckdb["task_local_candidate"])
        self.assertTrue(duckdb["provenance_review_required"])

    def test_symlink_parent_dotdot_preserves_the_observed_candidate(self):
        inner = self.bin / "inner"
        inner.mkdir()
        alias = self.task / "alias"
        try:
            alias.symlink_to(inner, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlinks unavailable")
        target = self.command(self.bin, "jq")
        decoy = self.command(self.task, "jq")
        before = self.snapshot()
        for entry in (str(alias / ".."), os.path.join("alias", "..")):
            with self.subTest(path_entry=entry):
                native = self.native_candidate("jq", entry)
                self.assertIsNotNone(native)
                expected = native if os.path.isabs(native) else os.path.join(str(self.task), native)
                output = self.run_inventory(path=entry)
                jq = self.by_name(output)["jq"]
                self.assertEqual(jq["candidate_path"], expected)
                self.assertTrue(Path(jq["candidate_path"]).samefile(expected))
                self.assertTrue(Path(expected).samefile(target) or Path(expected).samefile(decoy))
                if os.name != "nt":
                    # Keep the POSIX regression against lexical abspath: the
                    # alias/.. lookup must identify the external target.
                    self.assertEqual(expected, os.path.join(str(self.task), entry, target.name))
                    self.assertTrue(Path(jq["candidate_path"]).samefile(target))
                    self.assertFalse(Path(jq["candidate_path"]).samefile(decoy))
                self.assertTrue(jq["provenance_review_required"])
        self.assertEqual(self.snapshot(), before)

    def test_observed_symlink_parent_dotdot_spelling_is_never_collapsed(self):
        inner = self.bin / "inner"
        inner.mkdir()
        alias = self.task / "alias"
        try:
            alias.symlink_to(inner, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlinks unavailable")
        target = self.command(self.bin, "jq")
        decoy = self.command(self.task, "jq")
        before = self.snapshot()
        for observed in (str(alias / ".." / target.name),
                         os.path.join("alias", "..", target.name)):
            with self.subTest(observed_path=observed):
                # Exercise the returned spelling independently of the native
                # Windows cwd policy, without changing production precedence.
                prefix = '''import shutil
original_which = shutil.which
def observed_which(name, path=None):
    if name == "jq":
        return %r
    return original_which(name, path=path)
shutil.which = observed_which
''' % observed
                output = self.run_inventory(path=str(alias / ".."), prefix=prefix)
                jq = self.by_name(output)["jq"]
                expected = observed if os.path.isabs(observed) else os.path.join(str(self.task), observed)
                self.assertEqual(jq["candidate_path"], expected)
                self.assertTrue(Path(jq["candidate_path"]).samefile(expected))
                if os.name != "nt":
                    self.assertTrue(Path(jq["candidate_path"]).samefile(target))
                    self.assertFalse(Path(jq["candidate_path"]).samefile(decoy))
                self.assertTrue(jq["provenance_review_required"])
        self.assertEqual(self.snapshot(), before)

    def test_symlink_parent_dotdot_uses_the_actual_target_for_locality(self):
        inner = self.task / "inner"
        inner.mkdir()
        alias = self.bin / "alias"
        try:
            alias.symlink_to(inner, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlinks unavailable")
        target = self.command(self.task, "duckdb")
        decoy = self.command(self.bin, "duckdb")
        before = self.snapshot()
        output = self.run_inventory(path=str(alias / ".."))
        duckdb = self.by_name(output)["duckdb"]
        self.assertTrue(Path(duckdb["candidate_path"]).samefile(target))
        self.assertFalse(Path(duckdb["candidate_path"]).samefile(decoy))
        self.assertTrue(duckdb["task_local_candidate"])
        self.assertTrue(duckdb["provenance_review_required"])
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
