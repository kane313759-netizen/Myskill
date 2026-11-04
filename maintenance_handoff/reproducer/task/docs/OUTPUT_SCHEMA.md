# 출력 계약 — KB-TRIAL-1

이 문서는 `TASK.md`의 출력 형식을 구체화한다. 평가 산식은 `GRADE_POLICY.md`를 따른다. 아래 객체의 필드는 모두 필수이며, 별도 언급이 없으면 추가 필드는 허용하지 않는다.

## JSON 직렬화

JSON 파일과 JSONL 각 행은 다음 직렬화의 UTF-8 바이트 뒤에 LF 한 바이트를 붙인다. BOM은 없다.

```python
json.dumps(value, ensure_ascii=False, sort_keys=True,
           separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n'
```

지문을 계산할 때만 끝의 LF를 제외한다. SHA-256은 소문자 16진수 64자리 문자열이다. Boolean은 정수가 아니다. 중복 JSON 키와 깊이에 관계없는 비유한 숫자는 잘못된 입력이다. 원본 ID, 제목, 본문, 태그 문자열을 strip, 숫자 변환, 대소문자 변환 또는 Unicode 정규화하지 않는다.

## 빌드 번들

`build`는 `OUT`에 `index.sqlite`, `stats.json`, `rejections.json`, `manifest.json`을 만든다.

`stats.json`:

```json
{"as_of_utc":"2026-11-02T00:00:00Z","doc_count":0,"max_results":5,"policy_id":"KB-BASE-1","schema_version":1,"selected_keys":0,"status":"COMPLETE","tenant_count":0,"withdrawn_count":0}
```

예시의 수치 대신 실제 집계값을 넣는다. 모든 count는 0 이상의 Boolean이 아닌 정수다. `selected_keys = doc_count + withdrawn_count`이며, `tenant_count`는 등록된 비공개 tenant만 센다. `max_results`는 유효 정책의 양의 정수다. `as_of_utc`는 META의 원문 문자열, `policy_id`는 유효 정책 ID다.

`rejections.json`:

```json
{"counts":{"BAD_JSON":0,"BAD_SCHEMA":0,"DUPLICATE_RECORD_ID":0,"FUTURE":0,"OVERSIZE":0},"retained_records":0,"schema_version":1}
```

모든 집계값은 0 이상의 Boolean이 아닌 정수다. 거절 사유 합계와 `retained_records`의 합은 비어 있지 않은 문서 물리 행 수와 같아야 한다. `retained_records`는 버전 선택 전, 유효하고 중복되지 않아 유지한 record 수다. 공백 행은 세지 않는다.

`manifest.json`:

```json
{"artifacts":{"index.sqlite":"<sha256>","rejections.json":"<sha256>","stats.json":"<sha256>"},"as_of_utc":"2026-11-02T00:00:00Z","effective_policy":{"effective_at":"2026-11-01T00:00:00+09:00","max_results":5,"policy_id":"KB-BASE-1"},"policy_fingerprint":"<sha256>","schema_version":1,"source_fingerprint":"<sha256>","source_inventory":[{"path":"META.json","sha256":"<sha256>","size":0}]}
```

`source_inventory`는 DATA 아래 모든 일반 파일을 재귀적으로 포함하며, `path`는 DATA 기준 상대 POSIX 경로다. 경로의 UTF-8 바이트 오름차순으로 정렬하고 `size`는 실제 바이트 수를 쓴다. symlink와 비일반 항목은 거부한다. `source_fingerprint`는 canonical `source_inventory`의 SHA-256이며, `policy_fingerprint`는 canonical `effective_policy`의 SHA-256이다. `artifacts`는 완성된 각 파일의 바이트 SHA-256이다. manifest 자체의 해시는 포함하지 않는다.

`effective_policy`는 정확히 `policy_id`(비어 있지 않은 문자열), `max_results`(양의 Boolean 아닌 정수), `effective_at`(timezone-aware ISO 문자열) 세 필드다. `--policy FILE`은 정책 전체를 대체하며, 원본 `DATA/policy.json`은 바꾸지 않는다. 정책 효력 시각은 META 기준 시각보다 늦을 수 없다.

## SQLite 공개 스키마

아래 이름과 타입을 사용할 수 있어야 한다. 추가 열, 테이블, 인덱스는 허용한다.

```sql
CREATE TABLE docs (
  tenant_id TEXT,
  doc_id TEXT,
  revision INTEGER,
  title TEXT,
  body TEXT,
  tags TEXT,
  PRIMARY KEY (tenant_id, doc_id)
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
```

`docs`에는 최종 선택된 `PUBLISHED` 키만 들어간다. `WITHDRAWN`의 예전 공개본은 넣지 않는다. `revision`은 0 이상의 정수다. `tags`는 원본 태그 순서와 반복을 보존한 canonical JSON 배열 문자열이다. `title`과 `body`는 원문 문자열이다.

`meta`에는 다음 문자열 값이 필수다.

| key | value |
| --- | --- |
| `schema_version` | `"1"` |
| `as_of_utc` | META의 원문 시각 문자열 |
| `policy_fingerprint` | 유효 정책 지문 |
| `registered_tenants` | 등록된 모든 비공개 tenant ID를 UTF-8 바이트 순으로 정렬한 canonical JSON 문자열 배열 |
| `tag_weights` | 모든 알려진 태그를 양의 Boolean 아닌 정수 가중치에 매핑한 canonical JSON 객체 |

`registered_tenants`에는 `__public__`가 들어가지 않는다. 검색은 source DATA 없이 이 공개 번들로 동작해야 한다. 두 번의 새 빌드에서 SQLite 파일 바이트가 같을 필요는 없지만, 필수 논리 행과 모든 검색 응답은 같아야 한다.

## 검색 답안

각 유효 질의마다 정확히 한 행을 입력 순서대로 출력한다.

```json
{"policy_id":"KB-BASE-1","qid":"q-1","sources":[{"doc_id":"001","revision":2,"score":7,"snippet":"본문 앞부분","tenant_id":"01","title":"원문 제목"}],"status":"OK"}
```

최상위 필드는 정확히 `qid`, `status`, `policy_id`, `sources`다. `status`는 `OK`, `NO_MATCH`, `FORBIDDEN` 중 하나다. `NO_MATCH`와 `FORBIDDEN`의 `sources`는 빈 배열이다. `OK`에는 적어도 한 source가 있어야 한다.

source는 정확히 `tenant_id`, `doc_id`, `revision`, `title`, `score`, `snippet`을 가진다. `score`는 양의 Boolean 아닌 정수다. `snippet`은 본문의 Unicode code point 앞 80개로, Python의 `body[:80]`에 해당한다.

등록 tenant는 자기 tenant와 `__public__` 문서만 볼 수 있다. 모르는 tenant와 `__public__`를 질의한 경우 `FORBIDDEN`이다. 질의의 중복 term과 문서의 중복 tag는 각각 한 번만 매칭한다. 서로 다른 일치 태그의 가중치를 합하여 점수를 구한다. 점수 내림차순, `doc_id` UTF-8 바이트 오름차순, `tenant_id` UTF-8 바이트 오름차순으로 정렬한다. 결과 상한은 `min(질의 limit 또는 정책 max_results, 정책 max_results)`다.

## CLI와 HTTP

```text
python kb.py build --input DATA --out OUT [--policy FILE] [--resume]
python kb.py search --index OUT --queries FILE --out ANSWERS [--policy FILE]
python kb.py verify --index OUT
python kb.py serve --index OUT --host 127.0.0.1 --port PORT [--policy FILE]
```

성공은 exit 0, 계약상 실패는 exit 2다. 잘못된 질의가 하나라도 있으면 기존 ANSWERS 바이트를 보존한다. 동일 source inventory와 유효 정책으로 `--resume`하면 네 artifact의 바이트와 mtime을 모두 그대로 둔다. 변경된 resume와 비어 있지 않은 OUT에 대한 새 빌드는 실패해야 한다. 검색, 검증, 서비스는 번들의 바이트와 mtime을 바꾸지 않는다.

| 요청 | 응답 |
| --- | --- |
| `GET /health` | 200, `{"policy_id":"<id>","status":"ok"}` |
| `GET /stats` | 200, `stats.json` 객체 |
| `POST /search` | 200, 단일 질의 검색 결과 |
| 잘못된 JSON 또는 질의 | 400, `{"error":"BAD_QUERY"}` |
| 없는 경로 | 404, `{"error":"NOT_FOUND"}` |
| 지원하지 않는 메서드 | 405, `{"error":"METHOD_NOT_ALLOWED"}` |

JSON HTTP 본문도 canonical JSON과 LF다. `GET /`는 UTF-8 HTML로 정책 ID, 최대 결과 수, 기준 시각, 문서 수를 보여주고, 문서 근거 검색이며 생성된 상담 답변을 제공하지 않는다는 한계를 알린다. HTML 바이트는 고정하지 않는다. 불일치 정책을 넘긴 서비스는 listen 전에 exit 2로 끝나야 한다.

## verify의 범위와 공개 smoke

`verify`는 원본 DATA 없이 JSON 형식, 해시, 내부 지문, 공개 SQLite 스키마와 논리 일관성을 확인한다. 필수 DB meta와 정책 일치, tenant/tag 유효성, `doc_count = COUNT(docs)`, 상태 집계 불변식 등을 확인한다. 원본 source의 진실성이나 새로 재구축한 결과와의 일치를 증명하는 검증은 아니다.

`tools/public_smoke.py`는 sample에 대한 공개 smoke다. 10개 고정 항목의 `PASS`, `FAIL`, `UNRUN`을 보고하며 `UNRUN`은 통과로 세지 않는다. 공개 first12 정답과의 비교는 해당 12개에만 해당한다. smoke 통과가 전체 정답이나 비공개 평가 통과를 뜻하지 않는다.
