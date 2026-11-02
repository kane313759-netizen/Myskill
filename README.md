# AI Hackathon Starter Kit

범용 Codex 해커톤 스타터킷입니다. 특정 과제 정답이 아니라 **문제 이해 → 제약 → 명세 → 구현 → 검증 → 설명** 절차를 제공합니다.

## 최종 역할

- **Terra 5.6 — ORCHESTRATOR ONLY**: 단계 관리, subagent 호출, findings 취합
- **Sol 6.1 — persistent MAIN BUILDER**: 문제 이해, 요구사항/명세, 설계, 구현, 통합, 어려운 오류 수정, 최종 설명
- **Terra 5.6 — CODE RED**: 코드 버그·경계값·회귀·저장 문제 독립 리뷰
- **Sol 6.1 — independent CONSTRAINT RED**: 암묵 제약·현실성·trade-off·목표함수 허점 공격
- **Luna 6 — RECORDER**: 결정·검증·시스템 지도·후속질문 대비 기록

> **Sol이 만들고, Terra가 코드를 깨고, 다른 Sol이 문제 정의를 깨고, Luna가 기록한다.**

## 시험장에서 설치

Linux / cloud shell:

```bash
git clone https://github.com/kane313759-netizen/Myskill.git _hackathon_kit
bash _hackathon_kit/install.sh .
```

PowerShell:

```powershell
git clone https://github.com/kane313759-netizen/Myskill.git _hackathon_kit
powershell -ExecutionPolicy Bypass -File _hackathon_kit/install.ps1 -Target .
```

설치 뒤 Codex 첫 메시지:

```text
Use the hackathon-orchestrator skill. Start from Phase 0.
Keep Terra as orchestrator, create one persistent Sol 6.1 MAIN BUILDER,
and let that MAIN own specification through implementation.
Do not implement until the constraint gate is complete.
```

전체 시작문은 `BOOTSTRAP_PROMPT.md`, 짧은 호출법은 `CALLING.md`를 참고합니다.

## 핵심 원칙

1. 시험 규칙과 과제 문서가 이 키트보다 항상 우선합니다.
2. 문서에 없는 제한을 사실처럼 만들지 않습니다.
3. **규칙상 맞는가? + 현실에서도 쓸 수 있는가?** 둘 다 검사합니다.
4. Red Team과 Recorder는 source를 수정하지 않습니다.
5. 실제 source writer는 persistent MAIN Sol 하나만 둡니다.
6. 외부 AI, 외부 데이터 전송, 원격 push, Computer Use는 과제 규칙이 명시적으로 허용하지 않는 한 사용하지 않습니다.

## 구조

- `.agents/skills/` — Codex repo-local skills
- `prompts/` — 하위 에이전트 역할 프롬프트
- `references/` — 모델 정책·과제 유형·제약 체크리스트
- `templates/` — 시스템 지도·결정·검증 기록
- `scripts/` — 로컬 데이터/환경 sanity 검사

이 저장소는 **답을 미리 정하는 키트가 아니라, 답을 찾는 절차를 재사용하는 키트**입니다.
