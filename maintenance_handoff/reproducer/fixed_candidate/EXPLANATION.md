# 운영문서 근거검색 구현 설명

고객지원 담당자가 등록 고객사의 접근 범위 안에서 기준일에 유효한 최신 문서를 찾도록 만들었다. 상담 답변을 생성하거나 외부 AI/API에 연결하지 않는다. Python 표준 라이브러리와 sqlite3만 사용하며 `kb.py`가 `src/kb_service.py`를 실행한다.

## 마지막 정책 공지와 현재 결과

현재 유효 정책은 별도 모의 공지 `communications/official-policy-update.json`의 **KB-UPD-1**, 최대 결과 **3개**, 효력 시각 `2026-11-02T00:00:00+09:00`이다. 실제 SK 운영진의 공지가 아니다. 원래 DATA/policy.json과 이전 KB-BASE-1/max5 인덱스·답안·검증 기록은 보존했다. 접근 범위·버전 선택·점수·동률 순서·개정번호 정정은 바뀌지 않았다.

새 정책 파일을 --policy로 넘겨 **새 sample/full 인덱스와 답안을 실제로 다시 생성**했다. 이전 답안을 현재 결과로 재사용하지 않았다. 현재 별도 정책 검사는 **12/12 PASS**이며, sample80행/full1500행의 새 답안은 모두 canonical 입력 순서·KB-UPD-1·최대3개를 만족했다. 원래 공개 first12의 정책 ID를 바꾸고 기존 순서 앞3개만 취한 독립 기대값과 새 sample first12가 정확히 일치했다. 이는 변경하지 않은 점수·접근·순위 규칙에만 근거한 공개12개 검증이며, full 정답은 여전히 미공개다. 이전 공개 smoke10/10은 이전 max5 정책의 기록으로만 남긴다.

현재 max3 full build는 종료0/5.698초/최대RSS245308KiB, search는 종료0/0.964초/106168KiB였다. sample/full verify와 동일정책 resume가 모두 성공했고 번들 바이트·수정 시각이 유지되었다. 원래 DATA 정책 두 파일은 바이트 해시가 그대로다. 과거 max5 정책을 명시한 search는 종료2로 sentinel을 보존했고 serve도 포트 바인딩 전에 불일치 정책을 거절했다. HTTP health/stats/정상질의/HTML에서 KB-UPD-1·최대3개를 확인했으며 새 q1은 정확히3개였다. 두 번들의 현재 정책 fingerprint는 `f4b27816b6b9ca3a1f9ca529db522d6f7b47f039f9dd50ba18083d77a19d047f`다.

## 실행과 데이터 흐름

```text
python kb.py build --input data/sample --out work/example-index --policy communications/official-policy-update.json
python kb.py search --index work/example-index --queries queries/sample.jsonl --out work/example-answers.jsonl --policy communications/official-policy-update.json
python kb.py verify --index work/example-index
python kb.py serve --index work/example-index --host 127.0.0.1 --port 8000 --policy communications/official-policy-update.json
```

입력 파일 목록·바이트 해시 수집 → CP949 고객사/UTF-8 태그 및 유효 정책 확인 → 문서행 검증과 최초 유효 record_id 예약 → 최신 버전 선택 → SQLite와 집계/manifest → 고객사별 태그 검색 → canonical JSONL 또는 HTTP 응답 순서다. 정책 전체를 `--policy`로 바꿀 수 있고, 검색/서버에 지정한 정책 지문이 인덱스와 다르면 출력 교체 또는 포트 바인딩 전에 종료 코드 2로 거절한다.

문서는 상대 경로의 UTF-8 바이트 순서와 물리 행 순서로 읽는다. 첫 물리 행 BOM과 행 끝 LF/앞 CR을 제외한 payload를 기준으로 공백 무시, 65,536바이트 초과, JSON, 스키마, 미래 시각, 중복 ID 순으로 한 번만 판정한다. 중복 JSON 키와 비유한 숫자를 거부하며 bool을 정수로 인정하지 않는다. 식별자·본문·태그의 대소문자, 공백, Unicode 표기를 바꾸지 않는다. 새 모의 정정 REVISION-RANGE-ERRATUM-1에 따라 revision은 bool이 아닌 0..9223372036854775807 정수이며 범위 밖 행을 FUTURE/중복 판정보다 앞선 BAD_SCHEMA로 처리한다. 태그 가중치와 query limit에는 이 revision 상한을 적용하지 않는다. 원문이 허용하는 정확한 정수를 처리하도록 Python 정수의 4300자리 기본 변환 제한과 CSV의 131072문자 기본 필드 제한을 제거했다. META의 예상 행 수는 집계값으로 사용하지 않는다.

## 버전 선택과 실제 사례

같은 `(tenant_id, doc_id)`에서 revision이 크고, 같으면 timezone-aware datetime의 실제 updated_at이 늦은 행을 선택한다. 값이 모두 같으면 먼저 읽은 행을 유지한다. published_at은 미래 여부에만 쓴다. 선택된 최신 행이 WITHDRAWN이면 이전 PUBLISHED를 다시 살리지 않는다.

실제 소형 검사에서는 고객사 a의 문서 A에 같은 record_id `reserved`가 네 번 나왔다. 공백 제목은 BAD_SCHEMA, 미래 updated_at은 FUTURE였으므로 ID를 예약하지 않았다. 세 번째 유효 revision 1을 보존했고, 네 번째 revision 99는 이미 예약된 ID라 DUPLICATE_RECORD_ID로 거부했다. 실제 DB에는 A의 revision 1이 남았다. 별도 문서 withdraw는 공개 revision 2 뒤의 철회 revision 3이 최신이라 DB 검색 대상에서 제외되었다. 선택 키 6개 중 공개 5개, 철회 1개가 관찰되었다. 같은 revision의 `09:00:00.000001+09:00`과 `00:00:00.000002Z`도 실제 순간을 비교하여 뒤의 행을 선택했다.

## 저장, 검색과 파일 보호

필수 docs/meta 스키마에 선택된 공개 문서, 전체 등록 고객사와 태그 가중치를 저장한다. 원본 태그 배열의 순서와 중복을 보존한다. 조회는 SQLite를 읽기 전용 immutable 모드로 열고 DB를 닫은 뒤 메모리의 고객사·태그 목록으로 처리한다. 별도 가속 테이블이 없는 공개 스키마 독립 번들도 동작한다.

등록 고객사는 자기 고객사와 `__public__` 문서만 볼 수 있다. 미등록 고객사와 질의 고객사 `__public__`는 FORBIDDEN이다. 중복 질의 term과 문서 tag는 각각 한 번만 계산하여 서로 다른 일치 태그 가중치를 합한다. 양수 점수만 점수 내림차순, doc_id UTF-8 바이트, tenant_id UTF-8 바이트 순으로 정렬한다. limit과 정책 max_results 중 작은 수까지 반환한다. snippet은 원문 `body[:80]`이고 HTML 문자와 줄바꿈을 그대로 보존한다.

build는 완성된 임시 디렉터리를 공개하고 search는 전체 질의를 성공적으로 처리한 임시 파일만 교체한다. 오류 시 기존 답안을 보존한다. 원본/인덱스와 겹치는 출력, symlink, 특수 파일, hardlink 및 보호 원문 출력을 거절한다. 제공 경로 밖의 DATA도 보호하도록 선택적 `source_protection` 테이블에 원래 DATA 경로와 파일의 device/inode를 기록한다. 원본 파일이 이동해도 같은 파일 식별자를 가진 출력은 거절한다. 별도 외부 --policy 파일도 전체 부모 디렉터리를 막지 않고 그 파일의 정확한 경로와 device/inode만 기록한다. 자신의 형식 표식이 있는 번들에서만 보호 테이블을 해석하므로, 무관한 추가 테이블 source_protection(note TEXT)을 가진 독립 번들도 필수 docs/meta로 조회·검증할 수 있다.

verify는 원본 DATA 없이 canonical JSON, 필드/타입, 산출물 해시와 내부 fingerprint, 필수 SQLite 스키마, 고객사·태그 membership, DB 문서 수와 집계 불변식을 검사한다. 원본 데이터의 진실성 또는 원본으로 다시 계산한 정답을 인증하는 명령은 아니다. 동일 resume는 네 파일의 바이트와 수정 시각을 유지한다.

HTTP는 `/health`, `/stats`, `/search`, `/`를 제공한다. CLI와 같은 검색 함수를 사용하며 잘못된 JSON/질의는 400, 없는 경로는 404, 지원하지 않는 메서드는 405다. 첫 화면에는 정책·최대 결과·기준 시각·문서 수와 근거 검색/고객사 접근 범위의 한계를 설명한다. 자동 브라우저/UI 조작은 하지 않았다.

## 이전 정책 검증 이력과 발견한 오류

변경 전 제공 스텁의 고정 공개 smoke는 0/10이었다. build가 NOT_IMPLEMENTED로 종료 코드 2였고 나머지 9항목은 UNRUN이었다. 같은 공개 검사기·바이트가 같은 sample 입력·이전 기본 정책 KB-BASE-1/max5·first12 정답 범위에서 당시 최종 버전은 10/10이었다. 현재 max3 정책 검증은 위의 별도12항목 범위다. 공개 first12 일치는 해당 12질의에만 해당하며 전체 비공개 점수로 해석하지 않는다. 정정 전 원본 baseline은 보존했다. 정정은 제공 sample/full의 기대값을 바꾸지 않는다고 명시했으며, 새 revision 경계 검사는 별도 규칙 범위로 기록해 이전 경계 점수와 비교하지 않는다. 이전 max5 정책 소형 경계 검사는9/9, 보호 원문/일반 출력 검사는10/10, HTTP 검사는11/11이었다. 동일한 코드라도 이를 새 정책 검사 점수로 재명명하지 않는다.

이전 KB-BASE-1/max5 정책에서 같은 소스의 전체240,000행 build는 종료 0, 5.927초, 관찰 최대 RSS 245,092KiB였다. 1,500질의 search는 종료 0, 0.953초, 106,108KiB였고 입력 순서의 canonical 1,500행을 생성했다. verify는 종료 0이고 번들 바이트/수정 시각이 유지되었다. 산출물과 TMP 증가량은 34,654,620바이트였다. 전체 관찰 집계는 보존 198,000행, 선택 키 60,000개, 공개 문서 52,364개, 철회 7,636개, 고객사 48개다. 거절은 BAD_JSON 12,000, BAD_SCHEMA 20,980, DUPLICATE_RECORD_ID 3,000, FUTURE 6,000, OVERSIZE 20으로, 합계가 실제 240,000행과 맞았다. 제공 입력 inventory의 모든 크기·해시도 일치했다. 전체 정답 oracle은 공개되지 않아 이 수치의 정답성을 독립적으로 인증하지는 않았다.

독립 CP2 리뷰는 두 실제 보호 결함을 발견했다. 최초 구현은 임의 위치 DATA의 META.json을 search 출력으로 덮어쓸 수 있었고, 보호 목록을 좁히는 수정 과정에서는 ORIGINALS.json이 빠졌다. 각각 격리 복사본에서 실패를 보존한 뒤 원본 경로/파일 식별자 보호와 보호 원문 목록을 수정했다. 같은 CP2 리뷰어의 재검증에서 두 finding 모두 FIXED가 확인되었다. 정상 새 답안과 기존 일반 답안의 교체는 계속 허용한다. 이전 버전과 현재 전체 실행의 필수 docs/meta 논리 행, stats/rejections, 1,500개 답안 바이트는 같았고 보호용 추가 테이블과 그 형식 표식을 담는 private meta 행이 추가되었다.

CP3에서는 무관한 추가 테이블을 자신의 보호 테이블로 오인한 문제와, build에서 쓴 외부 정책 파일을 나중 search 출력으로 보호하지 못한 문제를 확인했다. 소유 형식 표식과 단일 정책 파일의 경로/inode 보호로 수정했고, 자체 분리 검사와 독립 같은 체크포인트 재검증으로 확인했다. 정상 답안을 외부 정책 파일과 같은 부모에 쓰는 것은 계속 허용한다.

원래 상한 없는 revision과 SQLite INTEGER의 표현 범위가 충돌하여 9223372036854775808 입력에서 build 종료 2가 관찰되었다. 임의 상한이나 부동소수점 변환을 도입하지 않고 문의했으며, 모의 출제자가 원문 오류를 인정하고 위 정정을 발행했다. 이는 실제 SK 운영진의 공지가 아니다. 원본 TASK/입력/채점 배점은 그대로이고 제공 데이터는 모두 새 범위 안이다. 정정 후 최대값은 정확히 저장하고, 최대값 초과·음수·bool은 BAD_SCHEMA로 처리하며 잘못된 ID를 예약하지 않는 것을 확인했다. 이전 원문 모순을 AI 구현 버그로 분류하지 않는다.

별도로 유효한 4301자리 태그 가중치가 Python 기본 변환 제한 때문에 실패한 것은 실제 구현 결함이었다. CSV 기본 필드 제한도 더 긴 유효 가중치를 막았다. 두 기본 제한을 제거한 앞서 수행한 새 개정번호 규칙/정밀 정수 검사는4/4이며, 131073자리 가중치와 JSON limit에서도 정확한 합산 점수·canonical 출력·읽기 전용 verify가 성공했다. 해당 큰 정수 사례의 build/search/verify는 각각 약 0.121/0.151/0.091초, 최대 RSS 16768KiB 이하였다. 숫자를 float으로 바꾸거나 임의 자리 수를 업무 규칙으로 제한하지 않았다. 독립 CP3 Constraint 재검증도 현재 소스에서 17/17을 확인했다. 독립 CP3 Code 재검증은 같은 현재 소스에서 경계 9/9, 원본 보호 7/7과 정책·추가 테이블·정수/개정번호 사례를 확인했으며 남은 차단 finding이 없다는 결과를 받았다.

검사 도구에서도 함수 이름이 http 모듈을 가린 오류와 종료한 HTTP 포트를 즉시 재사용한 충돌이 있었다. 한 전달 메시지의 공지 해시를 잘못 적은 일도 있어 실제 hashlib 결과로 바로잡았고, 문서에 자동 계산한 해시는 처음부터 맞았다. 실패 기록을 남긴 뒤 검사 코드만 고쳐 새 실행으로 확인했으며 제품 개선 점수로 계산하지 않았다. 모든 실행은 자동 로컬 검사이며 참가자의 수동 검증으로 주장하지 않는다.

## 한계와 제출 범위

비공개 전체 정답·공식 자동 점수와 별도 설명 4점은 확인되지 않았다. 실제 시험 UI·Proctor·실제 모델명·사람의 수동 행동은 이 로컬 실행으로 증명하지 않는다. 실제 런타임 모델은 UNKNOWN이다. 악의적인 동시 파일 교체에 대한 OS 수준 격리나 적대적 SQLite에 대한 완전한 sandbox를 제공하지 않는다. 기록된 파일 식별자는 해당 로컬 파일시스템의 것이다. 전체 105분 선행 작업은 수행한 사실이 없으며 이번 모의는 75분 잔여 시점에 접속했다.

수집 제품은 kb.py, src/, EXPLANATION.md, RUN_EVIDENCE.json이다. 입력·작업 산출물·kit/helper는 모의 수집 제외 경로에 보존한다. 준비 완료와 실제 감독자의 수집/고정은 별개이며 이 문서는 수집이 완료되었다고 주장하지 않는다. 명령·버전·범위·관찰 결과는 RUN_EVIDENCE.json에 보존했다.
