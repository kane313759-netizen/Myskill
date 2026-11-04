"""Restricted-workspace installation uses explicit opt-in and preserves task data."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]


class InternalSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='kit-internal-source-')
        self.base = Path(self.temp.name)
        self.external = self.base / 'verified-kit'
        shutil.copytree(SOURCE, self.external,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'tests'))
        self.target = self.base / '과제 task'
        self.target.mkdir()
        self.stage = self.target / '.myskill-source [임시]'
        self.backups = self.base / 'outside-backups'
        self.backups.mkdir()
        self.env = dict(os.environ, TMPDIR=str(self.backups), TEMP=str(self.backups),
                        TMP=str(self.backups))
        self.task_file = self.target / 'provided-data.txt'
        self.task_file.write_text('PROTECTED TASK DATA\n', encoding='utf-8')
        self.git('init', '-q')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, root=None):
        result = subprocess.run(['git', '-C', str(root or self.target), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def stage_source(self, path=None):
        path = path or self.stage
        shutil.copytree(self.external, path)
        return path

    def call(self, command, *args, source=None, target=None, timeout=None):
        target = target or self.target
        backend = self.external / 'scripts/kit_lifecycle.py'
        cmd = [sys.executable, '-B', str(backend), command]
        if command == 'install':
            cmd += ['--source', str(source or self.stage), '--target', str(target)]
        else:
            cmd += ['--kit', str(target / '.hackathon-kit')]
        return subprocess.run(cmd + list(args), capture_output=True, text=True,
                              env=self.env, timeout=timeout)

    def assert_rc(self, result, expected):
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def install_internal(self, source=None):
        result = self.call('install', '--allow-internal-source', source=source)
        self.assert_rc(result, 0)
        return result

    def manifest(self):
        return json.loads((self.target / '.hackathon-kit/manifest.json').read_text())

    def assert_task_preserved(self):
        self.assertEqual(self.task_file.read_text(encoding='utf-8'), 'PROTECTED TASK DATA\n')

    def test_internal_source_requires_opt_in_before_install_writes(self):
        self.stage_source()
        result = self.call('install')
        self.assert_rc(result, 2)
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertFalse((self.target / '.agents').exists())
        self.assertTrue((self.stage / 'install.sh').is_file())
        self.assert_task_preserved()

    def test_explicit_internal_install_records_source_and_git_exclusion(self):
        self.stage_source()
        # A real Git download may carry its own nested .git directory.
        self.git('init', '-q', root=self.stage)
        unrelated = self.target / '.agents/skills/project-skill/KEEP.txt'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('USER SKILL')
        self.install_internal()
        rel = self.stage.relative_to(self.target).as_posix()
        self.assertIn(rel, self.manifest()['internal_sources'])
        self.git('check-ignore', '-q', '--', rel + '/')
        self.assertTrue((self.stage / '.git').is_dir())
        self.assertTrue((self.stage / 'install.sh').is_file())
        self.assertTrue((self.target / '.hackathon-kit/run/STATE.md').is_file())
        self.assertEqual(unrelated.read_text(), 'USER SKILL')
        self.assert_task_preserved()

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'named pipes unavailable')
    def test_fifo_internal_source_is_rejected_before_any_task_writes(self):
        self.stage_source()
        fifo = self.stage / 'EXAM_POLICY.md'
        fifo.unlink()
        os.mkfifo(str(fifo))
        before = {p.relative_to(self.target).as_posix(): p.read_bytes()
                  for p in self.target.rglob('*') if p.is_file()}
        result = self.call('install', '--allow-internal-source', timeout=3)
        self.assert_rc(result, 2)
        self.assertIn('Non-regular file', result.stderr)
        self.assertTrue(stat.S_ISFIFO(fifo.lstat().st_mode))
        self.assertEqual({p.relative_to(self.target).as_posix(): p.read_bytes()
                          for p in self.target.rglob('*') if p.is_file()}, before)
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertFalse((self.target / '.agents').exists())
        self.assert_task_preserved()

    def test_doctor_warns_and_pre_submit_names_remaining_source(self):
        self.stage_source()
        self.install_internal()
        rel = self.stage.relative_to(self.target).as_posix()
        regular = self.call('doctor')
        self.assert_rc(regular, 0)
        self.assertIn(rel, regular.stdout + regular.stderr)
        self.assertIn('WARN', regular.stdout)
        before_submit = self.call('doctor', '--pre-submit')
        self.assert_rc(before_submit, 2)
        # A fresh gate is also open; requiring the actual source path proves the
        # source guard ran rather than observing only the unrelated gate error.
        self.assertIn(rel, before_submit.stdout + before_submit.stderr)
        self.assert_task_preserved()

    def test_cleanup_refuses_before_deletion_when_internal_source_remains(self):
        self.stage_source()
        personal = self.stage / 'personal-note.txt'
        personal.write_text('NOT OWNED BY CLEANUP')
        self.install_internal()
        modified_source = self.stage / '.agents/skills/grader-intake/SKILL.md'
        modified_source.write_text(modified_source.read_text() + '\nSOURCE EDIT AFTER INSTALL\n')
        source_after_edit = modified_source.read_bytes()
        owned = self.target / '.agents/skills/grader-intake/SKILL.md'
        before = owned.read_bytes()
        result = self.call('clean', '--apply')
        self.assert_rc(result, 2)
        self.assertIn(self.stage.relative_to(self.target).as_posix(),
                      result.stdout + result.stderr)
        self.assertEqual(owned.read_bytes(), before)
        self.assertTrue((self.target / '.hackathon-kit/manifest.json').is_file())
        self.assertEqual(personal.read_text(), 'NOT OWNED BY CLEANUP')
        self.assertEqual(modified_source.read_bytes(), source_after_edit)
        self.assertEqual(list(self.backups.iterdir()), [])
        self.assert_task_preserved()

    def test_source_removed_then_external_reinstall_preserves_notes_and_cleans(self):
        self.stage_source()
        self.install_internal()
        notes = self.target / '.hackathon-kit/run/DECISIONS.md'
        notes.write_text('ACTUAL USER DECISION\n')
        unrelated = self.target / '.agents/skills/project-skill/KEEP.txt'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('USER SKILL')
        rel = self.stage.relative_to(self.target).as_posix()
        shutil.rmtree(self.stage)
        self.assert_rc(self.call('doctor'), 0)
        self.assert_rc(self.call('install', source=self.external), 0)
        self.assertEqual(notes.read_text(), 'ACTUAL USER DECISION\n')
        self.assertIn(rel, self.manifest()['internal_sources'])
        result = self.call('clean', '--apply')
        self.assert_rc(result, 0)
        backup = Path(next(line.split(': ', 1)[1] for line in result.stdout.splitlines()
                           if line.startswith('Run-note backup: ')))
        self.assertEqual((backup / 'run/DECISIONS.md').read_text(), 'ACTUAL USER DECISION\n')
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertEqual(unrelated.read_text(), 'USER SKILL')
        self.assert_task_preserved()

    def test_reinstall_keeps_all_internal_source_paths(self):
        self.stage_source()
        self.install_internal()
        first_rel = self.stage.relative_to(self.target).as_posix()
        shutil.rmtree(self.stage)
        second = self.stage_source(self.target / '.myskill-second-source')
        second_rel = second.relative_to(self.target).as_posix()
        self.install_internal(source=second)
        self.assertEqual(set(self.manifest()['internal_sources']), {first_rel, second_rel})
        self.assert_rc(self.call('clean', '--apply'), 2)
        # Reusing an old source path must remain visible, not forgotten when a
        # later installation used a different source.
        self.stage.mkdir()
        sentinel = self.stage / 'new-user-file.txt'
        sentinel.write_text('KEEP NEW CONTENT')
        shutil.rmtree(second)
        result = self.call('clean', '--apply')
        self.assert_rc(result, 2)
        self.assertEqual(sentinel.read_text(), 'KEEP NEW CONTENT')
        self.assert_task_preserved()

    def test_opt_in_does_not_allow_equal_or_ancestor_source(self):
        for target in (self.external, self.external / 'nested-target'):
            with self.subTest(target=target):
                result = self.call('install', '--allow-internal-source',
                                   source=self.external, target=target)
                self.assert_rc(result, 2)
                self.assertFalse((target / '.hackathon-kit').exists())
        self.assert_task_preserved()

    def test_opt_in_cannot_stage_within_protected_install_or_git_paths(self):
        for rel in ('.agents/skills/source', '.hackathon-kit/source', '.git/source'):
            with self.subTest(source=rel):
                stage = self.stage_source(self.target / rel)
                result = self.call('install', '--allow-internal-source', source=stage)
                self.assert_rc(result, 2)
                self.assertTrue((stage / 'install.sh').is_file())
                self.assertFalse((self.target / '.hackathon-kit/manifest.json').exists())
                self.assert_task_preserved()
                shutil.rmtree(stage)
                # Keep only the .git metadata needed by this disposable repo.
                for path in (self.target / '.agents/skills', self.target / '.agents',
                             self.target / '.hackathon-kit'):
                    if path.is_dir():
                        try:
                            path.rmdir()
                        except OSError:
                            pass

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlink unsupported')
    def test_opt_in_does_not_follow_a_linked_source(self):
        try:
            self.stage.symlink_to(self.external, target_is_directory=True)
        except OSError:
            self.skipTest('symlink privilege unavailable')
        result = self.call('install', '--allow-internal-source')
        self.assert_rc(result, 2)
        self.assertTrue(self.stage.is_symlink())
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assert_task_preserved()

    def test_internal_install_and_doctor_need_no_external_temp_directory(self):
        self.stage_source()
        only_temp = self.target / 'only-temp'
        only_temp.mkdir()
        env = dict(self.env, TMPDIR=str(only_temp), TEMP=str(only_temp), TMP=str(only_temp))
        # Run the downloaded backend itself, not the fixture's outside copy.
        # This tests temp-directory selection, not kernel-enforced isolation.
        result = subprocess.run([
            sys.executable, '-B', str(self.stage / 'scripts/kit_lifecycle.py'),
            'install', '--source', str(self.stage), '--target', str(self.target),
            '--allow-internal-source'], capture_output=True, text=True, env=env)
        self.assert_rc(result, 0)
        backend = self.target / '.hackathon-kit/scripts/kit_lifecycle.py'
        kit = self.target / '.hackathon-kit'
        result = subprocess.run([sys.executable, '-B', str(backend), 'doctor',
                                 '--kit', str(kit)], capture_output=True, text=True, env=env)
        self.assert_rc(result, 0)
        notes = kit / 'run/DECISIONS.md'
        notes.write_text(notes.read_text() + '\nACTUAL NOTE TO PRESERVE\n')
        notes_before = notes.read_bytes()
        shutil.rmtree(self.stage)
        result = subprocess.run([sys.executable, '-B', str(backend), 'clean',
                                 '--kit', str(kit), '--apply'],
                                capture_output=True, text=True, env=env)
        self.assert_rc(result, 2)
        self.assertIn('inside the task tree', result.stdout + result.stderr)
        self.assertEqual(notes.read_bytes(), notes_before)
        self.assertTrue((kit / 'manifest.json').is_file())
        self.assertTrue((self.target / '.agents/skills/grader-intake/SKILL.md').is_file())
        self.assertEqual(list(only_temp.iterdir()), [])
        self.assertEqual(list(self.backups.iterdir()), [])
        self.assert_task_preserved()

    @unittest.skipUnless(os.name == 'posix', 'newline filenames are unavailable on Windows')
    def test_newline_source_path_cannot_inject_a_git_ignore_rule(self):
        task_source = self.target / 'src/main.py'
        task_source.parent.mkdir()
        task_source.write_text('print("TASK SOURCE MUST STAY VISIBLE")\n')
        check = ['git', '-C', str(self.target), '-c', 'core.excludesFile=/dev/null',
                 'check-ignore', '-q', '--', 'src/main.py']
        self.assertEqual(subprocess.run(check, capture_output=True).returncode, 1)
        exclude = self.target / '.git/info/exclude'
        exclude_before = exclude.read_bytes()
        stage = self.stage_source(self.target / '.stage\n/src')
        result = self.call('install', '--allow-internal-source', source=stage)
        self.assert_rc(result, 2)
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertFalse((self.target / '.agents').exists())
        self.assertEqual(exclude.read_bytes(), exclude_before)
        self.assertEqual(subprocess.run(check, capture_output=True).returncode, 1)
        self.assertEqual(task_source.read_text(), 'print("TASK SOURCE MUST STAY VISIBLE")\n')
        self.assertTrue((stage / 'install.sh').is_file())
        self.assert_task_preserved()

    def test_unsafe_internal_source_manifest_paths_are_rejected(self):
        self.stage_source()
        self.install_internal()
        manifest_path = self.target / '.hackathon-kit/manifest.json'
        original = self.manifest()
        for bad in ('../outside', '/absolute', '.', '.git/source', '.agents/skills',
                    '.hackathon-kit/source', 'source\\escape', 'C:/outside', 'C:outside',
                    '.GIT/source', '.AGENTS/skills', '.HACKATHON-KIT/source',
                    'stage\n/src', 123):
            with self.subTest(path=bad):
                value = dict(original, internal_sources=[bad])
                manifest_path.write_text(json.dumps(value))
                result = self.call('clean', '--apply')
                self.assert_rc(result, 2)
                self.assertTrue((self.target / '.agents/skills/grader-intake/SKILL.md').is_file())
                self.assertTrue(self.stage.is_dir())
                self.assert_task_preserved()

    @unittest.skipUnless(os.name == 'posix' and shutil.which('bash'), 'Bash wrapper requires POSIX')
    def test_bash_wrapper_forwards_explicit_internal_opt_in(self):
        self.stage_source()
        result = subprocess.run(['bash', str(self.stage / 'install.sh'), str(self.target),
                                 '--allow-internal-source'], capture_output=True,
                                text=True, env=self.env)
        self.assert_rc(result, 0)
        self.assertIn(self.stage.relative_to(self.target).as_posix(),
                      self.manifest()['internal_sources'])
        self.assert_task_preserved()

    @unittest.skipUnless(shutil.which('pwsh') or shutil.which('powershell'),
                         'PowerShell executable unavailable')
    def test_powershell_wrapper_forwards_explicit_internal_opt_in(self):
        self.stage_source()
        executable = shutil.which('pwsh') or shutil.which('powershell')
        result = subprocess.run([executable, '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                 '-File', str(self.stage / 'install.ps1'), '-Target',
                                 str(self.target), '-AllowInternalSource'],
                                capture_output=True, text=True, env=self.env)
        self.assert_rc(result, 0)
        self.assertIn(self.stage.relative_to(self.target).as_posix(),
                      self.manifest()['internal_sources'])
        self.assert_task_preserved()


if __name__ == '__main__':
    unittest.main()
