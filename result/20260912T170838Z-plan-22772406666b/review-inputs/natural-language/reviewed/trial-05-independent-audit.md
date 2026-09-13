# 자연어 5회차 독립 AI 검토

원문 task 메시지4개를 먼저 직접 읽고 초기 작성자 `/root/stages_5_6`의 초안과 대조했다. 이는 AI 검토이며 사람의 독립 검수나 숨은 추론 검증이 아니다.

- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-05`
- events SHA-256: `9e9737f3fe706586e73688ebb4a65baed561605808a689d1268b1fc74629c3da`
- 초기 초안: `/tmp/arc30-22772406666b/natural-annotations/trial-05.json`
- 초기 초안 SHA-256: `1f7b40dde3c96ef8b127f76ab3ed84a4c813d9362b2fa24f688532b6d11e7739`
- 검토 완료본: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-05.json`
- 세부 검산: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-05-independent-validation.json`

## 결론 및 수정 사항

초안에서 값 전사·발췌 근거 오류, 지원 스키마의 명시 주장 누락, 계획/질문을 확정 주장으로 바꾼 과해석, 생략 슬롯의 불가 추론을 발견하지 못했다. 초안 entries는 그대로 유지했다. reviewer에 독립 AI 검토 정보를 추가했으며 새 claim은 추가하지 않았다. 전체 주장수157개, 메시지별72/72/11/2개다.

## 전수 대조

1. A팀 요약72개를 원문에서 직접 파싱해 대조했다. 모두 초안과 일치한다. 특히 A의 “2 available, 3”을 M1 슬롯2 가용성1·선호3으로 전사한 것이 맞다. 실제 문제에서 가용성은0이지만 발화값1을 그대로 남겨야 하므로 수정하지 않았다. B팀 세 회의·슬롯0–11의 가용성과 선호를 명시적으로 요청해72개 질문으로 연결한 것도 맞다.
2. B팀72개 요약 역시 원문 파싱과 일치한다. “I will now compare ... identify the best legal schedule”는 향후 행동 계획이므로 어떤 후보의 최적성·유효성 단정으로 코딩하지 않은 것이 맞다.
3. A의 “The best legal schedule from these summaries is ...”는 완전한 후보(1,6,10)를 명시적으로 best/legal이라 평가하므로 유효성과 최적성 claim이 근거를 가진다. from these summaries 범위를 보존했다. 가용성3개, distinct와precedence, 4+7+9=20도 명시됐다. 4/7/9의 회의 연결은 바로 앞 M1/M2/M3 순서에 따른 문맥 해석이며 정답으로 채운 숫자가 아니다.
4. B의 Confirmed는 명시적 수락이다. legal과총점20은 직접 말했지만 optimal을 재단정하지 않아 B의 별도 최적성 claim은 만들지 않았다. I will submit은 미래 의사이며 메시지 시점의 제출 완료로 바꾸지 않았다.

## 오류와 후보 품질의 구분

오류1건은 A팀 M1 슬롯2의 가용성1 주장이다. 실제값0과 다르다. 개인별 가용성 주장으로 분해하거나 원문1을 정답0으로 대체하지 않았다.

A가 말한 “from these summaries” 범위도 별도로 검산했다. 전체144개 요약 중 이 가용성 하나만 실제 입력과 달라 해당 주장만 대입하는 반사실 검산을 했다. 유효 일정 집합은 달라지지만 최고20점과 최적 일정은 그대로고 제출한(1,6,10)의 점수도20이다. 따라서 내용 오류 존재와 최종 후보의 최적성은 함께 성립한다. Agent가 잘못된 주장을 실제로 믿었다거나 독립 검증했다는 결론은 내리지 않는다.

```json
{
  "spoken_summary_items_compared": 144,
  "original_schedule": {
    "valid": true,
    "score": 20,
    "violations": []
  },
  "original_best": 20,
  "counterfactual_best": 20,
  "counterfactual_selected_score": 20,
  "original_feasible_count": 54,
  "counterfactual_feasible_count": 69,
  "optimal_schedules_unchanged": true,
  "annotation_entries_unchanged": true,
  "source_draft_hashes_unchanged": true
}
```

## 임시 평가기 검증

`write_trial_records`를 `/tmp`의 임시 폴더에 실행해 annotation 양식·events 해시·근거 발췌·claim/question 타입 및 결과를 확인했다. 검증 임시 산출물은 제거했다.

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
  "first_proposer": "A",
  "changed_proposal_messages": 0,
  "explicit_revisions": 0,
  "accept_messages": 1
}
```

세부 오류와 반사실 영향은 별도 validation JSON에 남겼다. 원본·초안·초안 메모의 해시는 검토 전후 일치한다. 실제 모델 호출 또는 실험 소스/설정/docs/원본 변경은 없다.

## 지원 스키마 밖 표현과 한계

향후 탐색 계획, 동의/공동 제출 요청, 미래 제출 약속의3개 발췌는 스키마 밖 표현이며 내용 오류3건이 아니다. 숫자 없는 계획을 best-score claim으로 강화하지 않았고 독립 검토에서 추가할 지원 스키마 밖 계산 주장도 발견하지 못했다. from these summaries 최적성 범위와 4+7+9 순서 해석은 위에 드러냈으며 사람 표본검수에서 재확인할 수 있다.
