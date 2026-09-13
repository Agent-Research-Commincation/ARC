# 자연어 1회차 원문 근거 검수 메모

- 범위: 종료된 stage-1 trial-01의 실제 task 메시지 4개만 직접 읽었다. 실험 Agent의 내부 추론은 검수하지 않았다.
- 검수 유형: AI 원문 검수이며 사람의 독립 검수 완료를 의미하지 않는다.
- 원본: /Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-01
- 이벤트 SHA-256: 5d9602977c7088a8b34e26d8ad24dd9d36fdf70de53e2d1cd8aa86d89ee42b7d
- 주석: /tmp/arc30-22772406666b/natural-annotations/trial-01.json
- 저장한 값은 발화에서 수동 전사했다. 입력 데이터는 그 이후의 독립 검산에만 사용했다.
- 모든 entry와 claim의 evidence가 실제 메시지 부분문자열인지 검증 함수가 확인했다.

## 의미 해석과 측정 한계

메시지1은 “Here are my team summaries by slot ID 0–11.”라는 도입과 각 회의의 완결 목록을 근거로 가용성 나열을 전체 팀 가용성 목록으로 해석했다. 따라서 나열되지 않은 슬롯을 그 목록의 여집합 0으로 전개했다. 문장에 only라는 단어가 직접 있는 것은 아니므로 이 완결 목록 해석을 독립 검수 시 확인할 수 있도록 명시한다. 개인별 원자료를 공유하지 않은 것은 오류가 아니며 개인 원자료 주장을 추가하지 않았다.

메시지2의 feasible/distinct/선후관계/20점은 별개 명시 주장으로 기록했다. 아직 optimal이라고 하지 않았으므로 최적성 주장은 추가하지 않았다.

메시지3의 “feasible against my availability”는 A팀의 세 선택 슬롯 가용성만으로 전개했다. 전체 일정 유효성으로 확대하지 않았다. “gives my team 10 preference points”는 팀의 전체 일정 합계이고 현 claim types에 직접 대응하는 유형이 없어 unjudgeable로 보존했다. 입력으로 독립 검산한 A팀 합계는 10이며, 발화 10과 일치한다. 합계의 구성 요소를 Agent가 따로 말했다고 간주해 새로운 선호 주장을 만들지는 않았다.

메시지3의 요청은 모든 B팀 회의/슬롯 요약을 달라는 선택지와 최적성 확인이라는 대체 선택지의 disjunction이다. questions의 72개 typed summary 요청은 첫 선택지만 나타내며 모두 필수라는 판정이 아니다. “or confirm the score of 20 is optimal.”는 최적성 주장 자체가 아니라 질문이므로 별도 발췌와 notes로 남겼다. references=[2]는 숫자 2를 직접 말한 것이 아니라 유일한 선행 제안의 재확인이라는 문맥 연결이다.

메시지4의 feasible combined scores는 개별 회의 슬롯의 가용성과 점수를 말한 뒤 전체 distinct/precedence 제약을 검토하는 구조다. 목록에 명시한 15개 슬롯의 가용성만 세고 생략 슬롯의 부정값은 추가하지 않았다. coverage 검산은 별도 메모이며 주장 수에 포함하지 않는다. 조건부 최대값 문장은 현 스키마의 schedule_optimal(하나의 완전 시간표)과 다르므로 발췌를 유지하고 아래에서만 검산했다.

## 스키마 밖 발췌의 독립 검산

1. “gives my team 10 preference points” → A팀 선택 슬롯 총점 10로 일치.
2. “or confirm the score of 20 is optimal.” → 요청이며 사실 주장으로 채점하지 않음.
3. “for M1 slots 1, 4, 7, and 9, the best totals are respectively 20, 18, 19, and 19.” → M1을 각 슬롯에 고정한 뒤 모든 법적 시간표를 열거해 검산:

```json
[
  {
    "M1_slot": 1,
    "spoken_best": 20,
    "computed_best": 20,
    "matches": true,
    "candidate_count": 19
  },
  {
    "M1_slot": 4,
    "spoken_best": 18,
    "computed_best": 18,
    "matches": true,
    "candidate_count": 15
  },
  {
    "M1_slot": 7,
    "spoken_best": 19,
    "computed_best": 19,
    "matches": true,
    "candidate_count": 11
  },
  {
    "M1_slot": 9,
    "spoken_best": 19,
    "computed_best": 19,
    "matches": true,
    "candidate_count": 9
  }
]
```

개별 회의 가용 슬롯 목록의 별도 coverage 확인:

```json
{
  "M1": {
    "spoken_slots": [
      1,
      4,
      7,
      9,
      11
    ],
    "actual_individually_available_slots": [
      1,
      4,
      7,
      9,
      11
    ]
  },
  "M2": {
    "spoken_slots": [
      2,
      4,
      6,
      7,
      11
    ],
    "actual_individually_available_slots": [
      2,
      4,
      6,
      7,
      11
    ]
  },
  "M3": {
    "spoken_slots": [
      0,
      5,
      8,
      10,
      11
    ],
    "actual_individually_available_slots": [
      0,
      5,
      8,
      10,
      11
    ]
  }
}
```

## 검증 결과

종료된 회차를 별도 TemporaryDirectory에 복사한 뒤 해당 worktree의 write_trial_records 및 manual_annotations 검증 함수를 사용했다. 검증용 사본과 생성물은 검증 종료 시 삭제했으며, 원본 회차 파일 해시가 전후 동일함을 확인했다. 프로젝트 소스·설정·문서·원본은 수정하지 않았다.

```json
{
  "content_review_status": "complete",
  "task_messages": 4,
  "reviewed_messages": 4,
  "correct_claims": 183,
  "incorrect_claims": 1,
  "undetermined_claims": 0,
  "unjudgeable_expressions": 3,
  "codec_errors": 0,
  "claim_counts_by_type": {
    "fact": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    },
    "summary": {
      "occurrences": 147,
      "judged": 147,
      "correct": 147,
      "incorrect": 0,
      "undetermined": 0
    },
    "reason": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    },
    "schedule_score": {
      "occurrences": 2,
      "judged": 2,
      "correct": 2,
      "incorrect": 0,
      "undetermined": 0
    },
    "schedule_valid": {
      "occurrences": 1,
      "judged": 1,
      "correct": 1,
      "incorrect": 0,
      "undetermined": 0
    },
    "schedule_optimal": {
      "occurrences": 1,
      "judged": 1,
      "correct": 1,
      "incorrect": 0,
      "undetermined": 0
    },
    "meeting_score": {
      "occurrences": 15,
      "judged": 15,
      "correct": 14,
      "incorrect": 1,
      "undetermined": 0
    },
    "meeting_available": {
      "occurrences": 15,
      "judged": 15,
      "correct": 15,
      "incorrect": 0,
      "undetermined": 0
    },
    "schedule_constraint": {
      "occurrences": 2,
      "judged": 2,
      "correct": 2,
      "incorrect": 0,
      "undetermined": 0
    },
    "public_precedence": {
      "occurrences": 1,
      "judged": 1,
      "correct": 1,
      "incorrect": 0,
      "undetermined": 0
    }
  },
  "annotation_reviewer_kind": "ai"
}
```

판정된 내용 오류:

```json
[
  {
    "type": "meeting_score",
    "value": {
      "meeting": "M3",
      "slot": 8,
      "score": 3
    },
    "expected": 5,
    "correct": false,
    "impact": null,
    "judgment": "incorrect",
    "impact_status": "not_evaluated",
    "message": 4,
    "sender": "B",
    "evidence": "M3: slot 0 = 6, 5 = 4, 8 = 3, 10 = 9, 11 = 4.",
    "annotation_note": "Per-meeting combined score explicitly stated. This is not the score of a complete schedule. In particular M3 slot 8 remains the spoken value 3."
  }
]
```

B의 메시지4는 M3 슬롯8의 전체 선호합계를 3이라고 말했으나 원본 참석자 선호합은 5다. 주석에는 발화값 3을 유지했다. 이 meeting_score 주장은 현 검증기가 사실·요약의 counterfactual 영향과 같은 방식으로 계산하지 않으므로 영향은 not_evaluated이며, 전체 성공과 최적20점이라는 결과만으로 이 내용 오류를 제거하지 않았다.

네 메시지의 직접 검수와 지원되는 의미의 주석은 완료했다. 스키마 밖의 세 표현과 완결 목록 해석은 위에 공개했으며, 의미적으로 어려운 부분을 자동 채점 완료로 숨기지 않았다.
