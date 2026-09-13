# 자연어 3회차 원문 근거 주석 검산 메모

- 검수자 유형: AI. 사람의 독립 검수 또는 실험 Agent의 내부 추론 검증이 아니다.
- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-03`
- events SHA-256: `bedf2e7a8e5fb1f6e7075356fa091d5aee95ac024137e651742d410fcf2bbf22`
- 기록 범위: 종료된 3회차의 실제 전달 메시지 3개. 제어 응답/전달 로그의 중복은 별도 발화로 세지 않았다.
- 작성 파일: `trial-03.json`. 원본과 프로젝트 파일은 수정하지 않았다.

## 지원 스키마로 전개한 주장

| 메시지 | 발신 | 분류 | 명시 요약 주장 | 그 밖의 명시 주장 |
|---|---|---|---:|---|
| 1 | A | inform | 72 | M1이 M3보다 선행하는 공통 규칙 1개 |
| 2 | B | inform, propose, request | 72 | 후보 합법성 1개, 총점 20점 1개 |
| 3 | A | accept | 0 | 동일 후보 합법성 1개, 총점 20점 1개 |

총 149개 주장이다. 두 팀 모두 M1/M2/M3의 슬롯 0~11을 (available, preference sum) 쌍으로 빠짐없이 명시했다. 이 값들은 발화에서 파싱했으며 정답 원자료로 대체하지 않았다. 가용성 0인 슬롯의 선호합도 원문 값 그대로 기록했다. 개인별 데이터 72개를 보낸 것으로 분류하지 않는다.

## 스키마 밖 표현과 별도 검산

1. 메시지 1: “The meetings overlap pairwise through shared attendees, so they need distinct slots.”
   현재 reason에는 특정 슬롯이, schedule_constraint에는 완전한 후보가 필요하다. 발화에 없는 슬롯이나 후보를 만들지 않았다. 공유 참석자는 아래와 같고 1시간 슬롯을 사용하는 이 문제에서는 서로 다른 슬롯이 필요하다는 일반 규칙이 성립한다.
   - M1 / M2: A2, B1
   - M1 / M3: A1
   - M2 / M3: B2
   주석의 unjudgeable은 여기서 스키마 표현 범위 밖이라는 의미다. 이 문장은 거짓이나 근거 부재로 판정하지 않았다.
2. 메시지 2: “My best combined legal schedule”은 자기 탐색 결과를 한정하는 표현이다. 명시된 합법성과 20점은 지원 주장으로 기록했으나 이 수식어를 전역 최적성 단정으로 강화하지 않았다.
3. 메시지 3: “I found no better schedule.” 역시 자기 탐색 보고다. 실제 내부 탐색의 완전성은 외부 원문으로 판정할 수 없다. 최종 후보가 실제 최적이라는 평가 결과와 이 문장의 입증 가능성을 구분한다.
4. “Please confirm or share any better candidate.”는 확인/대안 요청으로 request 분류에 반영했다. 원문에 없는 개인 ID, 유효성·점수 질의 또는 재검토 메시지 ID는 만들어 넣지 않았다.
5. “I will submit the same schedule.”는 미래 행동 의사로 별도 사실 주장 수에 넣지 않았다. 이후 원본에는 B와 A가 각각 M1=1, M2=6, M3=10을 제출한 행동이 기록돼 있다. 수락 발화 자체가 독립 검증이나 제출 완료를 뜻하지 않는다.

## 임시 검증 결과

현재 프로젝트의 `manual_annotations`/`write_trial_records`를 임시 폴더에 실행하여 입력 양식, events 해시, 발췌 근거, claim 타입과 평가를 확인했다. 임시 산출물은 검증 종료 후 제거했다.

```json
{
  "content_review_status": "complete",
  "reviewed_messages": 3,
  "task_messages": 3,
  "correct_claims": 149,
  "incorrect_claims": 0,
  "undetermined_claims": 0,
  "unjudgeable_expressions": 3,
  "codec_errors": 0,
  "first_proposer": "B",
  "changed_proposal_messages": 0,
  "explicit_revisions": 0,
  "accept_messages": 1
}
```

원본 파일별 해시는 검증 전후 일치했다. 명시된 지원 주장에서는 오류나 보류가 없었다. 3개의 unjudgeable 발췌는 위에서 설명한 표현 범위/자기 탐색 보고이며 오류 3건을 뜻하지 않는다. 이번 검수는 AI 1인의 주석이고 사람의 표본 재검수는 하지 않았다. 다른 회차 및 본실험 비교 통계는 작성하지 않았다.
