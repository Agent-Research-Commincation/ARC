# 자연어 2회차 원문 근거 검수 메모

- 범위: 종료된 자연어 trial-02의 실제 task 메시지 5개만 직접 읽었다. 다른 회차의 발화나 결과로 값을 채우지 않았다.
- 원본: /Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-02
- 이벤트 SHA-256: c55a93fb769dcae785d7d641e0282ee4652cb661154586a380bb7e65114077fb
- 주석: /tmp/arc30-22772406666b/natural-annotations/trial-02.json
- 검수자 유형: AI. 사람의 독립 검수 완료를 뜻하지 않는다.

## 관찰한 협업

B가 전체 팀 요약을 공유하고 A가 M1=1/M2=6/M3=10의 20점 시간표를 제안했다. B는 잠정적인 유효성과 점수의 양립 가능성을 언급하면서 A팀 전체 요약을 요청했다. A는 요약과 최적 점수 20점이라는 주장을 전달하며 M1=6/M2=11/M3=10도 20점이라고 덧붙였다. B는 주요 시간표를 수락하고 M1=6 대안은 A팀 불가 슬롯 때문에 무효라고 직접 정정했다. 최종 제출은 주요 시간표로 일치했다.

## 완결성과 보수적 해석

메시지 1은 각 슬롯 0–11을 번호와 함께 available/unavailable/점수로 모두 명시했다. 메시지 4 역시 0 through 11의 12쌍을 명시했다. 따라서 모든 0/1이 발화 근거를 가지며, 목록에 없다는 이유로 불가 값을 추가한 경우는 없다. 개인별 원자료 주장은 추론하지 않았다.

메시지 2의 괄호 4+7+9는 직전에 나열한 M1/M2/M3 순서의 점수 분해로 읽었다. “This is legal”과 전체 20점은 별도 명시 주장이다. 동의 요청 “Please confirm if you agree.”는 현재 질문 스키마가 agreement를 지원하지 않아 발췌로 남겼다.

메시지 3의 “The proposed schedule appears legal”은 잠정 표현이므로 단정적 유효성 1로 강제하지 않았다. “the reported total is consistent with my B-team summaries.”는 한 팀 자료와의 양립 표현이며, 그 자료만으로 전체 20점을 독립 검증했다는 뜻으로 확대하지 않았다. 두 표현은 unjudgeable 발췌로 보존했다. B의 선택 슬롯 선호합은 독립 검산에서 10이지만, 이 값을 B가 발화한 새 주장으로 추가하지 않았다. 요약 요청은 명시된 A팀 전체 회의/슬롯 72개 질문으로 전개했다.

메시지 4는 전체 상한 20점과 현재 후보 20점을 함께 말하므로 현재 후보의 최적성에 연결했다. 대안의 “also scores 20”은 후보 점수 주장으로만 기록했다. 직접 말하지 않은 대안의 legal=1이나 교체 제안을 추가하지 않았다.

메시지 5는 주요 후보 수락과 대안 무효 정정을 동시에 한다. 무효 대안은 메시지 4의 유일한 M1=6 후보에 연결했다. 팀 불가 원인을 구체적인 개인의 불가 주장으로 바꾸지 않았다.

## 판정 보류한 후보 점수

발췌: “M1 at slot 6, M2 at slot 11, M3 at slot 10 also scores 20.”

이 후보는 불가능하다. 원본 선호의 단순 산술합은 23으로 발화 20과 다르다. 다만 고정된 v3 지시가 불가능한 후보의 score 의미를 정의하지 않았으므로 현재 검수 정책은 correct=null/undetermined로 남기며 arithmetic_matches=false를 함께 보존한다. 집계의 incorrect_claims=0만 보고 모든 발화가 정확했다고 말하면 안 된다. B는 후속 발화에서 대안의 유효성 문제를 직접 정정했다.

```json
[
  {
    "type": "schedule_score",
    "value": {
      "schedule": {
        "M1": 6,
        "M2": 11,
        "M3": 10
      },
      "score": 20
    },
    "expected": null,
    "correct": null,
    "impact": null,
    "judgment": "undetermined",
    "candidate_valid": false,
    "arithmetic_sum": 23,
    "arithmetic_matches": false,
    "interpretation": "legacy_infeasible_score_unspecified",
    "impact_status": "not_evaluated",
    "message": 4,
    "sender": "A",
    "evidence": "M1 at slot 6, M2 at slot 11, M3 at slot 10 also scores 20.",
    "annotation_note": "Preserve the stated 20. The candidate is infeasible, so the frozen legacy scoring policy leaves correctness undetermined while separately calculating the arithmetic sum. Do not replace it with a valid candidate or assert legality that was not explicitly stated."
  }
]
```

실제 입력으로 진행한 독립 검산이다. 발화 값을 생성하는 데에는 사용하지 않았다.

```json
{
  "selected_schedule": {
    "valid": true,
    "score": 20,
    "violations": []
  },
  "alternative_schedule": {
    "valid": false,
    "score": null,
    "violations": [
      "Unavailable: A1 at M1"
    ]
  },
  "alternative_arithmetic_sum": 23,
  "actual_global_best": 20,
  "B_selected_team_preference_sum": 10,
  "A_M1_slot6_summary": {
    "available": 0,
    "preference": 6
  }
}
```

## 검증

원본 회차를 별도 TemporaryDirectory에 복사하고 해당 worktree의 manual_annotations/write_trial_records로 검증했다. 모든 entry/claim의 직접 발췌와 이벤트 해시가 받아들여졌다. 검증용 사본과 생성물은 종료 시 삭제했고, 원본 파일들의 전후 해시가 동일함을 확인했다. 프로젝트 소스·설정·docs·다른 회차는 수정하거나 검수하지 않았다.

```json
{
  "content_review_status": "complete",
  "task_messages": 5,
  "reviewed_messages": 5,
  "correct_claims": 156,
  "incorrect_claims": 0,
  "undetermined_claims": 1,
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
      "occurrences": 145,
      "judged": 145,
      "correct": 145,
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
      "occurrences": 4,
      "judged": 3,
      "correct": 3,
      "incorrect": 0,
      "undetermined": 1
    },
    "schedule_valid": {
      "occurrences": 3,
      "judged": 3,
      "correct": 3,
      "incorrect": 0,
      "undetermined": 0
    },
    "schedule_optimal": {
      "occurrences": 2,
      "judged": 2,
      "correct": 2,
      "incorrect": 0,
      "undetermined": 0
    },
    "meeting_score": {
      "occurrences": 3,
      "judged": 3,
      "correct": 3,
      "incorrect": 0,
      "undetermined": 0
    },
    "meeting_available": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    },
    "schedule_constraint": {
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
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
  "annotation_reviewer_kind": "ai"
}
```

직접 검수는 5개 메시지 모두 완료했다. 잠정 표현·동의 질문 3개와 불가능한 후보 점수 1개의 측정 한계는 위에 명시했다.
