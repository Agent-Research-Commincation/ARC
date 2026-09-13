"""Post-run observation and readable records. Never feeds judgments to agents."""
import base64
import copy
import hashlib
import itertools
import json
import struct
from pathlib import Path

from .problem import PEOPLE, MEETINGS, SLOTS, evaluate, feasible_scores, team_summary
from .protocols import KINDS, canonical_frame, compact, CODEC_VERSION
from .contracts import RECORD_VERSION, SEMANTIC_VERSION
from .artifacts import file_hashes, digest, new_id, utcnow, verify_seal, read_events, write_json
from .evaluation import check_claim, validate_claim, summary_counterfactual, analyze_trial, REVIEW_POLICY_VERSION


def save_json(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    tmp.replace(path)


def fence(text):
    marker = "```"
    while marker in text:
        marker += "`"
    return marker+"text\n"+text+"\n"+marker


def manual_annotations(folder, events, packets, input_path=None):
    """Validate source-anchored annotations; an AI annotation is not human review."""
    path = folder / "manual-review.json"
    event_path = folder / "events.jsonl"
    fingerprint = hashlib.sha256(event_path.read_bytes() if event_path.exists() else b"").hexdigest()
    template = {"version":1, "events_sha256":fingerprint, "reviewer":"", "entries":[
        {"message":p["sequence"], "status":"pending", "evidence":"", "kinds":[], "schedule":{},
         "requests":[], "questions":[], "references":[], "claims":[], "unjudgeable":[], "notes":""} for p in packets]}
    review = json.loads(Path(input_path).read_text(encoding="utf-8")) if input_path else template
    save_json(path,review)
    if review.get("events_sha256") != fingerprint:
        raise ValueError("Manual review belongs to different event data")
    if review.get("reviewer_kind", "unspecified") not in ("ai", "human", "unspecified"):
        raise ValueError("Reviewer kind must be ai, human or unspecified")
    entries = review.get("entries", [])
    if len(entries) != len(packets) or {e["message"] for e in entries} != {p["sequence"] for p in packets}:
        raise ValueError("Manual review must have exactly one entry per task message")
    by_number = {p["sequence"]:p for p in packets}
    for entry in entries:
        if entry["status"] not in ("pending", "complete"):
            raise ValueError("Review status must be pending or complete")
        if entry["status"] == "pending":
            continue
        text = by_number[entry["message"]]["receiver_text"]
        if not review.get("reviewer", "").strip() or not entry.get("evidence") or entry["evidence"] not in text:
            raise ValueError("Completed review needs a reviewer and verbatim message evidence")
        if not isinstance(entry["kinds"], list) or any(k not in KINDS for k in entry["kinds"]):
            raise ValueError("Invalid message kinds")
        canonical_frame({"kind":"inform", "facts":[], "schedule":entry["schedule"], "requests":entry["requests"]})
        canonical_frame({"kind":"inform","facts":[],"schedule":{},"requests":[],
                         "questions":entry.get("questions",[]),"references":entry.get("references",[])})
        for claim in entry["claims"]:
            if not claim.get("evidence") or claim["evidence"] not in text:
                raise ValueError("Each annotated claim needs a verbatim evidence excerpt")
            validate_claim(claim["type"], claim["value"])
        for excerpt in entry["unjudgeable"]:
            if not isinstance(excerpt, str) or not excerpt or excerpt not in text:
                raise ValueError("Unjudgeable expressions must quote the message")
    return {e["message"]:e for e in entries}


def observation_markdown(data):
    def show(v):
        return "미측정/검수 대기" if v is None else str(v)
    lines = ["# 회차별 소통 관찰", "", "[대화](transcript.md) · [A 입력·응답](Agent_A.md) · [B 입력·응답](Agent_B.md) · [관찰 JSON](observation.json)", "",
             "실험 종료 후 작성한 관찰입니다. 필요한 정보의 생략을 오류로 세지 않습니다. 상대의 내부 추론이나 독립 검증 여부는 추측하지 않습니다.", "",
             "| 항목 | 관찰 |", "|---|---|",
             "| 내용 검수 | %s · %d/%d개 메시지 |" % (data["content_review_status"], data["reviewed_messages"],data["task_messages"]),
             "| 맞는 주장 / 틀린 주장 | %s / %s |" % (show(data["correct_claims"]),show(data["incorrect_claims"])),
             "| 의미 규약 미정으로 판정 보류한 주장 | %s |" % show(data["undetermined_claims"]),
             "| 판정 불가능한 표현 | %s |" % show(data["unjudgeable_expressions"]),
             "| 사후 평가 정책 | %s |" % data["review_policy_version"],
             "| 주석 검수자 유형 | %s |" % data.get("annotation_reviewer_kind", "구조화 자동 평가"),
             "| 코덱 보존 오류 | %d |" % data["codec_errors"],
             "| 최초 제안자 | %s |" % show(data["first_proposer"]),
             "| 이전 제안과 배치가 달라진 제안 메시지 | %s |" % show(data["changed_proposal_messages"]),
             "| 명시적 수정 / 수락 표현 메시지 | %s / %s |" % (data["explicit_revisions"],show(data["accept_messages"])),
             "| 최종 제출 완료 | %s |" % compact(data["completion"]), "",
             "부분 검수의 주장 수는 검수한 메시지만의 집계입니다. 정확한 주장이 많다는 이유만으로 더 효율적이라고 평가하지 않습니다.", "",
             "## 정보 공유", "", "개인 원자료 72개는 해당 Agent 소유 정보의 전체 크기입니다. 아래는 실제로 명시한 서로 다른 항목 수이며 필수 전송량이 아닙니다.", ""]
    for actor, style in data["information_sharing"].items():
        lines.append("- Agent %s: 개인 원자료 항목 %s개, 팀 요약 주장 %s개." % (actor,show(style["unique_own_raw_claims"]),show(style["summary_claims"])))
    lines += ["", "## 메시지별 과정", "", "| 메시지 | 방향 | 종류 | 요청 대상 | 사실 / 요약 / 사유 | 제안 평가 |", "|---|---|---|---|---|---|"]
    for row in data["messages"]:
        counts = [sum(c["type"] == kind for c in row["claims"]) for kind in ("fact","summary","reason")]
        lines.append("| %d | %s → %s | %s | %s | %s | %s |" %
                     (row["message"],row["sender"],row["receiver"],", ".join(row["kinds"]) or "검수 대기/분류 없음",
                      ", ".join(map(str,row["requests"])) or "—", " / ".join(map(str,counts)) if row["review_status"]=="complete" else "미측정",
                      compact(row["proposal_quality"]) if row["proposal_quality"] else "—"))
    lines += ["", "## 내용 오류와 영향", "",
              "영향은 해당 주장 하나만 사실이라고 가정한 사후 계산입니다. Agent가 실제로 그 주장을 믿었다는 판정은 아닙니다.", ""]
    for row in data["messages"]:
        for claim in row["claims"]:
            if claim["correct"] is False:
                lines += ["- 메시지 %d · %s: `%s` · 입력 기준 `%s` · 영향 `%s`" %
                          (row["message"],row["sender"],compact(claim["value"]),compact(claim["expected"]),compact(claim["impact"]))]
                if claim.get("evidence"):
                    lines += ["", fence(claim["evidence"])]
        if row.get("notes"):
            lines += ["", "메시지 %d 검수 메모:" % row["message"], "", fence(row["notes"])]
    lines += ["", "## 판정 보류와 모호한 표현", ""]
    for row in data["messages"]:
        for claim in row["claims"]:
            if claim["correct"] is None:
                lines += ["- 메시지 %d: `%s` · 후보 유효성 `%s` · 원자료 선호 산술합 `%s` · 산술 일치 `%s`. 당시 불가능 후보 점수의 의미가 명시되지 않아 맞음·틀림 집계에서 제외." %
                          (row["message"],compact(claim["value"]),claim.get("candidate_valid"),claim.get("arithmetic_sum"),claim.get("arithmetic_matches"))]
        for excerpt in row["unjudgeable"]:
            lines += ["- 메시지 %d: 수치·의미 기준을 확정할 수 없는 표현." % row["message"], "", fence(excerpt)]
    if data["content_review_scope"] == "source-anchored annotations":
        lines += ["", "[원문 근거 주석](manual-review.json)에 검수자 유형과 범위를 기록합니다. AI 검수 완료는 사람의 독립 검수 완료를 뜻하지 않습니다. pending 메시지를 오류 0건으로 판정하지 않습니다."]
    return "\n".join(lines)+"\n"


def write_transcripts(folder):
    folder = Path(folder)
    event_path = folder / "events.jsonl"
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()] if event_path.exists() else []
    result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    lines = ["# 회차 대화 원문", "", "[관찰표](observation.md) · [결과](result.json) · [원본 이벤트](events.jsonl)", "",
             "실제 전송 메시지와 제어 행동입니다. 시각은 원본 UTC이며 모델의 내부 추론은 포함하지 않습니다.", ""]
    for e in events:
        p = e.get("params", {})
        if e["method"] == "experiment/packet":
            lines += ["## 메시지 %d · %s → %s" % (p["sequence"],p["sender"],p["receiver"]), "",
                      "%s · %s · 본문 %d B + 헤더 %d B" % (e["recorded_at"],p["phase"],p["payload_length"],p["header_bytes"]), ""]
            if p.get("sender_source") is not None and p["sender_source"] != p["receiver_text"]:
                lines += ["송신 원문:", "", fence(p["sender_source"]), "", "수신 텍스트:", ""]
            lines += [fence(p["receiver_text"]), ""]
        elif e["method"] == "experiment/action":
            lines += ["## Agent %s · %s" % (p["actor"],p["action"]["action"]), "", fence(compact(p["action"])), ""]
        elif e["method"] in ("experiment/rejected","experiment/submissions_invalidated","experiment/applied","experiment/request_interrupted","experiment/response_received"):
            lines += ["## 실행기 기록 · " + e["method"].split("/")[-1], "", fence(compact(p)), ""]
    (folder / "transcript.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    for actor in ("A","B"):
        lines = ["# Agent %s 입력·응답" % actor,"", "[대화](transcript.md) · [관찰표](observation.md)", "",
                 "세션: " + str(result.get("sessions",{}).get(actor,"생성 기록 없음")), "",
                 "실행기가 제공한 지침·입력과 모델 응답, 거절 기록입니다. 내부 추론은 포함하지 않습니다.", ""]
        for e in events:
            p = e.get("params", {})
            if p.get("actor") != actor or e["method"] not in ("experiment/instructions","experiment/input","experiment/action","experiment/rejected","experiment/response_received","experiment/applied","experiment/request_interrupted"):
                continue
            text = p["text"] if "text" in p else json.dumps(p.get("action",p),ensure_ascii=False,indent=2)
            lines += ["## %s · %s" % (e["recorded_at"],e["method"].split("/")[-1]), "", fence(text), ""]
        (folder / ("Agent_%s.md" % actor)).write_text("\n".join(lines)+"\n", encoding="utf-8")
    return folder



def write_trial_records(folder, problem, stage, output, manual_input=None):
    """Review into a NEW directory. The source trial is never modified."""
    import shutil
    folder, output = Path(folder).resolve(), Path(output).resolve()
    if output == folder or folder in output.parents or output.exists():
        raise ValueError("Review output must be a new directory outside the source trial")
    output.mkdir(parents=True)
    for name in ("events.jsonl","result.json","language.json"):
        if (folder/name).exists(): shutil.copy2(folder/name,output/name)
    events = read_events(folder)
    result = json.loads((folder/"result.json").read_text())
    language = json.loads((folder/"language.json").read_text()) if (folder/"language.json").exists() else None
    packets = [e["params"] for e in events if e["method"]=="experiment/packet" and e["params"]["phase"]=="task"]
    manual = manual_annotations(output,events,packets,manual_input) if stage in (None,1) else {}
    data = analyze_trial(problem,stage,events,result,language,manual)
    if stage in (None,1):
        annotation = json.loads((output/"manual-review.json").read_text(encoding="utf-8"))
        data["annotation_reviewer_kind"] = annotation.get("reviewer_kind", "unspecified")
        data["annotation_reviewer"] = annotation.get("reviewer", "")
    save_json(output/"observation.json",data)
    (output/"observation.md").write_text(observation_markdown(data),encoding="utf-8")
    write_transcripts(output)
    return data


def review_run(folder, output_root=None, manual_inputs=None, reviewer="", recheck=None):
    folder = Path(folder).resolve()
    verify_seal(folder)
    manifest = json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] == "running" or manifest["runner_version"] != RECORD_VERSION:
        raise ValueError("Only terminated v3 runs can be reviewed")
    if manifest["comparison_settings"]["codec_version"] != CODEC_VERSION:
        raise ValueError("Use the matching codec version to review this run")
    before = file_hashes(folder)
    review_id = new_id("review")
    output_root = Path(output_root or folder.parent.parent/"reviews")
    output = output_root/manifest["run_id"]/review_id
    output.mkdir(parents=True,exist_ok=False)
    manual_inputs = manual_inputs or {}
    trial_names = {p.parent.name for p in folder.glob("trial-*/result.json")}
    if set(manual_inputs)-trial_names:
        raise ValueError("Manual review references an unknown trial")
    if recheck is not None:
        if not isinstance(recheck,dict) or recheck.get("status") not in ("pending","complete"):
            raise ValueError("Invalid sample recheck status")
        if recheck["status"]=="complete" and (not recheck.get("reviewer") or not recheck.get("entries")):
            raise ValueError("Completed recheck requires reviewer and explicit samples")
        for entry in recheck.get("entries",[]):
            if entry.get("trial") not in trial_names or type(entry.get("message")) is not int or not entry.get("evidence"):
                raise ValueError("Recheck samples require trial, message ID and evidence")
            messages = [e["params"] for e in read_events(folder/entry["trial"]) if e["method"]=="experiment/packet"]
            if not any(p["sequence"]==entry["message"] and entry["evidence"] in p["receiver_text"] for p in messages):
                raise ValueError("Recheck evidence not found in source message")
    rows = []
    try:
        for path in sorted(folder.glob("trial-*/result.json")):
            rows.append(write_trial_records(path.parent,manifest["comparison_settings"]["problem"],manifest["stage"],
                        output/path.parent.name,manual_inputs.get(path.parent.name)))
        # Archive the evaluator sources as well as their hashes for later replay.
        import shutil
        code_output = output/"evaluation-source"/"experiment"
        code_output.mkdir(parents=True)
        for code in Path(__file__).parent.glob("*.py"):
            shutil.copy2(code,code_output/code.name)
        review_manifest = {"version":RECORD_VERSION,"review_id":review_id,"source_run":str(folder),
            "source_files":before,"source_hash":digest(before),"created_at":utcnow(),"reviewer":reviewer,
            "review_policy_version":REVIEW_POLICY_VERSION,
            "evaluation_source_files":file_hashes(output/"evaluation-source"),
            "semantic_version":SEMANTIC_VERSION,"codec_version":CODEC_VERSION,
            "evaluation_code_hashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(__file__).with_name("evaluation.py"),Path(__file__).with_name("protocols.py"),Path(__file__).with_name("contracts.py"),Path(__file__).with_name("problem.py"))},
            "manual_input_hashes":{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in manual_inputs.items()},
            "sample_recheck":recheck or {"status":"pending","reviewer":None,"entries":[]},
            "status":"pending" if any(r["content_review_status"]=="pending" for r in rows) else "complete"}
        write_json(output/"manifest.json",review_manifest)
        write_json(output/"summary.json",{"trials":len(rows),"pending":sum(r["content_review_status"]=="pending" for r in rows),
            "review_policy_version":REVIEW_POLICY_VERSION,
            "correct_claims":sum(r["correct_claims"] or 0 for r in rows) if all(r["correct_claims"] is not None for r in rows) else None,
            "incorrect_claims":sum(r["incorrect_claims"] or 0 for r in rows) if all(r["incorrect_claims"] is not None for r in rows) else None,
            "undetermined_claims":sum(r["undetermined_claims"] or 0 for r in rows) if all(r["undetermined_claims"] is not None for r in rows) else None})
        if file_hashes(folder)!=before: raise ValueError("Review changed the source run")
        from .artifacts import seal_run
        seal_run(output)
    except BaseException:
        # Keep an explicit failed-review receipt; source data and older reviews remain untouched.
        write_json(output/"review-error.json",{"status":"incomplete","created_at":utcnow()})
        raise
    return output, rows
