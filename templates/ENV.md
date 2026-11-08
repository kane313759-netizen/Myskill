# 본선 환경 기록 — 미확인 사항은 공식 규칙이 아님

이 파일은 보수적인 준비값이다. 본선 원문·과제 지시·감독관 답변을 확인한 항목만 `CONFIRMED`로 바꾼다. `CONFIRMED`에는 작업 폴더 안의 원문 `source_path`, 현재 `source_sha256`, 원문 그대로인 `source_excerpt`가 필요하다. `PLAN_DEFAULT`는 운영 가정이며 공식 허용이나 금지를 증명하지 않는다. 2차 예선 규칙을 본선 확정으로 복사하지 않는다.

아래 블록 하나가 기계 판독 원본이다. 날짜가 있는 시각에는 시간대 오프셋도 기록한다. 경기 일정과 실제 제출 확정 마감은 별개다. 현재 모델 화면·허용 공지·실제 선택을 각각 확인한다. AVAILABLE에 보이는 것만으로 사용 허가가 되지 않는다. 모델 성능 순위는 추정하지 않는다.

```json
{
  "version": 1,
  "switches": {
    "FOLLOWUP": {"value": "AFTER_CONFIRM", "classification": "PLAN_DEFAULT", "reason": "2차 방식에 대비한 엄격한 계획값. 본선 후속 평가 방식 미확인"},
    "T_SUB": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "공식 제출 확정 마감 미확인"},
    "WINDOW_END": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "후속 평가를 포함한 공식 시간창 미확인"},
    "T_FU": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "고정 후속 평가 시작 시각 미확인"},
    "followup_minutes": {"value": 30, "classification": "PLAN_DEFAULT", "reason": "2차 방식에 대비한 계획값"},
    "transition_minutes": {"value": 5, "classification": "PLAN_DEFAULT", "reason": "계획 예비 시간"},
    "LUNCH_POLICY": {"value": "PAUSE", "classification": "PLAN_DEFAULT", "reason": "공식 점심 중 작업 허용 미확인"},
    "WORK_ENV": {"value": "PROVIDED", "classification": "PLAN_DEFAULT", "reason": "반입·제공 환경 미확인"},
    "AI_SCOPE": {"value": ["PROVIDED_ONLY"], "classification": "PLAN_DEFAULT", "reason": "제공 AI만 사용한다는 준비 가정. 실제 허용 목록 미확인"},
    "MODELS": {"value": {"AVAILABLE": [], "RECOMMENDED": [], "RESTRICTED": ["Astra"]}, "classification": "PLAN_DEFAULT", "reason": "본선 목록 미확인. Astra는 2차 제한을 유지하는 준비 가정"},
    "EXTERNAL_TRANSFER": {"value": "PROHIBITED", "classification": "PLAN_DEFAULT", "reason": "허용 환경 밖 저장소·클라우드·메일·다른 AI·다른 계정으로 전송하지 않는 준비 가정"},
    "GIT_PUSH": {"value": "PROHIBITED", "classification": "PLAN_DEFAULT", "reason": "본선 공식 허용 전에는 로컬 작업만"},
    "COMPUTER_USE": {"value": "PROHIBITED", "classification": "PLAN_DEFAULT", "reason": "본선 공식 허용 전에는 사용하지 않는 준비 가정"},
    "SUBMISSION": {"value": "UNKNOWN_AFTER_INSPECTION", "classification": "UNKNOWN", "reason": "수집 범위·용량·확정 절차를 GRADER와 현장에서 확인해야 함"},
    "S": {"value": 60, "classification": "PLAN_DEFAULT", "reason": "참가자가 요청한 마지막 학습 60분. 실제 선택 없이 자동 축소 금지"},
    "S_pre": {"value": 60, "classification": "PLAN_DEFAULT", "reason": "후속 평가가 없는 경우도 기본 학습 60분"},
    "R": {"value": 10, "classification": "PLAN_DEFAULT", "reason": "제출 조작 예비 최소 10분"},
    "C": {"value": 40, "classification": "PLAN_DEFAULT", "reason": "CP3 리뷰·수정 계획 예비 40분. 과제 크기에 따라 확대"},
    "PITCH_STUDY_WINDOW": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "제출 후 피칭 전 노트북 학습 허용 미확인"},
    "participant_study_choice": {"value": null, "classification": "UNKNOWN", "reason": "실제 참가자 선택 없음"}
  },
  "assignments": {"MAIN": "UNKNOWN", "CONSTRAINT_RED": "UNKNOWN", "DATA_EVAL_RED": "UNKNOWN", "ALGORITHM_RED": "UNKNOWN", "CODE_RED": "UNKNOWN", "EDGE_RED": "UNKNOWN", "SUBMISSION_RED": "UNKNOWN", "SECURITY_RED": "UNKNOWN"}
}
```

학습 시간을 줄일 경우 참가자의 실제 선택과 근거 문서 해시를 별도로 남긴다. `SUBMISSION` 확인은 미리보기 준비와 실제 확정 영수증을 구분한다. v2.7 계산은 `V27_STATE.json`에만 기록하며 기존 STATE 키를 추가하거나 계획 마감으로 공식 마감을 덮지 않는다.
