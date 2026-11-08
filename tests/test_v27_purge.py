"""Purge only fully verified snapshots before the unchanged kit cleanup."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest

from test_v27_snapshot import snapshot, remove_test_tree, OBSERVED

ROOT = Path(__file__).resolve().parents[1]


class SnapshotPurgeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='v27-purge-'))
        self.addCleanup(remove_test_tree, self.root)
        (self.root / 'product.txt').write_bytes(b'original product\n')
        self.manifest = {'files': ['product.txt']}

    def create(self, name='FINAL'):
        return Path(snapshot.create_snapshot(self.root, self.manifest, name, now=OBSERVED)['path'])

    def cli(self, *args):
        return subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/snapshot.py'), 'purge',
                               '--root', str(self.root)] + list(args), capture_output=True,
                              text=True, encoding='utf-8')

    def test_preview_preserves_readonly_snapshots_and_apply_removes_empty_parent(self):
        first, second = self.create('M1'), self.create('FINAL')
        before = {str(p): (p.read_bytes(), p.stat().st_mode) for p in first.parent.rglob('*') if p.is_file()}
        preview = self.cli()
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertEqual(json.loads(preview.stdout)['status'], 'PREVIEW')
        self.assertEqual(before, {str(p): (p.read_bytes(), p.stat().st_mode) for p in first.parent.rglob('*') if p.is_file()})
        self.assertTrue(all(snapshot._readonly(p) for path in (first, second) for p in sum(snapshot._walk(path), [])))
        applied = self.cli('--apply')
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertEqual(json.loads(applied.stdout)['status'], 'PURGED')
        self.assertFalse(first.parent.exists())
        self.assertEqual((self.root / 'product.txt').read_bytes(), b'original product\n')

    def test_any_foreign_direct_entry_refuses_before_deleting_valid_snapshot(self):
        path = self.create()
        foreign = path.parent / 'keep.txt'
        foreign.write_bytes(b'foreign content')
        for apply in (False, True):
            with self.assertRaisesRegex(ValueError, 'unrecognized|unexpected'):
                snapshot.purge(self.root, apply=apply)
            self.assertEqual(snapshot.verify_snapshot(path)['status'], 'VERIFIED')
            self.assertEqual(foreign.read_bytes(), b'foreign content')
        result = self.cli('--apply')
        self.assertEqual(result.returncode, 2)
        self.assertTrue(path.exists())

    def test_unknown_empty_directory_inside_valid_snapshot_is_preserved(self):
        path = self.create()
        os.chmod(str(path), stat.S_IRWXU)
        unknown = path / 'unknown-empty'
        unknown.mkdir()
        snapshot._set_readonly(unknown, directory=True)
        snapshot._set_readonly(path, directory=True)
        with self.assertRaisesRegex(ValueError, 'unexpected'):
            snapshot.purge(self.root, apply=True)
        self.assertTrue(unknown.exists())

    def test_invalid_name_or_marker_refuses_whole_inventory(self):
        valid = self.create()
        foreign = valid.parent / 'foreign-directory'
        foreign.mkdir()
        (foreign / 'MANIFEST.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unrecognized|unexpected'):
            snapshot.purge(self.root, apply=True)
        self.assertTrue(valid.exists())
        self.assertTrue(foreign.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows junction boundary')
    def test_junction_direct_entry_never_follows_or_deletes_external_content(self):
        import _winapi
        valid = self.create()
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'keep.txt').write_bytes(b'outside stays')
        junction = valid.parent / 'foreign-junction'
        _winapi.CreateJunction(str(outside), str(junction))
        try:
            with self.assertRaisesRegex(ValueError, 'linked|reparse'):
                snapshot.purge(self.root, apply=True)
            self.assertEqual((outside / 'keep.txt').read_bytes(), b'outside stays')
            self.assertTrue(valid.exists())
        finally:
            junction.rmdir()

    def test_no_snapshot_directory_is_a_readonly_noop(self):
        result = snapshot.purge(self.root)
        self.assertEqual(result['status'], 'PREVIEW')
        self.assertEqual(result['snapshots'], [])
        self.assertFalse((self.root / '.hackathon-kit').exists())

    def test_readonly_snapshots_parent_and_empty_collection_are_removed(self):
        path = self.create()
        parent = path.parent
        snapshot._set_readonly(parent, directory=True)
        self.assertEqual(snapshot.purge(self.root)['status'], 'PREVIEW')
        self.assertTrue(snapshot._readonly(parent))
        self.assertEqual(snapshot.purge(self.root, apply=True)['status'], 'PURGED')
        self.assertFalse(parent.exists())
        parent.mkdir()
        self.assertEqual(snapshot.purge(self.root)['snapshots'], [])
        self.assertFalse(snapshot.purge(self.root)['parent_removed'])
        self.assertTrue(snapshot.purge(self.root, apply=True)['parent_removed'])

    def test_hardlinked_payload_refuses_without_changing_external_attributes(self):
        path = self.create()
        copied = path / 'files/product.txt'
        external = self.root / 'external.txt'
        external.write_bytes(copied.read_bytes())
        os.chmod(str(copied.parent), stat.S_IRWXU)
        os.chmod(str(copied), stat.S_IREAD | stat.S_IWRITE)
        copied.unlink()
        try:
            os.link(str(external), str(copied))
        except (OSError, NotImplementedError) as error:
            self.skipTest('hardlink creation unavailable: ' + str(error))
        snapshot._set_readonly(copied)
        snapshot._set_readonly(copied.parent, directory=True)
        original = external.stat().st_mode
        with self.assertRaisesRegex(ValueError, 'hard-linked'):
            snapshot.purge(self.root, apply=True)
        self.assertEqual(external.stat().st_mode, original)
        self.assertEqual(external.read_bytes(), b'original product\n')
        self.assertTrue(path.exists())

    def test_installed_snapshot_purge_allows_original_clean(self):
        installer = runpy.run_path(str(ROOT / 'scripts/install_v27.py'))
        with contextlib.redirect_stdout(io.StringIO()):
            installer['install'](ROOT, self.root)
        kit = self.root / '.hackathon-kit'
        doctor = subprocess.run([sys.executable, '-I', str(kit / 'scripts/kit_lifecycle.py'),
                                 'doctor', '--kit', str(kit)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
        self.create()
        original_clean = [sys.executable, '-I', str(kit / 'scripts/kit_lifecycle.py'), 'clean', '--kit', str(kit), '--apply']
        blocked = subprocess.run(original_clean, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(blocked.returncode, 2)
        self.assertIn('Unexpected helper content', blocked.stderr)
        preview = self.cli()
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertTrue((kit / 'snapshots').exists())
        purge = subprocess.run([sys.executable, '-I', str(kit / 'scripts/snapshot.py'), 'purge',
                                '--root', str(self.root), '--apply'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(purge.returncode, 0, purge.stdout + purge.stderr)
        clean = subprocess.run(original_clean, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        self.assertFalse(kit.exists())
        self.assertEqual((self.root / 'product.txt').read_bytes(), b'original product\n')


if __name__ == '__main__':
    unittest.main()
