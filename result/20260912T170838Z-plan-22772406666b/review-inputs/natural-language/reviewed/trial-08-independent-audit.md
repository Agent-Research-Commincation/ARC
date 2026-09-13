# trial-08 독립 AI 전수 검수

검수자: Codex /root/stages_5_6. /root/stages_1_2 초안을 실제 전달 task 원문 2개 전체와 독립적으로 대조했다. AI 검수이며 사람 검수로 표시하지 않는다.

원본: `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-08`

이벤트 SHA-256: `36de7bebfa8508931ce776683c7a228df6d9b9bd67dad9913fdc4c0cc1588e54`

## 결론과 변경 범위

초안의 의미 판정은 유지했다. 리뷰어 메타데이터와 해석 메모만 보완했다. 메시지 1의 B팀 요약 72개, 메시지 2의 A팀 요약 72개 및 일정 평가 3개를 원문에서 대조했다. 임시 사본 검증은 2/2 메시지 complete, 맞는 주장147개, 오류0개, 의미 규약 보류0개, 스키마 밖 표현1개, 코덱 오류0개다.

## 증거와 누락 검수

양쪽 원문은 `slots 0 through 11` 범위를 명시하고 세 회의의 availability와 preference 배열을 각각 12개씩 직접 열거한다. 원문 배열을 독립 파싱한 144개 값은 초안과 전부 일치했다. 누락 슬롯을 불가로 채우거나 팀 요약을 개인별 사실로 분해하지 않았다. 사후 입력 대조에서도 전 값이 맞았다. 문장과 각 claim의 exact evidence가 실제 해당 packet의 receiver_text에 존재함을 확인했다.

B의 요청은 `Please share the corresponding A-attendee team summaries for all three meetings and all slots.`이다. `corresponding`은 직전의 availability/preference 두 관계를, `all three meetings and all slots`는 전체 범위를 직접 가리키므로 A팀 질문 72항목으로 전개한 근거가 충분하다. 이 숫자는 질문 문장 수가 아니다. 개인별 원자료 요청·메시지 ID 재검토 요청은 없으므로 requests/references를 빈 목록으로 유지했다.

## top-scoring과 후보 평가

정확한 원문은 `I calculate a top-scoring legal schedule as M1 slot 1, M2 slot 6, M3 slot 10, with total score 20.`이다. 여기서 명시된 후보에 대한 legal, 최고 점수, 총점20을 각각 schedule_valid=1, schedule_optimal=1, schedule_score=20으로 유지했다.

`top-scoring`은 최고 점수라는 최상급 수식이며, 이번 문장에는 비교 대상을 일부 후보로 제한하거나 특정 조건만의 최대라고 정하는 표현이 없다. 부정관사 `a`는 유일한 최적 후보라는 주장까지 하지 않는다는 뜻으로 읽었다. 단순 높은 점수 후보라는 의미로 축소하지 않았다. 반대로 `I calculate`만으로 전수검색을 완료했다거나 실제 내부 계산 절차를 검증했다는 주장도 만들지 않았다. 이 의미 해석은 공개하고, 내부 추론 완전성은 판정 범위에서 제외한다.

원문에는 선택 후보 외 대안 일정이나 별도 회의 점수가 없다. 따라서 사후 계산으로 알게 된 회의별4+7+9를 새로운 meeting_score 발화로 추가하지 않았다. 유효성에 포함되는 개별 hard constraint도 별도 직접 주장으로 늘리지 않았다.

## 스키마 밖 요청과 과해석 방지

`Please confirm or share any better candidate.`를 request 종류와 exact unjudgeable 발췌로 유지했다. 현재 typed questions는 동의 또는 새 후보 제안 요청을 직접 표현하지 못한다. 이 문장이 더 좋은 후보가 존재한다는 주장, 상대의 수락, 또는 특정 후보 점수 확인 질문이라고 추가 해석하지 않았다. 반론을 구하는 요청은 앞 문장의 top-scoring 평가를 취소하지 않는다. 스키마 밖 표현1개는 오류1개가 아니다.

## 독립 사후 검산과 종료

검수용 코드가 원자료의 참석자 가용성·겹침·선후관계를 직접 적용해 12^3 배치를 전수 확인했다. 가능한 일정은 54개, 최적값은 20이고, 원문 후보 M1=1/M2=6/M3=10은 유효한 20점이다. 세 회의의 사후 점수는 {'M1': 4, 'M2': 7, 'M3': 9}이며 검산 기록에만 남겼다. 지원되지 않는 후보 점수의 의미 보류 정책이 필요한 불가능 후보 발화는 없었다.

실제 task packet은 2개이고 뒤의 B submit(이벤트680), A submit(735)은 제어행동이다. 이를 추가 전달 메시지나 자연어 accept로 세지 않았다. 두 Agent가 같은 후보를 제출해 원본 status=success, operational_status=normal, evaluation valid=true/score20이며, 명시적 accept 메시지는 0개다.

## 검증과 보존

검수본: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-08.json`

독립 검산·해시·검증 결과: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-08-independent-validation.json`

원본을 tmp 사본으로 복사한 뒤 기존 write_trial_records에 검수본을 전달해 검증했다. 임시 검증 폴더는 제거했고 원본·초안·코어 해시는 전후 일치한다. 실행 소스·설정·docs·실험 원본 수정이나 실제 모델 호출은 없었다. 해석은 2개 전달 메시지에 한정하며 다른 회차 발화로 채우지 않았다.
