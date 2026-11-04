"""Installed instructions must name kit files by paths that resolve from the task root."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
# A kit-relative file mention: prompts/, references/, scripts/, templates/ or run/ plus a
# file name. Optional .hackathon-kit/ or .agents/ prefix; placeholders like <x.py> do not match.
TOKEN = re.compile(
    r'(?<![\w./<-])((?:\.hackathon-kit/|\.agents/)?'
    r'(?:prompts|references|scripts|templates|run)/[\w.-]+\.(?:md|py|sh|ps1|json))')


def installed_docs(target):
    kit = target / '.hackathon-kit'
    docs = list(target.glob('.agents/skills/*/SKILL.md'))
    docs += list(kit.glob('*.md'))
    for folder in ('prompts', 'references', 'templates'):
        docs += list((kit / folder).glob('*.md'))
    return sorted(docs)


class InstalledDocumentPathTests(unittest.TestCase):
    def test_installed_kit_paths_are_written_from_task_root_and_exist(self):
        with tempfile.TemporaryDirectory(prefix='myskill-docpaths-') as temporary:
            target = Path(temporary) / 'task'
            target.mkdir()
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/kit_lifecycle.py'), 'install',
                 '--source', str(ROOT), '--target', str(target)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            docs = installed_docs(target)
            self.assertGreater(len(docs), 30)
            bare, missing = [], []
            for doc in docs:
                rel = doc.relative_to(target).as_posix()
                for number, line in enumerate(doc.read_text(encoding='utf-8').splitlines(), 1):
                    for token in TOKEN.findall(line):
                        if not token.startswith(('.hackathon-kit/', '.agents/')):
                            bare.append('%s:%d %s' % (rel, number, token))
                        elif '/run/' not in token and not (target / token).is_file():
                            missing.append('%s:%d %s' % (rel, number, token))
            self.assertEqual(bare, [], 'kit paths must resolve from the task root (add .hackathon-kit/)')
            self.assertEqual(missing, [], 'referenced installed kit files must exist')

    def test_readme_installed_paths_exist_after_install(self):
        with tempfile.TemporaryDirectory(prefix='myskill-readmepaths-') as temporary:
            target = Path(temporary) / 'task'
            target.mkdir()
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/kit_lifecycle.py'), 'install',
                 '--source', str(ROOT), '--target', str(target)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (ROOT / 'README.md').read_text(encoding='utf-8')
            tokens = [t for t in TOKEN.findall(text) if t.startswith(('.hackathon-kit/', '.agents/'))]
            self.assertTrue(tokens)
            self.assertEqual([t for t in tokens if not (target / t).is_file()], [])


if __name__ == '__main__':
    unittest.main()
