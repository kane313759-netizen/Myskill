# 참가자 학습 자료

확인되지 않은 유형 B 카드부터 보여 준다. 참가자의 확인·한 줄 설명은 선택이며 MAIN 작업을 막지 않는다. 준비한 자료와 실제 전달·학습 시간을 구분한다. 기본 마지막 학습은 60분이며 축소는 참가자의 실제 선택으로만 기록한다.

```json
{"version": 1, "final_minutes": 60, "participant_choice": null, "delivery": "PREPARED", "actual_delivery_evidence": null, "type_b_cards": []}
```

카드마다 `decision`, `chosen`(쉬운 설명과 기술명), `why`(관찰·비교 근거), `alternative`, `limitations`(틀릴 조건), `change_location`(설정 키·함수)을 남긴다. 선택하지 않은 대안과 실제로 하지 않은 행동을 구분한다. 결정 원본은 기존 DECISIONS/HUMAN_JUDGMENT에 따른다.

학습 순서: 입력→처리→출력 부품 지도, 실제 한 건의 처리 경로, 전후 관찰과 수치의 범위, 경계값·오류 시험, N/A와 미검증 한계, 유지보수 네 유형. 중간 10+5+10분은 계획이며 실제 전달 시각을 별도 기록한다. 학습 중 AI는 검증 재실행·기록 정리만 한다.

후속 서술형이 본선에서 확인된 경우에만 공식 형식에 맞춰 기존 final-explain/followup-prep 결과를 넣는다. 과거 6문항을 본선 확정으로 가정하지 않는다. AI 금지 구간에는 학습 자료를 통한 AI 응답 생성·붙여넣기를 하지 않는다.
