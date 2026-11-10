# Universal v2.7 추가 배포

**시작은 [BOOTSTRAP_V27.md](BOOTSTRAP_V27.md)**의 한 문장을 사용한다. 키트를 설치할 수 없을 때의 짧은 대체 지시도 같은 파일에 있다.

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

## 수집 전 도우미 정리

최종 수집 준비와 증거 검사를 마친 뒤 다음 순서로 정리한다. purge 미리보기는 아무것도 지우지 않으며, `--apply`는 로컬 스냅샷을 삭제한다. 이 삭제 후에는 해당 보관본으로 복구할 수 없다. 다른 내용이나 연결 경로가 있으면 purge가 전체 삭제를 거부하므로 원인을 확인한다.

```text
python -I .hackathon-kit/scripts/snapshot.py purge --root .
python -I .hackathon-kit/scripts/snapshot.py purge --root . --apply
python -I .hackathon-kit/scripts/kit_lifecycle.py clean --kit .hackathon-kit --apply
```

마지막으로 실제 제출 파일과 원래 clean이 만든 메모 백업 등 수집 제외 대상을 확인한다. 검사가 끝나기 전에 스냅샷을 지우거나 helper 삭제를 제출 성공으로 기록하지 않는다.

기준 소스 `affd3c1623f67697247c67f6d30df9e76b9bc076`는 공개 [finals-r8.2-baseline](https://github.com/kane313759-netizen/Myskill/tree/finals-r8.2-baseline) 브랜치에서 확인할 수 있다.

## 변경 이력

### 2026-11-08 · v2.7 r1

- 기존 최종 기록 이름 FINAL을 재사용하고 논리 단계 CP3와 구분.
- 스냅샷 전체 선검증 purge의 미리보기·명시 적용 및 기존 clean 연결.
- 리뷰 예산 C의 순차/병렬 계산, c_basis와 점심 겹침 경고.
- 지난 CP3 시각 이후 일정 유지, passed 표시와 PAST_CONFIRMATION.
- 16:00을 공식 마감과 구별한 계획값으로 제공.
- EXECUTION_TOOLS와 수동 기록의 정직한 UNVERIFIED 처리.
- 한국어 단일 시작 문서·키트 없는 대체 지시의 패키징과 소유권 설치.
- 공개 기준 브랜치 추가. 보호 파일 112개 및 기존 정책·STATE는 보존.

### v2.7 r2 시험 개선

과제 원문의 hard_limits는 지키고 proxy_metrics 악화는 경고한다. 현행 유지에는 best_alternative와 rejection_basis를 기록한다. 진행자 회신 전에는 최종 잠금을 하지 않으며 최소 두 설정 변경의 실제 실행 증거를 요구한다. 감사 대상은 명시 파일로 한정한 채 gzip CSV와 규모 계단·시각 역행 후보를 검사한다. Type B 기술 선택은 AI가 수행하고 참가자 승인 카드로 바꾸지 않는다. 감사 경보와 실행 증거는 도메인 진실·공식 점수·인간 이해를 인증하지 않는다. 세부 스키마와 안전 예산은 references/v27-contract.md를 따른다.

### v2.7 r3 합성 회귀 보완

명시·자동 역할과 bounded 개체 표본으로 공정 순서·출처별 역행과 제안 시차를 점검한다. 파일별 gzip/CSV 스트리밍, 기간·출처별 10의 거듭제곱 규모 비교, FINDING 효과·관문·가정·실제 선택·요청 폴백 근거를 추가했다. 모든 경보·시차는 후보이며 사람의 검토가 필요하다.

Windows 실행 경험: 기본 python 별칭은 실제 인터프리터가 아니어서 PowerShell 설치 테스트가 종료 9009로 실패했다. `test_internal_source`의 일부 UTF-8 manifest 읽기는 CP949 기본값에서 UnicodeDecodeError가 났고, `test_local_score`의 일부 하위 프로세스 출력도 UTF-8/CP949 충돌로 읽지 못했다. 해당 테스트는 보호 파일이므로 수정하지 않았다. 환경에서 UTF-8 모드를 설정하고, `-I` 실행에는 `-X utf8`이 별도로 필요하다. 플랫폼별 미실행 CI는 통과로 적지 않는다.

### v2.7 r3.1 합성 회귀 보완

행 읽기 완결성과 검사별 표본·그룹 축소를 분리한다. UNVERIFIED는 행을 다 읽지 못한 경우만, 분석 축소는 경고다. 고유값 50개 초과 범주 그룹은 회수하고 기간·출처·출처×기간 표본은 총 float 2,000,000개 예산을 공유한다. 수치 최대 512열을 비교하며 `scale_columns`로 열을 선택할 수 있고, 그룹당 표본 크기와 생략은 결과에 기록한다. 출처 자체 제외 기준과 출처 내 기간 계단, 표본 중복률 기반의 세밀한 ID, 시간대 혼재 경고, 시간 없는 데이터의 인접 비교 중단 및 긴 형식 분리를 적용한다. 기본 파일별 시간 예산은 300초(최대 900초)다. 모든 경보는 확인이 필요한 후보이며 시차를 자동으로 적용하지 않는다.

모두 정수이고 고유값 50개 이하이며 최댓값이 100 이하이거나 이름에 code·bin·item·flag·type·class·status·grade·level이 들어간 열은 코드로 표시하고 단위 비교에서 제외한다. 따라서 100 이하인 작은 정수 측정값의 실제 10배 변화는 놓칠 수 있다.

JSONL·gzip JSONL을 스트리밍하고 깨진 줄은 건수와 미완료로 남긴다. 미지원 파일은 파일별 UNSUPPORTED 경고로 격리한다. POSITIVE 1~3개와 NEGATIVE 1개 이상을 검증하며 스냅샷은 M1과 최종만 남긴다.
