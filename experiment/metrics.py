"""Pure measurements; unknown costs are never zero."""
import statistics
import math
from collections import Counter
from .contracts import OPERATIONAL_STATES

def model_cost(usage, pricing):
    if not isinstance(usage, dict):
        return None
    required = {"inputTokens", "cachedInputTokens", "outputTokens"}
    if not required <= set(usage):
        return None
    input_tokens, cached, output = (usage[k] for k in ("inputTokens", "cachedInputTokens", "outputTokens"))
    writes = usage.get("cacheWriteInputTokens", 0)
    if any(type(x) is not int for x in (input_tokens,cached,output,writes)):
        return None
    rates = [pricing.get(k) for k in ("input_per_million","cached_input_per_million","cache_write_multiplier","output_per_million")]
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in rates):
        return None
    if min(input_tokens, cached, output, writes) < 0 or cached > input_tokens or writes > input_tokens-cached:
        return None
    # Input includes cached tokens. Reasoning is already a subset of output, not an extra charge.
    return ((input_tokens-cached) * pricing["input_per_million"]
            + cached * pricing["cached_input_per_million"]
            + writes * pricing["input_per_million"] * (pricing["cache_write_multiplier"]-1)
            + output * pricing["output_per_million"]) / 1_000_000


def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return {"count": len(values), "mean": statistics.mean(values), "median": statistics.median(values), "min": min(values), "max": max(values)}


def summarize(results, expected=5):
    successes = sum(bool(x["success"]) for x in results)
    infrastructure_errors = sum(x.get("status") == "infrastructure_error" or x.get("operational_status") == "infrastructure_error" for x in results)
    task_trials = sum(x.get("status") not in OPERATIONAL_STATES for x in results)
    complete = len(results) == expected and all(x.get("status") != "unconfirmed" for x in results)
    def complete_sum(key):
        vals = [x.get(key) for x in results]
        return sum(vals) if len(vals) == expected and all(x is not None for x in vals) else None
    total = complete_sum("total_cost_estimate_usd")
    model = complete_sum("model_cost_estimate_usd")
    return {"completed_trials": task_trials, "attempted_trials": len(results), "infrastructure_errors": infrastructure_errors,
            "terminal_trials":sum(x.get("status") != "unconfirmed" for x in results),
            "not_started_trials":expected-len(results), "status_counts":dict(Counter(x.get("status","success" if x["success"] else "failed") for x in results)),
            "operational_interruptions":sum(x.get("status") in OPERATIONAL_STATES or x.get("operational_status") in OPERATIONAL_STATES for x in results),
            "expected_trials": expected, "success_count": successes,
            "success_rate": successes/expected if complete else None,
            "batch_complete": complete,
            "quality_gap_successes": stats([x["quality_gap"] for x in results if x["success"]]),
            "total_cost_estimate_usd": total,
            "cost_per_success_estimate_usd": total/successes if complete and successes and total is not None else None,
            "model_cost_estimate_usd": model,
            "known_partial_model_cost_estimate_usd":sum(x["model_cost_estimate_usd"] for x in results if x.get("model_cost_estimate_usd") is not None)
                if any(x.get("model_cost_estimate_usd") is not None for x in results) else None,
            "model_cost_measured_trials":sum(x.get("model_cost_estimate_usd") is not None for x in results),
            "model_cost_per_success_estimate_usd": model/successes if complete and successes and model is not None else None,
            "cost_note": "Model-only values are partial API-equivalent estimates, not total costs or actual subscription charges. Unmeasured costs are null.",
            "completion_seconds_successes": stats([x["elapsed_seconds"] for x in results if x["success"]]),
            "termination_seconds_all": stats([x["elapsed_seconds"] for x in results]),
            "communication_bytes": stats([x["communication_bytes"] for x in results]),
            "communication_processing_cpu_seconds": stats([x["protocol_cpu_seconds"] for x in results]),
            "communication_processing_cost_estimate_usd": complete_sum("communication_processing_cost_estimate_usd"),
            "protocol_errors": sum(x["protocol_errors"] for x in results),
            "task_sender_text_bytes": stats([x.get("task_sender_text_bytes") for x in results]),
            "task_receiver_text_bytes": stats([x.get("task_receiver_text_bytes") for x in results]),
            "runner_turns": sum(x.get("actions", 0) for x in results),
            "request_count_scope": "Runner input/response turns, not provider-internal calls or HTTP requests.",
            # Retained for consumers of older summaries; this is the same turn count.
            "model_calls": sum(x.get("actions", 0) for x in results)}


def communication_totals(events):
    packets = [e["params"] for e in events if e["method"] == "experiment/packet"]
    rejected = [e["params"] for e in events if e["method"] == "experiment/codec_rejected"]
    task = [p for p in packets if p["phase"] == "task"]
    return {"message_count":len(packets), "payload_bytes":sum(p["payload_length"] for p in packets),
            "codec_task_timing":{key:sum((p.get("codec_timing") or {}).get(key,0.) for p in task)
                for key in ("encoding_cpu_seconds","decoding_cpu_seconds","encoding_wall_seconds","decoding_wall_seconds")},
            "framing_cpu_seconds":sum(p.get("framing_cpu_seconds",0.) for p in packets),
            "framing_wall_seconds":sum(p.get("framing_wall_seconds",0.) for p in packets),
            "envelope_bytes":sum(p["header_bytes"] for p in packets),
            "communication_bytes":sum(p["payload_length"]+p["header_bytes"] for p in packets),
            "task_sender_text_bytes":sum(len((p.get("sender_source") or "").encode()) for p in task),
            "task_receiver_text_bytes":sum(len(p["receiver_text"].encode()) for p in task),
            "protocol_cpu_seconds":sum(p["processing_cpu_seconds"] for p in packets+rejected),
            "protocol_wall_seconds":sum(p["processing_wall_seconds"] for p in packets+rejected),
            "actions":sum(e["method"] == "experiment/input" for e in events),
            "protocol_errors":sum(e["method"] == "experiment/rejected" for e in events)}
