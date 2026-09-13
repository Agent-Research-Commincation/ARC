#!/usr/bin/env python3
"""Read-only aggregation of explicitly selected, sealed experiment/review records.

Usage: python3 -B aggregate.py --collection collection.json --output NEWDIR
No experiment modules are imported and no model or network calls are made.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(text):
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON: " + x)))


def read(path):
    return decode(Path(path).read_text(encoding="utf-8"))


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    # The experiment's seals use insertion order, not sort_keys=True.
    return hashlib.sha256(compact(value).encode()).hexdigest()


def hashes(folder):
    result = {}
    for path in sorted(folder.rglob("*")):
        require(not path.is_symlink(), "Symlink in sealed record: " + str(path))
        if path.is_file():
            result[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verified(folder, kind):
    require(folder.is_dir(), "Missing " + kind + ": " + str(folder))
    manifest = read(folder / "manifest.json")
    allowed = {"completed", "incomplete", "interrupted", "cancelled"} if kind == "source" else {"complete", "pending"}
    require(manifest.get("status") in allowed, "Refusing nonterminated " + kind + ": " + str(folder))
    require(not (folder / "review-error.json").exists(), "Failed review cannot be aggregated: " + str(folder))
    seal = read(folder / "seal.json")
    version = manifest.get("runner_version") if kind == "source" else manifest.get("version")
    require(seal.get("version") == version, "Seal version mismatch: " + str(folder))
    all_hashes = hashes(folder)
    expected = dict(all_hashes)
    expected.pop("seal.json")
    require(expected == seal.get("files"), "Seal mismatch: " + str(folder))
    return manifest, all_hashes


def resolve(base, value, name):
    require(isinstance(value, str) and bool(value), "Explicit " + name + " path is required")
    path = Path(value)
    return (path if path.is_absolute() else base / path).resolve()


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def complete_sum(values):
    return sum(values) if values and all(numeric(v) for v in values) else None


def stats(values):
    known = [v for v in values if numeric(v)]
    return {"expected_count": len(values), "measured_count": len(known),
            "missing_count": len(values) - len(known),
            "total": complete_sum(values),
            "mean": statistics.mean(known) if known else None,
            "median": statistics.median(known) if known else None,
            "min": min(known) if known else None, "max": max(known) if known else None,
            "scope": "Mean/median/range use measured values only; total requires every value."}


TOKEN_FIELDS = {"input_tokens": "inputTokens", "output_tokens": "outputTokens",
                "cached_input_tokens": "cachedInputTokens", "cache_write_input_tokens": "cacheWriteInputTokens",
                "reasoning_output_tokens": "reasoningOutputTokens", "total_tokens": "totalTokens"}
METRICS = ["score", "quality_gap", "elapsed_seconds", "task_elapsed_seconds", "runtime_initialization_seconds",
           "runtime_cleanup_seconds", "record_render_seconds", "message_count", "task_message_count",
           "language_message_count", "runner_turns", "payload_bytes", "envelope_bytes", "communication_bytes",
           "task_sender_text_bytes", "task_receiver_text_bytes", "model_cost_estimate_usd", "total_cost_estimate_usd",
           "communication_processing_cost_estimate_usd", "protocol_cpu_seconds", "protocol_wall_seconds",
           "runner_cpu_seconds", "codex_process_cpu_seconds", "framing_cpu_seconds", "framing_wall_seconds",
           "encoding_cpu_seconds", "decoding_cpu_seconds", "encoding_wall_seconds", "decoding_wall_seconds",
           "language_setup_seconds", "protocol_errors", "correct_claims", "incorrect_claims", "undetermined_claims",
           "unjudgeable_expressions", "codec_errors", "reviewed_messages", "pending_messages",
           "first_candidate_score", "first_candidate_gap", "changed_proposal_messages", "explicit_revisions"] + list(TOKEN_FIELDS)


def candidate_quality(problem, schedule, optimal):
    meetings = {m["id"]: m for m in problem["meetings"]}
    require(all(m.get("duration_slots") == 1 for m in meetings.values()), "First-candidate evaluator supports one-slot meetings only")
    if set(schedule) != set(meetings):
        return None
    violations = []
    nslots = len(problem["slots"])
    for meeting, slot in schedule.items():
        if type(slot) is not int or not 0 <= slot < nslots:
            violations.append("slot:" + meeting)
    if violations:
        return {"valid": False, "score": None, "gap": None, "violations": violations}
    for meeting, slot in schedule.items():
        for person in meetings[meeting]["attendees"]:
            if not problem["people"][person]["availability"][slot]:
                violations.append("unavailable:" + meeting + ":" + person)
    for index, a in enumerate(meetings):
        for b in list(meetings)[index + 1:]:
            if schedule[a] == schedule[b] and set(meetings[a]["attendees"]) & set(meetings[b]["attendees"]):
                violations.append("overlap:" + a + ":" + b)
    for a, b in problem.get("precedence", []):
        if schedule[a] >= schedule[b]:
            violations.append("precedence:" + a + ":" + b)
    value = sum(problem["people"][p]["preferences"][schedule[m]] for m in meetings for p in meetings[m]["attendees"])
    return {"valid": not violations, "score": value if not violations else None,
            "gap": optimal - value if not violations and numeric(optimal) else None, "violations": violations}


def event_summary(path):
    sessions, packets, turns = [], [], 0
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                event = decode(line)
                method = event.get("method")
                if method == "experiment/session":
                    sessions.append(event["params"])
                elif method == "experiment/packet":
                    packets.append(event["params"])
                elif method == "experiment/input":
                    turns += 1
    return sessions, packets, turns


def trial_row(manifest, source, review, number, result, issues):
    row = {key: None for key in METRICS}
    row.update(stage=manifest["stage"], run_id=manifest["run_id"], trial=number,
               expected_trials=manifest["expected_trials"], recorded=result is not None,
               status="not_started", operational_status=None, success=None, optimal=None,
               content_review_status="not_started", content_review_scope=None,
               content_metrics_complete=False, first_candidate=None, first_candidate_valid=None,
               proposal_changed=None, explicitly_revised=None, sessions={}, session_evidence=[], error=None)
    if result is None:
        return row
    trial = "trial-%02d" % number
    require(result.get("trial_number") == number and result.get("stage") == manifest["stage"], "Trial identity mismatch: " + str(source / trial))
    require(result.get("status") in {"success", "failed", "stopped", "cancelled", "infrastructure_error", "unconfirmed"}, "Nonterminal trial: " + str(source / trial))
    observation = read(review / trial / "observation.json")
    sessions, packets, turns = event_summary(source / trial / "events.jsonl")
    for name in ("result.json", "events.jsonl", "language.json"):
        original, copied = source / trial / name, review / trial / name
        if original.exists():
            require(copied.exists() and original.read_bytes() == copied.read_bytes(), "Review/source trial mismatch: " + str(copied))
    row.update({key: result.get(key) for key in METRICS if key in result})
    row.update(status=result["status"], success=result.get("success"), error=result.get("error"),
               operational_status=result.get("operational_status"), first_speaker=result.get("first_speaker"),
               sessions=result.get("sessions", {}), session_evidence=sessions, runner_turns=result.get("actions"),
               score=(result.get("evaluation") or {}).get("score"), optimal_score=result.get("optimal_score"),
               task_message_count=sum(p.get("phase") == "task" for p in packets),
               language_message_count=sum(p.get("phase") == "language_setup" for p in packets),
               codec_task_timing=result.get("codec_task_timing"), protocol_error_counts=result.get("protocol_error_counts"),
               source_trial=str(source / trial), review_trial=str(review / trial))
    row["optimal"] = (row["score"] == row["optimal_score"]) if row["success"] and numeric(row["score"]) and numeric(row["optimal_score"]) else (False if row["success"] is False else None)
    usage = result.get("usage") or {}
    row["usage_by_agent"] = usage
    row["language_setup_usage"] = result.get("language_setup_usage")
    for key in ("encoding_cpu_seconds", "decoding_cpu_seconds", "encoding_wall_seconds", "decoding_wall_seconds"):
        row[key] = (result.get("codec_task_timing") or {}).get(key)
    for label, key in TOKEN_FIELDS.items():
        row[label] = complete_sum([(usage.get(actor) or {}).get(key) for actor in ("A", "B")])
    status = observation.get("content_review_status")
    complete = status == "complete"
    row.update(content_review_status=status, content_review_scope=observation.get("content_review_scope"),
               content_metrics_complete=complete, reviewed_messages=observation.get("reviewed_messages"),
               annotation_reviewer_kind=observation.get("annotation_reviewer_kind"),
               review_policy_version=observation.get("review_policy_version"),
               information_sharing=observation.get("information_sharing"),
               reviewed_claim_counts={k: observation.get(k) for k in ("correct_claims", "incorrect_claims", "undetermined_claims")},
               claim_counts_by_type=observation.get("claim_counts_by_type"),
               codec_errors=observation.get("codec_errors"), explicit_revisions=observation.get("explicit_revisions"))
    if numeric(observation.get("task_messages")) and numeric(row["reviewed_messages"]):
        row["pending_messages"] = observation["task_messages"] - row["reviewed_messages"]
    for key in ("correct_claims", "incorrect_claims", "undetermined_claims", "unjudgeable_expressions", "changed_proposal_messages"):
        row[key] = observation.get(key) if complete else None
    row["explicitly_revised"] = row["explicit_revisions"] > 0 if numeric(row["explicit_revisions"]) else None
    row["proposal_changed"] = row["changed_proposal_messages"] > 0 if numeric(row["changed_proposal_messages"]) else None
    if complete:
        meeting_ids = {m["id"] for m in manifest["comparison_settings"]["problem"]["meetings"]}
        for message in observation.get("messages", []):
            schedule = message.get("schedule") or {}
            if set(schedule) == meeting_ids:
                quality = candidate_quality(manifest["comparison_settings"]["problem"], schedule, row["optimal_score"])
                row["first_candidate"] = {"message": message.get("message"), "sender": message.get("sender"), "kinds": message.get("kinds"), "schedule": schedule, "quality": quality}
                row.update(first_candidate_valid=quality["valid"], first_candidate_score=quality["score"], first_candidate_gap=quality["gap"])
                break
    location = {"stage": row["stage"], "trial": number}
    if turns != row["runner_turns"]:
        issues.append({**location, "issue": "runner_turn_count_mismatch", "events": turns, "result": row["runner_turns"]})
    for key, actual in (("message_count", len(packets)), ("payload_bytes", sum(p["payload_length"] for p in packets)),
                        ("envelope_bytes", sum(p["header_bytes"] for p in packets))):
        if actual != row[key]:
            issues.append({**location, "issue": key + "_mismatch", "events": actual, "result": row[key]})
    if complete_sum([row["payload_bytes"], row["envelope_bytes"]]) != row["communication_bytes"]:
        issues.append({**location, "issue": "communication_byte_total_mismatch"})
    by_actor = {s.get("agent"): s.get("thread_id") for s in sessions}
    if by_actor != row["sessions"] or len(sessions) != len(by_actor):
        issues.append({**location, "issue": "session_result_event_mismatch"})
    if row["operational_status"] == "normal" and set(by_actor) != {"A", "B"}:
        issues.append({**location, "issue": "normal_trial_missing_two_sessions"})
    config = manifest["comparison_settings"]["config"]
    for session in sessions:
        if session.get("model") != config["model"] or session.get("reasoningEffort") != config["reasoning_effort"]:
            issues.append({**location, "issue": "model_or_effort_mismatch", "session": session})
        if session.get("instructionSources") != []:
            issues.append({**location, "issue": "unexpected_instruction_sources", "session": session})
    return row


def summarize(rows, manifest, label):
    expected = manifest["expected_trials"]
    recorded = [r for r in rows if r["recorded"]]
    confirmed = len(recorded) == expected and all(r["status"] != "unconfirmed" for r in recorded)
    success = sum(r["success"] is True for r in rows)
    optimal = sum(r["optimal"] is True for r in rows)
    metrics = {key: stats([r.get(key) for r in rows]) for key in METRICS}
    model_total = metrics["model_cost_estimate_usd"]["total"]
    total = metrics["total_cost_estimate_usd"]["total"]
    return {"stage": manifest["stage"], "label": label, "run_id": manifest["run_id"],
            "expected_trials": expected, "recorded_trials": len(recorded), "not_started_trials": expected - len(recorded),
            "manifest_status": manifest["status"], "batch_confirmed": confirmed,
            "status_counts": dict(Counter(r["status"] for r in rows)), "success_count": success,
            "optimal_count": optimal, "success_rate": success / expected if confirmed else None,
            "optimal_rate": optimal / expected if confirmed else None,
            "optimal_rate_among_successes": optimal / success if confirmed and success else None,
            "content_review_counts": dict(Counter(r["content_review_status"] for r in rows)),
            "proposal_changed_trials": sum(r["proposal_changed"] is True for r in rows),
            "proposal_changed_measured_trials": sum(r["proposal_changed"] is not None for r in rows),
            "explicitly_revised_trials": sum(r["explicitly_revised"] is True for r in rows),
            "model_cost_per_success_estimate_usd": model_total / success if confirmed and success and model_total is not None else None,
            "total_cost_per_success_estimate_usd": total / success if confirmed and success and total is not None else None,
            "metrics": metrics}


def display(value, digits=3):
    return "미측정" if value is None else (format(value, ".%df" % digits) if isinstance(value, float) else str(value))


def markdown(plan_id, summaries, integrity):
    lines = ["# 본실험 사후 비교", "", "계획: " + plan_id, "", "| 단계 | 성공/계획 | 최적/계획 | 점수 평균 | 종료 시간 평균(초) | 메시지 평균 | 전송량 평균(B) | 모델 추정비용/성공(USD) | 내용 검수 |", "|---|---|---|---|---|---|---|---|---|"]
    for stage in summaries:
        m = stage["metrics"]
        label = str(stage["label"]).replace("|", "\\|").replace("\n", " ")
        lines.append("| %s | %s/%s | %s/%s | %s | %s | %s | %s | %s | %s |" % (
            label, stage["success_count"], stage["expected_trials"], stage["optimal_count"], stage["expected_trials"],
            display(m["score"]["mean"]), display(m["elapsed_seconds"]["mean"]), display(m["message_count"]["mean"]),
            display(m["communication_bytes"]["mean"]), display(stage["model_cost_per_success_estimate_usd"], 8), compact(stage["content_review_counts"])))
    lines += ["", "- 표는 collection의 단계 순서이며 오류 수를 이용한 정확도 순위가 아닙니다.",
              "- 평균은 측정된 회차만 사용합니다. 각 지표의 measured_count/missing_count는 stage_summary.json에 있습니다.",
              "- 성공당 비용은 실패 회차까지 포함합니다. 모델 비용은 API 단가 기반 추정이고 실제 구독 청구액이 아닙니다. 총비용 미측정은 null입니다.",
              "- 입력 토큰에 캐시 입력이, 출력 토큰에 추론 출력이 포함되므로 중복 합산하지 않습니다.",
              "- 실행기 턴은 experiment/input 수입니다. 서비스 내부 요청 수가 아닙니다.",
              "- 통신량은 실제 전달 본문+헤더이며 모델 API 인터넷 트래픽은 제외합니다.",
              "- 내용 검수가 pending인 회차의 전체 내용 오류·보류 및 첫 후보 지표는 null입니다. 부분 검수 값은 reviewed_claim_counts에만 남깁니다.",
              "- 첫 후보는 완전 검수된 대화에 처음 등장하는 전체 회의 배치입니다. 불가능한 후보의 점수는 null입니다.",
              "- 시간·CPU는 결과에 기록된 범위를 따릅니다. 병렬 회차의 시간 합계는 전체 작업의 벽시계 시간이 아닙니다.",
              "", "무결성: " + ("통과" if integrity["valid"] else "불일치 확인 필요"),
              "세션: 기대 %s개, 실제 기록 %s개, 고유 %s개, 중복 ID %s개." % (
                  integrity["expected_sessions"], integrity["actual_session_records"], integrity["unique_sessions"], len(integrity["duplicate_sessions"])), ""]
    return "\n".join(lines)


def aggregate(collection_path, output):
    collection_path = Path(collection_path).resolve()
    if collection_path.is_dir():
        collection_path /= "collection.json"
    collection_bytes = collection_path.read_bytes()
    collection = decode(collection_bytes.decode("utf-8"))
    require(isinstance(collection.get("plan_id"), str) and collection["plan_id"], "Missing plan_id")
    require(isinstance(collection.get("records"), list) and collection["records"], "No collection records")
    output = Path(output).resolve()
    require(not output.exists(), "Output must be a new directory")
    records, settings, seen_stages, initial_hashes = [], None, set(), {}
    for record in collection["records"]:
        stage = record.get("stage")
        require(type(stage) is int and stage not in seen_stages, "Duplicate or invalid stage")
        seen_stages.add(stage)
        source = resolve(collection_path.parent, record.get("source"), "source")
        review = resolve(collection_path.parent, record.get("review"), "review")
        readable = resolve(collection_path.parent, record.get("readable"), "readable") if record.get("readable") is not None else None
        for folder in (source, review, readable):
            if folder is not None:
                require(output != folder and folder not in output.parents, "Output cannot alter input tree")
        require(source != review, "Source and review must be separate")
        m, sh = verified(source, "source")
        rm, rh = verified(review, "review")
        require(m.get("plan_id") == collection["plan_id"] and m.get("stage") == stage and m.get("purpose") == "experiment", "Source is not the selected plan/stage experiment")
        require(type(m.get("expected_trials")) is int and m["expected_trials"] > 0, "Invalid expected_trials")
        require(rm.get("source_files") == sh and rm.get("source_hash") == digest(sh), "Review is not bound to selected source")
        require(rm.get("codec_version") == m["comparison_settings"]["codec_version"], "Review codec mismatch")
        require(m.get("comparison_group") == digest(m["comparison_settings"]), "Comparison group digest mismatch")
        if settings is None:
            settings = m["comparison_settings"]
        require(settings == m["comparison_settings"], "Mixed comparison_settings are not comparable")
        require(readable is None or readable.exists(), "Missing readable artifact")
        initial_hashes[str(source)], initial_hashes[str(review)] = sh, rh
        records.append((record, source, review, readable, m, rm))
    rows, summaries, issues, checks, session_uses = [], [], [], [], defaultdict(list)
    for record, source, review, readable, manifest, rm in records:
        results = {}
        for path in sorted(source.glob("trial-*/result.json")):
            result = read(path)
            number = result.get("trial_number")
            require(type(number) is int and 1 <= number <= manifest["expected_trials"] and number not in results, "Invalid/duplicate trial number")
            require(path.parent.name == "trial-%02d" % number, "Trial folder mismatch")
            results[number] = result
        review_trials = {p.parent.name for p in review.glob("trial-*/observation.json")}
        require(review_trials == {"trial-%02d" % n for n in results}, "Review trial coverage mismatch")
        stage_rows = [trial_row(manifest, source, review, n, results.get(n), issues) for n in range(1, manifest["expected_trials"] + 1)]
        if manifest["status"] == "completed" and (len(results) != manifest["expected_trials"] or any(r["status"] == "unconfirmed" for r in stage_rows)):
            issues.append({"stage": record["stage"], "issue": "completed_manifest_has_missing_or_unconfirmed_trials"})
        for row in stage_rows:
            for session in row["session_evidence"]:
                sid = session.get("thread_id")
                require(isinstance(sid, str) and sid, "Invalid session ID")
                session_uses[sid].append({"stage": row["stage"], "trial": row["trial"], "agent": session.get("agent")})
        rows.extend(stage_rows)
        summaries.append(summarize(stage_rows, manifest, record.get("label", str(record["stage"]))))
        checks.append({"stage": record["stage"], "source": str(source), "review": str(review),
                       "readable": str(readable) if readable else None, "source_status": manifest["status"],
                       "source_seal_verified": True, "review_seal_verified": True, "review_source_binding_verified": True,
                       "review_id": rm.get("review_id"), "review_status": rm.get("status"),
                       "review_policy_version": rm.get("review_policy_version"), "sample_recheck": rm.get("sample_recheck"),
                       "source_files_digest": digest(initial_hashes[str(source)]), "review_files_digest": digest(initial_hashes[str(review)])})
    duplicates = {sid: uses for sid, uses in session_uses.items() if len(uses) > 1}
    expected_sessions = sum(m["expected_trials"] for _, _, _, _, m, _ in records) * len(("A", "B"))
    actual_sessions = sum(len(uses) for uses in session_uses.values())
    for folder, before in initial_hashes.items():
        require(hashes(Path(folder)) == before, "Input changed during aggregation: " + folder)
    require(collection_path.read_bytes() == collection_bytes, "Collection changed during aggregation")
    integrity = {"valid": not duplicates and not issues, "plan_id": collection["plan_id"],
                 "collection": str(collection_path), "collection_sha256": hashlib.sha256(collection_bytes).hexdigest(),
                 "comparison_settings_equal": True, "comparison_group": digest(settings), "expected_sessions": expected_sessions,
                 "actual_session_records": actual_sessions, "unique_sessions": len(session_uses),
                 "session_count_complete": actual_sessions == expected_sessions, "duplicate_sessions": duplicates,
                 "session_occurrences": dict(session_uses), "issues": issues, "records": checks,
                 "inputs_unchanged_after_read": True,
                 "review_policy_versions": sorted({str(rm.get("review_policy_version")) for _, _, _, _, _, rm in records}),
                 "note": "A smaller session count can reflect recorded operational interruption; it is reported separately from duplicate IDs."}
    output.mkdir(parents=True, exist_ok=False)
    metadata = {"plan_id": collection["plan_id"], "created_at": datetime.now(timezone.utc).isoformat(),
                "comparison_group": digest(settings), "integrity_valid": integrity["valid"]}
    for name, value in (("trial_rows.json", {**metadata, "rows": rows}),
                        ("stage_summary.json", {**metadata, "stages": summaries}), ("integrity.json", integrity)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "comparison.md").write_text(markdown(collection["plan_id"], summaries, integrity), encoding="utf-8")
    return integrity


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        integrity = aggregate(args.collection, args.output)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print("Aggregation refused: " + str(exc), file=sys.stderr)
        return 2
    print("Output: " + str(Path(args.output).resolve()))
    print("Sessions: %s actual / %s expected; %s unique" % (integrity["actual_session_records"], integrity["expected_sessions"], integrity["unique_sessions"]))
    return 0 if integrity["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
