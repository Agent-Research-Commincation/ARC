"""Select a confirmation fixture using structural criteria only; no model calls."""
import copy
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiment.problem import oracle, independent_oracle, problem_diagnostics
from experiment.artifacts import digest, write_json


def select_problem(development, seed=20260911):
    rng = random.Random(seed)
    candidate_index = 0
    while True:
        candidate_index += 1
        p = copy.deepcopy(development)
        p["id"] = "confirmation-v3-20260911"
        for info in p["people"].values():
            info["preferences"] = [rng.randrange(4) for _ in info["preferences"]]
        reference = oracle(p)
        diagnostic = problem_diagnostics(p)
        if diagnostic["coupling_gap"] > 0 and len(reference["optimal_schedules"]) == 1 and diagnostic["sensitivity_probe"]["optimal_schedules"] != reference["optimal_schedules"]:
            assert independent_oracle(p) == reference
            return p, {"purpose":"offline confirmation fixture selection; not model experiment data",
                "seed":seed,"candidate_index":candidate_index,"problem_hash":digest(p),
                "criteria":["same six people, three meetings, twelve slots", "independent meeting optima conflict", "unique global optimum", "private availability changes optimum"],
                "method":"Preserve development availability/meeting structure; resample all preference values; choose first candidate satisfying fixed criteria before any live model output",
                "oracle":reference,"independent_oracle":independent_oracle(p),"diagnostics":diagnostic}


if __name__ == "__main__":
    development = json.loads((ROOT/"tests/fixtures/problem.json").read_text())
    problem, receipt = select_problem(development)
    target = ROOT/"config/problem-reference.json"
    if target.exists():
        raise SystemExit("Confirmation fixture is already frozen; do not reselect after seeing results")
    write_json(ROOT/"config/problem.json",problem)
    write_json(target,receipt)
    print("Confirmation fixture frozen and independently checked; no model calls")
