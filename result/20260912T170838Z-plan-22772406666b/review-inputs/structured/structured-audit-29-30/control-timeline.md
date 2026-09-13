# 제어 흐름

모든 response/applied/rejected 및 제출 상태 대조.

## stage2 / trial29

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Duplicate JSON key: summaries|[]|[]→[]|
|request-2|A/task|send|applied|[1]|[]→[]|
|request-3|B/task|send|applied|[2]|[]→[]|
|request-4|A/task|submit|applied|[]|[]→['A']|
|request-5|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage2 / trial30

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage3 / trial29

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Unknown predicate or invalid syntax: asks ummary(available,B,M1,0).|[]|[]→[]|
|request-2|A/task|send|Unknown predicate or invalid syntax: asks ummary|[]|[]→[]|
|request-3|A/task|send|Unknown predicate or invalid syntax: asks ummary(available,B,M1,0).|[]|[]→[]|
|request-4|A/task|send|Unknown predicate or invalid syntax: asks ummary(available,B,M1,0).|[]|[]→[]|
|request-5|A/task|send|applied|[1]|[]→[]|
|request-6|B/task|send|Unknown predicate or invalid syntax: teamsummary|[]|[]→[]|
|request-7|B/task|send|applied|[2]|[]→[]|
|request-8|A/task|send|applied|[3]|[]→[]|
|request-9|B/task|send|Unknown predicate or invalid syntax: asks ummary|[]|[]→[]|
|request-10|B/task|send|Unknown predicate or invalid syntax: asks ummary(preference,A,M1,0).|[]|[]→[]|
|request-11|B/task|send|applied|[4]|[]→[]|
|request-12|A/task|send|applied|[5]|[]→[]|
|request-13|B/task|submit|applied|[]|[]→['B']|
|request-14|A/task|wait|applied|[]|['B']→['B']|
|request-15|B/task|send|applied|[6]|['B']→['B']|
|request-16|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage3 / trial30

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|Only one message kind|[]|[]→[]|
|request-2|B/task|send|applied|[1]|[]→[]|
|request-3|A/task|send|Unknown predicate or invalid syntax: te amavailable(A,M1,6,0).|[]|[]→[]|
|request-4|A/task|send|Unknown predicate or invalid syntax: ask summary(preference,B,M1,0).|[]|[]→[]|
|request-5|A/task|send|Unknown predicate or invalid syntax: ask summary(preference,B,M1,0).|[]|[]→[]|
|request-6|A/task|send|applied|[2]|[]→[]|
|request-7|B/task|send|applied|[3]|[]→[]|
|request-8|A/task|send|applied|[4]|[]→[]|
|request-9|B/task|send|applied|[5]|[]→[]|
|request-10|A/task|submit|applied|[]|[]→['A']|
|request-11|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage4 / trial29

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage4 / trial30

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage5 / trial29

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Unknown instruction or arity|[]|[]→[]|
|request-2|A/task|send|applied|[1]|[]→[]|
|request-3|B/task|send|applied|[2]|[]→[]|
|request-4|A/task|revise|applied|[3]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage5 / trial30

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage6 / trial29

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|applied|[2]|[]→[]|
|request-3|A/task|send|Message kind is required|[]|[]→[]|
|request-4|A/task|send|applied|[3]|[]→[]|
|request-5|B/task|send|applied|[4]|[]→[]|
|request-6|A/task|send|applied|[5]|[]→[]|
|request-7|B/task|send|applied|[6]|[]→[]|
|request-8|A/task|submit|applied|[]|[]→['A']|
|request-9|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage6 / trial30

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|Message kind is required|[]|[]→[]|
|request-5|A/task|send|applied|[4]|[]→[]|
|request-6|B/task|send|applied|[5]|[]→[]|
|request-7|A/task|send|applied|[6]|[]→[]|
|request-8|B/task|submit|applied|[]|[]→['B']|
|request-9|A/task|submit|applied|[]|['B']→['A', 'B']|

