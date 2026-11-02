"""Use the unpacked distribution as a participant would, without -B or test-only setup."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class DistributionIntegrationTests(unittest.TestCase):
    def test_flat_archive_install_data_tools_doctor_and_clean(self):
        with tempfile.TemporaryDirectory(prefix='myskill-full-') as temporary:
            base = Path(temporary)
            archive = base / 'kit.zip'
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/package_release.py'), '--source', str(ROOT), '--output', str(archive), '--include-untracked'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            source, target = base / 'source', base / 'task'
            source.mkdir()
            target.mkdir()
            with zipfile.ZipFile(archive) as package:
                self.assertIn('install.sh', package.namelist())
                self.assertFalse(any(name.endswith('.zip') for name in package.namelist()))
                package.extractall(source)
            (target / 'sample.csv').write_bytes('id,customer_wait_time\n001,10\n002,180\n'.encode('cp949'))
            backend = source / 'scripts/kit_lifecycle.py'
            def run(*args):
                return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
            install = run(backend, 'install', '--source', source, '--target', target)
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            scripts = target / '.hackathon-kit/scripts'
            for name in ('profile_data.py', 'sanity_check.py'):
                result = run(scripts / name, target / 'sample.csv')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('customer_wait_time', result.stdout)
                self.assertIn('max=180', result.stdout)
            self.assertFalse(list((target / '.hackathon-kit').rglob('__pycache__')))
            result = run(scripts / 'kit_lifecycle.py', 'doctor', '--kit', scripts.parent)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = run(scripts / 'kit_lifecycle.py', 'clean', '--kit', scripts.parent, '--apply')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            backup = Path(next(line.split(': ', 1)[1] for line in result.stdout.splitlines() if line.startswith('Run-note backup: ')))
            try:
                self.assertTrue((backup / 'run/STATE.md').is_file())
            finally:
                shutil.rmtree(backup)
            self.assertFalse((target / '.hackathon-kit').exists())
            self.assertTrue((target / 'sample.csv').is_file())


if __name__ == '__main__':
    unittest.main()
