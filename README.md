# SK hynix AI Hackathon Starter Kit

> **AI 에이전트에게 — 이 저장소를 "설치해서 작업 시작"하라는 요청을 받았다면 이 상자만 따른다.**
> 이 상자 아래의 본문은 기준판(r8.2) 설명이다. 설치·시작 방법은 이 상자가 우선한다.
>
> 1. 과제 폴더 **밖**의 새 임시 폴더에 이 저장소를 clone한다(기본 브랜치가 최신판이다).
>    설치 뒤 이 임시 clone은 지우지 않고 그대로 둔다(과제 밖이라 제출물에 섞이지 않고, 지우면 승인 요청이 생긴다). 본문의 "임시 원본 정리"는 과제 폴더 안에 둔 원본에만 해당한다.
> 2. 설치: `python -X utf8 -I <clone>/scripts/install_v27.py --source <clone> --target <과제 폴더>`
>    (install.sh·install.ps1 대신 이 명령을 쓴다. 시작 문서까지 함께 설치된다.
>    Windows에서 `python`이 실행되지 않으면 `py -3` 또는 실제 `python.exe` 전체 경로를 쓴다. `-X utf8`은 한국어 경로 출력이 깨지지 않게 한다.)
> 3. 점검: `python -X utf8 -I <과제 폴더>/.hackathon-kit/scripts/kit_lifecycle.py doctor --kit <과제 폴더>/.hackathon-kit`
> 4. 시작: `<과제 폴더>/.hackathon-kit/BOOTSTRAP_V27.md`의 시작 문장대로 **`$hackathon-orchestrator-universal`** 로 시작한다.
>    이 스킬이 `hackathon-finals` 절차를 포함하므로, 본문에 나오는 `hackathon-finals` 시작 문장 대신 이것을 쓴다.
>    참가자는 비개발자다. 공식 규칙 문서·과제 지시를 먼저 읽고, 당일 환경은 문서에서 찾아 적고, 문서에 없는 것만 한 번에 묻는다.

## r8.2 candidate — 핵심 RED 6종 + 조건부 SECURITY_RED

본선의 기본 검토는 **문제·명세 / 데이터·평가 / 알고리즘 / 코드 /
경계값·취약점 / 재현·제출**의 6종입니다. 별도 보안 검토는 실제 인증·권한,
외부 서비스·데이터 전송, 비밀값, 권한 있는 도구 실행, 민감정보 처리 경계가
확인될 때 발동합니다. 도구가 설치돼 있거나 AI라는 이유만으로 켜지 않습니다.
확인이 덜 된 조건은 UNKNOWN으로 남기고 미실행을 통과로 바꾸지 않습니다.

6개 작업자를 계속 동시에 띄우는 방식이 아닙니다. 초기 명세·평가 확인,
첫 실행의 알고리즘·코드·경계 검토, 최종 제출물 검토로 나눠 진행하며,
수용량이 부족하면 순차 실행합니다. 마지막 후보는 각 역할의 실제 실행
보고서와 현재 코드·설정·평가·산출물 해시를 함께 확인합니다.

전체 역할·발동 조건·검토 한계는 [본선 검토 구성](references/finals-reviews.md)에
있습니다. finals_review_check.py는 6종과 발동한 보안 검토의 기록 일관성을
확인합니다. 공식 점수·실제 최적성·완전한 보안·제출 완료를 보장하지 않으며,
현재 과제의 실행·검증 근거와 실제 보고서 확인이 필요합니다.

## 비개발자의 이해와 실제 독립 검토

비개발자도 **실제로 쓰는 도구·알고리즘이 무엇이고 왜 선택했는지** 설명할 수
있도록 선택 시점, 중요한 변경 후, 최종 설명에 짧은 한국어 해설을 제공합니다.
최적화기라면 라이브러리와 실제 알고리즘, 목표·제약, 대안, 실행 결과의 보장 범위를
구분합니다. 개발은 에이전트가 수행하며 참가자에게 기술 설계를 떠넘기지 않습니다.

하위 에이전트는 요청만으로 완료 처리하지 않습니다. 실제 작업자 ID, 시작 관찰,
완료 응답·보고서와 검토 파일 해시를 [실행 기록 절차](references/review-execution.md)에
따라 확인합니다. **CP1은 실행 증거가 없으면 gate를 통과하지 못합니다.** 기록의
존재·일관성 검사는 실제 플랫폼 응답 인증이나 무조건적인 실행 보장은 아닙니다.

새 **`edge-redteam` / EDGE_RED**는 코드·명세 검토와 별개로 경계값, 결측치,
잘못된 입력과 실제로 존재하는 취약점 경계를 점검합니다. 허용된 별도 에이전트로
실행하고 실행 불가 시 NOT_RUN을 밝힙니다. 자세한 설명 방식은
[참가자 도구·알고리즘 이해](references/participant-understanding.md)에 있습니다.

## 비개발자를 위한 본선 모드

본선에서는 **`hackathon-finals`**를 사용합니다. 공식 안내·과제 파일을 주면
스킬이 과제 유형과 풀이 방법을 선택하고, 구현·실행·수정·검증·설명·제출 준비를
진행합니다. 사용자가 모델·알고리즘·개발 도구를 직접 설계하거나 매 단계 승인할
필요가 없습니다. 중요한 공식 규정·접근 권한·업무 판단만 질문합니다.

```text
Use the hackathon-finals skill. Read .hackathon-kit/FINALS_POLICY.md first.
나는 비개발자입니다. 공식 자료를 바탕으로 구현·실행·검증·설명과 제출 준비까지 진행해 주세요.
```

`hackathon-orchestrator`로 시작해도 본선임이 확인되면 본선 모드로 연결합니다.
본선 정책은 [FINALS_POLICY.md](FINALS_POLICY.md), 과제별 절차는
[본선 풀이 가이드](references/finals-playbook.md)에 있습니다. 본선 run 기록은
`.hackathon-kit/run/FINALS_RUN.md`를 사용합니다. 이 개정은 r7.2.1 개선판
`9ac5479`를 기반으로 하며, 기존 main의 배포판과 구분되는 로컬 후보입니다.

11월 11일 안내문의 일정·준비물·현장 규칙과 아직 미확인인 AI·도구·제출 조건을
구분했습니다. **예선의 180분·서술형 6문항·모델 목록을 본선에 자동 적용하지
않습니다.** 본선에서 사전 스킬·로컬 파일을 사용할 수 있는지는 새 공식 안내로
확인해야 합니다. 기술 선택·검증 원칙은 유지하며 실제 과제 전에는 연습 결과만
확인할 수 있습니다.

일반 doctor는 설치 무결성 점검입니다. `doctor --pre-submit`과 `gate_check.py`는
기존 예선 전용이며 본선 준비 완료를 판정하지 않습니다. 본선은 실제 과제의
검증·수집 계약과 FINALS_RUN 기록으로 확인합니다.

## 기존 2차 예선 모드

SK하이닉스 AI 해커톤 **2차 예선 시험 형식은 고정하고 과제 도메인만 미정인 상황**을 위한 로컬 워크플로 키트입니다. 먼저 [EXAM_POLICY.md](EXAM_POLICY.md)를 읽으십시오. 새로운 공식 시험·과제 지침이 항상 우선합니다.

공식 불변조건은 최대 180분 풀이, 후속 서술형 6문항 × 5분, 후속 중 AI·복사/붙여넣기 금지입니다. Computer Use/자동 UI 제어, 외부 AI 연결, 문제·파일·결과의 외부 전송, Git Push를 금지합니다. 권장 제공 모델·Astra 제한과 공개 도구/부분 코드 재사용 조건은 EXAM_POLICY를 따릅니다. 이 키트의 공개 소스를 시험 전에 유지보수하는 것과 실제 시험 과제를 외부에 올리는 것은 구분하십시오.

r7.2.1은 마지막 설명에 **수정 전 상태와 현재 결과의 비교**, **과제에 맞는 실제 규칙 적용 사례**를 포함하도록 보강합니다. 선택·필터링 과제에서는 무엇을 왜 선택·제외했는지, 그 외 과제에서는 실제 검증·경계 사례를 설명합니다. 관찰한 사례가 없으면 NOT OBSERVED / UNVERIFIED로 표시하고, 비교 조건이 다르면 그대로 밝힙니다. 기존 설명·6개 답안 개요에 포함하며 질문이나 checkpoint를 추가하지 않습니다. 키트 수정본을 다른 에이전트에게 검토시킬 때는 [독립 검토 안내](references/independent-review.md)를 사용하십시오.

## 설치 — 외부 임시 폴더 우선, 불가능하면 분리된 내부 임시 폴더

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

오프라인 ZIP은 **한 번 해제하면 install.sh/install.ps1이 최상위에 보이는 구조**입니다. **개인 PC의 파일·비공개 Skill은 시험 환경에 업로드할 수 없습니다.** 시험 중에는 Probe 작업 환경 안에서 공개 GitHub 저장소를 Git Clone/다운로드하는 등 최신 공식 안내가 허용한 방법으로 가져옵니다.

### 과제 폴더 밖에 원본을 받을 수 없을 때

제공 환경에서 허용된 외부 임시 위치를 사용할 수 없다면, Codex가 **직접 새로 만든 고유한 과제 하위 임시 폴더**(예: `.myskill-source-<임의값>`)에 원본을 받습니다. 기존 과제 폴더를 원본 보관 장소로 재사용하지 않습니다. 이때만 다음 명시 옵션을 사용합니다.

```bash
bash "$KIT_DIR/install.sh" . --allow-internal-source
```

```powershell
powershell -ExecutionPolicy Bypass -File (Join-Path $KitDir "install.ps1") -Target . -AllowInternalSource
```

이 옵션은 원본과 과제가 동일한 경우, 과제가 원본 안에 있는 경우, 원본이 과제의 `.git`·`.agents`·`.hackathon-kit`과 겹치는 경우를 계속 거절합니다. 기존 파일·스킬 보호와 재설치 기록 보존도 유지합니다.

설치 확인 후 Codex는 자신이 새로 만든 임시 원본에 과제 파일·추가 내용·로컬 변경이 없는지 확인하고 **그 임시 원본만 정리한 뒤** 과제를 진행합니다. 기존 폴더나 소유권이 불명확한 파일을 강제로 지우지 않습니다. 설치기는 원본을 무조건 자동 삭제하지 않으며, 위치를 manifest에 기록합니다. 일반 doctor는 잔존 원본을 경고하고 제출 전 doctor와 helper cleanup은 잔존 시 실패하므로, 숨겨진 원본이 제출물에 섞인 채 완료로 처리하지 않습니다. 임시 원본의 Git 제외는 폴더 전체 제출에서 제거한다는 뜻이 아닙니다.

사용자는 외부/내부 경로를 직접 결정할 필요 없이 "검증된 개정의 README에 따라 설치 위치를 정하고 안전하게 설치·임시 원본 정리 후 시작 지침을 읽어 진행해 줘"라고 요청하면 됩니다. 기존 r7 `b4f4fee`에는 내부 설치 옵션이 없으므로 이 기능은 **r7.1 이후 검증 개정**을 사용해야 합니다.

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
| EDGE_RED | 별도 독립 허용 모델 | 경계값·결측치·잘못된 입력·실제 보안 경계 전담. 제품 수정 금지 |
| RECORDER | Luna 6 | 진행 중 근거 기록 단독 작성. STATE·receipt·동결 문서 수정 금지 |
| TUTOR | 선택적 Sol 6.1 | 참가자 이해를 돕는 완전 읽기 전용 세션 |

선호 모델이 없으면 허용된 대체 모델로 역할 분리를 유지하고 실제 선택을 기록합니다. Tutor가 MAIN과 같은 모델인 것은 금지사항이 아닙니다. 원문·코드·테스트 근거만 설명하고 구현 결정·파일 수정·변경 명령은 수행하지 않습니다.

```text
Read .hackathon-kit/prompts/TUTOR.md and .hackathon-kit/EXAM_POLICY.md.
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

**전체 종료 시각:** 최신 확인된 공식 일정은 **2026-11-04 19:00–23:00 (공식 안내 표기; 시간대는 응시 화면에서 확인)**입니다. 이 날짜를 이후 시험에 재사용하지 말고 최신 공식 화면의 날짜·시간대·단계 종료와 전체 종료를 확인하십시오. 새 공식 안내가 항상 우선합니다. 후속 30분과 문항 생성 전환 대기를 확보하며, 약 5분 안내와 별개로 UI에는 시도당 최대 10분이 표시되고 자동 재시도 때 준비 시간이 다시 시작될 수 있습니다. 전환 대기는 풀이 제한 시간에서는 빠지지만 전체 응시 시간에 포함되며, 지각·대기·재시도로 23:00이 연장되지 않습니다. 상세 가이드는 제출 마감 10분 전 제출 시작을 권고합니다.

**CP3 PRE-SUBMIT:** 남은 검토·수정·검증·제출·준비 시간을 기준으로 시작합니다. 15–20분은 알림이지 모든 일이 끝난다는 보장이 아닙니다. 최종 Code/Constraint Red → 차단 finding 처리·verification → Recorder → final-explain의 사실 설명 → followup-prep의 단일 연습 흐름 → doctor → 필요한 경우 마지막 cleanup 순서입니다.

공식 후속 6문항 전체를 대비하는 질문·답안 개요를 작성합니다. 제출 전에 30분짜리 모의시험을 강제하지 않으며, 짧은 연습은 예약한 제출 시간을 침범하지 않습니다. 마지막 리뷰·정정·수정이 요약 작성 뒤에 생기면 바뀐 판정만 Recorder에 전달해 VERIFY·LIMITATIONS·cheatsheet를 최신화하고, ORCHESTRATOR가 최종 상태와 대조합니다. 이미 기각된 finding을 미해결로 남기거나 과거 실패 자체를 지우지 않습니다. 퀴즈 전체를 반복할 필요는 없습니다. 미검증은 UNVERIFIED, 근거 없는 답은 UNANSWERABLE로 남깁니다. 마감이 차단 결함을 무효로 만들지는 않습니다.

제출 미리보기에는 일부 파일만 표시되며 숨김 파일·내부 도구 폴더가 생략될 수 있으므로, 목록에 보이지 않는다는 사실은 제출 제외의 증거가 아닙니다. 최종 제출 파일의 **전체 용량은 10GB 이하**여야 합니다. **“제출물 확정하고 문제풀기” 이후에는 파일을 수정할 수 없으며**, 확정은 최종 제출 완료와 다릅니다. 후속 서술형까지 마친 최종 완료 화면에서 제출 ID·시각·파일 수·크기를 확인하십시오.

## 수정 전부터 내부 검증 점수 기록

가능한 과제에서는 **수정 전 2/10 → 중간 6/10 → 최종 9/10**처럼 같은 항목으로
진척을 기록합니다. 제공된 채점기가 있으면 그 실제 점수를 우선 사용합니다.
없으면 AI가 원문 요구사항에서 작고 유용한 검사를 만들고, 별도 Red가 검사 기준과
정답 근거를 검토합니다. 공식 배점이 없는데 임의의 공식 100점 기준을 만들지는 않습니다.

`local_score.py`는 실제 검사 기록의 **통과 수 / 선언한 항목 수**를 계산하는
표준 라이브러리 도구입니다. 검사를 대신 실행하거나 숨은 채점 점수를 알아내지 않습니다.
건너뛴 항목은 통과로 세지 않고, 기준·검사 코드의 해시와 검사에 쓴 자료·정책·옵션의
식별자를 함께 기록합니다. 이 값이 다르거나 검사 범위가 미확인이면 점수 상승을
비교하지 않습니다. 최초 기록은 보존하고 현재 코드 버전과 근거를 남깁니다.
로컬 만점도 미검증이나 차단 결함을 없애주지는 않습니다.

이 작업은 기존 intake/CP1/verification에 포함되며 참가자의 추가 명령 암기나 새 역할이
필요하지 않습니다. 시간이 부족하거나 정답 근거가 없으면 현재 검사와 미검증 범위를
남기고 진행합니다. 전체 자료의 무거운 검사를 수정할 때마다 반복하지 않습니다.
스키마·비교 조건·종료 코드는 [내부 검증 절차](references/local-evaluation.md)에 있습니다.
[수정안 검증 범위](references/local-evaluation-validation.md)는 실제 실행과 미검증을 구분합니다.
[r7.2 전체 검토](references/r7.2-full-review.md)에는 후속 경계값 수정과 적용 한계가 있습니다.

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

내부 원본 설치 지원이 cleanup의 백업 보호를 해제하지는 않습니다. 과제 밖 쓰기가 모두 불가능하고 제출 형식상 helper 제거까지 필요하다면, 기록의 안전한 보존·제출 수집 방식을 공식 안내/Cofa Helper로 확인해야 합니다. 백업 없이 기록을 지우거나 외부 서비스에 전송하지 않습니다. 설치 원본 정리에는 run 기록이 없으므로 이 helper cleanup과 구분합니다.

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
