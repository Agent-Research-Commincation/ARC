"""Bounded communication codecs. No codec can read calendars or execute host code."""
import json
import math
import re
import struct
import time
from dataclasses import dataclass

from .problem import PEOPLE, MEETINGS, SLOTS

STAGES = {1: "자연어", 2: "JSON", 3: "논리식·관계 그래프", 4: "의미 벡터", 5: "바이트코드", 6: "공동 언어"}
KINDS = ["inform", "request", "propose", "accept", "reject"]
MEANINGS = KINDS + ["available", "preference", "at", "ask"]
CODEC_VERSION = "schedule-codecs-v1"


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
    return {"kind": kind, "facts": [], "schedule": {}, "requests": []}


def validate_frame(f):
    if not isinstance(f, dict) or set(f) != {"kind", "facts", "schedule", "requests"}:
        raise ValueError("Frame requires exactly kind, facts, schedule, requests")
    if f["kind"] not in KINDS or not isinstance(f["facts"], list):
        raise ValueError("Invalid kind or facts")
    if len(f["facts"]) > 144:
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
    return f


def canonical_frame(f):
    validate_frame(f)
    return {"kind": f["kind"], "facts": sorted(f["facts"]),
            "schedule": dict(sorted(f["schedule"].items())), "requests": sorted(f["requests"])}


def validate_language(entries):
    if not isinstance(entries, list) or len(entries) != len(MEANINGS):
        raise ValueError("Dictionary requires one entry per meaning: " + ",".join(MEANINGS))
    result = {}
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"meaning", "symbol"}:
            raise ValueError("Dictionary entries require meaning and symbol")
        meaning, symbol = item["meaning"], item["symbol"]
        if meaning not in MEANINGS or meaning in result:
            raise ValueError("Invalid or duplicate meaning")
        if not isinstance(symbol, str) or not re.fullmatch(r"[A-Za-z]{1,8}", symbol):
            raise ValueError("Symbols must contain 1-8 ASCII letters")
        if symbol in result.values():
            raise ValueError("Duplicate symbol")
        result[meaning] = symbol
    return result


def parse_logic(text, language=None):
    reverse = {v: k for k, v in (language or {x: x for x in MEANINGS}).items()}
    frame = empty_frame()
    have_kind = False
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines or len(lines) > 160:
        raise ValueError("Expected 1-160 predicate lines")
    for line in lines:
        match = re.fullmatch(r"([A-Za-z]+)\(([^()]*)\)\.", line)
        if not match or match[1] not in reverse:
            raise ValueError("Unknown predicate or invalid syntax: " + line[:80])
        predicate = reverse[match[1]]
        args = [x.strip() for x in match[2].split(",")] if match[2] else []
        if predicate in KINDS and not args:
            if have_kind:
                raise ValueError("Only one message kind")
            frame["kind"], have_kind = predicate, True
        elif predicate in ("available", "preference") and len(args) == 3:
            if not args[1].isdigit() or not args[2].isdigit():
                raise ValueError("Integer arguments required")
            frame["facts"].append([predicate, args[0], int(args[1]), int(args[2])])
        elif predicate == "at" and len(args) == 2 and args[1].isdigit():
            if args[0] in frame["schedule"]:
                raise ValueError("Duplicate meeting")
            frame["schedule"][args[0]] = int(args[1])
        elif predicate == "ask" and len(args) == 1:
            frame["requests"].append(args[0])
        else:
            raise ValueError("Invalid predicate arguments")
    if not have_kind:
        raise ValueError("Message kind is required")
    return canonical_frame(frame)


def render_logic(f, language=None):
    f = canonical_frame(f)
    symbols = language or {x: x for x in MEANINGS}
    lines = [symbols[f["kind"]] + "()."]
    lines += ["%s(%s,%d,%d)." % (symbols[r], p, s, v) for r, p, s, v in f["facts"]]
    lines += ["%s(%s,%d)." % (symbols["at"], m, s) for m, s in f["schedule"].items()]
    lines += ["%s(%s)." % (symbols["ask"], p) for p in f["requests"]]
    return "\n".join(lines)


def hadamard(values):
    out = list(values)
    half = 1
    while half < len(out):
        for start in range(0, len(out), 2 * half):
            for i in range(start, start + half):
                a, b = out[i], out[i + half]
                out[i], out[i + half] = a + b, a - b
        half *= 2
    return [v / 16 for v in out]  # normalized 256-dimensional orthogonal transform


def vector_encode(f):
    f = canonical_frame(f)
    x = [0.0] * 5 + [-1.0] * 144 + [-1.0] * 3 + [0.0] * 6 + [0.0] * 98
    x[KINDS.index(f["kind"])]=1.0
    for relation, person, slot, value in f["facts"]:
        idx = 5 + (0 if relation == "available" else 72) + PEOPLE.index(person) * 12 + slot
        x[idx] = float(value)
    for meeting, slot in f["schedule"].items():
        x[149 + MEETINGS.index(meeting)] = float(slot)
    for person in f["requests"]:
        x[152 + PEOPLE.index(person)] = 1.0
    return struct.pack("<256f", *hadamard(x))


def vector_decode(wire):
    if len(wire) != 1024:
        raise ValueError("Vector must contain 256 float32 values")
    values = hadamard(struct.unpack("<256f", wire))
    if any(not math.isfinite(x) or abs(x - round(x)) > 1e-5 for x in values):
        raise ValueError("Vector cannot be decoded into valid semantic features")
    x = [round(v) for v in values]
    if sorted(x[:5]) != [0, 0, 0, 0, 1] or any(x[158:]):
        raise ValueError("Invalid vector kind or padding")
    f = empty_frame(KINDS[x[:5].index(1)])
    for r, offset in (("available", 5), ("preference", 77)):
        for person in PEOPLE:
            for slot in range(12):
                value = x[offset + PEOPLE.index(person) * 12 + slot]
                if value != -1:
                    f["facts"].append([r, person, slot, value])
    for i, meeting in enumerate(MEETINGS):
        if x[149+i] != -1:
            f["schedule"][meeting] = x[149+i]
    for i, person in enumerate(PEOPLE):
        if x[152+i] not in (0, 1):
            raise ValueError("Invalid request feature")
        if x[152+i]:
            f["requests"].append(person)
    return canonical_frame(f)


def compile_bytecode(text):
    lines = [x.split() for x in text.splitlines() if x.strip()]
    if not lines or len(lines) > 160 or len(lines[0]) != 2 or lines[0][0] != "KIND" or lines[0][1] not in KINDS:
        raise ValueError("First instruction must be KIND inform|request|propose|accept|reject")
    wire = bytearray(b"ACB1" + bytes([KINDS.index(lines[0][1])]))
    for args in lines[1:]:
        if args[0] in ("AV", "PREF") and len(args) == 4:
            wire.extend([1 if args[0] == "AV" else 2, PEOPLE.index(args[1]), int(args[2]), int(args[3])])
        elif args[0] == "AT" and len(args) == 3:
            wire.extend([3, MEETINGS.index(args[1]), int(args[2])])
        elif args[0] == "ASK" and len(args) == 2:
            wire.extend([4, PEOPLE.index(args[1])])
        else:
            raise ValueError("Unknown instruction or arity")
    wire.append(255)
    decode_bytecode(bytes(wire))
    return bytes(wire)


def decode_bytecode(wire):
    if len(wire) < 6 or not wire.startswith(b"ACB1") or wire[4] >= len(KINDS):
        raise ValueError("Invalid bytecode header")
    frame = empty_frame(KINDS[wire[4]])
    i = 5
    try:
        while i < len(wire):
            op = wire[i]
            i += 1
            if op == 255:
                if i != len(wire):
                    raise ValueError("Trailing bytecode")
                return canonical_frame(frame)
            if op in (1, 2):
                frame["facts"].append(["available" if op == 1 else "preference", PEOPLE[wire[i]], wire[i+1], wire[i+2]])
                i += 3
            elif op == 3:
                m, s = MEETINGS[wire[i]], wire[i+1]
                if m in frame["schedule"]:
                    raise ValueError("Duplicate bytecode meeting")
                frame["schedule"][m] = s
                i += 2
            elif op == 4:
                frame["requests"].append(PEOPLE[wire[i]])
                i += 1
            else:
                raise ValueError("Unknown bytecode opcode")
    except IndexError as exc:
        raise ValueError("Truncated bytecode or invalid identifier") from exc
    raise ValueError("Missing END byte")


def render_assembly(f):
    f = canonical_frame(f)
    return "\n".join(["KIND " + f["kind"]]
                     + ["%s %s %d %d" % ("AV" if r == "available" else "PREF", p, s, v) for r, p, s, v in f["facts"]]
                     + ["AT %s %d" % (m, s) for m, s in f["schedule"].items()]
                     + ["ASK " + p for p in f["requests"]])


@dataclass
class Packet:
    wire: bytes
    receiver_text: str
    cpu_seconds: float
    wall_seconds: float
    frame: object = None


def transmit(stage, payload, language=None, max_bytes=16384):
    if (stage is not None and stage not in STAGES) or not isinstance(payload, str) or not payload.strip():
        raise ValueError("Unknown stage or empty payload")
    if len(payload.encode("utf-8")) > max_bytes:
        raise ValueError("Model payload exceeds byte limit")
    start_cpu, start_wall = time.process_time(), time.perf_counter()
    frame = None
    if stage is None or stage == 1:
        if stage == 1 and payload.lstrip().startswith(("{", "[", "```")):
            raise ValueError("Natural-language stage requires prose, not structured JSON or code blocks")
        wire = payload.encode("utf-8")
        received = wire.decode("utf-8")
    elif stage == 2:
        validate_frame(strict_json(payload))
        wire = payload.encode("utf-8")
        frame = canonical_frame(strict_json(wire.decode("utf-8")))
        received = wire.decode("utf-8")
    elif stage == 3:
        parse_logic(payload)
        wire = payload.encode("utf-8")
        frame = parse_logic(wire.decode("utf-8"))
        received = wire.decode("utf-8")
    elif stage == 4:
        wire = vector_encode(strict_json(payload))
        frame = vector_decode(wire)  # receiver derives everything exclusively from the wire
        received = compact(frame)
    elif stage == 5:
        wire = compile_bytecode(payload)
        frame = decode_bytecode(wire)
        received = compact(frame)
    else:
        if language is None:
            raise ValueError("Shared language has not been agreed")
        parse_logic(payload, language)
        wire = payload.encode("utf-8")
        frame = parse_logic(wire.decode("utf-8"), language)
        received = wire.decode("utf-8")
    if len(wire) > max_bytes:
        raise ValueError("Wire payload exceeds byte limit")
    return Packet(wire, received, time.process_time()-start_cpu, time.perf_counter()-start_wall, frame)


def instructions(stage, language=None):
    if stage is None:
        return ("Choose your own message content and format in payload. The channel delivers your UTF-8 text unchanged to your peer. "
                "No message representation or communication strategy is prescribed. Keep language empty; setup actions are unavailable.")
    example = {"kind": "inform", "facts": [["available", "A1", 0, 1], ["preference", "A1", 0, 2]], "schedule": {}, "requests": []}
    if stage == 1:
        return "Use English natural-language sentences in payload. You may describe facts, ask questions, propose or accept schedules. Do not use JSON, code blocks, or formal programs as the communication format."
    frame = ('Frame: {"kind":"inform|request|propose|accept|reject","facts":[["available|preference","A1|A2|A3|B1|B2|B3",slot,value]],"schedule":{"M1":slot},"requests":["A1"]}. '
             'All four fields required; no extra fields. facts/schedule/requests may be empty. Slots 0..11, availability 0/1, preferences 0..3. No duplicate facts. Arbitrary subsets are allowed. Example: ' + compact(example))
    if stage == 2:
        return "Put a JSON frame in payload. " + frame
    if stage == 3:
        return ("Use one predicate per line ending in a period. Begin with exactly one inform()., request()., propose()., accept()., or reject().\n"
                "Facts: available(A1,0,1). preference(A1,0,2). Schedule: at(M1,0). Requests: ask(A1).\n"
                "Only these predicates and person/meeting IDs are allowed. Slots 0..11; availability 0/1; preferences 0..3. Choose what to communicate yourself.")
    if stage == 4:
        return ("Put a JSON semantic frame in payload for the fixed encoder. Only its 256-dimensional float32 vector is sent; the peer sees the inverse-decoded semantic frame. This is a fixed feature-vector codec, not a learned embedding or hidden model state. " + frame)
    if stage == 5:
        return ("Write bytecode assembly in payload. First line KIND inform|request|propose|accept|reject. Subsequent lines may be AV A1 0 1, PREF A1 0 2, AT M1 0, or ASK A1. "
                "Compiler transmits actual binary bytecode; the receiver VM constructs a semantic frame. Only these instructions exist. Slots 0..11; availability 0/1; preferences 0..3. No host code or solving oracle exists.")
    if not language:
        return "First negotiate a dictionary using define_language / accept_language. Meanings: " + compact(MEANINGS)
    return ("Use this agreed dictionary for predicate names: " + compact(language)
            + ". Message starts with the symbol for one kind and empty parentheses, ending in a period. available/preference take (person,slot,value); at takes (meeting,slot); ask takes (person). One predicate per line. "
            "The grammar and IDs remain fixed; only the dictionary is negotiated. Example syntax: " + render_logic(example, language))
