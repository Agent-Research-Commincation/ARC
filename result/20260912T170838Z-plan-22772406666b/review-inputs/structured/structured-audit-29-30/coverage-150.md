# 구조화150개 회차 감사 coverage

**2~6단계 × 1~30회차 =150개를 정확히 한 번씩 포함한다. 누락0·중복0·범위 밖0이다.** 단계별30개이며13개 감사 묶음에 저장돼 있다.

|감사 묶음|회차|대상 단계|건수|
|---|---|---|---:|
|structured-audit-01-05|01~05|2~6|25|
|structured-audit-06-08|06~08|2~6|15|
|structured-audit-09-11|09~11|2~6|15|
|structured-audit-12-14|12~14|2~6|15|
|structured-audit-15-17|15~17|2~6|15|
|structured-audit-18-19|18~19|2~6|10|
|structured-audit-20|20~20|2~6|5|
|structured-audit-21-22|21~22|2~6|10|
|structured-audit-23|23~23|2~6|5|
|structured-audit-24|24~24|2~6|5|
|structured-audit-25-26|25~26|2~6|10|
|structured-audit-27-28|27~28|2~6|10|
|structured-audit-29-30|29~30|2~6|10|

150개 모두 임시 observation.json, 감사 지표·원문 읽기 범위, 독립 최종 산술 검산 기록이 있다. 임시 관찰값과 감사 인덱스, 원본 result의 상태·점수·quality gap, 원본 task packet 수를 대조했다. 독립 최종 검산도150개를 정확히 한 번씩 포함하며 원본 판정과 일치한다.

모든 묶음은 같은 `observation-review-v3.1`과 같은 comparison group이다. 150개 원본 회차 파일은 각각 감사 당시 해시와 현재 해시가 같고, 현재 단계별 실행 소스도13개 묶음의 저장 해시와 같다. 중앙 복사본을 별도 회차로 세지 않았으며, 27~28 감사에 포함된 3/07의 추가 값 비교도 중복 감사 회차로 세지 않았다.

**이것은 자동 전체 대조와 선별 원문 독해의 coverage다. 모든 메시지의 완전 수동 전수검수라는 뜻은 아니다.** 직접 읽은 메시지 범위는 각 묶음의 source-reading-log.json에 있다. 기존150개를 다시 모델 실행하거나 새로운 평가기로 재채점하지 않았다.

[150행 원본·산출물 대응표](coverage-150.csv) · [검사 결과와 묶음별 해시](coverage-150.json).
