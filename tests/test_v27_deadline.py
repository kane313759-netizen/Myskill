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
            with self.subTest(value=value):
                result = deadline.calculate(value)
                self.assertEqual(result['status'], 'KNOWN')
                self.assertEqual(tuple(result[key][11:16] for key in
                                       ('confirmation_deadline', 'submission_start', 'work_lock', 'cp3_start')), expected)
        self.assertEqual(deadline.calculate({})['status'], 'UNKNOWN')

    def test_earlier_submission_cutoff_is_respected_and_timezone_compared(self):
        result = deadline.calculate({'FOLLOWUP': 'AFTER_CONFIRM', 'WINDOW_END': at('16:00'),
                                     'T_SUB': '2026-11-11T05:00:00+00:00'})
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

    def test_past_review_time_requires_replanning(self):
        with self.assertRaisesRegex(ValueError, 'already past'):
            deadline.calculate({'FOLLOWUP': 'NONE', 'T_SUB': at('16:00'), 'NOW': at('14:11')})
        result = deadline.calculate({'FOLLOWUP': 'NONE', 'T_SUB': at('16:00'), 'NOW': at('14:10')})
        self.assertEqual(result['status'], 'KNOWN')

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
