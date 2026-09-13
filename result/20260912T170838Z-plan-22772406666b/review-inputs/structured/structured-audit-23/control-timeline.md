# 제어 흐름

모든 response/applied/rejected 및 제출 상태 대조.

## stage2 / trial23

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage3 / trial23

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Unknown predicate or invalid syntax: asksummmary(preference,B,M1,1).|[]|[]→[]|
|request-2|A/task|send|Unknown predicate or invalid syntax: asksummmary(preference,B,M1,1).|[]|[]→[]|
|request-3|A/task|send|Unknown predicate or invalid syntax: asksu mmary(preference,B,M1,1).|[]|[]→[]|
|request-4|A/task|send|Unknown predicate or invalid syntax: asks ummary(preference,B,M1,1).|[]|[]→[]|
|request-5|A/task|send|applied|[1]|[]→[]|
|request-6|B/task|send|Unknown predicate or invalid syntax: askSummary(availability,A,M1,0).|[]|[]→[]|
|request-7|B/task|send|Unknown predicate or invalid syntax: askSummary(available,A,M1,0).|[]|[]→[]|
|request-8|B/task|send|applied|[2]|[]→[]|
|request-9|A/task|send|applied|[3]|[]→[]|
|request-10|B/task|send|Unknown predicate or invalid syntax: askSummary(preference,A,M1,0).|[]|[]→[]|
|request-11|B/task|send|Unknown predicate or invalid syntax: askSummary(preference,A,M1,0).|[]|[]→[]|
|request-12|B/task|send|applied|[4]|[]→[]|
|request-13|A/task|send|applied|[5]|[]→[]|
|request-14|B/task|send|applied|[6]|[]→[]|
|request-15|A/task|send|applied|[7]|[]→[]|
|request-16|B/task|send|applied|[8]|[]→[]|
|request-17|A/task|send|applied|[9]|[]→[]|
|request-18|B/task|send|applied|[10]|[]→[]|
|request-19|A/task|send|applied|[11]|[]→[]|
|request-20|B/task|submit|applied|[]|[]→['B']|
|request-21|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage4 / trial23

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage5 / trial23

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|wait|applied|[]|['A']→['A']|
|request-5|A/task|wait|applied|[]|['A']→['A']|
|request-6|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage6 / trial23

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|applied|[2]|[]→[]|
|request-3|A/task|send|Message kind is required|[]|[]→[]|
|request-4|A/task|send|applied|[3]|[]→[]|
|request-5|B/task|send|applied|[4]|[]→[]|
|request-6|A/task|send|Invalid question type or arguments|[]|[]→[]|
|request-7|A/task|send|applied|[5]|[]→[]|
|request-8|B/task|submit|applied|[]|[]→['B']|
|request-9|A/task|submit|applied|[]|['B']→['A', 'B']|

