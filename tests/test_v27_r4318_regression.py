"""r4-3.18 regression: participant check points in the universal skill.

The participant does not read the skill during the finals; only messages on screen. Interventions that
mattered in practice (reviewing the CP1 rule table, cutting a loop on one checker error, choosing the safe
submission near the lock) must therefore be prompted by the agent itself.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'


class RegressionR4318(unittest.TestCase):
    def test_01_the_skill_prompts_the_participant_at_three_points(self):
        skill = SKILL.read_text(encoding='utf-8')
        start = skill.index('## 참가자 확인 지점 (본선, r4-3.18)')
        section = skill[start:skill.index('\n## ', start + 1) if '\n## ' in skill[start + 1:] else len(skill)]
        for phrase in ('`[참가자 확인]`', 'CP1 리뷰 직후, 구현을 시작하기 전', 'HARD_RULES 요약 표', '"다른 뜻은 없나요?"',
                       '30분 넘게', '가) 이유를 기록하고 넘어가 제출물부터 완성', '10분 안에 답이 없으면 가)', '작업 잠금 30분 전',
                       'baseline_guard', '기본: 단순안 또는 여유가 큰 안', '무인 실행이면', 'run/FINALS_RUN.md'):
            self.assertIn(phrase, section)


if __name__ == '__main__':
    unittest.main()
