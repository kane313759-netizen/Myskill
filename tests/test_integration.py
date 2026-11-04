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

            # Exercise an actual pre-edit/final evaluator through the installed CLI.
            candidate, checker = target / 'candidate.py', target / 'checker.py'
            (target / 'TASK.md').write_text('Read one integer and print that integer plus one.\n')
            candidate.write_text('print(0)\n')
            checker.write_text(
                'import hashlib,json,pathlib,subprocess,sys\n'
                'candidate=pathlib.Path(sys.argv[1])\n'
                'checks=[]\n'
                'for index,(value,expected) in enumerate([(\"1\",\"2\"),(\"0\",\"1\"),(\"-2\",\"-1\")]):\n'
                '    result=subprocess.run([sys.executable,str(candidate)],input=value,capture_output=True,text=True,timeout=2)\n'
                '    checks.append({\"id\":\"case\"+str(index),\"status\":\"PASS\" if result.returncode==0 and result.stdout.strip()==expected else \"FAIL\",\"evidence\":\"input=\"+value+\" expected=\"+expected+\" native_exit=\"+str(result.returncode)+\" stdout=\"+repr(result.stdout)})\n'
                'print(json.dumps({\"version\":1,\"label\":sys.argv[2],\"evaluated_version\":hashlib.sha256(candidate.read_bytes()).hexdigest(),\"evaluation_scope\":\"integer-cases-v1;timeout=2\",\"checks\":checks}))\n'
            )
            notes = target / '.hackathon-kit/run'
            rubric = notes / 'LOCAL_RUBRIC.json'
            rubric.write_text(json.dumps({
                'version': 1, 'unknowns': ['No hidden test score is available.'],
                'criteria': [{'id': 'case' + str(i), 'description': 'Required integer case',
                              'source': 'TASK.md: integer plus one', 'oracle': expected}
                             for i, expected in enumerate(['2', '1', '-1'])]
            }))
            observations = target / 'observations.json'
            baseline = notes / 'local-baseline.json'
            def score(label, compare=None):
                native = run(checker, candidate, label)
                self.assertEqual(native.returncode, 0, native.stderr)
                observations.write_text(native.stdout)
                args = [scripts / 'local_score.py', '--rubric', rubric,
                        '--results', observations, '--evaluator', checker]
                if compare:
                    args += ['--compare', compare]
                return run('-I', '-S', '-B', *args)
            initial = score('baseline')
            self.assertEqual(initial.returncode, 1, initial.stdout + initial.stderr)
            self.assertEqual(json.loads(initial.stdout)['score']['earned'], 0)
            baseline.write_text(initial.stdout)
            original_baseline = baseline.read_bytes()
            candidate.write_text('import sys\nprint(int(sys.stdin.read())+1)\n')
            final = score('final', baseline)
            self.assertEqual(final.returncode, 0, final.stdout + final.stderr)
            final_report = json.loads(final.stdout)
            self.assertEqual(final_report['score']['earned'], 3)
            self.assertEqual(final_report['comparison']['delta']['earned'], 3)
            self.assertNotEqual(final_report['evaluated_version'], json.loads(initial.stdout)['evaluated_version'])
            self.assertEqual(baseline.read_bytes(), original_baseline)
            rubric_bytes = rubric.read_bytes()
            reinstall = run(backend, 'install', '--source', source, '--target', target)
            self.assertEqual(reinstall.returncode, 0, reinstall.stdout + reinstall.stderr)
            self.assertEqual(rubric.read_bytes(), rubric_bytes)
            self.assertEqual(baseline.read_bytes(), original_baseline)
            self.assertFalse(list((target / '.hackathon-kit').rglob('__pycache__')))
            result = run(scripts / 'kit_lifecycle.py', 'doctor', '--kit', scripts.parent)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = run(scripts / 'kit_lifecycle.py', 'clean', '--kit', scripts.parent, '--apply')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            backup = Path(next(line.split(': ', 1)[1] for line in result.stdout.splitlines() if line.startswith('Run-note backup: ')))
            try:
                self.assertTrue((backup / 'run/STATE.md').is_file())
                self.assertEqual((backup / 'run/local-baseline.json').read_bytes(), original_baseline)
                self.assertEqual((backup / 'run/LOCAL_RUBRIC.json').read_bytes(), rubric_bytes)
            finally:
                shutil.rmtree(backup)
            self.assertFalse((target / '.hackathon-kit').exists())
            self.assertTrue((target / 'sample.csv').is_file())


if __name__ == '__main__':
    unittest.main()
