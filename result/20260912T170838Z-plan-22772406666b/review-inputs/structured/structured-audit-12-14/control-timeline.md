# 제어 흐름

실제 response/applied/rejected 및 제출 상태 재구성. `m`은 packet 번호이고 request 번호와 다르다.

## stage 2 / trial 12

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 2 / trial 13

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|revise|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [[]].

## stage 2 / trial 14

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 3 / trial 12

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|거절: Only one message kind|[]|[]→[]|
|request-2|B/task|send|applied|[1]|[]→[]|
|request-3|A/task|send|applied|[2]|[]→[]|
|request-4|B/task|send|거절: Unknown predicate or invalid syntax: asksummmary(available,A,M1,0).|[]|[]→[]|
|request-5|B/task|send|거절: Unknown predicate or invalid syntax: asksumary(available,A,M1,0).|[]|[]→[]|
|request-6|B/task|send|applied|[3]|[]→[]|
|request-7|A/task|send|applied|[4]|[]→[]|
|request-8|B/task|send|거절: Unknown predicate or invalid syntax: asksum mary(available,A,M1,0).|[]|[]→[]|
|request-9|B/task|send|거절: Unknown predicate or invalid syntax: asks ummary(available,A,M1,0).|[]|[]→[]|
|request-10|B/task|submit|applied|[]|[]→['B']|
|request-11|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 3 / trial 13

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|거절: Invalid question type or arguments|[]|[]→[]|
|request-2|A/task|send|applied|[1]|[]→[]|
|request-3|B/task|send|applied|[2]|[]→[]|
|request-4|A/task|send|applied|[3]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 3 / trial 14

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|revise|applied|[3]|[]→[]|
|request-4|A/task|submit|applied|[]|[]→['A']|
|request-5|B/task|submit|applied|[]|['A']→['A', 'B']|

실제 revise의 cleared_agents: [[]].

## stage 4 / trial 12

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 4 / trial 13

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|revise|applied|[3]|[]→[]|
|request-4|B/task|revise|applied|[4]|[]→[]|
|request-5|A/task|revise|applied|[5]|[]→[]|
|request-6|B/task|send|applied|[6]|[]→[]|
|request-7|A/task|submit|applied|[]|[]→['A']|
|request-8|B/task|submit|applied|[]|['A']→['A', 'B']|

실제 revise의 cleared_agents: [[], [], []].

## stage 4 / trial 14

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 5 / trial 12

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|revise|applied|[3]|[]→[]|
|request-4|A/task|revise|applied|[4]|[]→[]|
|request-5|B/task|revise|applied|[5]|[]→[]|
|request-6|A/task|revise|applied|[6]|[]→[]|
|request-7|B/task|send|applied|[7]|[]→[]|
|request-8|A/task|revise|applied|[8]|[]→[]|
|request-9|B/task|submit|applied|[]|[]→['B']|
|request-10|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [[], [], [], [], []].

## stage 5 / trial 13

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 5 / trial 14

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 6 / trial 12

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|send|applied|[5]|[]→[]|
|request-6|A/task|send|applied|[6]|[]→[]|
|request-7|B/task|submit|applied|[]|[]→['B']|
|request-8|A/task|submit|applied|[]|['B']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 6 / trial 13

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|send|거절: Only one message kind|[]|[]→[]|
|request-5|B/task|send|applied|[4]|[]→[]|
|request-6|A/task|send|applied|[5]|[]→[]|
|request-7|B/task|send|applied|[6]|[]→[]|
|request-8|A/task|submit|applied|[]|[]→['A']|
|request-9|B/task|submit|applied|[]|['A']→['A', 'B']|

실제 revise의 cleared_agents: [].

## stage 6 / trial 14

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|거절: Symbols must contain 1-8 ASCII letters|[]|[]→[]|
|request-2|B/setup|define_language|applied|[1]|[]→[]|
|request-3|A/setup|accept_language|applied|[2]|[]→[]|
|request-4|B/task|send|applied|[3]|[]→[]|
|request-5|A/task|send|applied|[4]|[]→[]|
|request-6|B/task|send|applied|[5]|[]→[]|
|request-7|A/task|submit|applied|[]|[]→['A']|
|request-8|B/task|submit|applied|[]|['A']→['A', 'B']|

실제 revise의 cleared_agents: [].

