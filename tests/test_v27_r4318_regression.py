"""r4-3.18 regression: participant check points in the universal skill.

The participant does not read the skill during the finals; only messages on screen. Interventions that
mattered in practice (reviewing the CP1 rule table, cutting a loop on one checker error, choosing the safe
submission near the lock) must therefore be prompted by the agent itself.

r4-3.18b: practice runs passed their own public and stress checks close to a numeric void limit and then
broke it in the hidden evaluation. A margin per limit is fixed at CP1 and every final check must stay inside
it. A participant guide with paste-ready sentences is installed with the kit and its path is given at the
first briefing.
"""
import contextlib
import copy
import io
import pathlib
import runpy
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
GUIDE = ROOT / 'templates/PARTICIPANT_GUIDE.md'
sys.path.insert(0, str(ROOT / 'tests'))
from test_v27_r4317_regression import Fixture  # noqa: E402


class RegressionR4318(unittest.TestCase):
    def test_01_the_skill_prompts_the_participant_at_three_points(self):
        skill = SKILL.read_text(encoding='utf-8')
        start = skill.index('## 참가자 확인 지점 (본선, r4-3.18)')
        section = skill[start:skill.index('\n## ', start + 1) if '\n## ' in skill[start + 1:] else len(skill)]
        for phrase in ('`[참가자 확인]`', 'CP1 리뷰 직후, 구현을 시작하기 전', 'HARD_RULES 요약 표', '"다른 뜻은 없나요?"',
                       '30분 넘게', '가) 이유를 기록하고 넘어가 제출물부터 완성', '10분 안에 답이 없으면 가)', '작업 잠금 30분 전',
                       'baseline_guard', '기본: 단순안 또는 여유가 큰 안', '무인 실행이면', 'run/FINALS_RUN.md'):
            self.assertIn(phrase, section)


class RegressionR4318b(Fixture):
    def test_02_cp1_needs_a_margin_for_every_numeric_void_limit(self):
        self.assertEqual(self.errors([self.limit_rule()], phase='cp1'), [])
        for extra in ({'margin': None}, {'margin': 0}, {'margin': -5}, {'margin': True}, {'margin_basis': ''}):
            errors = self.errors([self.limit_rule(**extra)], phase='cp1')
            self.assertTrue(any('margin (> 0' in e for e in errors), (extra, errors))

    def test_03_final_values_and_bounds_must_stay_inside_the_margin(self):
        inside = self.good_checks()
        inside[2] = self.check('stress', 'capacity_down', 450.0)
        self.assertEqual(self.errors([self.limit_rule(*inside)]), [])
        close = self.good_checks()
        close[2] = self.check('stress', 'capacity_down', 470.0)
        self.assertTrue(any('value 470.0 is inside the limit 500 but not inside the CP1 margin' in e
                            for e in self.errors([self.limit_rule(*close)])))
        floor = [self.check(value=0.99), self.check('stress', 'demand_up', 0.975), self.check('stress', 'capacity_down', 0.955)]
        errors = self.errors([self.limit_rule(*floor, limit=0.95, direction='min', margin=0.01)])
        self.assertTrue(any('value 0.955' in e and 'CP1 margin' in e for e in errors), errors)
        floor[2] = self.check('stress', 'capacity_down', 0.96)
        self.assertEqual(self.errors([self.limit_rule(*floor, limit=0.95, direction='min', margin=0.01)]), [])
        est = dict(metric_source='estimated', uses_model=True, known_real_cases=7, explained_definition='predicted fail on the returned part')
        checks = [self.check(kind, stress, value, estimated=True, risk_bound=bound, estimator_validation={'explained': 5, 'total': 7})
                  for kind, stress, value, bound in (('public', None, 120.0, 200.0), ('stress', 'demand_up', 180.0, 300.0),
                                                     ('stress', 'capacity_down', 210.0, 480.0))]
        self.assertTrue(any('95% bound 480.0 of the estimate is not inside the CP1 margin' in e
                            for e in self.errors([self.limit_rule(*checks, **est)])))

    def test_04_the_margin_cannot_be_lowered_after_cp1(self):
        cp1 = self.table([self.limit_rule()])
        lower = self.table([self.limit_rule(*self.good_checks(), margin=10)])
        self.assertTrue(any('margin lowered since CP1' in e for e in self.mod['compare_freeze'](cp1, lower)))
        higher = self.table([self.limit_rule(*self.good_checks(), margin=60)])
        self.assertFalse(any('margin' in e for e in self.mod['compare_freeze'](cp1, higher)))

    def test_05_the_participant_guide_is_installed_and_announced(self):
        installer = runpy.run_path(str(ROOT / 'scripts/install_v27.py'))
        self.assertIn('templates/PARTICIPANT_GUIDE.md', installer['MANDATORY'])
        with tempfile.TemporaryDirectory(prefix='v27-guide-') as tmp:
            target = pathlib.Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                installer['install'](ROOT, target)
            for rel in ('.hackathon-kit/templates/PARTICIPANT_GUIDE.md', '.hackathon-kit/run/PARTICIPANT_GUIDE.md'):
                self.assertEqual((target / rel).read_bytes(), GUIDE.read_bytes(), rel)
        skill = SKILL.read_text(encoding='utf-8')
        section = skill[skill.index('## 참가자 확인 지점 (본선, r4-3.18)'):]
        self.assertIn('.hackathon-kit/run/PARTICIPANT_GUIDE.md', section[:800])
        self.assertIn('처음 보고할 때 첫 줄에 가이드 경로', section[:800])
        guide = GUIDE.read_text(encoding='utf-8')
        for phrase in ('[참가자 확인 1]', '[참가자 확인 2]', '[참가자 확인 3]', '「표 그대로 진행해.」',
                       '「가) 이유를 기록하고 넘어가서 제출물부터 완성해.」', 'not inside the CP1 margin',
                       '한도의 10%', '평가 방법이 흐린 과제', '앱이 멈췄을 때', '하지 말 것'):
            self.assertIn(phrase, guide)


if __name__ == '__main__':
    unittest.main()
