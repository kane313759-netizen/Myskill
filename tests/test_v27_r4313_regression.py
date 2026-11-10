"""r4-3.13 regression: event-day operation.

Rehearsals ran before the event date, so `deadline.py --observe-now` never reported a passed milestone and the
recorded V27_STATE always equalled the recalculation. On the event day the same record made v27_check fail.
This file also pins the guidance added with that fix: measure review time at CP1, replan a lunch overlap by hand,
record the plan-only CP1 ALGORITHM_RED in the existing record, and run the two baseline helpers that import a
sibling module without -I.
"""
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
CHECK = runpy.run_path(str(ROOT / 'scripts/v27_check.py'))
DEADLINE = runpy.run_path(str(ROOT / 'scripts/deadline.py'))
BASE = {'FOLLOWUP': 'NONE', 'T_SUB': '2026-11-11T16:00:00+09:00'}


class RegressionR4313(unittest.TestCase):
    def test_01_observed_plans_enumerate_exactly_what_the_calculator_prints(self):
        plan = DEADLINE['calculate'](dict(BASE))
        plans = CHECK['observed_plans'](DEADLINE['calculate'], dict(BASE), plan)
        self.assertEqual(plans[0], plan)
        self.assertEqual(plans[1], plan)  # the same plan rebuilt without any NOW already in ENV
        self.assertEqual([tuple(item['passed']) for item in plans[1:]],
                         [(), ('cp3_start',), ('cp3_start', 'work_lock'), ('cp3_start', 'work_lock', 'submission_start'),
                          ('cp3_start', 'work_lock', 'submission_start', 'confirmation_deadline')])
        self.assertEqual([item['status'] for item in plans[1:]], ['KNOWN'] * 4 + ['PAST_CONFIRMATION'])
        stale = dict(BASE, NOW='2026-11-11T15:00:00+09:00')
        stale_plans = CHECK['observed_plans'](DEADLINE['calculate'], stale, DEADLINE['calculate'](stale))
        self.assertEqual({tuple(item['passed']) for item in stale_plans}, {tuple(item['passed']) for item in plans})
        self.assertEqual(stale, dict(BASE, NOW='2026-11-11T15:00:00+09:00'))
        for now in ('2026-11-11T13:20:00+09:00', '2026-11-11T13:20:00.000001+09:00', '2026-11-11T15:00:00+09:00',
                    '2026-11-11T07:00:00+00:00', '2026-11-11T16:00:00+09:00', '2026-11-11T16:00:01+09:00', '2026-11-12T09:00:00+09:00'):
            self.assertIn(DEADLINE['calculate'](dict(BASE, NOW=now)), plans, now)
        observed = DEADLINE['calculate'](dict(BASE, NOW='2026-11-11T15:00:00+09:00'))
        for forged in (dict(observed, passed=['no_such_milestone']), dict(observed, passed='cp3_start'), dict(observed, passed=['work_lock']),
                       dict(observed, warnings=observed['warnings'] + ['Observed NOW is past planned milestones: x']),
                       dict(observed, work_lock='2026-11-11T15:30:00+09:00'), dict(observed, status='PAST_CONFIRMATION'),
                       {key: value for key, value in observed.items() if key != 'passed'}):
            self.assertNotIn(forged, plans)
        exact = CHECK['exact']
        self.assertEqual(exact({'b': 1, 'a': [1]}), exact({'a': [1], 'b': 1}))
        self.assertEqual(len({exact(1), exact(1.0), exact(True)}), 3)
        # The nested ENV shape and equal milestone instants are enumerated too.
        nested = {'switches': {key: {'value': value, 'classification': 'PLAN_DEFAULT', 'reason': 'fixture'}
                               for key, value in dict(BASE, S_pre=0, PITCH_STUDY_WINDOW='YES', participant_study_choice=0).items()}}
        tied = DEADLINE['calculate'](nested)
        self.assertEqual(tied['work_lock'], tied['submission_start'])
        tied_plans = CHECK['observed_plans'](DEADLINE['calculate'], nested, tied)
        self.assertEqual([tuple(item['passed']) for item in tied_plans[1:]],
                         [(), ('cp3_start',), ('cp3_start', 'work_lock', 'submission_start'),
                          ('cp3_start', 'work_lock', 'submission_start', 'confirmation_deadline')])
        self.assertNotIn('NOW', nested['switches'])

    def test_02_lunch_replan_example_matches_the_calculation(self):
        env = {'FOLLOWUP': 'AFTER_CONFIRM', 'WINDOW_END': '2026-11-11T16:00:00+09:00', 'T_SUB': '2026-11-11T16:00:00+09:00',
               'LUNCH_POLICY': 'PAUSE', 'LUNCH_START': '2026-11-11T12:00:00+09:00', 'LUNCH_END': '2026-11-11T13:00:00+09:00'}
        result = DEADLINE['calculate'](env)
        self.assertEqual((result['work_lock'][11:16], result['cp3_start'][11:16], result['review_reserve_minutes']), ('14:15', '12:45', 90))
        self.assertTrue(any('overlaps PAUSE lunch' in text for text in result['warnings']))
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        for term in ('CP3 시작 = 점심 시작 − (리뷰 예비 − 점심 뒤 남는 시간)', '잠금 14:15, 점심 12:00~13:00, 리뷰 예비 90분이면 점심 뒤 75분이 남아 15분이 모자라므로 11:45에 시작한다',
                     '`cp3_start`는 바꾸지 않는다', 'run/FINALS_RUN.md'):
            self.assertIn(term, section)

    def test_03_review_time_is_measured_at_cp1_for_both_modes(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        for term in ('CP1 리뷰가 끝나면', '가장 긴 값을 REVIEW_MINUTES_EACH에 적고(순차·병렬 모두)', 'CP2 리뷰가 더 오래 걸렸으면',
                     '`--observe-now` 출력이어도 된다', '출력의 칸을 손으로 고치거나 빼지 않는다', 'ENV 값을 고치면 다시 계산해 다시 넣는다',
                     '`cp1_reviews` 기록에 같은 영수증 형식으로 ALGORITHM_RED 항목을 더한다'):
            self.assertIn(term, section)
        contract = (ROOT / 'references/v27-contract.md').read_text(encoding='utf-8')
        self.assertIn('`--observe-now`로 얻은 결과를 기록해도 된다', contract)
        self.assertIn('가운데 하나와 완전히 같은지 본다', contract)

    def test_04_baseline_profilers_run_without_isolated_mode(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        self.assertIn('이 둘만 `-X utf8 -E -s`로 실행한다', section)
        with tempfile.TemporaryDirectory(prefix='r4313 한글 ') as folder:
            sample = pathlib.Path(folder) / 'sample.csv'
            sample.write_text('lot,value\nA,1.0\nB,2.0\nC,\n', encoding='utf-8')
            for name, marker in (('profile_data.py', 'COLUMNS'), ('sanity_check.py', 'NUM')):
                script = str(ROOT / 'scripts' / name)
                good = subprocess.run([sys.executable, '-X', 'utf8', '-E', '-s', script, str(sample)], capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(good.returncode, 0, good.stderr)
                self.assertIn(marker, good.stdout)
                isolated = subprocess.run([sys.executable, '-X', 'utf8', '-I', script, str(sample)], capture_output=True, text=True, encoding='utf-8')
                self.assertNotEqual(isolated.returncode, 0, name + ' now runs under -I; drop the exception from the skill')
                self.assertIn('data_io', isolated.stderr)

    def test_05_single_session_uses_the_builder_row(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        for term in ('한 세션이 진행(ORCHESTRATOR)과 구현(MAIN_BUILDER)을 겸한다', '그 세션은 표의 MAIN_BUILDER 값으로 둔다',
                     '바꿔 달라고 한 번만 말하고, 기다리지 않고 진행한다', '확인하지 못하면 UNKNOWN으로 적는다'):
            self.assertIn(term, section)

    def test_06_cp1_fixes_the_specification_with_nine_items(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        items = [line.strip() for line in section.splitlines() if line.startswith('  ') and line.strip()[:2] in tuple('%d.' % n for n in range(1, 10))]
        self.assertEqual([item[0] for item in items], list('123456789'))
        for number, term in ((1, '제출물 목록'), (2, '0점·반려·탈락 조건'), (3, '여유를 정하는 방법'), (4, '깨진 행'), (5, '현행 기준선'),
                             (6, '평가 조건'), (7, '두 해석'), (8, '담당자에게 보낸 질문'), (9, '오류인지 실제 현상인지')):
            self.assertIn(term, items[number - 1])
        for term in ('CP1 리뷰 전에 SPEC_DRAFT에 아래 아홉 항목을 모두 적는다', '"없음(근거 한 줄)"으로 적고 비워 두지 않는다',
                     'CP1이 확정하는 것은 명세다', '구현 결함과 데이터에서 나오는 결과는 CP2·최종 리뷰가 잡는다',
                     '그 항목에 기대는 구현을 시작하기 전에 닫는다', '새 작업자로 다시 받는다', '"CP1 확정 항목과 달라진 점"을 먼저 찾게 한다'):
            self.assertIn(term, section)

    def test_07_cp1_review_covers_every_item_with_or_without_extra_workers(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        line = [text for text in section.splitlines() if text.startswith('- CP1 리뷰는 아홉 항목을 모두 덮는다')][0]
        for term in ('CONSTRAINT_RED가 1·2·7·8', 'DATA_EVAL_RED가 3·6·9', '5는 계획 전용 ALGORITHM_RED', '4는 계획 전용 EDGE_RED',
                     'CP2에서 실제로 돌릴 반례 입력 목록', '5는 DATA_EVAL_RED, 4는 CONSTRAINT_RED 의뢰문에 붙인다',
                     '어느 항목도 검토 없이 넘기지 않으며', '`cp1_reviews`에 같은 영수증 형식으로 더한다'):
            self.assertIn(term, line)
        covered = sorted(int(ch) for part in ('1·2·7·8', '3·6·9', '5', '4') for ch in part.split('·'))
        self.assertEqual(covered, list(range(1, 10)))
        # The CP1 checker requires only the two base roles, so extra plan-only entries cannot fail it.
        source = (ROOT / 'scripts/v27_check.py').read_text(encoding='utf-8')
        self.assertIn("for role in ('CONSTRAINT_RED', 'DATA_EVAL_RED'):", source)
    def test_08_main_session_load_is_shared_without_moving_decisions(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        line = [text for text in section.splitlines() if text.startswith('- 메인 세션의 부담을 줄인다')][0]
        for term in ('과제 원문 읽기, 판단, 제품과 SPEC_DRAFT 수정, 영수증·V27 기록, 리뷰 수락은 메인만 한다', 'RECORDER를 따로 띄워 설명 기록',
                     '읽기 전용 작업자에게 맡겨 결과 파일로 받는다', '제품을 고치지 않고, 독립 리뷰어로 다시 쓰지 않는다',
                     '자리를 리뷰에 먼저 준다', '띄우지 못하면 메인이 겸하고 그 사실을 적는다', 'run/FINALS_RUN.md와 SPEC_DRAFT를 먼저 다시 읽는다'):
            self.assertIn(term, line)

    def test_09_no_kit_cap_on_workers_and_submission_review_is_the_last_round(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        line = [text for text in section.splitlines() if text.startswith('- 하위 작업자 수는 키트가 정해 두지 않는다')][0]
        for term in ('공식 규칙과 실제 환경이 허용하는 만큼 동시에 띄운다', '한 번에 모두 띄워 보고', '실제로 동시에 돈 수를 REVIEW_CONCURRENCY에 적는다',
                     'CP1은 넷까지', '최종은 제출 형식 리뷰를 뺀 나머지를 한 번에 띄우고, 그 수정이 끝난 뒤 제출 형식 리뷰를 띄운다',
                     '제품을 고치는 작업자는 하나다', '동시 수를 줄이고 그 사실을 적는다'):
            self.assertIn(term, line)
        base = dict(BASE, REVIEW_PARALLEL='YES', REVIEW_MINUTES_EACH=10, FIX_BUFFER=20)
        for roles in (6, 7):
            for concurrency in (1, 2, 3, 4, 5, 6, 7, 20, 50):
                result = DEADLINE['calculate'](dict(base, FINAL_REVIEW_ROLES=roles, REVIEW_CONCURRENCY=concurrency))
                batches = result['c_basis']['batches']
                self.assertEqual(batches, -(-(roles - 1) // concurrency) + 1, (roles, concurrency))
                self.assertGreaterEqual(batches, 2)   # the other reviews, then SUBMISSION_RED on the fixed candidate
                self.assertLessEqual(batches, roles)  # never slower than sequential
                self.assertEqual(result['review_reserve_minutes'], 20 + 10 * batches)
        self.assertIn('(ceil((FINAL_REVIEW_ROLES - 1) / REVIEW_CONCURRENCY) + 1)', result['c_basis']['formula'])
        for path in ('references/v27-contract.md', 'templates/ENV.md'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertNotIn('동시 7명이면 30분', text)
            self.assertNotIn('동시 7명 30분', text)
            self.assertIn('40분', text)

    def test_10_void_rule_terms_with_two_meanings_are_not_ruled_on(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        line = [text for text in section.splitlines() if text.startswith('- 0점·반려·무효 조건에 쓰인 용어가')][0]
        for term in ('서로 다른 두 칸이나 두 정의에 맞을 수 있으면', '갈린 것으로 본다', '문서 우선순위(개정판·상위 규정)',
                     '추론만으로 한쪽을 버리지 않는다', '질문 예산을 여기에 먼저 써서', '공식 해석이 없으면 두 뜻을 모두 지키는 안을 낸다',
                     'CONSTRAINT_RED는 이런 조건에 판결을 내리지 않고', '뜻마다 따로 돌려, 다른 뜻에서 무효가 되는 건수가 0인지 확인'):
            self.assertIn(term, line)
        self.assertIn('그 조건에 쓰인 용어마다 가리킬 수 있는 자료 칸·정의 목록', section)

    def test_11_spare_time_before_the_lock_is_used_for_verified_improvement(self):
        section = SKILL.read_text(encoding='utf-8').split('## 당일 운영 보강 (r4-3.13)', 1)[1]
        line = [text for text in section.splitlines() if text.startswith('- 첫 완성안과 CP2가 끝났는데')][0]
        for term in ('일찍 끝내지 않는다', '검증된 현재 제출안은 그대로 보존하고', '배점이 큰데 확신이 낮은 항목부터', 'CANDIDATES.md',
                     '같은 자체 검증으로 확인된 뒤에만 교체한다', '수치 근거가 있을 때만 참가자에게 조기 잠금을 묻는다'):
            self.assertIn(term, line)


if __name__ == '__main__':
    unittest.main()
