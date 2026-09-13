# trial-06 독립 AI 원문 검수

검수자는 Codex /root/stages_5_6이며 초안 작성자 /root/stages_1_2와 별도로 전달 원문 4개를 직접 읽었다. 사람 검수로 표시하지 않는다. 원본 `/Users/hyohyeon/Desktop/agent-research-commincation/.worktree/20260912T170838Z-plan-22772406666b/stage-1/results/experiment/20260912T170838Z-stage1-b960a45a627b/trial-06`의 events SHA-256은 `addbc0dfa891e770c6a9b362dba569ffd268991b4b3d676d0afa5511838d0c82`이다.

## 최종 판정

초안의 의미 필드 변경은 없다. 양팀 요약 144개를 실제 발화의 숫자·available/unavailable에서 독립 파싱해 전 항목을 초안과 대조했다. 0–11 슬롯 모두 명시된 표이므로 누락을 불가로 보충한 항목은 없다. 정답 값으로 발화값을 수정하지 않았다. 메타데이터의 독립 검수자와 해석 메모만 보완했다.

임시 사본 검증은 complete, 4/4 메시지, 맞는 주장 148개, 틀린 주장 1개, 의미 규약 보류 0개, 스키마 밖 표현 7개, 코덱 오류 0개다. 개인별 원자료 주장을 만들지 않았다. 원본·초안·코어 파일 해시가 검수 전후 동일하다.

## 메시지별 대조

| 메시지 | 판정 범위 | 독립 검수 결과 |
|---|---|---|
| 1, B → A | B팀 요약 72개 | M3 슬롯 9 가용성만 원자료와 불일치. 발화값 1을 그대로 유지 |
| 2, A → B | 후보 1,6,10과 distinct·precedence·20점 | 명시된 3개 주장은 정확. 시간 라벨 3개는 별도 검산; 동의 요청을 수락으로 세지 않음 |
| 3, B → A | B팀 전체 기여 10, A팀 요약 요청 | 전체 기여는 지원 claim으로 바꾸지 않음. 문맥상 3회의×12슬롯×2관계인 요청 72항목으로 전개; 실제 문장 72개라는 의미가 아님 |
| 4, A → B | A팀 요약 72개, 총점20, maximum-scoring | 74개 지원 주장은 정확. 팀 전체 기여 A10/B10과 동의 요청은 별도 발췌 보존 |

## B M3 슬롯 9 오기와 영향

정확한 발췌는 메시지 1의 `For B attendees of M3, they are:`로 시작하는 문장 속 `slot 9 available, 2`다. B2는 슬롯 9 불가, B3는 가능하므로 B팀 전체 가용성은 0이다. 선호 합 2는 정확하다. 그러므로 하나의 잘못된 available 주장으로 세며 preference까지 오류로 늘리지 않는다.

독립 전수 계산의 가능한 일정 수는 54개에서 67개로 바뀐다. 이 값만 1이라고 가정하면 슬롯 9의 M3를 포함하는 일정 13개가 추가되고 제거는 0개다. 기존 공통 일정의 선호 합은 변하지 않는다. 평가기의 `schedule_scores_changed=true`는 가능한 일정→점수 사전의 항목 추가를 포함한다. 최적 점수 20와 최적 일정 집합, B가 제출한 1,6,10의 유효성·점수는 변하지 않는다. 이 반사실 계산은 Agent가 실제 그 값을 믿었거나 실패 원인이 이 오기였다는 판정이 아니다. 세부 추가 일정은 동반 검산 JSON에 보존한다.

## 지원 스키마 밖 표현의 검산

메시지 3: `I calculate the B-side preference contribution for your schedule as 10.`

메시지 4: `The proposed schedule gives A-side 10 and B-side 10`

`your schedule`/`The proposed schedule`은 대안이 없는 직전 후보 M1=1, M2=6, M3=10을 가리킨다. 전체 일정 기여는 A=2+3+5=10, B=2+4+4=10으로 모두 맞다. 이 회의별 세부 합은 사후 검산이며 새로 발화된 주장으로 넣지 않았다. 전체 팀 기여는 한 회의의 team summary도 두 팀 총점 schedule_score도 아니므로 별도 항목으로만 남겼다.

메시지 2의 `M1 at slot 1 (D1 10:00)`, `M2 at slot 6 (D2 09:00)`, `M3 at slot 10 (D2 14:00)`는 공개 슬롯 표와 모두 일치한다. 시간 라벨 claim 타입이 없어 unjudgeable에 남지만 참·거짓을 판단할 수 없는 자연어라는 뜻은 아니다. 동의 요청 `Please confirm this exact schedule.` 및 `please confirm if you agree.`도 지원 질문 타입이 없어 보존했다. 총 7개 발췌는 거짓 주장 7개가 아니다.

## recommended maximum-scoring 해석

원문은 `It remains my recommended maximum-scoring schedule;`다. `maximum-scoring`가 선택된 후보를 직접 수식하고 제한된 탐색 범위나 조건이 붙지 않았으므로 최대 점수 후보라는 명시적 평가를 schedule_optimal=1로 유지한다. 단순한 추천 또는 높은 점수라는 표현으로 읽은 것은 아니다. 다만 이 해석은 내부 전수 탐색을 실제 수행했다는 확인이나 상대의 수락을 뜻하지 않는다. 바로 앞 후보의 총점20과 독립 계산의 최적값20이 일치한다. `remains`는 동일 후보 재추천이므로 후보 변경이나 명시적 revise로 세지 않는다.

## 4개 전달 메시지와 3개 제어 행동의 구분

실제 전달 task packet은 4개다. 이후 원본 행동은 B submit(이벤트972) → A wait(1001) → B stop(1037)이다. 적용 기록은 각각973,1003,1038이다. B만 1,6,10을 제출했고 A는 제출하지 않았다. 명시적 수락 task 메시지는 0개다.

B stop payload `Submitted the agreed maximum-scoring schedule.`는 상대에게 전송된 task packet이 아니므로 주석 entry를 추가하거나 accept/optimal 주장을 더 세지 않았다. 이 제어 발화의 `agreed`만으로 실제 상호 동의가 확인됐다고 서술하지 않는다. B 제출 자체와 제출 후보의 최적성은 사후에 확인되지만 두 Agent의 제출 조건을 만족하지 못했다. 원본은 status=stopped, operational_status=normal, success=false, evaluation=null이고 그대로 유지했다. 기술적 인프라 실패나 점수20 성공 회차로 바꾸지 않는다.

## 재현·보존

검수본: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-06.json`

검산: `/tmp/arc30-22772406666b/natural-annotations/reviewed/trial-06-independent-validation.json`

검증은 tmp 사본을 입력으로 기존 write_trial_records에 manual_input을 주어 수행했다. 임시 검증 폴더는 제거했다. 원본·코어·설정·docs를 수정하거나 실제 모델을 추가 호출하지 않았다. AI가 해석한 대명사 후보 연결, 요약 요청 범위와 maximum-scoring 해석은 위에 공개했으며, Agent의 내부 탐색 완전성과 의도는 검수 범위 밖이다.
