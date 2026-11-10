"""r4-3.16 regression: hard-rule table (void, zero-point, rejection and penalty rules).

Practice runs failed the same way although the skill already spelled the rule out: a void rule's term
had two readings and the team kept one because a document said how a field is recorded, or which document
takes precedence, even after the stakeholder said the answer was not documented; a team filed its own stress
violation of a void limit as a limitation; and teams kept large margins on penalty limits.
The table makes these decisions explicit and v27_check fails cp1/final when they break the rule.
"""
import json
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
CONTRACT = ROOT / 'references/v27-contract.md'
HARD = ROOT / 'scripts/hard_rules.py'


def rules():
    return runpy.run_path(str(HARD))


def grade_rule(decision='ALL_MEANINGS', **extra):
    rule = {
        'id': 'R-4.3', 'rule': '한 묶음 안의 품목은 모두 같은 등급이어야 한다. 어기면 그 묶음 전부 무효.',
        'source': 'data/규정.md:38', 'consequence': 'VOID', 'term': '등급',
        'candidates': [{'meaning': '처리 조건 등급 P/Q', 'source': 'data/items.csv 머리글 process_grade'},
                       {'meaning': '제품 등급 X/Y/Z', 'source': 'data/items.csv 머리글 product_grade'}],
        'decision': decision}
    rule.update(extra)
    return rule


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.mod = rules()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        import hashlib
        return {'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def errors(self, rule_list, phase='cp1', **doc):
        value = {'version': 1, 'rules': rule_list}
        value.update(doc)
        return self.mod['validate'](value, self.root, phase)


class RegressionR4316(Fixture):
    def test_01_two_readings_cannot_be_settled_by_one_reading(self):
        errors = self.errors([grade_rule('SINGLE_MEANING')])
        self.assertTrue(any('more than one candidate meaning' in e for e in errors), errors)
        self.assertTrue(any('how a field is recorded' in e for e in errors))
        self.assertEqual(self.errors([grade_rule('ALL_MEANINGS')]), [])
        one = grade_rule('SINGLE_MEANING')
        one['candidates'] = one['candidates'][:1]
        self.assertEqual(self.errors([one]), [])

    def test_02_official_answer_must_be_a_real_ruling_in_a_recorded_file(self):
        self.write('ops/replies/R005.json', '{"text": "문서에 없음. 팀이 판단해 가정을 보고서에 적어 주세요"}')
        not_official = grade_rule('OFFICIAL_ANSWER', official_answer={
            'quote': '문서에 없음. 팀이 판단해 가정을 보고서에 적어 주세요', 'source': 'ops/replies/R005.json', 'meaning': '처리 조건 등급 P/Q'})
        self.assertTrue(any('not an official answer' in e for e in self.errors([not_official])))
        self.write('ops/replies/R006.json', '{"text": "규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다."}')
        missing = grade_rule('OFFICIAL_ANSWER', official_answer={
            'quote': '등급은 제품 등급까지 뜻합니다', 'source': 'ops/replies/R006.json', 'meaning': '제품 등급 X/Y/Z'})
        self.assertTrue(any('quote is not in its source' in e for e in self.errors([missing])))
        wrong_choice = grade_rule('OFFICIAL_ANSWER', official_answer={
            'quote': '규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다.', 'source': 'ops/replies/R006.json', 'meaning': '어느 것도 아님'})
        self.assertTrue(any('names' in e for e in self.errors([wrong_choice])))
        good = grade_rule('OFFICIAL_ANSWER', official_answer={
            'quote': '규정 4.3의 등급은  처리 조건 등급(P/Q)만 뜻합니다.', 'source': 'ops/replies/R006.json', 'meaning': '처리 조건 등급 P/Q'})
        self.assertEqual(self.errors([good]), [])
        outside = grade_rule('OFFICIAL_ANSWER', official_answer={'quote': 'x', 'source': '../outside.txt', 'meaning': '처리 조건 등급 P/Q'})
        self.assertTrue(self.errors([outside]))

    def test_03_final_needs_a_clean_own_check_for_every_kept_meaning(self):
        ok = self.write('run/check_hml.json', '{"violations": 0}')
        ok2 = self.write('run/check_cia.json', '{"violations": 0}')
        only_one = grade_rule(checks=[{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': ok}])
        self.assertTrue(any('no own check for kept meaning' in e for e in self.errors([only_one], 'final')))
        both = grade_rule(checks=[{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': ok},
                                  {'meaning': '제품 등급 X/Y/Z', 'scenario': 'public replay', 'violations': 0, 'evidence': ok2}])
        self.assertEqual(self.errors([both], 'final'), [])
        self.assertEqual(self.errors([grade_rule()], 'cp1'), [])
        self.assertTrue(any('final needs' in e for e in self.errors([grade_rule()], 'final')))
        (self.root / 'run/check_cia.json').write_text('{"violations": 1}', encoding='utf-8')
        self.assertTrue(any('stale or missing SHA256' in e for e in self.errors([both], 'final')))

    def test_04_a_violation_in_the_teams_own_stress_scenario_blocks_final(self):
        a = self.write('run/avg.json', '{}')
        b = self.write('run/peak_hot.json', '{}')
        demand = {'id': 'DEMAND', 'rule': '최대 수요 초과 주는 절감 무효', 'source': 'docs/계약.md:3', 'consequence': 'VOID', 'term': '최대 수요',
                  'candidates': [{'meaning': '구간 평균', 'source': 'docs/계약.md:3'}, {'meaning': '순간 최댓값', 'source': 'docs/운영규정.md:42'}],
                  'decision': 'ALL_MEANINGS',
                  'checks': [{'meaning': '구간 평균', 'scenario': 'public weeks 7-8 replay', 'violations': 0, 'evidence': a},
                             {'meaning': '순간 최댓값', 'scenario': 'hot stress week', 'violations': 1, 'evidence': b}]}
        errors = self.errors([demand], 'final')
        self.assertTrue(any('hot stress week' in e and 'not recorded as a limitation' in e for e in errors), errors)
        demand['checks'][1]['violations'] = True
        self.assertTrue(any('integer violation count' in e for e in self.errors([demand], 'final')))

    def test_05_cost_exception_needs_the_expected_value_to_favour_it(self):
        cheap = grade_rule('COST_EXCEPTION', exception={'meanings_kept': ['처리 조건 등급 P/Q'], 'loss_all_meanings': 2.0,
                                                        'loss_if_wrong': 10.0, 'probability_wrong': 0.5, 'basis': 'oven runs lost'})
        self.assertTrue(any('keep every meaning' in e for e in self.errors([cheap])))
        costly = grade_rule('COST_EXCEPTION', exception={'meanings_kept': ['처리 조건 등급 P/Q'], 'loss_all_meanings': 8.0,
                                                         'loss_if_wrong': 10.0, 'probability_wrong': 0.5, 'basis': 'oven runs lost'})
        self.assertEqual(self.errors([costly]), [])
        broken = grade_rule('COST_EXCEPTION', exception={'meanings_kept': ['처리 조건 등급 P/Q'], 'loss_all_meanings': 8.0,
                                                         'loss_if_wrong': 10.0, 'probability_wrong': 1.5, 'basis': 'x'})
        self.assertTrue(any('cost exception needs' in e for e in self.errors([broken])))
        ok = self.write('run/hml.json', '{}')
        costly['checks'] = [{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': ok}]
        self.assertEqual(self.errors([costly], 'final'), [])

    def test_06_penalty_limits_are_traded_by_expected_loss(self):
        review = {'id': 'CAPACITY', 'rule': '하루 검토 60장 초과분은 잔업 비용 2배', 'source': 'README.md:40', 'consequence': 'PENALTY'}
        self.assertEqual(self.errors([review], 'cp1'), [])
        self.assertTrue(any('expected loss' in e for e in self.errors([review], 'final')))
        review['tradeoff'] = {'chosen': 'send 77% to review', 'chosen_expected_loss': 6482,
                              'alternatives': [{'label': 'threshold at capacity', 'expected_loss': 4100}]}
        self.assertTrue(any('lower expected loss' in e for e in self.errors([review], 'final')))
        review['tradeoff']['reason'] = 'critical-miss limit binds below capacity (miss rate 5.3% at the cheaper setting)'
        self.assertEqual(self.errors([review], 'final'), [])
        review['tradeoff'] = {'chosen': 'threshold at capacity', 'chosen_expected_loss': 4100,
                              'alternatives': [{'label': 'send 77%', 'expected_loss': 6482}]}
        self.assertEqual(self.errors([review], 'final'), [])

    def test_07_table_shape(self):
        self.assertTrue(self.errors([]))
        self.assertEqual(self.errors([], no_hard_rules_reason='The task states no void, zero-point, rejection or penalty rule.'), [])
        self.assertTrue(any('consequence must be' in e for e in self.errors([dict(grade_rule(), consequence='FATAL')])))
        self.assertTrue(any('unique id' in e for e in self.errors([grade_rule(), grade_rule()])))
        self.assertTrue(any('candidates need' in e for e in self.errors([dict(grade_rule(), candidates=[])])))
        self.assertTrue(self.mod['validate']({'version': 2, 'rules': []}, self.root))
        self.assertTrue(self.mod['validate']([], self.root))

    def test_08_scan_lists_every_reading_of_a_term(self):
        self.write('data/규정.md', '# 규정\n4.3 한 묶음 안의 품목은 모두 같은 등급이어야 한다.\n')
        self.write('data/items.csv', 'item_id,제품 등급(X/Y/Z),처리 등급(P/Q)\nI1,X,P\n')
        self.write('.hackathon-kit/run/notes.md', '등급 메모\n')
        found = self.mod['scan'](self.root, ['등급'])
        files = {(hit['file'], hit['at']) for hit in found['hits']}
        self.assertIn(('data/규정.md', '2'), files)
        self.assertIn(('data/items.csv', '1'), files)
        self.assertFalse(any(hit['file'].startswith('.hackathon-kit/') for hit in found['hits']))
        process = subprocess.run([sys.executable, '-I', str(HARD), 'scan', '--root', str(self.root), '--term', '등급'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(json.loads(process.stdout)['hits']), 2)
        try:
            import openpyxl
        except ImportError:
            return
        book = openpyxl.Workbook()
        book.active.append(['item', '제품 등급'])
        book.save(self.root / 'data' / 'plan.xlsx')
        self.assertTrue(any(hit['file'] == 'data/plan.xlsx' for hit in self.mod['scan'](self.root, ['등급'])['hits']))

    def test_09_check_cli(self):
        self.write('.hackathon-kit/run/HARD_RULES.json', json.dumps({'version': 1, 'rules': [grade_rule('SINGLE_MEANING')]}, ensure_ascii=False))
        process = subprocess.run([sys.executable, '-I', str(HARD), 'check', '--root', str(self.root), '--phase', 'cp1'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads(process.stdout)['status'], 'FAIL')
        self.write('.hackathon-kit/run/HARD_RULES.json', json.dumps({'version': 1, 'rules': [grade_rule()]}, ensure_ascii=False))
        process = subprocess.run([sys.executable, '-I', str(HARD), 'check', '--root', str(self.root), '--phase', 'cp1'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stdout)

    def test_10_v27_check_requires_the_table_at_cp1_and_final(self):
        from test_v27_check import EvidenceTests
        t = EvidenceTests('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.cp1_records()
        t.record('cp1_reviews', t.reviews('CP1', ('CONSTRAINT_RED', 'DATA_EVAL_RED')))
        self.assertEqual(t.result('cp1')['errors'], [])
        saved = t.plan['records'].pop('hard_rules')
        self.assertTrue(any(e.startswith('hard_rules: void/zero/reject/penalty rule table missing') for e in t.result('cp1')['errors']))
        t.plan['records']['hard_rules'] = saved
        t.record('hard_rules', {'version': 1, 'rules': [grade_rule('SINGLE_MEANING')]})
        errors = t.result('cp1')['errors']
        self.assertTrue(any('more than one candidate meaning' in e for e in errors), errors)
        self.assertTrue(any('HARD_RULES' in e and 'CP1 independent scope' in e for e in errors), errors)

    def test_11_final_fails_on_an_own_check_violation(self):
        from test_v27_check import EvidenceTests
        t = EvidenceTests('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.complete_final_records()
        self.assertEqual(t.result('final')['status'], 'PASS')
        evidence = t.write('run/stress.json', '{"violations": 2}')
        rule = grade_rule(checks=[{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': evidence},
                                  {'meaning': '제품 등급 X/Y/Z', 'scenario': 'stress week', 'violations': 2, 'evidence': evidence}])
        t.record('hard_rules', {'version': 1, 'rules': [rule]})
        errors = t.result('final')['errors']
        self.assertTrue(any('stress week' in e for e in errors), errors)
        self.assertTrue(any('HARD_RULES' in e and 'CP3 independent scope' in e for e in errors), errors)

    def test_12_installed_kit_and_guidance(self):
        installer = (ROOT / 'scripts/install_v27.py').read_text(encoding='utf-8')
        self.assertIn("'scripts/hard_rules.py'", installer)
        self.assertIn("'templates/HARD_RULES.json'", installer)
        template = json.loads((ROOT / 'templates/HARD_RULES.json').read_text(encoding='utf-8'))
        self.assertEqual(template['version'], 1)
        self.assertTrue(rules()['validate'](template, ROOT))  # the empty template must be filled in
        skill = SKILL.read_text(encoding='utf-8')
        for phrase in ('HARD_RULES.json', 'hard_rules.py scan', '"어떻게 기록하는지"', '"한계"가 아니라 P1', '감점 한도(PENALTY', '(r4-3.16)'):
            self.assertIn(phrase, skill)
        contract = CONTRACT.read_text(encoding='utf-8')
        self.assertIn('### 무효·감점 규칙 표 (r4-3.16)', contract)
        self.assertIn('loss_all_meanings > probability_wrong × loss_if_wrong', contract)


    def test_13_scan_reads_legacy_korean_files_and_writes_utf8_on_any_console(self):
        legacy = self.root / 'data' / '옛규정.txt'
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes('제목\n5.1 등급이 다른 품목을 섞으면 무효\n'.encode('cp949'))
        (self.root / 'data' / 'two_rows.csv').write_bytes('구분,,\nitem_id,제품 등급,처리 등급\nI1,X,P\n'.encode('cp949'))
        found = {(hit['file'], hit['at']) for hit in self.mod['scan'](self.root, ['등급'])['hits']}
        self.assertIn(('data/옛규정.txt', '2'), found)
        self.assertIn(('data/two_rows.csv', '2'), found)
        self.write('ops/replies/R009.json', '')
        (self.root / 'ops/replies/R009.json').write_bytes('{"text": "규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다."}'.encode('cp949'))
        rule = grade_rule('OFFICIAL_ANSWER', official_answer={
            'quote': '규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다.', 'source': 'ops/replies/R009.json', 'meaning': '처리 조건 등급 P/Q'})
        self.assertEqual(self.errors([rule]), [])
        env = dict(os.environ, PYTHONIOENCODING='cp1252')
        process = subprocess.run([sys.executable, str(HARD), 'scan', '--root', str(self.root), '--term', '등급'],
                                 capture_output=True, env=env)
        self.assertEqual(process.returncode, 0, process.stderr)
        hits = json.loads(process.stdout.decode('utf-8'))['hits']
        self.assertTrue(any(hit['file'] == 'data/옛규정.txt' and '등급' in hit['text'] for hit in hits))

    def test_14_an_empty_table_fails_when_the_materials_state_an_outcome_rule(self):
        reason = 'No outcome rule found.'
        self.write('.venv/lib/site-packages/pkg/README.md', 'a transfer that is void\n')
        self.write('LICENSE.txt', 'any attempt otherwise to copy it is void\n')
        self.write('.hackathon-kit/run/notes.md', '무효 메모\n')
        self.assertEqual(self.errors([], no_hard_rules_reason=reason), [])
        self.write('docs/평가.md', '# 평가\n한도를 한 번이라도 넘으면 그 주 절감은 무효로 본다.\n')
        errors = self.errors([], no_hard_rules_reason=reason)
        self.assertTrue(any('docs/평가.md:2' in e and 'add each as a rule' in e for e in errors), errors)
        soft = {'id': 'NOTE', 'rule': '한도 초과 주 절감 무효', 'source': 'docs/평가.md:2', 'consequence': 'PENALTY'}
        self.assertFalse(any('table is empty' in e for e in self.errors([soft])))

if __name__ == '__main__':
    unittest.main()
