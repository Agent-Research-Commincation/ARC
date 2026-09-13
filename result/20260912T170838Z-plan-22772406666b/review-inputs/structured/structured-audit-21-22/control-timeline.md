# 제어 흐름

모든 response/applied/rejected 및 제출 상태를 대조했다.

## stage 2 / trial 21

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 2 / trial 22

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 3 / trial 21

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Only one message kind|[]|[]→[]|
|request-2|A/task|send|applied|[1]|[]→[]|
|request-3|B/task|send|applied|[2]|[]→[]|
|request-4|A/task|revise|applied|[3]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 3 / trial 22

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|Unknown predicate or invalid syntax: asksum mary(preference,A,M1,0).|[]|[]→[]|
|request-2|B/task|send|Unknown predicate or invalid syntax: asks ummary(available,A,M1,0).|[]|[]→[]|
|request-3|B/task|send|applied|[1]|[]→[]|
|request-4|A/task|send|applied|[2]|[]→[]|
|request-5|B/task|send|applied|[3]|[]→[]|
|request-6|A/task|submit|applied|[]|[]→['A']|
|request-7|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 4 / trial 21

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 4 / trial 22

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 5 / trial 21

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 5 / trial 22

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 6 / trial 21

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|send|applied|[4]|[]→[]|
|request-5|A/task|submit|applied|[]|[]→['A']|
|request-6|B/task|wait|applied|[]|['A']→['A']|
|request-7|A/task|send|applied|[5]|['A']→['A']|
|request-8|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 6 / trial 22

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

