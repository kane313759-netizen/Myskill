# v2.7 추가 계약

이 문서는 `hackathon-orchestrator-universal`의 기계 기록과 운영 절차를 연결한다. 먼저 `v27-r81-map.md`에서 기존 계약을 확인한다. 현재 기준은 r8.2이며 `v27-baseline.json`은 기존 112개 파일의 SHA256과 기존 STATE 키를 기록한다. 해시는 파일 무결성을 검사하며 작성자나 이벤트 진위를 인증하지 않는다.

## 환경과 시간

설치 시 `.hackathon-kit/run/ENV.md` 등 신규 템플릿을 초기화한다. 이미 작성한 기록은 보존한다. 각 스위치의 `classification`은 `CONFIRMED`, `PLAN_DEFAULT`, `UNKNOWN` 중 하나다. 확정에는 작업 폴더 안의 원문 경로·해시·정확한 발췌를 연결한다. 계획값은 허용 증거가 아니다. 날짜 시각은 ISO 8601 시간대 포함 형식으로 기록한다.

현재 전달된 안내문은 경기 09:30–16:00, 좌석 점심 12:00–13:00, 이후 키노트와 Top20 피칭을 안내한다. 이 일정만으로 실제 제출 확정 마감이나 본선 후속 평가를 확정하지 않는다. 모델은 현재 사용 가능 목록, 공식 허용·제한, 역할별 실제 배정을 구분한다. 모델 이름이나 성능 순위를 미리 고정하지 않는다. 예선 Astra 제한은 미확인 본선의 준비 가정으로만 보존한다.

```text
python -I .hackathon-kit/scripts/deadline.py --input .hackathon-kit/run/ENV.md
```

`deadline.calculate()`는 `FOLLOWUP=FIXED_TIME|AFTER_CONFIRM|NONE`을 계산한다. S=60, R≥10은 계획 기본값이다. C를 직접 지정하면 그 값을 쓰고 `c_basis`에 명시한다. 지정하지 않으면 `FIX_BUFFER + REVIEW_MINUTES_EACH × 배치 수`로 계산한다. 기본은 여유 20분 + 10분 × 7개 순차 리뷰 = 90분이다. REVIEW_PARALLEL=YES이고 실제로 동시에 도는 리뷰 작업자 수 REVIEW_CONCURRENCY를 적었을 때만 올림((FINAL_REVIEW_ROLES − 1) ÷ REVIEW_CONCURRENCY) + 1개 배치로 계산한다. 제출 형식 리뷰(SUBMISSION_RED)는 다른 리뷰의 수정이 끝난 실제 제출 후보를 보므로 마지막에 따로 한 번 돈다(리뷰 7개 기준 동시 6명 이상이면 40분, 3명이면 50분). NO/UNKNOWN이거나 동시 수가 UNKNOWN이면 순차다(r4-3.12). SECURITY_RED의 NOT_TRIGGERED를 확인한 경우에만 FINAL_REVIEW_ROLES를 6으로 갱신한다. 기본 7은 조건부 보안 리뷰까지 준비하는 가정이다.

학습 축소에는 실제 참가자 선택이 필요하다. NONE에서 S_pre=0은 확인된 피칭 전 학습 가능 시간도 필요하다. 템플릿의 T_SUB·WINDOW_END=16:00은 참가자가 전달한 경기 종료 시각을 쓴 PLAN_DEFAULT이며 공식 제출 확정 마감이 아니다. 그래서 계획은 KNOWN으로 계산하되 v27_check의 공식 마감 보류는 유지한다. 값 자체가 없으면 UNKNOWN이다. PAUSE 점심과 CP3 시작~작업 잠금이 겹치면 경고만 출력하고 일정을 자동 이동하지 않는다.

`--observe-now`는 실제 시스템 시각을 추가한다. CP3 시작 이후에도 남은 일정을 출력하고 지난 항목은 `passed`와 경고에 남긴다. 확정 마감을 지난 경우에만 `PAST_CONFIRMATION`과 종료 코드 1을 반환한다. 계산 결과는 V27_STATE의 `deadline`에만 기록하고 기존 STATE의 공식 마감과 섞지 않는다. `--observe-now`로 얻은 결과를 기록해도 된다: v27_check는 기록이 현재 ENV로 `deadline.py`가 실제로 낼 수 있는 출력(계획 그대로, 또는 지난 단계 경계마다의 관측 출력) 가운데 하나와 완전히 같은지 본다. 칸을 빼거나 고친 기록, 있을 수 없는 `passed`·경고 조합은 실패한다. 기록된 상태가 PAST_CONFIRMATION이면 제출 미확정으로 보류한다(r4-3.13).

## 증거와 단계

`V27_EVIDENCE.json`은 증거 색인이다. 각 `records` 값은 `{path, sha256}`이며 문서는 JSON 또는 정확히 한 개의 JSON 코드 블록을 사용한다. 템플릿은 미완성 상태로 배포되며 통과 증거가 아니다.

```text
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase intake
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase cp1
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase final
```

### 무효·감점 규칙 표 (r4-3.16)
`records.hard_rules`는 `.hackathon-kit/run/HARD_RULES.json`이다(틀 `templates/HARD_RULES.json`). cp1과 final은 이 기록이 없으면 FAIL이다. 규칙마다 consequence(VOID·ZERO·REJECT·PENALTY·SOFT)를 적는다. VOID·ZERO·REJECT는 결과를 정하는 낱말(term)과 그 낱말의 모든 읽기(candidates: meaning·source)를 적고, decision은 ALL_MEANINGS, OFFICIAL_ANSWER(official_answer의 quote가 source 파일에 그대로 있고 한 후보를 짚으며 "문서에 없음"류가 아님), SINGLE_MEANING(후보가 하나일 때만), COST_EXCEPTION(loss_all_meanings > probability_wrong × loss_if_wrong) 가운데 하나다. final은 지킨 뜻마다 checks(meaning·scenario·violations·evidence{path,sha256})를 요구하고, 위반이 1건이라도 있으면 FAIL이다. PENALTY는 final에 tradeoff(chosen·chosen_expected_loss·alternatives[label·expected_loss])를 요구하고, 더 작은 기대 손실의 대안이 있으면 reason이 없을 때 FAIL이다. 규칙이 하나도 없으면 rules를 비우고 no_hard_rules_reason을 적는다. 다만 과제 자료(키트·가상환경·라이선스 문서 제외)에 무효·0점·반려·감점·실격·불합격 같은 결과 낱말이 있으면 빈 표는 FAIL이다. 그 줄을 규칙으로 적고, 점수나 접수를 정하지 않는 줄이면 SOFT로 적는다. CP1·final 리뷰의 required_scope에는 이 기록의 현재 SHA256이 들어가야 한다. `hard_rules.py scan --root <과제 폴더> --term <낱말>`은 그 낱말이 나오는 문서 줄, CSV·TSV 머리글, XLSX 윗줄을 나열한다(키트·에이전트 폴더 제외).

인수 검사는 환경과 별도 상태를 확인한다. CP1은 데이터 감사·채점·결정·안전 및 CONSTRAINT_RED/DATA_EVAL_RED의 실제 실행을 확인한다. 최종 논리 단계 CP3에서는 기존 `checkpoint: FINAL` 계획·영수증을 그대로 두 검사에서 쓴다. 여섯 핵심 RED와 조건부 SECURITY_RED의 FINAL 집계, 최신 제출·보안·복사 재실행·학습 기록을 추가 확인한다. CP1·이전 CP2 기록의 이름은 그대로다. 스냅샷은 M1과 FINAL에만 보관하며 추가 리뷰 관문이 아니다. 본선에 예선 CP1의 고정 문서 게이트를 강요하지 않는다.

독립 리뷰는 기존 `review_execution.py`와 `finals_review_check.py` 계약을 재사용한다. 깨끗한 별도 작업자 컨텍스트와 실제 LAUNCHED/RUNNING/COMPLETED 관측·보고서·검토 파일 해시가 필요하다. 생성 계획, 본체의 셀프 체크, 완료 문구만으로 대체하지 않는다. 실행 불가 때 미실행이라고 보고한다. SECURITY_RED는 실제 인증·권한·비밀·외부 데이터/서비스 경로·특권 도구·민감 자료 경계가 있을 때 발동한다. P1/P0 발견은 수정 검증 또는 근거 있는 반증으로 닫는다.

`submission`, `security`, `clean_run` 참조에는 추가 `execution:{path,sha256}`가 필요하다. 해당 JSON은 실제 도구 호출의 `{tool:"exec_command",argv:[실제 인터프리터 절대경로,"-I",도우미 절대경로,...],request:{cmd:...},result:{exit_code:0,output:실제 JSON stdout}}`을 보존한다. tool은 ENV의 EXECUTION_TOOLS 목록으로 확인하며 기본은 `["exec_command"]`라는 PLAN_DEFAULT다. 실제 플랫폼의 도구 이름을 확인하면 예를 들어 `bash`를 추가하고 동일한 구조·명령·현재 파일 검사를 적용한다. 목록에 없는 도구 또는 `MANUAL_TRANSCRIPT`는 실행 확인 불가로 UNVERIFIED이며 PASS로 승격하지 않는다. 별도의 실제 파일 변경·잘못된 형식은 계속 FAIL이다.

`argv`는 실제 명령의 구조화된 사본이다. 실제 cmd는 어느 셸이 실행했든 같은 뜻인 인터프리터 호출 하나여야 하고, 그 낱말 목록이 argv와 같아야 한다. 인정하는 모양은 셋이다: (가) PowerShell `[$env:NAME='값'; …] & '<인터프리터>' …`(bash는 문법 오류, cmd.exe는 작은따옴표 인터프리터를 실행하지 못한다), (나) POSIX `NAME=값 … <인터프리터> …` 또는 작은따옴표로 감싼 인터프리터로 시작하는 줄(PowerShell·cmd.exe는 실행하지 못한다), (다) 따옴표 없는 낱말과 큰따옴표 낱말만 쓴 줄(세 셸이 같게 나눈다). NAME은 PYTHONUTF8·PYTHONIOENCODING·OMP_NUM_THREADS·OPENBLAS_NUM_THREADS·MKL_NUM_THREADS·NUMEXPR_NUM_THREADS·VECLIB_MAXIMUM_THREADS만 허용한다. 낱말에는 글자·숫자와 `_ - . / : = +`(따옴표 안에서는 공백 `, ( ) @ #`도)만 올 수 있고, 역슬래시는 bash가 그 줄을 실행할 수 없는 경우에만 허용한다. 빈 낱말, 역슬래시로 끝나는 낱말, `-`로 시작하며 `.`·`:`가 든 따옴표 없는 낱말은 거절한다. 인터프리터와 도우미 사이의 옵션은 `-I`·`-B`·`-u`·`-X utf8`만 허용한다. 인터프리터는 실행 중 Python의 `sys.executable` 실제 경로를 사용하며, `--root`와 현재 `--rules`/`--plan` 경로를 명시한다. 셸 블록·별칭·`-c`를 대신 쓰지 않는다. 실제 stdout이 결과 문서와 일치해야 하며 기록 자체를 스크립트가 생성한 결과로 가장하지 않는다.

## 데이터와 채점

명시 입력만 `data_audit.py --root . --plan audit-plan.json`으로 조사한다. 파일 경로·바이트/행 한도를 고정하며 저장소 전체를 재귀 조사하지 않는다. 10개 항목은 적용 여부·방법·관측·조치·한계를 기록한다. 의미를 검증하지 못한 항목을 통과로 만들지 않는다. 시간형 컬럼이 있으면 시간 무관 N/A를 막는다. DATA_AUDIT 템플릿과 V27_EVIDENCE의 계획 스키마를 따른다.

공식 grader가 우선이다. 없을 때만 작은 자체 채점기를 작성한다. 수치 점수를 얻을 수 없으면 `UNAVAILABLE_WITH_REASON`으로 기록한다. 자체 채점기 사용 시 요구사항에서 독립적으로 도출한 POSITIVE 1~3개 정답 사례, NEGATIVE 1개 이상 계약상 틀린 사례, 실행 결과와 실제 metric을 남긴다. 0벡터 등은 문제에 따라 정답일 수도 있으므로 자동으로 오답 취급하지 않는다. holdout을 보고 후보를 고르면 첫 사용부터 튜닝 데이터다. 4회 이상 조회 경고도 유지하되 첫 3회를 독립 검증이라고 주장하지 않는다.

## 제품 검사와 보관

각 CLI의 `--help`가 인수 계약이고 함수의 plan/rules는 해당 테스트의 작은 실행 예제로 확인할 수 있다. 결과 출력은 stdout이며 명시 `--output`만 파일을 만든다. 검사 대상·원자료를 출력 경로로 지정하지 않는다.

- `submit_check.py --root . --rules rules.json`: 명시한 파일의 JSON/CSV/text 형식, 필드, 열, 행 수, 허용 값·범위·유일 키·합계 제약과 총 용량을 검사한다. 공식 규칙을 자동 추측하지 않는다.
- `clean_run.py --root . --plan plan.json --scratch 새임시폴더`: 명시한 후보·허용 자료를 복사하고 `execution_authorized:true`인 명령만 실행한다. 출력의 기준 해시 또는 JSON 수치 허용오차를 비교한다. 의존성 설치·셸·Git·외부 전송을 자동 수행하지 않는다. 실행 허용은 sandbox를 뜻하지 않으며 파일 권한이나 네트워크를 OS 수준에서 격리하지 못한다.
- `security_check.py --root . --plan plan.json`: 명시 파일만 크기 제한으로 검사한다. 비밀/개인정보 패턴과 위험 호출 후보를 값 노출 없이 보고하고 근거 있는 disposition을 기록한다. 동적 공격·권한 전체·누출 부재를 보증하지 않는다.
- `snapshot.py create --help` 및 `verify --help`: 명시 파일을 로컬 보관하고 원자료는 해시만 기록한다. M1과 FINAL 두 번만 남긴다. 복사본은 읽기 전용이고 원본 권한은 바꾸지 않는다. 읽기 전용은 사용자나 프로세스가 해제할 수 있으며 장치 장애를 대비한 독립 백업이 아니다.

작업 폴더 통째 수집에 대비한 정리 순서는 **최종 수집 준비·모든 검증 완료 → purge 미리보기 → purge --apply → 기존 clean --apply**다.

```text
python -I .hackathon-kit/scripts/snapshot.py purge --root .
python -I .hackathon-kit/scripts/snapshot.py purge --root . --apply
python -I .hackathon-kit/scripts/kit_lifecycle.py clean --kit .hackathon-kit --apply
```

purge는 `.hackathon-kit/snapshots` 전체를 먼저 검증한다. 직계 하위의 올바른 이름·MANIFEST·무결성·소유 범위를 확인한 보관본만 삭제하고 빈 상위 폴더도 제거한다. 다른 파일·폴더·링크·reparse point가 하나라도 있으면 아무것도 삭제하지 않고 종료 코드 2로 거부한다. 미리보기는 바이트·권한을 바꾸지 않는다. 적용 시 소유 폴더와 파일만 쓰기 가능하게 바꾸며 스냅샷은 사라진다. 삭제된 스냅샷 증거를 현재 증거처럼 재검사하지 않는다. clean의 실행 메모 백업을 포함해 실제 수집 대상을 다시 확인한다.

깨끗한 재실행이나 규격 검사 통과만으로 공식 제출 확정 영수증을 대신하지 않는다. 최종 파일을 변경하면 관련 검사와 리뷰 범위를 갱신한다. 입출력 경로·해시·원래 안전 경계를 바꾸는 수정은 시간 부족만으로 생략하지 않는다.

## 참가자 이해와 학습

Type A는 실제 업무 판단·위험 수용·학습 시간 선택처럼 참가자 결정이 필요한 사안이다. Type B는 AI가 기술을 선택하고 선택한 이유·대안·예제·설정 변경 영향·한계를 먼저 설명하는 기록이다. 모든 기술 선택을 승인 질문으로 바꾸지 않는다. 참가자의 이해나 회상 성공은 AI가 대신 인증하지 않는다.

중간 10/5/10분과 최종 S=60분을 계획한다. 학습 블록에서 모델이나 알고리즘을 바꾸지 않는다. STUDY_BRIEF는 실제 코드·검사·결정에만 근거하고 `PREPARED`와 실제 전달 `DELIVERED`를 구분한다. 브리핑은 비개발자가 그대로 소리 내어 읽을 수 있는 자연스러운 한글 구어체 2~3줄과 실제 수치가 있으면 숫자 1줄로 정리한다. 공식 본선의 후속 평가가 미확인이면 연습 문항을 공식 6문항이라고 부르지 않는다. WHITEBOARD·MAINTENANCE·PITCH_NOTES는 필요한 경우 사용하는 보조 문서다. 시작 문장과 키트 없이 진행하는 짧은 대체 지시는 BOOTSTRAP_V27.md에 있다.

## 보존과 배포

`install_v27.py`는 원래 설치기의 소유권·충돌 보존을 재사용하고 추가 파일 존재/해시를 확인한다. BOOTSTRAP_V27.md는 설치 후 `.hackathon-kit/BOOTSTRAP_V27.md`에 복사하고 managed_files로 소유권을 기록해 기존 doctor·clean과 호환한다. 변경되지 않은 기존 소유 스킬만 갱신하며 사용자가 수정한 파일은 보존하고 충돌을 보고한다. `package_v27.py`는 원래 패키저의 허용 목록에 명시된 신규 지도·시작 문서·계약·보호 JSON을 더한다. 기존 112개 파일 및 EXAM_POLICY와 기존 STATE 키는 보존한다. `--source`를 제공한 v27_check도 보호 해시를 읽기 전용 확인한다. 이 자기 기재 manifest는 신뢰할 수 있는 배포 SHA와 함께 확인해야 한다.

P2 튜닝·변경 실험·피칭 검사 자동화는 구현하지 않았다. P1이 증거의 의미적 진실, 숨은 점수, 참가자의 기억, 모든 공격, 실제 접수 성공을 증명한다고 주장하지 않는다.

## r2: 기준선, 진행자 회신, 변경 실행

최종 검사에는 `records.baseline_comparison`, `records.external_requests`, `records.maintenance`가 필요하다. 모든 참조는 현재 작업 폴더의 `{path,sha256}`이다. 증거 자체는 출처 진위를 보증하지 않는다.

- baseline_comparison: `AVAILABLE`일 때 `metric`, `direction` (`HIGHER_IS_BETTER` 또는 `LOWER_IS_BETTER`), 유한한 `baseline_value`/`candidate_value`, `selection`, `shared_scope_evidence`, `baseline_evidence`, `candidate_evidence`를 기록한다. 두 점수 JSON은 각각 `{metric,value,scope,artifact:{path,sha256}}`를 갖고 scope는 공통 범위 JSON과 일치해야 한다. 후보 artifact는 현재 clean_run 산출물이어야 하며 현행 유지일 때 기준선 artifact와 SHA256이 같아야 한다. task_metric_ref가 있는 과제 지표의 동일 평가 악화는 오류이며 대리 지표 악화는 경고다. 평가가 불가능하면 `UNAVAILABLE_WITH_REASON`과 이유를 남기며 최종 검사는 UNVERIFIED다. 수치만 같고 조건이 다르면 비교로 취급하지 않는다. 선택이 `CURRENT_BASELINE`이면 `best_alternative`와 `rejection_basis` 및 기존 `baseline_assumptions_check`를 기록한다. 현행의 합법성·안전성은 별도로 확인한다.
- external_requests: `{status:NONE}` 또는 `{status:TRACKED,requests:[...]}`를 기록한다. 각 요청은 `PENDING` 또는 `RECEIVED`이고 RECEIVED는 `response_evidence`를 연결한다. PENDING은 최종 검사를 UNVERIFIED로 유지한다. 단 `deadline_fallback:true`와 과제 원문의 hard_limits 및 지표 비교 및 제출 검증 통과가 모두 확인되면 경고로 낮춘다. 채팅의 발송·응답 기록을 실제 근거로 보존하며, 대기 중에는 다른 독립 작업을 계속한다.
- maintenance: `runs`에 서로 다른 두 개 이상의 `{id,change,before_config,after_config,program,execution,observed_output,status:PASS,verification}`을 기록한다. 파일 참조는 해시를 포함하며, 두 설정의 바이트가 달라야 한다. 실제 native 실행은 `-I` Python으로 기록된 프로그램 및 변경 설정 파일을 사용하고 stdout JSON이 observed_output과 같아야 한다. 이 검사는 실행 기록과 파일 무결성만 검사하며 테스트 자체의 품질·OS 격리·인간 판단을 인증하지 않는다. 서로 다른 두 변화와 기대 관계를 요구하고 적절한 검토자가 내용을 검증한다.
- `decisions.type_b_cards`는 설명 기록이며 `selection_by:AI`를 명시한다. `selection_by:PARTICIPANT` 또는 `participant_approval_required:true`는 기술 결정을 참가자에게 전가하므로 FAIL이다. Type A 업무·위험 판단은 이 제한과 구별한다.
- 전체 데이터 감사는 명시된 CSV와 gzip CSV를 파일별 스트리밍한다. `max_rows`는 앞부분 프로파일 표본만 제한한다(실제 상한 10,000행). 전체 스캔은 `max_scan_bytes` 기본 2GiB, `max_scan_seconds` 기본 300초(최대 900초)를 각 파일에 적용하고, 초과 파일만 UNVERIFIED로 기록한 뒤 나머지를 계속 검사한다. 기간·출처·개체별 샘플은 기본 최대 2,000개이며 무작위 표본의 누락 가능성이 있다. CSV 외 기존 형식은 bounded 프로파일로 제한되며 전체를 읽지 못하면 UNVERIFIED다. 시각 역행·단위 계단은 후보 경보일 뿐, 이름·행 순서·누락·혼합 시간대·제품 구성에 따라 거짓 양성 또는 누락이 가능하다. 데이터의 실제 공정 순서·동일 개체·단위 개정 근거는 별도 확인한다.

같은 개체의 앞선 단계 종료와 다음 단계 시작을 교차 비교한다. `time_order`에 id·sequence·start·end·source 역할을 지정하거나 일반 명칭으로 자동 추정한다. 출처별 비율이 기준(기본 5%) 이상이면 -14~+14시간의 30분 단위 후보를 검토하되 자동 보정하지 않는다. 역행 쌍 통계는 한정된 개체 표본에 대한 수치다. 중복 단계·재작업·분기·시간대 의미는 확정하지 않는다.

## r3: 발견·관문·판단·요청 근거

- 독립 의미 검토에서 상태가 `FINDING`인 항목마다 `grading.finding_impacts`에 `{item_id,finding_ref,action,metric,before,after,split,grader_sha256}` 또는 `{item_id,unmeasurable_reason}`을 기록한다. 수치 근거의 grader 해시는 현재 평가기 해시와 연결한다. 미측정 사유는 경고이며 성능 개선의 증거가 아니다.
- 현행 유지의 `baseline_assumptions_check`는 `{check,method,result}` 목록이다. `response_shape`, `missing_reference_join`, `progress_variable`, `operating_shift` 중 중복 없는 세 가지 이상을 점검한다.
- `decisions.type_a_choices`는 허용된 업무 주제 `problem_choice`, `miss_vs_overkill`, `speed_vs_precision`, `risk_tolerance`, `final_study_minutes`, `emergency_no_review`와 해시가 연결된 `question_ref`, `answer_ref`를 기록한다. Type B는 AI 선택을 유지하며 `evidence_score:{metric,score,alternative_difference}`에 실제 튜닝 기준과 대안 차이를 남긴다. 점수가 없으면 만들어내지 않는다.
- `external_requests.requests` 각 항목에 hypothesis, target, expected_if_true, expected_if_false, budget_left, layer_check가 필요하다. 회신 전 fallback은 검증된 과제 hard_limits 및 지표 비교과 현재 제출·clean_run 증거가 있을 때만 경고다.
- 기간·출처의 중앙값 비가 10, 100, 1000배 또는 역수의 ±15%에 해당하면 `SCALE_STEP` 후보로 기록한다. 명시된 시간 열이나 첫 시간 열로 주·월을 구분한다. ID·순번 이름 힌트는 숫자 단위 비교에서 제외한다. 표본 근거는 사실·교정의 증명이 아니다.

개체 표본은 최대 2,000개, 개체별 단계는 최대 128개이며 초과 단계는 누락 수를 기록한다. 기간·출처·출처×기간의 축소는 검사별 `analysis_limits` 경고로 남기며 표본 float 예산은 공유한다. 분석 축소는 행 읽기 완료 여부를 바꾸지 않는다. 긴 범주 값은 생략한다. 출처 비교의 범주 값은 보고서에 포함될 수 있으므로 해당 파일의 민감도를 확인한다.

## r3.1: 행 완결성과 분석 한계

`complete_rows`와 `all_provided_rows_examined`는 행 전체를 읽었는지만 표시한다. UNVERIFIED는 행을 다 읽지 못한 경우만, 분석 축소는 경고로 처리한다. 각 파일의 `analysis_limits`는 검사·이유·열·생략 수를 기록하고 `v27_check.py`는 이를 pending이 아닌 warning으로 표시한다. 단 데이터 오류, 파싱 실패 또는 별도 증거 부족은 원래의 FAIL/UNVERIFIED 규칙을 유지한다.

고유값이 50을 넘은 범주 열은 즉시 출처 비교 그룹에서 제거한다. 단위 비교는 기간, 출처, 출처×기간 및 인접 비교의 표본에 합산 2,000,000개 float 예산을 적용한다. 수치 열 최대 512개를 비교하고 `scale_columns` 목록이 있으면 그 열만 지정 순서로 우선한다. 그룹별 표본 크기를 그룹 수에 따라 조정하며 최소 64개를 확보할 수 없는 그룹이나 512개 초과 열은 `analysis_limits`에 기록한다. 사용한 크기는 `scale_sampling`에 남긴다. 출처 중앙값은 자기 자신을 제외한 나머지 출처의 중앙값과 비교하며, 출처별 기간 변화도 검사한다. 시간 열이 없거나 시간순이 확인되지 않으면 파일 순서 인접 비교를 하지 않는다. 범주별 수준이 3배 이상 차이 나는 긴 형식은 항목별 시간 비교로 구분한다.

관측된 숫자가 모두 정수이고 고유값이 50개 이하면서 최댓값이 100 이하이거나 열 이름에 code·bin·item·flag·type·class·status·grade·level이 포함되면 `treated_as_code`로 표시하고 단위 비교에서 제외한다. 이 규칙은 100 이하의 작은 정수 측정값에 생긴 실제 10배 변화를 놓칠 수 있다. 도메인 정보와 원자료로 확인한다.

자동 ID는 표본의 (ID, 순서) 중복률이 가장 낮고 동률이면 서로 다른 ID가 더 많은 열을 선택하며 후보와 수치를 남긴다. 시간대 표시가 한 열에 섞이면 TIMEZONE_MIXED, 시간대 차이로 비교하지 못한 공정 쌍은 출처별 skipped_timezone_mismatch로 기록한다. 순서 역할을 유추하지 못한 시간 열 2개 이상의 입력에는 NOT_RUN과 역할 지정 필요를 표시한다. 모든 경보 및 시차 제안은 실제 현장 판단의 대체가 아니다.

비CSV 표는 제한된 프로파일 범위에서 시간순 확인과 긴 형식의 범주별 인접 비교를 수행한다. 기간·출처 비교는 수행하지 않으며 해당 분석 한계를 경고한다.

## r4-1

hard_limits는 과제 원문 한도만 담는다: {metric, limit, direction, candidate_value, evidence, source_quote}. source_quote는 원문 인용이며 빈 인용은 무효다. 위반은 오류, 계산 불가는 UNVERIFIED 경고다. proxy_metrics는 {metric, direction, baseline_value, candidate_value, relation_to_task_metric, uncertainty}이며 악화는 경고다. 기존 gates는 proxy로 읽고 legacy gate treated as proxy 경고를 낸다.

primary의 task_metric_ref가 있으면 같은 평가 범위에서 과제 지표 악화는 오류다. 없으면 대리 지표로 경고한다. CURRENT_BASELINE은 best_alternative {name, metric_values, rejection_reason, rejection_basis}가 필요하며 rejection_basis는 HARD_LIMIT | TASK_METRIC | SAFETY | OTHER다. OTHER 또는 대리 지표만으로 기각하면 NO_OP 경고다.

해석·독립 리뷰는 통합 스킬의 교체 문장을 따른다. grader controls는 POSITIVE 1~3개와 NEGATIVE 1개 이상이며 독립 지문과 음성 악화 검증은 유지한다. 스냅샷은 첫 E2E(M1)와 최종 두 번만 남기고 후보 비교는 run/CANDIDATES.md만 갱신한다.

.jsonl·.jsonl.gz는 줄 단위로 읽고 키 합집합을 열로, 중첩 값은 JSON 문자열로 둔다. 깨진 줄은 세고 건너뛰며 complete_rows=False다. 미지원 파일은 그 파일만 UNSUPPORTED로 기록하고 나머지 파일과 전체 RECORDED 상태를 유지하며 경고한다.

## r4-2

제약 해석과 데이터 오류 후보 판단을 분리하고, 확정할 수 없는 기록 오류는 보정·그대로 해석을 같은 시간순 자체 검증으로 비교한다. 원본은 보존한다. 자작 제한을 뺀 후보의 과제 지표를 함께 남기고, 평가 조건의 대표성·계산한 관계를 반영한 후보·대리 라벨의 실제 결과 대응을 확인한다. 시스템·에이전트·정책은 최소 기능과 최소 시뮬레이터부터 만든다. 현행 유지는 자동 기본 답이 아니며 best_alternative에는 결과 파일 evidence를 연결하고 metric_values와 일치하는지 읽어 검증한다. 작업자 자리가 모자라면 MAIN이 Recorder를 겸한다.

## r4-3

- clean_run: data_files 사본은 재실행 중에만 읽기 전용(변조 감시)이고, 변조 검사 뒤와 모든 종료 경로(시간 초과·예외)에서 소유자 쓰기 권한을 되돌린다. Windows 정리 단계가 읽기 전용 사본 때문에 중간에 실패하지 않게 하기 위함이다. 복원 실패는 결과 errors에 남긴다. 재실행 폴더는 보존한다.
- 추정값으로 판정하는 과제 한도: 추정기를 실제 결과와 대조해 편향·오차 폭을 잰다. 기대 과제 점수는 과제에 적힌 감점 규칙에만 쓰고(감점 공식을 지어내지 않음), 탈락형·감점 미공개 한도는 잰 오차의 위쪽 끝(단측 95%)이 한도 안인 운영점에서 고른다. 대조할 실제 결과가 없으면 추정값으로 "한도 안"이라 판정하지 않고 다른 신호를 찾거나 한도에서 떨어진 운영점을 고른다. 잰 오차에서 나온 여유는 자작 제한이 아니다. r4-2 자작 제한 목록의 "추가 안전 여유"는 "측정한 추정 오차에 근거하지 않은 추가 여유"로 좁혔다.
- 이벤트 종류: 정비·교체·세정·부품 교체의 효과를 종류별로(직후 일시 구간 포함) 추정하고, 기록에 빠진 이벤트는 센서·결과 계단으로 찾아 넣은/뺀 후보를 같은 자체 검증으로 비교한다.

## r4-3.1 (레드팀 반영)

- 한도 줄을 둘로 나눔: 감점 규칙이 적힌 한도만 기대 점수, 탈락형·미공개는 오차 위쪽 끝 기준. 실제 결과로 검증 못 하면 다른 신호 → 한도에서 떨어진 운영점.
- 무응답 규칙: 다른 해석에서 실격이 생길 때만 공통안, 그 밖에는 목표에 맞는 해석의 최선안 + 다른 해석 지표를 한계에.
- 비교 규칙은 현상이 보일 때만, 당일 환경은 공식 규칙 문서에서 먼저 찾고 없는 칸만 참가자에게 한 번에 물어 일정 재계산(`--observe-now`), 예산 사용, 읽기 순서, 시작 문서 누락 대비, UTF-8 명시·`--help`.
- v27_check.py에 `--output`(결과 JSON 파일 저장) 추가.

## r4-3.2

- data_audit: 시트를 지정하지 않은 엑셀은 모든 시트를 감사하고, 표가 아닌 시트(병합 셀·여러 줄 머리글·메모)는 `skipped_sheets`에 사유와 함께 남겨 파일 전체를 FAIL로 만들지 않는다(그 파일은 UNVERIFIED). 기록 배열이 여러 개인 JSON은 배열마다 감사한다. 시트·배열 지정 오류에는 계획 파일 문법(`{"path": ..., "sheet": ...}` / `{"path": ..., "records_key": "/키"}`)을 함께 보여 준다. CSV 경로는 바뀌지 않는다.

## r4-3.3

- JSONL 감사의 변환용 임시 폴더: 시스템 임시 폴더를 먼저 쓰고, 만들기나 쓰기가 막히면(Codex 샌드박스) 설치된 키트의 `run/.v27-tmp` 아래를 쓴다. 쓰고 나면 지운다.

## r4-3.4

- 구간별 표본 수: 표본이 적은 구간의 "효과 없음"만으로 항을 빼지 않는다(물리적으로 있는 효과는 남긴 후보와 비교).
- 진단 목록 정밀도: 근거 수치가 있는 항목만 findings에, 약한 의심은 "확인 필요"로.
- 설정이 바뀌는 시스템: 더 엄격한 설정에서 추정 오차를 다시 재고, 대조할 수 없으면 한도에서 더 떨어진 운영점.

## r4-3.6

- 반려·0점·실격 조건의 적용 범위가 모호하면: 출처·집계 경로 차이만으로 해당 없음으로 정하지 않고, 닿을 수 있는 칸은 공통안(문서가 정한 표기·보류). 적힌 배점상 공통안 손실이 더 클 때만 예외(계산 기록).
- 시스템 입력: 깨진 기록·샘플과 다른 형식은 그 기록만 격리하고 나머지 처리. 전체 거부는 과제 문서가 정한 거부 조건일 때만. 깨진 행·다른 형식 칸을 넣은 묶음으로 자체 시험.
- 탈락형 한도 여유: 잰 오차 분포의 단측 95% 위쪽 끝. 이력 최대 오차를 여유로 쓰면 그 운영점 지표를 CANDIDATES.md에 함께 기록.

## r4-3.7 (외부 검토 반영)

- JSONL 감사 임시 폴더 대체 경로: run/ 또는 run/.v27-tmp가 키트 밖으로 이어지는 링크·junction이면 쓰지 않고 오류로 처리한다(그 파일은 RECORDED가 아니다).
- 지식 참고자료의 포화(상·하한) 규칙: 실제 적용한(잘린) 설정값으로 상태 갱신, 적분형은 포화를 깊게 하는 방향일 때만 적분 정지(조건부 적분).
- 단측 95% 위쪽 끝: (실제 − 추정) 오차 또는 표준화 오차 z의 분포에서 구한다(계산 규칙은 r4-3.8 절).

## r4-3.8 (외부 검토 반영)

- 단측 95% 위쪽 끝은 정규분포를 가정하지 않는다(r4-3.9 절에서 표본 크기별 규칙과 표준오차 정의를 보완).

## r4-3.9 (외부 검토 반영)

- 단측 95% 위쪽 끝 계산 규칙(SKILL 한도 규칙 바로 다음 줄과 같다):
  - 대상: (실제 − 추정) 오차, 또는 z = (실제 − 추정) ÷ 그 항목의 예측 표준오차. 평균의 표준오차(표준편차 ÷ √n)를 쓰지 않는다(여유가 1/√n로 줄어 한도에 붙는다).
  - n ≥ 20: 경험적 95% 분위수(정렬 후 올림(0.95 × n)번째 값)와 평균 + 1.645 × 표준편차 중 큰 쪽. 두 값 기록.
  - n < 20: 경험적 분위수는 최댓값과 같아지므로 쓰지 않는다. 평균 + t(0.95, n − 1) × 표준편차 × √(1 + 1/n)(정규 근사 예측 한계, 한계로 기록).
  - z를 썼으면 고른 값 × 그 항목의 예측 표준오차를 추정에 더한다(z 값 자체는 단위 없는 배수다).
  - 단측 t(0.95, 자유도): 1 6.314 / 2 2.920 / 3 2.353 / 4 2.132 / 5 2.015 / 6 1.943 / 7 1.895 / 8 1.860 / 9 1.833 / 10 1.812 / 11 1.796 / 12 1.782 / 13 1.771 / 14 1.761 / 15 1.753 / 16 1.746 / 17 1.740 / 18 1.734 / 19 1.729
- 반려·0점 규칙 줄의 예시를 특정 과제와 무관한 일반 문구로 바꿨다.
- 지식 참고자료의 포화 규칙을 제어기 종류별로 나눴다: 상태 추정형(EWMA·런투런)은 실제 적용한(잘린) 설정값으로 계속 갱신하고 멈추지 않는다. 적분형(PI)은 포화를 깊게 하는 방향일 때만 그 단계 적분을 건너뛴다. 한 상태에 두 방식을 섞지 않는다.
- JSONL 임시 폴더 대체 경로 검사: 경로 비교를 실제 경로(링크·junction 해석, \\?\ 접두 제거, 대소문자 정규화)로 하고, 만든 뒤 검사에서 어떤 예외가 나도 만든 폴더를 지운다.
