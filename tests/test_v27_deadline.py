"""Source-supplied schedule vectors are calculations, not official schedule claims."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('v27_deadline', ROOT / 'scripts/deadline.py')
deadline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deadline)


def at(time):
    return '2026-11-11T' + time + ':00+09:00'


class DeadlineTests(unittest.TestCase):
    def test_six_original_vectors(self):
        cases = [
            ({'FOLLOWUP': 'FIXED_TIME', 'T_SUB': at('16:00'), 'T_FU': at('16:00')},
             ('15:00', '14:50', '14:50', '14:10')),
            ({'FOLLOWUP': 'AFTER_CONFIRM', 'WINDOW_END': at('16:00')},
             ('15:25', '15:15', '14:15', '13:35')),
            ({'FOLLOWUP': 'NONE', 'T_SUB': at('16:00')},
             ('16:00', '15:50', '14:50', '14:10')),
            ({'FOLLOWUP': 'NONE', 'T_SUB': at('16:00'), 'S_pre': 0,
              'PITCH_STUDY_WINDOW': 'YES', 'participant_study_choice': True},
             ('16:00', '15:50', '15:50', '15:10')),
            ({'FOLLOWUP': 'AFTER_CONFIRM', 'WINDOW_END': at('23:00')},
             ('22:25', '22:15', '21:15', '20:35')),
        ]
        for value, expected in cases:
            value = dict(value, C=40)
            with self.subTest(value=value):
                result = deadline.calculate(value)
                self.assertEqual(result['status'], 'KNOWN')
                self.assertEqual(tuple(result[key][11:16] for key in
                                       ('confirmation_deadline', 'submission_start', 'work_lock', 'cp3_start')), expected)
                self.assertEqual(result['c_basis'], {'mode': 'EXPLICIT', 'key': 'C', 'minutes': 40})
        self.assertEqual(deadline.calculate({})['status'], 'UNKNOWN')

    def test_earlier_submission_cutoff_is_respected_and_timezone_compared(self):
        result = deadline.calculate({'FOLLOWUP': 'AFTER_CONFIRM', 'WINDOW_END': at('16:00'),
                                     'T_SUB': '2026-11-11T05:00:00+00:00', 'C': 40})
        self.assertEqual(result['confirmation_deadline'], '2026-11-11T05:00:00+00:00')
        self.assertEqual(result['cp3_start'], '2026-11-11T03:10:00+00:00')

    def test_unknowns_do_not_invent_dates_or_followup(self):
        for value in ({'FOLLOWUP': 'NONE'}, {'FOLLOWUP': 'FIXED_TIME', 'T_FU': at('16:00')},
                      {'FOLLOWUP': 'AFTER_CONFIRM', 'T_SUB': at('16:00')},
                      {'FOLLOWUP': 'UNKNOWN', 'T_SUB': at('16:00')}):
            self.assertEqual(deadline.calculate(value)['status'], 'UNKNOWN')

    def test_invalid_naive_negative_or_unconfirmed_study_changes_fail(self):
        base = {'FOLLOWUP': 'NONE', 'T_SUB': at('16:00')}
        for change in ({'T_SUB': '16:00'}, {'T_SUB': '2026-11-11T16:00:00'}, {'S': -1},
                       {'R': 9}, {'C': 0}, {'S_pre': 0}, {'S_pre': 30}, {'R': float('nan')},
                       {'R': True}, {'FOLLOWUP': 'OTHER'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                deadline.calculate(dict(base, **change))

    def test_past_review_time_keeps_schedule_until_confirmation(self):
        base = {'FOLLOWUP': 'FIXED_TIME', 'T_SUB': at('16:00'), 'T_FU': at('16:00'), 'C': 40}
        result = deadline.calculate(dict(base, NOW=at('14:30')))
        self.assertEqual(result['status'], 'KNOWN')
        self.assertEqual(result['cp3_start'], at('14:10'))
        self.assertEqual(result['work_lock'], at('14:50'))
        self.assertEqual(result['passed'], ['cp3_start'])
        self.assertTrue(any('cp3_start' in message for message in result['warnings']))
        result = deadline.calculate(dict(base, NOW=at('15:05')))
        self.assertEqual(result['status'], 'PAST_CONFIRMATION')
        self.assertEqual(result['confirmation_deadline'], at('15:00'))
        self.assertIn('confirmation_deadline', result['passed'])
        self.assertEqual(deadline.calculate(dict(base, NOW=at('14:10')))['status'], 'KNOWN')

    def test_review_reserve_accounts_for_sequential_and_parallel_roles(self):
        base = {'FOLLOWUP': 'FIXED_TIME', 'T_SUB': at('16:00'), 'T_FU': at('16:00')}
        sequential = deadline.calculate(base)
        self.assertEqual(sequential['review_reserve_minutes'], 90)
        self.assertEqual(sequential['cp3_start'], at('13:20'))
        self.assertEqual(sequential['c_basis']['batches'], 7)
        self.assertEqual(sequential['c_basis']['parallel_assumption'], 'NO')
        parallel = deadline.calculate(dict(base, REVIEW_PARALLEL='YES', REVIEW_CONCURRENCY=7))
        self.assertEqual(parallel['review_reserve_minutes'], 40)  # six at once, then SUBMISSION_RED after their fixes
        self.assertEqual(parallel['c_basis']['batches'], 2)
        unknown_width = deadline.calculate(dict(base, REVIEW_PARALLEL='YES'))
        self.assertEqual(unknown_width['review_reserve_minutes'], 90)
        self.assertEqual(unknown_width['c_basis']['parallel_assumption'], 'NO')
        self.assertIn('REVIEW_CONCURRENCY', unknown_width['c_basis']['note'])
        no_security = deadline.calculate(dict(base, FINAL_REVIEW_ROLES=6, REVIEW_PARALLEL='NO'))
        self.assertEqual(no_security['review_reserve_minutes'], 80)
        self.assertEqual(no_security['c_basis']['final_review_roles'], 6)
        self.assertEqual(deadline.calculate(dict(base, REVIEW_RESERVE=40))['c_basis']['key'], 'REVIEW_RESERVE')

    def test_distributed_template_is_a_planning_schedule_with_lunch_warning(self):
        env = deadline._read_input(ROOT / 'templates/ENV.md')
        self.assertEqual(env['switches']['T_SUB']['classification'], 'PLAN_DEFAULT')
        self.assertEqual(env['switches']['WINDOW_END']['classification'], 'PLAN_DEFAULT')
        self.assertNotIn('C', env['switches'])
        result = deadline.calculate(env)
        self.assertEqual(result['status'], 'KNOWN')
        self.assertEqual(result['work_lock'], at('14:15'))
        self.assertEqual(result['cp3_start'], at('12:45'))
        self.assertEqual(result['review_reserve_minutes'], 90)
        self.assertTrue(any('lunch' in message.lower() for message in result['warnings']))
        self.assertEqual(env['switches']['EXECUTION_TOOLS']['value'], ['exec_command'])

    def test_lunch_warning_does_not_move_schedule_and_respects_boundaries(self):
        base = {'FOLLOWUP': 'FIXED_TIME', 'T_SUB': at('16:00'), 'T_FU': at('16:00'), 'C': 90,
                'LUNCH_POLICY': 'PAUSE', 'LUNCH_START': at('13:30'), 'LUNCH_END': at('14:00')}
        result = deadline.calculate(base)
        self.assertEqual((result['cp3_start'], result['work_lock']), (at('13:20'), at('14:50')))
        self.assertTrue(any('lunch' in message.lower() for message in result['warnings']))
        self.assertFalse(deadline.calculate(dict(base, LUNCH_END=at('13:20'), LUNCH_START=at('12:00')))['warnings'])
        self.assertFalse(deadline.calculate(dict(base, LUNCH_POLICY='CONTINUOUS'))['warnings'])

    def test_invalid_review_assumptions_and_lunch_intervals_fail(self):
        base = {'FOLLOWUP': 'NONE', 'T_SUB': at('16:00')}
        for change in ({'REVIEW_PARALLEL': 'MAYBE'}, {'REVIEW_CONCURRENCY': 0}, {'REVIEW_CONCURRENCY': 2.5}, {'REVIEW_CONCURRENCY': True}, {'REVIEW_MINUTES_EACH': 0},
                       {'FIX_BUFFER': -1}, {'FINAL_REVIEW_ROLES': True}, {'FINAL_REVIEW_ROLES': 0},
                       {'FINAL_REVIEW_ROLES': 8}, {'REVIEW_MINUTES_EACH': 1440},
                       {'LUNCH_POLICY': 'PAUSE', 'LUNCH_START': at('13:00'), 'LUNCH_END': at('12:00')}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                deadline.calculate(dict(base, **change))

    def test_past_confirmation_cli_returns_one_with_schedule(self):
        with tempfile.TemporaryDirectory(prefix='v27-deadline-now-') as temporary:
            source = Path(temporary) / 'ENV.json'
            base = {'FOLLOWUP': 'FIXED_TIME', 'T_SUB': at('16:00'), 'T_FU': at('16:00'), 'C': 40}
            cmd = [sys.executable, '-I', '-X', 'utf8', str(ROOT / 'scripts/deadline.py'), '--input', str(source)]
            for now, status, code in (('14:30', 'KNOWN', 0), ('15:05', 'PAST_CONFIRMATION', 1)):
                source.write_text(json.dumps(dict(base, NOW=at(now))), encoding='utf-8')
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                value = json.loads(result.stdout)
                self.assertEqual(value['status'], status)
                self.assertEqual(value['submission_start'], at('14:50'))

    def test_isolated_cli_markdown_input_unknown_and_new_output_only(self):
        with tempfile.TemporaryDirectory(prefix='v27-deadline-') as temporary:
            root = Path(temporary)
            source, output = root / 'ENV.md', root / 'calculated.json'
            source.write_text('# ENV\n```json\n' + json.dumps({'switches': {
                'FOLLOWUP': {'value': 'NONE'}, 'T_SUB': {'value': at('16:00')}}}) + '\n```\n', encoding='utf-8')
            cmd = [sys.executable, '-I', '-X', 'utf8', str(ROOT / 'scripts/deadline.py'), '--input', str(source)]
            before = source.read_bytes()
            result = subprocess.run(cmd + ['--output', str(output)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(source.read_bytes(), before)
            original = output.read_bytes()
            result = subprocess.run(cmd + ['--output', str(output)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_bytes(), original)
            source.write_text('{}', encoding='utf-8')
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['status'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
