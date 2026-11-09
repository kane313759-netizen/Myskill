# AI 에이전트 지침 (이 저장소)

참가자가 "kane313759-netizen myskill 최신버전 설치해서 작업 시작해 줘"처럼 이 저장소를 설치해 과제를 시작하라고 요청하면, README.md 맨 위 상자의 4단계를 따른다.

1. 과제 폴더 밖의 새 임시 폴더에 clone한다(기본 브랜치가 최신판).
2. `python -X utf8 -I <clone>/scripts/install_v27.py --source <clone> --target <과제 폴더>` — install.sh·install.ps1 대신 쓴다.
3. `python -X utf8 -I <과제 폴더>/.hackathon-kit/scripts/kit_lifecycle.py doctor --kit <과제 폴더>/.hackathon-kit`
4. `<과제 폴더>/.hackathon-kit/BOOTSTRAP_V27.md`의 시작 문장대로 `$hackathon-orchestrator-universal`로 시작한다(hackathon-finals 절차 포함).

이 저장소 자체를 고치는 작업(검토·패치 적용)이라면 위 단계는 해당하지 않는다. 그때는 요청받은 지시를 따른다.
