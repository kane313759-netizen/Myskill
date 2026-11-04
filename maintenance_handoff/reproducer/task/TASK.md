# 고객지원 운영문서 근거검색 로컬서비스

고객지원 담당자는 질문에 관련된 최신 운영문서를 빠르게 확인해야 합니다. 여러 고객사에 배포된 문서에는 개정 이력, 철회된 공지, 공개 문서, 잘못된 입력이 섞여 있습니다. 제공된 원본에서 유효한 최신 문서를 고르고, 고객사별 접근 범위를 지키며 근거를 반환하는 로컬 서비스를 구현하세요.

이 서비스는 태그에 근거한 문서 검색과 근거 제시를 수행합니다. 실제 상담 답변을 생성하거나 LLM, 외부 AI, 결제 시스템, 외부 DB에 연결하지 않습니다. Python 표준 라이브러리와 `sqlite3`만으로 실행할 수 있어야 합니다. Docker나 별도 프런트엔드 프레임워크는 요구하지 않습니다.

실행 제한 및 마감은 별도 `TASK_TIMING` 안내를 따릅니다. 과제 원문, 입력 자료, 제공 검사기, 공지 파일을 수정하거나 덮어쓰지 마세요. 과제·결과를 외부로 전송하거나 Git Push를 수행할 수 없으며, Computer Use와 자동 UI 조작도 금지됩니다. 제출·시험 UI 관련 문의 및 반복 기술 장애는 Cofa Helper로 전달하세요. 제공 보조 도구의 기대값과 원문이 충돌하면 원문 규칙을 우선하고 문의할 수 있습니다.

## 제공 자료

| 경로 | 내용 |
| --- | --- |
| `data/sample/` | 비공백 문서행 6,000개를 포함한 샘플 입력 |
| `data/full/` | 비공백 문서행 240,000개를 포함한 전체 입력 |
| `queries/sample.jsonl` | 샘플 질의 80개 |
| `queries/full.jsonl` | 전체 질의 1,500개 |
| `expected/sample-first12.jsonl` | 샘플 질의 중 처음 12개의 공개 정답 |
| `DATA_INVENTORY.json` | 입력의 실제 비공백 행 수·질의 수·파일 크기·SHA-256 |
| `docs/OUTPUT_SCHEMA.md` | 출력 파일·타입·직렬화와 검사 계약 |
| `tools/public_smoke.py` | 고정 10항목의 공개 기초 검사 |
| `tools/legacy_checker.py --answers FILE` | 선택적 기존 결과 비교 도구; 공식 점수·원문 계약을 정의하지 않음 |

각 입력 디렉터리에는 문서 이력 `documents-*.jsonl`, CP949 인코딩의 고객사 목록 `tenants.csv`, UTF-8 태그 가중치 `tag_weights.csv`, 기준 정보 `META.json`, 원본 정책 `policy.json`이 있습니다. 문서 본문에는 한국어, HTML 문자, 줄바꿈, Unicode 식별자가 포함됩니다. 압축 해제나 외부 다운로드가 필요하지 않습니다.

`tenants.csv`의 헤더는 정확히 `tenant_id,label`입니다. 고객사 ID는 비어 있지 않은 원래 문자열이며, 표시용 `label`은 빈칸일 수 있습니다. 중복 고객사 ID와 예약 ID `__public__`의 고객사 등록 행은 허용하지 않습니다. `tag_weights.csv`의 헤더는 정확히 `tag,weight`이며 BOM 없는 UTF-8입니다. 태그는 비어 있지 않은 원래 문자열, 가중치는 ASCII 패턴 `[1-9][0-9]*`의 양의 정수입니다. 중복 태그는 허용하지 않습니다. 두 CSV 모두 열 개수 오류, 잘못된 인코딩, 빈 파일, 빈 물리 행은 입력 오류이며 CSV 레코드의 순서는 의미를 갖지 않습니다.

`META.json`의 `expected_nonblank_document_rows`는 참고 통계입니다. 실제 처리 결과는 아래 원문 행 처리 규칙으로 계산해야 합니다. 입력의 실제 행 수와 파일 SHA-256은 제공 통계에서 확인할 수 있습니다. 전체 정답 및 집계 기대값은 공개하지 않습니다.

## 구현할 명령

현재 작업 디렉터리에서 다음 인터페이스를 제공하세요. 옵션명과 하위 명령명은 동일해야 합니다.

```text
python kb.py build --input DATA --out OUT [--policy FILE] [--resume]
python kb.py search --index OUT --queries FILE --out ANSWERS [--policy FILE]
python kb.py verify --index OUT
python kb.py serve --index OUT --host 127.0.0.1 --port PORT [--policy FILE]
```

정상 종료 코드는 `0`, 계약 위반·유효하지 않은 입력·정책 불일치·검증 실패의 종료 코드는 `2`입니다. 실패를 숨긴 채 정상 종료하거나 일부 결과를 정상 결과처럼 남기지 마세요.

`build`는 `OUT`에 다음 네 필수 산출물을 만듭니다.

- `index.sqlite`: 조회에 사용할 SQLite 데이터베이스
- `manifest.json`: 원본 파일 목록·크기·해시, 원본 및 정책 fingerprint, 산출물 해시
- `stats.json`: 완료 상태, 기준일, 유효 정책, 문서 수 등 집계
- `rejections.json`: 행 거부 사유별 집계 및 버전 선택 전 보존된 행 수

정확한 JSON 필드와 직렬화는 `docs/OUTPUT_SCHEMA.md`를 따르세요. SQLite의 필수 테이블은 `docs`와 `meta`입니다. 추가 인덱스·테이블·컬럼은 허용하지만 공개된 필수 스키마로 조회할 수 있어야 합니다. 새로 빌드한 SQLite 파일의 물리 바이트 일치까지 요구하지 않으며, 논리 내용과 검색 결과는 결정적이어야 합니다.

`meta`에는 `schema_version`, `as_of_utc`, `policy_fingerprint`와 함께 `registered_tenants`, `tag_weights`를 저장해야 합니다. 등록 고객사는 UTF-8 바이트 순으로 정렬한 전체 비공개 고객사 ID 배열의 canonical JSON, 가중치는 전체 태그와 양의 정수 가중치를 대응시킨 canonical JSON 객체입니다. 원본이 없는 인덱스 묶음에서도 고객사와 태그를 올바르게 판정할 수 있어야 합니다.

## 정책과 기준일

원본 정책은 다음과 같습니다.

```json
{"effective_at":"2026-11-01T00:00:00+09:00","max_results":5,"policy_id":"KB-BASE-1"}
```

입력 기준 시각은 `META.json`의 `as_of_utc`, `2026-11-02T00:00:00Z`입니다. `--policy FILE`을 지정하면 그 파일의 완전한 정책 객체를 유효 정책으로 사용합니다. 원본 `DATA/policy.json`을 바꾸지 마세요. 정책의 `effective_at`은 기준 시각을 넘을 수 없습니다.

정책 fingerprint는 유효 정책 전체를 정해진 canonical JSON으로 직렬화한 바이트의 SHA-256입니다. 검색·서버에 명시한 정책의 fingerprint가 인덱스에 저장된 fingerprint와 다르면 종료 코드 `2`로 실패해야 합니다. 서버는 이 경우 포트를 열지 않아야 하며, 검색은 기존 출력 파일을 보존해야 합니다. 정책을 생략한 검색·서버는 인덱스의 유효 정책을 사용합니다.

## 문서 검증과 행 처리

문서 객체의 필드는 다음 10개와 정확히 일치해야 하며 추가·누락 필드는 허용하지 않습니다.

| 필드 | 유효한 값 |
| --- | --- |
| `record_id` | 비어 있지 않은 문자열, 전체 입력에서 중복 판정 |
| `tenant_id` | 등록된 고객사 또는 예약 식별자 `__public__` |
| `doc_id` | 비어 있지 않은 문자열 |
| `revision` | `bool`이 아닌 0 이상의 정수 |
| `updated_at` | 시간대가 있는 유효한 ISO-8601 문자열 |
| `published_at` | 시간대가 있는 유효한 ISO-8601 문자열 |
| `state` | 정확히 `PUBLISHED` 또는 `WITHDRAWN` |
| `title` | 공백이 아닌 문자가 하나 이상 있는 문자열 |
| `body` | 문자열, 빈 문자열 허용 |
| `tags` | 알려진 태그 문자열의 배열, 빈 배열 및 중복 태그 허용 |

식별자에는 Unicode 정규화, 대소문자 변경, 앞뒤 공백 제거, 숫자 변환을 적용하지 않습니다. 서로 다르게 쓰인 원래 문자열은 서로 다른 식별자입니다. `bool`을 정수로 취급하거나 비유한 수 `NaN`, `Infinity` 등을 허용하지 않습니다. JSON 객체의 중복 키는 깊이에 관계없이 잘못된 JSON입니다.

문서 파일은 상대 경로를 UTF-8 바이트 순서로 정렬하여 읽고, 파일 안에서는 물리 행 순서로 읽습니다. 행의 끝 `LF` 하나와 그 앞 `CR` 하나를 제거합니다. 각 파일의 첫 물리 행에 있는 UTF-8 BOM도 제거합니다. 이때 남은 바이트를 payload라 합니다.

다음 순서로 행마다 한 번만 판정하세요.

1. payload가 비었거나, 올바른 UTF-8로 해석했을 때 전부 Unicode 공백이면 무시합니다.
2. 비공백 payload가 65,536바이트를 넘으면 다른 검증에 앞서 `OVERSIZE`입니다. BOM과 행 끝 CRLF는 이 크기에 포함하지 않습니다.
3. UTF-8 오류, JSON 문법 오류, 중복 JSON 키, 비유한 수는 `BAD_JSON`입니다.
4. 필드 타입·값·시각·고객사·태그 membership이 잘못되면 `BAD_SCHEMA`입니다.
5. `updated_at`, `published_at` 중 하나라도 기준 시각보다 미래이면 `FUTURE`입니다.
6. 앞서 보존한 유효 행과 `record_id`가 같으면 `DUPLICATE_RECORD_ID`입니다.
7. 그 외에는 보존하고 그 `record_id`를 예약합니다.

잘못된 행이나 미래 행은 `record_id`를 예약하지 않습니다. 같은 식별자의 나중 유효 행은 처음으로 보존될 수 있습니다. `record_id`의 중복 범위는 파일·고객사를 모두 포함합니다.

시간 문자열은 앞뒤 공백 없이 Python `datetime.fromisoformat`으로 해석할 수 있고 시간대 offset이 있어야 합니다. 마지막 `Z`는 `+00:00`으로 해석할 수 있습니다. 날짜만 있는 값이나 시간대가 없는 값은 유효하지 않습니다. 시각의 대소는 문자열 순서가 아니라 실제 순간으로 비교합니다.

## 최신 버전 선택

보존된 행을 원래 문자열 그대로의 `(tenant_id, doc_id)`로 묶습니다. 각 묶음에서 다음 순서로 하나를 고릅니다.

1. `revision`이 가장 큰 행
2. 그중 `updated_at`의 실제 순간이 가장 늦은 행
3. 이 값까지 정확히 같으면 물리적으로 가장 먼저 나온 행

`published_at`은 미래 행 제외에만 사용하고 버전의 우선순위에는 사용하지 않습니다. 선택된 최신 행이 `WITHDRAWN`이면 그 문서를 검색 결과에서 제외합니다. 과거 `PUBLISHED` 버전을 되살리지 마세요. `docs` 테이블에는 선택된 `PUBLISHED` 문서만 저장합니다.

## 질의와 검색 결과

질의 한 건은 다음 형식입니다. `limit`은 생략할 수 있습니다.

```json
{"qid":"q-example","tenant_id":"customer-01","terms":["배송","반품"],"limit":3}
```

허용된 필드는 `qid`, `tenant_id`, `terms`, 선택적 `limit`입니다. `qid`와 `tenant_id`는 비어 있지 않은 문자열이어야 합니다. `terms`는 문자열 배열이며 빈 배열과 알려지지 않은 문자열도 허용합니다. `limit`을 제공하면 `bool`이 아닌 양의 정수여야 합니다.

등록된 고객사는 자기 고객사 문서와 `__public__` 문서 중 선택된 `PUBLISHED` 문서만 볼 수 있습니다. 다른 고객사 문서는 점수와 관계없이 반환하면 안 됩니다. 알 수 없는 고객사와 `__public__`를 질의 고객사로 사용한 경우는 `FORBIDDEN`이며 `sources`는 빈 배열입니다.

검색은 태그 exact string 일치입니다. 질의 안에서 중복된 term은 한 번만 계산합니다. 문서와 일치하는 서로 다른 term의 가중치를 합해 점수를 구합니다. 점수가 양수인 문서만 다음 순서로 정렬합니다.

1. `score` 내림차순
2. `doc_id`의 UTF-8 바이트 오름차순
3. `tenant_id`의 UTF-8 바이트 오름차순

결과 개수는 `min(limit, policy.max_results)`를 넘지 않아야 하며, `limit`을 생략하면 정책의 `max_results`를 사용합니다. 빈 `terms`나 전부 알려지지 않은 term은 `NO_MATCH`와 빈 `sources`를 반환합니다. 결과가 있으면 `OK`입니다.

각 결과에는 `qid`, `status`, `policy_id`, `sources`를 넣습니다. 각 source에는 `tenant_id`, `doc_id`, `revision`, `title`, `score`, `snippet`을 넣습니다. `snippet`은 원래 본문을 Unicode 코드 포인트 기준으로 처음 80자 자른 문자열이며, HTML 해석·공백 압축·줄바꿈 삭제를 하지 않습니다.

`search`는 입력 질의 순서 그대로 canonical JSONL을 출력합니다. 하나라도 잘못된 질의가 있으면 종료 코드 `2`로 실패하고 기존 `ANSWERS` 파일의 바이트를 보존해야 합니다. 동일 인덱스·정책·질의의 결과는 항상 같아야 합니다.

## 재실행·검증·파일 보호

`build --resume`에서 원본 목록·크기·해시와 유효 정책이 기존 빌드와 같으면 종료 코드 `0`을 반환하고 네 산출물의 바이트와 수정 시각을 모두 유지합니다. 원본 또는 유효 정책이 다르면 종료 코드 `2`로 실패하고 기존 산출물을 보존합니다. `--resume` 없는 빌드는 비어 있지 않은 기존 `OUT`을 덮어쓰지 않습니다.

`OUT`과 입력 `DATA`는 서로 겹칠 수 없으며 원본 파일을 alias하는 경로도 허용하지 않습니다. 원본 목록은 `DATA` 내부의 모든 일반 파일을 재귀적으로 포함하며 상대 경로 UTF-8 바이트 순서로 정렬합니다. 심볼릭 링크와 일반 파일이 아닌 항목은 거부합니다. 원본·과제 문서·공지·보호 파일을 덮어쓰는 출력 경로는 거부해야 합니다.

`verify`는 원본 `DATA`가 없는 독립된 산출물 묶음에서도 실행되어야 합니다. JSON 형식과 타입, 해시·fingerprint, 필수 DB 스키마, 읽기 전용 DB 내용과 통계의 내부 일관성을 검사합니다. `verify`는 원본 내용의 진실성을 인증하거나 원본에서 다시 빌드하는 명령이 아닙니다. 자세한 검사 범위는 `docs/OUTPUT_SCHEMA.md`를 따릅니다.

`search`, `verify`, `serve`는 인덱스 묶음 파일의 바이트나 수정 시각을 바꾸면 안 됩니다. SQLite 조회도 이 조건을 만족해야 합니다.

## HTTP 서비스

`serve`는 다음 인터페이스를 제공해야 합니다.

| 요청 | 응답 |
| --- | --- |
| `GET /health` | HTTP 200, `{"policy_id":"<유효 정책 ID>","status":"ok"}` |
| `GET /stats` | HTTP 200, `stats.json`과 같은 JSON 객체 |
| `POST /search` | 단일 질의 JSON을 받아 CLI와 동일한 결과 JSON |
| `GET /` | 비개발자용 UTF-8 HTML 안내 |

잘못된 JSON 또는 질의는 HTTP 400과 `{"error":"BAD_QUERY"}`를 반환합니다. 없는 경로는 404와 `{"error":"NOT_FOUND"}`, 지원하지 않는 메서드는 405와 `{"error":"METHOD_NOT_ALLOWED"}`입니다. JSON 응답은 canonical JSON 뒤 LF 하나로 직렬화합니다.

첫 화면은 유효 정책 ID, 최대 결과 수, 기준 시각, 문서 수를 보여야 합니다. 또한 이 서비스가 상담 답변을 생성하지 않고 문서 근거를 찾아 주며, 고객사별 공개 범위와 기준일의 제한을 따른다는 점을 비개발자가 이해할 수 있게 설명하세요. HTML의 문구·스타일·레이아웃은 자유이며 자동 UI 조작은 요구하지 않습니다.

## 제출물과 설명

수집 대상은 `kb.py`, `src/`, 제품 실행에 필요한 정적 파일, `EXPLANATION.md`, `RUN_EVIDENCE.json`입니다. `data/`, `work/`, `communications/`, `.agents/`, `.hackathon-kit/`, 캐시는 제출 수집에서 제외됩니다. 제공 입력과 생성한 인덱스는 별도 작업 경로에서 사용하세요.

`EXPLANATION.md`에는 실제 구현의 데이터 처리 흐름, 최신 버전 선택·고객사 접근 제어·검색 방식, 다룬 사례, 실행·검증 결과와 남은 한계를 사실에 맞게 설명하세요. `RUN_EVIDENCE.json`에는 실제 실행한 명령과 확인 결과를 기록하세요. 실행하지 않은 검사나 구현하지 않은 기능을 완료했다고 적지 마세요.

후속 설명은 AI 및 복사·붙여넣기 없이 수행합니다. 최종 제출 전에 자신의 실제 구현과 사례를 스스로 설명할 수 있도록 준비하세요.
