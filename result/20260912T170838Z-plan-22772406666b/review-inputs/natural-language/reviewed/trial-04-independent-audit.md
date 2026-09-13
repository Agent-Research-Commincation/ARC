# 자연어 4회차 독립 AI 검토

원문 task 메시지 5개를 먼저 직접 읽고 다른 작성자의 초안과 대조했다. 이는 AI 독립 검토이며 사람 검수나 실험 Agent의 숨은 추론 검증이 아니다.

- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-04`
- events SHA-256: `545dcf941870b8637ab98ffce89009f89e2cb15e807e45b980558df8536a7df7`
- 초안: `/tmp/arc30-22772406666b/natural-annotations/trial-04.json`
- 초안 SHA-256: `fc6178ed0eebea545d1cab334ada021f6bc80cad8e8e911190aac827618a8eef`
- 검토 완료본: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-04.json`
- 검산 기록: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-04-independent-validation.json`

## 결론과 변경 범위

빠진 지원 스키마의 명시 주장, 값 전사 오류, 증거 발췌 불일치, 생략 슬롯 추론, 부정을 긍정으로 바꾼 오류를 발견하지 못했다. 초안 entries의 주장·질문·분류를 유지했으며 reviewer에 독립 AI 검토 정보를 추가했다. 초안과 원본은 변경하지 않았다.

## 메시지별 대조

1. B가 슬롯0–11의 가용성 및 선호합을 각각 12개 배열로 명시했다. 원문 배열에서 독립 파싱한 72개 팀 요약값이 초안과 전부 일치했다. “corresponding team A summaries” 요청은 바로 제시한 세 회의·전 슬롯·두 관계에 대응하는 A팀 요약72개 질문으로 적절하게 연결됐다. 개인 원자료 요청으로 바꾸지 않았다.
2. A팀 배열72개도 원문 독립 전사와 일치했다. (1,6,10)의 legal, 20점, M1 before M3를 분리한 주장이 발화에 근거한다. “high-scoring”을 전역 최적성 주장으로 강화하지 않았다.
3. B는 (9,6,10)을 제안하며 **22점**이라고 실제로 말했다. legal, 세 회의 가용성, distinct, precedence도 직접 명시됐다. “I checked”는 숨은 검토 절차를 검증했다고 주장하지 않고 발췌로 남겼다. “better”는 상대 비교 유형이 현재 스키마에 없어 별도 검산하며 중복 scalar 오류를 추가하지 않았다.
4. A는 (9,6,10)의 **19점**과 (1,6,10)의 **20점**을 분명히 구분했다. M1/M2/M3의 점수와 A/B팀별 숫자도 모두 직접 발화했다. 반복된 M2/M3 점수를 발생별로 보존한 점과 가용성·distinct·precedence의 대상이 후반부 (1,6,10)이라는 점을 확인했다.
5. A는 (1,6,10)으로 수정해 달라고 하고 20=4+7+9 및 이전 후보19점을 반복했다. “not 22”를 A의 긍정적인22점 주장으로 새로 세지 않았다. revise 제어행동은 원본에서1회 확인됐으며 자연어 kinds와 실제 제어행동을 구분했다. 수락 발화가 없는데 accept를 추가하지 않았다.

## 유효 후보 점수 오류와 정책

이번 B의 (9,6,10) 후보는 **유효한 일정**이다. 따라서 점수22 발화는 기존 정책에서도 판정 보류가 아니라 확정 오류다. 독립 채점과 단순 산술합은 모두19이다. 바로 앞 A의 후보20점보다 낮으므로 “better” 비교도 실제와 다르다. 이 비교는 지원 스키마 밖 검산으로 기록하고 별도 오류 수를 만들지 않았다.

A의 후속19점 정정은 정확하다. 초안에 B의 원래22점과 A의19점이 각각 남아 있어 오류를 사후 정답으로 덮어쓰지 않았다. 최종 양쪽 제출은 (1,6,10)으로 실제 평가20점이다. 불가능 후보의 score 정의가 불명확할 때 적용하는 null 정책을 이 유효 후보에 잘못 적용하지 않았다.

## 임시 평가기 검증

`write_trial_records`를 임시 폴더에 실행하여 events 해시·직접 발췌·주석 양식·사후 평가를 확인했다. 임시 산출물은 검증 후 제거했다.

```json
{
  "content_review_status": "complete",
  "task_messages": 5,
  "reviewed_messages": 5,
  "correct_claims": 177,
  "incorrect_claims": 1,
  "undetermined_claims": 0,
  "unjudgeable_expressions": 4,
  "codec_errors": 0,
  "first_proposer": "A",
  "changed_proposal_messages": 2,
  "explicit_revisions": 1,
  "accept_messages": 0
}
```

독립 검산:

```json
{
  "candidate_1_6_10": {
    "valid": true,
    "score": 20,
    "violations": []
  },
  "candidate_9_6_10": {
    "valid": true,
    "score": 19,
    "violations": []
  },
  "candidate_9_6_10_arithmetic_sum": 19,
  "better_than_previous_candidate": false,
  "original_and_draft_hashes_unchanged": true,
  "annotation_claims_unchanged": true
}
```

세부 오류, 이벤트 제어행동 및 해시는 별도 검산 JSON에 남겼다. 원본과 초안·초안 메모 해시는 검증 전후 일치했다. 프로젝트 소스·설정·docs·원본 수정이나 모델 재실행은 없었다.

## 해석 한계

high-scoring, I checked, better, not22의 4개 발췌는 스키마 표현 범위의 한계이며 오류4건을 뜻하지 않는다. 메시지5의 4+7+9는 직전 M1/M2/M3 순서로 읽는 문맥 해석임을 초안 notes가 공개한다. 이 작업은 사람의 독립 표본 검토를 대체하지 않는다.
