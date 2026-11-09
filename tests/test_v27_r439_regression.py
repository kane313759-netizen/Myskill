"""r4-3.9 regression (external review): executable checks instead of string checks.
(1) Saturation guidance by controller type: an EWMA/run-to-run state updated with the applied (clamped) setting recovers after the
limit releases, while freezing the update or updating with the computed setting does not; a PI integrator with conditional
integration recovers faster than a naive integrator and than "stop whenever saturated".
(2) One-sided 95% upper end: n >= 20 uses max(empirical 95% quantile, mean + 1.645 sd); n < 20 does not use the empirical quantile
(it equals the maximum) and uses the t prediction bound; standardized errors use each item's prediction standard error, and the
standard error of the mean under-covers.
(3) JSONL scratch fallback: an end-to-end audit through a linked run/ folder is refused and not RECORDED, nothing is written outside
the kit, and a fallback folder created before a failing check is removed."""
import json
import math
import os
import pathlib
import random
import runpy
import shutil
import statistics
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
T95 = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833, 10: 1.812,
       11: 1.796, 12: 1.782, 13: 1.771, 14: 1.761, 15: 1.753, 16: 1.746, 17: 1.740, 18: 1.734, 19: 1.729}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def disturbance():
    return [0.0] * 10 + [6.0] * 30 + [1.0] * 40      # needs u = -6 while the limit is -3, then u = -1


def ewma_sse_after_release(mode, lam=0.3, lo=-3.0, hi=3.0):
    dhat, sse = 0.0, 0.0
    for k, d in enumerate(disturbance()):
        cmd = -dhat
        u = clamp(cmd, lo, hi)
        y = u + d
        if k >= 40:
            sse += y * y
        if mode == 'applied':
            dhat = lam * (y - u) + (1 - lam) * dhat
        elif mode == 'freeze':
            if cmd == u:
                dhat = lam * (y - u) + (1 - lam) * dhat
        elif mode == 'computed':
            dhat = lam * (y - cmd) + (1 - lam) * dhat
    return sse


def pi_sse_after_release(mode, ki=0.5, lo=-3.0, hi=3.0):
    integ, y_prev, sse = 0.0, 0.0, 0.0
    for k, d in enumerate(disturbance()):
        e = -y_prev
        cmd = ki * integ
        u = clamp(cmd, lo, hi)
        saturated = cmd != u
        deeper = (cmd > hi and e > 0) or (cmd < lo and e < 0)
        if mode == 'naive' or (mode == 'conditional' and not deeper) or (mode == 'freeze' and not saturated):
            integ += e
        y = u + d
        if k >= 40:
            sse += y * y
        y_prev = y
    return sse


def upper_end(errors):
    """The documented rule, as a function of the measured errors."""
    n = len(errors)
    mean, sd = statistics.mean(errors), statistics.stdev(errors)
    if n >= 20:
        empirical = sorted(errors)[math.ceil(0.95 * n) - 1]
        return max(empirical, mean + 1.645 * sd)
    return mean + T95[n - 1] * sd * math.sqrt(1 + 1 / n)


def _link_dir(link, target):
    try:
        if os.name == 'nt':
            done = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True, text=True)
            return done.returncode == 0 and os.path.lexists(str(link))
        os.symlink(str(target), str(link), target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False


def _deny_system_temp(real):
    def guarded(suffix=None, prefix=None, dir=None):
        if dir is None:
            raise PermissionError('sandbox denied system temp')
        return real(suffix, prefix, dir)
    return guarded


class RegressionR439(unittest.TestCase):
    # ---- (1) saturation guidance ----
    def test_01_playbook_wording_by_controller_type(self):
        text = (ROOT / 'references/semiconductor-domain-playbook.md').read_text(encoding='utf-8')
        self.assertIn('EWMA·런투런 제어기는 계산한 값이 아니라 실제로 적용한(잘린) 설정값과 측정값으로 상태를 계속 갱신하고, 갱신을 멈추지 않는다', text)
        self.assertIn('PI 제어기는 출력이 포화됐고 오차가 포화를 더 깊게 하는 방향일 때만 그 단계의 적분을 건너뛰고', text)
        self.assertIn('한 상태에 두 방식을 섞지 않는다', text)

    def test_02_ewma_applied_update_recovers(self):
        applied, freeze, computed = (ewma_sse_after_release(m) for m in ('applied', 'freeze', 'computed'))
        self.assertLess(applied, 0.25 * freeze, (applied, freeze))
        self.assertLess(applied, 0.25 * computed, (applied, computed))

    def test_03_pi_conditional_integration_recovers(self):
        conditional, naive, freeze = (pi_sse_after_release(m) for m in ('conditional', 'naive', 'freeze'))
        self.assertLess(conditional, 0.25 * naive, (conditional, naive))
        self.assertLess(conditional, 0.25 * freeze, (conditional, freeze))

    # ---- (2) one-sided 95% upper end ----
    def test_04_rule_text_and_t_table(self):
        text = (ROOT / SKILL).read_text(encoding='utf-8')
        for term in ('그 항목 하나의 예측 표준오차이며, 평균의 표준오차(표준편차 ÷ √표본 수)가 아니다', '표본이 20개 이상이면',
                     '표본이 20개 미만이면 경험적 분위수가 최댓값과 같아지므로 쓰지 않고', 't(0.95, 표본 수 − 1) × 오차 표준편차 × √(1 + 1 ÷ 표본 수)',
                     'z를 쓰면 고른 값에 그 항목의 표준오차를 곱해 추정에 더한다'):
            self.assertIn(term, text)
        self.assertNotIn('잠정치가 숫자로 나가면 반려', text)
        contract = (ROOT / 'references/v27-contract.md').read_text(encoding='utf-8')
        self.assertIn('## r4-3.9', contract)
        for df, value in T95.items():
            self.assertIn('%d %.3f' % (df, value), contract)

    def test_05_small_sample_does_not_fall_back_to_the_maximum(self):
        errors = [0.1, -0.3, 0.2, 0.0, 0.4, -0.1, 0.3, -0.2, 0.1, 2.5]
        self.assertEqual(sorted(errors)[math.ceil(0.95 * len(errors)) - 1], max(errors), 'n < 20: empirical 95% quantile is the maximum')
        self.assertNotEqual(upper_end(errors), max(errors))

    def test_06_per_item_standard_error_covers_and_mean_standard_error_does_not(self):
        rng = random.Random(7)
        history = []
        for _ in range(400):
            se = rng.uniform(0.5, 2.0)
            z = rng.gauss(0, 1) if rng.random() < 0.9 else rng.gauss(1.5, 0.5)     # not normal: a second hump
            history.append((se, z * se))
        z_hist = [err / se for se, err in history]
        k = upper_end(z_hist)
        new = []
        for _ in range(4000):
            se = rng.uniform(0.5, 2.0)
            z = rng.gauss(0, 1) if rng.random() < 0.9 else rng.gauss(1.5, 0.5)
            new.append((se, z * se))
        covered = sum(err <= k * se for se, err in new) / len(new)
        self.assertGreaterEqual(covered, 0.94)
        sd = statistics.stdev(err for _, err in history)
        mean_se_margin = 1.645 * sd / math.sqrt(len(history))
        wrong = sum(err <= mean_se_margin for _, err in new) / len(new)
        self.assertLess(wrong, 0.75, 'standard error of the mean puts the margin almost on the estimate')

    # ---- (3) JSONL scratch fallback ----
    def test_07_audit_through_linked_run_is_refused_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            kit = pathlib.Path(td) / 'kit'
            shutil.copytree(str(ROOT / 'scripts'), str(kit / 'scripts'))
            outside = pathlib.Path(td) / 'outside'
            outside.mkdir()
            if not _link_dir(kit / 'run', outside):
                self.skipTest('directory links not permitted here')
            data = pathlib.Path(td) / 'data'
            data.mkdir()
            (data / 'events.jsonl').write_text('\n'.join(json.dumps({'id': i, 'v': i * 0.5}) for i in range(30)) + '\n', encoding='utf-8')
            audit = runpy.run_path(str(kit / 'scripts/data_audit.py'), run_name='r439_audit')['audit']
            with mock.patch.object(tempfile, 'mkdtemp', _deny_system_temp(tempfile.mkdtemp)):
                result = audit(data, {'files': ['events.jsonl']})
            self.assertTrue(any('scratch fallback refused' in str(e.get('error')) for e in result['errors']), result['errors'])
            self.assertFalse([a for a in result['files'] if a.get('path') == 'events.jsonl' and a.get('status') == 'RECORDED'])
            self.assertEqual(list(outside.iterdir()), [], 'nothing may be written outside the kit')

    def test_08_fallback_folder_removed_when_a_later_check_fails(self):
        with tempfile.TemporaryDirectory() as td:
            kit = pathlib.Path(td) / 'kit'
            (kit / 'scripts').mkdir(parents=True)
            shutil.copy2(str(ROOT / 'scripts/v27_jsonl.py'), str(kit / 'scripts/v27_jsonl.py'))
            scratch = runpy.run_path(str(kit / 'scripts/v27_jsonl.py'), run_name='r439_jsonl')['_scratch']
            real_inside = scratch.__globals__['_inside_kit']

            def failing_for_holder(path, kit_root, parts):
                if len(parts) > 2:
                    raise ValueError('simulated comparison failure')
                return real_inside(path, kit_root, parts)
            scratch.__globals__['_inside_kit'] = failing_for_holder
            try:
                with mock.patch.object(tempfile, 'mkdtemp', _deny_system_temp(tempfile.mkdtemp)):
                    with self.assertRaises(ValueError):
                        scratch()
            finally:
                scratch.__globals__['_inside_kit'] = real_inside
            self.assertEqual(list((kit / 'run' / '.v27-tmp').iterdir()), [], 'the created fallback folder must be removed')

    @unittest.skipUnless(os.name == 'nt', 'Windows long-path prefix')
    def test_09_long_path_prefix_is_normalized(self):
        real = runpy.run_path(str(ROOT / 'scripts/v27_jsonl.py'), run_name='r439_real')['_real']
        base = os.environ.get('SystemRoot', 'C:\\Windows')
        self.assertEqual(real('\\\\?\\' + base), real(base))


if __name__ == '__main__':
    unittest.main()
