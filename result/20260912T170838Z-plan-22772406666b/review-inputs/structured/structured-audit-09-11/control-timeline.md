# 제어 요청·적용·거절 순서

87개 제어 응답을 자동 연결했다. 제출 상태는 적용 사건으로 복원하여 최종 result와 대조했다. 상대 Agent에게 공개된 상태라는 뜻은 아니다.

## 2단계 trial-09

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 2단계 trial-10

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | submit | applied | [] | [] → ['B'] |
| request-4 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 2단계 trial-11

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 3단계 trial-09

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | send | applied | [3] | [] → [] |
| request-4 | B | task | revise | rejected: Unknown predicate or invalid syntax: revise(). | [] | [] → [] |
| request-5 | B | task | revise | applied | [4] | [] → [] |
| request-6 | A | task | submit | applied | [] | [] → ['A'] |
| request-7 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 3단계 trial-10

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | rejected: Unknown predicate or invalid syntax: asksumary(preference,A,M1,0). | [] | [] → [] |
| request-2 | B | task | send | rejected: Unknown predicate or invalid syntax: asks ummary(available,A,M1,0). | [] | [] → [] |
| request-3 | B | task | send | applied | [1] | [] → [] |
| request-4 | A | task | send | applied | [2] | [] → [] |
| request-5 | B | task | send | applied | [3] | [] → [] |
| request-6 | A | task | send | applied | [4] | [] → [] |
| request-7 | B | task | send | applied | [5] | [] → [] |
| request-8 | A | task | send | applied | [6] | [] → [] |
| request-9 | B | task | send | applied | [7] | [] → [] |
| request-10 | A | task | submit | applied | [] | [] → ['A'] |
| request-11 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 3단계 trial-11

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 4단계 trial-09

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | send | applied | [3] | [] → [] |
| request-4 | B | task | submit | applied | [] | [] → ['B'] |
| request-5 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 4단계 trial-10

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | rejected: Expecting ',' delimiter: line 1 column 4690 (char 4689) | [] | [] → [] |
| request-2 | B | task | send | applied | [1] | [] → [] |
| request-3 | A | task | send | applied | [2] | [] → [] |
| request-4 | B | task | submit | applied | [] | [] → ['B'] |
| request-5 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 4단계 trial-11

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | applied | [1] | [] → [] |
| request-2 | B | task | send | applied | [2] | [] → [] |
| request-3 | A | task | submit | applied | [] | [] → ['A'] |
| request-4 | B | task | wait | applied | [] | ['A'] → ['A'] |
| request-5 | A | task | send | applied | [3] | ['A'] → ['A'] |
| request-6 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 5단계 trial-09

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | rejected: Invalid question type or arguments | [] | [] → [] |
| request-2 | A | task | send | applied | [1] | [] → [] |
| request-3 | B | task | send | applied | [2] | [] → [] |
| request-4 | A | task | submit | applied | [] | [] → ['A'] |
| request-5 | B | task | submit | applied | [] | ['A'] → ['A', 'B'] |

## 5단계 trial-10

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | B | task | send | applied | [1] | [] → [] |
| request-2 | A | task | send | applied | [2] | [] → [] |
| request-3 | B | task | submit | applied | [] | [] → ['B'] |
| request-4 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 5단계 trial-11

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | task | send | rejected: Invalid question type or arguments | [] | [] → [] |
| request-2 | A | task | send | applied | [1] | [] → [] |
| request-3 | B | task | send | applied | [2] | [] → [] |
| request-4 | A | task | send | applied | [3] | [] → [] |
| request-5 | B | task | submit | applied | [] | [] → ['B'] |
| request-6 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 6단계 trial-09

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | setup | define_language | applied | [1] | [] → [] |
| request-2 | B | setup | accept_language | applied | [2] | [] → [] |
| request-3 | A | task | send | applied | [3] | [] → [] |
| request-4 | B | task | send | applied | [4] | [] → [] |
| request-5 | A | task | send | applied | [5] | [] → [] |
| request-6 | B | task | submit | applied | [] | [] → ['B'] |
| request-7 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 6단계 trial-10

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | B | setup | define_language | applied | [1] | [] → [] |
| request-2 | A | setup | accept_language | applied | [2] | [] → [] |
| request-3 | B | task | send | applied | [3] | [] → [] |
| request-4 | A | task | send | applied | [4] | [] → [] |
| request-5 | B | task | send | applied | [5] | [] → [] |
| request-6 | A | task | send | applied | [6] | [] → [] |
| request-7 | B | task | submit | applied | [] | [] → ['B'] |
| request-8 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

## 6단계 trial-11

| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |
|---|---|---|---|---|---|---|
| request-1 | A | setup | define_language | applied | [1] | [] → [] |
| request-2 | B | setup | accept_language | applied | [2] | [] → [] |
| request-3 | A | task | send | applied | [3] | [] → [] |
| request-4 | B | task | send | applied | [4] | [] → [] |
| request-5 | A | task | send | applied | [5] | [] → [] |
| request-6 | B | task | submit | applied | [] | [] → ['B'] |
| request-7 | A | task | submit | applied | [] | ['B'] → ['B', 'A'] |

