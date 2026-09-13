# 제어 흐름

모든 응답과 applied/rejected를 request ID로 연결하고 제출 상태를 재구성했다.

## stage 2 / trial 18

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|revise|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|wait|applied|[]|['B']→['B']|
|request-7|B/task|wait|applied|[]|['B']→['B']|
|request-8|A/task|revise|applied|[5]|['B']→[]|
|request-9|B/task|submit|applied|[]|[]→['B']|
|request-10|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 2 / trial 19

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 3 / trial 18

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|Unknown predicate or invalid syntax: teavailable(B,M1,0,1).|[]|[]→[]|
|request-2|B/task|send|applied|[1]|[]→[]|
|request-3|A/task|send|applied|[2]|[]→[]|
|request-4|B/task|send|applied|[3]|[]→[]|
|request-5|A/task|send|applied|[4]|[]→[]|
|request-6|B/task|send|applied|[5]|[]→[]|
|request-7|A/task|send|applied|[6]|[]→[]|
|request-8|B/task|submit|applied|[]|[]→['B']|
|request-9|A/task|wait|applied|[]|['B']→['B']|
|request-10|B/task|send|applied|[7]|['B']→['B']|
|request-11|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 3 / trial 19

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Invalid question type or arguments|[]|[]→[]|
|request-2|A/task|send|Unknown predicate or invalid syntax: askummary(preference,B,M2,8).|[]|[]→[]|
|request-3|A/task|send|applied|[1]|[]→[]|
|request-4|B/task|send|applied|[2]|[]→[]|
|request-5|A/task|send|applied|[3]|[]→[]|
|request-6|B/task|send|applied|[4]|[]→[]|
|request-7|A/task|send|applied|[5]|[]→[]|
|request-8|B/task|submit|applied|[]|[]→['B']|
|request-9|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 4 / trial 18

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 4 / trial 19

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 5 / trial 18

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 5 / trial 19

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 6 / trial 18

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|Message kind is required|[]|[]→[]|
|request-4|B/task|send|applied|[3]|[]→[]|
|request-5|A/task|send|Unknown predicate or invalid syntax: prop()|[]|[]→[]|
|request-6|A/task|send|applied|[4]|[]→[]|
|request-7|B/task|submit|applied|[]|[]→['B']|
|request-8|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 6 / trial 19

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|Only define_language can contain a dictionary|[]|[]→[]|
|request-3|B/setup|accept_language|applied|[2]|[]→[]|
|request-4|A/task|send|Message kind is required|[]|[]→[]|
|request-5|A/task|send|Invalid question type or arguments|[]|[]→[]|
|request-6|A/task|send|applied|[3]|[]→[]|
|request-7|B/task|send|Only one message kind|[]|[]→[]|
|request-8|B/task|send|applied|[4]|[]→[]|
|request-9|A/task|send|applied|[5]|[]→[]|
|request-10|B/task|submit|applied|[]|[]→['B']|
|request-11|A/task|wait|applied|[]|['B']→['B']|
|request-12|B/task|wait|applied|[]|['B']→['B']|
|request-13|A/task|send|applied|[6]|['B']→['B']|
|request-14|B/task|wait|applied|[]|['B']→['B']|
|request-15|A/task|submit|applied|[]|['B']→['A', 'B']|

