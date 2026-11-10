"""r4-3.12 regression: role model/effort roster and the temporary clone kept outside the task folder.

The participant set models and effort levels per role. references/model-policy.md is a protected baseline file
(it predates the v2.7 review roles), so the roster lives in the v2.7 entry skill and states that it takes priority.
ENV carries the plan (MODEL_PLAN) and the actual effort (ACTUAL_EFFORT) as classified switches; actual models stay in
assignments. The README box tells the agent to leave the temporary clone outside the task folder (deleting it raised
an approval prompt in a fresh session).
"""
import hashlib
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
EXPECTED = {
    'ORCHESTRATOR': ('Sol 6.1', 'high'), 'MAIN_BUILDER': ('Sol 6.1', 'Ultra'), 'CODE_RED': ('Sol 6.1', 'high'),
    'CONSTRAINT_RED': ('Sol 6.1', 'Max'), 'DATA_EVAL_RED': ('Sol 6.1', 'Max'), 'ALGORITHM_RED': ('Sol 6.1', 'Max'),
    'EDGE_RED': ('Sol 6.1', 'high'), 'SUBMISSION_RED': ('Sol 6.1', 'high'), 'SECURITY_RED': ('Sol 6.1', 'high'),
    'RECORDER': ('Luna 6', 'Max'), 'TUTOR': ('Sol 6.1', 'high'),
}


def env_document():
    text = (ROOT / 'templates/ENV.md').read_text(encoding='utf-8')
    return json.loads(re.findall(r'```json\n(.*?)\n```', text, re.S)[0])


class RegressionR4312(unittest.TestCase):
    def test_01_roster_covers_every_role_with_model_and_effort(self):
        text = SKILL.read_text(encoding='utf-8')
        self.assertIn('## 역할별 모델·노력 (r4-3.12, 참가자 지정)', text)
        section = text.split('## 역할별 모델·노력 (r4-3.12, 참가자 지정)', 1)[1]
        rows = {}
        for line in section.splitlines():
            match = re.match(r'^\| ([A-Z_]+) \([^)]*\) \| ([^|]+?) \| ([^|]+?) \|$', line)
            if match:
                rows[match.group(1)] = (match.group(2), match.group(3))
        self.assertEqual(rows, EXPECTED)

    def test_02_roster_overrides_protected_policy_without_editing_it(self):
        text = SKILL.read_text(encoding='utf-8')
        self.assertIn('`references/model-policy.md`의 선호 모델 표보다 우선한다', text)
        manifest = json.loads((ROOT / 'references/v27-baseline.json').read_text(encoding='utf-8'))
        policy = ROOT / 'references/model-policy.md'
        self.assertEqual(manifest['files']['references/model-policy.md'], hashlib.sha256(policy.read_bytes()).hexdigest())

    def test_03_roster_keeps_review_time_and_actual_selection_rules(self):
        section = SKILL.read_text(encoding='utf-8').split('## 역할별 모델·노력', 1)[1]
        for term in ('시간을 아끼려고 낮추지 않는다', 'REVIEW_PARALLEL=YES', 'REVIEW_CONCURRENCY', 'REVIEW_MINUTES_EACH', 'deadline.py --observe-now',
                     '리뷰를 줄여 시간을 맞추지 않는다', '`assignments`', '`ACTUAL_EFFORT`', '`MODEL_PLAN`', 'UNKNOWN'):
            self.assertIn(term, section)

    def test_04_env_plan_and_actual_effort_are_classified_switches(self):
        env = env_document()
        switches = env['switches']
        plan = switches['MODEL_PLAN']
        self.assertEqual(plan['classification'], 'PLAN_DEFAULT')
        self.assertTrue(plan['reason'])
        expected_plan = {('MAIN' if role == 'MAIN_BUILDER' else role): {'model': m, 'effort': e} for role, (m, e) in EXPECTED.items()}
        self.assertEqual(plan['value'], expected_plan)
        actual = switches['ACTUAL_EFFORT']
        self.assertEqual(actual['classification'], 'UNKNOWN')
        self.assertEqual(set(actual['value']), set(expected_plan))
        self.assertTrue(all(value == 'UNKNOWN' for value in actual['value'].values()))
        self.assertEqual(set(env['assignments']), set(expected_plan))
        self.assertTrue(all(value == 'UNKNOWN' for value in env['assignments'].values()))

    def test_05_env_template_still_passes_the_switch_rules(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import deadline
        finally:
            sys.path.pop(0)
        env = env_document()
        for name, item in env['switches'].items():
            self.assertIn(item.get('classification'), ('CONFIRMED', 'PLAN_DEFAULT', 'UNKNOWN'), name)
            self.assertIn('value', item, name)
            self.assertTrue(item.get('reason'), name)
        result = deadline.calculate(env)
        self.assertIn(result.get('status'), ('KNOWN', 'UNKNOWN', 'PAST_CONFIRMATION'))

    def test_06_readme_box_keeps_the_temporary_clone(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        box_end = text.index('## r8.2 candidate')
        box = text[:box_end]
        self.assertIn('설치 뒤 이 임시 clone은 지우지 않고 그대로 둔다', box)
        self.assertIn('본문의 "임시 원본 정리"는 과제 폴더 안에 둔 원본에만 해당한다', box)
        self.assertLess(box.index('지우지 않고'), box.index('install_v27.py'))
        manifest = json.loads((ROOT / 'references/v27-baseline.json').read_text(encoding='utf-8'))
        self.assertEqual(sorted(manifest['post_baseline_edits']), ['README.md'])
        self.assertIn('r4-3.12', manifest['post_baseline_edits']['README.md'])
        self.assertIn('body unchanged', manifest['post_baseline_edits']['README.md'])
        self.assertEqual(manifest['files']['README.md'], hashlib.sha256((ROOT / 'README.md').read_bytes()).hexdigest())

    def test_07_root_agents_md_repeats_the_clone_rule(self):
        text = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn('설치 뒤 이 임시 clone은 지우지 않고 둔다', text)

    def test_08_constraint_feasibility_and_cp1_plan_review(self):
        section = SKILL.read_text(encoding='utf-8').split('## 리뷰 범위 보강 (r4-3.12)', 1)[1]
        for term in ('현장 실행 가능성 점검', '장비 능력', '정비·교체 일정', '안전 절차', '근거가 있으면 제약으로 기록',
                     '제약으로 만들지 않고 담당자 질문·가정·보고서 한계로 남긴다', 'CP1 기본 리뷰는 CONSTRAINT_RED·DATA_EVAL_RED 둘이다',
                     'CP1에 ALGORITHM_RED를 하나 더 띄워 계획만 본다', '현행 기준선과 비교하는 방법', '코드와 결과 검토는 CP2', '이유를 기록한다'):
            self.assertIn(term, section)

    def test_09_partial_parallel_review_is_not_one_batch(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import deadline
        finally:
            sys.path.pop(0)
        base = {'FOLLOWUP': 'NONE', 'T_SUB': '2026-11-11T16:00:00+09:00', 'REVIEW_MINUTES_EACH': 10, 'FIX_BUFFER': 20}
        # r4-3.13: SUBMISSION_RED is its own last round, so batches = ceil((roles - 1) / concurrency) + 1.
        cases = [(dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=3, FINAL_REVIEW_ROLES=6), 50, 3),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=3, FINAL_REVIEW_ROLES=7), 50, 3),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=7, FINAL_REVIEW_ROLES=7), 40, 2),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=6, FINAL_REVIEW_ROLES=7), 40, 2),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=50, FINAL_REVIEW_ROLES=7), 40, 2),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=2, FINAL_REVIEW_ROLES=7), 60, 4),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=1, FINAL_REVIEW_ROLES=7), 90, 7),
                 (dict(REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=5, FINAL_REVIEW_ROLES=6), 40, 2),
                 (dict(REVIEW_PARALLEL='YES', FINAL_REVIEW_ROLES=7), 90, 7),
                 (dict(REVIEW_PARALLEL='NO', REVIEW_CONCURRENCY=7, FINAL_REVIEW_ROLES=7), 90, 7)]
        for extra, minutes, batches in cases:
            result = deadline.calculate(dict(base, **extra))
            self.assertEqual((result['review_reserve_minutes'], result['c_basis']['batches']), (minutes, batches), extra)
        section = SKILL.read_text(encoding='utf-8').split('## 역할별 모델·노력', 1)[1]
        self.assertIn('REVIEW_CONCURRENCY', section)
        self.assertEqual(env_document()['switches']['REVIEW_CONCURRENCY']['value'], 'UNKNOWN')
        self.assertIn('REVIEW_CONCURRENCY', (ROOT / 'references/v27-contract.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
