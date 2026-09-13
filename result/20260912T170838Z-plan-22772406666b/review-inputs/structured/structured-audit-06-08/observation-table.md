# 2~6단계 trial-06~08 임시 관찰표

종료된 15회만 사후 자동 대조했다. 현재 계획 전체의 최종 비교표가 아니다. 정/오/보류는 전달된 명시 주장 발생 횟수다. 첫 후보는 완전한 첫 propose이며, 제안 변경은 propose끼리의 배치 변경, revise는 실제 적용 사건이다. 질문 항목 수는 대화 횟수와 다르다.

| 단계/회차 | task 메시지 | 정/오/보류 | 첫 전체 후보 | 최종점수 | 변경/revise | 질문 | wait | 거절(task/setup) | 상세 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 2/06 | 4 | 147/0/1 | m2 A (5,6,10) 불가 | 20 | 1/1 | 2 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-2/trial-06/observation.md) |
| 2/07 | 2 | 144/0/0 | m2 B (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-2/trial-07/observation.md) |
| 2/08 | 2 | 144/0/0 | m2 A (1,6,10) 20점 | 20 | 0/0 | 0 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-2/trial-08/observation.md) |
| 3/06 | 3 | 144/0/0 | m2 A (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-3/trial-06/observation.md) |
| 3/07 | 2 | 133/11/0 | m2 B (7,6,10) 19점 | 19 | 0/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-3/trial-07/observation.md) |
| 3/08 | 3 | 144/0/0 | m3 B (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 1/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-3/trial-08/observation.md) |
| 4/06 | 6 | 147/0/0 | m3 B (1,6,10) 20점 | 20 | 1/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-4/trial-06/observation.md) |
| 4/07 | 5 | 154/0/0 | m3 A (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 1/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-4/trial-07/observation.md) |
| 4/08 | 2 | 144/0/0 | m2 A (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-4/trial-08/observation.md) |
| 5/06 | 2 | 144/0/0 | m2 A (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 1/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-5/trial-06/observation.md) |
| 5/07 | 2 | 144/0/0 | m2 B (1,6,10) 20점 | 20 | 0/0 | 72 | 2 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-5/trial-07/observation.md) |
| 5/08 | 4 | 144/0/0 | m2 A (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-5/trial-08/observation.md) |
| 6/06 | 3 | 146/0/0 | m4 A (1,6,10) 20점 | 20 | 0/0 | 72 | 1 | 1/1 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-6/trial-06/observation.md) |
| 6/07 | 3 | 144/0/0 | m4 B (1,6,10) 20점 | 20 | 0/0 | 72 | 0 | 0/0 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-6/trial-07/observation.md) |
| 6/08 | 3 | 144/0/0 | m6 B (1,6,10) 20점 | 20 | 0/0 | 74 | 0 | 3/2 | [관찰](/private/tmp/arc30-22772406666b/structured-audit-06-08/stage-6/trial-08/observation.md) |

15회 모두 양쪽 submit으로 완료되었다. 14회는 최적 20점, 3단계 trial-07은 유효한 19점(격차 1)이다. 46개 task 메시지: 정답 2167건, 오류 11건, 보류 1건, 코덱 오류 0건. 사전 합의 7개 패킷을 포함하면 전체 전달 메시지는 53개다.

96개 제어 응답 중 task에 적용된 동작은 send 45, revise 1, submit 30, wait 3, stop 0회다. setup 적용 7회와 거절 10회(task 7, setup 3)가 별도로 있다. 모든 거절 응답은 채널에 전달되지 않았다.

[과정 감사](/private/tmp/arc30-22772406666b/structured-audit-06-08/process-audit.md) · [제어 전체 순서](/private/tmp/arc30-22772406666b/structured-audit-06-08/control-timeline.md) · [거절 후속 행동](/private/tmp/arc30-22772406666b/structured-audit-06-08/rejection-followups.json) · [읽은 범위](/private/tmp/arc30-22772406666b/structured-audit-06-08/source-reading-log.json) · [원문 근거](/private/tmp/arc30-22772406666b/structured-audit-06-08/selected-source-evidence.md) · [검산](/private/tmp/arc30-22772406666b/structured-audit-06-08/verification.json)
