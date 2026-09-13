# 3단계 · 논리식·관계 표현

실행 구분: experiment

상태: 완료 · 성공 30회 / 계획 30회 · 시도 30회 · 과제 실행 30회 · 인프라 오류 0회

| 핵심 지표 | 결과 |
|---|---|
| 과제 성공률·결과 품질 | 성공률 1.000000 · 성공한 결과의 최적 점수 차이 평균 0.067 (최소 0.000, 최대 1.000) |
| 성공 1건당 총비용 추정(USD) | 미측정/계산 불가 |
| 전체 완료 시간(초) | 성공한 실행 평균 226.257 (최소 126.843, 최대 518.397) · 모든 실행의 종료 시간 평균 226.257 (최소 126.843, 최대 518.397) |
| 실제 통신량(bytes/회차) | 평균 6072.633 (최소 2442.000, 최대 9430.000) |
| 통신 처리 비용 | 분리 측정한 로컬 처리 비용 합계 미측정/계산 불가 USD · 로컬 CPU 초/회차 평균 0.003 (최소 0.002, 최대 0.006) |

| 회차 | 상태 | 점수 | 최적해 차이 | 경과 시간(초) | 통신량(bytes) | 모델 비용 추정(USD) |
|---|---|---|---|---|---|---|
| 1 | success | 20 | 0 | 518.40 | 7853 | 0.049382 |
| 2 | success | 20 | 0 | 220.07 | 6817 | 0.017921 |
| 3 | success | 20 | 0 | 158.83 | 4560 | 0.013535 |
| 4 | success | 20 | 0 | 202.95 | 7242 | 0.017685 |
| 5 | success | 20 | 0 | 181.58 | 6741 | 0.014652 |
| 6 | success | 20 | 0 | 161.20 | 6338 | 0.012732 |
| 7 | success | 19 | 1 | 152.50 | 6185 | 0.011449 |
| 8 | success | 20 | 0 | 188.77 | 6307 | 0.014809 |
| 9 | success | 20 | 0 | 225.27 | 6569 | 0.017343 |
| 10 | success | 20 | 0 | 276.62 | 5301 | 0.025369 |
| 11 | success | 20 | 0 | 157.03 | 6185 | 0.011905 |
| 12 | success | 20 | 0 | 225.36 | 2442 | 0.019629 |
| 13 | success | 20 | 0 | 187.93 | 4339 | 0.014948 |
| 14 | success | 20 | 0 | 163.45 | 6339 | 0.012418 |
| 15 | success | 20 | 0 | 259.99 | 6344 | 0.022912 |
| 16 | success | 20 | 0 | 172.09 | 5423 | 0.013485 |
| 17 | success | 20 | 0 | 250.39 | 6431 | 0.019846 |
| 18 | success | 20 | 0 | 229.78 | 6497 | 0.019372 |
| 19 | success | 20 | 0 | 270.79 | 9430 | 0.023704 |
| 20 | success | 20 | 0 | 187.54 | 8761 | 0.015722 |
| 21 | success | 20 | 0 | 185.42 | 4130 | 0.014375 |
| 22 | success | 20 | 0 | 156.25 | 4129 | 0.012222 |
| 23 | success | 20 | 0 | 484.50 | 5078 | 0.042784 |
| 24 | success | 20 | 0 | 207.72 | 6116 | 0.017837 |
| 25 | success | 20 | 0 | 160.33 | 3976 | 0.011505 |
| 26 | success | 20 | 0 | 126.84 | 3976 | 0.009098 |
| 27 | success | 19 | 1 | 276.46 | 6602 | 0.023243 |
| 28 | success | 20 | 0 | 288.89 | 8557 | 0.024122 |
| 29 | success | 20 | 0 | 269.82 | 6927 | 0.024889 |
| 30 | success | 20 | 0 | 240.94 | 6584 | 0.020381 |

성공 1건당 총비용 추정(USD): None

관측 성공 비율에는 인프라·사용자 중단도 포함됩니다. 미실행·미확정 슬롯이 있으면 전체 비율은 계산하지 않습니다. 이 비율만으로 모델의 문제 해결 능력을 추정하지 않습니다.

모델 비용만의 성공 1건당 추정(USD): 0.018975861333333333

통신 처리 비용: 로컬 변환·해석 CPU 시간과 설정된 CPU 단가로 측정. 모델 호출 안의 작업 추론과 메시지 생성 비용은 분리 측정 불가.

`null`/`None`은 미측정 또는 계산 불가이며 0이 아닙니다. 금액은 API 단가 기반 추정이며 실제 구독 청구액이 아닙니다.

통신량은 로컬 메시지 채널의 본문+공통 헤더 바이트입니다. Base64 로그 저장 크기, 모델 API 전송량, TLS/IP 오버헤드는 포함하지 않습니다.

## 모델 처리량과 대화 기록

작업 메시지 송신 원문(bytes/회차): 평균 5501.700 (최소 1988.000, 최대 8856.000)

작업 메시지 수신 텍스트(bytes/회차): 평균 5501.700 (최소 1988.000, 최대 8856.000)

실행기 요청/턴 합계: 277회. 제공자 내부 호출이나 HTTP 요청 수는 아닙니다. 전체 입력·출력·캐시 토큰은 회차별 결과에 별도 기록합니다.

각 회차의 관찰표에서 정보 공유·제안·수정·내용 정확성·완료 절차를 확인합니다. 자연어 내용 검수는 수동 검수가 완료될 때까지 미측정으로 표시합니다.

- 1회차: [대화](trial-01/transcript.md) · [관찰표](trial-01/observation.md) · [A](trial-01/Agent_A.md) · [B](trial-01/Agent_B.md)
- 2회차: [대화](trial-02/transcript.md) · [관찰표](trial-02/observation.md) · [A](trial-02/Agent_A.md) · [B](trial-02/Agent_B.md)
- 3회차: [대화](trial-03/transcript.md) · [관찰표](trial-03/observation.md) · [A](trial-03/Agent_A.md) · [B](trial-03/Agent_B.md)
- 4회차: [대화](trial-04/transcript.md) · [관찰표](trial-04/observation.md) · [A](trial-04/Agent_A.md) · [B](trial-04/Agent_B.md)
- 5회차: [대화](trial-05/transcript.md) · [관찰표](trial-05/observation.md) · [A](trial-05/Agent_A.md) · [B](trial-05/Agent_B.md)
- 6회차: [대화](trial-06/transcript.md) · [관찰표](trial-06/observation.md) · [A](trial-06/Agent_A.md) · [B](trial-06/Agent_B.md)
- 7회차: [대화](trial-07/transcript.md) · [관찰표](trial-07/observation.md) · [A](trial-07/Agent_A.md) · [B](trial-07/Agent_B.md)
- 8회차: [대화](trial-08/transcript.md) · [관찰표](trial-08/observation.md) · [A](trial-08/Agent_A.md) · [B](trial-08/Agent_B.md)
- 9회차: [대화](trial-09/transcript.md) · [관찰표](trial-09/observation.md) · [A](trial-09/Agent_A.md) · [B](trial-09/Agent_B.md)
- 10회차: [대화](trial-10/transcript.md) · [관찰표](trial-10/observation.md) · [A](trial-10/Agent_A.md) · [B](trial-10/Agent_B.md)
- 11회차: [대화](trial-11/transcript.md) · [관찰표](trial-11/observation.md) · [A](trial-11/Agent_A.md) · [B](trial-11/Agent_B.md)
- 12회차: [대화](trial-12/transcript.md) · [관찰표](trial-12/observation.md) · [A](trial-12/Agent_A.md) · [B](trial-12/Agent_B.md)
- 13회차: [대화](trial-13/transcript.md) · [관찰표](trial-13/observation.md) · [A](trial-13/Agent_A.md) · [B](trial-13/Agent_B.md)
- 14회차: [대화](trial-14/transcript.md) · [관찰표](trial-14/observation.md) · [A](trial-14/Agent_A.md) · [B](trial-14/Agent_B.md)
- 15회차: [대화](trial-15/transcript.md) · [관찰표](trial-15/observation.md) · [A](trial-15/Agent_A.md) · [B](trial-15/Agent_B.md)
- 16회차: [대화](trial-16/transcript.md) · [관찰표](trial-16/observation.md) · [A](trial-16/Agent_A.md) · [B](trial-16/Agent_B.md)
- 17회차: [대화](trial-17/transcript.md) · [관찰표](trial-17/observation.md) · [A](trial-17/Agent_A.md) · [B](trial-17/Agent_B.md)
- 18회차: [대화](trial-18/transcript.md) · [관찰표](trial-18/observation.md) · [A](trial-18/Agent_A.md) · [B](trial-18/Agent_B.md)
- 19회차: [대화](trial-19/transcript.md) · [관찰표](trial-19/observation.md) · [A](trial-19/Agent_A.md) · [B](trial-19/Agent_B.md)
- 20회차: [대화](trial-20/transcript.md) · [관찰표](trial-20/observation.md) · [A](trial-20/Agent_A.md) · [B](trial-20/Agent_B.md)
- 21회차: [대화](trial-21/transcript.md) · [관찰표](trial-21/observation.md) · [A](trial-21/Agent_A.md) · [B](trial-21/Agent_B.md)
- 22회차: [대화](trial-22/transcript.md) · [관찰표](trial-22/observation.md) · [A](trial-22/Agent_A.md) · [B](trial-22/Agent_B.md)
- 23회차: [대화](trial-23/transcript.md) · [관찰표](trial-23/observation.md) · [A](trial-23/Agent_A.md) · [B](trial-23/Agent_B.md)
- 24회차: [대화](trial-24/transcript.md) · [관찰표](trial-24/observation.md) · [A](trial-24/Agent_A.md) · [B](trial-24/Agent_B.md)
- 25회차: [대화](trial-25/transcript.md) · [관찰표](trial-25/observation.md) · [A](trial-25/Agent_A.md) · [B](trial-25/Agent_B.md)
- 26회차: [대화](trial-26/transcript.md) · [관찰표](trial-26/observation.md) · [A](trial-26/Agent_A.md) · [B](trial-26/Agent_B.md)
- 27회차: [대화](trial-27/transcript.md) · [관찰표](trial-27/observation.md) · [A](trial-27/Agent_A.md) · [B](trial-27/Agent_B.md)
- 28회차: [대화](trial-28/transcript.md) · [관찰표](trial-28/observation.md) · [A](trial-28/Agent_A.md) · [B](trial-28/Agent_B.md)
- 29회차: [대화](trial-29/transcript.md) · [관찰표](trial-29/observation.md) · [A](trial-29/Agent_A.md) · [B](trial-29/Agent_B.md)
- 30회차: [대화](trial-30/transcript.md) · [관찰표](trial-30/observation.md) · [A](trial-30/Agent_A.md) · [B](trial-30/Agent_B.md)

실행기 요청/턴은 제공자 내부 호출 수나 HTTP 요청 수가 아닙니다. 사용량 갱신 횟수와도 구분합니다. 수치는 종료 당시 값을 유지하며, 원문은 [source-report.md](source-report.md)에 있습니다.
