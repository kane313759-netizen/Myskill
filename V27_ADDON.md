# Universal v2.7 추가 배포

현재 기준은 `2026-11-08-finals-r8.2-candidate`이다. v2.7은 이 기준의 파일 112개를 수정하지 않고 기능을 추가한다. 원문 명세의 r8.1보다 이미 강화된 여섯 RED와 조건부 SECURITY_RED를 유지한다. 기준 VERSION을 v2.7로 바꾸지 않으며, 별도 추가 기능 버전은 2.7이다.

설치한 작업 폴더에서 `$hackathon-orchestrator-universal`로 시작한다. 본선 원문과 실제 과제를 먼저 확인하고, ENV의 준비 가정을 공식 규칙으로 취급하지 않는다. 현재 안내문만으로는 본선 후속 평가·모델·API·제출 확정 방식이 정해지지 않았다.

## 설치와 확인

검증을 통과한 커밋 전체를 별도 폴더에 내려받은 뒤 실행한다. 브랜치 이름은 움직일 수 있으므로 배포 결과에 안내된 전체 SHA를 사용한다. Python 3.8 이상이 필요하다.

```powershell
python -I scripts/install_v27.py --source . --target "C:\작업\실제과제"
python -I "C:\작업\실제과제\.hackathon-kit\scripts\kit_lifecycle.py" doctor --kit "C:\작업\실제과제\.hackathon-kit"
```

원본이 설치 대상 안에 있으면 명시적으로 `--allow-internal-source`를 추가한다. 기존 사용자 파일 충돌은 덮어쓰지 않는다. 설치 성공은 설치 무결성 확인이며 대회 허용·과제 통과·제출 완료를 뜻하지 않는다. 본선 당일 설치와 외부 전송은 공식 허용을 먼저 확인한다. 이 공개 배포에는 대회 과제나 참가자 작업 데이터를 넣지 않는다.

## 추가된 범위

- 환경별 스위치와 출처 구분, 시간대가 있는 마감 역산, 별도 V27_STATE.
- 실제 데이터에 적용되는 10항목 감사, 자체 채점기의 독립 정답 사례, holdout 재사용 기록.
- 실제 도구·알고리즘의 선택 이유와 한계 설명, 중간 10/5/10분 및 마지막 60분 학습 계획.
- 명시 파일만 보관하는 로컬 스냅샷과 원자료 해시, 제출 형식 검사, 복사본의 재실행 비교, 제한된 보안 검사.
- 실제 실행 영수증과 현재 산출물 해시를 확인하는 읽기 전용 검사. 기존 CP1/CP2/CP3를 추가하지 않는다.

P1 범위를 구현했다. P2의 `change_test.py`, `tune.py`, `pitch_check.py`는 포함하지 않는다. 알고리즘 변경 검증과 피칭 준비는 기존 ALGORITHM_RED 및 본선 스킬의 실제 증거 기반 절차를 계속 사용한다.

상세 계약과 실행 명령은 [추가 계약](references/v27-contract.md), 기존 동작 대응은 [R81_MAP](R81_MAP.md)에 있다. 추가 체크가 기존 예선 게이트를 통과시키거나 STATE를 변경하지 않는다. 스냅샷은 같은 장치의 보관본이며 장치 분실 복구를 보장하지 않는다. 정적 보안 검사는 전체 보안 인증이 아니며 재실행 프로세스는 OS 샌드박스가 아니다.

## 배포 검증

```text
python -B -m unittest discover -s tests -v
python -I scripts/package_v27.py --source . --output /임시폴더/Myskill-universal-v27.zip
```

별도 `validate-v27` CI가 Windows/Linux와 Python 3.8/3.12에서 기준 회귀·추가 기능·설치·패키지를 검사한다. 네 조합의 실제 결과 확인 전에는 해당 커밋을 설치 준비 완료로 표시하지 않는다. 기본 패키저와 기본 워크플로는 그대로 보존되므로 v2.7 배포에는 `package_v27.py`를 쓴다.
