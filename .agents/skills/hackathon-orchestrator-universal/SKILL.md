---
name: hackathon-orchestrator-universal
description: Start here for any SK hynix AI hackathon finals or finals-practice task, including short requests such as myskill 설치해서 작업 시작 or 본선 과제 시작. It runs the hackathon-finals workflow and adds environment and deadline planning, bounded data audit, limit and ambiguity rules, reproducible submission checks, local snapshots and nondeveloper study. When both are installed, use this instead of starting hackathon-finals directly.
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
- 주최 측·업무 담당자의 답이 끝내 없거나 "안내문대로"라는 답이면, 다른 해석에서 실격·hard_limit 위반이 생길 때만 두 해석 공통안을 제출한다. 그 밖에는 과제 목표·표 비고·예시와 맞는 해석의 최선안을 제출하고, 다른 해석에서의 지표를 보고서 한계 절에 적는다.
- 반려·0점·실격이 걸린 조건(예: 특정 상태의 값이 들어가면 보고 전체를 반려한다는 규정)이 어느 칸·결과까지 닿는지 문서끼리 갈리거나 불분명하면, 출처나 집계 경로가 다르다는 이유만으로 해당 없음으로 정하지 않는다. 닿을 수 있는 칸은 그 조건을 피하는 공통안(문서가 정한 표기·보류)으로 내고 계산한 값은 내부 기록에 남긴다. 적힌 배점으로 따져 공통안의 손실이 그 조건에 걸릴 때의 손실보다 클 때만 예외로 하고, 그 계산을 보고서에 적는다.
- 후보의 채택·기각은 과제에 적힌 평가 지표와 한도로 한다. 평가 지표를 직접 계산할 수 없으면 쓰는 대리 지표와 그 근거·불확실성을 밝히고, 과제에 없는 절대 탈락 조건(대리 지표가 1건이라도 늘면 탈락 등)은 만들지 않는다. 불량 판정과 허용 한도는 과제 정의를 따르며, 대리 라벨의 심각도 구분은 보조 분석에만 쓴다.
- 진행자 회신 대기 중에는 독립 작업을 계속하고, 검증된 제출물·과제 원문의 hard_limits 및 deadline_fallback 근거가 없다면 최종 잠금을 표시하지 않는다. 회신을 지어내거나 미응답을 수신으로 바꾸지 않는다.
- 최종 전 최소 두 가지 서로 다른 설정 변경을 실제 재실행하고 입력·명령·결과와 검증을 남긴다. 적용할 설정이 없거나 실행이 불가능하면 이유를 남기고 UNVERIFIED다. 원본이나 최종 후보를 변경하지 않는 격리 사본에서 실행한다.
- `data_audit.py`는 명시 파일의 모든 행을 예산 안에서 조사하고 `.csv.gz`, 인접 구간 중앙값의 스케일 계단, 같은 행의 시작/종료 시각 역행 후보를 보고한다. 바이트·시간·줄 길이 초과나 해독 실패로 모든 행을 읽지 못하면 완전 스캔이 아니다. 분석별 그룹·표본 한계는 행 읽기 완료와 분리해 경고한다. 탐지는 단위 변경이나 인과관계의 확정이 아니다.

FINDING은 실제 지표 전후와 평가기 해시 또는 측정 불가 사유를 기록한다. hard_limits는 반드시 지키고 proxy_metrics는 비교해 기록하며 현행 유지 시 서로 다른 세 가지 명시된 가정을 점검한다. 자세한 r3 계약은 references/v27-contract.md를 따른다.

- 이 키트에서 "보수적인 가정"은 되돌릴 수 있고 명시된 제약 안에 있다는 뜻이며, 현행 방식 유지를 뜻하지 않는다.
- 키트가 요구하는 기록 외에 별도 영수증·요약·중간 보고 파일을 만들지 않는다. 후보 비교는 run/CANDIDATES.md 한 파일만 갱신한다(후보·평가 조건·지표·채택/기각 이유). 안전·보안 기록과 재실행 명령·설정·최종 결과는 줄이지 않는다.

- 과제에 없는 제한(후보 걸러내기, "모든 경우 비악화" 조건, 변화량·속도 상한, 측정한 추정 오차에 근거하지 않은 추가 여유)을 해법에 넣으면, 그 제한을 뺀 후보의 과제 지표 값을 CANDIDATES.md에 함께 남긴다. 사람에게 위험 선택을 물을 때는 "비악화" 같은 관문을 선택지로 만들지 않고 기대값과 최악 손실을 숫자로 보여 준다.
- 자체 평가기는 과제의 평가 조건(측정 밀도·범위·기간·시나리오)을 흉내 내고, 과거 기록으로 한 번 대조한다. 후보 사이 점수 차이가 거의 없으면 평가기가 조건을 담지 못한다는 신호로 보고 시나리오를 보강한다. 리뷰·감사·분석에서 계산한 관계(환산식, 분포 꼬리, 방향성)는 그것을 반영한 후보를 실제로 비교하고, 버리면 수치 근거를 남긴다.
- 대리 라벨로 과제 한도를 판정하기 전에, 대리 라벨이 실제 결과(반품·재검사·추가 측정 등)와 얼마나 맞는지 확인할 수 있으면 확인한다. 확인할 수 없으면 대리 라벨의 상한은 탈락 기준이 아니라 위험 경고로 쓰고, 과대·과소 추정 방향을 적는다.
- 산출물이 시스템·에이전트·정책이면 먼저 실제 입력 하나가 검증·처리·결과 저장까지 통과하는 최소 기능과, 상태·행동·예산·중지 조건을 가진 최소 시뮬레이터(무조치·고정 조치 대비 숫자)를 만든다. 그다음 입력 변경·오류 입력·재실행을 확인하고, 화면·API는 과제가 요구할 때만 붙인다. 각 결정은 그 시점까지 도착한 정보만 쓴다.
- 입력 묶음 안의 깨진 기록이나 예상과 다른 형식(공개 샘플과 다른 칸 형식 포함)은 그 기록만 격리하고 사유를 남긴 뒤 나머지를 처리한다. 묶음 전체 거부는 과제 문서가 정한 거부 조건(필수 파일·필수 목록 없음 등)일 때만 쓴다. 문서에 정의되지 않은 칸 하나에 처리 전체를 걸지 않고, 깨진 행 하나와 형식이 다른 칸 하나를 넣은 묶음으로 끝까지 도는지 자체 시험한다.
- `현행 유지`는 자동 기본 답이 아니다. 현행을 제출하면 best_alternative(가장 나은 대안의 지표와 기각 근거)를 남긴다.
- 작업자 자리가 모자라면 Recorder 역할은 MAIN이 겸하고 그 사실을 기록한다.
- 과제 한도(불량률·이탈률 등)를 추정값으로 판정할 때는 그 추정기를 실제 결과(반품·재검사·파괴 분석·시간 분할 구간)와 대조해 편향과 오차 폭을 잰다. 기대 과제 점수는 과제에 적힌 감점 규칙에만 쓰고 감점 공식을 지어내지 않는다. 넘으면 탈락·실격하는 한도나 감점 규칙이 적히지 않은 한도는 잰 오차의 위쪽 끝(단측 95%)이 한도 안에 드는 운영점 가운데 과제 지표가 가장 좋은 것을 고른다. 이렇게 잰 오차에서 나온 여유는 자작 제한이 아니다. 검증하지 않은 추정값을 한도에 딱 맞추지 않으며, 모형 불확실성은 정보 없는 모형과 섞어 감추지 말고 오차 폭으로 나타낸다.
- 위 단측 95% 위쪽 끝은 잰 오차의 분포에서 구한다. 대상은 실제 결과와 대조한 (실제 − 추정) 오차, 또는 추정기가 항목마다 표준오차를 내면 표준화 오차 z = (실제 − 추정) ÷ 표준오차다. 여기서 표준오차는 그 항목 하나의 예측 표준오차이며, 평균의 표준오차(표준편차 ÷ √표본 수)가 아니다. 정규분포를 가정하지 않는다: 표본이 20개 이상이면 경험적 95% 분위수(작은 값부터 정렬해 올림(0.95 × 표본 수)번째 값)와 오차 평균 + 1.645 × 오차 표준편차를 둘 다 계산해 큰 쪽을 쓰고 두 값을 기록한다. 표본이 20개 미만이면 경험적 분위수가 최댓값과 같아지므로 쓰지 않고, 오차 평균 + t(0.95, 표본 수 − 1) × 오차 표준편차 × √(1 + 1 ÷ 표본 수)를 쓰며 정규 근사라는 한계를 적는다(t값은 references/v27-contract.md 표). 1.645는 정규분포일 때만 95%이므로 단독으로 쓰지 않는다. z를 쓰면 고른 값에 그 항목의 표준오차를 곱해 추정에 더한다. 이력의 최대 오차(최악 사례)는 표본이 늘수록 커지기만 하므로 여유로 쓰지 않고, 쓰려면 그 운영점의 과제 지표를 CANDIDATES.md에 함께 남긴다.
- 대조할 실제 결과가 없거나 추정기가 실제 사례 대부분을 잡지 못하면 그 추정값으로 "한도 안"이라 판정하지 않는다. 실제 사례를 설명하는 다른 신호(이상치·이웃·공간·이력)를 먼저 찾고, 못 찾으면 한도에서 떨어진 운영점 2~3개의 과제 지표를 CANDIDATES.md에 남긴 뒤 덜 공격적인 쪽을 고르고 포기한 지표 차이를 적는다. 이 줄은 대리 라벨 줄보다 우선하며, 이때의 여유는 자작 제한으로 세지 않는다.
- 정비·교체·세정·부품 교체 같은 이벤트는 종류별로 효과(직후 일시 구간 포함)를 따로 추정하고, 기록이 빠진 이벤트는 센서·결과의 계단으로 찾아 넣은 후보와 뺀 후보를 같은 자체 검증으로 비교한다.
- 위 비교 규칙(데이터 오류 후보·자작 제한·계산한 관계·추정 한도·이벤트 종류)은 감사·첫 전체 실행에서 그 현상이 실제로 보일 때만 적용하고, 보이지 않으면 CANDIDATES.md에 "해당 없음(근거 한 줄)"으로 끝낸다. 후보 차이가 작을 때 시나리오 보강은 한 번만 하고, 그래도 비슷하면 단순한 후보를 고른다.
- 공식 규칙 문서·안내를 읽은 직후 당일 환경(쓸 수 있는 AI·하위 작업자 허용·점심 중 작업·제출 방식과 마감·후속 평가·피칭)을 문서에서 먼저 찾아 출처와 함께 적고, 문서에 없는 칸만 참가자에게 한 번에 묻는다. 그 값으로 ENV의 FOLLOWUP(후속 평가가 없으면 NONE)·LUNCH_POLICY·REVIEW_PARALLEL(하위 작업자가 허용되고 실제로 뜨면 YES)·T_SUB를 고쳐 deadline.py를 다시 돌리고, 답이 없는 칸만 계획값을 쓴다. 외부 전송·git push·computer use 금지는 공식 허용 전까지 바꾸지 않는다. 작업 잠금 시각과 학습 시간 S를 한 줄로 보여 주고 Type A(final_study_minutes)로 확인받으며, CP마다 `--observe-now`로 남은 일정을 다시 계산한다.
- 공식 연습 평가·추가 데이터·측정 요청 예산은 쓰라고 준 자원이다. 첫 완성안 뒤 한 번 쓰고, 앞 회신을 읽은 뒤 다음 요청을 설계하며, 나머지는 정보가 가장 큰 시점(변화·정비 직후, 불확실한 대상)에 쓴다. 남기면 이유를 적는다. 써서 고른 결과는 TUNING으로 기록할 뿐 사용을 피할 이유가 아니다.
- references/v27-contract.md의 r2 "전체 데이터 감사"·r3·r3.1 절은 감사 결과를 해석하거나 오류가 날 때만 읽는다. 맥락이 압축되거나 대화를 이어받으면 이 SKILL의 "## r2 시험 결과 반영" 아래를 다시 읽는다.
- 설치 폴더에 BOOTSTRAP_V27.md가 없으면(install.sh 설치 등) 받은 키트 폴더의 BOOTSTRAP_V27.md를 읽고, 가능하면 `scripts/install_v27.py`로 다시 설치한다.
- 직접 쓰는 스크립트의 파일 읽기·쓰기는 encoding='utf-8'을 명시한다(한국어 Windows 기본값은 cp949). 키트 도우미는 처음 쓰기 전에 `--help`로 인자를 확인한다.
- 자체 평가로 항·규칙을 넣고 뺄 때는 결론에 쓰는 구간(정비·교체 직후, 신제품, 드문 조건)별 표본 수를 함께 적는다. 표본이 적은 구간에서 "효과 없음"이 나왔다는 것만으로 그 구간의 항을 빼지 않는다. 그 구간 표본을 늘리거나, 물리적으로 있는 효과는 남긴 후보를 함께 제출 후보로 비교한다.
- 원인·자료 문제 목록(findings 등)에는 데이터 근거 수치가 있는 항목만 올린다. 근거가 약한 의심은 보고서의 "확인 필요"에 따로 적는다. 없는 문제를 원인으로 올리면 감점되는 평가가 많다.
- 설정값(한도·비용)이 바뀌는 시스템은 더 엄격한 설정에서 추정 오차를 다시 잰다. 그 설정 근처에서 실제 결과와 대조할 수 없으면, 한도에서 더 떨어진 운영점을 고르고 그 이유를 결정 기록에 남긴다.

- 반도체 공정·장비·품질 용어나 메커니즘이 필요할 때만 설치된 `references/semiconductor-domain-playbook.md`(1부)·`references/semiconductor-domain-playbook-2.md`(2부)에서 해당 절을 찾아 읽는다. 처음부터 전체를 읽지 않는다. 플레이북의 수치·사례는 가설의 출발점이며, 과제 데이터로 확인하기 전에는 사실이나 제약으로 쓰지 않는다.
- DATA_EVAL_RED·ALGORITHM_RED 의뢰문에는 설치된 `references/domain-review-questions.md`를 붙인다. 리뷰어는 해당 질문마다 확인함(근거)·해당 없음(이유)·미확인으로만 답하고, 미확인이면서 과제 지표에 영향이 클 때만 P1로 올린다.

## 역할별 모델·노력 (r4-3.12, 참가자 지정)

이 표가 `references/model-policy.md`의 선호 모델 표보다 우선한다(그 파일은 보호 원본이라 고치지 않는다). 역할 경계, 리뷰어의 깨끗한 맥락(`fork_turns="none"`), 실제 선택 기록 규칙은 그대로다.

| 역할 | 모델 | 노력 |
|---|---|---|
| ORCHESTRATOR (진행) | Sol 6.1 | high |
| MAIN_BUILDER (구현) | Sol 6.1 | Ultra |
| CODE_RED (코드 리뷰) | Sol 6.1 | high |
| CONSTRAINT_RED (제약 리뷰) | Sol 6.1 | Max |
| DATA_EVAL_RED (데이터·평가 리뷰) | Sol 6.1 | Max |
| ALGORITHM_RED (알고리즘 리뷰) | Sol 6.1 | Max |
| EDGE_RED (경계값·결측·예외 리뷰) | Sol 6.1 | high |
| SUBMISSION_RED (제출 형식 리뷰) | Sol 6.1 | high |
| SECURITY_RED (보안 리뷰, 조건부) | Sol 6.1 | high |
| RECORDER (기록) | Luna 6 | Max |
| TUTOR (설명, 선택) | Sol 6.1 | high |

- 당일 모델 화면·공식 안내에서 이 모델과 노력 단계를 쓸 수 있는지 확인한다. 쓸 수 있으면 그대로 쓰고, 시간을 아끼려고 낮추지 않는다. 없거나 공식 금지면 그 역할에 허용된 가장 강한 모델과 가장 높은 노력 단계를 쓴다.
- 실제 선택은 ENV에 적는다: 모델은 `assignments`(MODELS.AVAILABLE에 있는 이름), 노력은 `ACTUAL_EFFORT` 스위치. 확인하지 못한 값은 UNKNOWN으로 두고 바꿨다고 주장하지 않는다. 리뷰 영수증의 actual_model에도 실제 모델을 쓴다. 계획값은 ENV의 `MODEL_PLAN` 스위치에 있다.
- Max·Ultra는 한 번에 오래 걸린다. 하위 작업자가 허용되고 실제로 뜨면 REVIEW_PARALLEL=YES로 하고, 실제로 동시에 띄운 리뷰 작업자 수를 REVIEW_CONCURRENCY에 적는다. 마감은 올림((리뷰 수 − 1) ÷ 동시 수) + 1개 배치로 계산된다. 제출 형식 리뷰가 다른 리뷰의 수정 뒤에 따로 돌기 때문이며, 위 "one batch"는 이 계산으로 대체한다. 동시 수를 모르면 순차로 계산된다. 차례로 돌 때는 첫 리뷰에 걸린 실제 시간으로 REVIEW_MINUTES_EACH를 고치고 `deadline.py --observe-now`로 남은 일정을 다시 계산한다. 리뷰를 줄여 시간을 맞추지 않는다.

## 리뷰 범위 보강 (r4-3.12)

- CONSTRAINT_RED 의뢰문에 현장 실행 가능성 점검을 붙인다. 제안이 실제 장비 능력, 정비·교체 일정, 사람이 할 조치, 안전 절차, 주어진 시간 안에서 실행되는지 묻는다. 과제 문서나 담당자 답에 근거가 있으면 제약으로 기록한다. 근거 없는 "현실적으로 어려울 것 같다"는 제약으로 만들지 않고 담당자 질문·가정·보고서 한계로 남긴다(자작 제한 규칙과 함께 적용).
- CP1 기본 리뷰는 CONSTRAINT_RED·DATA_EVAL_RED 둘이다. 현행 최적값을 넘기거나 원인을 찾는 과제(최적화·탐색·원인 분석)면 CP1에 ALGORITHM_RED를 하나 더 띄워 계획만 본다: 정식화(목표·결정 변수·제약), 탐색 범위, 현행 기준선과 비교하는 방법, 확인 실험·추가 측정 설계. 코드와 결과 검토는 CP2에서 한다. 리뷰를 동시에 띄울 수 없고 시간이 빠듯하면 이 계획 검토만 생략하고 이유를 기록한다.

## 당일 운영 보강 (r4-3.13)

- V27_STATE의 `deadline`에는 `deadline.py` 출력을 그대로 넣는다. `--observe-now` 출력이어도 된다. 검사는 기록이 현재 ENV로 낼 수 있는 실제 출력과 완전히 같은지 보므로, 출력의 칸을 손으로 고치거나 빼지 않는다. ENV 값을 고치면 다시 계산해 다시 넣는다.
- 리뷰 시간은 일찍 잰다. CP1 리뷰가 끝나면 역할별 실제 소요 시간 가운데 가장 긴 값을 REVIEW_MINUTES_EACH에 적고(순차·병렬 모두) `deadline.py`를 다시 돌린다. CP2 리뷰가 더 오래 걸렸으면 그 값으로 다시 고친다. 최종 리뷰를 시작한 뒤에 처음 재면 늦다.
- `deadline.py`가 점심 겹침 경고를 내면 CP3 시작을 직접 다시 잡는다. 점심이 끝난 뒤부터 작업 잠금까지의 시간이 리뷰 예비(`review_reserve_minutes`)보다 짧으면 모자란 만큼 점심 시작 전으로 당긴다: CP3 시작 = 점심 시작 − (리뷰 예비 − 점심 뒤 남는 시간). 예: 잠금 14:15, 점심 12:00~13:00, 리뷰 예비 90분이면 점심 뒤 75분이 남아 15분이 모자라므로 11:45에 시작한다. 다시 잡은 시각과 계산은 run/FINALS_RUN.md에 한 줄로 적는다. 스크립트 출력의 `cp3_start`는 바꾸지 않는다.
- CP1에 계획 검토용 ALGORITHM_RED를 띄웠으면 `cp1_reviews` 기록에 같은 영수증 형식으로 ALGORITHM_RED 항목을 더한다. 별도 파일을 만들지 않는다. CP1 검사는 CONSTRAINT_RED·DATA_EVAL_RED 두 역할만 필수로 본다.
- CP1은 "무엇을 만들고 어떻게 채점되는가"를 확정하는 관문이다. 뒤 단계에서 뚫린 문제는 대부분 여기서 잘못 읽은 것이므로, CP1 리뷰 전에 SPEC_DRAFT에 아래 아홉 항목을 모두 적는다. 해당이 없으면 "없음(근거 한 줄)"으로 적고 비워 두지 않는다.
  1. 제출물 목록과 파일 이름·형식·필수 칸
  2. 채점 지표와 배점, 0점·반려·탈락 조건과 그 조건이 닿는 칸, 그리고 그 조건에 쓰인 용어마다 가리킬 수 있는 자료 칸·정의 목록
  3. 지켜야 할 한도와, 추정으로 판정할 때 여유를 정하는 방법
  4. 입력 처리: 빈 값·0건·깨진 행·중복·극단값·형식이나 이름이 바뀐 입력·필수 파일 없음 각각의 처리(격리·거부·보류)와 문서 근거
  5. 풀이 계획: 정식화(목표·결정 변수·제약), 현행 기준선, 후보를 비교하는 방법
  6. 자체 평가가 과제의 평가 조건(범위·기간·시나리오)을 어떻게 흉내 내는지
  7. 문서끼리 갈리거나 모호한 문장, 두 해석과 각각의 영향
  8. 담당자에게 보낸 질문, 아직 없는 답, 답이 없을 때의 계획
  9. 데이터 감사에서 나온 기록 이상과, 오류인지 실제 현상인지 가릴 비교 계획
- CP1 리뷰는 아홉 항목을 모두 덮는다. CONSTRAINT_RED가 1·2·7·8, DATA_EVAL_RED가 3·6·9를 본다. 5는 계획 전용 ALGORITHM_RED, 4는 계획 전용 EDGE_RED를 따로 띄워 본다(EDGE_RED는 CP2에서 실제로 돌릴 반례 입력 목록도 낸다). 동시에 띄울 자리나 시간이 모자라면 따로 띄우지 않고 5는 DATA_EVAL_RED, 4는 CONSTRAINT_RED 의뢰문에 붙인다. 어느 항목도 검토 없이 넘기지 않으며, 추가한 리뷰는 `cp1_reviews`에 같은 영수증 형식으로 더한다.
- 0점·반려·무효 조건에 쓰인 용어가 자료의 서로 다른 두 칸이나 두 정의에 맞을 수 있으면(예: "등급"이 번인 온도 등급과 제품 등급 둘 다에 맞음) 갈린 것으로 본다. 문서 우선순위(개정판·상위 규정)나 "문맥상 이쪽"이라는 추론만으로 한쪽을 버리지 않는다. 질문 예산을 여기에 먼저 써서 담당자에게 그 조건을 짚어 공식 해석을 묻고, 공식 해석이 없으면 두 뜻을 모두 지키는 안을 낸다. CONSTRAINT_RED는 이런 조건에 판결을 내리지 않고 "용어 → 가리킬 수 있는 칸·정의 → 갈림 여부"만 낸다. 제출 전 자체 검사는 뜻마다 따로 돌려, 다른 뜻에서 무효가 되는 건수가 0인지 확인하고 그 숫자를 보고서에 적는다. 두 뜻을 모두 지키는 안의 손실이 큰 경우의 예외는 위 반려 조건 규칙의 계산을 따른다.
- CP1의 P0/P1과 아홉 항목의 빈칸은 그 항목에 기대는 구현을 시작하기 전에 닫는다. 담당자 답을 기다리는 항목은 두 해석 모두에서 허용되는 계획으로 진행한다. CP1이 확정하는 것은 명세다. 구현 결함과 데이터에서 나오는 결과는 CP2·최종 리뷰가 잡는다.
- CP1 뒤에 아홉 항목 가운데 하나를 바꾸면(새 해석·지표·한도·제출물·입력 규칙) 바뀐 항목과 이유를 SPEC_DRAFT에 적고 그 항목을 맡은 리뷰를 새 작업자로 다시 받는다. CP2·최종 리뷰 의뢰문에는 "CP1 확정 항목과 달라진 점"을 먼저 찾게 한다.
- 본선 흐름에서는 한 세션이 진행(ORCHESTRATOR)과 구현(MAIN_BUILDER)을 겸한다. 그 세션은 표의 MAIN_BUILDER 값으로 둔다. 세션의 모델·노력은 참가자가 화면에서 고르는 값이라 스스로 바꿀 수 없다. 첫 브리핑에서 현재 값을 확인해 표와 다르면 바꿔 달라고 한 번만 말하고, 기다리지 않고 진행한다. 확인하지 못하면 UNKNOWN으로 적는다.
- 하위 작업자 수는 키트가 정해 두지 않는다. 공식 규칙과 실제 환경이 허용하는 만큼 동시에 띄운다. 한도를 모르면 그 단계에 필요한 리뷰를 한 번에 모두 띄워 보고, 실제로 동시에 돈 수를 REVIEW_CONCURRENCY에 적는다(거절되거나 대기한 것은 다음 차례로 넘긴다). CP1은 넷까지, CP2는 셋(보안 조건이면 넷)을 한 번에 띄운다. 최종은 제출 형식 리뷰를 뺀 나머지를 한 번에 띄우고, 그 수정이 끝난 뒤 제출 형식 리뷰를 띄운다. 작업자가 많아도 제품을 고치는 작업자는 하나다. 사용량·속도 한도 경고가 나오면 동시 수를 줄이고 그 사실을 적는다.
- 첫 완성안과 CP2가 끝났는데 작업 잠금까지 시간이 남으면 일찍 끝내지 않는다. 검증된 현재 제출안은 그대로 보존하고, 배점이 큰데 확신이 낮은 항목부터 개선 후보를 CANDIDATES.md에 적어 (남은 연습 예산·확인 실험 포함) 잠금 시각까지 진행한다. 더 나은 안은 같은 자체 검증으로 확인된 뒤에만 교체한다. 더 올릴 여지가 없다는 수치 근거가 있을 때만 참가자에게 조기 잠금을 묻는다.
- 메인 세션의 부담을 줄인다. 과제 원문 읽기, 판단, 제품과 SPEC_DRAFT 수정, 영수증·V27 기록, 리뷰 수락은 메인만 한다. 작업자 자리가 비는 동안에는 (가) RECORDER를 따로 띄워 설명 기록(TEST_LOG·DECISIONS·CANDIDATES 같은 run 노트) 정리를 맡기고 메인은 실제 명령 출력과 결정만 넘긴다, (나) 오래 걸리는 기계적 실행(전체 데이터 감사, 격리 사본에서의 후보 재실행·설정 비교)은 읽기 전용 작업자에게 맡겨 결과 파일로 받는다. 이 작업자들은 제품을 고치지 않고, 독립 리뷰어로 다시 쓰지 않는다. 리뷰를 띄울 때는 자리를 리뷰에 먼저 준다. 띄우지 못하면 메인이 겸하고 그 사실을 적는다. 맥락이 압축되면 run/FINALS_RUN.md와 SPEC_DRAFT를 먼저 다시 읽는다.
- 기존 r8.2 도우미 `profile_data.py`·`sanity_check.py`는 같은 폴더의 `data_io.py`를 불러오므로 `-I`로는 실행되지 않는다(ModuleNotFoundError). 이 둘만 `-X utf8 -E -s`로 실행한다. 환경 변수와 사용자 패키지를 무시하는 것은 같다. 나머지 도우미는 `-I` 그대로다.
- 키트 검사 도우미(`submit_check.py`·`security_check.py`·`clean_run.py`·`v27_check.py`)와 그 실행 영수증에 남길 명령은 한 줄로 실행한다. Windows PowerShell에서는 `& '<실제 python.exe>' '-X' 'utf8' '-I' '<도우미 절대경로>' '--root' '<과제 폴더>' …`처럼 모든 낱말을 작은따옴표로 감싸고, 앞에 환경변수가 필요하면 `$env:NAME='값';`으로 PYTHONUTF8·PYTHONIOENCODING·스레드 수(OMP·OPENBLAS·MKL·NUMEXPR·VECLIB)만 붙인다. POSIX에서는 따옴표 없는 한 줄이나 `NAME=값 '<python>' …`를 쓴다. `-I`에서는 PYTHONUTF8이 무시되므로 Windows의 UTF-8은 `-X utf8`로 켠다. 영수증에는 어떤 셸이 실행했는지가 없으므로, 셸마다 다르게 읽힐 수 있는 글자(`& | < > ^ % ! ; $` 백틱, 따옴표, `* ? [ ] { } ~`, 둥근 따옴표·특수 공백)가 경로나 값에 있으면 영수증이 인정되지 않는다. 그런 이름의 폴더에서 작업하지 않는다. 그 밖의 변수·다른 명령 연결·파이프·재지정도 인정되지 않는다(r4-3.15). final 검사가 영수증 형식만으로 FAIL이면 명령을 이 모양으로 다시 실행해 영수증을 새로 남기고, 결과를 손으로 고치지 않는다.
