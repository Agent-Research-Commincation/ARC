"""Batch lifecycle, trial execution, and reports. Planning lives in scheduling."""
import copy
import json
import resource
import shutil
import subprocess
import time
from pathlib import Path
from . import VERSION
from .codex import AppServer, ISOLATION_CONFIG
from .contracts import validate_config, schedule_from_action, CodexError, Cancelled, OPERATIONAL_STATES
from .artifacts import ROOT, Recorder, utcnow, digest, write_json, new_id, source_snapshot, seal_run, read_events, file_hashes
from .metrics import model_cost, stats, summarize, communication_totals
from .trial import Trial, base_prompt
from .problem import oracle, problem_diagnostics
from .protocols import STAGES, CODEC_VERSION, VECTOR_FEATURES, VECTOR_DIMENSIONS


def codex_version():
    executable = shutil.which("codex")
    if not executable:
        return "unavailable"
    return subprocess.check_output([executable,"--version"],text=True,stderr=subprocess.DEVNULL).strip()


def initialize_run(config, problem, stage, count, purpose, output_root, plan_id=None, profile=None, source_root=ROOT):
    validate_config(config)
    snapshot = source_snapshot(source_root)
    settings = {"config":copy.deepcopy(config),"problem":copy.deepcopy(problem),"codex_version":codex_version(),
        "source_hash":snapshot["sha256"],"codec_version":CODEC_VERSION,"isolation":ISOLATION_CONFIG,
        "execution_profile":profile or {"jobs":1,"mode":"serial"}}
    run_id = new_id("observe" if stage is None else "stage%d" % stage)
    folder = Path(output_root)/purpose/run_id
    folder.mkdir(parents=True,exist_ok=False)
    for relative in snapshot["files"]:
        target = folder/"source"/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(Path(source_root)/relative,target)
    if file_hashes(folder/"source") != snapshot["files"]:
        raise ValueError("Source changed while snapshot was being copied")
    manifest = {"run_id":run_id,"plan_id":plan_id,"purpose":purpose,"stage":stage,
        "stage_name":STAGES[stage] if stage else "소통 형식 자율 선택","created_at":utcnow(),
        "expected_trials":count,"runner_version":VERSION,"comparison_group":digest(settings),
        "comparison_settings":settings,"source_snapshot":snapshot,"problem_hash":digest(problem),
        "oracle":oracle(problem),"problem_diagnostics":problem_diagnostics(problem),"status":"running"}
    write_json(folder/"manifest.json",manifest)
    return folder


def failure_result(stage, status, error, elapsed=0):
    return {"status":status,"success":False,"error":error,"stage":stage,
        "task_outcome":None,"operational_status":status,"submissions":{},"sessions":{},
        "evaluation":None,"quality_gap":None,"elapsed_seconds":elapsed,"actions":0,
        "communication_bytes":0,"payload_bytes":0,"envelope_bytes":0,"message_count":0,
        "protocol_cpu_seconds":0.,"protocol_wall_seconds":0.,"protocol_errors":0,
        "model_cost_estimate_usd":None,"total_cost_estimate_usd":None,
        "communication_processing_cost_estimate_usd":None,"usage":{},"actual_charge_usd":None}


def execute_trial(config, problem, stage, folder, number, first_speaker, backend_factory=AppServer, cancel_event=None):
    folder = Path(folder)
    rec = Recorder(folder/("trial-%02d" % number))
    started,cpu_started = time.monotonic(),time.process_time()
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    result,initialization = None,0.
    try:
        backend = backend_factory(config,event_sink=rec.event)
        if cancel_event is not None:
            backend.cancel_event = cancel_event
        with backend:
            initialization = time.monotonic()-started
            trial = Trial(backend,config,problem,stage,rec,first_speaker,cancel_event)
            result = trial.run()
            task_finished = time.monotonic()
        cleanup = time.monotonic()-task_finished
    except (KeyboardInterrupt,Cancelled) as exc:
        result = result or failure_result(stage,"cancelled",str(exc) or "User cancelled",time.monotonic()-started)
        cleanup = 0.
    except Exception as exc:
        if result is None:
            result = failure_result(stage,"infrastructure_error",type(exc).__name__+": "+str(exc),time.monotonic()-started)
        else:
            # Preserve an already obtained task outcome even when cleanup fails.
            result["operational_status"] = "infrastructure_error"
            result["cleanup_error"] = str(exc)
        cleanup = 0.
    events = read_events(rec.folder)
    result.update(communication_totals(events))
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = (after.ru_utime+after.ru_stime)-(children.ru_utime+children.ru_stime)
    result.update(trial_number=number,first_speaker=first_speaker,
        runtime_initialization_seconds=initialization,runtime_cleanup_seconds=cleanup,
        task_elapsed_seconds=result["elapsed_seconds"],elapsed_seconds=time.monotonic()-started,
        runner_cpu_seconds=time.process_time()-cpu_started,codex_process_cpu_seconds=child_cpu)
    rate = config["pricing"]["local_processing_usd_per_cpu_second"]
    cpu_cost = (result["runner_cpu_seconds"]+child_cpu)*rate if rate is not None else None
    result["runner_cost_estimate_usd"] = cpu_cost
    model = result["model_cost_estimate_usd"]
    result["total_cost_estimate_usd"] = model+cpu_cost if model is not None and cpu_cost is not None else None
    result["communication_processing_cost_estimate_usd"] = result["protocol_cpu_seconds"]*rate if rate is not None else None
    save_started = time.monotonic()
    write_json(rec.folder/"result.json",result)
    from .records import write_transcripts
    (rec.folder/"observation.md").write_text("# 사후 검수 대기\n\n이 파일은 평가 결과가 아닙니다. 종료된 실행에 review 명령을 사용하면 별도 검수 버전이 생성됩니다.\n",encoding="utf-8")
    write_transcripts(rec.folder)
    result["record_render_seconds"] = time.monotonic()-save_started
    result["runner_cpu_seconds"] = time.process_time()-cpu_started
    cpu_cost = (result["runner_cpu_seconds"]+child_cpu)*rate if rate is not None else None
    result["runner_cost_estimate_usd"] = cpu_cost
    result["total_cost_estimate_usd"] = model+cpu_cost if model is not None and cpu_cost is not None else None
    result["elapsed_seconds"] = time.monotonic()-started
    result["timing_scope"] = "Backend initialization through record rendering; final atomic result write excluded. Coordinator queue/worktree time recorded separately."
    result["cost_scope"] = "API-equivalent model cost plus measured local CPU for this trial. Coordinator/worktree overhead is outside the per-trial boundary. Not a subscription invoice."
    write_json(rec.folder/"result.json",result)
    return result


def finalize_run(folder, state=None):
    folder = Path(folder)
    manifest = json.loads((folder/"manifest.json").read_text())
    results = [json.loads(p.read_text()) for p in sorted(folder.glob("trial-*/result.json"))]
    summary = summarize(results,manifest["expected_trials"])
    manifest["status"] = "completed" if summary["batch_complete"] else "incomplete"
    manifest["finished_at"] = utcnow()
    write_json(folder/"manifest.json",manifest)
    write_json(folder/"run-state.json",state or {"slots":[{"trial":i,"status":next((r["status"] for r in results if r["trial_number"]==i),"not_started")} for i in range(1,manifest["expected_trials"]+1)]})
    write_json(folder/"summary.json",summary)
    (folder/"report.md").write_text(report_markdown(manifest["stage"],summary,results,manifest["purpose"]),encoding="utf-8")
    seal_run(folder)
    return summary


def run_batch(config, problem, stage, repetitions=None, purpose="experiment", backend_factory=AppServer, output_root=None):
    from .scheduling import run_requested
    count = repetitions or config["repetitions"]
    if stage is None and not (purpose=="observation" and count==5):
        raise ValueError("Stage must be 1 through 6")
    if stage is not None and stage not in STAGES:
        raise ValueError("Stage must be 1 through 6")
    if purpose not in ("experiment","pilot","observation") or count != (1 if purpose=="pilot" else 5):
        raise ValueError("Main/observation requests require five trials; pilot requires one")
    plan_path, folders = run_requested(config,problem,[stage],count,purpose,output_root or ROOT/"results",backend_factory=backend_factory)
    folder = folders[0]
    return folder,json.loads((folder/"summary.json").read_text())

def report_markdown(stage, summary, results, purpose):
    def number(value):
        return "미측정/계산 불가" if value is None else "%.6f" % value
    def average(value):
        return "해당 결과 없음" if value is None else "평균 %.3f (최소 %.3f, 최대 %.3f)" % (value["mean"], value["min"], value["max"])
    title = "기본 동작 관찰 · 소통 형식 자율 선택" if stage is None else "%d단계 · %s" % (stage, STAGES[stage])
    lines = ["# " + title, "", "실행 구분: " + purpose,
             "", "상태: %s · 성공 %d회 / 계획 %d회 · 시도 %d회 · 과제 실행 %d회 · 인프라 오류 %d회" %
             ("완료" if summary["batch_complete"] else "미완료", summary["success_count"], summary["expected_trials"],
              summary["attempted_trials"], summary["completed_trials"], summary["infrastructure_errors"]), "",
             "| 핵심 지표 | 결과 |", "|---|---|",
             "| 과제 성공률·결과 품질 | 성공률 %s · 성공한 결과의 최적 점수 차이 %s |" % (number(summary["success_rate"]), average(summary["quality_gap_successes"])),
             "| 성공 1건당 총비용 추정(USD) | %s |" % number(summary["cost_per_success_estimate_usd"]),
             "| 전체 완료 시간(초) | 성공한 실행 %s · 모든 실행의 종료 시간 %s |" % (average(summary["completion_seconds_successes"]), average(summary["termination_seconds_all"])),
             "| 실제 통신량(bytes/회차) | %s |" % average(summary["communication_bytes"]),
             "| 통신 처리 비용 | 분리 측정한 로컬 처리 비용 합계 %s USD · 로컬 CPU 초/회차 %s |" % (number(summary["communication_processing_cost_estimate_usd"]), average(summary["communication_processing_cpu_seconds"])), "",
             "| 회차 | 상태 | 점수 | 최적해 차이 | 경과 시간(초) | 통신량(bytes) | 모델 비용 추정(USD) |",
             "|---|---|---|---|---|---|---|"]
    for i, result in enumerate(results, 1):
        evaluation = result.get("evaluation") or {}
        model = result["model_cost_estimate_usd"]
        lines.append("| %d | %s | %s | %s | %.2f | %d | %s |" % (
            i, result["status"], evaluation.get("score", "—"), result["quality_gap"], result["elapsed_seconds"],
            result["communication_bytes"], "미측정" if model is None else "%.6f" % model))
    lines += ["", "성공 1건당 총비용 추정(USD): " + str(summary["cost_per_success_estimate_usd"]),
              "", "관측 성공 비율에는 인프라·사용자 중단도 포함됩니다. 미실행·미확정 슬롯이 있으면 전체 비율은 계산하지 않습니다. 이 비율만으로 모델의 문제 해결 능력을 추정하지 않습니다.",
              "", "모델 비용만의 성공 1건당 추정(USD): " + str(summary["model_cost_per_success_estimate_usd"]),
              "", "통신 처리 비용: 로컬 변환·해석 CPU 시간과 설정된 CPU 단가로 측정. 모델 호출 안의 작업 추론과 메시지 생성 비용은 분리 측정 불가.",
              "", "`null`/`None`은 미측정 또는 계산 불가이며 0이 아닙니다. 금액은 API 단가 기반 추정이며 실제 구독 청구액이 아닙니다.",
              "", "통신량은 로컬 메시지 채널의 본문+공통 헤더 바이트입니다. Base64 로그 저장 크기, 모델 API 전송량, TLS/IP 오버헤드는 포함하지 않습니다."]
    if stage == 4:
        lines += ["", "4단계는 고정 의미 특성 %d개를 %d차원 float32 벡터와 손실 없는 메시지 참조 정수 영역으로 전달하는 방식입니다. 학습된 임베딩이나 모델 내부 잠재 상태 교환을 평가한 결과가 아닙니다." % (VECTOR_FEATURES, VECTOR_DIMENSIONS)]
    if stage == 6:
        lines += ["", "6단계는 고정 문법 위에서 두 Agent가 매회 기호 사전을 합의합니다. 언어 합의 과정도 시간·통신량·비용에 포함합니다."]
    if stage is None:
        lines += ["", "공통 실험 환경에서 메시지 형식을 지정하지 않고 매회 새 A/B 세션으로 5회 관찰합니다. Codex 제품의 기본 설정을 대표하지 않으며, 같은 문제 5회만으로 다른 작업의 성공률을 추정하지 않습니다.",
                  "", "모델·정보 분리·도구 제한·교대 순서·제출 규칙은 유지합니다. 공통 행동 외피와 입력은 JSON이므로 형식 선택에 영향을 줄 수 있습니다.",
                  "", "Agent 간 실제 대화와 제출(단계별 본실험 비교에서는 제외):", ""]
        lines += ["- [%d회차 대화 원문](trial-%02d/transcript.md)" % (i, i) for i in range(1, len(results)+1)]
    errors = ["- 회차 %d: %s" % (i, x["error"]) for i, x in enumerate(results, 1) if x.get("error")]
    if errors:
        lines += ["", "실패·중단 사유:", ""] + errors
    lines += ["", "## 모델 처리량과 대화 기록", "",
              "작업 메시지 송신 원문(bytes/회차): " + average(summary["task_sender_text_bytes"]), "",
              "작업 메시지 수신 텍스트(bytes/회차): " + average(summary["task_receiver_text_bytes"]), "",
              "모델 호출 합계: %d회. 전체 입력·출력·캐시 토큰은 회차별 결과에 별도 기록합니다." % summary["model_calls"], "",
              "각 회차의 관찰표에서 정보 공유·제안·수정·내용 정확성·완료 절차를 확인합니다. 자연어 내용 검수는 수동 검수가 완료될 때까지 미측정으로 표시합니다.", ""]
    lines += ["- %d회차: [대화](trial-%02d/transcript.md) · [관찰표](trial-%02d/observation.md) · [A](trial-%02d/Agent_A.md) · [B](trial-%02d/Agent_B.md)" % (i,i,i,i,i) for i in range(1,len(results)+1)]
    return "\n".join(lines) + "\n"
