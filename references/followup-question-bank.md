# Follow-up question bank

The official brief confirms **6 written questions × 5 minutes** without AI/copy-paste. Exact questions are unknown.
This bank is preparation coverage, not leaked/official questions.

## 20 question families

| # | Family | Example wording | Evidence to prepare |
|---|---|---|---|
| 1 | Problem | 무엇을 해결했나? 누구를 위한 것인가? | problem-intake / SPEC |
| 2 | Success | 성공했다고 판단한 기준은? | GRADER / tests |
| 3 | Requirements | 핵심 요구사항은? | task evidence |
| 4 | Constraints | 가장 중요한 제약은? | CONSTRAINTS |
| 5 | Edge case | 가장 까다로운 edge/boundary는? | EDGE_CASES / VERIFY |
| 6 | Implicit risk | 명시되지 않았지만 고려한 위험은? | assumptions / Constraint Red |
| 7 | AI miss | AI가 처음 놓친 것은? | actual missed proposal/event and AI_FAILURES |
| 8 | AI could not solve | AI가 해결 못한 문제를 어떻게 처리했나? | real failure only |
| 9 | Human contribution | AI 외에 본인이 한 것은? | sourced participant event in HUMAN_JUDGMENT |
| 10 | AI usage | AI를 어떻게 활용했나? | DECISIONS / model roles |
| 11 | Model choice | 왜 Sol/Terra/Luna를 사용했나? | actual runtime/model record |
| 12 | Prompt strategy | 어떤 지시/전략이 중요했나? | workflow decisions |
| 13 | System flow | 입력이 어떻게 결과가 되나? | SYSTEM_MAP |
| 14 | Boundary | 시스템 경계는 어디인가? | SYSTEM_MAP |
| 15 | Storage | 무엇이 어디 저장되고 재시작 후 남나? | SYSTEM_MAP / code |
| 16 | Technology | 실제 사용한 기술/도구를 왜 골랐나? | task requirement / actual code path |
| 17 | Verification | 정확성을 어떻게 검증했나? | BASELINE / VERIFY |
| 18 | Debugging | 가장 어려운 오류와 원인은? | real debug evidence |
| 19 | Trade-off | 다른 방법 대신 왜 이 방법인가? | DECISIONS |
| 20 | Limitations | 한계/미확인/추가 시간이 있다면? | LIMITATIONS |

## Six-axis coverage

A. 무엇을 만들었나?
B. 왜 그렇게 만들었나?
C. AI를 어떻게 썼나?
D. 내가 직접 무엇을 판단했나?
E. 어떻게 맞다고 확인했나?
F. 어디까지 되고 무엇이 한계인가?

Build these factual axes at CP2 rather than discovering all missing evidence at submission time. Recorder updates the sheet from material event handoffs and refreshes changed facts at CP3. Link original sources and preserve UNKNOWN / UNVERIFIED / UNANSWERABLE FROM CURRENT RECORDS when evidence is missing.

At CP3 `followup-prep` selects six task-specific hard families once and is the sole quiz owner. Prepare all six concise answer outlines. Rehearsal can be brief and adaptive within the remaining task time; it is not a mandatory 30-minute simulation. Stop before the submission boundary and before the official no-AI phase.

## Answer skeleton

**Problem → AI action → Human judgment → Verification → Result / limitation**

Do not force all five parts when the question does not need them.

## Truth handling

### Edge case
A difficult edge case does not need to have caused a bug.
A prevented boundary case with a real test/check is valid.

### AI failure
Never manufacture one. Distinguish no recorded failure, a failed attempt later resolved, and a still-unresolved failure. Explain the actual status and evidence. If the requested event is absent from the records, say so; another human-judgment example is usable only when it really occurred and is relevant to the question. Empty AI_FAILURES and HUMAN_JUDGMENT records are valid.

### Human contribution
Good evidence includes:
- challenging an assumption
- asking a material business question
- selecting between alternatives
- noticing a pathological result
- manually verifying something automation could not verify
- deciding what remained an assumption instead of inventing a rule

AI-only work must not be presented as participant contribution.
Retain the time/event reference and original participant statement or action. A Tutor question or acknowledgement does not establish that the participant challenged a design, selected an implementation, or performed a manual check. Direct checks require the participant's explicit account of what they checked and the result; automated checks must be identified separately.
