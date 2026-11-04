# 채점 계약

총점은 100점이며 자동 채점 96점과 별도 설명 평가 4점으로 구성한다. 설명 평가 전에는 4점을 PENDING으로 남기고 자동 점수에 더하지 않는다.

| 구성 | 배점 | 계산 |
|---|---:|---|
| 데이터 산출물 | 24 | sample 40%, full 60%; 각 데이터의 stats, rejections, manifest, SQLite 논리내용 각 6점 |
| 검색 | 44 | sample 40%, full 60%; 질문별 전체 결과 일치율 40점 + 전체 행 수·canonical JSONL·성공 종료 4점 |
| CLI·resume·verify | 12 | 공개 계약에 따른 12개 동작 각 1점 |
| HTTP | 12 | 정상 기동, health, stats, 정상 검색, 공개 tenant 차단, 잘못된 query, 잘못된 JSON, 404, 405, HTML, 읽기전용, 정책불일치 차단 각 1점 |
| 자원 | 4 | sample/full 각각 build/search, 유효 산출물과 성공 종료 및 자원 제한 준수 각 1점 |
| 설명 | 4 | 아래 두 개념을 각각 2점으로 별도 평가 |

한 산출물의 누락 때문에 다른 올바른 산출물의 데이터 점수를 삭제하지 않는다. 질문 점수는 질문별 정확한 객체 전체를 비교한다. 문자열·boolean·integer를 구별한다. 알려진 tenant에 대한 양성 질문을 모두 NO_MATCH로 답하면 해당 양성 질문 점수는 모두 0이다. 실제 NO_MATCH나 FORBIDDEN 질문의 정답 부분점수는 유지한다.

항상 성공하거나 항상 거부하는 프로그램에 기능 점수를 주지 않도록 다음 전제를 적용한다. build의 거부·resume·새 빌드 결정성 점수는 정상 sample build로 내부적으로 유효한 bundle을 만든 경우에 평가한다. verify 점수는 별도로 제공하는 공개 schema의 독립 bundle에서 평가하므로 자신의 build 성공을 요구하지 않는다. verify의 거부 점수는 정상 bundle 검증 성공이 전제이며, 정상 검증 점수에는 hash 손상과 재해시한 schema 손상 두 가지 거부가 필요하다. search의 잘못된 입력·정책불일치·안전한 출력 거부 점수는 같은 독립 bundle에 대한 정상 양성 질문 한 건의 정확한 검색이 전제다. HTTP의 읽기전용 및 정책불일치 거부 점수는 정상 서버 기동이 전제다. 따라서 빈 프로그램, 아무 일도 하지 않는 프로그램, 항상 거부하는 프로그램은 0점이다.

CLI 12개는 독립 bundle 정상 검증, nonempty 출력 거부, 동일 resume 무변경, fresh 논리 결정성, source 변경 resume 거부, hash 손상 거부, 재해시된 형식 손상 거부, 잘못된 query의 기존 답 보존, 다른 정책의 기존 답 보존, 잘못된 source 거부, source symlink 거부, 출력 symlink 거부다. 기존 답 보존은 bytes를 비교하고 bundle의 읽기전용·resume는 bytes와 mtime을 함께 비교한다. SQLite fresh bytes 자체의 동일성은 요구하지 않는다.

정상 build 또는 검색을 할 수 없더라도 제공된 bundle의 verify와 HTTP 기능은 각각 점수를 얻을 수 있다. 이 bundle은 공개된 필수 SQLite schema를 사용하며 source 원본이 없어도 동작해야 한다. verify는 hash·형식·내부 일관성을 검증하며 원본 데이터의 정답성까지 증명하는 기능은 아니다.

full build와 search는 각각 180초, sample과 변형은 각각 90초다. 개별 실행의 관찰 RSS는 768MiB 이하, 출력과 TMP 증가량은 합계 2GiB 이하다. grader는 새 cwd의 새 프로세스로 고정된 절대경로의 후보만 실행한다. HTTP 응답은 제한된 길이로 읽고 파일은 symlink나 FIFO를 열기 전에 regular file 여부를 확인한다. RSS와 디스크는 관찰 방식이며 악성 코드 격리 sandbox를 의미하지 않는다.

권한 밖 tenant 자료와 철회·존재하지 않는 문서 인용, 안전하지 않은 출력 경로 수락은 수치 점수와 별도 안전성 기록에 남긴다. 이 기록을 근거 없이 총점 0점으로 바꾸지 않는다. 설명 평가의 두 기준은 (1) 첫 유효 record_id 예약, 버전 선택, 철회의 관계, (2) 정밀 실제 시각, tenant ACL, distinct tag 점수와 UTF-8 동률 순서다.

추후 공식 공지가 max_results를 변경하면 같은 계산식을 새 effective policy와 그에 맞는 독립 정답에 적용한다. 다른 규칙은 공지에 변경이 없는 한 유지한다.
