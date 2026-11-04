# 동시 작업 조정 — 제출 시작 알림 보완

사용자가 Claude에 이미 작업을 맡겼다고 알렸다. 이후 Codex는 코드 추가 수정을 중지한다.

- 현재 시험용 exam-r7.2.1: df825438c37e966fe6d835cc93e69f656b05449d.
- 기존 9ac5479 대비 실행 스크립트/EXAM_POLICY/역할/게이트는 그대로이고 canonical orchestrator SKILL.md의11줄만 추가했다.
- 변경: 예약한 제출시작시각(마감10분전 권고)에 사람이 '제출하고 문제풀기' 미리보기를 열도록 알림. Recorder/doctor/선택연습이 끝나길 기다리며 알림을 미루지 않는다. preview와confirmation은 구분하며, 차단결함/검증된부분결과/6개개요/10GB/확정뒤쓰기금지/사람직접제출은 유지한다.
- 독립 readonly 표적재검토: 해당P2해결, 남은finding0. 로컬 기존156tests완료(155통과,PowerShell1skip). 이전9ac4matrix/packageCI는PASS이나 새df의전체운영/Windows재실행을 했다고 주장하지 않는다.
- 새20분압축리플레이fixture/참조정답·빈프로그램control만 준비했으며 actor실행은 시작하지 않았다. 따라서 새로운 end-to-endPASS가 아니다.
- Claude는 원격브랜치와diff를 확인하고 이 변경을 보존/통합해 최종 검증할 커밋을 한 곳으로 정한다. force push로 기존 작업을 덮어쓰지 않는다. 사용자서술형연습은 계속 제외한다.

인계브랜치의키트원본은9ac기반이다. 최종검증대상은이알림과Claude수정을반영한정확한새hash로명시한다. 실제시험UI/모델은여전히미검증이다.
