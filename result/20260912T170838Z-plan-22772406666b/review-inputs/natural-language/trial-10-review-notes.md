# 자연어 10회차 전체 task 메시지 AI 초기 주석

- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-10`
- events SHA-256: `c1a3037125595193e46443814f53b9b8048ab86ae9cfc0f7da5ffcc4df867793`
- 주석: `/tmp/arc30-22772406666b/natural-annotations/trial-10.json`
- 검수 유형: AI 초기 주석이며 별도 독립 검토는 후속 작업이다.
- 범위: 실제 전달 task 메시지 2개 전체. 제어응답과 로그 중복을 별도 발화로 세지 않았다.

## 직접 전개한 주장

| 메시지 | 발신 | 내용 | 주장 수 |
|---|---|---|---:|
| 1 | B | 세 회의·슬롯0–11 가용성/선호합 | 72 |
| 2 | A | 같은 범위 팀 요약72개, 후보 유효성, 선후관계 충족 | 74 |

전체146개 주장이다. 각 메시지는 모든 슬롯의 가용성과 선호합을 직접 나열했다. 원문 배열만 파싱했으며 정답 데이터로 발화값을 대체하거나 생략 슬롯을 불가로 채우지 않았다. 팀별 선호합을 개인 원자료나 다른 회의별 계산 주장으로 분해하지 않았다.

메시지1의 “corresponding team summaries”는 방금 보낸 세 회의·슬롯0–11의 가용성과 선호합에 대응하는 A팀 요약을 요청한 것으로 읽어72개 질문으로 연결했다. 이 범위 해석은 notes에 공개했다. “so we can select a legal high-scoring schedule”는 향후 협업 목표여서 현재 후보의 유효성이나 최적성 claim으로 만들지 않았다.

메시지2는 “I propose M1 at slot 1, M2 at slot 6, and M3 at slot 10; this is legal with M1 before M3.”라고 직접 말했다. 완전한 후보1/6/10과 legal·선후관계 충족을 기록했다. **총점20이나 best/optimal은 말하지 않았다.** 사후 평가에서 최적20점이라는 이유로 이런 주장을 추가하지 않았다. 별도로 말하지 않은 distinct 또는 각 회의의 가용성 주장도 legal에서 재분해하지 않았다.

## 스키마 밖 표현과 결과의 경계

지원되는 명시 주장 밖에 별도 수치 계산 주장은 없다. 법적 고득점 일정 선택이라는 목표 문장은 계획으로 설명했고, 불명확한 현재 상태 주장으로 세지 않았다. 따라서 unjudgeable 발췌는0개다. 이0은 모든 가능한 Agent 내부 상태를 측정했다는 뜻이 아니다.

원문 이후 B와A가 각각 같은 후보를 제출했다. 이것은 실제 제출의 증거이며 채널에 없는 accept 메시지를 만들어 넣는 근거가 아니다.

```json
[
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

후보의 아래 사후 평가는 검산 메모에만 둔다. 주석의 schedule_score 또는 schedule_optimal로 넣지 않았다. 불가능 후보의 점수 발화가 없어 invalid-score 보류 정책을 적용할 대상이 없다.

```json
{
  "valid": true,
  "score": 20,
  "violations": []
}
```

## 임시 검증

`write_trial_records`를 임시 폴더에 실행하여 events 해시, 전체 메시지 근거, claim/question 양식과 사후 평가를 확인했다. 임시 산출물은 제거했고 원본 파일 해시는 검증 전후 일치했다. 실제 모델 호출과 실험 소스·설정·docs·원본 변경은 없었다.

```json
{
  "content_review_status": "complete",
  "task_messages": 2,
  "reviewed_messages": 2,
  "correct_claims": 146,
  "incorrect_claims": 0,
  "undetermined_claims": 0,
  "unjudgeable_expressions": 0,
  "codec_errors": 0,
  "first_proposer": "A",
  "changed_proposal_messages": 0,
  "explicit_revisions": 0,
  "accept_messages": 0,
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

지원 주장146개는 모두 정확했다. 실험 Agent의 내부 검증이나 완전 탐색 여부를 판단하지 않았고, 독립 검토 전의 AI 초기 주석임을 유지한다.
