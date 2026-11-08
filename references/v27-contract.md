# v2.7 추가 계약

이 문서는 `hackathon-orchestrator-universal`의 기계 기록과 운영 절차를 연결한다. 먼저 `v27-r81-map.md`에서 기존 계약을 확인한다. 현재 기준은 r8.2이며 `v27-baseline.json`은 기존 112개 파일의 SHA256과 기존 STATE 키를 기록한다. 해시는 파일 무결성을 검사하며 작성자나 이벤트 진위를 인증하지 않는다.

## 환경과 시간

설치 시 `.hackathon-kit/run/ENV.md` 등 신규 템플릿을 초기화한다. 이미 작성한 기록은 보존한다. 각 스위치의 `classification`은 `CONFIRMED`, `PLAN_DEFAULT`, `UNKNOWN` 중 하나다. 확정에는 작업 폴더 안의 원문 경로·해시·정확한 발췌를 연결한다. 계획값은 허용 증거가 아니다. 날짜 시각은 ISO 8601 시간대 포함 형식으로 기록한다.

현재 전달된 안내문은 경기 09:30–16:00, 좌석 점심 12:00–13:00, 이후 키노트와 Top20 피칭을 안내한다. 이 일정만으로 실제 제출 확정 마감이나 본선 후속 평가를 확정하지 않는다. 모델은 현재 사용 가능 목록, 공식 허용·제한, 역할별 실제 배정을 구분한다. 모델 이름이나 성능 순위를 미리 고정하지 않는다. 예선 Astra 제한은 미확인 본선의 준비 가정으로만 보존한다.

```text
python -I .hackathon-kit/scripts/deadline.py --input .hackathon-kit/run/ENV.md
```

`deadline.calculate()`는 `FOLLOWUP=FIXED_TIME|AFTER_CONFIRM|NONE`을 계산한다. S=60, R≥10은 계획 기본값이다. C를 직접 지정하면 그 값을 쓰고 `c_basis`에 명시한다. 지정하지 않으면 `FIX_BUFFER + REVIEW_MINUTES_EACH × 배치 수`로 계산한다. 기본은 여유 20분 + 10분 × 7개 순차 리뷰 = 90분이다. REVIEW_PARALLEL=YES일 때만 한 배치로 계산해 기본 30분이며 NO/UNKNOWN은 순차다. SECURITY_RED의 NOT_TRIGGERED를 확인한 경우에만 FINAL_REVIEW_ROLES를 6으로 갱신한다. 기본 7은 조건부 보안 리뷰까지 준비하는 가정이다.

학습 축소에는 실제 참가자 선택이 필요하다. NONE에서 S_pre=0은 확인된 피칭 전 학습 가능 시간도 필요하다. 템플릿의 T_SUB·WINDOW_END=16:00은 참가자가 전달한 경기 종료 시각을 쓴 PLAN_DEFAULT이며 공식 제출 확정 마감이 아니다. 그래서 계획은 KNOWN으로 계산하되 v27_check의 공식 마감 보류는 유지한다. 값 자체가 없으면 UNKNOWN이다. PAUSE 점심과 CP3 시작~작업 잠금이 겹치면 경고만 출력하고 일정을 자동 이동하지 않는다.

`--observe-now`는 실제 시스템 시각을 추가한다. CP3 시작 이후에도 남은 일정을 출력하고 지난 항목은 `passed`와 경고에 남긴다. 확정 마감을 지난 경우에만 `PAST_CONFIRMATION`과 종료 코드 1을 반환한다. 계산 결과는 V27_STATE의 `deadline`에만 기록하고 기존 STATE의 공식 마감과 섞지 않는다.

## 증거와 단계

`V27_EVIDENCE.json`은 증거 색인이다. 각 `records` 값은 `{path, sha256}`이며 문서는 JSON 또는 정확히 한 개의 JSON 코드 블록을 사용한다. 템플릿은 미완성 상태로 배포되며 통과 증거가 아니다.

```text
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase intake
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase cp1
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase final
```

인수 검사는 환경과 별도 상태를 확인한다. CP1은 데이터 감사·채점·결정·안전 및 CONSTRAINT_RED/DATA_EVAL_RED의 실제 실행을 확인한다. 최종 논리 단계 CP3에서는 기존 `checkpoint: FINAL` 계획·영수증을 그대로 두 검사에서 쓴다. 여섯 핵심 RED와 조건부 SECURITY_RED의 FINAL 집계, 최신 제출·보안·복사 재실행·학습 기록을 추가 확인한다. CP1·이전 CP2 기록의 이름은 그대로다. M1/M2/M3는 보관 시점이며 추가 리뷰 관문이 아니다. 본선에 예선 CP1의 고정 문서 게이트를 강요하지 않는다.

독립 리뷰는 기존 `review_execution.py`와 `finals_review_check.py` 계약을 재사용한다. 깨끗한 별도 작업자 컨텍스트와 실제 LAUNCHED/RUNNING/COMPLETED 관측·보고서·검토 파일 해시가 필요하다. 생성 계획, 본체의 셀프 체크, 완료 문구만으로 대체하지 않는다. 실행 불가 때 미실행이라고 보고한다. SECURITY_RED는 실제 인증·권한·비밀·외부 데이터/서비스 경로·특권 도구·민감 자료 경계가 있을 때 발동한다. P1/P0 발견은 수정 검증 또는 근거 있는 반증으로 닫는다.

`submission`, `security`, `clean_run` 참조에는 추가 `execution:{path,sha256}`가 필요하다. 해당 JSON은 실제 도구 호출의 `{tool:"exec_command",argv:[실제 인터프리터 절대경로,"-I",도우미 절대경로,...],request:{cmd:...},result:{exit_code:0,output:실제 JSON stdout}}`을 보존한다. tool은 ENV의 EXECUTION_TOOLS 목록으로 확인하며 기본은 `["exec_command"]`라는 PLAN_DEFAULT다. 실제 플랫폼의 도구 이름을 확인하면 예를 들어 `bash`를 추가하고 동일한 구조·명령·현재 파일 검사를 적용한다. 목록에 없는 도구 또는 `MANUAL_TRANSCRIPT`는 실행 확인 불가로 UNVERIFIED이며 PASS로 승격하지 않는다. 별도의 실제 파일 변경·잘못된 형식은 계속 FAIL이다.

`argv`는 실제 명령의 구조화된 사본이다. 단일 명령을 `subprocess.list2cmdline(argv)` 또는 `shlex.join(argv)`로 렌더링하고 PowerShell이면 앞에 `& `를 붙일 수 있다. 이 렌더링과 실제 cmd가 같아야 한다. 인터프리터는 실행 중 Python의 `sys.executable` 실제 경로를 사용하며, `--root`와 현재 `--rules`/`--plan` 경로를 명시한다. 셸 블록·별칭·`-c`를 대신 쓰지 않는다. 실제 stdout이 결과 문서와 일치해야 하며 기록 자체를 스크립트가 생성한 결과로 가장하지 않는다.

## 데이터와 채점

명시 입력만 `data_audit.py --root . --plan audit-plan.json`으로 조사한다. 파일 경로·바이트/행 한도를 고정하며 저장소 전체를 재귀 조사하지 않는다. 10개 항목은 적용 여부·방법·관측·조치·한계를 기록한다. 의미를 검증하지 못한 항목을 통과로 만들지 않는다. 시간형 컬럼이 있으면 시간 무관 N/A를 막는다. DATA_AUDIT 템플릿과 V27_EVIDENCE의 계획 스키마를 따른다.

공식 grader가 우선이다. 없을 때만 작은 자체 채점기를 작성한다. 수치 점수를 얻을 수 없으면 `UNAVAILABLE_WITH_REASON`으로 기록한다. 자체 채점기 사용 시 요구사항에서 독립적으로 도출한 3–5개 정답 사례, 계약상 틀린 사례, 실행 결과와 실제 metric을 남긴다. 0벡터 등은 문제에 따라 정답일 수도 있으므로 자동으로 오답 취급하지 않는다. holdout을 보고 후보를 고르면 첫 사용부터 튜닝 데이터다. 4회 이상 조회 경고도 유지하되 첫 3회를 독립 검증이라고 주장하지 않는다.

## 제품 검사와 보관

각 CLI의 `--help`가 인수 계약이고 함수의 plan/rules는 해당 테스트의 작은 실행 예제로 확인할 수 있다. 결과 출력은 stdout이며 명시 `--output`만 파일을 만든다. 검사 대상·원자료를 출력 경로로 지정하지 않는다.

- `submit_check.py --root . --rules rules.json`: 명시한 파일의 JSON/CSV/text 형식, 필드, 열, 행 수, 허용 값·범위·유일 키·합계 제약과 총 용량을 검사한다. 공식 규칙을 자동 추측하지 않는다.
- `clean_run.py --root . --plan plan.json --scratch 새임시폴더`: 명시한 후보·허용 자료를 복사하고 `execution_authorized:true`인 명령만 실행한다. 출력의 기준 해시 또는 JSON 수치 허용오차를 비교한다. 의존성 설치·셸·Git·외부 전송을 자동 수행하지 않는다. 실행 허용은 sandbox를 뜻하지 않으며 파일 권한이나 네트워크를 OS 수준에서 격리하지 못한다.
- `security_check.py --root . --plan plan.json`: 명시 파일만 크기 제한으로 검사한다. 비밀/개인정보 패턴과 위험 호출 후보를 값 노출 없이 보고하고 근거 있는 disposition을 기록한다. 동적 공격·권한 전체·누출 부재를 보증하지 않는다.
- `snapshot.py create --help` 및 `verify --help`: 명시 파일을 로컬 보관하고 원자료는 해시만 기록한다. M1과 FINAL 및 최근 5개를 유지한다. 복사본은 읽기 전용이고 원본 권한은 바꾸지 않는다. 읽기 전용은 사용자나 프로세스가 해제할 수 있으며 장치 장애를 대비한 독립 백업이 아니다.

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

- baseline_comparison: `AVAILABLE`일 때 `metric`, `direction` (`HIGHER_IS_BETTER` 또는 `LOWER_IS_BETTER`), 유한한 `baseline_value`/`candidate_value`, `selection`, `shared_scope_evidence`, `baseline_evidence`, `candidate_evidence`를 기록한다. 두 점수 JSON은 각각 `{metric,value,scope,artifact:{path,sha256}}`를 갖고 scope는 공통 범위 JSON과 일치해야 한다. 후보 artifact는 현재 clean_run 산출물이어야 하며 현행 유지일 때 기준선 artifact와 SHA256이 같아야 한다. 더 나쁜 후보는 FAIL. 평가가 불가능하면 `UNAVAILABLE_WITH_REASON`과 이유를 남기며 최종 검사는 UNVERIFIED다. 수치만 같고 조건이 다르면 비교로 취급하지 않는다. 선택이 `CURRENT_BASELINE`이면 `alternatives`에 서로 다른 두 `name`, `assumptions`, `result`, `evidence`와 `baseline_assumptions_check`가 필요하다. 현행의 합법성·안전성은 별도로 확인한다.
- external_requests: `{status:NONE}` 또는 `{status:TRACKED,requests:[...]}`를 기록한다. 각 요청은 `PENDING` 또는 `RECEIVED`이고 RECEIVED는 `response_evidence`를 연결한다. PENDING은 최종 검사를 UNVERIFIED로 유지한다. 채팅의 발송·응답 기록을 실제 근거로 보존하며, 대기 중에는 다른 독립 작업을 계속한다.
- maintenance: `runs`에 서로 다른 두 개 이상의 `{id,change,before_config,after_config,program,execution,observed_output,status:PASS,verification}`을 기록한다. 파일 참조는 해시를 포함하며, 두 설정의 바이트가 달라야 한다. 실제 native 실행은 `-I` Python으로 기록된 프로그램 및 변경 설정 파일을 사용하고 stdout JSON이 observed_output과 같아야 한다. 이 검사는 실행 기록과 파일 무결성만 검사하며 테스트 자체의 품질·OS 격리·인간 판단을 인증하지 않는다. 서로 다른 두 변화와 기대 관계를 요구하고 적절한 검토자가 내용을 검증한다.
- `decisions.type_b_cards`는 설명 기록이며 `selection_by:AI`를 명시한다. `selection_by:PARTICIPANT` 또는 `participant_approval_required:true`는 기술 결정을 참가자에게 전가하므로 FAIL이다. Type A 업무·위험 판단은 이 제한과 구별한다.
- 전체 데이터 감사는 명시적으로 제공된 파일만 대상으로 기본 최대 1,000,000행이다. `max_rows`, `max_file_bytes`, `max_decompressed_bytes`의 안전 한도를 넘으면 부분 검사 또는 오류를 기록하고 최종 통과로 바꾸지 않는다. gzip 원본의 압축 해제 상한은 64MiB다. 시각 역행·단위 계단은 후보 경보일 뿐, 이름·행 순서·누락·혼합 시간대·제품 구성에 따라 거짓 양성 또는 누락이 가능하다. 데이터의 실제 공정 순서·동일 개체·단위 개정 근거는 별도 확인한다.

같은 wafer_id의 step_seq가 앞선 공정 종료와 다음 공정 시작을 교차 비교하는 경우도 후보로 기록한다. 중복 단계·재작업·분기·시간대 의미는 확정하지 않는다.
