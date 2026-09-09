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
        raise ValueError("Protocol v1 requires six named people and twelve slots")
    if [m["id"] for m in p["meetings"]] != MEETINGS:
        raise ValueError("Protocol v1 requires M1, M2, M3")
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
    data = {k: copy.deepcopy(v) for k, v in p.items() if k != "people"}
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
