# 180회 제어·전송 이벤트 집계

원본 worktree의 **180개 고유 회차(단계별30개)**에서 직접 집계했다. `rejected.phase/category`를 사용했으며 결과 파일의 범주 합계로 phase를 추정하지 않았다.

|단계|task 거절: message_payload|setup 거절: language_setup|setup 거절: action_envelope|거절 합계|
|---|---:|---:|---:|---:|
|1|0|0|0|0|
|2|2|0|0|2|
|3|65|0|0|65|
|4|2|0|0|2|
|5|4|0|0|4|
|6|34|4|4|42|

다른 phase×category 조합은0건이다. **6단계는 setup8건·task34건**이며 `codec_rejected` 중복 이벤트는 다시 더하지 않았다.

|단계|전달 task|전달 setup|submit|wait|stop|revise 전체|기존 제출을 지운 revise|지운 제출 수|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1|103|0|60|9|1|2|1|1|
|2|86|0|61|3|0|13|1|1|
|3|150|0|60|2|0|8|0|0|
|4|85|0|60|3|0|10|0|0|
|5|89|0|60|7|0|9|0|0|
|6|114|62|60|5|0|3|0|0|
|합계|627|62|361|29|1|45|2|2|

제어 행동은 성공적으로 적용된 `experiment/applied` 기준이다. 실패한 응답 시도는 JSON의 attempted_actions에 별도 보존했다. setup 전송은 packet의 실제 phase인 `language_setup`이고 제어·거절의 phase는 `setup`이다.

기존 제출 삭제는 `submissions_invalidated.cleared_agents`가 비어 있지 않은 사건만 센다. 제출 상태를 응답 순서로 재구성해 실제 남아 있던 제출과 대조했으며, 모든 최종 제출도 result.json과 일치했다. 실제 삭제는 1/04 request-8과 2/18 request-8에서 각각 B 제출1개를 지운 두 사건이다. 유일한 stop은 1/06 request-7의 B 행동이며, 당시 B 제출만 있고 A는 미제출이었다. JSON에 회차·request·원본 경로를 남겼다.

응답1195개는 적용1080개+거절115개로 정확히 분리된다. 누락·중복 회차0개, A/B 세션360개도 모두 고유하다. 원본 파일1110개의 전후 해시가 같으며 추가 모델 호출은 없다.

[전체 집계·근거](control-summary.json) · [원본 해시](control-summary-source-hashes.json).
