# 제어 흐름

모든 response/applied/rejected 및 제출 상태 대조.

## stage2 / trial27

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage2 / trial28

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|revise|applied|[5]|[]→[]|
|request-6|A/task|revise|applied|[6]|[]→[]|
|request-7|B/task|submit|applied|[]|[]→['B']|
|request-8|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage3 / trial27

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Unknown predicate or invalid syntax: asksumary|[]|[]→[]|
|request-2|A/task|send|Unknown predicate or invalid syntax: asksumary|[]|[]→[]|
|request-3|A/task|send|Unknown predicate or invalid syntax: asksumary(availability,B,M1,0).|[]|[]→[]|
|request-4|A/task|send|Unknown predicate or invalid syntax: asksumm ary(available,B,M1,0).|[]|[]→[]|
|request-5|A/task|send|applied|[1]|[]→[]|
|request-6|B/task|send|applied|[2]|[]→[]|
|request-7|A/task|send|applied|[3]|[]→[]|
|request-8|B/task|send|applied|[4]|[]→[]|
|request-9|A/task|send|applied|[5]|[]→[]|
|request-10|B/task|submit|applied|[]|[]→['B']|
|request-11|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage3 / trial28

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|Invalid question type or arguments|[]|[]→[]|
|request-2|B/task|send|applied|[1]|[]→[]|
|request-3|A/task|send|Only one message kind|[]|[]→[]|
|request-4|A/task|send|applied|[2]|[]→[]|
|request-5|B/task|send|applied|[3]|[]→[]|
|request-6|A/task|send|applied|[4]|[]→[]|
|request-7|B/task|send|applied|[5]|[]→[]|
|request-8|A/task|send|applied|[6]|[]→[]|
|request-9|B/task|submit|applied|[]|[]→['B']|
|request-10|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage4 / trial27

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|revise|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage4 / trial28

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|revise|applied|[3]|[]→[]|
|request-4|A/task|revise|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage5 / trial27

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage5 / trial28

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage6 / trial27

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|send|applied|[4]|[]→[]|
|request-5|A/task|send|applied|[5]|[]→[]|
|request-6|B/task|send|applied|[6]|[]→[]|
|request-7|A/task|submit|applied|[]|[]→['A']|
|request-8|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage6 / trial28

|request|주체/phase|action|결과|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|Only define_language can contain a dictionary|[]|[]→[]|
|request-3|A/setup|define_language|applied|[2]|[]→[]|
|request-4|B/setup|accept_language|applied|[3]|[]→[]|
|request-5|B/task|send|applied|[4]|[]→[]|
|request-6|A/task|send|Only one message kind|[]|[]→[]|
|request-7|A/task|send|Unknown predicate or invalid syntax: askvalid(1,6,10).|[]|[]→[]|
|request-8|A/task|send|applied|[5]|[]→[]|
|request-9|B/task|send|Only one message kind|[]|[]→[]|
|request-10|B/task|send|applied|[6]|[]→[]|
|request-11|A/task|send|applied|[7]|[]→[]|
|request-12|B/task|send|applied|[8]|[]→[]|
|request-13|A/task|submit|applied|[]|[]→['A']|
|request-14|B/task|submit|applied|[]|['A']→['A', 'B']|

