# 2~6단계 trial18~19 추가 과정 감사

10회 모두 첫 전체 후보와 최종 제출이 `(M1,M2,M3)=(1,6,10)`, 유효·20점이다. 내용 주장은 **정답 1,572 / 오류 0 / 보류 0**, 전달된 task 메시지는 36개, 코덱 오류는 0건이다. 다만 2/18은 중간에 불가능 후보로 바뀌었다. 최종 성공과 과정의 문제를 구분한다.

## 핵심 사례: 같은 payload의 revise가 기존 제출을 지움

**2단계 trial18**의 흐름은 다음과 같다.

|원문 위치|관찰된 행동|제출 상태|
|---|---|---|
|m1 / request-1 B|B 팀 요약에 `available/B/M1/8=0`을 정확히 전달.|없음|
|m2 / request-2 A|최적 `(1,6,10)` 제안.|없음|
|m3 / request-3 B|`revise`로 `(8,6,10)` 재제안. B1이 M1 슬롯 8에 불가하므로 불가능 후보.|없음→없음|
|m4 / request-4 A|`send`로 `(1,6,10)`과 `unavailable/M1/B1/8` 사유 전달.|없음|
|request-5 B|대안 `(1,6,10)` 제출.|B|
|request-6 A, request-7 B|각각 wait.|B 유지|
|m5 / request-8 A|**m4와 완전히 같은 payload를 `revise`로 재전송.**|B→없음|
|request-9 B, request-10 A|B가 같은 일정을 재제출하고 A도 제출.|B→A·B|

`experiment/submissions_invalidated`는 첫 revise에 `cleared_agents=[]`, 두 번째에는 **`['B']`**를 기록했다. 동일 payload 여부 및 B 재제출 일정의 동일성을 문자열·상태 대조로 확인했다. 두 번째 revise는 후보 값을 더 고친 동작이 아니며, 이미 유효한 B 제출을 무효화하고 다시 제출하게 했다. 반면 m3의 불가능 후보는 m4의 정확한 불가 사유와 대안으로 수정됐고 B는 그 대안을 제출했다. 불가능 후보 자체에 명시 `valid=1` 주장이 없으므로 내용 오류로 추가 계산하지 않았다. A가 왜 같은 내용을 revise했는지는 원문 행동만으로 단정하지 않는다.

## 다른 제어·정보 교환 사례

**6단계 trial19 — 제출을 유지한 채 wait와 동일 요약 재전송.** B가 request-10에서 `(1,6,10)`을 제출한 뒤 A·B가 request-11·12에서 연속 두 번 wait했다. A는 request-13/m6에서 자기 팀 전체 요약 72개를 다시 보냈다. 이 값들은 m3의 A 요약과 전부 동일하고 후보 슬롯 요약 6개도 m5에서 이미 보낸 상태다. B가 request-14에서 한 번 더 wait한 뒤 A가 request-15에서 제출했다. send가 사이에 있어 마지막 wait의 연속 횟수는 1이다. 이 과정에서 B의 제출은 계속 유지됐으며 stop·revise는 없었다. m6은 내용 오류 교정이나 새 요약 정보 추가로 표현하지 않는다.

**3단계 trial18 — 개인 자료 10개에서 72개로 요청 확대, 제출 후 수락 전송.** B는 후보 슬롯의 A 개인 가용성·선호도 10개를 m3에서 요청하고 m4에서 받았다. m5에서는 A1~A3 전체 슬롯 자료 72개를 요청했고 m6에서 모두 받았다. B 제출(request-8) → A wait(request-9) → B의 별도 accept 전송(m7/request-10) → A 제출(request-11)로 끝났다. 이때도 기존 제출은 유지됐다.

**3단계 trial19 — 질문 72개에 주장 108개로 응답.** 적용된 m1 질문은 B 팀 선호도 요약 36개와 B 개인 가용성 36개다. B의 m2는 요청된 자료에 더해 **B 팀 가용성 요약 36개**도 포함한다. 요청 누락 0개와 추가 36개를 키 집합으로 확인했다. 이후 A의 m3은 후보와 해당 슬롯의 A 요약 6개를 담고, B의 m4 요청에 A가 전체 요약 72개를 m5로 응답한다. 추가·중복 전달을 오류 교정으로 세지 않는다.

## 거절과 그 후 실제 수정

|범위|기록된 거절|이후 행동|
|---|---|---|
|3/18 request-1|알 수 없는 술어 `teavailable`|`teamavailable`로 바꾼 m1 전달. 이 치환 외의 내용은 동일.|
|3/19 request-1|`Invalid question type or arguments`|A 요약과 `asksummary(availability,...)`를 포함한 요청이 거절된 뒤 자기 요약을 빼고 선호도 요약·개인 가용성의 혼합 질문으로 바꿈. 단순 오타 치환만 한 것은 아님.|
|3/19 request-2|알 수 없는 술어 `askummary`|해당 철자를 `asksummary`로 수정한 m1 전달. 수치·다른 내용은 동일.|
|6/18 request-3|`Message kind is required`|`inf().`를 앞에 추가한 m3 전달. 나머지 payload 동일.|
|6/18 request-5|문법 오류 `prop()`|누락된 마침표를 붙여 `prop().`로 수정한 m4 전달. 나머지 payload 동일.|
|6/19 setup request-2|`Only define_language can contain a dictionary`|`accept_language`의 language 배열을 비운 request-3이 적용됨.|
|6/19 request-4|`Message kind is required`|`i().`를 추가했으나 다음 request-5도 아래 인수 문제로 거절됨. 이 시점에는 아직 전달되지 않음.|
|6/19 request-5|`Invalid question type or arguments`|`qs(av,...)`, `qs(pref,...)`의 인수를 `available`, `preference`로 바꾼 m3 전달. 합의 기호는 술어 이름에 적용되고 이 질문의 타입 인수에는 원래 타입명이 사용됨.|
|6/19 request-7|`Only one message kind`|`i()` 정보와 `prp()` 제안을 한 응답에 넣은 거절 뒤, 제안 부분을 제거하고 정보만 m4로 전달. 최초 전달된 전체 후보는 이후 A의 m5.|

총 거절 **9건(task 8, setup 1)**이다. 전체 제어 응답 76개 중 task 적용은 `send 34 / revise 2 / submit 21 / wait 6`, setup 적용은 4개다. 적용된 stop은 없고 모든 회차가 양쪽 제출로 끝났다. 코드의 revise 분기는 일정 비교 없이 기존 제출을 비우며, 이 효과가 2/18 기록과 일치한다. 이 감사에서는 코드를 바꾸지 않았다.

## 검산 및 직접 읽은 범위

- 같은 `write_trial_records`와 `observation-review-v3.1`로 10회 전체를 임시 출력에 재계산했다. 정규화된 task 36개·제어 응답 76개를 자동 대조했다. 질문 442개를 사실 주장으로 추가하지 않았고, 코덱 오류 0은 전달된 메시지에 대한 값이다. 전달 전 거절 9건은 별도다.
- 직접 읽은 task 원문은 **23/36개**: 2/18 m1~5, 3/18 m1~7, 3/19 m1~5, 6/18 m3~4, 6/19 m3~6. 거절 응답 9개 전체, 2/18 모든 제어 응답, 3/18 request-8~11, 6/19 setup 수락과 제출·wait 응답 및 단계6 두 사전도 읽었다. 나머지는 자동대조·정규화 검토 범위다.
- 기존 평가기 산술 함수를 쓰지 않고 추출된 주장 **1,572개(팀 요약 1,164·개인 사실 406·불가 사유 2)**와 전체 후보 16개·최종 10개를 원본 문제에서 재계산했다. 모두 기존 판정과 일치하고 불가능 후보는 2/18 m3 하나다. 주장 추출 자체는 기존 파서를 사용했다. 1,728개 배정 중 유효 54개, 유일 최적 20점도 재확인했다.
- 원본 파일과 실행 소스 해시는 전후 동일하며 단계별 평가 소스도 같다. 코어·설정·원본 수정이나 추가 모델 호출은 없었다. 이 10회에서 방식의 우열·인과 효과를 일반화하지 않는다.

[관찰표](observation-table.md) · [선별 원문](selected-source-evidence.md) · [제어 흐름](control-timeline.md) · [검산](verification.json) · [읽기 기록](source-reading-log.json). `stage-N/trial-XX/` 아래 관찰 파일은 임시 사후 산출물이다.
