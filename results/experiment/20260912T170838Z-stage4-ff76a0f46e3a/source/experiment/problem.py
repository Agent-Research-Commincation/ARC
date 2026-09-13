import copy
import itertools
import json

PEOPLE = ["A1", "A2", "A3", "B1", "B2", "B3"]
MEETINGS = ["M1", "M2", "M3"]
SLOTS = 12


def load_problem(path):
    with open(path, encoding="utf-8") as f:
        problem = json.load(f)
    validate_problem(problem)
    return problem


def validate_problem(p):
    if len(p["slots"]) != SLOTS or set(p["people"]) != set(PEOPLE):
        raise ValueError("This protocol requires six named people and twelve slots")
    if [m["id"] for m in p["meetings"]] != MEETINGS:
        raise ValueError("This protocol requires M1, M2, M3")
    for person, info in p["people"].items():
        if info["owner"] != person[0]:
            raise ValueError("Invalid person ownership")
        if len(info["availability"]) != SLOTS or len(info["preferences"]) != SLOTS:
            raise ValueError("Every person needs twelve availability/preference values")
        if any(type(x) is not bool for x in info["availability"]):
            raise ValueError("Availability must be boolean")
        if any(type(x) is not int or not 0 <= x <= 3 for x in info["preferences"]):
            raise ValueError("Preferences must be integers from 0 through 3")
    for m in p["meetings"]:
        if m["duration_slots"] != 1 or not m["attendees"]:
            raise ValueError("Meetings must last one slot and have attendees")
        if len(set(m["attendees"])) != len(m["attendees"]):
            raise ValueError("Duplicate attendee")
        if not set(m["attendees"]) <= set(PEOPLE):
            raise ValueError("Unknown attendee")
        if {x[0] for x in m["attendees"]} != {"A", "B"}:
            raise ValueError("Each meeting must involve both teams")
    if any(len(pair) != 2 or not set(pair) <= set(MEETINGS) or pair[0] == pair[1]
           for pair in p["precedence"]):
        raise ValueError("Invalid precedence")


def public_input(p):
    # Explicit allowlist: observer metadata and future reference answers cannot leak.
    data = {k: copy.deepcopy(p[k]) for k in ("id", "slots", "meetings", "precedence")}
    data["slot_indexing"] = {
        "base": 0,
        "rule": "Slot IDs are 0 through 11. The entry at index i in slots, availability, and preferences refers to slot i. Use these same IDs in messages and final submissions.",
        "mapping": [{"slot": i, "time": label} for i, label in enumerate(p["slots"])],
    }
    return data


def agent_input(p, owner):
    if owner not in ("A", "B"):
        raise ValueError("Unknown agent")
    return {"agent": owner, "public": public_input(p), "your_people": {
        k: copy.deepcopy(v) for k, v in p["people"].items() if v["owner"] == owner
    }}


def evaluate(p, schedule):
    errors = []
    if not isinstance(schedule, dict) or set(schedule) != set(MEETINGS):
        return {"valid": False, "score": None, "violations": ["Expected M1, M2, M3"]}
    for m, slot in schedule.items():
        if type(slot) is not int or not 0 <= slot < SLOTS:
            errors.append("Invalid slot for " + m)
    if errors:
        return {"valid": False, "score": None, "violations": errors}
    occupied = set()
    score = 0
    for m in p["meetings"]:
        slot = schedule[m["id"]]
        for person in m["attendees"]:
            if not p["people"][person]["availability"][slot]:
                errors.append("Unavailable: %s at %s" % (person, m["id"]))
            if (person, slot) in occupied:
                errors.append("Double booking: %s at %s" % (person, slot))
            occupied.add((person, slot))
            score += p["people"][person]["preferences"][slot]
    for before, after in p["precedence"]:
        if schedule[before] >= schedule[after]:
            errors.append("Precedence: %s before %s" % (before, after))
    return {"valid": not errors, "score": score if not errors else None, "violations": errors}


def oracle(p):
    best = -1
    best_schedules = []
    count = 0
    scores = set()
    for slots in itertools.product(range(SLOTS), repeat=3):
        schedule = dict(zip(MEETINGS, slots))
        result = evaluate(p, schedule)
        if result["valid"]:
            count += 1
            scores.add(result["score"])
            if result["score"] > best:
                best, best_schedules = result["score"], [schedule]
            elif result["score"] == best:
                best_schedules.append(schedule)
    if not count or len(scores) < 2:
        raise ValueError("Problem must have multiple feasible quality levels")
    return {"optimal_score": best, "optimal_schedules": best_schedules,
            "feasible_count": count, "distinct_scores": sorted(scores)}


def team_summary(p, owner, meeting, slot):
    """Evaluator-side calculation; never supplied to the experiment agents."""
    attendees = next(m["attendees"] for m in p["meetings"] if m["id"] == meeting)
    people = [p["people"][person] for person in attendees if p["people"][person]["owner"] == owner]
    return {"available": int(all(person["availability"][slot] for person in people)),
            "preference": sum(person["preferences"][slot] for person in people)}


def feasible_scores(p):
    """Full outcome space for offline sensitivity checks (including infeasible variants)."""
    scores = {}
    for slots in itertools.product(range(SLOTS), repeat=len(MEETINGS)):
        result = evaluate(p, dict(zip(MEETINGS, slots)))
        if result["valid"]:
            scores[slots] = result["score"]
    return scores


def problem_diagnostics(p):
    """Describe coupling and a decisive private fact, without modifying task inputs."""
    reference = oracle(p)
    maxima = {}
    for meeting in p["meetings"]:
        values = {s: sum(p["people"][a]["preferences"][s] for a in meeting["attendees"])
                  for s in range(SLOTS) if all(p["people"][a]["availability"][s] for a in meeting["attendees"])}
        best = max(values.values())
        maxima[meeting["id"]] = {"score": best, "slots": [s for s, value in values.items() if value == best]}
    altered = copy.deepcopy(p)
    altered["people"]["B3"]["availability"][10] = not p["people"]["B3"]["availability"][10]
    changed = feasible_scores(altered)
    best = max(changed.values(), default=None)
    return {"oracle": reference, "per_meeting_independent_maxima": maxima,
            "coupling_gap": sum(m["score"] for m in maxima.values())-reference["optimal_score"],
            "sensitivity_probe": {"fact": ["available", "B3", 10, int(altered["people"]["B3"]["availability"][10])],
                "feasible_count": len(changed), "optimal_score": best,
                "optimal_schedules": [dict(zip(MEETINGS, slots)) for slots, value in changed.items() if value == best],
                "offline_only": True}}


def independent_oracle(p):
    """Independent enumeration: checks per-person meeting assignments, without evaluate()."""
    choices = []
    for meeting in p["meetings"]:
        choices.append([s for s in range(SLOTS) if all(p["people"][person]["availability"][s] for person in meeting["attendees"])])
    feasible = {}
    for slots in itertools.product(*choices):
        assignment = dict(zip(MEETINGS,slots))
        if any(assignment[a] >= assignment[b] for a,b in p["precedence"]):
            continue
        if any(len(times) != len(set(times)) for times in
               ([assignment[m["id"]] for m in p["meetings"] if person in m["attendees"]] for person in PEOPLE)):
            continue
        score = sum(p["people"][person]["preferences"][assignment[m["id"]]] for person in PEOPLE for m in p["meetings"] if person in m["attendees"])
        feasible[slots] = score
    best = max(feasible.values(),default=None)
    return {"optimal_score":best,"optimal_schedules":[dict(zip(MEETINGS,k)) for k,v in feasible.items() if v==best],
            "feasible_count":len(feasible),"distinct_scores":sorted(set(feasible.values()))}
