# 안전 시험 — 축소 운전에서도 유지

시험 목록 작성과 실제 통과 기록을 구분한다. 실제 결과에는 입력·기대 행동의 근거·현재 코드/설정 해시·실행 출력 경로/해시·관찰 결과를 남긴다. `PASS`만 적은 행은 실행 증거가 아니다.

```json
{
  "version": 1,
  "agent_or_interactive": false,
  "enabled_core": ["independent_reviews", "submission_constraints", "clean_replay", "security_and_transfer", "safe_fallback"],
  "results": {}
}
```

에이전트·대화형 과제면 `agent_or_interactive`를 true로 바꾸고 `agent_instruction_boundary`, `irreversible_action_approval`, `current_document_only`를 추가한다. 데이터 속 지시문을 실행 지시로 취급하지 않는지, 되돌릴 수 없는 조치를 승인·이관하는지, 폐기 문서를 근거로 쓰지 않는지 실제로 시험한다.

깨진 입력·경계값·결측치·근거 부족 시 사전 검증된 보수적 판정 또는 사람 확인 요청과 경고 기록을 확인한다. 현행 방식으로 복귀하는 것이 안전하다는 별도 근거가 없으면 자동 복귀하지 않는다. 축소 순서는 설정 스윕 확장, 자동 탐색, 복잡한 모델, 나머지 P2, 발표 장식이다. 학습 60분과 핵심 안전·독립 리뷰는 자동 축소하지 않는다.

각 `results` 항목 형식: `{"status":"PASS","evidence":{"path":"실제 실행 기록 JSON","sha256":"현재 해시"},"scope":{"제품/설정/시험 경로":"현재 해시"}}`. 범위는 현재 clean_run의 입력·최종 산출물을 포함한다. 실행 기록은 `tool:exec_command`, 실제 `argv`, 정확한 `request.cmd`, `result.exit_code:0`, 실제 `result.output`을 보존한다. 출력 JSON은 `tests:{시험명:PASS}`와 동일한 `scope`를 담고 실제 시험 파일을 호출해야 한다. 계획된 명령·서술형 근거만으로 실행 통과를 주장하지 않는다. 기록의 진위와 시험 내용의 적절성은 독립 검토의 한계 안에서 별도 확인한다.
