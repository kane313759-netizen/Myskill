"""Exercise actual bounded copies, read-only attributes, verification and retention."""
from datetime import datetime, timedelta, timezone
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

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('v27_snapshot', ROOT / 'scripts/snapshot.py')
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)
OBSERVED = datetime(2026, 11, 8, 9, 0, tzinfo=timezone.utc)


def remove_test_tree(path):
    """Clear attributes only inside this independently created temporary test root."""
    path = Path(path).absolute()
    if snapshot._linked(path):
        raise ValueError('temporary cleanup root must not be a link/reparse path')
    root = path.resolve()
    # Make parent directories writable before rmtree attempts any child unlink.
    # Do not follow an unexpected link out of this private test fixture.
    for directory, names, files in os.walk(str(path), topdown=True, followlinks=False):
        current = Path(directory)
        if snapshot._linked(current) or (current.resolve() != root and root not in current.resolve().parents):
            raise ValueError('temporary cleanup escaped its own root')
        os.chmod(str(current), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        for name in names + files:
            if snapshot._linked(current / name):
                raise ValueError('unexpected link/reparse path in temporary fixture')
    def writable_retry(function, target, error):
        os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        function(target)
    shutil.rmtree(str(path), onerror=writable_retry)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='v27-snapshot-'))
        self.addCleanup(remove_test_tree, self.root)
        for relative, content in {'src/code.py': b'print("baseline")\n',
                                  'config.json': b'{"limit": 3}\n',
                                  '.hackathon-kit/run/NOTE.md': b'Observed example run.\n',
                                  'data/raw.csv': b'id,value\n1,2\n'}.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.manifest = {'files': ['src/code.py', 'config.json', '.hackathon-kit/run/NOTE.md'],
                         'data_files': ['data/raw.csv']}

    def create(self, name='CHECK', now=OBSERVED, **options):
        return snapshot.create_snapshot(self.root, self.manifest, name, now=now, **options)

    def test_explicit_copy_raw_data_hash_only_and_original_unchanged(self):
        originals = {relative: ((self.root / relative).read_bytes(),
                               (self.root / relative).stat())
                     for relative in self.manifest['files'] + self.manifest['data_files']}
        result = self.create()
        self.assertEqual(result['status'], 'VERIFIED')
        path = Path(result['path'])
        record = json.loads((path / 'MANIFEST.json').read_text(encoding='utf-8'))
        for relative in self.manifest['files']:
            self.assertEqual((path / 'files' / relative).read_bytes(), originals[relative][0])
        self.assertFalse((path / 'files/data/raw.csv').exists())
        raw = originals['data/raw.csv'][0]
        self.assertEqual(record['data_files']['data/raw.csv'],
                         {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
        self.assertEqual(result['copied_files'], 3)
        self.assertEqual(result['data_hashes'], 1)
        for relative, (content, info) in originals.items():
            target = self.root / relative
            self.assertEqual(target.read_bytes(), content)
            self.assertEqual(target.stat().st_mode, info.st_mode)
            if os.name == 'nt':
                self.assertEqual(target.stat().st_file_attributes, info.st_file_attributes)
        self.assertEqual(snapshot.verify_snapshot(path)['status'], 'VERIFIED')
        self.assertEqual(snapshot.verify_snapshot(path / 'MANIFEST.json')['status'], 'VERIFIED')

    def test_all_snapshot_files_and_directories_are_readonly(self):
        path = Path(self.create()['path'])
        files, directories = snapshot._walk(path)
        self.assertTrue(all(snapshot._readonly(item) for item in files + directories))
        self.assertFalse(snapshot._readonly(self.root / 'src/code.py'))
        self.assertIn('not remote backup or OS isolation', snapshot.verify_snapshot(path)['notice'])

    def test_same_name_same_clock_observation_creates_distinct_snapshots(self):
        first, second = self.create(), self.create()
        self.assertNotEqual(first['path'], second['path'])
        self.assertTrue(Path(first['path']).exists())
        self.assertTrue(Path(second['path']).exists())

    def test_content_tamper_and_attribute_tamper_fail_verification(self):
        path = Path(self.create()['path'])
        copied = path / 'files/src/code.py'
        os.chmod(str(copied), stat.S_IREAD | stat.S_IWRITE)
        with self.assertRaisesRegex(ValueError, 'read-only'):
            snapshot.verify_snapshot(path)
        copied.write_bytes(b'print("tampered")\n')
        snapshot._set_readonly(copied)
        with self.assertRaisesRegex(ValueError, 'changed'):
            snapshot.verify_snapshot(path)
        self.assertEqual((self.root / 'src/code.py').read_bytes(), b'print("baseline")\n')

    def test_retention_keeps_named_pins_latest_five_and_unverified_directories(self):
        self.create('M1', OBSERVED)
        self.create('FINAL', OBSERVED + timedelta(seconds=1))
        snapshots = self.root / '.hackathon-kit/snapshots'
        foreign = snapshots / 'foreign'
        foreign.mkdir()
        (foreign / 'keep.txt').write_text('unknown owner', encoding='utf-8')
        tampered = Path(self.create('BROKEN', OBSERVED + timedelta(seconds=2))['path'])
        # Windows directory readonly is an attribute, not access-control isolation.
        os.chmod(str(tampered), stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        (tampered / 'foreign.txt').write_text('preserve unknown addition', encoding='utf-8')
        snapshot._set_readonly(tampered, directory=True)
        records = []
        for index in range(7):
            records.append(self.create('CP' + str(index), OBSERVED + timedelta(minutes=index + 1)))
        known_names = []
        for item in snapshots.iterdir():
            try:
                known_names.append(snapshot.verify_snapshot(item)['name'])
            except (OSError, ValueError):
                pass
        self.assertEqual(set(known_names), {'M1', 'FINAL', 'CP2', 'CP3', 'CP4', 'CP5', 'CP6'})
        self.assertFalse(Path(records[0]['path']).exists())
        self.assertFalse(Path(records[1]['path']).exists())
        self.assertEqual((foreign / 'keep.txt').read_text(encoding='utf-8'), 'unknown owner')
        self.assertEqual((tampered / 'foreign.txt').read_text(encoding='utf-8'), 'preserve unknown addition')
        self.assertIn('foreign', records[-1]['retention']['preserved_unverified'])
        self.assertIn(tampered.name, records[-1]['retention']['preserved_unverified'])

    def test_retention_unlinks_only_after_owned_parents_are_writable(self):
        path = Path(self.create()['path'])
        files, directories = snapshot._walk(path)
        self.assertTrue(all(snapshot._readonly(item) for item in files + directories))
        parent = path.parent
        foreign = parent / 'unverified-foreign'
        foreign.mkdir()
        unknown = foreign / 'keep.txt'
        unknown.write_bytes(b'preserve foreign fixture')
        snapshot._set_readonly(unknown)
        source = self.root / 'src/code.py'
        unchanged = {item: (item.stat().st_mode, item.read_bytes() if item.is_file() else None)
                     for item in (parent, foreign, unknown, source)}
        original_unlink, removed = Path.unlink, []

        def posix_unlink(target, *args, **kwargs):
            # Enforce POSIX's parent-write requirement even on Windows or a
            # privileged POSIX runner, so the original order fails everywhere.
            if not target.parent.stat().st_mode & stat.S_IWUSR:
                raise PermissionError('cannot unlink from a readonly parent directory')
            self.assertIn(path, target.parents)
            removed.append(target)
            return original_unlink(target, *args, **kwargs)

        with mock.patch.object(Path, 'unlink', new=posix_unlink):
            snapshot._remove_owned_snapshot(parent, path)
        self.assertFalse(path.exists())
        self.assertEqual(len(removed), len(files))
        for item, (mode, content) in unchanged.items():
            self.assertEqual(item.stat().st_mode, mode)
            if content is not None:
                self.assertEqual(item.read_bytes(), content)

    def test_fixture_cleanup_handles_readonly_parent_directories(self):
        fixture = self.root / 'cleanup-fixture'
        nested = fixture / 'nested'
        nested.mkdir(parents=True)
        leaf = nested / 'readonly.txt'
        leaf.write_bytes(b'owned test fixture')
        snapshot._set_readonly(leaf)
        snapshot._set_readonly(nested, directory=True)
        snapshot._set_readonly(fixture, directory=True)
        self.assertTrue(all(snapshot._readonly(item) for item in (fixture, nested, leaf)))
        remove_test_tree(fixture)
        self.assertFalse(fixture.exists())

    def test_traversal_metadata_directories_and_duplicate_paths_are_rejected(self):
        for relative in ('../outside.py', '..\\outside.py', str(self.root / 'config.json'),
                         'C:\\outside.py', 'src', 'config.json:secret'):
            with self.subTest(relative=relative), self.assertRaises((OSError, ValueError)):
                snapshot.create_snapshot(self.root, {'files': [relative]}, 'REJECT', now=OBSERVED)
        for relative in ('.git/config', '.GIT/config', '.agents/skills/task/SKILL.md',
                         '.hackathon-kit/snapshots/old/MANIFEST.json', '.hackathon-kit/scripts/helper.py'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'protected metadata')
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, 'cannot be snapshotted'):
                snapshot.create_snapshot(self.root, {'files': [relative]}, 'REJECT', now=OBSERVED)
        for manifest in ({'files': ['config.json', './config.json']},
                         {'files': ['config.json'], 'data_files': ['config.json']}):
            with self.assertRaisesRegex(ValueError, 'duplicate or overlapping'):
                snapshot.create_snapshot(self.root, manifest, 'REJECT', now=OBSERVED)

    def test_manifest_count_per_file_total_and_clock_limits(self):
        with mock.patch.object(snapshot, 'MAX_FILES', 1), self.assertRaisesRegex(ValueError, 'file-count'):
            self.create()
        with mock.patch.object(snapshot, 'MAX_FILE_BYTES', 3), self.assertRaisesRegex(ValueError, 'bounded regular'):
            self.create()
        with mock.patch.object(snapshot, 'MAX_TOTAL_BYTES', 4), self.assertRaisesRegex(ValueError, 'total-byte'):
            self.create()
        with self.assertRaisesRegex(ValueError, 'timezone'):
            self.create(now=datetime(2026, 11, 8, 9, 0))
        for name in ('../BAD', '', 'unsafe name'):
            with self.assertRaises(ValueError):
                self.create(name=name)
        with self.assertRaises(ValueError):
            self.create(keep_recent=0)

    def test_symlink_or_reparse_sources_are_rejected_when_supported(self):
        link = self.root / 'linked.py'
        try:
            link.symlink_to(self.root / 'src/code.py')
        except (OSError, NotImplementedError) as error:
            self.skipTest('symlink creation unavailable: ' + str(error))
        self.addCleanup(lambda: link.unlink() if link.is_symlink() else None)
        with self.assertRaisesRegex(ValueError, 'symlink/junction/reparse'):
            snapshot.create_snapshot(self.root, {'files': ['linked.py']}, 'REJECT', now=OBSERVED)

    def test_isolated_cli_creation_and_verification(self):
        manifest = self.root / 'snapshot-input.json'
        manifest.write_text(json.dumps(self.manifest), encoding='utf-8')
        original = manifest.read_bytes()
        prefix = [sys.executable, '-I', '-X', 'utf8', str(ROOT / 'scripts/snapshot.py')]
        result = subprocess.run(prefix + ['create', '--root', str(self.root), '--manifest', str(manifest),
                                          '--name', 'CLI'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        result = subprocess.run(prefix + ['verify', '--snapshot', value['path']],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'VERIFIED')
        self.assertEqual(manifest.read_bytes(), original)

    def test_hash_only_record_cannot_also_declare_copied_payload(self):
        path = Path(self.create()['path'])
        marker = path / 'MANIFEST.json'
        record = json.loads(marker.read_text(encoding='utf-8'))
        record['data_files']['src/code.py'] = record['files']['src/code.py']
        os.chmod(str(marker), stat.S_IREAD | stat.S_IWRITE)
        marker.write_text(json.dumps(record), encoding='utf-8')
        snapshot._set_readonly(marker)
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            snapshot.verify_snapshot(path)


if __name__ == '__main__':
    unittest.main()
