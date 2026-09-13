# 자연어 4회차 원문 근거 검수 메모

- 원본: /Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-04
- 이벤트 SHA-256: 545dcf941870b8637ab98ffce89009f89e2cb15e807e45b980558df8536a7df7
- 범위: 종료된 trial-04의 실제 task 메시지 5개만 직접 검수했다. 다른 회차의 발화나 정답으로 주석 값을 채우지 않았다.
- 주석: /tmp/arc30-22772406666b/natural-annotations/trial-04.json
- 검수 유형: AI. 사람의 독립 검수 완료를 의미하지 않는다.

## 관찰한 협업과 정정

B와 A가 전체 팀 요약을 교환했다. A는 1,6,10의 20점 후보를 제안했다. B는 9,6,10을 더 나은 합법 후보라며 22점이라고 제시했다. A는 그 후보의 실제 합계를 19점으로 계산하고 M1=3, M2=7, M3=9 및 각 팀의 구성값까지 전달했다. 이어 기존 1,6,10의 20점 후보를 재요청했다.

B는 메시지 4 뒤에 이미 1,6,10을 제출했다. A와 B가 각각 wait한 뒤 A가 메시지 5를 revise로 보내 수정 요청을 반복했다. B와 A는 같은 1,6,10을 다시 제출해 종료했다. 실제 제출을 명시적인 accept 메시지로 바꾸지 않았다. 메시지에는 accept 표현이 없다.

## 주석 원칙과 해석 한계

1. 두 팀 요약은 “slots 0 through 11”을 명시하고 12개 0/1 및 12개 점수를 직접 말한다. 빠진 슬롯을 불가로 채운 경우는 없다. 개인별 원자료를 추론하지 않았다.
2. “A high-scoring legal candidate”의 legal은 채점 가능한 유효성 주장이다. high-scoring은 기준이 없어 발췌와 notes로 남겼으며 optimal로 바꾸지 않았다.
3. “I checked the joint availability and preferences.”는 내부 검토 과정에 관한 자기 보고다. 실제 수행 여부는 메시지 로그만으로 검증할 수 없어 unjudgeable로 보존했다.
4. “A better legal candidate”의 better는 이전 20점 후보와의 비교지만 현 스키마에 후보간 비교 유형이 없다. 정확한 발췌를 보존하고 아래에서 별도로 비교했다. 실제로는 19점으로 이전 20점보다 낮으므로 better라는 비교는 맞지 않는다. 이를 별도의 scalar claim으로 만들어 중복 오류 집계하지 않았다.
5. 메시지 4는 9,6,10의 19점과 1,6,10의 20점을 명확히 구분했다. 같은 M2/M3 값의 반복은 발화 발생별로 보존했다. 팀별 구성 숫자도 직접 말한 값만 전개했다.
6. 메시지 5의 “not 22.”는 부정이다. A가 22점이라고 주장한 것처럼 추가하지 않았으며, 직접 주장한 값 19만 schedule_score에 넣었다. 부등식은 발췌와 별도 검산으로 남겼다.
7. 메시지 5는 실제 revise 행동이다. manual kinds의 지원 목록에는 revise가 없으므로 propose로 기록하고, explicit_revisions는 원본 제어 이벤트를 통해 계산했다. 동의 요청이나 최종 제출을 명시적 수락으로 추측하지 않았다.

## 내용 오류 및 스키마 밖 검산

B가 말한 9,6,10 후보는 유효하지만 22점이 아닌 19점이다. 유효한 후보 점수이므로 기존 검수 정책에서도 확정적인 incorrect다. 주석에는 발화값 22를 유지했다. A가 다음 메시지에서 직접 19점으로 바로잡았다는 사실도 별도로 남겼다.

```json
[
  {
    "type": "schedule_score",
    "value": {
      "schedule": {
        "M1": 9,
        "M2": 6,
        "M3": 10
      },
      "score": 22
    },
    "expected": 19,
    "correct": false,
    "impact": null,
    "judgment": "incorrect",
    "candidate_valid": true,
    "arithmetic_sum": 19,
    "arithmetic_matches": false,
    "interpretation": "feasible_candidate",
    "impact_status": "not_evaluated",
    "message": 3,
    "sender": "B",
    "evidence": "for 22 total points",
    "annotation_note": "Preserve B's stated 22 rather than replacing it with the later correction."
  }
]
```

실제 입력을 사용한 사후 검산이다. 발화 값을 생성하는 데에는 사용하지 않았다.

```json
{
  "message2_candidate": {
    "valid": true,
    "score": 20,
    "violations": []
  },
  "message3_candidate": {
    "valid": true,
    "score": 19,
    "violations": []
  },
  "better_than_message2": false,
  "message3_candidate_score_not_22": true
}
```

제어행동 순서:

```json
[
  {
    "actor": "B",
    "action": "send",
    "schedule": []
  },
  {
    "actor": "A",
    "action": "send",
    "schedule": []
  },
  {
    "actor": "B",
    "action": "send",
    "schedule": []
  },
  {
    "actor": "A",
    "action": "send",
    "schedule": []
  },
  {
    "actor": "B",
    "action": "submit",
    "schedule": [
      {
        "meeting": "M1",
        "slot": 1
      },
      {
        "meeting": "M2",
        "slot": 6
      },
      {
        "meeting": "M3",
        "slot": 10
      }
    ]
  },
  {
    "actor": "A",
    "action": "wait",
    "schedule": []
  },
  {
    "actor": "B",
    "action": "wait",
    "schedule": []
  },
  {
    "actor": "A",
    "action": "revise",
    "schedule": []
  },
  {
    "actor": "B",
    "action": "submit",
    "schedule": [
      {
        "meeting": "M1",
        "slot": 1
      },
      {
        "meeting": "M2",
        "slot": 6
      },
      {
        "meeting": "M3",
        "slot": 10
      }
    ]
  },
  {
    "actor": "A",
    "action": "submit",
    "schedule": [
      {
        "meeting": "M1",
        "slot": 1
      },
      {
        "meeting": "M2",
        "slot": 6
      },
      {
        "meeting": "M3",
        "slot": 10
      }
    ]
  }
]
```

## 임시 사본 검증

원본 회차를 별도 TemporaryDirectory에 복사한 뒤 해당 worktree의 manual_annotations/write_trial_records 함수로 검증했다. 모든 근거 발췌와 events_sha256이 받아들여졌다. 검증용 사본과 생성물은 종료 시 삭제했다. 원본 회차의 전후 파일 해시는 동일하며 실행 소스·설정·docs·다른 회차는 수정하거나 검수하지 않았다.

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
  "claim_counts_by_type": {
    "fact": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    },
    "summary": {
      "occurrences": 150,
      "judged": 150,
      "correct": 150,
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
      "occurrences": 6,
      "judged": 6,
      "correct": 5,
      "incorrect": 1,
      "undetermined": 0
    },
    "schedule_valid": {
      "occurrences": 2,
      "judged": 2,
      "correct": 2,
      "incorrect": 0,
      "undetermined": 0
    },
    "schedule_optimal": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    },
    "meeting_score": {
      "occurrences": 9,
      "judged": 9,
      "correct": 9,
      "incorrect": 0,
      "undetermined": 0
    },
    "meeting_available": {
      "occurrences": 6,
      "judged": 6,
      "correct": 6,
      "incorrect": 0,
      "undetermined": 0
    },
    "schedule_constraint": {
      "occurrences": 5,
      "judged": 5,
      "correct": 5,
      "incorrect": 0,
      "undetermined": 0
    },
    "public_precedence": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    }
  },
  "first_proposer": "A",
  "changed_proposal_messages": 2,
  "explicit_revisions": 1,
  "accept_messages": 0,
  "annotation_reviewer_kind": "ai"
}
```

지원되는 주장과 전체 메시지의 직접 검수는 완료했다. high-scoring, 내부 점검 보고, better 비교, not22 부정의 표현 범위는 위에 공개했다.
