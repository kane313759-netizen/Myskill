"""r4-3.16 regression: hard-rule table (void, zero-point, rejection and penalty rules).

Practice runs failed the same way although the skill already spelled the rule out: a void rule's term
had two readings and the team kept one because a document said how a field is recorded, or which document
takes precedence, even after the stakeholder said the answer was not documented; a team filed its own stress
violation of a void limit as a limitation; and teams kept large margins on penalty limits.
The table makes these decisions explicit and v27_check fails cp1/final when they break the rule.
"""
import copy
import hashlib
import json
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
CONTRACT = ROOT / 'references/v27-contract.md'
HARD = ROOT / 'scripts/hard_rules.py'
RULE_TEXT = '4.3 한 묶음 안의 품목은 모두 같은 등급이어야 한다. 어기면 그 묶음 전부 무효.'
NO_LIMIT = 'The rule counts mixed items; it has no numeric threshold.'


def rules():
    return runpy.run_path(str(HARD))


def grade_rule(decision='ALL_MEANINGS', **extra):
    rule = {
        'id': 'R-4.3', 'rule': RULE_TEXT, 'source': 'data/규정.md:2', 'consequence': 'VOID', 'term': '등급',
        'candidates': [{'meaning': '처리 조건 등급 P/Q', 'source': 'data/items.csv 머리글 process_grade'},
                       {'meaning': '제품 등급 X/Y/Z', 'source': 'data/items.csv 머리글 product_grade'}],
        'decision': decision, 'no_numeric_limit_reason': NO_LIMIT}
    rule.update(extra)
    return rule


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.mod = rules()
        self.write('data/규정.md', '# 규정\n' + RULE_TEXT + '\n')

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding='utf-8')
        return {'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def proof(self, rel, **numbers):
        return self.write(rel, json.dumps(numbers))

    def table(self, rule_list, **doc):
        value = {'version': 1, 'rules': rule_list, 'materials': ['data'], 'no_baseline_reason': 'No tuned output in this fixture.'}
        value.update(doc)
        return value

    def errors(self, rule_list, phase='cp1', frozen=None, **doc):
        value = self.table(rule_list, **doc)
        if phase == 'final' and frozen is None:
            frozen = copy.deepcopy(value)
        return self.mod['validate'](value, self.root, phase, frozen=frozen)


class RegressionR4316(Fixture):
    def test_01_two_readings_cannot_be_settled_by_one_reading(self):
        errors = self.errors([grade_rule('SINGLE_MEANING')])
        self.assertTrue(any('more than one candidate meaning' in e for e in errors), errors)
        self.assertTrue(any('how a field is recorded' in e for e in errors))
        self.assertEqual(self.errors([grade_rule('ALL_MEANINGS')]), [])
        one = grade_rule('SINGLE_MEANING')
        one['candidates'] = one['candidates'][:1]
        self.assertTrue(any('scan_hits equal to the scan' in e for e in self.errors([one])))
        self.assertEqual(self.errors([dict(one, scan_hits=1)]), [])

    def test_02_official_answer_must_be_a_real_ruling_in_a_recorded_reply(self):
        bad = self.write('ops/replies/R005.json', '{"text": "문서에 없음. 팀이 판단해 가정을 보고서에 적어 주세요"}')
        good_ref = self.write('ops/replies/R006.json', '{"text": "규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다."}')
        sources = {'answer_sources': [bad, good_ref]}

        def answer(quote, source, meaning):
            return grade_rule('OFFICIAL_ANSWER', official_answer={'quote': quote, 'source': source, 'meaning': meaning})
        not_official = answer('문서에 없음. 팀이 판단해 가정을 보고서에 적어 주세요', 'ops/replies/R005.json', '처리 조건 등급 P/Q')
        self.assertTrue(any('not an official answer' in e for e in self.errors([not_official], **sources)))
        paraphrase = answer('문서상 특정되지 않음', 'ops/replies/R005.json', '처리 조건 등급 P/Q')
        self.assertTrue(any('not an official answer' in e for e in self.errors([paraphrase], **sources)))
        missing = answer('등급은 제품 등급까지 뜻합니다', 'ops/replies/R006.json', '제품 등급 X/Y/Z')
        self.assertTrue(any('quote is not in its source' in e for e in self.errors([missing], **sources)))
        wrong_choice = answer('규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다.', 'ops/replies/R006.json', '어느 것도 아님')
        self.assertTrue(any('names' in e for e in self.errors([wrong_choice], **sources)))
        good = answer('규정 4.3의 등급은  처리 조건 등급(P/Q)만 뜻합니다.', 'ops/replies/R006.json', '처리 조건 등급 P/Q')
        self.assertEqual(self.errors([good], **sources), [])
        self.assertTrue(any('answer_sources' in e for e in self.errors([good])))
        greeting_ref = self.write('ops/replies/R007.json', '{"text": "안녕하세요. 질문을 받았습니다."}')
        greeting = answer('안녕하세요. 질문을 받았습니다.', 'ops/replies/R007.json', '처리 조건 등급 P/Q')
        self.assertTrue(any('must name the rule term' in e for e in self.errors([greeting], answer_sources=[greeting_ref])))
        team = self.write('.hackathon-kit/run/note.md', '등급은 처리 조건 등급만 뜻한다')
        self_quote = answer('등급은 처리 조건 등급만 뜻한다', '.hackathon-kit/run/note.md', '처리 조건 등급 P/Q')
        self.assertTrue(any('team file' in e for e in self.errors([self_quote], answer_sources=[team])))
        outside = answer('등급 x', '../outside.txt', '처리 조건 등급 P/Q')
        self.assertTrue(self.errors([outside], **sources))

    def test_03_final_needs_a_clean_own_check_for_every_kept_meaning(self):
        ok = self.proof('run/check_pq.json', violations=0)
        ok2 = self.proof('run/check_xyz.json', violations=0)
        only_one = grade_rule(checks=[{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': ok}])
        self.assertTrue(any('no own check for kept meaning' in e for e in self.errors([only_one], 'final')))
        both = grade_rule(checks=[{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': ok},
                                  {'meaning': '제품 등급 X/Y/Z', 'scenario': 'public replay', 'violations': 0, 'evidence': ok2}])
        self.assertEqual(self.errors([both], 'final'), [])
        self.assertEqual(self.errors([grade_rule()], 'cp1'), [])
        self.assertTrue(any('final needs' in e for e in self.errors([grade_rule()], 'final')))
        empty = self.write('run/empty.json', '{}')
        hollow = copy.deepcopy(both)
        hollow['checks'][1]['evidence'] = empty
        self.assertTrue(any('does not state the recorded violations' in e for e in self.errors([hollow], 'final')))
        (self.root / 'run/check_xyz.json').write_text('{"violations": 1}', encoding='utf-8')
        self.assertTrue(any('stale or missing SHA256' in e for e in self.errors([both], 'final')))

    def test_04_a_violation_in_the_teams_own_stress_scenario_blocks_final(self):
        self.write('data/계약.md', '# 계약\n최대 수요를 넘긴 주는 절감이 무효다.\n')
        a = self.proof('run/avg.json', violations=0)
        b = self.proof('run/peak_hot.json', violations=1)
        demand = {'id': 'DEMAND', 'rule': '최대 수요를 넘긴 주는 절감이 무효다.', 'source': 'data/계약.md:2', 'consequence': 'VOID', 'term': '최대 수요',
                  'candidates': [{'meaning': '구간 평균', 'source': 'data/계약.md:2'}, {'meaning': '순간 최댓값', 'source': 'data/운영규정.md:42'}],
                  'decision': 'ALL_MEANINGS', 'no_numeric_limit_reason': 'The limit value is per contract; checked as violation counts.',
                  'checks': [{'meaning': '구간 평균', 'scenario': 'public weeks 7-8 replay', 'violations': 0, 'evidence': a},
                             {'meaning': '순간 최댓값', 'scenario': 'hot stress week', 'violations': 1, 'evidence': b}]}
        errors = self.errors([grade_rule(checks=[]), demand][1:], 'final')
        self.assertTrue(any('hot stress week' in e and 'not recorded as a limitation' in e for e in errors), errors)
        demand['checks'][1]['violations'] = True
        self.assertTrue(any('integer violation count' in e for e in self.errors([demand], 'final')))

    def test_05_cost_exception_needs_the_expected_value_to_favour_it(self):
        cheap = grade_rule('COST_EXCEPTION', exception={'meanings_kept': ['처리 조건 등급 P/Q'], 'loss_all_meanings': 2.0,
                                                        'loss_if_wrong': 10.0, 'probability_wrong': 0.5, 'basis': 'runs lost'})
        self.assertTrue(any('keep every meaning' in e for e in self.errors([cheap])))
        costly = grade_rule('COST_EXCEPTION', exception={'meanings_kept': ['처리 조건 등급 P/Q'], 'loss_all_meanings': 8.0,
                                                         'loss_if_wrong': 10.0, 'probability_wrong': 0.5, 'basis': 'runs lost'})
        self.assertEqual(self.errors([costly]), [])
        broken = grade_rule('COST_EXCEPTION', exception={'meanings_kept': ['처리 조건 등급 P/Q'], 'loss_all_meanings': 8.0,
                                                         'loss_if_wrong': 10.0, 'probability_wrong': 1.5, 'basis': 'x'})
        self.assertTrue(any('cost exception needs' in e for e in self.errors([broken])))
        ok = self.proof('run/pq.json', violations=0)
        side = self.proof('run/xyz.json', violations=3)
        costly['checks'] = [{'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': ok},
                            {'meaning': '제품 등급 X/Y/Z', 'scenario': 'reference only', 'violations': 3, 'evidence': side}]
        self.assertEqual(self.errors([costly], 'final'), [])

    def test_06_penalty_limits_are_traded_by_expected_loss(self):
        review = {'id': 'CAPACITY', 'rule': '하루 검토 60장 초과분은 잔업 비용 2배', 'source': 'README.md:40', 'consequence': 'PENALTY'}
        note = {'not_rules': [{'at': 'data/규정.md:2', 'why': 'covered by another test'}]}
        self.assertEqual(self.errors([review], 'cp1', **note), [])
        self.assertTrue(any('at least two alternatives' in e for e in self.errors([review], 'final', **note)))

        def tradeoff(chosen, loss, alternatives, at_limit=True):
            alts = [dict(label=label, expected_loss=value) for label, value in alternatives]
            if at_limit:
                alts[0]['at_limit'] = True
            evidence = self.proof('run/tradeoff_%s.json' % len(chosen), chosen_expected_loss=loss, alternatives=dict(alternatives))
            return {'chosen': chosen, 'chosen_expected_loss': loss, 'alternatives': alts, 'evidence': evidence}
        review['tradeoff'] = tradeoff('send 77% to review', 6482, [('threshold at capacity', 4100), ('send 90%', 7900)])
        self.assertTrue(any('lower expected loss' in e for e in self.errors([review], 'final', **note)))
        review['tradeoff']['reason'] = 'a reason does not make it cheaper'
        self.assertTrue(any('lower expected loss' in e for e in self.errors([review], 'final', **note)))
        review['tradeoff'] = tradeoff('threshold at capacity', 4100, [('at capacity exactly', 4100), ('send 77%', 6482)])
        self.assertEqual(self.errors([review], 'final', **note), [])
        review['tradeoff'] = tradeoff('threshold at capacity', 4100, [('a', 4100), ('send 77%', 6482)], at_limit=False)
        self.assertTrue(any('at_limit' in e for e in self.errors([review], 'final', **note)))

    def test_07_table_shape_and_malformed_input(self):
        reason = 'The task states no outcome rule.'
        self.assertTrue(any('give no_hard_rules_reason' in e for e in self.errors([])))
        errors = self.errors([], no_hard_rules_reason=reason)
        self.assertTrue(any('data/규정.md:2' in e and 'not in the table' in e for e in errors), errors)
        self.assertEqual(self.errors([], no_hard_rules_reason=reason, not_rules=[{'at': 'data/규정.md:2', 'why': 'example in a glossary'}]), [])
        self.assertTrue(any('consequence must be' in e for e in self.errors([dict(grade_rule(), consequence='FATAL')])))
        self.assertTrue(any('unique id' in e for e in self.errors([grade_rule(), grade_rule()])))
        self.assertTrue(any('candidates need' in e for e in self.errors([dict(grade_rule(), candidates=[])])))
        self.assertTrue(self.mod['validate']({'version': 2, 'rules': []}, self.root))
        self.assertTrue(self.mod['validate']([], self.root))
        self.assertTrue(any('materials must list' in e for e in self.errors([grade_rule()], materials=[])))
        self.assertTrue(any('team output' in e for e in self.errors([grade_rule()], materials=['data', '.hackathon-kit/run'])))
        for broken in ([dict(grade_rule(), id=[])], [dict(grade_rule(), limit=1, stress_plan=[{}])]):
            self.assertTrue(self.errors(broken))
        self.assertTrue(self.errors([grade_rule()], 'final', baseline_plan=[{'output': []}], baseline_guard=[{'output': []}]))

    def test_08_scan_lists_every_reading_of_a_term(self):
        self.write('data/items.csv', 'item_id,제품 등급(X/Y/Z),처리 등급(P/Q)\nI1,X,P\n')
        self.write('.hackathon-kit/run/notes.md', '등급 메모\n')
        found = self.mod['scan'](self.root, ['등급'])
        files = {(hit['file'], hit['at']) for hit in found['hits']}
        self.assertIn(('data/규정.md', '2'), files)
        self.assertIn(('data/items.csv', '1'), files)
        self.assertFalse(any(hit['file'].startswith('.hackathon-kit/') for hit in found['hits']))
        process = subprocess.run([sys.executable, '-I', str(HARD), 'scan', '--root', str(self.root), '--term', '등급', '--path', 'data'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(json.loads(process.stdout)['hits']), 2)
        with zipfile.ZipFile(self.root / 'data' / 'plan.xlsx', 'w') as book:
            book.writestr('xl/sharedStrings.xml', '<sst><si><t>item</t></si><si><t>제품 등급</t></si></sst>')
        with zipfile.ZipFile(self.root / 'data' / 'guide.docx', 'w') as doc:
            doc.writestr('word/document.xml', '<w:document><w:p><w:r><w:t>등급 정의</w:t></w:r></w:p></w:document>')
        self.write('data/broken.xlsx', b'not a zip file')
        self.write('data/manual.pdf', b'%PDF-1.4')
        found = self.mod['scan'](self.root, ['등급'], paths=('data',))
        self.assertTrue(any(hit['file'] == 'data/plan.xlsx' for hit in found['hits']))
        self.assertTrue(any(hit['file'] == 'data/guide.docx' for hit in found['hits']))
        self.assertEqual({item['file'] for item in found['skipped']}, {'data/broken.xlsx', 'data/manual.pdf'})
        errors = self.errors([grade_rule()])
        self.assertTrue(any('data/manual.pdf could not be scanned' in e for e in errors), errors)
        reviewed = [{'file': 'data/manual.pdf', 'note': 'opened: no outcome rule'}, {'file': 'data/broken.xlsx', 'note': 'corrupt test input'}]
        self.assertEqual(self.errors([grade_rule()], unscanned_reviewed=reviewed), [])

    def test_09_outcome_words_match_whole_tokens_and_any_case(self):
        self.write('data/배점.md', '# 배점\n정확도 10점, 보고서 100점\n')
        self.write('data/en.md', 'A run that IS VOID is rerun.\n')
        found = self.mod['scan'](self.root, ['0점', 'void'], paths=('data',))
        self.assertFalse(any(hit['file'] == 'data/배점.md' for hit in found['hits']))
        self.assertTrue(any(hit['file'] == 'data/en.md' for hit in found['hits']))
        self.write('data/zero.md', '제출 형식이 틀리면 0점\n')
        self.assertTrue(any(hit['file'] == 'data/zero.md' for hit in self.mod['scan'](self.root, ['0점'], paths=('data',))['hits']))

    def test_10_check_cli_reads_a_bom_table_and_the_cp1_copy(self):
        table = self.table([grade_rule()])
        self.write('.hackathon-kit/run/HARD_RULES.json', b'\xef\xbb\xbf' + json.dumps(table, ensure_ascii=False).encode('utf-8'))
        process = subprocess.run([sys.executable, '-I', str(HARD), 'check', '--root', str(self.root), '--phase', 'cp1'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stdout)
        table['rules'] = [grade_rule('SINGLE_MEANING')]
        self.write('.hackathon-kit/run/HARD_RULES.json', json.dumps(table, ensure_ascii=False))
        process = subprocess.run([sys.executable, '-I', str(HARD), 'check', '--root', str(self.root), '--phase', 'cp1'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads(process.stdout)['status'], 'FAIL')
        process = subprocess.run([sys.executable, '-I', str(HARD), 'check', '--root', str(self.root), '--phase', 'final'],
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertTrue(any('CP1 copy' in e for e in json.loads(process.stdout)['errors']))

    def test_11_v27_check_requires_the_table_and_the_cp1_copy(self):
        from test_v27_check import EvidenceTests
        t = EvidenceTests('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.cp1_records()
        saved = t.plan['records'].pop('hard_rules')
        self.assertTrue(any(e.startswith('hard_rules: void/zero/reject/penalty rule table missing') for e in t.result('cp1')['errors']))
        t.plan['records']['hard_rules'] = saved
        t.record('hard_rules', {'version': 1, 'rules': [grade_rule('SINGLE_MEANING')], 'materials': ['TASK.md'], 'no_baseline_reason': 'No tuned output.'})
        errors = t.result('cp1')['errors']
        self.assertTrue(any('more than one candidate meaning' in e for e in errors), errors)
        t.complete_final_records()
        self.assertEqual(t.result('final')['status'], 'PASS')
        evidence = t.write('run/stress.json', '{"violations": 2}')
        rule = grade_rule(source='TASK.md:1', checks=[
            {'meaning': '처리 조건 등급 P/Q', 'scenario': 'public replay', 'violations': 0, 'evidence': t.write('run/public.json', '{"violations": 0}')},
            {'meaning': '제품 등급 X/Y/Z', 'scenario': 'stress week', 'violations': 2, 'evidence': evidence}])
        t.record('hard_rules', {'version': 1, 'rules': [rule], 'materials': ['TASK.md'], 'no_baseline_reason': 'No tuned output in this fixture.'})
        errors = t.result('final')['errors']
        self.assertTrue(any('stress week' in e for e in errors), errors)
        self.assertTrue(any('HARD_RULES' in e and 'CP3 independent scope' in e for e in errors), errors)
        del t.plan['records']['hard_rules_cp1']
        self.assertTrue(any(e.startswith('hard_rules_cp1: record the copy') for e in t.result('final')['errors']))

    def test_12_installed_kit_and_guidance(self):
        installer = (ROOT / 'scripts/install_v27.py').read_text(encoding='utf-8')
        self.assertIn("'scripts/hard_rules.py'", installer)
        self.assertIn("'templates/HARD_RULES.json'", installer)
        template = json.loads((ROOT / 'templates/HARD_RULES.json').read_text(encoding='utf-8'))
        self.assertEqual(template['rules'], [])
        self.assertEqual(template['materials'], [])
        skill = SKILL.read_text(encoding='utf-8')
        for phrase in ('HARD_RULES.json', 'hard_rules.py scan', '"어떻게 기록하는지"', '"한계"가 아니라 P1', '감점 한도(PENALTY', '(r4-3.16)',
                       'hard_rules_cp1', 'not_rules', 'answer_sources'):
            self.assertIn(phrase, skill)
        contract = CONTRACT.read_text(encoding='utf-8')
        self.assertIn('loss_all_meanings > probability_wrong × loss_if_wrong', contract)

    def test_13_scan_reads_legacy_korean_files_and_writes_utf8_on_any_console(self):
        self.write('data/옛규정.txt', '제목\n5.1 등급이 다른 품목을 섞으면 무효\n'.encode('cp949'))
        self.write('data/two_rows.csv', '구분,,\nitem_id,제품 등급,처리 등급\nI1,X,P\n'.encode('cp949'))
        found = {(hit['file'], hit['at']) for hit in self.mod['scan'](self.root, ['등급'])['hits']}
        self.assertIn(('data/옛규정.txt', '2'), found)
        self.assertIn(('data/two_rows.csv', '2'), found)
        reply = self.write('ops/replies/R009.json', '{"text": "규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다."}'.encode('cp949'))
        rule = grade_rule('OFFICIAL_ANSWER', sources=['data/옛규정.txt:2'], official_answer={
            'quote': '규정 4.3의 등급은 처리 조건 등급(P/Q)만 뜻합니다.', 'source': 'ops/replies/R009.json', 'meaning': '처리 조건 등급 P/Q'})
        self.assertEqual(self.errors([rule], answer_sources=[reply]), [])
        env = dict(os.environ, PYTHONIOENCODING='cp1252')
        process = subprocess.run([sys.executable, str(HARD), 'scan', '--root', str(self.root), '--term', '등급'], capture_output=True, env=env)
        self.assertEqual(process.returncode, 0, process.stderr)
        hits = json.loads(process.stdout.decode('utf-8'))['hits']
        self.assertTrue(any(hit['file'] == 'data/옛규정.txt' and '등급' in hit['text'] for hit in hits))

    def test_14_a_table_with_rules_still_accounts_for_every_outcome_sentence(self):
        self.write('data/평가.md', '# 평가\n한도를 한 번이라도 넘으면 그 주 절감은 무효로 본다.\n')
        soft = {'id': 'NOTE', 'rule': '참고', 'source': 'data/규정.md:2', 'consequence': 'SOFT'}
        errors = self.errors([soft])
        self.assertTrue(any('data/평가.md:2' in e and 'not in the table' in e for e in errors), errors)
        self.write('.venv/lib/site-packages/pkg/README.md', 'a transfer that is void\n')
        self.write('data/LICENSE.txt', 'any attempt otherwise to copy it is void\n')
        week = {'id': 'WEEK', 'rule': '한도를 넘은 주는 절감 무효', 'source': 'data/평가.md:2', 'consequence': 'PENALTY'}
        self.assertEqual(self.errors([soft, week], materials=['data', '.venv']), [])


if __name__ == '__main__':
    unittest.main()
