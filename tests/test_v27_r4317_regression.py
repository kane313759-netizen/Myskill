"""r4-3.17 regression: CP1 plans for numeric limits, two-sided targets, simple baselines and the search, and
final results checked against the CP1 copy.

Practice runs that passed their own replay still failed hidden evaluations: a numeric void limit was judged
with a point estimate from an estimator that explained none of the known real cases; a stress set was no
harsher than the public data; a 90% interval target was overshot to 100%; per-unit thresholds tuned on a short
window lost to the current practice and to one pooled threshold on later data; and a request policy lost to
uniform requests. Reviews of the first draft added: plans rewritten after CP1, evidence files that do not hold
the recorded numbers, bounds on the wrong side, dummy search rounds and unproven optimum bounds.
"""
import copy
import hashlib
import json
import pathlib
import runpy
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARD = ROOT / 'scripts/hard_rules.py'
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
CONTRACT = ROOT / 'references/v27-contract.md'
README = '# 과제\nDPPM이 500을 넘으면 불합격이다.\n평가 지표는 30일 총비용(원)이다.\n'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.mod = runpy.run_path(str(HARD))
        self.write('docs/README.md', README)
        self.serial = 0

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return {'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def proof(self, **numbers):
        self.serial += 1
        return self.write('run/proof_%d.json' % self.serial, json.dumps(numbers, ensure_ascii=False))

    def table(self, rules, **doc):
        value = {'version': 1, 'rules': rules, 'materials': ['docs'], 'no_baseline_reason': 'No tuned output in this fixture.',
                 'not_rules': [{'at': 'docs/README.md:2', 'why': 'covered by the limit rule when present'}]}
        value.update(doc)
        return value

    def errors(self, rules, phase='final', frozen=None, **doc):
        value = self.table(rules, **doc)
        if phase == 'final' and frozen is None:
            frozen = copy.deepcopy(value)
        return self.mod['validate'](value, self.root, phase, frozen=frozen)

    def limit_rule(self, *checks, **extra):
        rule = {'id': 'DPPM', 'rule': 'DPPM이 500을 넘으면 불합격이다.', 'source': 'docs/README.md:2', 'consequence': 'REJECT',
                'term': 'DPPM', 'candidates': [{'meaning': '출하 칩 기준 DPPM', 'source': 'docs/README.md:2'}],
                'decision': 'ALL_MEANINGS', 'limit': 500, 'direction': 'max', 'inclusive': True, 'unit': 'DPPM',
                'statistic': 'all shipped chips in the evaluation period', 'stress_plan': ['demand_up', 'capacity_down'],
                'metric_source': 'simulator', 'uses_model': False, 'margin': 50,
                'margin_basis': '10% of the limit', 'checks': list(checks)}
        rule.update(extra)
        return rule

    def check(self, kind='public', stress_type=None, value=120.0, meaning='출하 칩 기준 DPPM', **extra):
        item = {'meaning': meaning, 'scenario': kind + (' ' + stress_type if stress_type else ''), 'scenario_kind': kind,
                'violations': 0, 'value': value}
        if stress_type:
            item.update(stress_type=stress_type, stress_param='+20%')
        item.update(extra)
        item['evidence'] = self.proof(violations=item['violations'], value=item['value']) if number(item['value']) else self.proof(violations=0)
        return item

    def good_checks(self):
        return [self.check(), self.check('stress', 'demand_up', 180.0), self.check('stress', 'capacity_down', 210.0)]


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class RegressionR4317(Fixture):
    def test_01_numeric_limit_needs_public_and_every_planned_stress_per_meaning(self):
        self.assertEqual(self.errors([self.limit_rule(*self.good_checks())]), [])
        self.assertEqual(self.errors([self.limit_rule()], phase='cp1'), [])
        only_public = self.errors([self.limit_rule(self.check())])
        self.assertTrue(any('has not run planned stress' in e for e in only_public), only_public)
        two = self.limit_rule(candidates=[{'meaning': 'M1', 'source': 'docs/README.md:2'}, {'meaning': 'M2', 'source': 'docs/README.md:2'}])
        two['checks'] = [self.check(meaning='M1'), self.check('stress', 'demand_up', 180.0, meaning='M1'),
                         self.check(meaning='M2'), self.check('stress', 'capacity_down', 210.0, meaning='M2')]
        split = self.errors([two])
        self.assertTrue(any('"M1" has not run planned stress: capacity_down' in e for e in split), split)
        self.assertTrue(any('"M2" has not run planned stress: demand_up' in e for e in split))

    def test_02_values_operators_and_harshness(self):
        broken = self.good_checks()
        broken[2] = self.check('stress', 'capacity_down', 512.0)
        self.assertTrue(any('value 512.0 breaks the limit 500' in e for e in self.errors([self.limit_rule(*broken)])))
        at = self.good_checks()
        at[2] = self.check('stress', 'capacity_down', 500.0)
        edge = self.good_checks()
        edge[2] = self.check('stress', 'capacity_down', 450.0)
        self.assertEqual(self.errors([self.limit_rule(*edge)]), [])
        self.assertTrue(any('not inside the CP1 margin' in e for e in self.errors([self.limit_rule(*at)])))
        self.assertTrue(any('equal not allowed' in e for e in self.errors([self.limit_rule(*at, inclusive=False)])))
        milder = self.good_checks()
        milder[1] = self.check('stress', 'demand_up', 100.0)
        self.assertTrue(any('milder than the public replay' in e for e in self.errors([self.limit_rule(*milder)])))
        same = [self.check(), self.check('stress', 'demand_up', 120.0), self.check('stress', 'capacity_down', 120.0)]
        self.assertTrue(any('repeats the public data' in e for e in self.errors([self.limit_rule(*same)])))
        no_param = self.good_checks()
        del no_param[1]['stress_param']
        self.assertTrue(any('stress_param required' in e for e in self.errors([self.limit_rule(*no_param)])))
        floor = self.limit_rule(self.check(value=0.97), self.check('stress', 'demand_up', 0.96), self.check('stress', 'capacity_down', 0.94),
                                limit=0.95, direction='min', margin=0.01)
        self.assertTrue(any('value 0.94 breaks the limit 0.95' in e for e in self.errors([floor])))
        for key, value in (('direction', 'up'), ('inclusive', None), ('unit', ''), ('statistic', '')):
            self.assertTrue(self.errors([self.limit_rule(**{key: value})], phase='cp1'), key)

    def test_03_estimates_use_the_bound_on_the_limit_side_and_enough_real_cases(self):
        est = dict(metric_source='estimated', uses_model=True, known_real_cases=7, explained_definition='predicted fail on the returned die')

        def checks(**extra):
            out = []
            for kind, stress, value in (('public', None, 120.0), ('stress', 'demand_up', 180.0), ('stress', 'capacity_down', 210.0)):
                fields = dict(estimated=True, risk_bound=value + 50, estimator_validation={'explained': 5, 'total': 7})
                fields.update(extra)
                out.append(self.check(kind, stress, value, **fields))
            return out
        self.assertEqual(self.errors([self.limit_rule(*checks(), **est)]), [])
        self.assertTrue(any('explains only 0 of 7' in e for e in self.errors([self.limit_rule(*checks(estimator_validation={'explained': 0, 'total': 7}), **est)])))
        self.assertTrue(any('fewer than the 7 planned' in e for e in self.errors([self.limit_rule(*checks(estimator_validation={'explained': 1, 'total': 1}), **est)])))
        self.assertTrue(any('strictly beyond the estimate' in e for e in self.errors([self.limit_rule(*checks(risk_bound=10.0), **est)])))
        self.assertTrue(any('95% bound 600.0' in e for e in self.errors([self.limit_rule(*checks(risk_bound=600.0), **est)])))
        plain = self.good_checks()
        self.assertTrue(any('every check is an estimate' in e for e in self.errors([self.limit_rule(*plain, **est)])))
        self.assertTrue(any('metric_source must be estimated' in e for e in self.errors([self.limit_rule(uses_model=True)], phase='cp1')))
        few = dict(est, known_real_cases=3)
        self.assertTrue(any('cannot certify this void limit' in e for e in self.errors([self.limit_rule(**few)], phase='cp1')))
        self.assertTrue(any('explained_definition' in e for e in self.errors([self.limit_rule(**dict(est, explained_definition=''))], phase='cp1')))

    def test_04_a_numeric_rule_cannot_drop_its_limit(self):
        rule = self.limit_rule()
        for key in ('limit', 'direction', 'inclusive', 'unit', 'statistic', 'stress_plan', 'metric_source', 'uses_model'):
            rule.pop(key)
        self.assertTrue(any('numeric limit' in e for e in self.errors([rule], phase='cp1')))
        rule['no_numeric_limit_reason'] = 'judged by counts'
        self.assertTrue(any('states a numeric threshold ("500을 넘")' in e for e in self.errors([rule], phase='cp1')))

    def test_05_two_sided_targets(self):
        target = {'id': 'COVER', 'rule': '90% 구간 포함률', 'source': 'docs/README.md:1', 'consequence': 'TARGET', 'target': 0.9, 'tolerance': 0.02}
        self.assertEqual(self.errors([target], phase='cp1'), [])
        self.assertTrue(any('observed {value, evidence}' in e for e in self.errors([target])))
        over = dict(target, observed={'value': 1.0, 'evidence': self.proof(value=1.0)})
        self.assertTrue(any('overshooting' in e for e in self.errors([over])))
        self.assertEqual(self.errors([dict(target, observed={'value': 0.91, 'evidence': self.proof(value=0.91)})]), [])
        self.assertTrue(any('does not state the recorded value' in e for e in self.errors([dict(target, observed={'value': 0.91, 'evidence': self.proof(value=0.5)})])))
        wide = dict(target, tolerance=0.2)
        self.assertTrue(any('wider than 5%' in e for e in self.errors([wide], phase='cp1')))
        self.write('docs/target.md', '포함률은 70~100% 사이면 만점이다.\n')
        quoted = dict(wide, tolerance_quote='포함률은 70~100% 사이면 만점이다.', tolerance_source='docs/target.md')
        self.assertEqual(self.errors([quoted], phase='cp1', not_rules=[{'at': 'docs/README.md:2', 'why': 'x'}, {'at': 'docs/target.md:1', 'why': 'this target'}]), [])
        self.assertTrue(any('docs/target.md:1' in e for e in self.errors([target], phase='cp1')))

    def plan(self, **extra):
        plan = {'output': 'policy.csv', 'metric': '30일 총비용', 'unit': '원', 'better': 'lower',
                'metric_quote': '평가 지표는 30일 총비용(원)이다.', 'metric_file': 'docs/README.md',
                'baselines': ['current', 'pooled'], 'per_group': True, 'search_plan': ['grid', 'local search'], 'min_gain': 200.0,
                'holdout_kind': 'time', 'tuning_until': '2026-06-30', 'evaluated_from': '2026-07-01'}
        plan.update(extra)
        return plan

    def guard(self, submitted=70000.0, baselines=None, rounds=None, **extra):
        self.write('submission/policy.csv', 'chamber,threshold\nA,240\n')
        artifact = self.write('submission/policy.csv', 'chamber,threshold\nA,240\n')
        baselines = baselines or [{'label': '현행 주기', 'kind': 'current', 'value': 120000.0},
                                  {'label': '전체 공통 임계', 'kind': 'pooled', 'value': 80000.0}]
        values = rounds or [95000.0, 70200.0, 70050.0, 70000.0]
        methods = ['grid', 'local search', 'local search', 'grid']
        round_list = [{'method': methods[i % 4], 'value': v, 'candidate_sha256': 'c%d' % i} for i, v in enumerate(values)]
        round_list[-1]['candidate_sha256'] = artifact['sha256']
        guard = {'output': 'policy.csv', 'submitted': submitted, 'baselines': baselines, 'artifact': artifact,
                 'holdout_kind': 'time', 'tuning_until': '2026-06-30', 'evaluated_from': '2026-07-01',
                 'optimization': {'rounds': round_list, 'chosen': len(round_list) - 1,
                                  'evidence': self.proof(rounds=values)}}
        guard['evidence'] = self.proof(submitted=submitted, baselines={b['label']: b['value'] for b in baselines})
        guard.update(extra)
        return guard

    def guarded(self, guard, plan=None, frozen_plan=None):
        plan = plan or self.plan()
        doc = {'baseline_plan': [plan], 'baseline_guard': [guard]}
        doc.pop('no_baseline_reason', None)
        value = self.table([], no_hard_rules_reason='The fixture task states no outcome rule.', **doc)
        value.pop('no_baseline_reason')
        frozen = copy.deepcopy(value)
        frozen['baseline_plan'] = [frozen_plan or plan]
        return self.mod['validate'](value, self.root, 'final', frozen=frozen)

    def test_06_cp1_baseline_plan(self):
        doc = self.table([], no_hard_rules_reason='none here')
        doc.pop('no_baseline_reason')
        self.assertTrue(any('CP1 needs baseline_plan' in e for e in self.mod['validate'](doc, self.root, 'cp1')))
        self.assertEqual(self.mod['validate'](dict(doc, baseline_plan=[self.plan()]), self.root, 'cp1'), [])
        for extra, message in (({'baselines': ['current']}, 'pooled baseline'), ({'per_group': None}, 'per_group (true/false)'),
                               ({'search_plan': ['grid']}, 'two different optimisation methods'), ({'min_gain': 0}, 'min_gain'),
                               ({'metric_quote': '평가 지표는 정확도다.'}, 'metric_quote is not in metric_file'), ({'unit': ''}, 'unit'),
                               ({'evaluated_from': '2026-2-01'}, 'full ISO dates'), ({'evaluated_from': '2026-02-30'}, 'full ISO dates'),
                               ({'evaluated_from': '2026-06-30'}, 'overlaps'), ({'holdout_kind': 'group'}, 'holdout_groups')):
            errors = self.mod['validate'](dict(doc, baseline_plan=[self.plan(**extra)]), self.root, 'cp1')
            self.assertTrue(any(message in e for e in errors), (extra, errors))

    def test_07_the_guard_compares_with_simple_baselines_on_the_evaluation_period(self):
        self.assertEqual(self.guarded(self.guard()), [])
        worse = self.guarded(self.guard(submitted=250000.0))
        self.assertTrue(any('worse than baseline "현행 주기"' in e for e in worse), worse)
        self.assertTrue(any('worse than baseline "전체 공통 임계"' in e and 'overfitted' in e for e in worse))
        rule = self.limit_rule(*self.good_checks())
        bad = self.proof(violations=4)
        all_out = [{'label': '현행 주기', 'kind': 'current', 'value': 1.0, 'admissible': False, 'violated_rule': 'DPPM', 'violation_evidence': bad},
                   {'label': '전체 공통 임계', 'kind': 'pooled', 'value': 2.0, 'admissible': False, 'violated_rule': 'DPPM', 'violation_evidence': bad}]
        doc = {'baseline_plan': [self.plan()], 'baseline_guard': [self.guard(baselines=all_out)]}
        value = self.table([rule], **doc)
        value.pop('no_baseline_reason')
        self.assertEqual(self.mod['validate'](value, self.root, 'final', frozen=copy.deepcopy(value)), [])
        reasonless = [dict(all_out[0], violated_rule='legacy'), all_out[1]]
        value['baseline_guard'] = [self.guard(baselines=reasonless)]
        self.assertTrue(any('only for breaking a rule in this table' in e for e in self.mod['validate'](value, self.root, 'final', frozen=copy.deepcopy(value))))
        self.assertTrue(any('planned at CP1 are missing at final: current' in e for e in self.guarded(self.guard(baselines=[{'label': '공통', 'kind': 'pooled', 'value': 80000.0}]))))
        moved = self.guarded(self.guard(tuning_until='2026-07-15', evaluated_from='2026-07-16'))
        self.assertTrue(any('boundary differs from the CP1 plan' in e for e in moved), moved)
        lying = self.guard()
        lying['evidence'] = self.proof(submitted=1.0, baselines={})
        self.assertTrue(any('does not state the recorded' in e for e in self.guarded(lying)))

    def test_08_the_search_reaches_the_optimum(self):
        still = self.guarded(self.guard(rounds=[95000.0, 80000.0, 75000.0, 70000.0]))
        self.assertTrue(any('has not reached the optimum' in e for e in still), still)
        dummy = self.guarded(self.guard(rounds=[95000.0, 70000.0, 99000.0, 98000.0]))
        self.assertTrue(any('has not reached the optimum' in e for e in dummy) or any('better admissible round' in e for e in dummy), dummy)
        g = self.guard(rounds=[95000.0, 80000.0, 75000.0, 70000.0])
        g['optimization'].update(bound=69500.0, bound_method='LP relaxation', bound_evidence=self.proof(bound=69500.0))
        self.assertEqual(self.guarded(g), [])
        g['optimization']['bound_evidence'] = self.proof(bound=1.0)
        self.assertTrue(any('does not state the recorded bound' in e for e in self.guarded(g)))
        g['optimization'].update(bound=71000.0, bound_evidence=self.proof(bound=71000.0))
        self.assertTrue(any('not a bound on the optimum' in e for e in self.guarded(g)))
        proven = self.guard(rounds=[70000.0])
        proven['optimization'].update(bound=70000.0, bound_method='MILP optimal', bound_evidence=self.proof(bound=70000.0))
        self.assertEqual(self.guarded(proven), [])
        twice = self.guard()
        twice['optimization']['rounds'][1]['candidate_sha256'] = twice['optimization']['rounds'][0]['candidate_sha256']
        self.assertTrue(any('repeat the same candidate' in e for e in self.guarded(twice)))
        early = self.guard()
        early['optimization']['chosen'] = 1
        self.assertTrue(any('better admissible round' in e for e in self.guarded(early)))
        other = self.guard()
        other['artifact'] = self.write('submission/other.csv', 'x')
        self.assertTrue(any('not the candidate of the chosen round' in e for e in self.guarded(other)))
        late = self.guard(rounds=[95000.0, 80000.0, 75000.0, 70000.0])
        late['optimization']['stop'] = {'reason': 'deadline', 'round_minutes': 20, 'remaining_minutes': 8}
        self.assertEqual(self.guarded(late), [])
        one = self.guard()
        for r in one['optimization']['rounds']:
            r['method'] = 'grid'
        self.assertTrue(any('one method only' in e for e in self.guarded(one)))
        self.assertTrue(any('planned at CP1 but not run: local search' in e for e in self.guarded(one)))

    def test_09_final_keeps_what_the_cp1_review_saw(self):
        cp1_rule = self.limit_rule()
        final_rule = self.limit_rule(*self.good_checks(), limit=800)
        self.assertTrue(any('changed since CP1 (limit)' in e for e in self.errors([final_rule], frozen=self.table([cp1_rule]))))
        two = dict(cp1_rule, candidates=cp1_rule['candidates'] + [{'meaning': '전체 칩', 'source': 'docs/README.md:2'}])
        self.assertTrue(any('dropped since CP1' in e for e in self.errors([self.limit_rule(*self.good_checks())], frozen=self.table([two]))))
        single = dict(cp1_rule, decision='SINGLE_MEANING')
        answered = dict(self.limit_rule(*self.good_checks()), decision='OFFICIAL_ANSWER')
        self.assertTrue(any('decision changed' in e for e in self.errors([answered], frozen=self.table([single]))))
        self.assertTrue(any('stress types dropped' in e for e in self.errors(
            [self.limit_rule(*self.good_checks())], frozen=self.table([dict(cp1_rule, stress_plan=['demand_up', 'capacity_down', 'mix_shift'])]))))
        self.assertTrue(any('rule from the CP1 table was removed' in e for e in self.errors([], no_hard_rules_reason='gone', frozen=self.table([cp1_rule]))))
        moved = self.guarded(self.guard(), plan=self.plan(evaluated_from='2026-07-10'), frozen_plan=self.plan())
        self.assertTrue(any('changed since CP1' in e and 'evaluated_from' in e for e in moved), moved)
        doc = self.table([], no_hard_rules_reason='none')
        frozen = dict(copy.deepcopy(doc), baseline_plan=[self.plan()])
        self.assertTrue(any('planned output removed since CP1' in e for e in self.mod['validate'](doc, self.root, 'final', frozen=frozen)))
        self.assertTrue(any('CP1 copy' in e for e in self.mod['validate'](doc, self.root, 'final')))

    def test_10_v27_check_anchors_the_cp1_copy_to_the_cp1_review(self):
        from test_v27_check import EvidenceTests
        t = EvidenceTests('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.complete_final_records()
        t.record('cp1_reviews', {'required_scope': {t.plan['records']['hard_rules']['path']: t.plan['records']['hard_rules']['sha256']}})
        self.assertFalse(any('hard_rules_cp1' in e for e in t.result('final')['errors']))
        t.record('hard_rules_cp1', {'version': 1, 'rules': [], 'materials': ['TASK.md'], 'no_hard_rules_reason': 'rewritten later', 'no_baseline_reason': 'x'})
        self.assertTrue(any('not the HARD_RULES.json version the CP1 review saw' in e for e in t.result('final')['errors']))

    def test_11_documents_and_template(self):
        template = json.loads((ROOT / 'templates/HARD_RULES.json').read_text(encoding='utf-8'))
        for key in ('baseline_plan', 'baseline_guard', 'materials', 'not_rules', 'answer_sources', 'unscanned_reviewed'):
            self.assertEqual(template[key], [], key)
        self.assertTrue(any('TARGET' in note for note in template['schema_notes']))
        skill = SKILL.read_text(encoding='utf-8')
        for phrase in ('(r4-3.17)', 'capacity_down', 'risk_bound', 'estimator_validation', '90% 목표에 100%', 'baseline_guard', 'per_group',
                       'no_baseline_reason', 'stress_plan', 'metric_source', 'baseline_plan', 'search_plan', '합격 수준에서 멈추지 않는다',
                       'inclusive', 'hard_rules_cp1', '튜닝 기간 점수'):
            self.assertIn(phrase, skill)
        contract = CONTRACT.read_text(encoding='utf-8')
        for phrase in ('r4-3.17', 'hard_rules_cp1', 'risk_bound', 'candidate_sha256', 'min_gain'):
            self.assertIn(phrase, contract)


    def test_12_review_findings_on_the_first_patch(self):
        # A deadline stop with fewer than three rounds is allowed when less than one round of time is left.
        late = self.guard(rounds=[95000.0, 70000.0])
        late['optimization']['stop'] = {'reason': 'deadline', 'round_minutes': 20, 'remaining_minutes': 8}
        self.assertEqual(self.guarded(late), [])
        late['optimization']['stop']['remaining_minutes'] = 30
        self.assertTrue(any('deadline stop needs' in e for e in self.guarded(late)))
        # inclusive and explained_definition are fixed at CP1.
        cp1_rule = self.limit_rule(inclusive=False)
        final_rule = self.limit_rule(*self.good_checks(), inclusive=True)
        self.assertTrue(any('changed since CP1 (inclusive)' in e for e in self.errors([final_rule], frozen=self.table([cp1_rule]))))
        est = dict(metric_source='estimated', uses_model=True, known_real_cases=7)
        old = self.limit_rule(explained_definition='predicted fail on the returned die', **est)
        new_rule = self.limit_rule(explained_definition='any alarm in the same week', **est)
        self.assertTrue(any('explained_definition' in e for e in self.mod['compare_freeze'](self.table([old]), self.table([new_rule]))))
        # A source naming line 20 does not account for line 2.
        lines = ['# 과제', 'DPPM이 500을 넘으면 불합격이다.'] + ['내용 %d' % n for n in range(3, 20)] + ['20번 줄: 보고서가 없으면 0점']
        self.write('docs/README.md', '\n'.join(lines) + '\n')
        rule = self.limit_rule(source='docs/README.md:20')
        errors = self.errors([rule], phase='cp1', not_rules=[])
        self.assertTrue(any('docs/README.md:2 ' in e and 'not in the table' in e for e in errors), errors)
        rule['source'] = 'docs/README.md:2, docs/README.md:20'
        self.assertEqual(self.errors([rule], phase='cp1', not_rules=[]), [])
        rule['source'] = 'docs/README.md:2-20'
        self.assertEqual(self.errors([rule], phase='cp1', not_rules=[]), [])

    def test_13_a_citation_of_a_file_name_with_spaces_counts(self):
        self.write('docs/과제 규정.md', '# 규정\n불량률이 기준을 넘으면 불합격\n')
        hit = [h for h in self.mod['scan'](self.root, ['불합격'], paths=('docs',))['hits'] if h['file'] == 'docs/과제 규정.md'][0]
        self.assertEqual(hit['key'], 'docs/과제 규정.md:2')
        rule = {'id': 'Q', 'rule': '불량률이 기준을 넘으면 불합격', 'source': hit['key'], 'consequence': 'SOFT'}
        self.assertEqual(self.errors([rule], phase='cp1'), [])
        for source in ('docs/과제 규정.md:20', 'old docs/과제 규정.md:2x', 'mydocs/과제 규정.md:2'):
            errors = self.errors([dict(rule, source=source)], phase='cp1')
            self.assertTrue(any('docs/과제 규정.md:2 ' in e for e in errors), (source, errors))
        self.assertEqual(self.errors([dict(rule, source='근거: docs/과제 규정.md:1-3, docs/README.md:9')], phase='cp1'), [])

if __name__ == '__main__':
    unittest.main()
