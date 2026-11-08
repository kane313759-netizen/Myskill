---
name: hackathon-orchestrator-universal
description: Add environment and deadline planning, bounded data audit, reproducible submission checks, local snapshots and nondeveloper study to the existing SK hynix finals workflow. Use for the requested v2.7 add-on; preserve the installed baseline roles, real review execution and official stage rules.
---

Read the installed `references/v27-contract.md`, `references/v27-r81-map.md` and
FINALS_POLICY.md first (root policy and references in a source checkout). This is
an additive entry point over `hackathon-finals`, not a replacement of its six core
REDs or conditional SECURITY_RED. Latest official task rules take priority. Keep
the existing writer/reviewer ownership and actual worker lifecycle receipts.
Do not apply second-preliminary limits/models/6-question rules as confirmed finals
facts. The add-on's strict defaults are temporary planning restrictions only.

Follow the baseline finals workflow. In one intake pass capture original sources,
environment switches/model availability, required output and evaluation; use the
provided v27 templates and V27_EVIDENCE.json. CP1, first end-to-end CP2 and final
CP3 remain the three logical review checkpoints. M1/M2/M3 are scheduling milestones,
not new review checkpoints. Reuse the existing FINAL plan and execution receipts
unchanged in both final checkers. CP3 is the logical phase, not a new receipt label.

The agent performs engineering and runs the scripts with the actual Python
executable and `-I`; the participant does not need to memorize commands. Inspect
side effects first. The scripts are bounded local helpers, not OS/network isolation.
Only approved original task dependencies are used. No remote backup, other-account
AI transfer or automatic UI action follows from this skill.

Ask the participant only source-unanswerable business/risk/time preferences,
official permission or unavailable human-only steps. Explain technical selections
proactively with actual tool/algorithm, rationale, alternative, case and limits.
AI decisions are labeled AI; actual participant choices alone are human judgment.
Use concise type-B explanations without routine approval loops. The default final
study reserve is 60 minutes; reducing it requires an actual participant choice.
Plan three short learning blocks (10/5/10 minutes) around actual progress, not
invented fixed official times. Unconfirmed follow-up stays unconfirmed; prepare
six evidence-based practice outlines only if applicable, never predict questions.
Start from BOOTSTRAP_V27.md. Deliver briefings in natural spoken Korean the
participant can read aloud: two or three short lines plus one numeric line when
actual measurements exist. Use its short fallback only when the kit is unavailable.

Before metrics drive decisions, use DATA_EVAL_RED to inspect audit applicability,
independent positive/negative grader controls and untouched final evaluation.
Any adaptive use of a holdout makes it tuning evidence, even before four looks.
Do not demand numeric scores or all ten semantic audit conclusions when evidence
is unavailable. Record UNAVAILABLE_WITH_REASON/UNVERIFIED; N/A needs prerequisites.

Use `deadline.py` for explicit timezone-aware official cutoffs and planning values;
missing inputs produce UNKNOWN. The template's 16:00 cutoff is an explicit planning
default, not a confirmed submission deadline. With no explicit C, reserve repair
buffer plus all sequential review slots (90 minutes by default), or one batch only
when parallel review is actually available. Read c_basis, passed milestones and
lunch warnings; replan explicitly without silently moving deadlines. Use `snapshot.py`
on explicit product/config/output/run paths at checkpoints/milestones. Declared
raw inputs are hash-only. Named M1/final plus recent snapshots are local recovery,
not resilience to loss of the workspace or exclusion from whole-folder collection.
Pause during lunch unless the official rule permits continued isolated work.

Near final collection, use the task-specific `submit_check.py`, authorized isolated
`clean_run.py`, scoped static `security_check.py`, actual triggered security review
and baseline six-role evidence. Run `v27_check.py --phase final` against retained
current executions and records; it is read-only and does not close/change baseline
gates. Do not refresh a reviewed hash without real affected recheck. Missing review
is NOT_RUN; degraded operation is disclosed and never a CLOSED gate or permission
to waive an official rule. Reserve repair/submission time before studying/freezing.
Use ENV EXECUTION_TOOLS for the current platform's retained native tool names.
Unknown tools and MANUAL_TRANSCRIPT remain UNVERIFIED; they cannot establish PASS.
After final collection preparation and all evidence checks, preview then apply
`snapshot.py purge --root <task> --apply` before the original
`kit_lifecycle.py clean --kit <task>/.hackathon-kit --apply`. Purge removes the local
snapshots permanently. It refuses all deletion if any foreign/linked content exists.
Check the exact collected files after cleanup, including any retained notes backup.

Shrink optional search/ensembles/sweeps/pitch decoration first. Do not remove
required review, feasibility, data-transfer safeguards, relevant safety or final
collection checks. An invalid input may stop with an explicit error if no verified
safe fallback exists; never fabricate a valid decision to keep the process alive.
After actual freeze no product edits. Human submission completion needs observed
receipt, not a prepared file or a helper PASS. Refresh delivered explanations when
pre-freeze fixes change the actual method/result; do not certify human comprehension.

## r2 시험 결과 반영

- 기술 선택은 AI가 Type B로 직접 결정하고 쉬운 말로 이유·대안·한계를 설명한다. 가상 또는 실제 비개발자에게 기술 A/B 선택이나 승인을 요구하지 않는다. 업무 위험 수용 등 실제 사람만 결정할 사안은 Type A로 남긴다.
- 비교 가능한 현행 기준선이 있으면 같은 지표·방향·데이터·제약에서 후보와 비교한다. 후보가 더 나쁘면 제출 후보로 선택하지 않고 현행 기준선을 보존한다. 수치 비교가 불가능하면 이유와 `UNAVAILABLE_WITH_REASON`을 남기고 개선이나 최종 검증 완료를 주장하지 않는다.
- `현행 유지`는 자동 기본 답이 아니다. 서로 다른 두 대안을 실제로 검토하고 결과·근거와 현행 방식의 가정을 점검한다. 점수만 높아도 안전·하드 제약은 별도 충족해야 한다.
- 진행자에게 보낸 필수 요청의 회신이 대기 중이면 독립 작업은 계속하되 결과를 최종 잠금으로 표시하지 않는다. 기한이 임박해도 회신을 지어내거나 미응답을 수신으로 바꾸지 않는다.
- 최종 전 최소 두 가지 서로 다른 설정 변경을 실제 재실행하고 입력·명령·결과와 검증을 남긴다. 적용할 설정이 없거나 실행이 불가능하면 이유를 남기고 UNVERIFIED다. 원본이나 최종 후보를 변경하지 않는 격리 사본에서 실행한다.
- `data_audit.py`는 명시 파일의 모든 행을 예산 안에서 조사하고 `.csv.gz`, 인접 구간 중앙값의 스케일 계단, 같은 행의 시작/종료 시각 역행 후보를 보고한다. 예산 초과·부분 스캔·해독 불가는 완전 검사로 취급하지 않는다. 탐지는 단위 변경이나 인과관계의 확정이 아니다.
