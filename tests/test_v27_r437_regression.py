"""r4-3.7 regression: (1) the JSONL scratch fallback refuses a run/ or run/.v27-tmp link or junction that leads outside the kit,
and an audit whose scratch is refused is not RECORDED; (2) the playbook's saturation rule updates the state with the applied
(clamped) setting and uses conditional integration instead of stopping updates unconditionally; (3) the one-sided 95% line
names the error statistic and formula."""
import json
import os
import pathlib
import runpy
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = '.agents/skills/hackathon-orchestrator-universal/SKILL.md'


def _deny_system_temp(real):
    def guarded(suffix=None, prefix=None, dir=None):
        if dir is None:
            raise PermissionError('sandbox denied system temp')
        return real(suffix, prefix, dir)
    return guarded


def _link_dir(link, target):
    """Make a directory link: a junction on Windows (no privilege needed), a symlink elsewhere. Returns False if not possible."""
    try:
        if os.name == 'nt':
            done = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True, text=True)
            return done.returncode == 0 and os.path.lexists(str(link))
        os.symlink(str(target), str(link), target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False


class RegressionR437(unittest.TestCase):
    def _fake_kit(self, td):
        kit = pathlib.Path(td) / 'kit'
        (kit / 'scripts').mkdir(parents=True)
        shutil.copy2(str(ROOT / 'scripts/v27_jsonl.py'), str(kit / 'scripts/v27_jsonl.py'))
        outside = pathlib.Path(td) / 'outside'
        outside.mkdir()
        return kit, outside

    def _scratch(self, kit):
        module = runpy.run_path(str(kit / 'scripts/v27_jsonl.py'), run_name='r437_jsonl')
        with mock.patch.object(tempfile, 'mkdtemp', _deny_system_temp(tempfile.mkdtemp)):
            return module['_scratch']()

    def test_01_fallback_inside_kit_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            kit, _ = self._fake_kit(td)
            holder = self._scratch(kit)
            try:
                real = os.path.normcase(os.path.realpath(holder.name))
                self.assertTrue(real.startswith(os.path.normcase(os.path.realpath(str(kit / 'run' / '.v27-tmp')))), real)
            finally:
                holder.cleanup()

    def test_02_run_link_outside_kit_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            kit, outside = self._fake_kit(td)
            if not _link_dir(kit / 'run', outside):
                self.skipTest('directory links not permitted here')
            with self.assertRaises(OSError):
                self._scratch(kit)
            self.assertEqual(list(outside.iterdir()), [], 'nothing may be written outside the kit')

    def test_03_scratch_link_outside_kit_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            kit, outside = self._fake_kit(td)
            (kit / 'run').mkdir()
            if not _link_dir(kit / 'run' / '.v27-tmp', outside):
                self.skipTest('directory links not permitted here')
            with self.assertRaises(OSError):
                self._scratch(kit)
            self.assertEqual(list(outside.iterdir()), [], 'nothing may be written outside the kit')

    def test_04_refused_scratch_is_not_recorded(self):
        def always_denied(suffix=None, prefix=None, dir=None):
            raise PermissionError('no scratch anywhere')
        with tempfile.TemporaryDirectory() as kit_dir, tempfile.TemporaryDirectory() as td:
            # A throwaway kit copy keeps the repository free of run/ folders.
            shutil.copytree(str(ROOT / 'scripts'), str(pathlib.Path(kit_dir) / 'scripts'))
            audit = runpy.run_path(str(pathlib.Path(kit_dir) / 'scripts/data_audit.py'), run_name='r437_audit')['audit']
            (pathlib.Path(td) / 'events.jsonl').write_text('\n'.join(json.dumps({'id': i}) for i in range(5)) + '\n', encoding='utf-8')
            with mock.patch.object(tempfile, 'mkdtemp', always_denied):
                result = audit(pathlib.Path(td), {'files': ['events.jsonl']})
        self.assertTrue(result['errors'], result)
        self.assertFalse([a for a in result['files'] if a.get('path') == 'events.jsonl' and a.get('status') == 'RECORDED'])

    def test_05_playbook_saturation_rule_is_conditional(self):
        text = (ROOT / 'references/semiconductor-domain-playbook.md').read_text(encoding='utf-8')
        self.assertNotIn('설정값이 상·하한에 걸리면 상태 갱신을 멈춘다(안티와인드업).', text)
        # Wording refined in r4-3.9 (split by controller type); behaviour is simulated in test_v27_r439_regression.
        self.assertIn('실제로 적용한(잘린) 설정값과 측정값으로 상태를 계속 갱신하고', text)
        self.assertIn('회복 방향이면 적분한다(조건부 적분 안티와인드업)', text)

    def test_06_margin_line_names_statistic_and_formula(self):
        text = (ROOT / SKILL).read_text(encoding='utf-8')
        for term in ('(실제 − 추정) 오차', '표준화 오차 z = (실제 − 추정) ÷ 표준오차', '1.645 × 오차 표준편차', '경험적 95% 분위수'):
            self.assertIn(term, text)


if __name__ == '__main__':
    unittest.main()
