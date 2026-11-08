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
only at the first E2E (M1) and final, on explicit product/config/output/run paths. Do not run snapshot.py at other checkpoints. Declared
raw inputs are hash-only. Named M1/final snapshots are local recovery,
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

- 과제 사이 정보 교환 금지는 과제 사이에만 적용한다. 같은 과제 안에서 실제 작업자로 리뷰를 띄우는 것은 필수 절차다. CP1·CP2 리뷰는 제출 잠금 전에 실행하고, P0/P1은 잠금 전에 고친다. NOT_RUN은 도구 부재·사용 금지·호출 실패·시간 부족 중 실제 사유와 그 증거를 남길 때만 쓴다.
- 리뷰 의뢰문에는 다음을 덧붙인다. 해석 쟁점은 판결 대신 두 열로 낸다: (가) 글자 그대로의 제약, (나) 스키마·숫자가 허용하는 제약, 각 제약이 나온 문장과 그 제약에서의 지표 값. 알고리즘 리뷰는 현재 최선안을 이길 수 있는 반례나 비교 실험 하나를 제시한다. 목표 미달만으로 P1을 매기지 않는다.

- 기술 선택은 AI가 Type B로 직접 결정하고 쉬운 말로 이유·대안·한계를 설명한다. 가상 또는 실제 비개발자에게 기술 A/B 선택이나 승인을 요구하지 않는다. 업무 위험 수용 등 실제 사람만 결정할 사안은 Type A로 남긴다.
- 안전·보안과 과제에 적힌 제약·제출 계약은 넓히지 않는다. 템플릿·스키마의 계약(함수 인자, 반환 형식, 단위 표기)이 산문과 충돌하면 계약을 따른다. 누수와 시간 순서 위반은 어떤 해석으로도 허용하지 않는다.
- 데이터 감사가 찾은 기록 문제(단위·스케일 계단, 시간대 혼재, 중복, 코드 정의 변경)는 제약이 아니라 데이터 오류 후보다. 문서에 적힌 단위·형식으로 맞추는 것이 무결성이다. 오류인지 확정할 수 없으면 "보정" 해석과 "그대로" 해석을 같은 자체 검증(시간순 분할)으로 비교해 점수가 나은 쪽을 쓰고, 두 값과 근거를 기록한다. 원본은 보존한다.
- 그 밖의 산문이 모호해 결과가 달라지면 두 해석의 지표 값을 함께 계산해 남기고, 업무 담당자나 주최 측에 묻는다. 답을 받기 전에는 두 해석 모두에서 허용되는 제출안을 확보한다.
- 후보의 채택·기각은 과제에 적힌 평가 지표와 한도로 한다. 평가 지표를 직접 계산할 수 없으면 쓰는 대리 지표와 그 근거·불확실성을 밝히고, 과제에 없는 절대 탈락 조건(대리 지표가 1건이라도 늘면 탈락 등)은 만들지 않는다. 불량 판정과 허용 한도는 과제 정의를 따르며, 대리 라벨의 심각도 구분은 보조 분석에만 쓴다.
- 진행자 회신 대기 중에는 독립 작업을 계속하고, 검증된 제출물·과제 원문의 hard_limits 및 deadline_fallback 근거가 없다면 최종 잠금을 표시하지 않는다. 회신을 지어내거나 미응답을 수신으로 바꾸지 않는다.
- 최종 전 최소 두 가지 서로 다른 설정 변경을 실제 재실행하고 입력·명령·결과와 검증을 남긴다. 적용할 설정이 없거나 실행이 불가능하면 이유를 남기고 UNVERIFIED다. 원본이나 최종 후보를 변경하지 않는 격리 사본에서 실행한다.
- `data_audit.py`는 명시 파일의 모든 행을 예산 안에서 조사하고 `.csv.gz`, 인접 구간 중앙값의 스케일 계단, 같은 행의 시작/종료 시각 역행 후보를 보고한다. 바이트·시간·줄 길이 초과나 해독 실패로 모든 행을 읽지 못하면 완전 스캔이 아니다. 분석별 그룹·표본 한계는 행 읽기 완료와 분리해 경고한다. 탐지는 단위 변경이나 인과관계의 확정이 아니다.

FINDING은 실제 지표 전후와 평가기 해시 또는 측정 불가 사유를 기록한다. hard_limits는 반드시 지키고 proxy_metrics는 비교해 기록하며 현행 유지 시 서로 다른 세 가지 명시된 가정을 점검한다. 자세한 r3 계약은 references/v27-contract.md를 따른다.

- 이 키트에서 "보수적인 가정"은 되돌릴 수 있고 명시된 제약 안에 있다는 뜻이며, 현행 방식 유지를 뜻하지 않는다.
- 키트가 요구하는 기록 외에 별도 영수증·요약·중간 보고 파일을 만들지 않는다. 후보 비교는 run/CANDIDATES.md 한 파일만 갱신한다(후보·평가 조건·지표·채택/기각 이유). 안전·보안 기록과 재실행 명령·설정·최종 결과는 줄이지 않는다.

- 과제에 없는 제한(후보 걸러내기, "모든 경우 비악화" 조건, 변화량·속도 상한, 추가 안전 여유)을 해법에 넣으면, 그 제한을 뺀 후보의 과제 지표 값을 CANDIDATES.md에 함께 남긴다. 사람에게 위험 선택을 물을 때는 "비악화" 같은 관문을 선택지로 만들지 않고 기대값과 최악 손실을 숫자로 보여 준다.
- 자체 평가기는 과제의 평가 조건(측정 밀도·범위·기간·시나리오)을 흉내 내고, 과거 기록으로 한 번 대조한다. 후보 사이 점수 차이가 거의 없으면 평가기가 조건을 담지 못한다는 신호로 보고 시나리오를 보강한다. 리뷰·감사·분석에서 계산한 관계(환산식, 분포 꼬리, 방향성)는 그것을 반영한 후보를 실제로 비교하고, 버리면 수치 근거를 남긴다.
- 대리 라벨로 과제 한도를 판정하기 전에, 대리 라벨이 실제 결과(반품·재검사·추가 측정 등)와 얼마나 맞는지 확인할 수 있으면 확인한다. 확인할 수 없으면 대리 라벨의 상한은 탈락 기준이 아니라 위험 경고로 쓰고, 과대·과소 추정 방향을 적는다.
- 산출물이 시스템·에이전트·정책이면 먼저 실제 입력 하나가 검증·처리·결과 저장까지 통과하는 최소 기능과, 상태·행동·예산·중지 조건을 가진 최소 시뮬레이터(무조치·고정 조치 대비 숫자)를 만든다. 그다음 입력 변경·오류 입력·재실행을 확인하고, 화면·API는 과제가 요구할 때만 붙인다. 각 결정은 그 시점까지 도착한 정보만 쓴다.
- `현행 유지`는 자동 기본 답이 아니다. 현행을 제출하면 best_alternative(가장 나은 대안의 지표와 기각 근거)를 남긴다.
- 작업자 자리가 모자라면 Recorder 역할은 MAIN이 겸하고 그 사실을 기록한다.
