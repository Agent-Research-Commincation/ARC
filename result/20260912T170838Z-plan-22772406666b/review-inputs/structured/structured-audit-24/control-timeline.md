# 제어 흐름

모든 response/applied/rejected 및 제출 상태 대조.

## stage2 / trial24

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage3 / trial24

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|Unknown predicate or invalid syntax: ask summary|[]|[]→[]|
|request-4|B/task|send|Unknown predicate or invalid syntax: ask summary|[]|[]→[]|
|request-5|B/task|send|Unknown predicate or invalid syntax: ask summary|[]|[]→[]|
|request-6|B/task|send|Unknown predicate or invalid syntax: ask summary|[]|[]→[]|
|request-7|B/task|send|Unknown predicate or invalid syntax: ask summary|[]|[]→[]|
|request-8|B/task|send|applied|[3]|[]→[]|
|request-9|A/task|send|applied|[4]|[]→[]|
|request-10|B/task|send|applied|[5]|[]→[]|
|request-11|A/task|send|applied|[6]|[]→[]|
|request-12|B/task|submit|applied|[]|[]→['B']|
|request-13|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage4 / trial24

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage5 / trial24

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|submit|applied|[]|[]→['A']|
|request-5|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage6 / trial24

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|send|applied|[5]|[]→[]|
|request-6|A/task|submit|applied|[]|[]→['A']|
|request-7|B/task|submit|applied|[]|['A']→['A', 'B']|

