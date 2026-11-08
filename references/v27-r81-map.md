# R81_MAP — v2.7 추가판과 실제 로컬 기반 대조

요청의 r8.1 명칭은 현재 로컬 r8.2 기반까지 대조했다. 기준 커밋 affd3c1623f67697247c67f6d30df9e76b9bc076, VERSION 2026-11-08-finals-r8.2-candidate. v2.7은 기존 추적 파일을 수정하지 않는다. 최신 공식 본선 지시가 우선하며, EXAM_POLICY.md는 2차 예선 전용이다. 기존 승인 RED 6종과 조건부 SECURITY_RED는 유지한다.

| 장치 | 현재 위치 | 추가판 연결 |
|---|---|---|
| 정책 우선순위 | `EXAM_POLICY.md:3` | 2차 예선 전용 보존. 본선은 FINALS_POLICY와 신규 출처 기록을 우선 |
| 본선 진입·기술 소유권 | `.agents/skills/hackathon-finals/SKILL.md:15` | 현재 본선 절차 보존; 새 universal 진입점이 추가 자료를 연결 |
| 기존 역할·체크포인트 | `.agents/skills/hackathon-orchestrator/SKILL.md:15` | 예선 역할/CP1~3는 그대로. 본선에는 현재 finals-reviews 적용 |
| 독립 검토 실행 확인 | `references/review-execution.md:12` | 작업자 ID·활동·완료 원문 기록 보존 |
| CP1 영수증 | `scripts/gate_check.py:121` | 예선 5개 문서·실행 영수증 검사 변경 금지 |
| EDGE_RED | `.agents/skills/edge-redteam/SKILL.md:6` | 실제 별도 역할 유지; CODE_RED로 대체하지 않음 |
| 본선 RED 6종 + 조건부 SECURITY | `references/finals-reviews.md:29` | r8.2에 추가된 승인 구성까지 유지 |
| 현재 검토 집계 | `scripts/finals_review_check.py:8` | 기존 필수 역할·현재 설정/트리거·별도 보고서 검사 보존 |
| 로컬 평가 | `references/local-evaluation.md:1` | 원문 오라클·양성/음성 대조군과 비교 가능 범위 유지 |
| 설명과 실제 도구 이해 | `references/participant-understanding.md:9` | 선택/변경/최종에 실제 방법·대안·한계 설명 유지 |
| 최종 설명 | `.agents/skills/final-explain/SKILL.md:6` | 본선은 final-explain의 예선 분기 대신 finals 설명 사용 |
| 후속 6개 개요 | `.agents/skills/followup-prep/SKILL.md:6` | 본선 FOLLOWUP 확인 시에만 준비; 공식 없는 6문항 단정 금지 |
| 실제 사람 판단 | `templates/HUMAN_JUDGMENT.md:1` | 실제 선택만 기록; AI 기본값을 사람 선택으로 기록하지 않음 |
| 설치·소유권·정리 | `scripts/kit_lifecycle.py:289` | 기존 backend 수정 없이 추가 wrapper/새 파일로 연결 |
| 역할 프롬프트 | `prompts/CODE_RED.md:1` | 예선 고정 정책 프롬프트를 본선에 복사 사용하지 않음 |
| STATE 키 | `templates/STATE.md:1` | 원래 키 불변; 추가 상태는 별도 V27_STATE.json |

현재 기반과 다른 제안: 본선 정책은 이미 FINALS_POLICY.md에 있으며, 모델·6문항·게이트는 예선 전용이다. 신규 EXAM_POLICY_FINAL.md는 실제 본선 출처 기록이며 기존 정책 파일을 대체하지 않는다. 모든 예선 문서를 본선에 강제하는 방식으로 되돌리지 않는다.

보호 범위는 이 기준 커밋의 모든 추적 파일이며 references/v27-baseline.json에 작업 트리 SHA256을 고정했다. 새 부가 파일과 설치 후의 가변 run 기록은 보호된 원본과 구분한다.
