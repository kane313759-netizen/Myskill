"""Evidence-gate regressions: the review must control implementation, not just five tokens."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kit_gate', ROOT / 'scripts/gate_check.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='kit-gate-')
        self.task = Path(self.temp.name)
        self.kit = self.task / '.hackathon-kit'
        shutil.copytree(ROOT / 'templates', self.kit / 'templates')
        shutil.copytree(ROOT / 'templates', self.kit / 'run')
        shutil.copy2(ROOT / 'EXAM_POLICY.md', self.kit / 'EXAM_POLICY.md')
        (self.task / 'task.txt').write_text('Input: integer n. Required output filename: result.json; score equals n.\n')

    def tearDown(self):
        self.temp.cleanup()

    def complete_state(self):
        text = (self.kit / 'run/STATE.md').read_text()
        replacements = {
            'grader_contract: NOT_INSPECTED': 'grader_contract: RECORDED',
            'baseline: NOT_RUN': 'baseline: UNAVAILABLE_WITH_REASON',
            'immutable_inventory: NOT_RUN': 'immutable_inventory: RECORDED',
            'cp1_constraint_red: NOT_RUN': 'cp1_constraint_red: DONE',
            'constraint_gate: OPEN': 'constraint_gate: CLOSED',
        }
        for before, after in replacements.items():
            text = text.replace(before, after)
        (self.kit / 'run/STATE.md').write_text(text)

    def complete(self):
        self.complete_state()
        contents = {
            'GRADER.md': '# GRADER\n## What is scored\nTask task.txt:1 scores n.\n## Required output / submission path\nresult.json, exact JSON integer n.\n## Submission collection\nFile upload result.json; helpers excluded. Source task.txt:1.\n## Evidence / inspection\ntask.txt:1 inspected; no test/build commands supplied.\n',
            'BASELINE.md': '# BASELINE\n## Before edits\nUNAVAILABLE_WITH_REASON: task.txt supplies only I/O, no executable baseline or tests. Inspected task.txt and task directory.\n',
            'IMMUTABLES.md': '# IMMUTABLES\n## Inventory\nRequired filename result.json and integer output, from task.txt:1; preserve exact contract.\n',
            'SPEC_DRAFT.md': '# SPEC\n## Grading target\nEmit n as specified in task.txt:1.\n## Required output / command\nresult.json via task-provided invocation.\n## Input contract\nOne integer n, task.txt:1.\n## Output contract\nJSON integer n in result.json.\n## Confirmed constraints with evidence\nFilename result.json, task.txt:1.\n## Assumptions / open questions\nN/A: no extra domain penalty or unsupported resource assumptions.\n## Verification plan\nCheck filename, parse integer, compare to n using temporary data.\n',
            'CONSTRAINTS.md': '# CONSTRAINTS\n## Constraint register\nCONFIRMED: filename result.json and integer n, task.txt:1; verify exact output and value.\n',
            'CP1_RED.md': '# CP1\n## Attacks and original evidence\nAttacked output filename against task.txt:1; result.json matches. Attacked invented objective; spec preserves n.\n',
        }
        for name, content in contents.items():
            (self.kit / 'run' / name).write_text(content)
        self.report = {
            'version': 1, 'status': 'COMPLETE',
            'reviewer': {'role': 'CONSTRAINT_RED', 'actual_model': 'Sol 6.1', 'context_mode': 'NO_HISTORY'},
            'source_paths': ['task.txt'], 'artifacts': gate.artifact_hashes(self.kit),
            'findings': [], 'attempted_attacks': ['Required filename checked against task.txt:1; no mismatch survived.'],
        }
        self.save_report()

    def save_report(self):
        (self.kit / 'run/CP1_REVIEW.json').write_text(json.dumps(self.report))

    def test_official_policy_is_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT / 'EXAM_POLICY.md').read_bytes()).hexdigest(), 'b4deca2c78495bee0d19d0fbbfea797e65d49075aae461c80d21651f9b6ed558')

    def test_preflight_checks_format_before_review_but_cannot_approve_implementation(self):
        cli = [sys.executable, '-B', str(ROOT / 'scripts/gate_check.py'), '--kit', str(self.kit), '--preflight']
        initial = subprocess.run(cli, capture_output=True, text=True)
        self.assertEqual(initial.returncode, 2)
        self.assertIn('PREFLIGHT FAIL', initial.stdout)
        self.complete()
        (self.kit / 'run/STATE.md').write_text((ROOT / 'templates/STATE.md').read_text())
        (self.kit / 'run/CP1_REVIEW.json').unlink()
        (self.kit / 'run/CP1_RED.md').unlink()
        before = {p.name: p.read_bytes() for p in (self.kit / 'run').iterdir() if p.is_file()}
        ready = subprocess.run(cli, capture_output=True, text=True)
        self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)
        self.assertIn('document format only', ready.stdout)
        self.assertNotIn('GATE OK', ready.stdout)
        self.assertTrue(gate.check_gate(self.kit))
        after = {p.name: p.read_bytes() for p in (self.kit / 'run').iterdir() if p.is_file()}
        self.assertEqual(before, after)

    def test_initial_state_and_marker_only_completion_fail(self):
        self.assertTrue(gate.check_gate(self.kit))
        self.complete_state()
        errors = gate.check_gate(self.kit)
        self.assertTrue(any('template' in error for error in errors))

    def test_actual_evidence_and_no_surviving_findings_pass(self):
        self.complete()
        self.assertEqual(gate.check_gate(self.kit), [])

    def test_unresolved_p1_cannot_close_even_when_review_is_done(self):
        self.complete()
        self.report['findings'] = [{'id': 'R1', 'severity': 'P1', 'status': 'OPEN', 'evidence': 'task.txt:1 requires result.json; output is answer.json', 'verification': ''}]
        self.save_report()
        self.assertTrue(any('blocking finding R1' in error for error in gate.check_gate(self.kit)))
        self.report['findings'][0]['status'] = 'ACCEPTED_RISK'
        self.report['findings'][0]['verification'] = 'Deadline is near'
        self.save_report()
        self.assertTrue(any('blocking finding' in error for error in gate.check_gate(self.kit)))

    def test_fixed_and_disproved_need_evidence_and_recheck(self):
        self.complete()
        self.report['findings'] = [{'id': 'R1', 'severity': 'P1', 'status': 'FIXED', 'evidence': 'task.txt:1 filename', 'verification': ''}]
        self.save_report()
        self.assertTrue(any('needs verification' in error for error in gate.check_gate(self.kit)))
        self.report['findings'][0]['verification'] = 'Reviewer rechecked corrected SPEC filename against task.txt:1'
        self.save_report()
        self.assertEqual(gate.check_gate(self.kit), [])

    def test_contract_change_invalidates_old_review(self):
        self.complete()
        path = self.kit / 'run/SPEC_DRAFT.md'
        path.write_text(path.read_text().replace('result.json', 'answer.json'))
        self.assertTrue(any('changed: SPEC_DRAFT.md' in error for error in gate.check_gate(self.kit)))

    def test_routine_verification_note_does_not_invalidate_contract(self):
        self.complete()
        (self.kit / 'run/VERIFY.md').write_text('A new regression passed; output log evidence attached.\n')
        self.assertEqual(gate.check_gate(self.kit), [])

    def test_duplicate_state_rejected_and_basic_markdown_supported(self):
        self.complete()
        path = self.kit / 'run/STATE.md'
        original = path.read_text()
        path.write_text(original.replace('- baseline: UNAVAILABLE_WITH_REASON', '- **baseline**: UNAVAILABLE_WITH_REASON (no supplied tests)'))
        self.assertEqual(gate.check_gate(self.kit), [])
        path.write_text(path.read_text() + '\nconstraint_gate: CLOSED\n')
        self.assertTrue(any('duplicate key' in error for error in gate.check_gate(self.kit)))

    def test_missing_original_or_main_notes_as_original_rejected(self):
        self.complete()
        self.report['source_paths'] = ['missing-task.txt']
        self.save_report()
        self.assertTrue(any('does not exist' in error for error in gate.check_gate(self.kit)))
        self.report['source_paths'] = ['.hackathon-kit/run/GRADER.md']
        self.save_report()
        self.assertTrue(any('not original' in error for error in gate.check_gate(self.kit)))

    def test_ui_only_task_requires_provenance_and_actual_excerpt(self):
        self.complete()
        self.report['source_paths'] = ['.hackathon-kit/run/TASK_EVIDENCE.md']
        self.save_report()
        self.assertTrue(gate.check_gate(self.kit))
        (self.kit / 'run/TASK_EVIDENCE.md').write_text('# Evidence\n## Provenance\nParticipant task UI excerpt at 12:10 UTC, original instructions.\n## Original task / answer excerpts\nRequired filename is result.json.\n')
        self.assertEqual(gate.check_gate(self.kit), [])

    def test_clean_reviewer_and_concrete_attacks_required(self):
        self.complete()
        self.report['reviewer']['context_mode'] = 'INHERITED'
        self.report['attempted_attacks'] = []
        self.save_report()
        errors = gate.check_gate(self.kit)
        self.assertTrue(any('NO_HISTORY' in error for error in errors))
        self.assertTrue(any('attempted_attacks' in error for error in errors))

    def test_heading_only_edit_does_not_make_template_substantive(self):
        self.complete()
        path = self.kit / 'run/GRADER.md'
        text = (self.kit / 'templates/GRADER.md').read_text().replace('# GRADER / SUBMISSION CONTRACT', '# Edited title')
        path.write_text(text)
        self.report['artifacts'] = gate.artifact_hashes(self.kit)
        self.save_report()
        self.assertTrue(any('needs evidence in section' in error for error in gate.check_gate(self.kit)))

    def test_malformed_receipt_fails_without_traceback(self):
        self.complete()
        for value in ([], None, {'reviewer': {'context_mode': []}}, {'findings': [{'id': [], 'severity': [], 'status': []}]}):
            (self.kit / 'run/CP1_REVIEW.json').write_text(json.dumps(value))
            self.assertTrue(gate.check_gate(self.kit))

    def test_cli_hashes_is_utility_not_approval_and_gate_is_read_only(self):
        self.complete()
        before = {p.name: p.read_bytes() for p in (self.kit / 'run').iterdir() if p.is_file()}
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/gate_check.py'), '--kit', str(self.kit)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('GATE OK', result.stdout)
        after = {p.name: p.read_bytes() for p in (self.kit / 'run').iterdir() if p.is_file()}
        self.assertEqual(before, after)
        utility = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/gate_check.py'), '--kit', str(self.kit), '--artifact-hashes'], capture_output=True, text=True)
        self.assertEqual(json.loads(utility.stdout), self.report['artifacts'])


if __name__ == '__main__':
    unittest.main()
