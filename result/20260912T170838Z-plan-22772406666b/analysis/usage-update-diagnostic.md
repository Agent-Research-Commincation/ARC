# 6/09 B 사용량 갱신 진단

**차이는 이전 사용량 snapshot의 반복 갱신으로 설명된다. 최종 provider total 검산과 total 기반 보고 비용에는 영향이 없다.** 원본·중앙 events/result 파일은 바이트 단위로 같고 진단 중 변경하지 않았다.

`audit_events.py`는 각 세션의 최신 total을 확정 사용량으로 사용한다. 모든 last를 더하는 루프는 별도 진단용이다. 기존180회 감사는 모두 total 검산을 통과했고, 진단 불일치는6/09 B 한 건으로 기록돼 있다. 이번에는 이 회차의 A·B 전체8개 사용량 이벤트를 독립 대조했다.

|B event|request/phase|turn|totalTokens|last.totalTokens|직전 total 대비 증가|
|---:|---|---|---:|---:|---:|
|241|request-2/setup|01a096b8-6347-75e2-b98d-406c69b8e99a|7316|7316|7316|
|1669|request-4/task|01a096b8-ecd3-7bd2-9e2b-c35c813d6561|7316|7316|0|
|2500|request-4/task|01a096b8-ecd3-7bd2-9e2b-c35c813d6561|19504|12188|12188|
|2589|request-6/task|01a096ba-5045-7fe0-abe9-202435293828|31866|12362|12362|

**event1669의 tokenUsage(total·last·modelContextWindow)는 setup event241과 완전히 같다.** 다만 turnId는 다음 task request-4의 것으로 다르다. 따라서 원본 이벤트 전체가 동일하게 복제됐다는 뜻은 아니다. 새 task 진행 중 이전 사용량 snapshot을 다시 받은 것이 관측되며, provider가 그렇게 내보낸 내부 원인은 이 자료만으로 확정할 수 없다. 이후 같은 task의 event2500에서 실제 증가분12,188이 반영된다.

|필드|최종 provider total = result|모든 last의 단순 합|초과분|
|---|---:|---:|---:|
|totalTokens|31866|39182|7316|
|inputTokens|30873|38134|7261|
|cachedInputTokens|26880|33792|6912|
|cacheWriteInputTokens|0|0|0|
|outputTokens|993|1048|55|
|reasoningOutputTokens|76|105|29|

초과분 전체가 event241/1669의 동일한 setup last와 일치한다. total 증분을 모두 더하거나 같은 turn의 마지막 갱신만 비교하면 최종 total과 모든 필드가 일치한다. 이는 진단상의 재구성이며 원본 이벤트를 삭제하거나 기존 감사 코드를 고치지 않았다. A의4개 이벤트는 last 합과 total이 원래 일치한다.

**비용:** 저장된 total과 고정 실험 단가로 독립 계산한 B 비용은 **$0.00252780**, A+B 합은 **$0.00854540**이다. result와 raw-measurement-audit의 비용에 일치한다. 잘못 last 합을 비용에 사용했다면 **$0.00027404**가 더해지겠지만 실제 보고서는 total을 사용하므로 **보고 비용 영향은 $0**이다. API 단가 기반 추정이며 실제 구독 청구서를 확인한 것은 아니다.

원본·중앙 자료, 감사 코드·감사 보고서·단가 manifest의 전후 해시가 같다. 사용량 이벤트8개를 빠짐없이 JSON에 보존했으며 추가 모델 호출은 없다.

[전체 필드·이벤트·해시 근거](usage-update-diagnostic.json).
