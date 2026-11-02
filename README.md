# SK hynix AI Hackathon Starter Kit

SK하이닉스 AI 해커톤 **2차 예선 시험 형식은 고정하고 과제 도메인만 미정인 상황**을 위한 로컬 워크플로 키트입니다. 먼저 [EXAM_POLICY.md](EXAM_POLICY.md)를 읽으십시오. 새로운 공식 시험·과제 지침이 항상 우선합니다.

공식 불변조건은 최대 180분 풀이, 후속 서술형 6문항 × 5분, 후속 중 AI·복사/붙여넣기 금지입니다. Computer Use/자동 UI 제어, 외부 AI 연결, 문제·파일·결과의 외부 전송, Git Push를 금지합니다. 권장 제공 모델·Astra 제한과 공개 도구/부분 코드 재사용 조건은 EXAM_POLICY를 따릅니다. 이 키트의 공개 소스를 시험 전에 유지보수하는 것과 실제 시험 과제를 외부에 올리는 것은 구분하십시오.

## 설치 — 과제 레포 밖에서 내려받기

필수: **Python 3.8 이상**. Bash와 PowerShell은 같은 Python 표준 라이브러리 backend를 호출합니다. Git은 선택 사항이고, XLSX 분석만 선택 의존성 openpyxl을 사용합니다. 시험 전에 사용할 개정 SHA를 정하고 클론 또는 압축 해제본을 보관하십시오.

```bash
KIT_DIR="$(mktemp -d)"
git clone https://github.com/kane313759-netizen/Myskill.git "$KIT_DIR"
# 시험 전에 검증한 SHA로 고정: git -C "$KIT_DIR" checkout <검증한-commit-SHA>
bash "$KIT_DIR/install.sh" .
```

```powershell
$KitDir = Join-Path $env:TEMP ("Myskill-" + [guid]::NewGuid())
git clone https://github.com/kane313759-netizen/Myskill.git $KitDir
# 시험 전에 검증한 SHA로 고정: git -C $KitDir checkout <검증한-commit-SHA>
powershell -ExecutionPolicy Bypass -File (Join-Path $KitDir "install.ps1") -Target .
```

오프라인 ZIP은 **한 번 해제하면 install.sh/install.ps1이 최상위에 보이는 구조**입니다. 키트 폴더와 과제 폴더는 겹치면 안 됩니다.

설치 시 `.agents/skills/`와 `.hackathon-kit/`만 사용하고 기존 AGENTS.md·.gitignore·과제 소스는 수정하지 않습니다. 필수 스킬의 동명 충돌은 쓰기 전에 차단합니다. 바이트가 동일한 기존 스킬은 빌려 사용하며 cleanup에서 삭제하지 않습니다. 선택 스킬 충돌은 보존·보고합니다.

재설치는 run 기록을 유지하고, 소유권 manifest로 확인된 수정하지 않은 스킬·지원 파일만 갱신합니다. 로컬 변경은 덮어쓰지 않고 보고하며 doctor가 확인합니다. 구버전은 동일한 파일만 안전하게 이관합니다. 소유권을 확인할 수 없으면 강제 삭제하지 않습니다. 설치 개정과 해시는 `.hackathon-kit/manifest.json` 및 VERSION에 남습니다.

Git 제외 규칙은 하위 폴더·연결 worktree에서도 설치 위치를 기준으로 만듭니다. 공유·기존 제외 규칙은 cleanup 뒤에도 로컬 Git 메타데이터에 유지합니다. **Git에서 숨기는 것은 폴더 전체/ZIP 제출에서 제외한다는 뜻이 아닙니다.** 제출 수집 방식은 GRADER.md에 기록하고, 불명확한 시험 UI/제출 문제는 Cofa Helper로 확인하십시오.

## 첫 메시지

```text
Use the hackathon-orchestrator skill.
Read .hackathon-kit/EXAM_POLICY.md first.
Follow its canonical checkpoint/ownership protocol.
Start with grader intake and a safe pre-edit baseline in one evidence pass.
Do not edit product logic until the independent CP1 review, evidence gate,
and blocking-finding dispositions pass.
```

긴 시작 프롬프트는 [BOOTSTRAP_PROMPT.md](BOOTSTRAP_PROMPT.md), 단계별 호출은 [CALLING.md](CALLING.md)에 있습니다.

## 역할과 기록 소유권

| 역할 | 선호 모델(실제 제공 여부 확인) | 책임 |
|---|---|---|
| ORCHESTRATOR | Terra 5.6 | STATE·gate·checkpoint·리뷰 receipt 단독 작성. 제품 소스 수정 금지 |
| MAIN_BUILDER | Sol 6.1 | 유일한 제품 소스 작성자. Phase 0의 5개 intake/spec 문서 작성 |
| CODE_RED | 독립된 Terra | 코드·계약·회귀 검토 결과 반환. 공유 파일 수정 금지 |
| CONSTRAINT_RED | 독립된 Sol 6.1 | 원문 기준 명세·가정·제약 공격. 공유 파일 수정 금지 |
| RECORDER | Luna 6 | 진행 중 근거 기록 단독 작성. STATE·receipt·동결 문서 수정 금지 |
| TUTOR | 선택적 Sol 6.1 | 참가자 이해를 돕는 완전 읽기 전용 세션 |

선호 모델이 없으면 허용된 대체 모델로 역할 분리를 유지하고 실제 선택을 기록합니다. Tutor가 MAIN과 같은 모델인 것은 금지사항이 아닙니다. 원문·코드·테스트 근거만 설명하고 구현 결정·파일 수정·변경 명령은 수행하지 않습니다.

```text
Read .hackathon-kit/prompts/TUTOR.md and EXAM_POLICY.md.
You are strictly read-only, including run notes.
Explain actual code and evidence; do not make MAIN's implementation decisions.
```

참가자의 실제 질문·선택·수동 검증은 사건과 근거를 MAIN/Recorder에 전달해 기록합니다. 단순한 질문이나 이해했다는 표현을 수동 검증으로 바꾸지 않습니다. 사람 판단·AI 실패 사례가 없는 것도 유효한 사실입니다. 기록 전달·준비는 풀이 단계에서만 하며 후속 시험 중에는 AI·복사/붙여넣기를 사용하지 않습니다.

## 3개 checkpoint

**Phase 0:** MAIN이 grader-intake → immutable-inventory → task-router → problem-intake → constraint-discovery를 한 번의 근거 수집으로 수행하고 문서를 묶어서 작성합니다. baseline 명령의 변경·네트워크·실행 시간을 먼저 확인하며 필요한 경우 임시 데이터로 격리합니다. 실행 불가는 이유와 확인한 자료를 남깁니다.

**CP1 전 형식 확인:** MAIN은 설치된 템플릿의 `##` 제목을 유지하고 내용을 채운 뒤 `python .hackathon-kit/scripts/gate_check.py --preflight`로 형식을 확인합니다. 형식 때문에 리뷰를 반복하지 않도록 Red를 부르기 전에 수행합니다. 이 통과만으로 구현할 수는 없습니다.

**CP1 SPEC FREEZE:** Red는 원문을 먼저 읽고 MAIN 문서를 검증할 주장으로 취급합니다. 새 에이전트의 기본 이력 상속에 의존하지 말고 지원 시 `fork_turns="none"`, 아니면 깨끗한 별도 세션을 사용합니다. 실제 리뷰는 CP1_RED.md에, 소스 경로·모델/컨텍스트·5개 문서 해시·finding 처리 결과는 CP1_REVIEW.json에 남깁니다. P0/P1은 근거에 따라 수정/기각하고 재검증해야 합니다.

```bash
# 검토한 문서 해시 확인 도구. 이 명령만으로 gate가 닫히지는 않습니다.
python .hackathon-kit/scripts/gate_check.py --artifact-hashes
python .hackathon-kit/scripts/gate_check.py
```

GRADER·BASELINE·IMMUTABLES·SPEC_DRAFT·CONSTRAINTS는 승인 후 동결합니다. 일반 검증은 VERIFY에 기록합니다. 중요한 계약 변경은 gate를 다시 열고 영향 범위만 독립 재검토합니다. 상태값만 바꾸거나 수정한 파일을 무조건 재해시해서는 안 됩니다. UI/chat 원문만 있는 경우 TASK_EVIDENCE.md에 출처·실제 발언/발췌를 기록할 수 있습니다.

checker는 기록의 구조·존재·변경·차단 finding 처리를 확인합니다. 실제 모델 선택·컨텍스트 생성·업무 규칙의 진실까지 자동으로 증명하지는 않습니다.

**CP2 FIRST END-TO-END:** Code Red와 Recorder를 실행합니다. 제약/목적 위험이 생겼을 때만 추가 Constraint Red를 실행합니다. 여섯 축의 후속 근거와 cheatsheet를 이때부터 누적합니다.

**전체 종료 시각:** 원본 브리프의 시험 창은 10:00–14:00이며 전환 대기 약 5분도 전체 시간에 포함됩니다. 지각·대기로 14:00이 연장되지 않습니다. 최신 공식 화면의 시간대·단계 종료와 전체 종료를 확인하고 후속 30분과 전환 시간을 확보하십시오. 상세 가이드는 제출 마감 10분 전 제출 시작을 권고합니다.

**CP3 PRE-SUBMIT:** 남은 검토·수정·검증·제출·준비 시간을 기준으로 시작합니다. 15–20분은 알림이지 모든 일이 끝난다는 보장이 아닙니다. 최종 Code/Constraint Red → 차단 finding 처리·verification → Recorder → final-explain의 사실 설명 → followup-prep의 단일 연습 흐름 → doctor → 필요한 경우 마지막 cleanup 순서입니다.

공식 후속 6문항 전체를 대비하는 질문·답안 개요를 작성합니다. 제출 전에 30분짜리 모의시험을 강제하지 않으며, 짧은 연습은 예약한 제출 시간을 침범하지 않습니다. 마지막 리뷰·정정·수정이 요약 작성 뒤에 생기면 바뀐 판정만 Recorder에 전달해 VERIFY·LIMITATIONS·cheatsheet를 최신화하고, ORCHESTRATOR가 최종 상태와 대조합니다. 이미 기각된 finding을 미해결로 남기거나 과거 실패 자체를 지우지 않습니다. 퀴즈 전체를 반복할 필요는 없습니다. 미검증은 UNVERIFIED, 근거 없는 답은 UNANSWERABLE로 남깁니다. 마감이 차단 결함을 무효로 만들지는 않습니다.

## Doctor와 마지막 cleanup

```bash
bash .hackathon-kit/scripts/doctor.sh
bash .hackathon-kit/scripts/doctor.sh --pre-submit
# 설명·연습 완료 후, 제출 규칙상 helper 제거가 필요할 때만:
bash .hackathon-kit/scripts/clean.sh --apply
```

```powershell
powershell -ExecutionPolicy Bypass -File .hackathon-kit/scripts/doctor.ps1 -PreSubmit
powershell -ExecutionPolicy Bypass -File .hackathon-kit/scripts/clean.ps1 -Apply
```

Doctor는 소유/필수 스킬·지원 파일·버전·모든 설치 제외 경로를 확인하고, 제출 전에는 동일한 CP1 gate 검사 결과를 사용합니다. 제품의 실제 채점·수동 UI 검증을 대신하지 않습니다. cleanup 기본값은 dry-run이며, 적용하면 run 기록을 과제 밖의 고유한 로컬 임시 디렉터리에 백업합니다. 로컬 변경·알 수 없는 파일·symlink 때문에 소유권이 불확실하면 삭제 전에 중단합니다. 이때 helper가 남았는지 보고 제출 파일 목록을 확인하십시오. TMPDIR/TEMP가 과제 안을 가리키면 외부 로컬 임시 위치로 바꿔야 합니다.

## 조건부 도구

과제·채점 근거가 있을 때만 도메인 playbook을 켭니다. 배차·웹·Docker·ML을 기본 구조로 가정하지 않으며 공식 채점에 없는 penalty를 추가하지 않습니다.

**기본값은 과제 도구만 사용, 선택 도구 추가 없음입니다.** 과제가 제공하거나 원래
설정·설명서에 선언한 도구, 실제 필수 기능을 위한 최소 의존성, 키트 도구와
표준 라이브러리로 진행합니다. 과제의 정상 설치·실행 절차는 유지합니다.

Python·CSV·JSON·PDF라는 이유만으로 Ruff·DuckDB·jq·pdfplumber 등을 자동
검색·도입·설치하지 않으며, 이미 설치되어 있다는 이유로 사용하지도 않습니다.
필수 도구가 없으면 가능한 대안·부분 결과와 미완료 범위를 명시합니다.
편의를 위한 도구를 AI가 스스로 필수라고 바꾸어 부르지 않습니다.

과제 도구의 원문 근거·설치/실행 계획·대안·원본/정확성 보호·시간 예산을 기존
SPEC 검증 계획에서 함께 검토합니다. 추가 승인 단계나 새 역할은 없습니다.
[선택 도구 참고표](references/optional-tools.md)는 별도 사전 연습이나 이후 특정
도구 사용을 명시적으로 요청할 때의 자료이며 기본 시작 절차에서는 열지 않습니다.
`tool_inventory.py`도 기본 호출에서 빠진 수동 진단 도구입니다.

이는 안정성을 위한 키트 기본값이며 공식 브리프의 공개 도구 다운로드 허용을
새로 금지하는 규칙이 아닙니다. 현재 정책과 이전 r6 선택 검증의 범위·한계는
[검증 기록](references/tool-selection-validation.md)에 구분해 기록합니다.

```bash
python .hackathon-kit/scripts/env_scan.py --root .
python .hackathon-kit/scripts/profile_data.py supplied.csv --max-rows 50000
python .hackathon-kit/scripts/profile_data.py output.json --records-key results
python .hackathon-kit/scripts/profile_data.py tables.xlsx --list-sheets
python .hackathon-kit/scripts/sanity_check.py output.csv --encoding cp949
```

Inventory는 제한된 보조 탐색으로, 원문 채점 계약을 대체하지 않습니다. 데이터 도구는 표본 행·JSON 바이트·읽기 샘플을 제한합니다. 모든 형식의 전체 메모리 하드캡을 보장하지 않습니다. 복수 JSON 레코드 배열·복수 XLSX 시트는 선택을 요구하며, 문자열 NULL의 의미는 `--null-token`으로 명시할 수 있습니다. 로그 요약은 triage만 돕고 실제 테스트 종료 코드·프레임워크 결과가 판정 기준입니다.

## 키트 개발 검증과 단일 ZIP 생성

다음은 실제 시험 과제 밖에서 키트를 유지보수할 때의 명령입니다.

```bash
python -B -m unittest discover -s tests -v
python scripts/package_release.py --source . --output /tmp/Myskill-exam-safe.zip
```

새로 작성해 아직 Git에 추가하지 않은 배포 파일까지 검증할 때만 `--include-untracked`를 사용하십시오. 패키지는 허용된 소스만 포함하고 run 기록·.git·캐시·중첩 ZIP을 제외합니다. Actions도 압축된 ZIP을 다시 감싸지 않고 배포 디렉터리 내용을 직접 업로드합니다.

실제 에이전트 3개 모의 과제와 두 수정 경로의 재검증 범위는 [운영 리허설 기록](references/operational-rehearsal.md)에 있습니다. 실제 시험장 모델·180분 전체 운영·사람의 서술형 답변까지 검증했다는 의미는 아닙니다.
