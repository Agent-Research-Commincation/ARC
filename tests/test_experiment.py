import contextlib
import base64
import copy
import io
import json
import random
import tempfile
import struct
import unittest
from pathlib import Path
from unittest.mock import patch

from experiment.cli import load_settings
from experiment.cli import main as cli_main
from experiment.codex import AppServer, CodexError, ActionFormatError, ISOLATION_CONFIG, validate_action
from experiment.problem import agent_input, public_input, evaluate, oracle, problem_diagnostics, PEOPLE, MEETINGS
from experiment.protocols import (STAGES, KINDS, MEANINGS, canonical_frame, compact, empty_frame,
    validate_frame, validate_language, render_logic, parse_logic, render_assembly,
    compile_bytecode, decode_bytecode, vector_encode, vector_decode, transmit, strict_json, VECTOR_DIMENSIONS)
from experiment.runner import Recorder, Trial, base_prompt, model_cost, summarize, schedule_from_action, run_batch

FIXTURES = Path(__file__).parent/"fixtures"
CONFIG = json.loads((FIXTURES/"config.json").read_text())
PROBLEM = json.loads((FIXTURES/"problem.json").read_text())
LANGUAGE = {meaning: "x" + chr(97+i) for i, meaning in enumerate(MEANINGS)}
LANGUAGE_ENTRIES = [{"meaning": k, "symbol": v} for k, v in LANGUAGE.items()]
GOOD_SCHEDULE = oracle(PROBLEM)["optimal_schedules"][0]


def action(kind, payload="", schedule=None, language=None):
    return {"action": kind, "payload": payload,
            "schedule": [{"meeting": m, "slot": s} for m, s in (schedule or {}).items()],
            "language": language or []}


class ScriptedBackend:
    """Offline fixture ONLY: deterministic responses never count as model experiment data."""
    created = []
    fail_once = False
    mismatch = False

    def __init__(self, config, event_sink=None):
        self.config = config
        self.usage = {}
        self.roles = {}
        self.calls = {}
        self.inputs = []
        self.thread_settings = {}
        self.language_calls = 0
        self.sent_bad = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def new_session(self, agent, instructions):
        tid = "fixture-%d-%s" % (len(self.created), agent)
        self.created.append(tid)
        self.stage = int(instructions.split("Stage ")[-1].split()[0]) if "Stage " in instructions else None
        self.roles[tid], self.calls[tid] = agent, 0
        self.usage[tid] = {"total": {"inputTokens": 0, "cachedInputTokens": 0, "outputTokens": 0, "totalTokens": 0}}
        return tid

    def turn(self, tid, text, schema=None, request_id=None):
        self.inputs.append((self.roles[tid], text))
        u = self.usage[tid]["total"]
        u["inputTokens"] += 100
        u["outputTokens"] += 30
        u["totalTokens"] += 130
        if schema and "define_language" in schema["properties"]["action"]["enum"]:
            self.language_calls += 1
            return action("define_language", language=LANGUAGE_ENTRIES) if self.language_calls == 1 else action("accept_language")
        if self.fail_once and not self.sent_bad:
            self.sent_bad = True
            return action("send", payload="not valid structured content")
        self.calls[tid] += 1
        turn = self.calls[tid]
        actor = self.roles[tid]
        if turn >= 3:
            schedule = dict(GOOD_SCHEDULE)
            if self.mismatch and actor == "B":
                schedule["M3"] = (schedule["M3"]+1) % 12
            return action("submit", schedule=schedule)
        f = empty_frame("inform" if turn == 1 else ("propose" if actor == "A" else "accept"))
        if turn == 1:
            person = actor+"1"
            f["facts"] = [["available", person, 0, int(PROBLEM["people"][person]["availability"][0])]]
        else:
            f["schedule"] = dict(GOOD_SCHEDULE)
        if self.stage == 1:
            payload = "I can confirm the calendar information." if turn == 1 else "I agree to " + ", ".join("%s at slot %d" % x for x in GOOD_SCHEDULE.items()) + "."
        elif self.stage in (None, 2, 4):
            payload = compact(f)
        elif self.stage == 3:
            payload = render_logic(f)
        elif self.stage == 5:
            payload = render_assembly(f)
        else:
            payload = render_logic(f, LANGUAGE)
        return action("send", payload=payload)


class ProblemTests(unittest.TestCase):
    def test_oracle_has_quality_variation(self):
        ref = oracle(PROBLEM)
        self.assertEqual(ref["feasible_count"], 54)
        self.assertGreater(len(ref["distinct_scores"]), 1)
        for s in ref["optimal_schedules"]:
            self.assertEqual(evaluate(PROBLEM, s)["score"], ref["optimal_score"])

    def test_known_legal_schedule(self):
        result = evaluate(PROBLEM, {"M1": 4, "M2": 6, "M3": 10})
        self.assertTrue(result["valid"])
        self.assertEqual(result["score"], 25)

    def test_missing_and_out_of_range(self):
        for schedule in ({}, {"M1": 1, "M2": 2, "M3": 12}, {"M1": True, "M2": 2, "M3": 3}):
            self.assertFalse(evaluate(PROBLEM, schedule)["valid"])

    def test_double_booking(self):
        result = evaluate(PROBLEM, {"M1": 4, "M2": 4, "M3": 10})
        self.assertTrue(any("Double booking" in s for s in result["violations"]))

    def test_precedence(self):
        result = evaluate(PROBLEM, {"M1": 10, "M2": 6, "M3": 4})
        self.assertTrue(any("Precedence" in s for s in result["violations"]))

    def test_unavailability(self):
        result = evaluate(PROBLEM, {"M1": 0, "M2": 6, "M3": 10})
        self.assertTrue(any("Unavailable" in s for s in result["violations"]))

    def test_disjoint_private_inputs(self):
        a, b = agent_input(PROBLEM, "A"), agent_input(PROBLEM, "B")
        self.assertEqual(set(a["your_people"]), {"A1", "A2", "A3"})
        self.assertEqual(set(b["your_people"]), {"B1", "B2", "B3"})
        self.assertEqual(a["public"], b["public"])
        self.assertNotIn("people", public_input(PROBLEM))
        a["your_people"]["A1"]["preferences"][0] = 99
        self.assertNotEqual(PROBLEM["people"]["A1"]["preferences"][0], 99)

    def test_explicit_slot_ids_match_calendar_arrays_and_evaluator(self):
        for actor in ("A", "B"):
            data = agent_input(PROBLEM, actor)
            indexing = data["public"]["slot_indexing"]
            self.assertEqual(indexing["base"], 0)
            self.assertEqual(indexing["mapping"][1], {"slot": 1, "time": "D1 10:00"})
            for item in indexing["mapping"]:
                self.assertEqual(PROBLEM["slots"][item["slot"]], item["time"])
        # Distinct fixture slot IDs must remain distinct.
        self.assertEqual(evaluate(PROBLEM, {"M1": 1, "M2": 11, "M3": 10})["score"], 25)
        self.assertFalse(evaluate(PROBLEM, {"M1": 2, "M2": 11, "M3": 10})["valid"])


class CodecTests(unittest.TestCase):
    def example(self):
        return {"kind": "propose", "facts": [["available", "A1", 0, 1], ["preference", "B3", 11, 3]],
                "schedule": {"M1": 1, "M3": 10}, "requests": ["B1"],
                "summaries": [["available","A","M3",10,1],["preference","B","M3",10,5]],
                "reasons": [["unavailable","M3","B3",10],["overlap","M1","M2",4]]}

    def test_semantics_roundtrip_all_structured_stages(self):
        f = self.example()
        for stage, payload in ((2, compact(f)), (3, render_logic(f)), (4, compact(f)),
                               (5, render_assembly(f)), (6, render_logic(f, LANGUAGE))):
            with self.subTest(stage=stage):
                packet = transmit(stage, payload, LANGUAGE)
                self.assertEqual(packet.frame, canonical_frame(f))
                self.assertGreaterEqual(packet.cpu_seconds, 0)

    def test_random_vector_roundtrips(self):
        rng = random.Random(23)
        for _ in range(150):
            f = empty_frame(rng.choice(KINDS))
            for person in PEOPLE:
                for slot in range(12):
                    if rng.random() < .2:
                        f["facts"].append(["available", person, slot, rng.randrange(2)])
                    if rng.random() < .2:
                        f["facts"].append(["preference", person, slot, rng.randrange(4)])
            f["schedule"] = {m: rng.randrange(12) for m in MEETINGS if rng.random() < .5}
            f["requests"] = rng.sample(PEOPLE, rng.randrange(7))
            wire = vector_encode(f)
            self.assertEqual(len(wire), VECTOR_DIMENSIONS*4+5)
            self.assertEqual(vector_decode(wire), canonical_frame(f))

    def test_full_vector_frame(self):
        f = empty_frame()
        f["facts"] = [[r, p, s, 1] for r in ("available", "preference") for p in PEOPLE for s in range(12)]
        self.assertEqual(vector_decode(vector_encode(f)), canonical_frame(f))

    def test_vector_invalid_data(self):
        for wire in (b"short", b"\xff"*(VECTOR_DIMENSIONS*4), b"\x00"*(VECTOR_DIMENSIONS*4)):
            with self.assertRaises(ValueError):
                vector_decode(wire)

    def test_bytecode_is_binary(self):
        wire = compile_bytecode("KIND inform\nAV A1 0 1")
        self.assertEqual(wire, b"ACB3\x00\x01\x00\x00\x01\xff")
        self.assertEqual(decode_bytecode(wire)["facts"], [["available", "A1", 0, 1]])

    def test_bytecode_rejects_execution_and_invalid_bytes(self):
        for source in ("KIND inform\nEXEC rm file", "KIND inform\nAV A1 99 1", "KIND inform\nPREF B1 0 255"):
            with self.assertRaises(ValueError):
                compile_bytecode(source)
        valid = compile_bytecode("KIND inform\nAV A1 0 1")
        for wire in (valid[:-1], valid+b"extra", b"ACB1\x00\xee\xff", b"ACB1\x00\x01\xff"):
            with self.assertRaises(ValueError):
                decode_bytecode(wire)

    def test_json_rejects_duplicate_keys_and_nonfinite(self):
        for payload in ('{"kind":"inform","kind":"reject"}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                strict_json(payload)

    def test_frame_rejects_extra_free_text(self):
        f = self.example()
        f["note"] = "bypass"
        with self.assertRaises(ValueError):
            validate_frame(f)

    def test_frame_rejects_duplicate_or_invalid_facts(self):
        f = self.example()
        f["facts"].append(f["facts"][0])
        with self.assertRaises(ValueError):
            validate_frame(f)
        f = self.example()
        f["facts"][0][3] = True
        with self.assertRaises(ValueError):
            validate_frame(f)

    def test_logic_rejects_unknown_predicates(self):
        for source in ("inform().\nexec(rm).", "available(A1,0,1).", "inform().\nreject()."):
            with self.assertRaises(ValueError):
                parse_logic(source)

    def test_natural_wire_is_utf8(self):
        text = "I propose a meeting tomorrow. 일정 확인 부탁드립니다."
        packet = transmit(1, text)
        self.assertEqual(packet.wire, text.encode("utf-8"))
        self.assertEqual(packet.receiver_text, text)

    def test_natural_rejects_json(self):
        with self.assertRaises(ValueError):
            transmit(1, compact(self.example()))

    def test_observation_preserves_agent_chosen_format(self):
        for payload in ('{"free_form":"자율"}', '[1,2,3]', '```text\ncustom data\n```', 'A free prose message.'):
            packet = transmit(None, payload)
            self.assertEqual(packet.wire, payload.encode("utf-8"))
            self.assertEqual(packet.receiver_text, payload)

    def test_large_valid_payloads_have_no_research_byte_budget(self):
        text = "Natural language message. "*2000
        self.assertEqual(transmit(1,text).receiver_text,text)
        self.assertGreater(len(transmit(4,compact(empty_frame())).wire),16384)

    def test_language_requires_agreement(self):
        with self.assertRaises(ValueError):
            transmit(6, "hello().")

    def test_language_validation(self):
        self.assertEqual(validate_language(LANGUAGE_ENTRIES), LANGUAGE)
        for entries in (LANGUAGE_ENTRIES[:-1], [{"meaning": k, "symbol": "same"} for k in MEANINGS],
                        [{"meaning": k, "symbol": "../bad"} for k in MEANINGS]):
            with self.assertRaises(ValueError):
                validate_language(entries)


class MetricTests(unittest.TestCase):
    def test_cache_and_reasoning_not_double_counted(self):
        usage = {"inputTokens": 1000, "cachedInputTokens": 200, "cacheWriteInputTokens": 100,
                 "outputTokens": 500, "reasoningOutputTokens": 450}
        expected = (800*.2+200*.02+100*.2*.25+500*1.2)/1e6
        self.assertAlmostEqual(model_cost(usage, CONFIG["pricing"]), expected)

    def test_missing_usage_is_not_zero(self):
        self.assertIsNone(model_cost(None, CONFIG["pricing"]))
        self.assertIsNone(model_cost({}, CONFIG["pricing"]))

    def sample(self, success, amount):
        return {"success": success, "quality_gap": 0 if success else None,
                "total_cost_estimate_usd": amount, "model_cost_estimate_usd": amount/2,
                "elapsed_seconds": 2, "communication_bytes": 100, "protocol_cpu_seconds": .01,
                "communication_processing_cost_estimate_usd": None, "protocol_errors": 0}

    def test_success_cost_includes_failures(self):
        values = [self.sample(i < 2, 1) for i in range(5)]
        s = summarize(values)
        self.assertEqual(s["cost_per_success_estimate_usd"], 2.5)
        self.assertEqual(s["success_rate"], .4)

    def test_zero_success_not_free(self):
        s = summarize([self.sample(False, 1) for _ in range(5)])
        self.assertIsNone(s["cost_per_success_estimate_usd"])
        self.assertEqual(s["total_cost_estimate_usd"], 5)

    def test_incomplete_batch_does_not_claim_five(self):
        s = summarize([self.sample(True, 1)])
        self.assertFalse(s["batch_complete"])
        self.assertIsNone(s["success_rate"])
        self.assertIsNone(s["cost_per_success_estimate_usd"])

    def test_partial_cost_is_not_total(self):
        values = [self.sample(True, 1) for _ in range(5)]
        values[0]["total_cost_estimate_usd"] = None
        s = summarize(values)
        self.assertIsNone(s["cost_per_success_estimate_usd"])
        self.assertIsNotNone(s["model_cost_per_success_estimate_usd"])


class RunnerTests(unittest.TestCase):
    def run_fixture(self, stage, backend=None, config=None):
        with tempfile.TemporaryDirectory() as tmp:
            backend = backend or ScriptedBackend(CONFIG)
            rec = Recorder(Path(tmp) / "trial")
            result = Trial(backend, config or CONFIG, PROBLEM, stage, rec).run()
            events = [json.loads(line) for line in (rec.folder/"events.jsonl").read_text().splitlines()]
            return result, events, backend

    def test_all_six_trial_pipelines(self):
        for stage in STAGES:
            with self.subTest(stage=stage):
                result, events, backend = self.run_fixture(stage)
                self.assertEqual(result["status"], "success", result)
                self.assertEqual(result["quality_gap"], 0)
                self.assertEqual(result["message_count"], 6 if stage == 6 else 4)
                packets = [x["params"] for x in events if x["method"] == "experiment/packet"]
                self.assertEqual(result["communication_bytes"], sum(x["payload_length"]+x["header_bytes"] for x in packets))
                self.assertIsNone(result["total_cost_estimate_usd"])
                self.assertIsNotNone(result["model_cost_estimate_usd"])

    def test_task_initialization_does_not_include_peer_calendar(self):
        _, _, backend = self.run_fixture(2)
        for owner, text in backend.inputs:
            if text.startswith("TASK START."):
                data = json.loads(text.split("TASK START. ", 1)[1].split("\nProtocol:", 1)[0])
                self.assertTrue(all(person.startswith(owner) for person in data["your_people"]))

    def test_submissions_not_forwarded_as_messages(self):
        result, events, _ = self.run_fixture(2)
        packets = [e for e in events if e["method"] == "experiment/packet"]
        self.assertEqual(len(packets), 4)
        self.assertEqual(set(result["submissions"]), {"A", "B"})

    def test_disagreement_fails(self):
        backend = ScriptedBackend(CONFIG)
        backend.mismatch = True
        result, _, _ = self.run_fixture(2, backend)
        self.assertFalse(result["success"])
        self.assertIn("different schedules", result["error"])

    def test_invalid_message_is_not_delivered(self):
        backend = ScriptedBackend(CONFIG)
        backend.fail_once = True
        result, events, _ = self.run_fixture(2, backend)
        self.assertTrue(result["success"])
        self.assertEqual(result["protocol_errors"], 1)
        packets = [x for x in events if x["method"] == "experiment/packet"]
        self.assertFalse(any("not valid structured" in x["params"]["receiver_text"] for x in packets))

    def test_measured_frame_is_the_actual_serialized_packet(self):
        _, events, _ = self.run_fixture(4)
        for event in events:
            if event["method"] != "experiment/packet":
                continue
            p = event["params"]
            wire = base64.b64decode(p["packet_base64"])
            length = struct.unpack("<I", wire[:4])[0]
            self.assertEqual(length+4, p["header_bytes"])
            self.assertEqual(len(wire), p["header_bytes"]+p["payload_length"])
            self.assertEqual(wire[4+length:], base64.b64decode(p["payload_base64"]))

    def test_infrastructure_failure_stops_without_filling_fake_trials(self):
        class BrokenBackend:
            def __init__(self, *args, **kwargs):
                raise CodexError("fixture connection unavailable")
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            folder, summary = run_batch(CONFIG, PROBLEM, 1, backend_factory=BrokenBackend, output_root=tmp)
            self.assertEqual(summary["completed_trials"], 0)
            self.assertEqual(summary["attempted_trials"], 1)
            self.assertFalse(summary["batch_complete"])
            self.assertIsNone(summary["success_rate"])
            manifest = json.loads((folder/"manifest.json").read_text())
            self.assertEqual(manifest["status"], "incomplete")

    def test_legacy_limit_config_is_rejected_not_silently_used(self):
        from experiment.contracts import validate_config
        with self.assertRaises(ValueError):
            validate_config(dict(CONFIG,max_messages=1))

    def test_five_new_pairs_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            before = len(ScriptedBackend.created)
            folder, summary = run_batch(CONFIG, PROBLEM, 2, backend_factory=ScriptedBackend, output_root=tmp)
            self.assertEqual(summary["success_count"], 5)
            self.assertEqual(len(set(ScriptedBackend.created[before:])), 10)
            other, _ = run_batch(CONFIG, PROBLEM, 2, backend_factory=ScriptedBackend, output_root=tmp)
            self.assertNotEqual(folder, other)
            self.assertTrue((folder / "report.md").exists())

    def test_language_reset_between_trials(self):
        first, _, backend1 = self.run_fixture(6)
        second, _, backend2 = self.run_fixture(6)
        self.assertEqual(backend1.language_calls, 2)
        self.assertEqual(backend2.language_calls, 2)
        self.assertNotEqual(first["sessions"], second["sessions"])

    def test_observation_has_five_fresh_pairs_and_each_actual_message_transcript(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            before = len(ScriptedBackend.created)
            folder, summary = run_batch(CONFIG, PROBLEM, None, repetitions=5, purpose="observation",
                                        backend_factory=ScriptedBackend, output_root=tmp)
            self.assertEqual(len(set(ScriptedBackend.created[before:])), 10)
            self.assertEqual(summary["success_count"], 5)
            self.assertEqual(summary["expected_trials"], 5)
            for i in range(1, 6):
                self.assertTrue((folder / ("trial-%02d/transcript.md" % i)).exists())
            self.assertEqual(folder.parent.name, "observation")
            manifest = json.loads((folder / "manifest.json").read_text())
            self.assertIsNone(manifest["stage"])
            transcript = (folder / "trial-01/transcript.md").read_text()
            self.assertIn('"kind":"inform"', transcript)
            self.assertIn("Agent A · submit", transcript)
            prompt = base_prompt("A", None)
            self.assertNotIn("Stage ", prompt)
            self.assertNotIn("Available language meanings", prompt)

    def test_unrestricted_observation_cannot_become_main_experiment(self):
        with self.assertRaises(ValueError):
            run_batch(CONFIG, PROBLEM, None)

    def test_no_submission_control_channel(self):
        bad = action("send", "hello", GOOD_SCHEDULE)
        with self.assertRaises(ValueError):
            validate_action(bad)

    def test_duplicate_submission_meeting(self):
        bad = action("submit", schedule=GOOD_SCHEDULE)
        bad["schedule"][1] = dict(bad["schedule"][0])
        with self.assertRaises(ValueError):
            schedule_from_action(bad)


class CodexConfigurationTests(unittest.TestCase):
    def test_tools_and_external_sources_disabled(self):
        for key in ("features.shell_tool", "features.multi_agent", "features.apps", "features.plugins", "features.memories"):
            self.assertIs(ISOLATION_CONFIG[key], False)
        self.assertEqual(ISOLATION_CONFIG["mcp_servers"], {})
        self.assertEqual(ISOLATION_CONFIG["project_doc_max_bytes"], 0)

    def test_wrong_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = AppServer(CONFIG)
            backend.tmp = type("Tmp", (), {"name": tmp})()
            with patch.object(backend, "rpc", return_value={"model": "other"}):
                with self.assertRaises(CodexError):
                    backend.new_session("A", "test")

    def test_new_session_has_no_environment_or_inherited_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = AppServer(CONFIG)
            backend.tmp = type("Tmp", (), {"name": tmp})()
            result = {"model": CONFIG["model"], "reasoningEffort": "high", "instructionSources": [], "thread": {"id": "mock"}}
            with patch.object(backend, "rpc", return_value=result) as rpc:
                backend.new_session("A", "test")
                params = rpc.call_args[0][1]
                self.assertEqual(params["environments"], [])
                self.assertEqual(params["selectedCapabilityRoots"], [])
                self.assertTrue(params["ephemeral"])
                self.assertFalse(params["allowProviderModelFallback"])

    def test_notifications_before_rpc_response_are_preserved(self):
        backend = AppServer(CONFIG)
        event = {"method": "item/completed", "params": {"threadId": "t", "item": {"type": "agentMessage", "text": "early"}}}
        backend.queue.put(event)
        backend.queue.put({"id": 1, "result": {"ok": True}})
        with patch.object(backend, "send"):
            self.assertEqual(backend.rpc("mock", {}), {"ok": True})
        self.assertEqual(list(backend.notifications), [event])

    def test_turn_result_and_usage_synchronized(self):
        backend = AppServer(CONFIG)
        final = action("wait")
        backend.queue.put({"method": "thread/tokenUsage/updated", "params": {
            "threadId": "t", "turnId": "u", "tokenUsage": {"total": {"inputTokens": 50, "cachedInputTokens": 0, "outputTokens": 10, "totalTokens": 60}}}})
        backend.queue.put({"method": "item/completed", "params": {"threadId": "t", "item": {"type": "agentMessage", "text": compact(final)}}})
        backend.queue.put({"method": "turn/completed", "params": {"threadId": "t", "turn": {"id": "u", "status": "completed"}}})
        with patch.object(backend, "rpc", side_effect=[{"turn": {"id": "u"}}, {}]):
            self.assertEqual(backend.turn("t", "hello"), final)
        self.assertEqual(backend.usage["t"]["total"]["totalTokens"], 60)

    def test_missing_final_usage_does_not_reuse_old_cost(self):
        backend = AppServer(CONFIG)
        backend.usage["t"] = {"total": {"inputTokens": 50}}
        backend.usage_turn_ids["t"] = "old"
        backend.queue.put({"method": "item/completed", "params": {"threadId": "t", "item": {"type": "agentMessage", "text": compact(action("wait"))}}})
        backend.queue.put({"method": "turn/completed", "params": {"threadId": "t", "turn": {"id": "u", "status": "completed"}}})
        with patch.object(backend, "rpc", side_effect=[{"turn": {"id": "u"}}, {}]):
            backend.turn("t", "hello")
        self.assertNotIn("t", backend.usage)

    def test_unexpected_model_tool_fails_closed(self):
        backend = AppServer(CONFIG)
        backend.queue.put({"method": "item/started", "params": {"threadId": "t", "item": {"type": "commandExecution"}}})
        with patch.object(backend, "rpc", side_effect=[{"turn": {"id": "u"}}, {}]):
            with self.assertRaises(CodexError):
                backend.turn("t", "hello")

    def test_model_reroute_fails_closed(self):
        backend = AppServer(CONFIG)
        backend.queue.put({"method": "model/rerouted", "params": {"threadId": "t", "toModel": "other"}})
        with patch.object(backend, "rpc", side_effect=[{"turn": {"id": "u"}}, {}]):
            with self.assertRaises(CodexError):
                backend.turn("t", "hello")


class CommandRoutingTests(unittest.TestCase):
    def test_observe_does_not_launch_any_numbered_stage(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with patch("experiment.cli.run_batch", return_value=(Path("/tmp/fixture"), {"batch_complete": True})) as run:
                self.assertEqual(cli_main(["observe"]), 0)
                run.assert_called_once()
                self.assertIsNone(run.call_args[0][2])
                self.assertEqual(run.call_args[1]["repetitions"], 5)
                self.assertEqual(run.call_args[1]["purpose"], "observation")

    def test_requested_stage_only_and_exactly_five_trials(self):
        for stage in STAGES:
            with self.subTest(stage=stage), contextlib.redirect_stdout(io.StringIO()):
                with patch("experiment.cli.run_batch", return_value=(Path("/tmp/fixture"), {"batch_complete": True})) as run:
                    self.assertEqual(cli_main(["run", str(stage)]), 0)
                    run.assert_called_once()
                    self.assertEqual(run.call_args[0][2], stage)
                    self.assertEqual(run.call_args[1]["repetitions"], 5)
                    self.assertEqual(run.call_args[1]["purpose"], "experiment")

    def test_invalid_stage_rejected_before_backend(self):
        with contextlib.redirect_stderr(io.StringIO()), patch("experiment.cli.run_batch") as run:
            with self.assertRaises(SystemExit):
                cli_main(["run", "7"])
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
