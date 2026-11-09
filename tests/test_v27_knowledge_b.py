"""Local knowledge variant (B): playbooks and reviewer questions are present, referenced, and stay out of MAIN's default reading."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
FILES = ('references/semiconductor-domain-playbook.md',
         'references/semiconductor-domain-playbook-2.md',
         'references/domain-review-questions.md')


class KnowledgeVariantTest(unittest.TestCase):
    def test_files_exist_and_are_utf8(self):
        for rel in FILES:
            text = (ROOT / rel).read_text(encoding='utf-8')
            self.assertGreater(len(text), 500, rel)

    def test_skill_references_each_file_once(self):
        text = SKILL.read_text(encoding='utf-8')
        for rel in FILES:
            self.assertEqual(text.count(rel), 1, rel)

    def test_playbook_is_on_demand_and_subordinate_to_task_data(self):
        text = SKILL.read_text(encoding='utf-8')
        self.assertIn('처음부터 전체를 읽지 않는다', text)
        self.assertIn('과제 데이터로 확인하기 전에는 사실이나 제약으로 쓰지 않는다', text)

    def test_review_questions_are_reviewer_only_and_not_rules(self):
        q = (ROOT / FILES[2]).read_text(encoding='utf-8')
        self.assertIn('MAIN은 처음부터 읽지 않는다', q)
        self.assertIn('질문은 규칙이 아니다', q)
        self.assertNotIn('출제자', q)
        self.assertIn('P1은 예상 지표 변화(숫자)와 확인 방법을 함께 적을 때만', q)
        for rel in FILES[:2]:
            self.assertIn('결선 과제 주제와 다르면 1장 수식·2장 공통 점검만 참고', (ROOT / rel).read_text(encoding='utf-8'))
        self.assertEqual(len(re.findall(r'^\d+\. ', q, flags=re.M)), 20)


if __name__ == '__main__':
    unittest.main()
