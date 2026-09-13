# 제어 요청·적용·제출 상태

96개 응답의 action과 applied/rejected/packet을 자동 연결했다. 제출 상태는 적용 사건으로 복원했으며 회차별 최종 result.submissions와 일치했다. 이는 상대 Agent에게 공개된 상태가 아니다. send/submit/wait/revise/stop의 payload와 동작을 구분한다.

## 2단계 / trial-06

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | send | applied | [3] | [] → [] |
| request-4 | A | task | revise | applied | [4] | [] → [] |
| request-5 | B | task | submit | applied | [] | [] → ['B'] |
| request-6 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 2단계 / trial-07

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 2단계 / trial-08

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | submit | applied | [] | [] → ['B'] |
| request-4 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 3단계 / trial-06

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | send | applied | [3] | [] → [] |
| request-4 | A | task | submit | applied | [] | [] → ['A'] |
| request-5 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 3단계 / trial-07

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 3단계 / trial-08

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | rejected: Only one message kind | [] | [] → [] |
| request-3 | A | task | send | applied | [2] | [] → [] |
| request-4 | B | task | send | applied | [3] | [] → [] |
| request-5 | A | task | submit | applied | [] | [] → ['A'] |
| request-6 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 4단계 / trial-06

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | send | applied | [3] | [] → [] |
| request-4 | A | task | send | applied | [4] | [] → [] |
| request-5 | B | task | send | applied | [5] | [] → [] |
| request-6 | A | task | send | applied | [6] | [] → [] |
| request-7 | B | task | submit | applied | [] | [] → ['B'] |
| request-8 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 4단계 / trial-07

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | rejected: Duplicate JSON key: summaries | [] | [] → [] |
| request-2 | A | task | send | applied | [1] | [] → [] |
| request-3 | B | task | send | applied | [2] | [] → [] |
| request-4 | A | task | send | applied | [3] | [] → [] |
| request-5 | B | task | send | applied | [4] | [] → [] |
| request-6 | A | task | send | applied | [5] | [] → [] |
| request-7 | B | task | submit | applied | [] | [] → ['B'] |
| request-8 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 4단계 / trial-08

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | submit | applied | [] | [] → ['B'] |
| request-4 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 5단계 / trial-06

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | rejected: Unknown instruction or arity | [] | [] → [] |
| request-2 | B | task | send | applied | [1] | [] → [] |
| request-3 | A | task | send | applied | [2] | [] → [] |
| request-4 | B | task | submit | applied | [] | [] → ['B'] |
| request-5 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 5단계 / trial-07

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | wait | applied | [] | ['A'] → ['A'] |
| request-5 | A | task | wait | applied | [] | ['A'] → ['A'] |
| request-6 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 5단계 / trial-08

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | send | applied | [3] | [] → [] |
| request-4 | A | task | send | applied | [4] | [] → [] |
| request-5 | B | task | submit | applied | [] | [] → ['B'] |
| request-6 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 6단계 / trial-06

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | setup | define_language | rejected: Symbols must contain 1-8 ASCII letters | [] | [] → [] |
| request-2 | B | setup | define_language | applied | [1] | [] → [] |
| request-3 | A | setup | accept_language | applied | [2] | [] → [] |
| request-4 | B | task | send | rejected: Message kind is required | [] | [] → [] |
| request-5 | B | task | send | applied | [3] | [] → [] |
| request-6 | A | task | send | applied | [4] | [] → [] |
| request-7 | B | task | submit | applied | [] | [] → ['B'] |
| request-8 | A | task | wait | applied | [] | ['B'] → ['B'] |
| request-9 | B | task | send | applied | [5] | ['B'] → ['B'] |
| request-10 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 6단계 / trial-07

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | A | setup | define_language | applied | [1] | [] → [] |
| request-2 | B | setup | accept_language | applied | [2] | [] → [] |
| request-3 | A | task | send | applied | [3] | [] → [] |
| request-4 | B | task | send | applied | [4] | [] → [] |
| request-5 | A | task | send | applied | [5] | [] → [] |
| request-6 | B | task | submit | applied | [] | [] → ['B'] |
| request-7 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 6단계 / trial-08

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |
|---|---|---|---|---|---|---|
| request-1 | B | setup | define_language | rejected: Symbols must contain 1-8 ASCII letters | [] | [] → [] |
| request-2 | B | setup | define_language | applied | [1] | [] → [] |
| request-3 | A | setup | accept_language | rejected: Only define_language can contain a dictionary | [] | [] → [] |
| request-4 | A | setup | define_language | applied | [2] | [] → [] |
| request-5 | B | setup | accept_language | applied | [3] | [] → [] |
| request-6 | B | task | send | rejected: Unknown predicate or invalid syntax: teavl(B,M1,0,1). | [] | [] → [] |
| request-7 | B | task | send | applied | [4] | [] → [] |
| request-8 | A | task | send | rejected: Unknown predicate or invalid syntax: teavl(A,M1,0,0). | [] | [] → [] |
| request-9 | A | task | send | rejected: Only one message kind | [] | [] → [] |
| request-10 | A | task | send | applied | [5] | [] → [] |
| request-11 | B | task | send | applied | [6] | [] → [] |
| request-12 | A | task | submit | applied | [] | [] → ['A'] |
| request-13 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

