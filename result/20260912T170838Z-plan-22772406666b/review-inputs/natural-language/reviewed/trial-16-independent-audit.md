# trial-16 독립 AI 전수 검수

검수자 Codex /root/stages_5_6가 /root/stages_1_2 초안을 이번 실제 전달 task 원문 전체와 독립 대조했다. 사람 검수로 표시하지 않는다.

원본: /Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-16

events SHA-256: 2ce5b50f15f31e1da163b706d4040c703c82e92143797182321b2b9a8a02da66

## 결과와 수정 범위

task 메시지 3개, 명시 주장 149개(72·72·5)를 모두 검수했다. 정확 149개, 오류 0개, 의미 보류 0개이며 스키마 밖 발췌 8개와 코덱 오류 0개는 별도다. 초안 의미 필드·발화값·evidence는 모두 유지하고 reviewer와 독립 검수 메모만 보완했다.

두 팀 요약 144개는 이번 원문의 명시된 슬롯 0–11 배열을 직접 읽고 따로 전개해 초안과 전수 대조했다. 원자료는 그 다음 정확성 검산에만 사용했다. 생략 슬롯을 불가로 추가하거나 다른 회차·원자료로 발화를 대체하지 않았다. 모든 발췌는 해당 receiver_text의 정확한 부분 문자열이다.

## 메시지별 의미

1. B의 세 회의 요약은 각각 자기 팀 참석자의 가용성·선호합이다. 요청 “Please share your team summaries so we can find the highest-scoring legal schedule.”의 summaries 범위는 바로 앞 3회의·12슬롯·두 관계를 받는 것으로 읽어 A 요약 질문 72개를 유지했다. 이는 문맥 범위 해석이며 원문이 72라는 숫자를 말한 것은 아니다. “so we can find”는 협업 목표이며 현재 최적성·탐색 완료 주장으로 만들지 않았다.
2. A의 “Please share a candidate schedule or let me know if you want me to search for the highest-scoring one.”은 후보를 보내거나 A가 탐색할지 알려 달라는 OR 요청이다. 지원 question 유형이 없어 request와 전체 발췌만 유지했다. 두 의무를 동시에 요구한다고 바꾸거나 실제 탐색·후보·최적성 주장으로 추가하지 않았다.
3. B의 “The highest-scoring legal schedule from the shared summaries is M1 at slot 1, M2 at slot 6, and M3 at slot 10”은 현재 후보의 명시적 최적성·유효성 주장이다. “from the shared summaries”의 근거 범위는 유지한다. 실제 공유 요약만 이용한 사후 전수검산도 원자료 기준과 동일한 가능 일정 54개와 유일한 20점 최적 일정 1/6/10을 내므로 이 회차에서 범위 차이가 판정을 바꾸지 않는다. Agent가 내부적으로 완전 탐색했는지는 알 수 없다.
4. “It is valid”는 첫 문장의 legal과 별도 문장에서 다시 발화한 유효성 발생으로 유지했다. 같은 후보의 distinct·각 회의 availability까지 추가 분해하지 않았다. “respects M1 before M3”는 후보 선후관계 만족이고 “scores 20 total.”은 총점 주장이다. 회의별 점수·개인 사실을 합계에서 새 발화로 만들지 않았다.

## 스키마 밖 8개

- “M1 (B1)”, “M2 (B1+B2)”, “M3 (B2+B3)”는 B팀 참석자 구성이다. 공개 참석자와 B팀 소속의 교집합으로 확인해 각각 일치했다. 전체 회의 참석자가 이들뿐이라는 뜻으로 해석하지 않았다. M1의 요약값이 B1 값과 같아도 개인 fact를 중복 추가하지 않았다.
- 위 A의 OR 요청 한 문장은 자료 질문과 다른 제어·협업 요청이므로 타입을 만들어 넣지 않았다.
- “D1 10:00”, “D2 09:00”, “D2 14:00”은 직전 M1/M2/M3 순서와 연결되는 것으로 읽었다. 이 대응은 문맥 순서 해석임을 공개하며 공개 슬롯1·6·10 라벨과 각각 일치했다. 현재 스키마에 시간 라벨 claim이 없어 발췌와 별도 검산으로 보존했다.
- “Please confirm and submit this exact schedule.”은 확인과 제출을 요청하는 말이다. 실제 수락 발화나 제어 제출이 이미 있었다는 주장으로 바꾸지 않았다.

이 8개는 오류 수가 아니다. 참석자 구성과 시간 라벨 6개는 별도 검산에서 맞았고, 두 요청은 사실 참·거짓 판정 대상이 아니다. 검수 JSON에 각 발췌·해석·비교값을 남겼다.

## 사후 평가와 행동 경계

원자료와 독립 전수계산 모두 후보 {'M1': 1, 'M2': 6, 'M3': 10}의 유효성 참·점수20을 확인했다. 불가능 후보 점수는 항상 의미 보류하는 기존 정책을 유지하며 이번에는 그 대상 발화가 없다.

task 패킷은 B 요약 → A 요약 → B 후보 제안의 3개다. 이후 제어 A submit(이벤트641), B submit(이벤트696)에서 양측이 같은 후보를 제출했다. 전송 accept는0개, 변경 제안0개, 실제 revise0개이며 submit을 추가 task 메시지나 수락 발화로 세지 않았다. 원본 success/normal과 평가20을 유지했다. 잠재 추론·실제 이해·미관찰 탐색완전성은 판단하지 않는다.

## 임시 검증과 보존

임시 사본에서 write_trial_records에 최종 주석을 넣어 전체 메시지 대응·정확한 evidence·events 해시·claim/question schema를 검증했다. 모든 149개 주장에 대한 독립 검산 expected/correct가 기존 검증 함수와 일치했다. 검증 사본은 제거했다.

원본 전체 파일 해시, 초안 바이트, 코어 snapshot은 전후 동일하다. 실험·모델 추가 실행이나 원본·코어·설정·docs 변경은 없다.

최종 주석: /tmp/arc30-22772406666b/natural-annotations/reviewed/trial-16.json

검산·감사 검증 JSON: /tmp/arc30-22772406666b/natural-annotations/reviewed/trial-16-independent-validation.json
