import argparse
import json
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .codex import AppServer
from .problem import load_problem, oracle, problem_diagnostics
from .protocols import STAGES, compact, instructions, transmit
from .artifacts import source_snapshot, verify_seal
from .scheduling import run_requested, resume_plan, worker_main
from .runner import ROOT, Recorder, Trial, base_prompt, digest, run_batch, schedule_from_action, utcnow, validate_config, write_json


def load_settings():
    config = json.loads((ROOT / "config/experiment.json").read_text(encoding="utf-8"))
    validate_config(config)
    problem = load_problem(ROOT / config["problem_file"])
    reference = json.loads((ROOT/"config/problem-reference.json").read_text())
    if reference["problem_hash"] != digest(problem):
        raise ValueError("Frozen confirmation problem changed")
    return config, problem


def implementation_fingerprint(config, problem):
    return digest({"config":config,"problem":problem,"sources":source_snapshot()})


def offline_check():
    config, problem = load_settings()
    expected = oracle(problem)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun == 0:
        return 1
    folder = ROOT / ".runtime"
    folder.mkdir(exist_ok=True)
    write_json(folder / "offline-check.json", {"checked_at": utcnow(), "passed": True,
               "tests": result.testsRun, "fingerprint": implementation_fingerprint(config, problem), "oracle": expected,
               "problem_diagnostics": problem_diagnostics(problem)})
    print("오프라인 점검 통과: %d개 테스트, 유효 시간표 %d개, 최적 점수 %d" % (result.testsRun, expected["feasible_count"], expected["optimal_score"]))
    print("모델 호출 없음. 실제 연결 검증: python3 lab.py verify-live")
    return 0


def verification_receipt(config, problem):
    path = ROOT / ".runtime/live-check.json"
    if not path.exists():
        return None
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("fingerprint") != implementation_fingerprint(config, problem):
        return {**receipt, "stale": True}
    return receipt


def show_status():
    config, problem = load_settings()
    reference = oracle(problem)
    receipt = verification_receipt(config, problem)
    offline_path = ROOT/".runtime/offline-check.json"
    offline = json.loads(offline_path.read_text()) if offline_path.exists() else None
    ready = bool(offline and offline.get("passed") and offline.get("fingerprint")==implementation_fingerprint(config,problem))
    print("오프라인 구현 검증: " + ("현재 소스 통과" if ready else "미검증 또는 소스 변경 — check 필요"))
    print("모델: %s / %s · 단계당 %d회 · 유효 시간표 %d개" % (config["model"], config["reasoning_effort"], config["repetitions"], reference["feasible_count"]))
    diagnosis = problem_diagnostics(problem)
    print("실험실 v%s · 문제 %s · 최적 점수 %d · 회의 간 상충 차이 %d" %
          (config["version"], problem["id"], reference["optimal_score"], diagnosis["coupling_gap"]))
    print("Codex CLI: " + (shutil.which("codex") or "설치 필요"))
    print("단계 | 소통 방식 | 로컬 구현 | 실제 연결 점검")
    for stage, name in STAGES.items():
        record = (receipt or {}).get("stages", {}).get(str(stage))
        label = "미검증"
        if receipt and receipt.get("stale"):
            label = "구현 변경 후 재검증 필요"
        elif record:
            label = "통과" if record.get("passed") else "실패: " + record.get("error", "unknown")
        print("%d | %s | %s | %s" % (stage, name, "검증 통과" if ready else "검증 필요", label))
    print("실행: python3 lab.py run <1~6> · 비교: python3 lab.py compare")
    return 0


def verify_live(stage=None):
    config, problem = load_settings()
    stages = [stage] if stage else list(STAGES)
    folder = ROOT / "results/verification" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    records = {}
    expected = {"M1": 1, "M2": 4, "M3": 10}
    for number in stages:
        print("%d단계 연결·전송·해석 점검 시작 (본실험 아님)" % number, flush=True)
        rec = Recorder(folder / ("stage-%d" % number))
        began = time.monotonic()
        try:
            with AppServer(config, rec.event) as backend:
                trial = Trial(backend, config, problem, number, rec)
                for actor in ("A", "B"):
                    trial.threads[actor] = backend.new_session(actor, base_prompt(actor, number))
                if number == 6:
                    if not trial.negotiate():
                        raise ValueError("Agent stopped during verification setup")
                trial.phase = "task"
                prompt = ("TRANSPORT VERIFICATION ONLY, NOT A SCHEDULING TRIAL. Send one proposal communicating M1 at slot 1, M2 at slot 4, M3 at slot 10. "
                          "Do not use private calendar facts or solve a scheduling task. action=send, empty schedule/language arrays. Use this protocol in payload: " + instructions(number, trial.language))
                sent = trial.ask("A", prompt)
                if sent["action"] != "send":
                    raise ValueError("Sender did not send a message")
                packet = transmit(number, sent["payload"], trial.language)
                trial.wire_record("A", packet.wire, packet.receiver_text, cpu=packet.cpu_seconds, wall=packet.wall_seconds, source=sent["payload"])
                received = trial.ask("B", "TRANSPORT VERIFICATION ONLY. Read the peer's message and return action=submit with exactly the three meeting-slot pairs it says. "
                                     "No task solving, no additional communication. Empty payload/language. Protocol: " + instructions(number, trial.language)
                                     + "\nPeer message:\n" + packet.receiver_text)
                if received["action"] != "submit" or schedule_from_action(received) != expected:
                    raise ValueError("Receiver did not reconstruct the transmitted schedule")
                records[str(number)] = {"passed": True, "elapsed_seconds": time.monotonic()-began,
                    "sessions": trial.threads, "confirmed_settings": backend.thread_settings,
                    "usage": {a: backend.usage.get(t) for a, t in trial.threads.items()},
                    "message_bytes": trial.payload_bytes+trial.envelope_bytes,
                    "language": trial.language}
                print("%d단계 통과: 새 세션 2개, 실제 전송 데이터에서 수신 결과 복원" % number, flush=True)
        except Exception as exc:
            records[str(number)] = {"passed": False, "error": str(exc), "elapsed_seconds": time.monotonic()-began}
            print("%d단계 실패: %s" % (number, exc), flush=True)
        write_json(rec.folder / "verification.json", records[str(number)])
    receipt = {"checked_at": utcnow(), "purpose": "transport_verification_not_experiment",
               "fingerprint": implementation_fingerprint(config, problem), "stages": records, "folder": str(folder)}
    old = verification_receipt(config, problem)
    if stage and old and not old.get("stale"):
        receipt["stages"] = {**old.get("stages", {}), **records}
    write_json(folder / "verification.json", receipt)
    (ROOT / ".runtime").mkdir(exist_ok=True)
    write_json(ROOT / ".runtime/live-check.json", receipt)
    print("검증 기록: " + str(folder), flush=True)
    return 0 if all(x["passed"] for x in records.values()) else 1


def compare():
    groups = {}
    root = ROOT / "results/experiment"
    if root.exists():
        paths = sorted(root.glob("*/manifest.json"))
        superseded = {json.loads(p.read_text()).get("supersedes") for p in paths}
        for path in paths:
            if str(path.parent.resolve()) in superseded: continue
            verify_seal(path.parent)
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if manifest.get("purpose") != "experiment":
                continue
            summary_path = path.parent / "summary.json"
            if not summary_path.exists():
                continue
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            groups.setdefault(manifest["comparison_group"], []).append((manifest, summary, path.parent))
    if not groups:
        print("본실험 결과가 없습니다. 준비 점검·예비 실행은 비교에 포함하지 않습니다.")
        return 0
    for group, entries in groups.items():
        print("\n동일 조건 그룹: " + group[:16])
        print("단계 | 상태 | 성공 | 품질 차이 평균 | 성공당 총비용 USD | 성공 완료시간 평균(초) | 통신량 평균(bytes) | 통신 CPU 평균(초)")
        def mean(data):
            return "미측정" if not data else "%.3f" % data["mean"]
        for manifest, summary, folder in entries:
            cost = summary["cost_per_success_estimate_usd"]
            print("%d %s | %s | %d/%d | %s | %s | %s | %s | %s" % (
                manifest["stage"], manifest["stage_name"], manifest["status"], summary["success_count"], summary["expected_trials"],
                mean(summary["quality_gap_successes"]), "미측정/계산불가" if cost is None else "%.6f" % cost,
                mean(summary["completion_seconds_successes"]), mean(summary["communication_bytes"]),
                mean(summary["communication_processing_cpu_seconds"])))
            print("  시간은 동일 실행 블록 여부를 함께 확인해야 합니다. 내용 정확도는 별도 검수 버전이 필요합니다.")
            print("  실행 블록: %s · 프로필: %s" % (manifest.get("plan_id"),compact(manifest["comparison_settings"].get("execution_profile"))))
            print("  시도 %d개 · 과제 실행 %d개 · 보고서: %s" % (summary.get("attempted_trials", summary["completed_trials"]), summary["completed_trials"], folder / "report.md"))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="여섯 방식의 자율 소통 실험실 v3. run/run-many는 실제 모델 본실험을 실행합니다.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="모델 호출 없이 단계별 준비 상태 확인")
    sub.add_parser("check", help="모델 호출 없는 데이터·프로토콜·실행기 테스트")
    sub.add_parser("observe", help="소통 형식을 지정하지 않고 독립 A/B 세션으로 일정 협업을 5회 관찰; 단계별 본실험과 별도")
    live = sub.add_parser("verify-live", help="실제 Luna high로 전송 경로 점검; 본실험과 별도")
    live.add_argument("--stage", type=int, choices=list(STAGES))
    for name, help_text in (("run", "요청한 단계만 독립 세션으로 5회 본실험"), ("pilot", "요청한 단계 1회 예비 실행; 본실험과 별도")):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("stage", type=int, choices=list(STAGES))
    sub.add_parser("compare", help="같은 설정의 기존 본실험 결과만 비교")
    review = sub.add_parser("review", help="종료된 실행의 대화·관찰표와 수동 검수를 재집계; 모델 호출 없음")
    review.add_argument("folder", type=Path)
    review.add_argument("--manual-inputs",type=Path,help="회차 이름 → 작성한 수동 검수 파일 경로의 JSON")
    review.add_argument("--reviewer",default="",help="검수자 식별자")
    review.add_argument("--recheck",type=Path,help="표본 재검수 근거 JSON")
    many = sub.add_parser("run-many",help="요청 단계만 동일 소스 worktree에서 각 5회 실행")
    many.add_argument("stages",nargs="+",type=int,choices=list(STAGES))
    many.add_argument("--jobs",type=int,default=1,help="동시 회차 수; 기본 1")
    resume = sub.add_parser("resume",help="고정 계획에서 아직 시작하지 않은 슬롯만 재개")
    resume.add_argument("plan",help="계획 ID 또는 plan.json 경로")
    worker = sub.add_parser("_run-slot",help=argparse.SUPPRESS)
    worker.add_argument("plan",type=Path); worker.add_argument("slot"); worker.add_argument("folder",type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            return show_status()
        if args.command == "check":
            return offline_check()
        if args.command == "compare":
            return compare()
        if args.command == "review":
            from .records import review_run
            manual = json.loads(args.manual_inputs.read_text()) if args.manual_inputs else None
            recheck = json.loads(args.recheck.read_text()) if args.recheck else None
            output,observations = review_run(args.folder,manual_inputs=manual,reviewer=args.reviewer,recheck=recheck)
            print("새 사후 검수 %d회차 · 내용 검수 대기 %d회차 · 모델 호출 없음 · %s" %
                  (len(observations), sum(x["content_review_status"] == "pending" for x in observations),output))
            return 0
        if args.command == "_run-slot":
            return worker_main(args.plan,args.slot,args.folder)
        if args.command == "resume":
            path = Path(args.plan)
            if not path.exists(): path = ROOT/"results/plans"/args.plan/"plan.json"
            folders = resume_plan(path)
            for folder in folders.values(): print("보고서: " + str(folder/"report.md"))
            return 0
        if args.command == "verify-live":
            return verify_live(args.stage)
        config, problem = load_settings()
        if args.command == "run-many":
            plan,folders = run_requested(config,problem,args.stages,jobs=args.jobs)
            print("실행 계획: " + str(plan))
            for folder in folders: print("보고서: " + str(folder/"report.md"))
            return 0 if all(json.loads((f/"summary.json").read_text())["batch_complete"] for f in folders) else 1
        if args.command == "observe":
            print("기본 동작 관찰 · %s / %s · 매회 새 A/B 세션, 동일 합성 일정, 5회" % (config["model"], config["reasoning_effort"]), flush=True)
            folder, summary = run_batch(config, problem, None, repetitions=5, purpose="observation")
            print("보고서: " + str(folder / "report.md"))
            print("회차별 대화 원문: " + str(folder / "trial-*/transcript.md"))
            return 0 if summary["batch_complete"] else 1
        purpose = "experiment" if args.command == "run" else "pilot"
        print("%d단계 %s · %s / %s · %s" % (args.stage, STAGES[args.stage], config["model"], config["reasoning_effort"], purpose), flush=True)
        folder, summary = run_batch(config, problem, args.stage,
                                    repetitions=5 if purpose == "experiment" else 1, purpose=purpose)
        print("보고서: " + str(folder / "report.md"))
        return 0 if summary["batch_complete"] else 1
    except KeyboardInterrupt:
        print("중단했습니다. 완료된 결과는 보존됩니다.", file=sys.stderr)
        return 130
    except Exception as exc:
        print("실행 오류: " + str(exc), file=sys.stderr)
        return 1
