"""Shared task semantics and phase-specific control contracts. No problem answers."""
import copy
import json
import math
from .problem import PEOPLE, MEETINGS, SLOTS

RECORD_VERSION = "3.0.0"
SEMANTIC_VERSION = "schedule-semantics-v3"
KINDS = ["inform", "request", "propose", "accept", "reject"]
TEAMS = ["A", "B"]
REASONS = ["unavailable", "overlap"]
MAX_REASONS = len(MEETINGS) * (len(PEOPLE) + len(MEETINGS)-1) * SLOTS
MEANINGS = KINDS + ["available", "preference", "at", "ask", "teamavailable", "teampreference", "unavailable", "overlap", "askfact", "asksummary", "askvalid", "askscore", "valid", "score", "recheck"]
TASK_ACTIONS = ["send", "revise", "wait", "submit", "stop"]
SETUP_ACTIONS = ["define_language", "accept_language", "stop"]
TERMINAL_STATES = {"success", "failed", "stopped", "cancelled", "infrastructure_error", "unconfirmed"}
OPERATIONAL_STATES = {"cancelled", "infrastructure_error", "unconfirmed"}
LEGACY_BUDGET_KEYS = {"max_turns", "max_messages", "max_language_turns", "max_trial_tokens", "max_payload_bytes", "trial_timeout_seconds", "turn_timeout_seconds"}

class CodexError(RuntimeError):
    pass

class Cancelled(RuntimeError):
    pass

class ActionFormatError(ValueError):
    def __init__(self, category, message, raw=None):
        super().__init__(message)
        self.category, self.raw = category, raw


def bounded_slot(value):
    return type(value) is int and 0 <= value < SLOTS


def validate_question(value):
    if not isinstance(value, list) or not value:
        raise ValueError("Question must be a typed array")
    kind, *args = value
    if kind == "fact" and len(args) == 3:
        valid = args[0] in ("available", "preference") and args[1] in PEOPLE and bounded_slot(args[2])
    elif kind == "summary" and len(args) == 4:
        valid = args[0] in ("available", "preference") and args[1] in TEAMS and args[2] in MEETINGS and bounded_slot(args[3])
    elif kind in ("valid", "score") and len(args) == 3:
        valid = all(bounded_slot(x) for x in args)
    else:
        valid = False
    if not valid:
        raise ValueError("Invalid question type or arguments")


def validate_evaluation(value):
    if not isinstance(value, list) or len(value) != 5:
        raise ValueError("Evaluation is [valid|score,M1_slot,M2_slot,M3_slot,value]")
    kind, *slots, number = value
    if kind not in ("valid", "score") or not all(bounded_slot(s) for s in slots):
        raise ValueError("Invalid candidate evaluation")
    if type(number) is not int or not 0 <= number <= (1 if kind == "valid" else 54):
        raise ValueError("Invalid candidate evaluation value")

def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def strict_json(text):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("Duplicate JSON key: " + k)
            out[k] = v
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Non-finite number")))


def empty_frame(kind="inform"):
    return {"kind": kind, "facts": [], "schedule": {}, "requests": [], "summaries": [], "reasons": [], "questions": [], "evaluations": [], "references": []}


def validate_frame(f):
    required = {"kind", "facts", "schedule", "requests"}
    if not isinstance(f, dict) or not required <= set(f) or set(f)-required-{"summaries", "reasons", "questions", "evaluations", "references"}:
        raise ValueError("Frame requires kind, facts, schedule, requests; optional summaries and reasons")
    if f["kind"] not in KINDS or not isinstance(f["facts"], list):
        raise ValueError("Invalid kind or facts")
    if len(f["facts"]) > len(PEOPLE)*SLOTS*2:
        raise ValueError("Too many facts")
    seen = set()
    for fact in f["facts"]:
        if not isinstance(fact, list) or len(fact) != 4:
            raise ValueError("Fact is [available|preference, person, slot, value]")
        relation, person, slot, value = fact
        if relation not in ("available", "preference") or person not in PEOPLE:
            raise ValueError("Unknown fact relation or person")
        if type(slot) is not int or not 0 <= slot < SLOTS or type(value) is not int:
            raise ValueError("Fact slot/value must be bounded integers")
        if not 0 <= value <= (1 if relation == "available" else 3):
            raise ValueError("Invalid fact value")
        key = (relation, person, slot)
        if key in seen:
            raise ValueError("Duplicate fact")
        seen.add(key)
    if not isinstance(f["schedule"], dict) or not set(f["schedule"]) <= set(MEETINGS):
        raise ValueError("Unknown meeting")
    if any(type(s) is not int or not 0 <= s < SLOTS for s in f["schedule"].values()):
        raise ValueError("Invalid schedule slot")
    if not isinstance(f["requests"], list) or any(x not in PEOPLE for x in f["requests"]):
        raise ValueError("Requests must list person IDs")
    if len(set(f["requests"])) != len(f["requests"]):
        raise ValueError("Duplicate request")
    summaries = f.get("summaries", [])
    if not isinstance(summaries, list) or len(summaries) > 144:
        raise ValueError("Summaries must be a list of at most 144 claims")
    seen = set()
    for item in summaries:
        if not isinstance(item, list) or len(item) != 5:
            raise ValueError("Summary is [available|preference, team, meeting, slot, value]")
        relation, team, meeting, slot, value = item
        if relation not in ("available", "preference") or team not in TEAMS or meeting not in MEETINGS:
            raise ValueError("Invalid summary relation/team/meeting")
        if type(slot) is not int or not 0 <= slot < SLOTS or type(value) is not int or not 0 <= value <= (1 if relation == "available" else 9):
            raise ValueError("Invalid summary slot/value")
        key = (relation, team, meeting, slot)
        if key in seen:
            raise ValueError("Duplicate summary")
        seen.add(key)
    reasons = f.get("reasons", [])
    if not isinstance(reasons, list) or len(reasons) > MAX_REASONS:
        raise ValueError("Reasons exceed the finite semantic domain")
    seen = set()
    for item in reasons:
        if not isinstance(item, list) or len(item) != 4:
            raise ValueError("Reason is [unavailable, meeting, person, slot] or [overlap, meeting, other_meeting, slot]")
        kind, meeting, target, slot = item
        if kind not in REASONS or meeting not in MEETINGS or target not in (PEOPLE if kind == "unavailable" else MEETINGS):
            raise ValueError("Invalid reason kind/meeting/target")
        if kind == "overlap" and meeting == target:
            raise ValueError("Overlap requires distinct meetings")
        if type(slot) is not int or not 0 <= slot < SLOTS:
            raise ValueError("Invalid reason slot")
        if tuple(item) in seen:
            raise ValueError("Duplicate reason")
        seen.add(tuple(item))
    questions = f.get("questions", [])
    evaluations = f.get("evaluations", [])
    references = f.get("references", [])
    for values, validator, label in ((questions, validate_question, "question"), (evaluations, validate_evaluation, "evaluation")):
        if not isinstance(values, list):
            raise ValueError(label + "s must be an array")
        keys = set()
        for value in values:
            validator(value)
            key = tuple(value if label == "question" else value[:-1])
            if key in keys:
                raise ValueError("Duplicate " + label)
            keys.add(key)
    if not isinstance(references, list) or any(type(x) is not int or x < 1 for x in references):
        raise ValueError("References are positive message IDs to recheck")
    if len(set(references)) != len(references):
        raise ValueError("Duplicate reference")
    return f


def canonical_frame(f):
    validate_frame(f)
    return {"kind": f["kind"], "facts": sorted(f["facts"]),
            "schedule": dict(sorted(f["schedule"].items())), "requests": sorted(f["requests"]),
            "summaries": sorted(f.get("summaries", [])), "reasons": sorted(f.get("reasons", [])),
            "questions": sorted(f.get("questions", [])), "evaluations": sorted(f.get("evaluations", [])),
            "references": sorted(f.get("references", []))}


def action_schema(stage=None, phase="task"):
    if phase not in ("task", "setup") or (phase == "setup" and stage != 6):
        raise ValueError("Only stage 6 has a setup phase")
    props = {
        "action": {"type": "string", "enum": SETUP_ACTIONS if phase == "setup" else TASK_ACTIONS},
        "payload": {"type": "string"},
        "schedule": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "required": ["meeting", "slot"], "properties": {
                "meeting": {"type": "string", "enum": MEETINGS},
                "slot": {"type": "integer", "minimum": 0, "maximum": 11}}}},
        "language": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "required": ["meaning", "symbol"], "properties": {
                "meaning": {"type": "string", "enum": MEANINGS}, "symbol": {"type": "string"}}}},
    }
    if phase == "task":
        props["language"] = {"type":"array","maxItems":0,"items":{"type":"string"}}
    else:
        props["schedule"] = {"type":"array","maxItems":0,"items":{"type":"string"}}
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


def validate_action(a, stage=None, phase="task"):
    schema = action_schema(stage, phase)
    if not isinstance(a, dict) or set(a) != set(schema["required"]):
        raise ValueError("Action requires action, payload, schedule, language")
    if a["action"] not in schema["properties"]["action"]["enum"]:
        raise ValueError("Action unavailable in this phase")
    if not isinstance(a["payload"], str) or not isinstance(a["schedule"], list) or not isinstance(a["language"], list):
        raise ValueError("Invalid action field type")
    if a["action"] not in ("send", "revise", "stop") and a["payload"]:
        raise ValueError("Only send, revise or observer-only stop reason can contain payload")
    if a["action"] != "submit" and a["schedule"]:
        raise ValueError("Only submit can contain a schedule")
    if a["action"] != "define_language" and a["language"]:
        raise ValueError("Only define_language can contain a dictionary")
    return a


def schedule_from_action(action):
    entries = action["schedule"]
    if len(entries) != len(MEETINGS):
        raise ValueError("Submit exactly three meetings")
    schedule = {}
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"meeting", "slot"}:
            raise ValueError("Schedule entry requires meeting and slot")
        if item["meeting"] not in MEETINGS or item["meeting"] in schedule or not bounded_slot(item["slot"]):
            raise ValueError("Unknown/duplicate meeting or invalid slot")
        schedule[item["meeting"]] = item["slot"]
    return schedule


def validate_config(c):
    legacy = LEGACY_BUDGET_KEYS & set(c)
    if legacy:
        raise ValueError("v3 rejects research budgets: " + ", ".join(sorted(legacy)))
    allowed = {"version", "model", "reasoning_effort", "repetitions", "first_speakers", "service_tier", "problem_file", "pricing", "schedule_seed"}
    if set(c) != allowed or c["version"] != RECORD_VERSION:
        raise ValueError("Expected the v3 configuration schema; unknown/missing fields are rejected")
    if c["model"] != "gpt-5.6-luna" or c["reasoning_effort"] != "high" or type(c["repetitions"]) is not int or c["repetitions"] != 5:
        raise ValueError("This experiment requires gpt-5.6-luna / high / five repetitions")
    if c["first_speakers"] != ["A", "B", "A", "B", "A"] or c["service_tier"] != "default":
        raise ValueError("Expected paired first speakers A,B,A,B,A and default service tier")
    if type(c["schedule_seed"]) is not int:
        raise ValueError("Schedule seed must be an integer")
    for key in ("input_per_million", "cached_input_per_million", "cache_write_multiplier", "output_per_million", "local_processing_usd_per_cpu_second"):
        value = c["pricing"][key]
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            raise ValueError("Invalid pricing value: " + key)
