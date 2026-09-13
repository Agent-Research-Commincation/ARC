# 180회 실험 기록

같은 일정 문제를 여섯 소통 방식으로 각각 30회 실행했다. 아래에서 방식을 고른 뒤 `trial-01`부터 `trial-30`까지 회차를 열면 된다.

[프로젝트 가설·과정·결과·인사이트](../../docs/experiment-report.md) · [상세 측정표](analysis/metrics.md)

## 방식별 대화

| 단계 | 소통 방식 | 실제 회차 | 유효 합의 | 가장 선호하는 일정 |
|---|---|---:|---:|---:|
| 1 | [자연어](stage-01-natural-language/README.md) | 30 | 28 | 28 |
| 2 | [JSON](stage-02-json/README.md) | 30 | 30 | 30 |
| 3 | [논리식·관계 표현](stage-03-relations/README.md) | 30 | 30 | 28 |
| 4 | [고정 의미 특성 벡터](stage-04-fixed-vector/README.md) | 30 | 30 | 30 |
| 5 | [바이트코드](stage-05-bytecode/README.md) | 30 | 30 | 30 |
| 6 | [공동 기호 언어](stage-06-shared-dictionary/README.md) | 30 | 29 | 29 |

과제 실패는 자연어 14회차와 공동 기호 언어 25회차, Agent 자체 종료는 자연어 6회차다. 논리식 7·27회차는 유효하지만 최적이 아닌 일정이다. 실패를 제외해 성공 30회를 채우는 재실행은 하지 않았다.

## 회차 폴더 읽는 법

| 파일 | 읽을 내용 |
|---|---|
| `transcript.md` | 시간순 실제 입력·응답과 전달·거절·제출 과정 |
| `Agent_A.md`, `Agent_B.md` | 해당 Agent의 관점에서 받은 입력과 실제 응답 |
| `observation.md` | 선택한 사후 검수의 주장·근거·대화 과정 |
| `result.json` | 최종 일정, 상태, 시간, 모델 사용량, 통신량 |
| `events.jsonl` | 발화·전송·제어 이벤트 원본 |

`observation.md`는 사후 검수이며 실험 중 상대 Agent에게 보낸 대화가 아니다. `source-report.md`는 실행 종료 당시 보고서다. 주석이 필요한 자연어의 당시 검수 대기 표시는 그대로 보존했으며, **현재 선택한 검수 결과는 각 회차의 `observation.md`와 `selected-review/`**에서 확인한다. `report.md`는 종료 당시 수치를 유지하며 단위명을 정리한 표시용 사본이다.

자연어의 모든 전달 메시지를 AI가 주석하고 작성자와 다른 AI가 전수 검토했다. 구조화 메시지는 전체 필드 자동 검산과 별도 AI의 산술·선택 원문 검토를 사용했다. 사람의 검수로 표시하지 않는다. 판정 항목 밖의 내용과 모호한 표현은 오류가 없다는 주장으로 바꾸지 않고 발췌·메모에 남겼다.

## 실행 조건과 검증 자료

- 실행: 2026-09-13 한국 시간, `gpt-5.6-luna` / `high`, Codex CLI `0.153.4`.
- 동일 실행 커밋: `13076ad4e2355c6ebceba40c67aa7dd584e9fe2e`. 방식별 worktree, 같은 회차 6개 병렬, 회차 안의 연구용 실행 상한 없음.
- 방식별 A 선발화 15회·B 선발화 15회, 서로 다른 세션 360개. 같은 머신·계정·서비스를 사용했으며 서비스 부하와 캐시 조건을 단계별로 통제하거나 초기화하지 않았다.
- [계획](execution-plan/plan.json), [종료 상태](execution-plan/state.json), [worktree와 중앙 원본 대조](worktree-equivalence.json).
- [선택한 원본·검수 목록](collection.json), [원본·검수 봉인과 세션 대조](analysis/integrity.json), [토큰·실제 패킷 검산](analysis/raw-measurement-audit.json), [일정과 대화 과정 독립 검산](analysis/process-summary.json).
- [자연어 초기 주석과 독립 검토](review-inputs/natural-language/README.md), [구조화 검토 범위](review-inputs/structured/README.md), [집계 도구와 재현 방법](analysis-tools/README.md).

각 방식 폴더에는 실행 코드 `source/`와 선택한 평가 코드·주석·봉인 `selected-review/`를 함께 보존했다. 아래 명령은 해당 방식 폴더에서 실행하며 모델을 호출하지 않는다. 출력은 기존 기록 밖의 새 폴더여야 한다.

```sh
python3 -B replay_review.py --export . --output ../new-review-replay
```

이는 선택한 주석의 판정과 집계가 재현되는지 확인하는 작업이다. 자연어 의미를 새로 독립 해석하거나 실험 Agent를 다시 실행하는 작업은 아니다.
