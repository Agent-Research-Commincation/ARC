"""Pure post-run claim evaluation. Never sends feedback to experiment agents."""
import copy
import itertools
from collections import Counter
from .problem import PEOPLE, MEETINGS, SLOTS, evaluate, feasible_scores, team_summary
import base64
import json
import struct
from .contracts import compact
from .protocols import source_frame, wire_frame

REVIEW_POLICY_VERSION = "observation-review-v3.1"
CLAIM_TYPES = ("fact", "summary", "reason", "schedule_score", "schedule_valid",
               "schedule_optimal", "meeting_score", "meeting_available",
               "schedule_constraint", "public_precedence")


def validate_schedule(schedule):
    if not isinstance(schedule, dict) or set(schedule) != set(MEETINGS) or any(
            type(s) is not int or not 0 <= s < SLOTS for s in schedule.values()):
        raise ValueError("Candidate requires a complete bounded schedule")


def raw_preference_sum(problem, schedule):
    """Arithmetic only; does not imply that the schedule can be executed."""
    validate_schedule(schedule)
    return sum(problem["people"][person]["preferences"][schedule[m["id"]]]
               for m in problem["meetings"] for person in m["attendees"])

def outcome_signature(scores):
    best = max(scores.values(), default=None)
    return best, {slots for slots, score in scores.items() if score == best}


def summary_counterfactual(problem, claim):
    relation, owner, meeting, slot, value = claim
    summaries = {(a, m, s): team_summary(problem, a, m, s)
                 for a in ("A", "B") for m in MEETINGS for s in range(SLOTS)}
    summaries[owner, meeting, slot][relation] = value
    scores = {}
    for slots in itertools.product(range(SLOTS), repeat=3):
        schedule = dict(zip(MEETINGS, slots))
        original = evaluate(problem, schedule)
        if any(v.startswith(("Double booking:", "Precedence:")) for v in original["violations"]):
            continue
        if all(summaries[a, m, s]["available"] for m, s in schedule.items() for a in ("A", "B")):
            scores[slots] = sum(summaries[a, m, s]["preference"] for m, s in schedule.items() for a in ("A", "B"))
    return scores


def validate_claim(kind, value):
    """Validate a review annotation's meaning, without assuming its truth."""
    if kind in ("schedule_score","schedule_valid","schedule_optimal"):
        key = {"schedule_score":"score", "schedule_valid":"valid", "schedule_optimal":"optimal"}[kind]
        if not isinstance(value,dict) or set(value)!={"schedule",key} or type(value[key]) is not int or (key in ("valid","optimal") and value[key] not in (0,1)):
            raise ValueError("Candidate claim requires schedule and integer " + key)
        validate_schedule(value["schedule"])
        return
    if kind in ("meeting_score", "meeting_available"):
        key = "score" if kind == "meeting_score" else "available"
        if (not isinstance(value,dict) or set(value)!={"meeting","slot",key}
                or value["meeting"] not in MEETINGS or type(value["slot"]) is not int
                or not 0 <= value["slot"] < SLOTS or type(value[key]) is not int
                or (key == "available" and value[key] not in (0,1))):
            raise ValueError("Meeting claim requires meeting, slot and integer " + key)
        return
    if kind == "schedule_constraint":
        if (not isinstance(value,dict) or set(value)!={"schedule","constraint","satisfied"}
                or value["constraint"] not in ("precedence","distinct")
                or type(value["satisfied"]) is not int or value["satisfied"] not in (0,1)):
            raise ValueError("Invalid schedule constraint assertion")
        validate_schedule(value["schedule"])
        return
    if kind == "public_precedence":
        if (not isinstance(value,dict) or set(value)!={"before","after"}
                or value["before"] not in MEETINGS or value["after"] not in MEETINGS):
            raise ValueError("Invalid public precedence assertion")
        return
    sizes = {"fact":4, "summary":5, "reason":4}
    if kind not in sizes or not isinstance(value, list) or len(value) != sizes[kind]:
        raise ValueError("Invalid claim type or shape")
    if kind in ("fact", "summary"):
        relation, *_, slot, number = value
        if relation not in ("available", "preference") or type(slot) is not int or not 0 <= slot < SLOTS or type(number) is not int:
            raise ValueError("Invalid fact/summary relation, slot or value")
        if relation == "available" and number not in (0,1):
            raise ValueError("Annotate availability as 0/1 or leave the expression unjudgeable")
        if kind == "fact" and value[1] not in PEOPLE:
            raise ValueError("Unknown person")
        if kind == "summary" and (value[1] not in ("A","B") or value[2] not in MEETINGS):
            raise ValueError("Unknown summary owner/meeting")
    else:
        reason, meeting, target, slot = value
        if reason not in ("unavailable", "overlap") or meeting not in MEETINGS or type(slot) is not int or not 0 <= slot < SLOTS:
            raise ValueError("Invalid reason")
        if target not in (PEOPLE if reason == "unavailable" else MEETINGS):
            raise ValueError("Invalid reason target")


def check_claim(problem, kind, value, baseline, submissions, impact_cache):
    validate_claim(kind, value)
    details = {}
    if kind == "fact":
        relation, person, slot, actual = value
        expected = problem["people"][person]["availability" if relation == "available" else "preferences"][slot]
        expected = int(expected)
        correct = actual == expected
    elif kind == "summary":
        relation, owner, meeting, slot, actual = value
        expected = team_summary(problem, owner, meeting, slot)[relation]
        correct = actual == expected
    elif kind == "schedule_score":
        evaluation = evaluate(problem, value["schedule"])
        expected = evaluation["score"]
        arithmetic = raw_preference_sum(problem, value["schedule"])
        # The frozen v3 prompts did not define scores for infeasible candidates.
        # Preserve that uncertainty instead of imposing a new rule retroactively.
        correct = value["score"] == expected if evaluation["valid"] else None
        details = {"candidate_valid":evaluation["valid"], "arithmetic_sum":arithmetic,
                   "arithmetic_matches":value["score"] == arithmetic,
                   "interpretation":"feasible_candidate" if evaluation["valid"] else "legacy_infeasible_score_unspecified"}
    elif kind == "schedule_valid":
        expected = int(evaluate(problem,value["schedule"])["valid"])
        correct = value["valid"] == expected
    elif kind == "schedule_optimal":
        candidate = evaluate(problem,value["schedule"])
        best = max((baseline or feasible_scores(problem)).values())
        expected = int(candidate["valid"] and candidate["score"] == best)
        correct = value["optimal"] == expected
    elif kind in ("meeting_score", "meeting_available"):
        attendees = next(m["attendees"] for m in problem["meetings"] if m["id"] == value["meeting"])
        key = "score" if kind == "meeting_score" else "available"
        expected = (sum(problem["people"][p]["preferences"][value["slot"]] for p in attendees)
                    if key == "score" else int(all(problem["people"][p]["availability"][value["slot"]] for p in attendees)))
        correct = value[key] == expected
    elif kind == "schedule_constraint":
        schedule = value["schedule"]
        expected = int(all(schedule[a] < schedule[b] for a,b in problem["precedence"]) if value["constraint"] == "precedence"
                       else len(set(schedule.values())) == len(schedule))
        correct = value["satisfied"] == expected
    elif kind == "public_precedence":
        expected = [value["before"],value["after"]] in problem["precedence"]
        correct = expected
    else:
        reason, meeting, target, slot = value
        attendees = {m["id"]: set(m["attendees"]) for m in problem["meetings"]}
        if reason == "unavailable":
            expected = target in attendees[meeting] and not problem["people"][target]["availability"][slot]
        else:
            expected = meeting != target and bool(attendees[meeting] & attendees[target])
        correct = bool(expected)
    impact = None
    if correct is False and kind in ("fact", "summary"):
        cache_key = compact([kind, value])
        if cache_key not in impact_cache:
            if kind == "fact":
                changed = copy.deepcopy(problem)
                relation, person, slot, actual = value
                changed["people"][person]["availability" if relation == "available" else "preferences"][slot] = bool(actual) if relation == "available" else actual
                alternate = feasible_scores(changed)
            else:
                alternate = summary_counterfactual(problem, value)
            before, before_schedules = outcome_signature(baseline)
            after, after_schedules = outcome_signature(alternate)
            selected = {tuple(s[m] for m in MEETINGS) for s in submissions.values() if set(s) == set(MEETINGS)}
            impact_cache[cache_key] = {
                "method": "isolated counterfactual; other claims unchanged",
                "feasible_set_changed": set(baseline) != set(alternate), "schedule_scores_changed": baseline != alternate,
                "optimal_score_before": before, "optimal_score_after": after,
                "optimal_schedules_changed": before_schedules != after_schedules,
                "submitted_schedule_affected": any(baseline.get(s) != alternate.get(s) for s in selected) if selected else None,
                "submission_impact_status":"evaluated" if selected else "not_applicable"}
        impact = impact_cache[cache_key]
    return {"type":kind, "value":value, "expected":expected, "correct":correct, "impact":impact,
            "judgment":"undetermined" if correct is None else "correct" if correct else "incorrect", **details,
            "impact_status":"evaluated" if impact is not None else ("not_needed" if correct else "not_evaluated")}




def claim_counts(claims):
    result = {}
    for kind in CLAIM_TYPES:
        subset = [c for c in claims if c["type"]==kind]
        judged = [c for c in subset if c["correct"] is not None]
        result[kind] = {"occurrences":len(subset), "judged":len(judged),
                        "correct":sum(c["correct"] is True for c in judged) if judged else None,
                        "incorrect":sum(c["correct"] is False for c in judged) if judged else None,
                        "undetermined":sum(c["correct"] is None for c in subset)}
    return result


def claim_changes(claims):
    previous, changes = {}, []
    for c in claims:
        if c["type"] in ("fact","summary"):
            key = compact([c["sender"],c["type"],c["value"][:-1]])
            number = c["value"][-1]
            if key in previous and previous[key][0] != number:
                changes.append({"key":key,"from_message":previous[key][1],"to_message":c["message"],"previous":previous[key][0],"value":number})
            previous[key] = (number,c["message"])
    return changes


def analyze_trial(problem, stage, events, result, language=None, manual=None):
    packets = [e["params"] for e in events if e["method"] == "experiment/packet" and e["params"]["phase"] == "task"]
    manual = manual or {}
    baseline, impact_cache, rows = feasible_scores(problem), {}, []
    claims, codec_errors, pending, first_proposer = [], 0, 0, None
    owned = {a:set() for a in ("A","B")}
    summary_counts = {a:0 for a in ("A","B")}
    previous_proposal = None
    proposal_changes = 0
    for p in packets:
        logged_wire = base64.b64decode(p["payload_base64"], validate=True)
        framed = base64.b64decode(p["packet_base64"], validate=True)
        framing_ok = False
        wire = logged_wire
        try:
            length = struct.unpack("<I",framed[:4])[0]
            header = json.loads(framed[4:4+length].decode("utf-8"))
            wire = framed[4+length:]
            expected_header = {k:p[k] for k in ("sequence","sender","receiver","stage","phase","payload_length","proposal_revision")}
            framing_ok = (length+4 == p["header_bytes"] and len(wire) == p["payload_length"]
                          and wire == logged_wire and header == expected_header)
        except (ValueError,struct.error,UnicodeError):
            pass
        notes = ""
        decode_error = None
        if stage in (None,1):
            codec_ok = framing_ok and wire == p["sender_source"].encode("utf-8") and wire == p["receiver_text"].encode("utf-8")
            annotation = manual.get(p["sequence"], {"status":"pending"})
            completed = annotation["status"] == "complete"
            pending += not completed
            row_claims = annotation["claims"] if completed else []
            kinds = annotation["kinds"] if completed else []
            schedule = annotation["schedule"] if completed else {}
            requests = annotation["requests"] if completed else []
            unjudgeable = annotation["unjudgeable"] if completed else []
            notes = annotation.get("notes", "") if completed else ""
        else:
            source = source_frame(stage, p["sender_source"], language)
            try:
                received = wire_frame(stage, wire, language)
                expected_text = compact(received) if stage in (4,5) else wire.decode("utf-8")
                codec_ok = framing_ok and source == received and expected_text == p["receiver_text"]
            except (ValueError,TypeError,KeyError,UnicodeError) as exc:
                codec_ok, decode_error = False, str(exc)
            # Score what the sender actually asserted, separately from codec preservation.
            row_claims = [{"type":kind,"value":value} for kind, key in (("fact","facts"),("summary","summaries"),("reason","reasons")) for value in source[key]]
            row_claims += [{"type":"schedule_valid" if e[0]=="valid" else "schedule_score", "value":{"schedule":dict(zip(MEETINGS,e[1:4])), "valid" if e[0]=="valid" else "score":e[4]}} for e in source["evaluations"]]
            kinds, schedule, requests, unjudgeable = [source["kind"]], source["schedule"], source["requests"], []
            completed = True
        codec_errors += not codec_ok
        checked = []
        for claim in row_claims:
            verdict = check_claim(problem, claim["type"], claim["value"], baseline, result.get("submissions", {}), impact_cache)
            verdict.update(message=p["sequence"], sender=p["sender"], evidence=claim.get("evidence"),
                           annotation_note=claim.get("note"))
            checked.append(verdict)
            if claim["type"] == "fact" and claim["value"][1].startswith(p["sender"]):
                owned[p["sender"]].add(tuple(claim["value"][:3]))
            if claim["type"] == "summary":
                summary_counts[p["sender"]] += 1
        quality = None
        if "propose" in kinds:
            first_proposer = first_proposer or p["sender"]
            if previous_proposal is not None and schedule != previous_proposal:
                proposal_changes += 1
            previous_proposal = schedule
            if set(schedule) == set(MEETINGS):
                quality = evaluate(problem, schedule)
                best, _ = outcome_signature(baseline)
                quality["gap"] = best-quality["score"] if quality["valid"] else None
        claims += checked
        rows.append({"message":p["sequence"],"sender":p["sender"],"receiver":p["receiver"],"review_status":"complete" if completed else "pending",
                     "kinds":kinds,"schedule":schedule,"requests":requests,"claims":checked,"unjudgeable":unjudgeable,
                     "proposal_quality":quality,"codec_preserved":codec_ok,"framing_preserved":framing_ok,
                     "decode_error":decode_error,"notes":notes,
                     "questions":source["questions"] if stage not in (None,1) else annotation.get("questions",[]),
                     "references":source["references"] if stage not in (None,1) else annotation.get("references",[])})
    measured = bool(packets) and pending < len(packets)
    errors = [e["params"] for e in events if e["method"] == "experiment/rejected"]
    styles = {}
    for actor in ("A","B"):
        raw_count = len(owned[actor])
        reviewed = sum(r["sender"] == actor and r["review_status"] == "complete" for r in rows)
        styles[actor] = {"reviewed_messages":reviewed,"unique_own_raw_claims":raw_count if reviewed else None,
                         "all_72_own_raw_claims_stated":raw_count == 72 if reviewed else None,
                         "summary_claims":summary_counts[actor] if reviewed else None}
    submissions = result.get("submissions", {})
    return {"version":3, "review_policy_version":REVIEW_POLICY_VERSION, "claim_counts_by_type":claim_counts(claims),
            "unique_claims":len({compact([c["type"],c["value"]]) for c in claims}) if measured else None,
            "claim_occurrences":len(claims) if measured else None, "claim_changes":claim_changes(claims),"scope":"post-run observable content; no hidden reasoning; no feedback to agents",
            "content_review_status":("pending" if pending else "complete") if packets else "no_messages",
            "content_review_scope":"source-anchored annotations" if stage in (None,1) else "structured explicit assertions",
            "task_messages":len(packets),"reviewed_messages":len(packets)-pending,
            "correct_claims":sum(c["correct"] is True for c in claims) if measured else None,
            "incorrect_claims":sum(c["correct"] is False for c in claims) if measured else None,
            "undetermined_claims":sum(c["correct"] is None for c in claims) if measured else None,
            "unjudgeable_expressions":sum(len(r["unjudgeable"]) for r in rows) if measured else None,
            "codec_errors":codec_errors,"information_sharing":styles,
            "first_proposer":first_proposer,"changed_proposal_messages":proposal_changes if measured else None,
            "explicit_revisions":sum(e["method"] == "experiment/submissions_invalidated" for e in events),
            "accept_messages":sum("accept" in r["kinds"] for r in rows) if measured else None,
            "agreement_note":"Acceptance expressions do not prove independent verification or final submission.",
            "completion":{"submitted_agents":sorted(submissions),"both_submitted":len(submissions)==2,
                          "identical_submissions":submissions.get("A")==submissions.get("B") if len(submissions)==2 else None,
                          "task_status":result["status"],"error":result.get("error")},
            "format_errors":errors,"messages":rows}
