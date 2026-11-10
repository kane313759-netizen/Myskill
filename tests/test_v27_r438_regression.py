"""r4-3.8 regression: the one-sided 95% upper end does not assume a normal distribution. The documented rule takes the larger of the
empirical 95% quantile (ceil(0.95 n)-th smallest) and mean + 1.645 sd; 1.645 alone is not used. Counterexample from external review:
errors -1/0/+1 with 10%/80%/10% (skew 0, n = 10,000) give mean + 1.645 sd = 0.7357 but only 90% coverage."""
import math
import pathlib
import statistics
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = '.agents/skills/hackathon-orchestrator-universal/SKILL.md'


def documented_upper_end(errors):
    """The rule as written in SKILL: max(empirical 95% quantile, mean + 1.645 sd)."""
    ordered = sorted(errors)
    empirical = ordered[math.ceil(0.95 * len(ordered)) - 1]
    normal = statistics.mean(errors) + 1.645 * statistics.pstdev(errors)
    return max(empirical, normal), empirical, normal


class RegressionR438(unittest.TestCase):
    def test_01_rule_text(self):
        text = (ROOT / SKILL).read_text(encoding='utf-8')
        for term in ('정규분포를 가정하지 않는다', '올림(0.95 × 표본 수)번째 값', '둘 다 계산해 큰 쪽을 쓰고 두 값을 기록한다',
                     '1.645는 정규분포일 때만 95%이므로 단독으로 쓰지 않는다'):
            self.assertIn(term, text)
        self.assertNotIn('위쪽 끝은 추정 + (오차 평균 + 1.645 × 오차 표준편차)로 계산하고', text)
        contract = (ROOT / 'references/v27-contract.md').read_text(encoding='utf-8')
        self.assertIn('## r4-3.8', contract)
        self.assertNotIn('z의 평균 + 1.645 × 표준편차, 표본 30개 미만', contract)

    def test_02_counterexample_is_covered(self):
        errors = [-1.0] * 1000 + [0.0] * 8000 + [1.0] * 1000
        upper, empirical, normal = documented_upper_end(errors)
        self.assertAlmostEqual(normal, 0.7357, places=3)
        self.assertEqual(empirical, 1.0)
        self.assertGreaterEqual(sum(e <= upper for e in errors) / len(errors), 0.95)
        self.assertLess(sum(e <= normal for e in errors) / len(errors), 0.95, 'the normal-only formula is the defect this guards against')

    def test_03_normal_like_sample_unchanged(self):
        errors = [statistics.NormalDist().inv_cdf((i + 0.5) / 2000) for i in range(2000)]
        upper, empirical, normal = documented_upper_end(errors)
        self.assertAlmostEqual(upper, 1.645, delta=0.02)


if __name__ == '__main__':
    unittest.main()
