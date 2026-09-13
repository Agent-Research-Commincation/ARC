# 집계와 검증 자료

[실험 보고서](../../../docs/experiment-report.md) · [180회 대화](../README.md) · [상세 측정표](metrics.md)

| 자료 | 내용 |
|---|---|
| [회차별 수치](trial_rows.json) | 실제 180회와 선택한 검수의 지표 |
| [방식별 통계](stage_summary.json) | 평균·중앙값·범위·측정 수·성공당 모델 비용 |
| [선택본 결합과 세션](integrity.json) | 원본·검수 봉인, 같은 조건, 고유 세션 360개 |
| [독립 AI 최종 대조](final-report-verification.md) | 원본·선택 주석·보존 평가기·최신 보고서의 수치와 해석 확인 |
| [원시 측정값 검산](raw-measurement-audit.json) | 제공자 사용량, 모델 비용, 실제 패킷 본문·헤더와 사전 합의 연결 |
| [일정과 과정 검산](process-summary.json) | 독립 완전 탐색, 첫 후보·최종 결과·검수된 주장 |
| [제어 행동 집계](control-summary.md) | 전달·거절 구간, 제출·대기·종료·실제 제출 취소 |
| [사용량 갱신 진단](usage-update-diagnostic.md) | 6단계 9회차 B의 반복 사용량 알림과 비용 영향 확인 |

단순 `last` 사용량 알림 합산은 6단계 9회차 B에서 같은 사용량을 두 번 세게 된다. 이전 스냅샷과 같은 알림이 다시 왔고 누적 `total`은 증가하지 않았다. 보고 비용은 최종 누적 `total`을 사용하므로 영향이 없다. 원문은 수정하지 않았으며 세부 갱신과 검산을 진단 자료에 보존했다.

모든 회차의 작업 메시지 검수는 완료 상태이며, 자연어의 판정 범위 밖·모호한 표현은 별도 기록한다. 내용 오류는 총 63개 주장 발생이며 같은 값의 반복도 포함한다. 이 숫자로 방식의 정확도를 순위 매기지 않는다. 작업 메시지 627개와 사전 메시지 62개는 모델 응답 요청 1,195회와 단위가 다르다.

각 방식의 보존된 평가 코드로 30회씩 재현한 결과는 다음과 같다. 이는 선택한 주석의 재현이지 새로운 독립 의미 주석이 아니다.

- [자연어 재현](replays/stage-01-natural-language/replay.json)
- [JSON 재현](replays/stage-02-json/replay.json)
- [논리식 재현](replays/stage-03-relations/replay.json)
- [고정 벡터 재현](replays/stage-04-fixed-vector/replay.json)
- [바이트코드 재현](replays/stage-05-bytecode/replay.json)
- [공동 언어 재현](replays/stage-06-shared-dictionary/replay.json)

실험 A·B의 비용과 사후 AI 검토·문서 작성 비용은 구분한다. 현재 비용 표는 전자에 고정 API 단가를 적용한 추정이며 실제 구독 청구액이 아니다. 집계를 다시 실행하려면 [도구 안내](../analysis-tools/README.md)를 따른다.
