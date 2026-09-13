# 자연어 5회차 원문 근거 검수 메모

- 원본: /Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-05
- 이벤트 SHA-256: 9e9737f3fe706586e73688ebb4a65baed561605808a689d1268b1fc74629c3da
- 주석: /tmp/arc30-22772406666b/natural-annotations/trial-05.json
- 범위: 종료된 trial-05의 실제 task 메시지 4개만 직접 읽었다. 다른 회차의 발화나 정답으로 값을 채우지 않았다.
- 검수 유형: AI. 사람의 독립 검수 완료를 뜻하지 않는다.

## 실제 소통

A가 전체 팀 요약을 공유하고 B팀 요약을 요청했다. B는 자기 팀 요약을 전달하면서 앞으로 전체 점수를 비교하겠다고 말했다. A는 요약에 따른 최선의 법적 시간표라며 M1=1/M2=6/M3=10의 20점 후보를 제안했다. B는 같은 배치를 명시적으로 확인하고 제출하겠다고 응답했다. 실제 결과에서도 두 제출이 일치했다.

## 원문과 주석의 경계

메시지 1과 2는 각 슬롯 0–11을 번호와 available/unavailable 및 점수로 모두 직접 열거한다. 따라서 가용성의 부정값은 직접 발화 근거가 있으며, 빠진 슬롯을 불가로 추가한 경우가 없다. 팀 요약을 개인별 원자료 주장으로 바꾸지 않았다.

A는 메시지 1의 M1 슬롯 2를 “2 available, 3”이라고 직접 말했다. 주석은 available=1을 그대로 보존했다. 실제 A팀 M1 가용성은 0이므로 이는 명시된 내용 오류다. 선호값 3은 별도 주장으로 기록했고 오류 없이 일치한다.

“I will now compare combined totals to identify the best legal schedule.”는 B의 앞으로의 비교 계획이다. 이미 탐색을 마쳤다거나 전역 최적성을 확인했다는 주장으로 강화하지 않았다. 이 계획의 실제 실행 여부는 내부 추론에서 추정하지 않는다.

A의 메시지 3은 반대로 “The best legal schedule from these summaries is …”라고 직접 단정한다. 따라서 후보의 legal과 best를 각각 기록하되 from these summaries라는 범위를 note에 보존했다. 4+7+9는 직전에 나열한 M1/M2/M3 순서의 점수 분해로 읽었다. 직접 발화되지 않은 최적 점수나 개인별 점수를 추가하지 않았다.

“Please confirm, and then we should both submit this exact schedule.”는 동의 확인과 후속 제출 요청이며 아직 상대가 수락했다는 말이 아니다. 현재 typed questions에 agreement/submit 유형이 없어 전체 발췌와 메모로 보존했다.

B의 “Confirmed”는 명시적인 수락이다. “I will submit this exact schedule.”는 앞으로의 행동 약속이므로 메시지 시점에 이미 제출했다는 사실로 세지 않았다. B가 최적이라고 재단정하지 않았으므로 B의 별도 schedule_optimal 주장은 만들지 않았다.

## 내용 오류와 사후 검산

```json
[
  {
    "type": "summary",
    "value": [
      "available",
      "A",
      "M1",
      2,
      1
    ],
    "expected": 0,
    "correct": false,
    "impact": {
      "method": "isolated counterfactual; other claims unchanged",
      "feasible_set_changed": true,
      "schedule_scores_changed": true,
      "optimal_score_before": 20,
      "optimal_score_after": 20,
      "optimal_schedules_changed": false,
      "submitted_schedule_affected": false,
      "submission_impact_status": "evaluated"
    },
    "judgment": "incorrect",
    "impact_status": "evaluated",
    "message": 1,
    "sender": "A",
    "evidence": "M1: slot 0 unavailable, 4 points; 1 available, 2; 2 available, 3; 3 available, 3; 4 available, 0; 5 unavailable, 5; 6 unavailable, 6; 7 available, 2; 8 available, 6; 9 available, 3; 10 unavailable, 4; 11 available, 5.",
    "annotation_note": "Each slot 0 through 11 is explicitly numbered and described. Values are the spoken availability and team preference total; no complement or omitted-person assertion is inferred. M1 slot 2 remains the spoken available=1."
  }
]
```

오류가 있는 A팀 요약을 따르는 경우와 원본 입력을 따르는 경우를 각각 검산했다. 선택한 시간표와 최고 점수 20은 양쪽에서 같지만, 가용성 오류로 다른 후보의 유효 집합이나 점수가 바뀔 수 있다. 영향 결과는 해당 주장 하나만 바꾼 사후 계산이며 실제 Agent가 그 주장을 믿었다는 뜻이 아니다.

```json
{
  "original_candidate_evaluation": {
    "valid": true,
    "score": 20,
    "violations": []
  },
  "original_best": 20,
  "shared_summary_counterfactual_best": 20,
  "candidate_score_under_shared_summary_counterfactual": 20,
  "counterfactual_scope": "All other explicit team summary claims agree with the input; only the spoken A/M1/2 availability is replaced. This does not prove an agent believed it."
}
```

## 검증

별도 TemporaryDirectory에 종료된 원본 회차를 복사하고 해당 worktree의 manual_annotations/write_trial_records로 검증했다. events_sha256과 모든 entry/claim의 직접 발췌가 받아들여졌다. 검증용 사본과 생성물은 끝나면 삭제했으며, 원본 회차의 전후 파일 해시가 동일함을 확인했다. 프로젝트 실행 소스·설정·docs·다른 회차·실제 실험에는 변경이나 메시지를 전달하지 않았다.

```json
{
  "content_review_status": "complete",
  "task_messages": 4,
  "reviewed_messages": 4,
  "correct_claims": 156,
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
      "occurrences": 144,
      "judged": 144,
      "correct": 143,
      "incorrect": 1,
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
      "occurrences": 2,
      "judged": 2,
      "correct": 2,
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
      "occurrences": 3,
      "judged": 3,
      "correct": 3,
      "incorrect": 0,
      "undetermined": 0
    },
    "meeting_available": {
      "occurrences": 3,
      "judged": 3,
      "correct": 3,
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
      "occurrences": 0,
      "judged": 0,
      "correct": null,
      "incorrect": null,
      "undetermined": 0
    }
  },
  "first_proposer": "A",
  "changed_proposal_messages": 0,
  "explicit_revisions": 0,
  "accept_messages": 1,
  "annotation_reviewer_kind": "ai"
}
```

4개 메시지의 직접 검수는 완료했다. 향후 탐색 계획, 동의 및 제출 요청, 미래 제출 약속의 세 표현은 스키마 밖 의미로 정확한 발췌와 설명을 유지했다.
