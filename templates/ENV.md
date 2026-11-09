# 본선 환경 기록 — 미확인 사항은 공식 규칙이 아님

이 파일은 보수적인 준비값이다. 본선 원문·과제 지시·감독관 답변을 확인한 항목만 `CONFIRMED`로 바꾼다. `CONFIRMED`에는 작업 폴더 안의 원문 `source_path`, 현재 `source_sha256`, 원문 그대로인 `source_excerpt`가 필요하다. `PLAN_DEFAULT`는 운영 가정이며 공식 허용이나 금지를 증명하지 않는다. 2차 예선 규칙을 본선 확정으로 복사하지 않는다. FOLLOWUP·LUNCH_POLICY·REVIEW_PARALLEL·S_pre 값은 2차 예선 방식의 계획값이며, 당일 공식 안내를 읽은 직후 참가자에게 받은 환경으로 고쳐 deadline.py를 다시 계산한다.

아래 블록 하나가 기계 판독 원본이다. 날짜가 있는 시각에는 시간대 오프셋도 기록한다. 경기 일정과 실제 제출 확정 마감은 별개다. 현재 모델 화면·허용 공지·실제 선택을 각각 확인한다. AVAILABLE에 보이는 것만으로 사용 허가가 되지 않는다. 모델 성능 순위는 추정하지 않는다.

```json
{
  "version": 1,
  "switches": {
    "FOLLOWUP": {"value": "AFTER_CONFIRM", "classification": "PLAN_DEFAULT", "reason": "2차 방식에 대비한 엄격한 계획값. 본선 후속 평가 방식 미확인"},
    "T_SUB": {"value": "2026-11-11T16:00:00+09:00", "classification": "PLAN_DEFAULT", "reason": "참가자가 전달한 본선 안내의 경기 종료 시각(FINALS_POLICY.md). 공식 제출 확정 마감 아님"},
    "WINDOW_END": {"value": "2026-11-11T16:00:00+09:00", "classification": "PLAN_DEFAULT", "reason": "참가자가 전달한 본선 안내의 경기 종료 시각(FINALS_POLICY.md). 공식 제출 확정 마감 아님"},
    "T_FU": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "고정 후속 평가 시작 시각 미확인"},
    "followup_minutes": {"value": 30, "classification": "PLAN_DEFAULT", "reason": "2차 방식에 대비한 계획값"},
    "transition_minutes": {"value": 5, "classification": "PLAN_DEFAULT", "reason": "계획 예비 시간"},
    "LUNCH_POLICY": {"value": "PAUSE", "classification": "PLAN_DEFAULT", "reason": "공식 점심 중 작업 허용 미확인"},
    "LUNCH_START": {"value": "2026-11-11T12:00:00+09:00", "classification": "PLAN_DEFAULT", "reason": "참가자가 전달한 본선 안내의 점심 시작 시각. 작업 허용 여부와 별개인 계획값"},
    "LUNCH_END": {"value": "2026-11-11T13:00:00+09:00", "classification": "PLAN_DEFAULT", "reason": "참가자가 전달한 본선 안내의 점심 종료 시각. 작업 허용 여부와 별개인 계획값"},
    "WORK_ENV": {"value": "PROVIDED", "classification": "PLAN_DEFAULT", "reason": "반입·제공 환경 미확인"},
    "AI_SCOPE": {"value": ["PROVIDED_ONLY"], "classification": "PLAN_DEFAULT", "reason": "제공 AI만 사용한다는 준비 가정. 실제 허용 목록 미확인"},
    "MODELS": {"value": {"AVAILABLE": [], "RECOMMENDED": [], "RESTRICTED": ["Astra"]}, "classification": "PLAN_DEFAULT", "reason": "본선 목록 미확인. Astra는 2차 제한을 유지하는 준비 가정"},
    "EXECUTION_TOOLS": {"value": ["exec_command"], "classification": "PLAN_DEFAULT", "reason": "현재 Codex 실행 도구의 준비값. 실제 본선 플랫폼 도구 이름 확인 후 목록을 갱신"},
    "EXTERNAL_TRANSFER": {"value": "PROHIBITED", "classification": "PLAN_DEFAULT", "reason": "허용 환경 밖 저장소·클라우드·메일·다른 AI·다른 계정으로 전송하지 않는 준비 가정"},
    "GIT_PUSH": {"value": "PROHIBITED", "classification": "PLAN_DEFAULT", "reason": "본선 공식 허용 전에는 로컬 작업만"},
    "COMPUTER_USE": {"value": "PROHIBITED", "classification": "PLAN_DEFAULT", "reason": "본선 공식 허용 전에는 사용하지 않는 준비 가정"},
    "SUBMISSION": {"value": "UNKNOWN_AFTER_INSPECTION", "classification": "UNKNOWN", "reason": "수집 범위·용량·확정 절차를 GRADER와 현장에서 확인해야 함"},
    "S": {"value": 60, "classification": "PLAN_DEFAULT", "reason": "참가자가 요청한 마지막 학습 60분. 실제 선택 없이 자동 축소 금지"},
    "S_pre": {"value": 60, "classification": "PLAN_DEFAULT", "reason": "후속 평가가 없는 경우도 기본 학습 60분"},
    "R": {"value": 10, "classification": "PLAN_DEFAULT", "reason": "제출 조작 예비 최소 10분"},
    "REVIEW_PARALLEL": {"value": "UNKNOWN", "classification": "PLAN_DEFAULT", "reason": "본선 독립 리뷰 동시 실행 가능 여부 미확인. 확인 전에는 순차 실행으로 계산"},
    "REVIEW_CONCURRENCY": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "실제로 동시에 띄울 수 있는 리뷰 작업자 수 미확인. 적기 전에는 REVIEW_PARALLEL=YES여도 순차로 계산"},
    "REVIEW_MINUTES_EACH": {"value": 10, "classification": "PLAN_DEFAULT", "reason": "독립 리뷰 1개당 계획 10분. 실제 과제·실행 관측에 따라 조정"},
    "FIX_BUFFER": {"value": 20, "classification": "PLAN_DEFAULT", "reason": "최종 리뷰 발견 사항 수정·재검증 계획 예비 20분"},
    "FINAL_REVIEW_ROLES": {"value": 7, "classification": "PLAN_DEFAULT", "reason": "핵심 RED 6개와 조건부 SECURITY_RED 1개. SECURITY_RED가 TRIGGERED 또는 UNKNOWN이면 7, NOT_TRIGGERED를 확인하면 6으로 갱신"},
    "PITCH_STUDY_WINDOW": {"value": "UNKNOWN", "classification": "UNKNOWN", "reason": "제출 후 피칭 전 노트북 학습 허용 미확인"},
    "participant_study_choice": {"value": null, "classification": "UNKNOWN", "reason": "실제 참가자 선택 없음"},
    "MODEL_PLAN": {"value": {"ORCHESTRATOR": {"model": "Sol 6.1", "effort": "high"}, "MAIN": {"model": "Sol 6.1", "effort": "Ultra"}, "CODE_RED": {"model": "Sol 6.1", "effort": "high"}, "CONSTRAINT_RED": {"model": "Sol 6.1", "effort": "Max"}, "DATA_EVAL_RED": {"model": "Sol 6.1", "effort": "Max"}, "ALGORITHM_RED": {"model": "Sol 6.1", "effort": "Max"}, "EDGE_RED": {"model": "Sol 6.1", "effort": "high"}, "SUBMISSION_RED": {"model": "Sol 6.1", "effort": "high"}, "SECURITY_RED": {"model": "Sol 6.1", "effort": "high"}, "RECORDER": {"model": "Luna 6", "effort": "Max"}, "TUTOR": {"model": "Sol 6.1", "effort": "high"}}, "classification": "PLAN_DEFAULT", "reason": "참가자가 지정한 역할별 모델·노력 계획값(r4-3.12). 사용 허가가 아니며 당일 화면·공식 안내로 확인한다"},
    "ACTUAL_EFFORT": {"value": {"ORCHESTRATOR": "UNKNOWN", "MAIN": "UNKNOWN", "CODE_RED": "UNKNOWN", "CONSTRAINT_RED": "UNKNOWN", "DATA_EVAL_RED": "UNKNOWN", "ALGORITHM_RED": "UNKNOWN", "EDGE_RED": "UNKNOWN", "SUBMISSION_RED": "UNKNOWN", "SECURITY_RED": "UNKNOWN", "RECORDER": "UNKNOWN", "TUTOR": "UNKNOWN"}, "classification": "UNKNOWN", "reason": "당일 실제로 고른 노력 단계 미확인. 확인한 역할만 값으로 바꾼다"}
  },
  "assignments": {"ORCHESTRATOR": "UNKNOWN", "MAIN": "UNKNOWN", "CONSTRAINT_RED": "UNKNOWN", "DATA_EVAL_RED": "UNKNOWN", "ALGORITHM_RED": "UNKNOWN", "CODE_RED": "UNKNOWN", "EDGE_RED": "UNKNOWN", "SUBMISSION_RED": "UNKNOWN", "SECURITY_RED": "UNKNOWN", "RECORDER": "UNKNOWN", "TUTOR": "UNKNOWN"}
}
```

학습 시간을 줄일 경우 참가자의 실제 선택과 근거 문서 해시를 별도로 남긴다. `SUBMISSION` 확인은 미리보기 준비와 실제 확정 영수증을 구분한다. v2.7 계산은 `V27_STATE.json`에만 기록하며 기존 STATE 키를 추가하거나 계획 마감으로 공식 마감을 덮지 않는다.

기본 C는 별도로 고정하지 않고 리뷰 수·동시 실행 가능 여부·수정 예비로 계산한다. 기본값은 20 + 10 × 7 = 90분이다. 동시 실행 YES와 실제 동시 리뷰 작업자 수(REVIEW_CONCURRENCY)를 확인하면 올림((리뷰 수 − 1) ÷ 동시 수) + 1개 배치로 줄어든다. 제출 형식 리뷰는 다른 리뷰의 수정 뒤에 따로 돌기 때문이다(동시 6명 이상 40분, 3명이면 50분). 필요하면 출처 분류와 이유를 갖춘 `C` 스위치를 추가해 직접 지정할 수 있다. `c_basis`가 실제 계산 근거를 남긴다. 점심 겹침 경고는 일정을 자동 변경하지 않으므로 필요한 경우 참가자가 일정을 재계획한다.
