# v2.7 추가 계약

이 문서는 `hackathon-orchestrator-universal`의 기계 기록과 운영 절차를 연결한다. 먼저 `v27-r81-map.md`에서 기존 계약을 확인한다. 현재 기준은 r8.2이며 `v27-baseline.json`은 기존 112개 파일의 SHA256과 기존 STATE 키를 기록한다. 해시는 파일 무결성을 검사하며 작성자나 이벤트 진위를 인증하지 않는다.

## 환경과 시간

설치 시 `.hackathon-kit/run/ENV.md` 등 신규 템플릿을 초기화한다. 이미 작성한 기록은 보존한다. 각 스위치의 `classification`은 `CONFIRMED`, `PLAN_DEFAULT`, `UNKNOWN` 중 하나다. 확정에는 작업 폴더 안의 원문 경로·해시·정확한 발췌를 연결한다. 계획값은 허용 증거가 아니다. 날짜 시각은 ISO 8601 시간대 포함 형식으로 기록한다.

현재 전달된 안내문은 경기 09:30–16:00, 좌석 점심 12:00–13:00, 이후 키노트와 Top20 피칭을 안내한다. 이 일정만으로 실제 제출 확정 마감이나 본선 후속 평가를 확정하지 않는다. 모델은 현재 사용 가능 목록, 공식 허용·제한, 역할별 실제 배정을 구분한다. 모델 이름이나 성능 순위를 미리 고정하지 않는다. 예선 Astra 제한은 미확인 본선의 준비 가정으로만 보존한다.

```text
python -I .hackathon-kit/scripts/deadline.py --input .hackathon-kit/run/ENV.md
```

`deadline.calculate()`는 `FOLLOWUP=FIXED_TIME|AFTER_CONFIRM|NONE`을 계산한다. S=60, R≥10, C=40은 계획 기본값이다. 학습 축소에는 실제 참가자 선택이 필요하다. NONE에서 S_pre=0은 확인된 피칭 전 학습 가능 시간도 필요하다. 마감이 없으면 UNKNOWN이며 임의로 16시를 대입하지 않는다. `--observe-now`는 실제 시스템 시각을 추가해 이미 지난 CP3 시작을 거부한다. 계산 결과는 V27_STATE의 `deadline`에만 기록하고 기존 STATE의 공식 마감과 섞지 않는다.

## 증거와 단계

`V27_EVIDENCE.json`은 증거 색인이다. 각 `records` 값은 `{path, sha256}`이며 문서는 JSON 또는 정확히 한 개의 JSON 코드 블록을 사용한다. 템플릿은 미완성 상태로 배포되며 통과 증거가 아니다.

```text
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase intake
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase cp1
python -I .hackathon-kit/scripts/v27_check.py --root . --plan .hackathon-kit/run/V27_EVIDENCE.json --phase final
```

인수 검사는 환경과 별도 상태를 확인한다. CP1은 데이터 감사·채점·결정·안전 및 CONSTRAINT_RED/DATA_EVAL_RED의 실제 실행을 확인한다. 최종 검사는 여섯 핵심 RED와 조건부 SECURITY_RED의 CP3 집계, 최신 제출·보안·복사 재실행·학습 기록을 추가 확인한다. CP2 리뷰와 실질 변경 후 재검사는 기존 본선 절차를 따른다. M1/M2/M3는 보관 시점이며 추가 리뷰 관문이 아니다. 본선에 예선 CP1의 고정 문서 게이트를 강요하지 않는다.

독립 리뷰는 기존 `review_execution.py`와 `finals_review_check.py` 계약을 재사용한다. 깨끗한 별도 작업자 컨텍스트와 실제 LAUNCHED/RUNNING/COMPLETED 관측·보고서·검토 파일 해시가 필요하다. 생성 계획, 본체의 셀프 체크, 완료 문구만으로 대체하지 않는다. 실행 불가 때 미실행이라고 보고한다. SECURITY_RED는 실제 인증·권한·비밀·외부 데이터/서비스 경로·특권 도구·민감 자료 경계가 있을 때 발동한다. P1/P0 발견은 수정 검증 또는 근거 있는 반증으로 닫는다.

`submission`, `security`, `clean_run` 참조에는 추가 `execution:{path,sha256}`가 필요하다. 해당 JSON은 실제 도구 호출의 `{tool:"exec_command",argv:[실제 인터프리터 절대경로,"-I",도우미 절대경로,...],request:{cmd:...},result:{exit_code:0,output:실제 JSON stdout}}`을 보존한다. `argv`는 실제 명령의 구조화된 사본이다. 단일 명령을 `subprocess.list2cmdline(argv)` 또는 `shlex.join(argv)`로 렌더링하고 PowerShell이면 앞에 `& `를 붙일 수 있다. 이 렌더링과 실제 cmd가 같아야 한다. 인터프리터는 실행 중 Python의 `sys.executable` 실제 경로를 사용하며, `--root`와 현재 `--rules`/`--plan` 경로를 명시한다. 셸 블록·별칭·`-c`를 대신 쓰지 않는다. 실제 stdout이 결과 문서와 일치해야 하며 기록 자체를 스크립트가 생성한 결과로 가장하지 않는다.

## 데이터와 채점

명시 입력만 `data_audit.py --root . --plan audit-plan.json`으로 조사한다. 파일 경로·바이트/행 한도를 고정하며 저장소 전체를 재귀 조사하지 않는다. 10개 항목은 적용 여부·방법·관측·조치·한계를 기록한다. 의미를 검증하지 못한 항목을 통과로 만들지 않는다. 시간형 컬럼이 있으면 시간 무관 N/A를 막는다. DATA_AUDIT 템플릿과 V27_EVIDENCE의 계획 스키마를 따른다.

공식 grader가 우선이다. 없을 때만 작은 자체 채점기를 작성한다. 수치 점수를 얻을 수 없으면 `UNAVAILABLE_WITH_REASON`으로 기록한다. 자체 채점기 사용 시 요구사항에서 독립적으로 도출한 3–5개 정답 사례, 계약상 틀린 사례, 실행 결과와 실제 metric을 남긴다. 0벡터 등은 문제에 따라 정답일 수도 있으므로 자동으로 오답 취급하지 않는다. holdout을 보고 후보를 고르면 첫 사용부터 튜닝 데이터다. 4회 이상 조회 경고도 유지하되 첫 3회를 독립 검증이라고 주장하지 않는다.

## 제품 검사와 보관

각 CLI의 `--help`가 인수 계약이고 함수의 plan/rules는 해당 테스트의 작은 실행 예제로 확인할 수 있다. 결과 출력은 stdout이며 명시 `--output`만 파일을 만든다. 검사 대상·원자료를 출력 경로로 지정하지 않는다.

- `submit_check.py --root . --rules rules.json`: 명시한 파일의 JSON/CSV/text 형식, 필드, 열, 행 수, 허용 값·범위·유일 키·합계 제약과 총 용량을 검사한다. 공식 규칙을 자동 추측하지 않는다.
- `clean_run.py --root . --plan plan.json --scratch 새임시폴더`: 명시한 후보·허용 자료를 복사하고 `execution_authorized:true`인 명령만 실행한다. 출력의 기준 해시 또는 JSON 수치 허용오차를 비교한다. 의존성 설치·셸·Git·외부 전송을 자동 수행하지 않는다. 실행 허용은 sandbox를 뜻하지 않으며 파일 권한이나 네트워크를 OS 수준에서 격리하지 못한다.
- `security_check.py --root . --plan plan.json`: 명시 파일만 크기 제한으로 검사한다. 비밀/개인정보 패턴과 위험 호출 후보를 값 노출 없이 보고하고 근거 있는 disposition을 기록한다. 동적 공격·권한 전체·누출 부재를 보증하지 않는다.
- `snapshot.py create --help` 및 `verify --help`: 명시 파일을 로컬 보관하고 원자료는 해시만 기록한다. M1과 FINAL 및 최근 5개를 유지한다. 복사본은 읽기 전용이고 원본 권한은 바꾸지 않는다. 읽기 전용은 사용자나 프로세스가 해제할 수 있으며 장치 장애를 대비한 독립 백업이 아니다.

깨끗한 재실행이나 규격 검사 통과만으로 공식 제출 확정 영수증을 대신하지 않는다. 최종 파일을 변경하면 관련 검사와 리뷰 범위를 갱신한다. 입출력 경로·해시·원래 안전 경계를 바꾸는 수정은 시간 부족만으로 생략하지 않는다.

## 참가자 이해와 학습

Type A는 실제 업무 판단·위험 수용·학습 시간 선택처럼 참가자 결정이 필요한 사안이다. Type B는 AI가 기술을 선택하고 선택한 이유·대안·예제·설정 변경 영향·한계를 먼저 설명하는 기록이다. 모든 기술 선택을 승인 질문으로 바꾸지 않는다. 참가자의 이해나 회상 성공은 AI가 대신 인증하지 않는다.

중간 10/5/10분과 최종 S=60분을 계획한다. 학습 블록에서 모델이나 알고리즘을 바꾸지 않는다. STUDY_BRIEF는 실제 코드·검사·결정에만 근거하고 `PREPARED`와 실제 전달 `DELIVERED`를 구분한다. 공식 본선의 후속 평가가 미확인이면 연습 문항을 공식 6문항이라고 부르지 않는다. WHITEBOARD·MAINTENANCE·PITCH_NOTES는 필요한 경우 사용하는 보조 문서다.

## 보존과 배포

`install_v27.py`는 원래 설치기의 소유권·충돌 보존을 재사용하고 추가 파일 존재/해시를 확인한다. `package_v27.py`는 원래 패키저의 허용 목록에 명시된 신규 지도·계약·보호 JSON을 더한다. 기존 112개 파일 및 EXAM_POLICY와 기존 STATE 키는 보존한다. `--source`를 제공한 v27_check도 보호 해시를 읽기 전용 확인한다. 이 자기 기재 manifest는 신뢰할 수 있는 배포 SHA와 함께 확인해야 한다.

P2 튜닝·변경 실험·피칭 검사 자동화는 구현하지 않았다. P1이 증거의 의미적 진실, 숨은 점수, 참가자의 기억, 모든 공격, 실제 접수 성공을 증명한다고 주장하지 않는다.
