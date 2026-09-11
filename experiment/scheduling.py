"""Frozen paired plans, atomic slot claims, isolated worktrees, explicit resume."""
import copy
import fcntl
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from pathlib import Path

from .artifacts import ROOT, digest, new_id, source_snapshot, utcnow, write_json, file_hashes, verify_seal
from .contracts import validate_config, OPERATIONAL_STATES, RECORD_VERSION
from .codex import AppServer
from .protocols import STAGES


def make_plan(config, problem, stages, count=5, jobs=1, purpose="experiment"):
    validate_config(config)
    if not stages or len(stages)!=len(set(stages)) or any(s not in STAGES and not (s is None and purpose=="observation") for s in stages):
        raise ValueError("Choose unique stages 1 through 6")
    if type(jobs) is not int or not 1 <= jobs <= len(stages):
        raise ValueError("jobs must be between one and the number of requested stages")
    if count != (1 if purpose=="pilot" else 5):
        raise ValueError("Exactly five planned attempts (one for pilot)")
    rng = random.Random(config["schedule_seed"])
    slots = []
    for number in range(1,count+1):
        order = list(stages); rng.shuffle(order)
        for stage in order:
            slots.append({"id":"stage%s-trial%02d" % (stage,number),"stage":stage,"trial":number,
                "first_speaker":config["first_speakers"][number-1],"block":number,"order":len(slots)})
    return {"version":RECORD_VERSION,"id":new_id("plan"),"created_at":utcnow(),"purpose":purpose,
        "config":copy.deepcopy(config),"problem":copy.deepcopy(problem),"config_hash":digest(config),"problem_hash":digest(problem),
        "stages":list(stages),"count":count,"jobs":jobs,"profile":{"jobs":jobs,"mode":"serial" if jobs==1 else "parallel"},
        "source_snapshot":source_snapshot(),"slots":slots}


@contextmanager
def state_lock(plan_path):
    with (Path(plan_path).parent/"state.lock").open("a") as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f,fcntl.LOCK_UN)


@contextmanager
def coordinator_lock(plan_path):
    with Path(plan_path).with_name("coordinator.lock").open("a") as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("This plan already has a running coordinator") from exc
        try:
            yield
        finally:
            fcntl.flock(f,fcntl.LOCK_UN)


def load_state(plan_path):
    return json.loads(Path(plan_path).with_name("state.json").read_text())


def update_state(plan_path, mutate):
    with state_lock(plan_path):
        state = load_state(plan_path)
        result = mutate(state)
        write_json(Path(plan_path).with_name("state.json"),state)
        return result


def claim_slot(plan_path, slot_id):
    def claim(state):
        if state["status"] != "running" or state["slots"][slot_id]["status"] != "not_started":
            return False
        state["slots"][slot_id].update(status="running",started_at=utcnow())
        return True
    return update_state(plan_path,claim)


def finish_slot(plan_path, slot_id, result):
    def finish(state):
        if state["slots"][slot_id]["status"] != "running":
            raise ValueError("Slot was not claimed or has already finished")
        state["slots"][slot_id].update(status=result["status"],finished_at=utcnow(),operational_status=result.get("operational_status","normal"))
        if result.get("operational_status") in OPERATIONAL_STATES or result["status"] in OPERATIONAL_STATES:
            state["status"] = "paused"
    update_state(plan_path,finish)


def checkpoint_worktrees(plan, plan_folder):
    """Use a private Git index; never commit/stage/revert the user's checkout or index."""
    root = ROOT
    original_head = subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    with tempfile.TemporaryDirectory(prefix="communication-index-") as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp)/"index"))
        subprocess.run(["git","read-tree","HEAD"],cwd=root,env=env,check=True,capture_output=True)
        subprocess.run(["git","add","-A","--","experiment","config","tests","scripts","lab.py","AGENTS.md","README.md","docs"],cwd=root,env=env,check=True,capture_output=True)
        tree = subprocess.check_output(["git","write-tree"],cwd=root,env=env,text=True).strip()
        commit = subprocess.check_output(["git","-c","user.name=Communication Lab","-c","user.email=lab@localhost",
            "commit-tree",tree,"-p",original_head,"-m","Frozen source for " + plan["id"]],cwd=root,env=env,text=True).strip()
    paths = {}
    for stage in plan["stages"]:
        path = root/".worktree"/plan["id"]/("stage-%s" % stage)
        if path.exists(): raise ValueError("Refusing to reuse a worktree")
        subprocess.run(["git","worktree","add","--detach",str(path),commit],cwd=root,check=True,capture_output=True,text=True)
        if source_snapshot(path) != plan["source_snapshot"]:
            raise ValueError("Worktree source does not match the frozen implementation")
        paths[str(stage)] = str(path)
    write_json(Path(plan_folder)/"worktrees.json",{"commit":commit,"original_head":original_head,"paths":paths})
    return paths


def run_worker(plan_path, slot, run_folder, worktree, cancel_event):
    command = [sys.executable,str(Path(worktree)/"lab.py"),"_run-slot",str(plan_path),slot["id"],str(run_folder)]
    proc = subprocess.Popen(command,cwd=worktree,start_new_session=True)
    interrupted = False
    while proc.poll() is None:
        if cancel_event.is_set() and not interrupted:
            # Worker propagates cancellation to its App Server; no model deadline.
            os.killpg(proc.pid,signal.SIGINT)
            interrupted = True
        time.sleep(.1)
    path = Path(run_folder)/("trial-%02d" % slot["trial"])/"result.json"
    if not path.exists():
        from .runner import failure_result
        return failure_result(slot["stage"],"unconfirmed","Worker exited without a final result (exit %s)" % proc.returncode)
    return json.loads(path.read_text())


def execute_plan(plan_path, folders, backend_factory=AppServer, worktrees=None, executor=None, cancel_event=None):
    """Dispatch a block at a time. After infrastructure failure, allocate no new slots."""
    from .runner import execute_trial, failure_result
    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text())
    cancel_event = cancel_event or threading.Event()
    worktrees = worktrees or {}
    start = time.monotonic()
    def perform(slot):
        key = str(slot["stage"])
        root = worktrees.get(key,ROOT)
        if source_snapshot(root) != plan["source_snapshot"]:
            return failure_result(slot["stage"],"infrastructure_error","Implementation changed after plan creation")
        if executor:
            return executor(slot,folders[key],cancel_event)
        if key in worktrees:
            return run_worker(plan_path,slot,folders[key],worktrees[key],cancel_event)
        return execute_trial(plan["config"],plan["problem"],slot["stage"],folders[key],slot["trial"],slot["first_speaker"],backend_factory,cancel_event)
    with ThreadPoolExecutor(max_workers=plan["jobs"]) as pool:
        active = {}
        try:
            for block in range(1,plan["count"]+1):
                pending = [s for s in plan["slots"] if s["block"]==block and load_state(plan_path)["slots"][s["id"]]["status"]=="not_started"]
                while pending or active:
                    while pending and len(active)<plan["jobs"] and not cancel_event.is_set() and load_state(plan_path)["status"]=="running":
                        slot = pending.pop(0)
                        if not claim_slot(plan_path,slot["id"]): continue
                        update_state(plan_path,lambda state:state["slots"][slot["id"]].update(queue_seconds=time.monotonic()-start))
                        print("%s · %s단계 %d/%d 시작 · 선발화 %s" % (plan["id"],slot["stage"],slot["trial"],plan["count"],slot["first_speaker"]),flush=True)
                        active[pool.submit(perform,slot)] = slot
                    if not active: break
                    done,_ = wait(active,timeout=.25,return_when=FIRST_COMPLETED)
                    for future in done:
                        slot = active.pop(future)
                        try: result = future.result()
                        except BaseException as exc:
                            result = failure_result(slot["stage"],"unconfirmed",type(exc).__name__+": "+str(exc))
                        target = Path(folders[str(slot["stage"])])/("trial-%02d" % slot["trial"])
                        if not (target/"result.json").exists():
                            target.mkdir(parents=True,exist_ok=True)
                            result["trial_number"] = slot["trial"]
                            write_json(target/"result.json",result)
                        finish_slot(plan_path,slot["id"],result)
                        print("%s단계 %d/%d: %s" % (slot["stage"],slot["trial"],plan["count"],result["status"]),flush=True)
                    if load_state(plan_path)["status"] != "running": pending.clear()
                if cancel_event.is_set() or load_state(plan_path)["status"] != "running": break
        except KeyboardInterrupt:
            cancel_event.set()
            update_state(plan_path,lambda state:state.update(status="paused"))
            for future,slot in active.items():
                try: result = future.result()
                except BaseException as exc: result = failure_result(slot["stage"],"unconfirmed",str(exc))
                target = Path(folders[str(slot["stage"])])/("trial-%02d" % slot["trial"])
                if not (target/"result.json").exists():
                    target.mkdir(parents=True,exist_ok=True)
                    result["trial_number"] = slot["trial"]
                    write_json(target/"result.json",result)
                finish_slot(plan_path,slot["id"],result)
    def end(state):
        state["status"] = "completed" if all(s["status"] not in ("not_started","running","unconfirmed") for s in state["slots"].values()) else "paused"
        state.setdefault("execution_segments",[]).append({"finished_at":utcnow(),"elapsed_seconds":time.monotonic()-start})
    update_state(plan_path,end)


def finalize_plan(plan_path, folders, worktrees=None):
    from .runner import finalize_run
    state = load_state(plan_path)
    for stage,folder in folders.items():
        if not (Path(folder)/"seal.json").exists():
            finalize_run(folder,{"plan_id":state["plan_id"],"slots":{k:v for k,v in state["slots"].items() if k.startswith("stage%s-" % stage)}})
    if worktrees:
        for stage,source in folders.items():
            source = Path(source)
            central = Path(plan_path).parent.parent.parent/"experiment"/source.name
            if central.exists(): raise ValueError("Central result already exists")
            shutil.copytree(source,central)
            if file_hashes(source)!=file_hashes(central): raise ValueError("Central copy differs from worktree result")
            folders[stage] = central
    update_state(plan_path,lambda state:state.update(runs={k:str(v) for k,v in folders.items()}))
    return folders


def run_requested(config, problem, stages, count=5, purpose="experiment", output_root=None, jobs=1, backend_factory=AppServer, use_worktrees=None):
    from .runner import initialize_run
    request_started = time.monotonic()
    output_root = Path(output_root or ROOT/"results").resolve()
    plan = make_plan(config,problem,stages,count,jobs,purpose)
    plan_folder = output_root/"plans"/plan["id"]
    plan_folder.mkdir(parents=True,exist_ok=False)
    plan_path = plan_folder/"plan.json"
    write_json(plan_path,plan)
    write_json(plan_folder/"state.json",{"plan_id":plan["id"],"plan_hash":digest(plan),"status":"preparing","runs":{},
        "slots":{s["id"]:{"status":"not_started"} for s in plan["slots"]}})
    use_worktrees = len(stages)>1 if use_worktrees is None else use_worktrees
    if jobs>1 and not use_worktrees and backend_factory is AppServer:
        raise ValueError("Live parallel trials require isolated worktree workers")
    prepared = time.monotonic()
    worktrees = checkpoint_worktrees(plan,plan_folder) if use_worktrees else {}
    folders = {}
    for stage in stages:
        root = Path(worktrees[str(stage)]) if worktrees else ROOT
        dest = root/"results" if worktrees else output_root
        folders[str(stage)] = initialize_run(config,problem,stage,count,purpose,dest,plan["id"],plan["profile"],root)
    update_state(plan_path,lambda state:state.update(status="running",runs={k:str(v) for k,v in folders.items()},preparation_seconds=time.monotonic()-prepared))
    with coordinator_lock(plan_path):
        execute_plan(plan_path,folders,backend_factory,worktrees)
        finalization_started = time.monotonic()
        folders = finalize_plan(plan_path,folders,worktrees)
        update_state(plan_path,lambda state:state.update(finalization_seconds=time.monotonic()-finalization_started,
            request_elapsed_seconds=time.monotonic()-request_started))
    return plan_path,[folders[str(stage)] for stage in stages]


def resume_plan(plan_path, backend_factory=AppServer):
    with coordinator_lock(plan_path):
        return _resume_plan(plan_path,backend_factory)


def _resume_plan(plan_path, backend_factory=AppServer):
    from .runner import codex_version
    request_started = time.monotonic()
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    state = load_state(plan_path)
    if state["plan_hash"] != digest(plan) or source_snapshot()!=plan["source_snapshot"]:
        raise ValueError("Plan/source changed; do not resume under different conditions")
    if state["status"] not in ("paused","completed") or not any(s["status"]=="not_started" for s in state["slots"].values()):
        raise ValueError("No explicitly resumable unstarted slots")
    worktree_record = plan_path.with_name("worktrees.json")
    worktrees = json.loads(worktree_record.read_text())["paths"] if worktree_record.exists() else {}
    folders = {}
    for stage,old in state["runs"].items():
        old = Path(old); verify_seal(old)
        manifest = json.loads((old/"manifest.json").read_text())
        if manifest["comparison_settings"]["codex_version"] != codex_version():
            raise ValueError("Codex version changed")
        if worktrees and source_snapshot(worktrees[stage]) != plan["source_snapshot"]:
            raise ValueError("Worktree source changed")
        parent = Path(worktrees[stage])/"results"/plan["purpose"] if worktrees else old.parent
        new = parent/new_id("resume-stage%s" % stage)
        shutil.copytree(old,new)
        (new/"seal.json").unlink()  # A new derivative run, never modify the previous sealed run.
        manifest.update(run_id=new.name,status="running",supersedes=str(old),parent_seal_hash=digest(file_hashes(old)))
        write_json(new/"manifest.json",manifest)
        folders[stage] = new
    update_state(plan_path,lambda s:s.update(status="running",runs={k:str(v) for k,v in folders.items()}))
    execute_plan(plan_path,folders,backend_factory,worktrees)
    folders = finalize_plan(plan_path,folders,worktrees)
    update_state(plan_path,lambda state:state.setdefault("resume_elapsed_seconds",[]).append(time.monotonic()-request_started))
    return folders


def worker_main(plan_path, slot_id, run_folder):
    from .runner import execute_trial
    plan = json.loads(Path(plan_path).read_text())
    if source_snapshot() != plan["source_snapshot"]:
        raise ValueError("Worker implementation differs from plan")
    state = load_state(plan_path)
    if state["plan_hash"] != digest(plan) or state["slots"][slot_id]["status"] != "running":
        raise ValueError("Worker slot is not reserved")
    slot = next(s for s in plan["slots"] if s["id"]==slot_id)
    if Path(run_folder).resolve() != Path(state["runs"][str(slot["stage"]) ]).resolve():
        raise ValueError("Worker output folder differs from the fixed plan")
    # A second worker for the same reservation cannot start another model call.
    claim = Path(plan_path).parent/(slot_id+".started")
    with claim.open("x") as f: f.write(utcnow())
    cancel = threading.Event()
    signal.signal(signal.SIGINT,lambda *_:cancel.set())
    signal.signal(signal.SIGTERM,lambda *_:cancel.set())
    result = execute_trial(plan["config"],plan["problem"],slot["stage"],run_folder,slot["trial"],slot["first_speaker"],cancel_event=cancel)
    return 0 if result["status"] not in OPERATIONAL_STATES else 1
