# 집계 도구와 재현 방법

[전체 결과](../README.md) · [상세 측정표](../analysis/metrics.md)

이 디렉터리는 본실험 종료 후 사용한 집계·검증 코드를 보존한다. Python 표준 라이브러리만 사용하며 실험 모델을 호출하지 않는다. 실행 코드와 사후 평가기는 각 방식 폴더의 `source/`, `selected-review/evaluation-source/`에 따로 보존한다.

| 도구 | 확인하는 내용 |
|---|---|
| `aggregate.py` | 명시적으로 선택한 원본·검수의 봉인과 결합, 회차별 수치·평균·중앙값·범위 |
| `record_checks.py` | 여섯 방식×30회의 정확한 범위, 선택본의 해시·경로·변경 여부 |
| `audit_events.py` | 제공자 누적 사용량·세션 설정, 실제 패킷 바이트, 사전 제안·수락과 최종 사전의 결합 |
| `analyze_process.py` | 독립적인 일정 완전 탐색, 최종 결과·첫 전체 후보, 검수된 대화 행동 |
| `render_metrics.py` | 완료된 집계 자료의 분모·단위·미측정 값을 보존한 Markdown 표 |

아래 명령은 이 묶음의 루트(`collection.json`이 있는 폴더)에서 실행한다. `collection.json`이 가리키는 프로젝트의 중앙 원본과 선택한 검수 폴더가 필요하다. `analysis-recomputed`는 존재하지 않는 새 출력 폴더여야 한다.

```sh
python3 -B analysis-tools/aggregate.py --collection collection.json --output analysis-recomputed
python3 -B analysis-tools/audit_events.py --collection collection.json --output analysis-recomputed/raw-measurement-audit.json
python3 -B analysis-tools/analyze_process.py --collection collection.json --aggregate analysis-recomputed --output analysis-recomputed/process-summary.json
python3 -B analysis-tools/render_metrics.py analysis-recomputed
```

한 방식의 대화 폴더만 옮긴 경우에는 그 폴더에 들어 있는 `replay_review.py`로 선택한 주석과 평가를 재현할 수 있다. 여섯 방식 모두 이 방식으로 30회씩 재현해 일치를 확인했으며, 결과는 `../analysis/replays/`에 있다. 주석을 재사용하는 재현과 다른 AI가 자연어 의미를 다시 읽은 검토는 구분한다.

비용은 실험 A·B의 모델 사용량에 고정 API 단가를 적용한다. 사후 주석·AI 검토·문서 작성 비용은 해당 측정 범위에 포함하지 않는다. 원본에 저장한 누적 사용량이 비용의 기준이며, 사용량 알림의 `last` 값을 단순 합산하지 않는다.
