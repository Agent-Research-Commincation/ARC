# 제어 흐름

response/applied/rejected와 제출 상태를 전체 재구성했다.

## stage 2 / trial 15

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 2 / trial 16

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|submit|applied|[]|[]→['B']|
|request-4|A/task|wait|applied|[]|['B']→['B']|
|request-5|B/task|send|applied|[3]|['B']→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 2 / trial 17

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 3 / trial 15

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|send|Unknown predicate or invalid syntax: asksumMARY(available,B,M1,0).|[]|[]→[]|
|request-4|A/task|send|Unknown predicate or invalid syntax: asksumMARY(available,B,M1,0).|[]|[]→[]|
|request-5|A/task|send|Unknown predicate or invalid syntax: asksummmary(available,B,M1,0).|[]|[]→[]|
|request-6|A/task|send|Unknown predicate or invalid syntax: asks ummary(preference,B,M1,1).|[]|[]→[]|
|request-7|A/task|send|applied|[3]|[]→[]|
|request-8|B/task|send|applied|[4]|[]→[]|
|request-9|A/task|send|applied|[5]|[]→[]|
|request-10|B/task|send|applied|[6]|[]→[]|
|request-11|A/task|submit|applied|[]|[]→['A']|
|request-12|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 3 / trial 16

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|Invalid question type or arguments|[]|[]→[]|
|request-4|B/task|send|applied|[3]|[]→[]|
|request-5|A/task|send|applied|[4]|[]→[]|
|request-6|B/task|submit|applied|[]|[]→['B']|
|request-7|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 3 / trial 17

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|Only one message kind|[]|[]→[]|
|request-2|A/task|send|applied|[1]|[]→[]|
|request-3|B/task|send|applied|[2]|[]→[]|
|request-4|A/task|send|Invalid question type or arguments|[]|[]→[]|
|request-5|A/task|send|applied|[3]|[]→[]|
|request-6|B/task|send|Unknown predicate or invalid syntax: teამavailable(B,M1,0,1).|[]|[]→[]|
|request-7|B/task|send|applied|[4]|[]→[]|
|request-8|A/task|submit|applied|[]|[]→['A']|
|request-9|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 4 / trial 15

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|submit|applied|[]|[]→['B']|
|request-5|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 4 / trial 16

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|submit|applied|[]|[]→['B']|
|request-6|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 4 / trial 17

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 5 / trial 15

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|wait|applied|[]|['A']→['A']|
|request-5|A/task|send|applied|[3]|['A']→['A']|
|request-6|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 5 / trial 16

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/task|send|applied|[1]|[]→[]|
|request-2|A/task|send|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|submit|applied|[]|[]→['A']|
|request-5|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 5 / trial 17

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/task|send|applied|[1]|[]→[]|
|request-2|B/task|send|applied|[2]|[]→[]|
|request-3|A/task|submit|applied|[]|[]→['A']|
|request-4|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 6 / trial 15

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|Only define_language can contain a dictionary|[]|[]→[]|
|request-3|B/setup|accept_language|applied|[2]|[]→[]|
|request-4|A/task|send|Invalid question type or arguments|[]|[]→[]|
|request-5|A/task|send|applied|[3]|[]→[]|
|request-6|B/task|send|applied|[4]|[]→[]|
|request-7|A/task|submit|applied|[]|[]→['A']|
|request-8|B/task|submit|applied|[]|['A']→['A', 'B']|

## stage 6 / trial 16

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|B/setup|define_language|applied|[1]|[]→[]|
|request-2|A/setup|accept_language|applied|[2]|[]→[]|
|request-3|B/task|send|applied|[3]|[]→[]|
|request-4|A/task|send|applied|[4]|[]→[]|
|request-5|B/task|send|Unknown predicate or invalid syntax: askvalid(1,6,10).|[]|[]→[]|
|request-6|B/task|send|applied|[5]|[]→[]|
|request-7|A/task|send|applied|[6]|[]→[]|
|request-8|B/task|submit|applied|[]|[]→['B']|
|request-9|A/task|submit|applied|[]|['B']→['A', 'B']|

## stage 6 / trial 17

|request|주체/phase|action|적용/거절|m|제출 상태 전→후|
|---|---|---|---|---|---|
|request-1|A/setup|define_language|applied|[1]|[]→[]|
|request-2|B/setup|accept_language|applied|[2]|[]→[]|
|request-3|A/task|send|applied|[3]|[]→[]|
|request-4|B/task|send|applied|[4]|[]→[]|
|request-5|A/task|send|Unknown predicate or invalid syntax: askvalid(1,6,10).|[]|[]→[]|
|request-6|A/task|send|applied|[5]|[]→[]|
|request-7|B/task|send|applied|[6]|[]→[]|
|request-8|A/task|submit|applied|[]|[]→['A']|
|request-9|B/task|submit|applied|[]|['A']→['A', 'B']|

