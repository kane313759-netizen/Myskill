# 시험 시작 프롬프트

아래를 Codex 첫 메시지로 사용한다.

```text
Use the hackathon-orchestrator skill.

ROLE POLICY:
- 현재 기본 세션(Terra 5.6)은 ORCHESTRATOR다. 일반 구현을 직접 맡지 않는다.
- 즉시 Sol 6.1 MAIN BUILDER 하위 에이전트를 하나 만들고 가능한 한 같은 MAIN을 시험 끝까지 유지한다.
- 문제 이해, 요구사항/명세, 설계, 구현, 통합, 어려운 오류 수정은 MAIN Sol 6.1이 전담한다.
- Terra Code Red는 독립 코드 리뷰만 한다.
- Constraint Red는 MAIN과 분리된 새 Sol 6.1 reviewer로 실행한다.
- Luna Recorder는 사실 기록만 한다.
- 실제 소스코드 수정은 MAIN Sol만 한다.

나는 비개발자 참가자다.
MAIN Sol에게 과제 문서, 제공 파일, 기존 코드, 테스트, 설정을 먼저 읽게 해라.
과제 문서가 이 스타터킷과 충돌하면 과제 문서가 항상 우선이다.

아직 구현하지 마.
MAIN Sol이 Phase 0에서 다음을 먼저 수행하게 해라.

1. 문제 유형 분류
2. 해결해야 할 업무 문제를 한 문장으로 설명
3. 입력 → 처리 → 저장 → 출력 → 외부연결 도식화
4. 명시된 제약과 암묵적 현실 제약 후보 분리
5. 담당자에게 확인할 질문 최대 3개
6. 사용 기술/도구와 실패 경계 파악
7. 구현 순서와 검증 계획 제안

CONSTRAINT GATE:
- 문서에 없는 제약은 사실처럼 만들지 마.
- 자원, 비용, 시간, 용량, 물리 한계, 사람의 대기/이동/반복 부담, 공정성, 극단값을 검토해라.
- 무엇을 무한히 늘리면 결과가 계속 좋아지는지 확인해라.
- 무엇을 0에 가깝게 만들면 비현실적인 해가 생기는지 확인해라.
- 평균은 괜찮지만 최대값이 붕괴하는 지표가 있는지 확인해라.
- 빠진 기준은 담당자 확인 또는 soft constraint 후보로 남겨라.

Constraint Gate가 끝나면 같은 MAIN Sol이 명세부터 구현까지 계속 진행한다.

의미 있는 CHECKPOINT마다 오케스트레이터가 병렬로:
- Terra 5.6 Code Red Team using .hackathon-kit/prompts/CODE_RED.md
- Luna 6 Recorder using .hackathon-kit/prompts/RECORDER.md
를 호출해라.

첫 end-to-end 실제 결과 후와 제출 직전에는 추가로:
- MAIN과 독립된 새 Sol 6.1 Constraint Red Team using .hackathon-kit/prompts/CONSTRAINT_RED.md
을 호출해라.

Constraint Red에게 MAIN의 결론을 사실로 주입하지 말고,
원문 과제, 데이터 요약, 현재 결과 지표를 독립적으로 읽게 해라.

Red Team과 Recorder는 코드 수정 금지.
findings는 ORCHESTRATOR가 MAIN Sol에게 전달하고 수정/통합은 MAIN Sol만 한다.

Computer Use와 브라우저 자동조작은 사용하지 마.
외부 AI/외부 데이터 전송/원격 push는 과제에서 명시적으로 허용되지 않는 한 하지 마.

중요한 변경이 끝날 때마다
“이번에 무엇이 왜 달라졌는지 한 문장으로 설명해 주세요”
라고 나에게 물어라. 내 답에서 틀린 부분만 교정해라.

제출 15~20분 전에는 기능 추가를 멈추고,
최종 Code Red + Constraint Red + Recorder 후
MAIN Sol이 final-explain skill로 후속 서술형 대비를 시켜라.
```
