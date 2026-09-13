# 자연어 6회차 전체 task 메시지 AI 주석

- 검수자 유형: AI. 사람의 독립 검수는 후속 작업이다.
- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-06`
- 이벤트 SHA-256: `addbc0dfa891e770c6a9b362dba569ffd268991b4b3d676d0afa5511838d0c82`
- 주석: `/tmp/arc30-22772406666b/natural-annotations/trial-06.json`
- 범위: 종료된 trial-06의 실제 전달 task 메시지4개. stop 제어응답은 전달 메시지/주장으로 넣지 않았다.

## 메시지별 완전성

| 메시지 | 발신 | 직접 코딩한 주장 | 스키마 밖 또는 행동 표현 |
|---|---|---|---|
| 1 | B | 슬롯별 B팀 요약72개 | 없음 |
| 2 | A | distinct·precedence·총점20의3개 | 세 시간표기 대응, 동의 요청 |
| 3 | B | 지원 claim 없음; A팀 요약72개 질문 | B팀 전체 일정 기여10점 |
| 4 | A | A팀 요약72개·총점20·최대점수 평가의74개 | A/B팀 전체 일정 기여각10점, 동의 요청 |

전체149개 지원 주장이다. 요약 값은 정답 원자료가 아니라 발화에서 직접 파싱했다. 양팀 모두 세 회의·슬롯0–11을 직접 명시했으므로 누락 슬롯을 불가로 채운 주장은 없다. 개인별 값으로 분해하지 않았다.

## 발화값 보존과 내용 오류

메시지1 B의 M3 슬롯9는 실제 “slot 9 available, 2”라고 발화했다. 가용성1을 원문 그대로 기록했으며, 정답의0으로 대체하지 않았다. 다른 필드인 선호합2는 그대로 참이다. 이 틀린 팀가용성 주장의 반사실 영향은 아래 평가 결과에 따로 기록된다. 실제 Agent가 그 값을 믿었다고 추론하지 않는다.

```json
[
  {
    "type": "summary",
    "value": [
      "available",
      "B",
      "M3",
      9,
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
    "sender": "B",
    "evidence": "For B attendees of M3, they are: slot 0 available, 4; slot 1 unavailable, 4; slot 2 available, 1; slot 3 available, 4; slot 4 unavailable, 0; slot 5 available, 2; slot 6 available, 2; slot 7 available, 2; slot 8 available, 2; slot 9 available, 2; slot 10 available, 4; slot 11 available, 1.",
    "annotation_note": "실제 원문에서 직접 열거한 값을 전개. available/unavailable을 정답으로 대체하지 않았다."
  }
]
```

## 전체 팀 기여·시간표기 별도 검산

메시지3의 B-side10, 메시지4의 A-side10/B-side10은 **해당 팀의 모든 회의를 합한 일정 기여**다. 현재 summary는 한 회의에 대한 팀 기여이고 schedule_score는 양팀 전체 합이므로 어느 타입으로도 바꾸지 않았다. 별도 주장으로 메모에 남기고 아래에서 검산했다. 검산에 사용한 회의별 기여는 Agent가 이 문장에서 말한 새로운 숫자로 claim에 추가하지 않았다.

메시지2의 슬롯1=D1 10:00, 슬롯6=D2 09:00, 슬롯10=D2 14:00 대응은 현재 claim types가 시간 라벨을 표현하지 못해 공통 입력과 직접 대조했다. 모두 일치한다. 이 발췌가 unjudgeable에 있다는 이유로 거짓으로 해석하면 안 된다.

```json
{
  "schedule": {
    "M1": 1,
    "M2": 6,
    "M3": 10
  },
  "schedule_evaluation_for_post_run_check_only": {
    "valid": true,
    "score": 20,
    "violations": []
  },
  "A_whole_schedule_contribution": 10,
  "B_whole_schedule_contribution": 10,
  "team_contribution_details_for_post_run_check_only": {
    "A": {
      "M1": 2,
      "M2": 3,
      "M3": 5
    },
    "B": {
      "M1": 2,
      "M2": 4,
      "M3": 4
    }
  },
  "spoken_time_labels": {
    "1": "D1 10:00",
    "6": "D2 09:00",
    "10": "D2 14:00"
  }
}
```

## recommended maximum-scoring 해석

메시지4 “It remains my recommended maximum-scoring schedule;”의 It은 앞서 명시된1,6,10 후보다. “maximum-scoring”가 후보 자체를 수식하므로 **최대 점수 후보라는 명시적 평가**를 schedule_optimal=1로 기록했다. 단순히 “my recommended” 또는 “high-scoring”만 있었다면 최적성 단정으로 강화하지 않았을 것이다. 추천 태도와 최대점수 평가는 구분하며, 이 코딩이 내부에서 모든 후보를 검사했음을 뜻하지 않는다. 같은 후보 재추천이므로 변경 제안이나 상대 수락으로 기록하지 않았다.

## 종료와 전달 경계

원본은 status=stopped, operational_status=normal이며 B만 제출했다. 이후 A가wait하고 B가stop했다. B의 stop 이유 “Submitted the agreed maximum-scoring schedule.”는 제어 payload이고 peer task packet이 아니다. 이 문장을 동의·최적성·완료 주장으로 넣지 않았다.

```json
[
  {
    "actor": "B",
    "action": "submit",
    "payload": "",
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
    "payload": "",
    "schedule": []
  },
  {
    "actor": "B",
    "action": "stop",
    "payload": "Submitted the agreed maximum-scoring schedule.",
    "schedule": []
  }
]
```

유일한 제출1,6,10은 사후 검산상 유효한20점이지만, 두 Agent 제출 조건을 만족하지 못했으므로 과제 성공으로 바꾸지 않는다. 원본 evaluation=null을 주석으로 덮어쓰지 않았다.

## 임시 사본 검증

`write_trial_records`를 `/tmp` 임시 폴더에 실행해 전체 메시지 근거, events 해시, claim/question 타입과 평가를 확인했다. 임시 산출물은 제거했다. 원본 파일 해시는 검증 전후 일치했고 소스·설정·docs·원본 수정 및 모델 호출은 없었다.

```json
{
  "content_review_status": "complete",
  "task_messages": 4,
  "reviewed_messages": 4,
  "correct_claims": 148,
  "incorrect_claims": 1,
  "undetermined_claims": 0,
  "unjudgeable_expressions": 7,
  "codec_errors": 0,
  "first_proposer": "A",
  "changed_proposal_messages": 0,
  "explicit_revisions": 0,
  "accept_messages": 0,
  "completion": {
    "submitted_agents": [
      "B"
    ],
    "both_submitted": false,
    "identical_submissions": null,
    "task_status": "stopped",
    "error": "Submitted the agreed maximum-scoring schedule."
  }
}
```

스키마 밖 발췌7개는 시간라벨3개, 팀 전체합 발췌2개, 동의 요청2개다. 이는 오류7건이나 보류7개가 아니다. 지원 claim의 틀린값1개와 명확히 구분한다. 질문72개 전개는 앞서 전 슬롯의 모든 요약을 제시한 문맥에서 A팀의 대응 요약을 요청한 해석임을 notes에 공개했다. 이 AI 주석은 사람의 독립 검수나 내부 추론 검증을 대체하지 않는다.
