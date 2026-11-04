"""Regression tests use disposable repositories; no network or Unity/domain assumptions."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1]


def snapshot(root):
    paths = list(root.rglob('*'))
    return ({p.relative_to(root).as_posix() for p in paths if p.is_dir()},
            {p.relative_to(root).as_posix(): p.read_bytes() for p in paths if p.is_file()})


def backend_module():
    spec = importlib.util.spec_from_file_location('reviewed_lifecycle', SOURCE / 'scripts/kit_lifecycle.py')
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='kit-lifecycle-test-')
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        shutil.copytree(SOURCE, self.source, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'tests'))
        self.target = self.base / 'task'
        self.target.mkdir()
        self.git('init', '-q')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, root=None):
        r = subprocess.run(['git', '-C', str(root or self.target), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def call(self, command, *args, target=None, timeout=None):
        root = target or self.target
        cmd = [sys.executable, '-B', str(self.source / 'scripts/kit_lifecycle.py'), command]
        if command == 'install':
            cmd += ['--source', str(self.source), '--target', str(root)]
        else:
            cmd += ['--kit', str(root / '.hackathon-kit')]
        return subprocess.run(cmd + list(args), capture_output=True, text=True, timeout=timeout)

    def install(self, **kwargs):
        r = self.call('install', **kwargs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def assert_rc(self, r, code):
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)

    def manifest(self):
        return json.loads((self.target / '.hackathon-kit/manifest.json').read_text())

    def test_install_reinstall_doctor_cleanup_and_notes_backup(self):
        existing = self.target / '.agents/skills/existing-skill/KEEP.txt'
        existing.parent.mkdir(parents=True)
        existing.write_text('original')
        self.install()
        for name in ('STATE', 'BASELINE', 'SPEC_DRAFT', 'HUMAN_JUDGMENT', 'EDGE_CASES', 'AI_FAILURES', 'LIMITATIONS', 'FOLLOWUP_CHEATSHEET'):
            self.assertTrue((self.target / '.hackathon-kit/run' / (name + '.md')).is_file())
        notes = self.target / '.hackathon-kit/run/DECISIONS.md'
        notes.write_text(notes.read_text() + '\nKEEP_ME\n')
        self.install()
        self.assertIn('KEEP_ME', notes.read_text())
        self.assert_rc(self.call('doctor'), 0)
        self.assertFalse(list((self.target / '.hackathon-kit').rglob('__pycache__')))
        r = self.call('clean', '--apply')
        self.assert_rc(r, 0)
        backup = Path(next(x.split(': ', 1)[1] for x in r.stdout.splitlines() if x.startswith('Run-note backup: ')))
        try:
            self.assertIn('KEEP_ME', (backup / 'run/DECISIONS.md').read_text())
            self.assertNotIn(self.target, backup.parents)
        finally:
            shutil.rmtree(backup)
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertEqual(existing.read_text(), 'original')

    def test_required_collision_fails_before_any_install_writes(self):
        skill = self.target / '.agents/skills/grader-intake/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('UNRELATED_SENTINEL')
        r = self.call('install')
        self.assert_rc(r, 2)
        self.assertIn('Required skill name collision', r.stderr)
        self.assertEqual(skill.read_text(), 'UNRELATED_SENTINEL')
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertEqual(list(skill.parent.parent.iterdir()), [skill.parent])

    @unittest.skipUnless(os.name == 'posix', 'control-character filenames are unavailable on Windows')
    def test_external_source_target_controls_cannot_change_git_exclusions(self):
        task_source = self.target / 'src/main.py'
        task_source.parent.mkdir()
        task_source.write_bytes(b'PROTECTED TASK SOURCE\n')
        source_before = snapshot(self.source)
        for control in ('\n', '\r', '\t', '\x7f'):
            with self.subTest(control=repr(control)):
                target = self.target / ('stage' + control) / ('src' + control) / 'task'
                target.mkdir(parents=True)
                task_before = snapshot(self.target)
                result = self.call('install', target=target, timeout=3)
                self.assert_rc(result, 2)
                self.assertIn('Unsafe target path', result.stderr)
                self.assertEqual(snapshot(self.target), task_before)
                self.assertEqual(snapshot(self.source), source_before)
                self.assertEqual(subprocess.run(['git', '-C', str(self.target), 'check-ignore',
                                                 '-q', '--', 'src/main.py'], capture_output=True).returncode, 1)

    def test_invalid_git_exclusion_destination_fails_before_helper_writes(self):
        exclude = self.target / '.git/info/exclude'
        exclude.unlink()
        exclude.mkdir()
        sentinel = exclude / 'KEEP'
        sentinel.write_bytes(b'EXISTING GIT METADATA\n')
        task_before, source_before = snapshot(self.target), snapshot(self.source)
        result = self.call('install', timeout=3)
        self.assert_rc(result, 2)
        self.assertIn('Non-regular file', result.stderr)
        self.assertEqual(snapshot(self.target), task_before)
        self.assertEqual(snapshot(self.source), source_before)

    def test_unreadable_git_exclusions_fail_before_helper_writes(self):
        lifecycle = backend_module()
        # Exercise a lexical alias everywhere; Windows temp paths can also differ
        # through 8.3 names after the installer resolves the target directory.
        target_alias = self.target / '..' / self.target.name
        exclude = (target_alias / '.git/info/exclude').resolve()
        original_open = os.open
        denied_reads = []
        def denied_open(path, flags, *args, **kwargs):
            if Path(path).resolve() == exclude:
                denied_reads.append(Path(path))
                raise PermissionError('EXCLUSION_READ_DENIED')
            return original_open(path, flags, *args, **kwargs)
        task_before, source_before = snapshot(self.target), snapshot(self.source)
        with mock.patch.object(lifecycle.os, 'open', side_effect=denied_open):
            with self.assertRaisesRegex(PermissionError, 'EXCLUSION_READ_DENIED'):
                lifecycle.install(self.source, target_alias)
        self.assertEqual(len(denied_reads), 1)
        self.assertEqual(snapshot(self.target), task_before)
        self.assertEqual(snapshot(self.source), source_before)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'named pipes unavailable')
    def test_fifo_source_files_are_rejected_without_opening_or_writes(self):
        for name in ('EXAM_POLICY.md', 'VERSION'):
            with self.subTest(name=name):
                path = self.source / name
                original = path.read_bytes()
                path.unlink()
                os.mkfifo(str(path))
                try:
                    source_before, task_before = snapshot(self.source), snapshot(self.target)
                    result = self.call('install', timeout=3)
                    self.assert_rc(result, 2)
                    self.assertIn('Non-regular file', result.stderr)
                    self.assertTrue(stat.S_ISFIFO(path.lstat().st_mode))
                    self.assertEqual(snapshot(self.source), source_before)
                    self.assertEqual(snapshot(self.target), task_before)
                finally:
                    path.unlink()
                    path.write_bytes(original)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'named pipes unavailable')
    def test_fifo_manifest_legacy_and_exclusions_fail_without_mutations(self):
        self.install()
        for relative, commands in (
                ('.hackathon-kit/manifest.json', ('install', 'doctor', 'clean')),
                ('.hackathon-kit/run/INSTALLED_SKILLS.txt', ('install', 'doctor', 'clean')),
                ('.git/info/exclude', ('install',))):
            with self.subTest(path=relative):
                path = self.target / relative
                original = path.read_bytes() if path.exists() else None
                if path.exists():
                    path.unlink()
                os.mkfifo(str(path))
                try:
                    task_before, source_before = snapshot(self.target), snapshot(self.source)
                    for command in commands:
                        args = ('--apply',) if command == 'clean' else ()
                        result = self.call(command, *args, timeout=3)
                        self.assert_rc(result, 2)
                        self.assertIn('Non-regular file', result.stderr)
                        self.assertTrue(stat.S_ISFIFO(path.lstat().st_mode))
                        self.assertEqual(snapshot(self.target), task_before)
                        self.assertEqual(snapshot(self.source), source_before)
                finally:
                    path.unlink()
                    if original is not None:
                        path.write_bytes(original)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'named pipes unavailable')
    def test_digest_rechecks_opened_descriptor_after_file_becomes_fifo(self):
        lifecycle = backend_module()
        path = self.base / 'changing-source'
        path.write_bytes(b'ORIGINAL')
        original_open = os.open
        def replaced_open(filename, flags):
            path.unlink()
            os.mkfifo(str(path))
            self.assertTrue(flags & os.O_NONBLOCK)
            return original_open(filename, flags)
        with mock.patch.object(lifecycle.os, 'open', side_effect=replaced_open):
            with self.assertRaisesRegex(lifecycle.LifecycleError, 'Opened file is not regular'):
                lifecycle.digest(path)

    def test_metadata_byte_limits_preserve_source_and_installation(self):
        lifecycle = backend_module()
        self.install()
        for path, limit, commands in (
                (self.target / '.hackathon-kit/manifest.json', lifecycle.METADATA_LIMIT, ('install', 'doctor', 'clean')),
                (self.target / '.hackathon-kit/run/INSTALLED_SKILLS.txt', lifecycle.METADATA_LIMIT, ('install', 'doctor', 'clean')),
                (self.target / '.git/info/exclude', lifecycle.METADATA_LIMIT, ('install',)),
                (self.source / 'VERSION', lifecycle.VERSION_LIMIT, ('install',))):
            with self.subTest(path=path):
                original = path.read_bytes() if path.exists() else None
                with path.open('wb') as handle:
                    handle.truncate(limit + 1)
                try:
                    task_before, source_before = snapshot(self.target), snapshot(self.source)
                    for command in commands:
                        args = ('--apply',) if command == 'clean' else ()
                        result = self.call(command, *args, timeout=3)
                        self.assert_rc(result, 2)
                        self.assertIn('byte limit', result.stderr)
                        self.assertEqual(snapshot(self.target), task_before)
                        self.assertEqual(snapshot(self.source), source_before)
                finally:
                    if original is None:
                        path.unlink()
                    else:
                        path.write_bytes(original)

    def test_support_copy_has_no_metadata_size_cap(self):
        lifecycle = backend_module()
        path = self.source / 'CALLING.md'
        path.write_bytes(b'X' * (lifecycle.METADATA_LIMIT + 1))
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        self.install()
        copied = self.target / '.hackathon-kit/CALLING.md'
        self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest(), expected)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_identical_borrowed_core_is_verified_and_never_deleted(self):
        src = self.source / '.agents/skills/grader-intake'
        dst = self.target / '.agents/skills/grader-intake'
        shutil.copytree(src, dst)
        self.install()
        self.assertIn('grader-intake', self.manifest()['borrowed_skills'])
        self.assertNotIn('grader-intake', self.manifest()['owned_skills'])
        self.assert_rc(self.call('doctor'), 0)
        p = dst / 'SKILL.md'
        original = p.read_bytes()
        p.write_bytes(original + b'\nchanged\n')
        self.assert_rc(self.call('doctor'), 2)
        p.write_bytes(original)
        r = self.call('clean', '--apply')
        self.assert_rc(r, 0)
        backup = Path(next(x.split(': ', 1)[1] for x in r.stdout.splitlines() if x.startswith('Run-note backup: ')))
        shutil.rmtree(backup)
        self.assertTrue(p.is_file())

    def test_unmodified_owned_skill_updates_but_local_changes_preserved(self):
        self.install()
        p = self.source / '.agents/skills/grader-intake/SKILL.md'
        p.write_text(p.read_text() + '\nNEW_RELEASE\n')
        (self.source / 'VERSION').write_text('test-upgrade\n')
        self.install()
        dst = self.target / '.agents/skills/grader-intake/SKILL.md'
        self.assertIn('NEW_RELEASE', dst.read_text())
        self.assertEqual(self.manifest()['version'], 'test-upgrade')
        dst.write_text(dst.read_text() + '\nLOCAL_CHANGE\n')
        r = self.install()
        self.assertIn('Locally changed owned skill preserved', r.stdout)
        self.assertIn('LOCAL_CHANGE', dst.read_text())
        self.assert_rc(self.call('doctor'), 2)
        self.assert_rc(self.call('clean', '--apply'), 2)
        self.assertTrue((self.target / '.hackathon-kit/scripts/clean.sh').is_file())

    def test_locally_changed_support_file_preserved_and_cleanup_refused(self):
        self.install()
        p = self.target / '.hackathon-kit/CALLING.md'
        p.write_text('LOCAL_NOTES')
        r = self.install()
        self.assertIn('support file preserved', r.stdout)
        self.assertEqual(p.read_text(), 'LOCAL_NOTES')
        self.assert_rc(self.call('doctor'), 2)
        self.assert_rc(self.call('clean', '--apply'), 2)
        self.assertEqual(p.read_text(), 'LOCAL_NOTES')

    def test_optional_name_collision_preserves_visible_project_skill(self):
        skill = self.target / '.agents/skills/debugging/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('UNRELATED_OPTIONAL_SKILL')
        self.install()
        self.assertEqual(skill.read_text(), 'UNRELATED_OPTIONAL_SKILL')
        self.assertNotIn('debugging', self.manifest()['owned_skills'])
        r = subprocess.run(['git', '-C', str(self.target), 'check-ignore', '-q', str(skill)], capture_output=True)
        self.assertEqual(r.returncode, 1)
        self.assert_rc(self.call('doctor'), 0)

    def test_unexpected_helper_content_prevents_cleanup_before_any_deletion(self):
        self.install()
        p = self.target / '.hackathon-kit/personal-notes.txt'
        p.write_text('KEEP')
        self.assert_rc(self.call('clean', '--apply'), 2)
        self.assertEqual(p.read_text(), 'KEEP')
        self.assertTrue((self.target / '.agents/skills/grader-intake/SKILL.md').is_file())
        self.assertTrue((self.target / '.hackathon-kit/scripts/clean.sh').is_file())

    def test_backup_location_inside_task_is_refused(self):
        self.install()
        tmp = self.target / 'local-temp'
        tmp.mkdir()
        env = dict(os.environ, TMPDIR=str(tmp), TEMP=str(tmp), TMP=str(tmp))
        r = subprocess.run([sys.executable, '-B', str(self.source / 'scripts/kit_lifecycle.py'),
                            'clean', '--kit', str(self.target / '.hackathon-kit'), '--apply'],
                           capture_output=True, text=True, env=env)
        self.assert_rc(r, 2)
        self.assertIn('inside the task tree', r.stderr)
        self.assertTrue((self.target / '.hackathon-kit/scripts/clean.sh').is_file())
        self.assertEqual(list(tmp.iterdir()), [])

    def test_auto_initializes_json_templates_without_overwrite(self):
        p = self.source / 'templates/NEW_RECORD.json'
        p.write_text('{"status": "NOT_RUN"}\n')
        self.install()
        dst = self.target / '.hackathon-kit/run/NEW_RECORD.json'
        self.assertEqual(dst.read_text(), p.read_text())
        dst.write_text('{"status": "KEPT"}\n')
        self.install()
        self.assertIn('KEPT', dst.read_text())

    def test_excludes_without_final_newline_preserved(self):
        exclude = self.target / '.git/info/exclude'
        exclude.write_bytes(b'existing-data.bin')
        (self.target / 'existing-data.bin').write_text('data')
        self.install()
        self.assertTrue(exclude.read_bytes().startswith(b'existing-data.bin\n'))
        self.git('check-ignore', '-q', 'existing-data.bin')
        self.git('check-ignore', '-q', '.hackathon-kit/')
        self.git('check-ignore', '-q', '.agents/skills/grader-intake/')

    def test_nested_git_target_all_helper_paths_ignored(self):
        nested = self.target / '과제 [a]'
        nested.mkdir()
        self.install(target=nested)
        self.assert_rc(self.call('doctor', target=nested), 0)
        self.git('check-ignore', '-q', '과제 [a]/.hackathon-kit/')
        self.git('check-ignore', '-q', '과제 [a]/.agents/skills/grader-intake/')

    def test_new_nested_git_target_is_excluded_before_it_exists(self):
        nested = self.target / '새 과제 [a]' / 'new task'
        source_before = snapshot(self.source)
        self.install(target=nested)
        self.assert_rc(self.call('doctor', target=nested), 0)
        self.git('check-ignore', '-q', '새 과제 [a]/new task/.hackathon-kit/')
        self.git('check-ignore', '-q', '새 과제 [a]/new task/.agents/skills/grader-intake/')
        self.assertEqual(snapshot(self.source), source_before)

    def test_shared_worktree_excludes_and_preexisting_rules_survive_cleanup(self):
        self.git('config', 'user.email', 'test@example.com')
        self.git('config', 'user.name', 'test')
        (self.target / 'README').write_text('task')
        self.git('add', 'README')
        self.git('commit', '-qm', 'baseline')
        linked = self.base / 'linked'
        self.git('worktree', 'add', '-q', '-b', 'linked', str(linked))
        exclude = self.target / '.git/info/exclude'
        exclude.write_bytes(b'/.hackathon-kit/\npreexisting-rule\n')
        self.install()
        self.install(target=linked)
        r = self.call('clean', '--apply')
        self.assert_rc(r, 0)
        backup = Path(next(x.split(': ', 1)[1] for x in r.stdout.splitlines() if x.startswith('Run-note backup: ')))
        shutil.rmtree(backup)
        self.assertIn('preexisting-rule', exclude.read_text())
        self.assert_rc(self.call('doctor', target=linked), 0)
        self.assertEqual(self.git('status', '--short', root=linked).stdout, '')

    def test_manifest_traversal_rejected_without_deletion(self):
        self.install()
        sentinel = self.target / 'KEEP.txt'
        sentinel.write_text('keep')
        manifest = self.manifest()
        manifest['owned_skills']['../../KEEP.txt'] = '0' * 64
        (self.target / '.hackathon-kit/manifest.json').write_text(json.dumps(manifest))
        self.assert_rc(self.call('clean', '--apply'), 2)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertTrue((self.target / '.hackathon-kit').is_dir())

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlink unsupported')
    def test_managed_symlinks_are_never_followed_or_deleted(self):
        self.install()
        sentinel = self.base / 'KEEP.txt'
        sentinel.write_text('keep')
        link = self.target / '.hackathon-kit/run/link'
        try:
            link.symlink_to(sentinel)
        except OSError:
            self.skipTest('symlink privilege unavailable')
        self.assert_rc(self.call('clean', '--apply'), 2)
        self.assertTrue(link.is_symlink())
        self.assertEqual(sentinel.read_text(), 'keep')

    def test_legacy_crlf_adoption_preserves_notes_and_rejects_traversal(self):
        kit = self.target / '.hackathon-kit'
        (kit / 'run').mkdir(parents=True)
        (kit / 'run/INSTALLED_SKILLS.txt').write_bytes(b'grader-intake\r\n')
        (kit / 'run/DECISIONS.md').write_text('LEGACY_KEEP')
        shutil.copytree(self.source / '.agents/skills/grader-intake', self.target / '.agents/skills/grader-intake')
        self.install()
        self.assertIn('grader-intake', self.manifest()['owned_skills'])
        self.assertEqual((kit / 'run/DECISIONS.md').read_text(), 'LEGACY_KEEP')
        (kit / 'run/INSTALLED_SKILLS.txt').write_bytes(b'../../README\r\n')
        self.assert_rc(self.call('install'), 2)
        self.assert_rc(self.call('clean', '--apply'), 2)

    def test_unverified_legacy_support_is_preserved(self):
        kit = self.target / '.hackathon-kit'
        (kit / 'run').mkdir(parents=True)
        (kit / 'run/INSTALLED_SKILLS.txt').write_bytes(b'grader-intake\r\n')
        (kit / 'CALLING.md').write_text('UNVERIFIED_LEGACY_NOTES')
        self.install()
        self.assertEqual((kit / 'CALLING.md').read_text(), 'UNVERIFIED_LEGACY_NOTES')
        self.assert_rc(self.call('doctor'), 2)
        self.assert_rc(self.call('clean', '--apply'), 2)

    def test_cleanup_backups_are_unique(self):
        backups = []
        try:
            for note in ('FIRST', 'SECOND'):
                self.install()
                (self.target / '.hackathon-kit/run/DECISIONS.md').write_text(note)
                r = self.call('clean', '--apply')
                self.assert_rc(r, 0)
                backup = Path(next(x.split(': ', 1)[1] for x in r.stdout.splitlines() if x.startswith('Run-note backup: ')))
                backups.append(backup)
                self.assertEqual((backup / 'run/DECISIONS.md').read_text(), note)
            self.assertNotEqual(*backups)
            self.assertEqual((backups[0] / 'run/DECISIONS.md').read_text(), 'FIRST')
        finally:
            for backup in backups:
                shutil.rmtree(backup)

    def test_legacy_cleanup_without_verified_ownership_refused(self):
        kit = self.target / '.hackathon-kit'
        (kit / 'run').mkdir(parents=True)
        (kit / 'run/INSTALLED_SKILLS.txt').write_bytes(b'grader-intake\r\n')
        self.assert_rc(self.call('clean', '--apply'), 2)
        self.assertTrue(kit.exists())

    def test_source_target_overlap_rejected(self):
        for root in (self.source, self.base, self.source / 'nested'):
            self.assert_rc(self.call('install', target=root), 2)
        self.assertFalse((self.source / '.hackathon-kit').exists())

    def test_pre_submit_runs_installed_gate_and_propagates_failure(self):
        gate = self.source / 'scripts/gate_check.py'
        gate.write_text(gate.read_text().replace('raise SystemExit(main())', 'print("GATE_ARGS", __import__("sys").argv[1:])\n    raise SystemExit(main())'))
        self.install()
        self.assert_rc(self.call('doctor'), 0)
        r = self.call('doctor', '--pre-submit')
        self.assert_rc(r, 2)
        self.assertIn('GATE_ARGS', r.stdout)
        self.assertIn('--kit', r.stdout)
        self.assertIn('Pre-submit gate check failed', r.stdout)

    def test_default_doctor_uses_bulleted_gate_parser_and_closed_evidence(self):
        self.install()
        state = self.target / '.hackathon-kit/run/STATE.md'
        self.assertIn('- constraint_gate: OPEN', state.read_text())
        r = self.call('doctor')
        self.assert_rc(r, 0)
        self.assertIn('Constraint gate is open', r.stdout)
        state.write_text(state.read_text().replace('constraint_gate: OPEN', 'constraint_gate: CLOSED'))
        r = self.call('doctor')
        self.assert_rc(r, 2)
        self.assertIn('GATE FAIL', r.stdout)
        self.assertIn('Closed gate evidence check failed', r.stdout)
        self.assertNotIn('Constraint gate is open', r.stdout)
        self.assertFalse(list((self.target / '.hackathon-kit').rglob('__pycache__')))

    def test_default_doctor_rejects_duplicate_and_malformed_statuses(self):
        self.install()
        state = self.target / '.hackathon-kit/run/STATE.md'
        original = state.read_text()
        state.write_text(original + '\n- constraint_gate: CLOSED\n')
        r = self.call('doctor')
        self.assert_rc(r, 2)
        self.assertIn('duplicate key constraint_gate', r.stdout)
        for value in ('CLOSED accidentally', 'BROKEN_STATUS', 'open'):
            state.write_text(original.replace('constraint_gate: OPEN', 'constraint_gate: ' + value))
            r = self.call('doctor')
            self.assert_rc(r, 2)
            self.assertIn('invalid or missing status constraint_gate', r.stdout)

    @unittest.skipUnless(os.name == 'posix' and shutil.which('bash'), 'Bash entry points are exercised on POSIX; Windows uses PowerShell')
    def test_bash_wrappers_use_shared_backend(self):
        r = subprocess.run(['bash', str(self.source / 'install.sh'), str(self.target)], capture_output=True, text=True)
        self.assert_rc(r, 0)
        r = subprocess.run(['bash', str(self.target / '.hackathon-kit/scripts/doctor.sh')], capture_output=True, text=True)
        self.assert_rc(r, 0)
        r = subprocess.run(['bash', str(self.target / '.hackathon-kit/scripts/clean.sh')], capture_output=True, text=True)
        self.assert_rc(r, 0)
        self.assertTrue((self.target / '.hackathon-kit').exists())


if __name__ == '__main__':
    unittest.main()
