# 제어 흐름

전체 response/applied/rejected 및 제출 상태 대조.

## stage 2 / trial20

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 3 / trial20

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|Invalid question type or arguments|[]|[]→[]|
|request-2|B/task|send|applied|[1]|[]→[]|
|request-3|A/task|send|applied|[2]|[]→[]|
|request-4|B/task|send|applied|[3]|[]→[]|
|request-5|A/task|send|applied|[4]|[]→[]|
|request-6|B/task|send|applied|[5]|[]→[]|
|request-7|A/task|submit|applied|[]|[]→['A']|
|request-8|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 4 / trial20

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 5 / trial20

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|wait|applied|[]|['B']→['B']|
|request-5|B/task|wait|applied|[]|['B']→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 6 / trial20

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|Only one message kind|[]|[]→[]|
|request-5|A/task|send|applied|[4]|[]→[]|
|request-6|B/task|send|Invalid predicate arguments|[]|[]→[]|
|request-7|B/task|send|Invalid predicate arguments|[]|[]→[]|
|request-8|B/task|send|Invalid predicate arguments|[]|[]→[]|
|request-9|B/task|send|Invalid predicate arguments|[]|[]→[]|
|request-10|B/task|send|applied|[5]|[]→[]|
|request-11|A/task|send|applied|[6]|[]→[]|
|request-12|B/task|send|applied|[7]|[]→[]|
|request-13|A/task|send|applied|[8]|[]→[]|
|request-14|B/task|send|applied|[9]|[]→[]|
|request-15|A/task|send|applied|[10]|[]→[]|
|request-16|B/task|revise|applied|[11]|[]→[]|
|request-17|A/task|submit|applied|[]|[]→['A']|
|request-18|B/task|submit|applied|[]|['A']→['A', 'B']|

