"""Additive distribution must preserve baseline bytes and ownership boundaries."""
import contextlib
import ast
import io
import json
import re
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMON = runpy.run_path(str(ROOT / 'scripts/v27_common.py'))
PACKAGE = runpy.run_path(str(ROOT / 'scripts/package_v27.py'))
INSTALL = runpy.run_path(str(ROOT / 'scripts/install_v27.py'))


class AddonTests(unittest.TestCase):
    def test_protected_baseline_and_state_keys_unchanged(self):
        self.assertEqual(COMMON['check_protected'](ROOT), [])
        manifest = COMMON['read_json'](ROOT / 'references/v27-baseline.json')
        self.assertEqual(len(manifest['files']), 112)
        self.assertEqual(manifest['baseline_commit'], 'affd3c1623f67697247c67f6d30df9e76b9bc076')

    def test_additive_helpers_have_no_outbound_network_imports(self):
        blocked = {'socket', 'http', 'urllib', 'requests', 'httpx', 'ftplib', 'smtplib', 'boto3', 'paramiko'}
        baseline = COMMON['read_json'](ROOT / 'references/v27-baseline.json')['files']
        for path in (ROOT / 'scripts').glob('*.py'):
            if path.relative_to(ROOT).as_posix() in baseline:
                continue
            for node in ast.walk(ast.parse(path.read_bytes())):
                if isinstance(node, ast.Import):
                    self.assertFalse(blocked & {item.name.split('.')[0] for item in node.names}, path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0], blocked, path.name)

    def test_v27_bootstrap_is_packaged(self):
        with tempfile.TemporaryDirectory(prefix='v27-bootstrap-') as tmp:
            archive = Path(tmp) / 'kit.zip'
            with contextlib.redirect_stdout(io.StringIO()):
                PACKAGE['build'](ROOT, archive, include_untracked=True)
            with zipfile.ZipFile(archive) as bundle:
                self.assertIn('BOOTSTRAP_V27.md', bundle.namelist())
                text = bundle.read('BOOTSTRAP_V27.md').decode('utf-8')
                blocks = re.findall(r'```text\n(.*?)\n```', text, re.S)
                self.assertEqual(len(blocks), 2)
                self.assertEqual(len(blocks[0].splitlines()), 1)
                self.assertIn('$hackathon-orchestrator-universal', blocks[0])
                self.assertLessEqual(len(blocks[1].splitlines()), 25)

    def test_package_install_reinstall_doctor_and_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='v27-dist-') as tmp:
            base = Path(tmp)
            archive, source, target = base / 'kit.zip', base / 'source', base / 'task'
            with contextlib.redirect_stdout(io.StringIO()):
                result = PACKAGE['build'](ROOT, archive, include_untracked=True)
            self.assertTrue(result['baseline_preserved'])
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
                self.assertTrue(set(INSTALL['MANDATORY']) <= names)
                self.assertTrue(set(PACKAGE['EXTRAS']) <= names)
                self.assertIn('.agents/skills/hackathon-orchestrator-universal/SKILL.md', names)
                self.assertFalse(any('/run/' in p or p.startswith('outputs/') or p.startswith('.git/') for p in names))
                bundle.extractall(source)
            self.assertEqual(COMMON['check_protected'](source), [])
            target.mkdir()
            task = target / 'TASK.txt'
            task.write_text('original task', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                installed = INSTALL['install'](source, target)
            self.assertEqual(installed['status'], 'INSTALLED')
            kit = target / '.hackathon-kit'
            self.assertEqual((kit / 'BOOTSTRAP_V27.md').read_bytes(), (source / 'BOOTSTRAP_V27.md').read_bytes())
            self.assertIn('BOOTSTRAP_V27.md', COMMON['read_json'](kit / 'manifest.json')['managed_files'])
            notes = kit / 'run/ENV.md'
            notes.write_text('actual user notes', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                INSTALL['install'](source, target)
            self.assertEqual(notes.read_text(encoding='utf-8'), 'actual user notes')
            self.assertEqual(task.read_text(encoding='utf-8'), 'original task')
            # A verified, unchanged owned r0/r1 installation can receive a skill
            # update; unrelated/local edits remain protected by the collision test.
            skill = source / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
            skill.write_bytes(skill.read_bytes() + b'\nUpdated source skill fixture.\n')
            with contextlib.redirect_stdout(io.StringIO()):
                INSTALL['install'](source, target)
            self.assertEqual((target / '.agents/skills/hackathon-orchestrator-universal/SKILL.md').read_bytes(), skill.read_bytes())
            self.assertEqual(notes.read_text(encoding='utf-8'), 'actual user notes')
            doctor = subprocess.run([sys.executable, '-I', str(kit / 'scripts/kit_lifecycle.py'),
                                     'doctor', '--kit', str(kit)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            cleanup = subprocess.run([sys.executable, '-I', str(kit / 'scripts/kit_lifecycle.py'),
                                      'clean', '--kit', str(kit), '--apply'], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(cleanup.returncode, 0, cleanup.stdout + cleanup.stderr)
            self.assertFalse(kit.exists())
            self.assertTrue(task.exists())

    def test_new_skill_collision_fails_before_task_writes(self):
        with tempfile.TemporaryDirectory(prefix='v27-collision-') as tmp:
            target = Path(tmp)
            existing = target / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
            existing.parent.mkdir(parents=True)
            existing.write_text('user owned', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'collision'):
                INSTALL['install'](ROOT, target)
            self.assertFalse((target / '.hackathon-kit').exists())
            self.assertEqual(existing.read_text(encoding='utf-8'), 'user owned')

    def test_changed_bootstrap_is_preserved_before_any_backend_writes(self):
        with tempfile.TemporaryDirectory(prefix='v27-bootstrap-collision-') as tmp:
            target = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                INSTALL['install'](ROOT, target)
            bootstrap = target / '.hackathon-kit/BOOTSTRAP_V27.md'
            bootstrap.write_text('user modified bootstrap', encoding='utf-8')
            sentinel = target / '.hackathon-kit/scripts/deadline.py'
            before = sentinel.stat().st_mtime_ns
            with self.assertRaisesRegex(ValueError, 'BOOTSTRAP_V27'):
                INSTALL['install'](ROOT, target)
            self.assertEqual(bootstrap.read_text(encoding='utf-8'), 'user modified bootstrap')
            self.assertEqual(sentinel.stat().st_mtime_ns, before)

    def test_isolated_package_cli(self):
        with tempfile.TemporaryDirectory(prefix='v27-cli-') as tmp:
            result = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/package_v27.py'),
                                     '--source', str(ROOT), '--output', str(Path(tmp) / 'v27.zip'),
                                     '--include-untracked'], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows junction regression')
    def test_junction_blocked_before_any_backend_write(self):
        import _winapi
        with tempfile.TemporaryDirectory(prefix='v27-junction-') as tmp:
            base = Path(tmp)
            target, outside = base / 'task', base / 'outside'
            outside.mkdir()
            kit = target / '.hackathon-kit'
            kit.mkdir(parents=True)
            _winapi.CreateJunction(str(outside), str(kit / 'scripts'))
            try:
                with self.assertRaisesRegex(ValueError, 'reparse'):
                    INSTALL['install'](ROOT, target)
                self.assertEqual(list(outside.iterdir()), [])
                self.assertFalse((target / '.agents').exists())
            finally:
                (kit / 'scripts').rmdir()

    @unittest.skipUnless(sys.platform == 'win32', 'Windows Git junction regression')
    def test_git_exclude_junction_rejected_before_install(self):
        import _winapi
        with tempfile.TemporaryDirectory(prefix='v27-git-junction-') as tmp:
            base = Path(tmp)
            target, outside = base / 'task', base / 'outside'
            target.mkdir()
            subprocess.run(['git', 'init', '-q', str(target)], check=True, capture_output=True)
            info = target / '.git/info'
            info.rename(outside)
            exclude = outside / 'exclude'
            original = exclude.read_bytes()
            _winapi.CreateJunction(str(outside), str(info))
            try:
                with self.assertRaisesRegex(ValueError, 'reparse'):
                    INSTALL['install'](ROOT, target)
                self.assertEqual(exclude.read_bytes(), original)
                self.assertFalse((target / '.hackathon-kit').exists())
            finally:
                info.rmdir()


if __name__ == '__main__':
    unittest.main()
