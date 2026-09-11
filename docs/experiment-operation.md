# 실행 방법

Python 3.9 이상과 로그인된 Codex CLI가 필요하다. 명령은 `lab.py`가 있는 프로젝트 루트에서 실행한다. 모델은 `gpt-5.6-luna` / `high`, 반복 횟수는 방식별 5회로 설정돼 있다.

[문서 안내](README.md) · [실험 소개](phase-1-experiment.md) · [지표 읽는 법](metrics.md)

## 준비 상태 확인

```sh
python3 lab.py status
```

이 명령은 모델을 호출하지 않는다. 현재 소스의 오프라인 점검이 없거나 변경으로 오래된 경우 아래 명령으로 확인한다.

```sh
python3 lab.py check
```

`status`가 별도 연결 점검 기록이 없다고 표시해도 기존 본실험이 없다는 의미는 아니다. 기존 30회의 결과는 [대화 기록](../results/readable/20260911T092336Z-plan-cfd3ab2b1222-review-v3-1/README.md)에서 확인한다.

## 원하는 방식 실행

아래 명령은 실제 모델을 호출한다. 선택한 방식만 같은 문제에서 5회 실행하며, 매회 A·B 세션을 새로 만든다.

| 사용자 요청 | 방식 | 명령 |
|---|---|---|
| 1단계 해줘 | 자연어 | `python3 lab.py run 1` |
| 2단계 해줘 | JSON | `python3 lab.py run 2` |
| 3단계 해줘 | 논리식·관계 표현 | `python3 lab.py run 3` |
| 4단계 해줘 | 고정 의미 특성 벡터 | `python3 lab.py run 4` |
| 5단계 해줘 | 바이트코드 | `python3 lab.py run 5` |
| 6단계 해줘 | 공동 기호 언어 | `python3 lab.py run 6` |

실험 중 코드·설정·문제를 바꾸지 않는다. 실패한 회차도 결과에 포함하며 성공할 때까지 다시 실행하지 않는다. 별도 예비 실행이 없어도 요청한 본실험을 바로 실행할 수 있다.

## worktree에서 병렬 실행

```sh
python3 lab.py run-many 1 2 3 4 5 6 --jobs 6
```

요청한 단계별로 같은 소스 커밋의 새 `.worktree`를 만들고, 총 30회를 실행한다. 기존 결과 폴더를 덮어쓰지 않는다. 각 방식 안에서는 두 회차가 겹치지 않으며 회차마다 새 세션을 사용한다. 예를 들어 1·2단계만 병렬 실행하려면 다음과 같이 지정한다.

```sh
python3 lab.py run-many 1 2 --jobs 2
```

`--jobs`의 기본값은 1이다. 병렬 실행 수와 실행 순서는 계획에 기록되고, 원본과 중앙 사본은 파일 해시로 대조한다. 실행기의 worker는 별도 프로세스다. 담당 서브에이전트의 진행·기록 관리까지 원하면 함께 요청하며, `run-many` 자체가 Codex 서브에이전트를 만드는 것은 아니다.

## 결과와 대화 읽기

실행이 끝나면 안내된 실행 폴더의 `report.md`에서 묶음 결과를 확인한다. 각 `trial-01`~`trial-05`에는 실제 시작한 회차의 결과가 저장된다.

```text
results/plans/<plan-id>/                 실행 배정·진행 상태·worktree 위치
results/experiment/<run-id>/            실행 조건·원본 이벤트·회차 결과·보고서
results/reviews/<run-id>/<review-id>/    대화 내용 평가와 판정 근거
results/readable/<batch-id>/<방식>/      사람이 읽는 대화·Agent별 기록
results/analysis/<analysis-id>/         비교표·대화 사례·집계 자료
```

| 파일 | 읽을 내용 |
|---|---|
| `transcript.md` | 시간순 실제 대화와 전달·거절·수정·제출 과정 |
| `Agent_A.md`, `Agent_B.md` | 각 Agent에게 제공된 입력과 실제 응답 |
| `observation.md` | 명시된 주장과 내용 오류의 근거 |

기존 결과만 비교하려면 아래 명령을 사용한다. 모델은 호출하지 않으며 같은 문제·구현·설정·CLI 버전·실행 프로필끼리 묶는다. 대화 내용 평가는 선택한 평가 버전의 관찰표를 함께 읽는다.

```sh
python3 lab.py compare
```

## 대화 평가와 내보내기

`review`는 종료된 원본을 읽어 별도의 평가 버전을 만든다. 모델을 호출하지 않는다. 구조화 주장은 자동 평가하고, 자연어는 원문을 검토할 입력 양식을 생성한다. 자연어 양식을 작성하지 않은 상태는 내용 평가 대기이며 오류 0건이 아니다.

```sh
python3 lab.py review <실행 폴더>
python3 lab.py review <실행 폴더> --manual-inputs <회차별 입력 경로.json> --reviewer <검토자>
python3 scripts/export_histories.py --source <실행 폴더> --review <평가 폴더> --output results/readable/<새 묶음>/<방식>
```

`--manual-inputs` 파일은 `{"trial-01":"/절대/경로/입력.json"}`처럼 회차와 작성한 양식을 연결한다. 양식에는 원문 근거와 작성자가 AI인지 사람인지 표시한다. 원본·기존 평가 폴더를 직접 고치지 않고 새 버전으로 저장한다.

내보내기는 지정한 원본과 평가를 사람이 읽는 파일로 옮긴다. 다시 채점하지 않으며 기존 출력 폴더를 덮어쓰지 않는다. `--review`를 생략하면 내용 평가 대기로 표시된다. 평가의 의미와 한계는 [지표 읽는 법](metrics.md)을 따른다.

## 중단과 보조 명령

Agent의 진행 포기나 과제 실패는 해당 회차의 결과로 남긴다. 인프라 오류는 새 회차 배정을 멈추며, 사용자 취소는 진행 중인 작업에도 전달된다. 정상적으로 중단 기록을 남긴 계획은 아래 명령으로 아직 시작하지 않은 회차만 재개한다.

```sh
python3 lab.py resume <계획 ID 또는 plan.json>
```

이전 결과는 보존된다. 강제 종료로 실행 여부가 미확정인 회차는 자동 재실행하지 않으며 원본과 프로세스 상태를 먼저 확인해야 한다.

다음 명령도 실제 모델을 호출하며 본실험과 구분해 저장한다.

| 명령 | 용도 |
|---|---|
| `python3 lab.py observe` | 메시지 형식을 지정하지 않은 협업 5회 관찰 |
| `python3 lab.py pilot 1` | 1단계의 1회 예비 실행 |
| `python3 lab.py verify-live --stage 1` | 일정 풀이와 분리한 연결·전송 점검 |

## 결과를 다른 사람에게 전달하기

기존 30회는 [공유용 ZIP과 체크섬](../releases/README.md)으로 전달할 수 있다. 읽기용 기록뿐 아니라 원본, 선택한 평가 코드·manifest·주석, 분석 코드가 함께 들어 있다. 원래 프로젝트 폴더와 Codex 로그인 없이 Python 3.9 이상에서 확인할 수 있다.

압축을 푼 묶음의 README가 있는 폴더에서 실행한다. 출력은 아직 없는 새 폴더로 지정한다.

```sh
python3 scripts/verify_release.py --bundle . --output ../new-replay
```

이 명령은 체크섬·원본 봉인, 30회 관찰표, 비용·시간·전송량과 주요 표를 다시 확인한다. 기존 주석의 판정을 재현하며 자연어를 새로 독립 해석하거나 실험 모델을 호출하지 않는다. 결과는 출력 폴더의 `verification.json`과 `analysis/`에 남는다.

`--review`로 평가를 선택한 새 단일 내보내기에는 `selected-review/`에 정확한 사후 평가 코드와 주석이 들어간다. 실험 당시 코드는 `source/`에 따로 보존한다. 해당 내보내기의 `README.md`와 `replay_review.py`가 있는 폴더에서 아래 명령으로 판정을 재현한다. 출력은 내보내기 폴더 밖의 아직 없는 새 폴더로 지정한다.

```sh
python3 replay_review.py --export . --output ../new-review-replay
```

현재 선택된 30회에 대해 배포 묶음을 다시 만들려면 아래 명령을 사용한다. 다른 실행 묶음을 자동 선택하는 명령은 아니다. 고유한 새 이름과 출력 경로를 지정하며 기존 결과·배포 파일은 덮어쓰지 않는다.

```sh
python3 scripts/build_release.py --release-id <새 이름> --output results/releases/<새 이름> --archive releases/<새 이름>.zip
```
