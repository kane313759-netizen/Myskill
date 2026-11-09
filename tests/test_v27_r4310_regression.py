"""r4-3.10 regression: a short request such as "myskill 최신버전 설치해서 작업 시작해 줘" must lead to the v2.7 path.
The README (read first by agents) opens with a box that names install_v27.py and $hackathon-orchestrator-universal; the
universal skill describes itself as the finals entry point; BOOTSTRAP's one-line start carries the day-of defaults;
a root AGENTS.md repeats the steps; the README edit is the only documented post-baseline edit. Then the box's commands are
executed as written and must install the start document and the universal skill."""
import contextlib
import hashlib
import io
import json
import os
import pathlib
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'


class RegressionR4310(unittest.TestCase):
    def test_01_readme_box_comes_first(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        head = text[:2500]
        self.assertTrue(text.startswith('# SK hynix AI Hackathon Starter Kit\n\n> **AI 에이전트에게'))
        for term in ('python -X utf8 -I <clone>/scripts/install_v27.py --source <clone> --target <과제 폴더>', 'install.sh·install.ps1 대신',
                     'kit_lifecycle.py doctor', 'BOOTSTRAP_V27.md', '$hackathon-orchestrator-universal', '기본 브랜치가 최신판'):
            self.assertIn(term, head)
        self.assertLess(head.index('$hackathon-orchestrator-universal'), text.index('Use the hackathon-finals skill'))
        self.assertIn('Use the hackathon-finals skill', text, 'baseline body kept')

    def test_02_baseline_manifest_documents_only_the_readme_edit(self):
        manifest = json.loads((ROOT / 'references/v27-baseline.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['files']), 112)
        self.assertEqual(sorted(manifest.get('post_baseline_edits', {})), ['README.md'])
        self.assertEqual(manifest['files']['README.md'], hashlib.sha256((ROOT / 'README.md').read_bytes()).hexdigest())

    def test_03_universal_skill_is_the_entry_point(self):
        description = next(line for line in SKILL.read_text(encoding='utf-8').splitlines() if line.startswith('description:'))
        self.assertIn('Start here for any SK hynix AI hackathon finals', description)
        self.assertIn('use this instead of starting hackathon-finals directly', description)
        self.assertLessEqual(len(description), 1024)

    def test_04_bootstrap_one_line_start_has_day_defaults(self):
        text = (ROOT / 'BOOTSTRAP_V27.md').read_text(encoding='utf-8')
        first = re.findall(r'```text\n(.*?)\n```', text, re.S)[0]
        self.assertEqual(len(first.splitlines()), 1)
        for term in ('$hackathon-orchestrator-universal', '문서에서 찾아 출처와 함께 적고', '문서에 없는 것만 나에게 한 번에', '최종 학습은 60분'):
            self.assertIn(term, first)
        self.assertIn('짧게 요청했다면, 설치 뒤 이 문장을 받은 것으로 보고', text)

    def test_05_root_agents_md_repeats_the_steps(self):
        text = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        for term in ('install_v27.py', 'install.sh·install.ps1 대신', '$hackathon-orchestrator-universal', 'README.md 맨 위 상자'):
            self.assertIn(term, text)

    def test_06_box_commands_install_the_v27_start(self):
        with tempfile.TemporaryDirectory(prefix='r4310-') as tmp:
            clone, task = pathlib.Path(tmp) / 'clone', pathlib.Path(tmp) / '과제 폴더'
            shutil.copytree(str(ROOT), str(clone), ignore=shutil.ignore_patterns('.git', 'run', '__pycache__'))
            task.mkdir()
            env = dict(os.environ, PYTHONUTF8='1')
            done = subprocess.run([sys.executable, '-X', 'utf8', '-I', str(clone / 'scripts/install_v27.py'), '--source', str(clone), '--target', str(task)],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
            self.assertEqual(done.returncode, 0, done.stderr[-500:])
            self.assertTrue((task / '.hackathon-kit/BOOTSTRAP_V27.md').is_file())
            installed = (task / '.agents/skills/hackathon-orchestrator-universal/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('Start here for any SK hynix AI hackathon finals', installed)
            doctor = subprocess.run([sys.executable, '-X', 'utf8', '-I', str(task / '.hackathon-kit/scripts/kit_lifecycle.py'), 'doctor', '--kit', str(task / '.hackathon-kit')],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
            self.assertEqual(doctor.returncode, 0, doctor.stdout[-500:] + doctor.stderr[-500:])


    def test_08_install_survives_a_non_utf8_console(self):
        """Windows CI (cp1252) printed Korean paths from the protected backend and aborted the install."""
        import contextlib
        import io
        installer = runpy.run_path(str(ROOT / 'scripts/install_v27.py'), run_name='r4310_install')
        with tempfile.TemporaryDirectory(prefix='r4310-cp1252-') as tmp:
            task = pathlib.Path(tmp) / '과제 폴더 한글'
            task.mkdir()
            out = io.TextIOWrapper(io.BytesIO(), encoding='cp1252', errors='strict')
            err = io.TextIOWrapper(io.BytesIO(), encoding='cp1252', errors='strict')
            argv = ['install_v27.py', '--source', str(ROOT), '--target', str(task), '--allow-internal-source']
            with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = installer['main']()
            err.seek(0)
            self.assertEqual(code, 0, err.buffer.getvalue().decode('cp1252', 'replace')[-400:])
            self.assertTrue((task / '.hackathon-kit/BOOTSTRAP_V27.md').is_file())

    def test_07_every_skill_frontmatter_parses(self):
        """The skill loader parses YAML frontmatter; an unquoted ': ' inside a value breaks the whole skill."""
        try:
            import yaml
        except ImportError:
            yaml = None
        for path in sorted((ROOT / '.agents/skills').glob('*/SKILL.md')):
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.startswith('---\n'), path)
            front = text.split('---', 2)[1]
            if yaml is not None:
                data = yaml.safe_load(front)
                self.assertIsInstance(data, dict, path)
                self.assertTrue(data.get('name') and data.get('description'), path)
                self.assertLessEqual(len(str(data['description'])), 1024, path)
            for line in front.strip().splitlines():
                key, sep, value = line.partition(':')
                self.assertEqual(sep, ':', '%s: frontmatter line without key: %r' % (path, line))
                value = value.strip()
                if value[:1] in ('"', "'"):
                    continue
                self.assertNotIn(': ', value, '%s: unquoted ": " in %s' % (path.parent.name, key))
                self.assertNotIn(' #', value, '%s: unquoted " #" in %s' % (path.parent.name, key))
                self.assertFalse(value[:1] in tuple('&*!|>%@`{[]}'), '%s: %s starts with a YAML indicator' % (path.parent.name, key))


if __name__ == '__main__':
    unittest.main()
