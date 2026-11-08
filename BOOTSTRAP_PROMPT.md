# 시작 프롬프트 — 본선 / 2차 예선

## 본선 또는 본선 연습

비개발자도 다음 한 문장으로 시작합니다. 과제와 공식 안내 파일이 있으면 함께 지정합니다.

```text
Use the hackathon-finals skill. Read .hackathon-kit/FINALS_POLICY.md first.
나는 비개발자입니다. 제공된 공식 과제와 안내를 읽고, 기술 선택부터 구현·실행·검증·설명·제출 준비까지 진행해 주세요. 공식 권한이나 중요한 업무 판단이 필요한 경우에만 질문하고, 나머지 기술 선택은 근거에 따라 처리해 주세요. 예선의 시간·6문항·모델·제출 규칙을 본선에 자동 적용하지 마세요.
```

사전 연습이면 합성 자료임을 표시하고 실제 대회 검증과 구분합니다. 본선의
도구·사전 파일 사용 허용 여부는 현장 공식 안내를 확인해야 합니다.

## 2차 예선 전용

Codex 첫 메시지로 사용:

```text
Use the hackathon-orchestrator skill.
Read .hackathon-kit/EXAM_POLICY.md first. Newer official exam/task instructions win.
Follow the orchestrator skill as the canonical checkpoint and ownership protocol.

If installation used an internal temporary kit source, verify the installation and
remove only the unique source directory we created, after checking for unexpected
content or local changes. Never delete preexisting/task files. The manifest tracks
these sources; resolve doctor warnings before intake and never hide a leftover source.

Keep Terra as ORCHESTRATOR only. It owns STATE, gate, checkpoint reports and review receipts.
Create one persistent Sol 6.1 MAIN when actually available; only MAIN edits product source.
Use clean Code Red / Constraint Red contexts with no inherited history:
fork_turns="none" where supported, otherwise a clean separate session.
Give reviewers EXAM_POLICY and original evidence first; MAIN notes are claims to verify.
Recorder is the sole ongoing evidence-note writer. Tutor, if used, is strictly read-only.
Verify actual available models; preserve roles with allowed substitutes, never claim a switch without evidence.

Phase 0 is one evidence pass: grader-intake → immutable-inventory → task-router →
problem-intake → constraint-discovery. Batch GRADER, BASELINE, IMMUTABLES,
CONSTRAINTS and SPEC_DRAFT using their installed template headings. Run gate_check.py --preflight
before Red review; it checks format only and never authorizes implementation.
Inspect command side effects/network/time before baseline.
Use references/local-evaluation.md for small useful pre-edit-to-final local checks;
freeze rubric/checker hashes and scope, keep proxy counts separate from visible scores.
Record original source paths or provenance-marked TASK_EVIDENCE for UI/chat-only originals.
Use original task tools, kit helpers and standard library; optional additions are NONE.
No automatic catalog/PATH search, optional helper trial or installation, even if installed.
Preserve permitted task-required setup; record sources/setup/guards/fallback/budget in
the existing SPEC verification plan for CP1. Required unavailable work stays blocked/partial.

Before implementation, independent CP1 Constraint Red must review the actual specification.
ORCHESTRATOR records CP1_RED.md and CP1_REVIEW.json with original sources,
actual reviewer/context, exact reviewed artifact hashes, findings and attempted attacks.
Resolve/disprove P0/P1 with evidence and recheck, then set the canonical STATE flags.
Run gate_check.py. Product implementation begins only after this check passes.
Freeze the five reviewed documents. Routine results go in VERIFY.
Material contract changes reopen the gate and need targeted clean review before continuing.

CP2: first scoring-relevant end-to-end path → clean Code Red → Recorder.
Add Constraint Red only when material task/constraint/objective risk warrants it.
Start factual six-axis follow-up coverage and FOLLOWUP_CHEATSHEET.md here.
Capture actual material human questions/choices/checks and failed-attempt evidence as they occur;
never manufacture human contributions or AI failures. Ask only material questions.

CP3: budget backwards from the real submission deadline; start earlier when needed.
Stop feature expansion → final clean Code Red and Constraint Red → fix/recheck blockers →
verification → Recorder → factual final-explain → followup-prep once → doctor.
Prepare six evidence-backed question/answer outlines; short rehearsal must preserve submission time.
ORCHESTRATOR records CP3 review/verification/followup completion in STATE.
Cleanup is last, after explanation/practice, only if submission collection requires helper removal.

Computer Use / automated UI control, external AI connections,
external transmission of problem/files/results, and Git Push are prohibited in the exam.
Public tools/Skills/MCP/Plugins may be downloaded only within those restrictions;
external code may be partially reused but must not replace the submission wholesale.
Use Cofa Helper for exam UI/submission questions; participant handles UI actions.
The official follow-up is 6 questions × 5 minutes without AI or copy/paste.
```
