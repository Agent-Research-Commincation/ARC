# 자연어 12회차 전체 task 메시지 AI 초기 주석

- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-12`
- events SHA-256: `10450c479c7788a82b892ad78bf43e463481586c8f65b6b567ded8605a5c2082`
- 주석: `/tmp/arc30-22772406666b/natural-annotations/trial-12.json`
- 검수 유형: AI 초기 주석. 독립 재검수와 사람 검수는 아직 이 산출물의 범위가 아니다.
- task 메시지 6개를 모두 직접 읽고 주석화했다. 제어 응답과 전송 packet 중복을 각각의 추가 발화로 세지 않았다.

## 명시 주장 범위

| 메시지 | 발신 | 범위 | 주장 수 |
|---|---|---|---:|
| 1 | B | 개인 가용성 긍정 31개 + 선호 36개 | 67 |
| 2 | A | 개인 가용성 긍정 29개 + 선호 36개, 8/6/10 후보 legal·선후관계·24점 | 68 |
| 3 | B | 기존 후보 무효성·불가 원인, 회의별 가능 슬롯 및 점수 30개, 새 후보 관련 5개 | 37 |
| 4 | A | 기존 후보 무효성 인정, 새 후보 가용성·제약·점수, M1 슬롯 9 설명, M3 재계산 | 17 |
| 5 | A | 동일 후보 20점 및 alignment 요청 | 1 |
| 6 | B | 동일 후보 20점 및 Confirmed | 1 |

전체 191개 주장이다. 원문을 읽은 뒤 숫자 목록만 코드로 전개했다. 원자료로 발화값을 바꾸지 않았다. A2/A3 선호의 생략된 슬롯 범위는 같은 메시지의 첫 A1 문장 및 공통 슬롯 범위에 대응하며 12개 값을 순서대로 보존했다.

가용성 목록에는 only/exactly/그 외 불가가 명시되지 않았다. 열거한 슬롯은 직접 긍정으로 전개하고, 생략한 슬롯은 부정 사실로 생성하지 않았다. 전체 목록으로 읽을 여지는 있으므로 여섯 문장을 발췌하고 범위 불확실성을 기록했다. B의 feasible slot scores도 직접 열거한 15항목의 가용성과 점수만 주석화했으며 생략 슬롯을 불가로 만들지 않았다. 이 목록은 각 회의의 개별 가능 슬롯이지 슬롯 간 선후관계까지 충족하는 완전 후보 목록은 아니다.

메시지 1의 개인 자료 또는 팀 요약 요청은 OR이다. 지원 평면 배열이 이 선택 관계를 표현하지 못하므로 requests/questions를 비우고 request 분류와 전체 발췌로 보존했다. 둘 다 필수라고 강제하지 않았다.

## 오류와 정정의 구분

A의 최초 후보 8/6/10에서 legal은 틀렸다. 24점은 원문 그대로 유지했지만 불가능 후보 점수의 의미가 frozen v3에서 정의되지 않았으므로 오류로 단정하지 않고 의미 보류했다. 선호 원자료의 산술합 25와 발화 24의 불일치는 별도 정보이며 의미 보류 정책을 바꾸는 근거가 아니다.

B는 이 후보의 무효성과 B1 슬롯 8 불가를 정확히 지적했다. 회의별 목록에서 M3 슬롯 8을 7점(실제 5), 슬롯 10을 8점(실제 9)으로 말했고, 실제 유효한 1/6/10을 19점(실제 20)으로 말했다. 세 점수 주장은 확정 오류다. best legal이라는 후보의 최적성 주장 자체는 별도 판정한다. 후보 1/6/10이 최적이라는 사실과 19점이라는 잘못된 숫자를 한 항목으로 합치지 않았다.

A는 1/6/10의 4/7/9, 총 20점을 정확히 정정했지만 M1 슬롯 9가 infeasible이고 원인은 B1 unavailable이라고 잘못 말했다. 이는 meeting_available=0과 reason 두 개의 명시 주장으로 보존했다. 같은 reason의 개인 불가 내용을 다시 fact로 중복 계수하지 않았다. 실제 B1은 슬롯 9에 가용하고 M1도 슬롯 9에 가능하다. 반대로 M1 슬롯 8의 원인도 같은 reason 단위로 처리했다.

M3 슬롯 10의 9점은 회의별 나열과 뒤의 구체적인 재계산에서 각각 발화되어 두 발생을 보존했다. 괄호의 A1=3, A3=2, B2=1, B3=3은 직접 개인 선호 주장 네 개로 기록했고 합 9와 일치한다. 스키마 밖의 별도 팀 전체 기여 합계는 이 회차에 없다.

## 모호·스키마 밖 표현과 제어 행동

high-scoring은 최적성으로 강화하지 않았다. Rechecking/rechecked/misread는 자기 보고여서 실제 내부 사고 과정이 입증됐다고 기록하지 않았다. 확인 요청·미래 제출 약속·조건부 양측 제출 권유는 실제 합의 또는 제출 사실로 바꾸지 않았다. 마지막 Confirmed는 직전 alignment 요청에 대한 명시 수락이므로 accept로 기록했다.

마지막 I submitted 행동 보고는 지원 claim schema 밖이다. 원본 사건상 B는 메시지 4 뒤에 1/6/10을 실제 submit했고, A와 B의 wait 뒤 메시지 5와 6이 전송됐다. 마지막 A submit까지 아래 제어 행동 목록으로 확인할 수 있다. 이 목록은 발화 claim에 덧붙인 것이 아니다.

```json
[
  {
    "event_sequence": 335,
    "actor": "B",
    "action": "send",
    "schedule": []
  },
  {
    "event_sequence": 667,
    "actor": "A",
    "action": "send",
    "schedule": []
  },
  {
    "event_sequence": 883,
    "actor": "B",
    "action": "send",
    "schedule": []
  },
  {
    "event_sequence": 1062,
    "actor": "A",
    "action": "send",
    "schedule": []
  },
  {
    "event_sequence": 1118,
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
    "event_sequence": 1145,
    "actor": "A",
    "action": "wait",
    "schedule": []
  },
  {
    "event_sequence": 1173,
    "actor": "B",
    "action": "wait",
    "schedule": []
  },
  {
    "event_sequence": 1243,
    "actor": "A",
    "action": "send",
    "schedule": []
  },
  {
    "event_sequence": 1302,
    "actor": "B",
    "action": "send",
    "schedule": []
  },
  {
    "event_sequence": 1358,
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

가용 목록 완전성, OR 요청, 상대적 high-scoring, 자기 보고, 확인/미래 행동, 제출 보고 발췌는 총 16개다. 이 수치는 오류 수와 다르다. 후보 무효성 인정인 You’re right를 새 후보의 accept로 만들지 않았고, B의 실제 submit 자체를 전송된 수락 메시지로 세지 않았다.

## 임시 검증

`write_trial_records`를 새 임시 폴더에 실행해 events 해시, 전체 task packet 대응, 원문 evidence와 claim/question schema 및 사후 평가를 확인했다. 검증 임시 사본은 제거했다. 원본 모든 파일 해시는 검증 전후 일치한다. 소스·설정·docs·원본을 바꾸지 않았으며 실제 모델을 호출하지 않았다.

```json
{
  "content_review_status": "complete",
  "task_messages": 6,
  "reviewed_messages": 6,
  "correct_claims": 184,
  "incorrect_claims": 6,
  "undetermined_claims": 1,
  "unjudgeable_expressions": 16,
  "codec_errors": 0,
  "first_proposer": "A",
  "changed_proposal_messages": 1,
  "explicit_revisions": 0,
  "accept_messages": 1,
  "completion": {
    "submitted_agents": [
      "A",
      "B"
    ],
    "both_submitted": true,
    "identical_submissions": true,
    "task_status": "success",
    "error": null
  }
}
```

오류 및 보류 상세:

```json
[
  {
    "message": 2,
    "type": "schedule_valid",
    "value": {
      "schedule": {
        "M1": 8,
        "M2": 6,
        "M3": 10
      },
      "valid": 1
    },
    "correct": false,
    "expected": 0,
    "judgment": "incorrect"
  },
  {
    "message": 2,
    "type": "schedule_score",
    "value": {
      "schedule": {
        "M1": 8,
        "M2": 6,
        "M3": 10
      },
      "score": 24
    },
    "correct": null,
    "expected": null,
    "judgment": "undetermined",
    "candidate_valid": false,
    "arithmetic_sum": 25,
    "arithmetic_matches": false
  },
  {
    "message": 3,
    "type": "meeting_score",
    "value": {
      "meeting": "M3",
      "slot": 8,
      "score": 7
    },
    "correct": false,
    "expected": 5,
    "judgment": "incorrect"
  },
  {
    "message": 3,
    "type": "meeting_score",
    "value": {
      "meeting": "M3",
      "slot": 10,
      "score": 8
    },
    "correct": false,
    "expected": 9,
    "judgment": "incorrect"
  },
  {
    "message": 3,
    "type": "schedule_score",
    "value": {
      "schedule": {
        "M1": 1,
        "M2": 6,
        "M3": 10
      },
      "score": 19
    },
    "correct": false,
    "expected": 20,
    "judgment": "incorrect",
    "candidate_valid": true,
    "arithmetic_sum": 20,
    "arithmetic_matches": false
  },
  {
    "message": 4,
    "type": "meeting_available",
    "value": {
      "meeting": "M1",
      "slot": 9,
      "available": 0
    },
    "correct": false,
    "expected": 1,
    "judgment": "incorrect"
  },
  {
    "message": 4,
    "type": "reason",
    "value": [
      "unavailable",
      "M1",
      "B1",
      9
    ],
    "correct": false,
    "expected": false,
    "judgment": "incorrect"
  }
]
```

초기 후보 사후 검산:

```json
{
  "valid": false,
  "score": null,
  "violations": [
    "Unavailable: B1 at M1"
  ]
}
```

최종 후보 사후 검산:

```json
{
  "valid": true,
  "score": 20,
  "violations": []
}
```

AI 초기 주석이며 독립 재검수 전이다. 실제 메시지 내용과 관찰 가능한 행동을 다루고 Agent의 내적 이해·신뢰·완전 탐색은 판정하지 않는다. 오류 수로 방식별 정확도 순위를 매기지 않는다.
