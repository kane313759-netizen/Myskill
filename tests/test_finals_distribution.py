"""Finals assets must survive distribution, installation, updates and cleanup."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class FinalsDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='myskill-finals-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.target = self.base / 'task'
        self.source.mkdir()
        self.target.mkdir()
        self.archive = self.base / 'kit.zip'
        result = self.run_python(ROOT / 'scripts/package_release.py', '--source', ROOT,
                                 '--output', self.archive, '--include-untracked')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIsNone(archive.testzip())
            archive.extractall(self.source)

    def run_python(self, *args):
        return subprocess.run([sys.executable, '-B', *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def install(self):
        return self.run_python(self.source / 'scripts/kit_lifecycle.py', 'install',
                               '--source', self.source, '--target', self.target)

    def test_finals_assets_installed_owned_and_notes_preserved_on_reinstall(self):
        user_file = self.target / 'TASK.md'
        user_file.write_text('preserve original task', encoding='utf-8')
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        kit = self.target / '.hackathon-kit'
        manifest = json.loads((kit / 'manifest.json').read_text(encoding='utf-8'))
        self.assertIn('hackathon-finals', manifest['owned_skills'])
        self.assertEqual((self.target / '.agents/skills/hackathon-finals/SKILL.md').read_bytes(),
                         (ROOT / '.agents/skills/hackathon-finals/SKILL.md').read_bytes())
        for rel in ('FINALS_POLICY.md', 'references/finals-playbook.md',
                    'templates/FINALS_RUN.md'):
            self.assertEqual((kit / rel).read_bytes(), (ROOT / rel).read_bytes())
            self.assertEqual(manifest['managed_files'][rel],
                             hashlib.sha256((kit / rel).read_bytes()).hexdigest())
        note = kit / 'run/FINALS_RUN.md'
        note.write_text('actual finals evidence retained', encoding='utf-8')
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(note.read_text(encoding='utf-8'), 'actual finals evidence retained')
        self.assertEqual(user_file.read_text(encoding='utf-8'), 'preserve original task')
        result = self.run_python(kit / 'scripts/kit_lifecycle.py', 'doctor', '--kit', kit)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # Installation success must not be advertised as finals submission approval.
        self.assertIn('does not establish finals readiness', result.stdout)
        self.assertEqual((kit / 'EXAM_POLICY.md').read_bytes(),
                         (ROOT / 'EXAM_POLICY.md').read_bytes())

    def test_existing_unrelated_finals_skill_blocks_before_task_writes(self):
        skill = self.target / '.agents/skills/hackathon-finals/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('existing unrelated skill', encoding='utf-8')
        before = {p.relative_to(self.target): p.read_bytes()
                  for p in self.target.rglob('*') if p.is_file()}
        result = self.install()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('Required skill name collision: hackathon-finals', result.stderr)
        self.assertFalse((self.target / '.hackathon-kit').exists())
        self.assertEqual(before, {p.relative_to(self.target): p.read_bytes()
                                 for p in self.target.rglob('*') if p.is_file()})

    def test_missing_finals_playbook_cannot_produce_incomplete_release(self):
        (self.source / 'references/finals-playbook.md').unlink()
        output = self.base / 'incomplete.zip'
        result = self.run_python(self.source / 'scripts/package_release.py', '--source',
                                 self.source, '--output', output)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('references/finals-playbook.md', result.stderr)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
