# 2~6단계 trial-06~08 추가 과정 감사

현재 계획 `20260912T170838Z-plan-22772406666b`의 완료된 15회만 검토했다. 앞선 회차·자연어 회차·이후 회차는 이 집계에 포함하지 않는다. 15회 모두 두 Agent가 유효한 같은 일정을 제출했다. 그중 14회는 20점이며, 3단계 trial-07은 19점으로 최적점수보다 1점 낮다.

[관찰표](/tmp/arc30-22772406666b/structured-audit-06-08/observation-table.md), [제어 요청 전체 순서](/tmp/arc30-22772406666b/structured-audit-06-08/control-timeline.md), [거절과 후속 응답](/tmp/arc30-22772406666b/structured-audit-06-08/rejection-followups.json), [선별 원문](/tmp/arc30-22772406666b/structured-audit-06-08/selected-source-evidence.md), [검산 기록](/tmp/arc30-22772406666b/structured-audit-06-08/verification.json), [읽은 범위](/tmp/arc30-22772406666b/structured-audit-06-08/source-reading-log.json)를 함께 보존한다.

## 방법과 읽은 범위

검토자는 AI `/root/stages_3_4`다. 같은 worktree 평가 코드의 `write_trial_records`를 실행 원본과 다른 tmp 출력 폴더에 사용했다. 평가 정책은 `observation-review-v3.1`이다. 2~6단계 실행 소스의 파일별 해시는 모두 같고, 검토 전후에도 원본 회차 파일과 실행 소스 해시가 유지되었다. 실제 모델 추가 호출·실험 개입·코드/설정/docs 수정은 없다.

46개 task 메시지 전체를 자동으로 정규화하고, 명시 주장의 값 및 코덱 복원을 대조했다. 96개 제어 응답의 action·phase·실행기 적용/거절·전달 패킷을 모두 자동 연결하고 그 순서를 읽었다. 적용된 submit/revise로 제출 상태를 복원하여 15개 최종 result의 제출 상태와 대조했다. **이는 자동 전수 대조와 선별 원문 검토이며, 메시지 원문 전체의 수동 전수 검수가 아니다.** 원문을 읽은 정확한 범위는 다음과 같다.

| 단계/회차 | 송신 원문 전체를 직접 읽은 task 메시지 |
|---|---|
| 2/06 | m2, m3, m4 |
| 3/07 | m1, m2 |
| 3/08 | m2, m3 |
| 4/06 | m2~m6 |
| 4/07 | m1, m3, m5 |
| 5/06 | m1, m2 |
| 5/07 | m2 |
| 6/06 | m3, m4, m5 |
| 6/08 | m5, m6; m4는 처음 240문자만 발췌 대조 |

전체 송신 원문을 읽은 메시지는 23개다. m번호는 `experiment/packet.params.sequence`이고 request 번호는 실행기 응답 요청 번호다. 거절이 있으면 둘은 다르다. 6단계의 m번호에는 사전 합의 패킷도 포함된다.

5/07 request-3~6과 6/06 request-7~10의 제어 응답·입력을 전체로 읽었다. 6/06 request-1~3, 6/08 request-1~5의 사전 합의 제어 응답과 최종 사전을 읽었다. 거절 10건은 모두 오류 필드와 후속 실제 동작을 대조했다. 거절 원문 전체를 읽은 것은 5/06 request-1, 6/06 request-1, 6/08 request-1·3의 4건이다. 나머지 거절 task payload는 처음/끝 250문자와 메시지 종류 선언 등 오류 관련 발췌를 읽었다. 원문 전체를 증거 파일에 보존한 것과 검토자가 전체를 읽은 것은 구분한다.

독립적인 표준 라이브러리 검산으로 완전한 배치를 담은 메시지 21건과 최종 제출 15건의 가용성·겹침·선행 조건·점수를 재계산했다. 모두 평가기와 일치했다. 가능한 1728개 배치 중 유효한 54개가 있으며 유일한 최적 배치는 (M1,M2,M3)=(1,6,10), 20점이었다. 오류 요약 11건의 기대값도 원자료 참석자를 기준으로 별도 계산했다.

## 확정 오류와 보류

46개 task 메시지에서 맞음 2167건, 틀림 11건, 의미 보류 1건, 코덱 오류 0건이다. 틀린 11건은 모두 **3단계 trial-07, m2 B의 M1 팀 요약**에 있다. B의 M1 참석자는 B1 한 명이므로 가용성과 선호는 B1의 해당 슬롯 값과 같아야 한다.

| 정확한 송신 원문 | 원자료 기대값 |
|---|---:|
| `teamavailable(B,M1,1,0).` | 1 |
| `teamavailable(B,M1,9,0).` | 1 |
| `teampreference(B,M1,0,4).` | 2 |
| `teampreference(B,M1,1,3).` | 2 |
| `teampreference(B,M1,3,2).` | 1 |
| `teampreference(B,M1,5,4).` | 2 |
| `teampreference(B,M1,6,4).` | 2 |
| `teampreference(B,M1,7,3).` | 1 |
| `teampreference(B,M1,9,2).` | 0 |
| `teampreference(B,M1,10,4).` | 3 |
| `teampreference(B,M1,11,4).` | 3 |

B가 같은 m2에서 보낸 M1 요약 24항목은 같은 메시지의 M2 요약 24항목과 값이 모두 같다. 이 비교는 원문과 자동 키 대조에서 확인했다. M2 팀 참석자는 B1·B2이므로 M1과 M2의 의미는 다르다. 이는 **M1 필드에 M2 요약과 동일한 값 묶음이 들어간 관찰**이지, 내부에서 복사·붙여넣기를 했다는 추론은 아니다. 11건을 11개의 독립적인 실패 사건으로 일반화하지 않는다.

첫 전체 후보는 같은 m2의 (7,6,10)이다. 이후 A request-3, B request-4가 그 배치를 submit했으며 추가 peer 메시지·질문·명시 교정·revise는 없다. 따라서 11건의 후속 명시 교정은 **없음**이고, 최종 일정은 유효하지만 19점이다. 후보를 제안했다는 사실에 “최적이다”라는 주장을 추가하지 않았으므로 별도의 거짓 최적성 주장으로 세지 않는다.

평가기의 단일 주장 반사실 검사에서 `teamavailable(B,M1,1,0)` 하나만 대입하면 실제 최적 후보가 배제되고 최적점수가 20→19로 바뀐다. `teampreference(B,M1,7,3)` 하나만 대입하면 제출 배치의 계산 점수가 19→21로 바뀐다. 각각 다른 값은 원자료 그대로 둔 조건이다. 이는 영향 가능성의 근거이며, 이 오류가 실제 Agent의 내부 선택이나 최종 19점을 유발했다는 인과 증명은 아니다. 11개를 함께 대입한 효과로 잘못 읽어서는 안 된다.

보류 1건은 **2단계 trial-06 m3 B의 `["score",5,6,10,23]`**이다. (5,6,10)은 A2가 M1 슬롯 5에 불가하여 실행할 수 없다. 원시 선호 합계는 23으로 송신값과 같지만, 불가능한 후보의 score 의미가 고정 프롬프트에서 미정이므로 현재 지표 기준에 따라 정오를 보류했다. 같은 메시지의 `["valid",5,6,10,0]`은 정확하다. 이 보류를 맞는 점수나 틀린 점수로 임의 전환하지 않는다.

## send·submit·wait·stop·revise

15회 전체에서 task에 적용된 동작은 send 45회, submit 30회, wait 3회, revise 1회다. **stop 시도와 적용은 모두 0회**다. 거절된 submit·wait·stop·revise도 없다. 모든 회차가 양쪽 제출로 끝났으므로 이 범위에서는 양쪽 제출 전에 stop하여 종료된 사례가 발견되지 않았다. 자연어 trial-06의 원문이나 결과는 이번 검토에 포함하지 않았으며 방식 간 인과 비교를 하지 않는다.

### 5단계 trial-07: 한쪽만 제출된 상태에서 두 번 wait

| 요청 | 관찰된 동작 | 실행기 제출 상태 |
|---|---|---|
| request-2 B | m2로 (1,6,10) 제안과 B 요약 전송 | 없음 |
| request-3 A | (1,6,10) submit | A만 제출 |
| request-4 B | `{"action":"wait","payload":"","schedule":[],"language":[]}` | A만 제출 유지 |
| request-5 A | 같은 wait 동작 | A만 제출 유지 |
| request-6 B | (1,6,10) submit | 양쪽 일치, 성공 |

B request-4와 request-6 입력에는 자신의 제출 hash가 `none`이라고 표시된다. A request-5 입력에는 이미 기록된 자신의 hash가 있다. 상대의 제출은 peer 메시지로 전달되지 않는다. 두 wait 사이에는 추가 peer 메시지가 없고, B는 다음 기회에 제출했다. 대기가 관찰되었지만 실패나 규칙 위반으로 자동 채점하지 않는다. 무엇을 기다렸는지에 대한 설명은 응답에 없으므로 이유를 추측하지 않는다.

### 6단계 trial-06: submit 후 별도 send로 수락 표시

| 요청 | 관찰된 동작 | 실행기 제출 상태 |
|---|---|---|
| request-6 A | m4로 (1,6,10) 제안과 A 요약 | 없음 |
| request-7 B | (1,6,10) submit | B만 제출 |
| request-8 A | wait | B만 제출 유지 |
| request-9 B | m5 `accept(). valid(1,6,10,1). score(1,6,10,20).`를 send | 기존 B 제출 유지 |
| request-10 A | (1,6,10) submit | 양쪽 일치, 성공 |

request-9의 send는 이미 기록된 B 제출을 취소하지 않았다. request-10의 A 입력에서 m5가 실제 peer 메시지로 전달된 것을 확인했다. 이 순서는 submit과 상대에게 보이는 수락 메시지가 서로 다른 행위임을 보여 준다. A가 수락 메시지 때문에 제출했다고 인과를 확정하거나, B의 제출을 A가 이미 알고 있었다고 쓰지는 않는다.

### 2단계 trial-06: 제안 변경과 revise가 다른 요청에서 일어남

A m2/request-2는 (5,6,10)을 제안하고 valid/score를 질문한다. 동시에 보낸 자기 팀 요약에는 A·M1·슬롯 5의 available=0이 명시되어 있다. B m3/request-3은 **send**로 그 후보의 valid=0과 대안 (1,6,10)의 valid=1·20점을 전달한다. A m4/request-4는 **revise** 동작의 payload에 `kind:"accept"`와 대안 배치를 넣는다. 적용 revision은 1이지만 `cleared_agents=[]`이므로 기존 제출 취소는 없다. 이후 두 Agent가 새 revision에서 제출한다.

여기서 제안 배치 변경은 B m3에, 명시 revise는 A m4에 발생했다. 두 지표가 각각 1이어도 같은 사건이라는 뜻이 아니다. 첫 불가능한 후보는 유효한 20점 일정으로 교정되었고 그대로 제출되지 않았다.

### 4단계 trial-06: 합의 전 후보 변경과 reject·accept

B m3은 최적 (1,6,10)을 제안한다. A m4는 **send**로 (8,6,10)을 제안한다. B m5는 `kind:"reject"`에 `["unavailable","M1","B1",8]` 사유와 정확한 B 요약 두 항목, `references:[1,3]`을 넣는다. A m6은 `kind:"accept"`로 (1,6,10)에 돌아온 뒤 양쪽이 제출한다. B1의 슬롯 8 불가 사유는 원자료와 같다.

이 회차는 적용 revise가 0이고 제안 변경은 1이다. 원래 배치로 돌아온 m6은 accept이므로 propose끼리 비교하는 변경 수에는 추가되지 않는다. 앞선 m3은 아직 상호 합의나 제출이 없는 제안이었고 m4 이전에 accept·submit이 없었다. 고정 지침은 합의하거나 제출한 제안의 변경에 revise를 요구하므로, 단순히 배치가 바뀌었는데 revise가 없다는 이유로 이 사례를 제어 규칙 위반으로 단정하지 않는다.

## 거절 원인과 이후 실제 행동

거절 10건은 task 메시지 7건, 사전 합의 3건이다. 거절에는 전달 패킷이 없고 사후 명시 주장 검산에도 포함하지 않는다. 실제 요청·응답 기록에는 남는다. 다음 표는 기록된 오류 문자열과 이후 적용된 행동을 구분한다.

| 사례 | 기록된 거절 | 원문 발췌 및 이후 실제 행동 |
|---|---|---|
| 3/08 A request-2 | `Only one message kind` | `propose().`와 `inform().`가 함께 있음. request-3은 inform과 요약만 m2로 전달. 상대 B가 request-4/m3으로 제안 |
| 4/07 A request-1 | `Duplicate JSON key: summaries` | 요약 목록 뒤에 다시 `"summaries":[]`이 있음. request-2/m1은 요약 없이 B1·B2·B3 요청만 전달. 이후 A m3에서 후보 관련 개인 사실 10개, B m4의 요청 뒤 A m5에서 전체 팀 요약 72개 전송 |
| 5/06 B request-1 | `Unknown instruction or arity` | 처음 `KIND inform` 뒤 본문에 `KIND request`가 다시 있음. 파서에서 중간 KIND는 허용하지 않음. request-2/m1은 첫 KIND request 하나로 요약과 질문을 전달 |
| 6/06 B request-1, setup | `Symbols must contain 1-8 ASCII letters` | `teamavail`은 9자. request-2가 `teamavl`로 수정하여 사전 제안 전달, request-3에서 상대가 accept_language 적용 |
| 6/06 B request-4 | `Message kind is required` | 종류 선언 없이 요약·질문을 작성. request-5/m3은 `inform().`을 포함하여 전달 |
| 6/08 B request-1, setup | `Symbols must contain 1-8 ASCII letters` | `teamavail`(9자), `asksummary`(10자)를 포함. request-2는 `teamavl`, `asksum`으로 사전 제안 전달 |
| 6/08 A request-3, setup | `Only define_language can contain a dictionary` | accept_language에 사전 배열을 넣음. request-4에서는 같은 사전 배열에 action을 define_language로 바꾸어 재제안. B request-5가 빈 사전 배열의 accept_language로 수락 |
| 6/08 B request-6 | `Unknown predicate or invalid syntax: teavl(B,M1,0,1).` | 최종 사전의 가용성 기호는 `teamavl`. request-7/m4의 가용성 발췌는 `teamavl`로 수정되어 전달 |
| 6/08 A request-8 | `Unknown predicate or invalid syntax: teavl(A,M1,0,0).` | 가용성 기호가 사전과 다름. 다음 request-9는 그 기호를 바꿨지만 다시 거절됨 |
| 6/08 A request-9 | `Only one message kind` | inform과 propose가 함께 있음. request-10/m5는 inform과 A 요약만 전달, B request-11/m6이 제안 |

6/08 request-8에는 잘못된 기호와 두 종류 선언이 함께 있지만, 실제 해당 응답에 기록된 오류는 기호 오류 하나다. 다음 request-9에 별도 거절된 두 종류 오류를 구분해야 하며, 하나의 거절 응답을 여러 거절 사건으로 늘리지 않는다. 사전 재제안이 실제 적용되어 6/08의 setup 패킷은 3개다. 모든 6단계 회차의 setup을 기계적으로 2개라고 가정하면 안 된다.

5/06 request-1의 **거절된** payload에는 `TPREF B M3 1 1`도 보인다. 실제 B·M3·슬롯 1 선호 합은 B2(1)+B3(3)=4이며, 최초 전달된 request-2/m1에서는 `TPREF B M3 1 4`로 바뀌어 있다. 파서는 값 오류를 지적한 것이 아니라 문법 오류를 반환했다. 이 값 변화는 전송 전에 일어난 재작성이고, 상대가 받은 오류의 교정이나 task 내용 오류 11건의 추가 항목으로 세지 않는다.

6/08 마지막 m6에는 올바른 후보와 `askvalid(1,6,10).`, `askscore(1,6,10).`가 있다. 그 뒤 A request-12와 B request-13은 submit으로 끝난다. 해당 질문에 답하는 추가 peer 메시지는 없다. 제출과 평가기 성공은 확인되지만, 질문에 대한 명시적 답변이나 상대의 독립 검산 수행을 대신하는 증거로 보지 않는다.

## 평가 동등성과 한계

구조화 표현은 공통 명시 필드로 정규화되어 동일한 주장 검산 함수를 사용했다. 오류 11건의 원문 값과 기대값, 보류 1건, 코덱 0건이 직접 대조 범위와 일치했다. 원문에 없는 유효성·최적성 주장 추가, 질문의 사실 채점, 생략의 오류 채점은 발견하지 않았다. 다만 공통 스키마 자체가 표현 범위를 제한하며 자연어 전체 의미와 동등한 측정을 입증하지는 않는다.

불가능한 후보 자체와 거짓 명시 주장은 별개다. 2/06과 4/06의 불가능한 제안은 후보 품질에서 검출되지만, 거짓 valid 주장을 덧붙이지 않은 이상 내용 오류를 추가하지 않는다. 반대로 3/07은 최종 유효 일정에 합의했어도 전송된 요약 오류와 최적점수 격차가 남는다.

코덱 보존 검사 46개는 task 패킷 범위다. 사전 합의 7개는 이 주장·task 코덱 검사의 분모에 포함하지 않는다. 4단계는 고정 의미 특성 벡터이고 5단계는 고정 바이트코드이며 모델은 복원된 JSON을 읽는다. 틀린 내용을 보존했다는 사실과 모델 이해·추론의 정확성을 구분한다.

이 15회에서 제출 미완료로 끝난 stop은 없지만, 제한된 표본으로 제어 문제가 일반적으로 없다고 결론 내리지 않는다. wait의 원인, 오류 요약이 19점의 실제 원인이었는지, 거절 때문에 특정 전략으로 바뀌었는지는 내부 상태를 관측하지 못했다. 추가 모델 호출이나 실험 개입 없이 확인한 동작 순서와 원문 근거만 기록했으며 방식별 순위나 인과 효과를 일반화하지 않는다.
