# 제어 흐름

모든 response/applied/rejected 및 제출 상태 대조.

## stage2 / trial25

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Duplicate JSON key: summaries|[]|[]→[]|
|request-2|A/task|send|applied|[1]|[]→[]|
|request-3|B/task|send|applied|[2]|[]→[]|
|request-4|A/task|send|applied|[3]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage2 / trial26

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|revise|applied|[3]|[]→[]|
|request-4|A/task|revise|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage3 / trial25

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage3 / trial26

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage4 / trial25

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|wait|applied|[]|['A']→['A']|
|request-5|A/task|wait|applied|[]|['A']→['A']|
|request-6|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage4 / trial26

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage5 / trial25

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|revise|applied|[3]|[]→[]|
|request-4|B/task|revise|applied|[4]|[]→[]|
|request-5|A/task|submit|applied|[]|[]→['A']|
|request-6|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage5 / trial26

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|submit|applied|[]|[]→['A']|
|request-5|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage6 / trial25

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|Symbols must contain 1-8 ASCII letters|[]|[]→[]|
|request-2|A/setup|define_language|applied|[1]|[]→[]|
|request-3|B/setup|accept_language|applied|[2]|[]→[]|
|request-4|A/task|send|Unknown predicate or invalid syntax: tpref(A,M1,0,4).|[]|[]→[]|
|request-5|A/task|send|Only one message kind|[]|[]→[]|
|request-6|A/task|send|applied|[3]|[]→[]|
|request-7|B/task|send|Only one message kind|[]|[]→[]|
|request-8|B/task|send|applied|[4]|[]→[]|
|request-9|A/task|send|applied|[5]|[]→[]|
|request-10|B/task|send|applied|[6]|[]→[]|
|request-11|A/task|submit|applied|[]|[]→['A']|
|request-12|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage6 / trial26

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|send|applied|[5]|[]→[]|
|request-6|A/task|submit|applied|[]|[]→['A']|
|request-7|B/task|submit|applied|[]|['A']→['A', 'B']|

