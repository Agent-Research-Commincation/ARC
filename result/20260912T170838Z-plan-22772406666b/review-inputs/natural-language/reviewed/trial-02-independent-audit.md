# 자연어 2회차 독립 AI 검토

원문을 먼저 직접 읽은 뒤 다른 작성자의 초안과 대조했다. 사람의 독립 검수 완료를 뜻하지 않는다.

- 원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-02`
- 원본 events SHA-256: `c55a93fb769dcae785d7d641e0282ee4652cb661154586a380bb7e65114077fb`
- 초안: `/tmp/arc30-22772406666b/natural-annotations/trial-02.json`
- 초안 SHA-256: `7065fe524054e85b00e08a616bd6e0179e7677fb4d8119a45fab24363d2d567a`
- 검토 완료본: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-02.json`
- 초안 작성자: `Codex /root/stages_5_6; direct source reading of completed natural-language trial-02`
- 독립 검토자: Codex `/root/stages_1_2`

## 결론과 변경 범위

값 전사 오류, 빠진 지원 스키마의 명시 주장, 질문을 확정 주장으로 바꾼 오류, 생략 슬롯에 대한 가용성 추론은 발견하지 못했다. 초안의 메시지·주장·질문·분류를 그대로 유지했다. 검토 완료본에는 reviewer에 독립 AI 검토 정보를 추가했으며 새 메타 claim은 추가하지 않았다. 초안 JSON·초안 메모·원본은 유지했다.

## 원문 대조

1. 메시지 1의 B팀 세 회의 × 12개 슬롯 × 가용성/선호합 72개 주장을 원문 번호·표현에서 별도로 파싱해 초안과 비교했다. 72개 모두 일치했다. available/unavailable이 전 슬롯에 직접 명시돼 있다.
2. 메시지 2의 (1,6,10) 후보 합법성, 총점 20, 괄호 4+7+9를 각각 확인했다. 회의별 4/7/9 연결은 바로 앞의 M1/M2/M3 나열 순서를 따른 명시된 순서 해석이다. 최적성 주장을 추가하지 않은 점을 확인했다.
3. 메시지 3의 “appears legal”은 잠정 표현, “consistent with my B-team summaries”는 한 팀 정보와의 양립 표현이다. 둘을 전체 유효성/점수의 확정 주장으로 바꾸지 않았다. “could you share ... across all slots”는 A팀 세 회의·전 슬롯·두 요약값 72개 질문으로 전개돼 있으며 “whether a higher-scoring legal schedule exists”를 존재 또는 최적성 주장으로 만들지 않았다.
4. 메시지 4의 A팀 자료도 원문 availability/points 12쌍을 슬롯 0–11 순으로 별도 파싱해 72개 주장과 대조했다. 모두 일치했다. “I find no legal schedule scoring above 20”과 바로 이어진 현재 후보 20점을 연결한 최적성 주석은 원문의 정량적 상한 결론을 기록하는 해석으로 유지했다. 이것은 내부 탐색이 완전했음을 확인했다는 메타 주장이 아니다. 이 연결 해석을 독립 검토 메모에 드러내 두었다.
5. 메시지 5의 “optimal from the summaries”는 명시적인 최적성 발화다. 주요 후보 수락과 다른 후보 무효 정정을 분리했다. 팀 불가 근거를 특정 개인의 불가 발화로 분해하지 않았다.

## 불가능 대안과 후속 정정

A의 “M1 at slot 6, M2 at slot 11, M3 at slot 10 also scores 20.”는 **(6,11,10)의 20점 주장**으로 원문 그대로 보존됐다. 그 문장에 없는 legal=1을 추가하지 않았고 현재 제안을 대안으로 교체하라는 지시로 바꾸지 않았다.

B의 “the alternative with M1 at slot 6 is invalid”는 앞서 등장한 유일한 해당 대안을 가리키므로 (6,11,10)의 valid=0으로 별도 기록했다. “the A-team M1 summary says slot 6 is unavailable”도 A팀 M1 슬롯6 가용성0으로 기록했다. B가 A의 점수 설명에 대해 후보의 무효성을 직접 지적한 것이다. B가 20을 23으로 교정했다고 쓰지 않는다.

독립 사후 검산에서 이 후보는 불가능하고 선호 원자료의 단순 합은 23이다. 그러나 고정된 실험 지시에서 불가능 후보의 score 의미가 정의되지 않았으므로 기존 정책에 따라 발화 20의 correct는 null/undetermined이다. 산술 23과 20의 불일치도 따로 남긴다. incorrect_claims=0이 모든 발화가 정확했다는 뜻은 아니다.

## 임시 평가기 검증

현재 `write_trial_records`를 `/tmp`의 임시 폴더로 실행해 annotation 스키마, events 해시, 발췌, 질문·claim 타입 및 사후 평가를 확인했다. 임시 산출물은 종료 후 제거했다.

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
  "first_proposer": "A",
  "changed_proposal_messages": 0,
  "explicit_revisions": 0
}
```

판정 보류 1건의 상세:

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

현재 제안(1,6,10)은 유효한 최적20점이다. 원본·초안·초안 메모의 해시는 검토 전후 모두 일치했다. 초안 유지 외 실험 소스·설정·docs·원본 수정이나 추가 모델 호출은 없었다.

## 해석 한계

- 메시지2의 동의 요청과 메시지3의 잠정성/팀 정보 양립성은 현재 스키마 밖 발췌 3개로 남아 있다. 이는 내용 오류 3건이 아니다.
- 메시지4의 “I find no ... above20”를 현재 후보 최적성에 연결하는 해석과 메시지2의 괄호 순서 해석은 원문 문맥에 기반하지만 사람 검수자가 재확인할 수 있게 명시했다.
- 이 작업은 별도 AI 검토이며 사람의 독립 검수나 실험 Agent의 숨은 추론 검증이 아니다.
