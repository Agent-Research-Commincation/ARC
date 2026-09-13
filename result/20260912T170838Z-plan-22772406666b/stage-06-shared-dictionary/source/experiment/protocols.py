"""Bounded communication codecs. No codec can read calendars or execute host code."""
import json
import math
import re
import struct
import time
from dataclasses import dataclass

from .problem import PEOPLE, MEETINGS, SLOTS

from itertools import product
from .contracts import (KINDS, MEANINGS, TEAMS, REASONS, MAX_REASONS, compact, strict_json,
                        empty_frame, validate_frame, canonical_frame)

STAGES = {1: "자연어", 2: "JSON", 3: "논리식·관계 표현", 4: "고정 의미 특성 벡터", 5: "바이트코드", 6: "공동 기호 언어"}
CODEC_VERSION = "schedule-codecs-v3"
# Finite problem semantics get fixed coordinates; unbounded message IDs use a lossless suffix.
FACT_KEYS = [(r,p,s) for r in ("available","preference") for p in PEOPLE for s in range(SLOTS)]
SUMMARY_KEYS = [(r,t,m,s) for r in ("available","preference") for t in TEAMS for m in MEETINGS for s in range(SLOTS)]
REASON_KEYS = [("unavailable",m,p,s) for m in MEETINGS for p in PEOPLE for s in range(SLOTS)] + [("overlap",m,n,s) for m in MEETINGS for n in MEETINGS if m != n for s in range(SLOTS)]
EVALUATION_KEYS = [(r,)+slots for r in ("valid","score") for slots in product(range(SLOTS),repeat=3)]
QUESTION_KEYS = [("fact",)+key for key in FACT_KEYS] + [("summary",)+key for key in SUMMARY_KEYS] + EVALUATION_KEYS
VECTOR_FEATURES = len(KINDS)+len(FACT_KEYS)+3+6+len(SUMMARY_KEYS)+len(REASON_KEYS)+len(QUESTION_KEYS)+len(EVALUATION_KEYS)
VECTOR_DIMENSIONS = 1 << (VECTOR_FEATURES-1).bit_length()


def unsigned(value):
    if type(value) is not int or value < 0:
        raise ValueError("Unsigned integer required")
    out = bytearray()
    while value >= 128:
        out.append((value & 127)|128)
        value >>= 7
    out.append(value)
    return bytes(out)


def read_unsigned(wire, offset):
    result, shift, start = 0, 0, offset
    while offset < len(wire):
        byte = wire[offset]; offset += 1
        result |= (byte & 127) << shift
        if byte < 128:
            if wire[start:offset] != unsigned(result):
                raise ValueError("Non-canonical integer")
            return result, offset
        shift += 7
    raise ValueError("Truncated integer")


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
    if not lines:
        raise ValueError("Expected predicate lines")
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
        elif predicate in ("teamavailable", "teampreference") and len(args) == 4 and args[2].isdigit() and args[3].isdigit():
            frame["summaries"].append(["available" if predicate == "teamavailable" else "preference", args[0], args[1], int(args[2]), int(args[3])])
        elif predicate == "askfact" and len(args) == 3:
            frame["questions"].append(["fact", args[0], args[1], int(args[2])])
        elif predicate == "asksummary" and len(args) == 4:
            frame["questions"].append(["summary", args[0], args[1], args[2], int(args[3])])
        elif predicate in ("askvalid", "askscore") and len(args) == 3:
            frame["questions"].append([predicate[3:]] + [int(x) for x in args])
        elif predicate in ("valid", "score") and len(args) == 4:
            frame["evaluations"].append([predicate] + [int(x) for x in args])
        elif predicate == "recheck" and len(args) == 1:
            frame["references"].append(int(args[0]))
        elif predicate in REASONS and len(args) == 3 and args[2].isdigit():
            frame["reasons"].append([predicate, args[0], args[1], int(args[2])])
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
    lines += ["%s(%s,%s,%d,%d)." % (symbols["team"+r], team, m, s, v) for r, team, m, s, v in f["summaries"]]
    lines += ["%s(%s,%s,%d)." % (symbols[r], m, target, s) for r, m, target, s in f["reasons"]]
    for q in f["questions"]:
        predicate = {"fact":"askfact", "summary":"asksummary", "valid":"askvalid", "score":"askscore"}[q[0]]
        lines.append(symbols[predicate] + "(" + ",".join(map(str,q[1:])) + ").")
    for e in f["evaluations"]:
        lines.append(symbols[e[0]] + "(" + ",".join(map(str,e[1:])) + ").")
    lines += [symbols["recheck"] + "(%d)." % r for r in f["references"]]
    return "\n".join(lines)


def vector_encode(f):
    f = canonical_frame(f)
    x = [int(f["kind"] == k) for k in KINDS]
    for field, keys in (("facts", FACT_KEYS),):
        lookup = {tuple(row[:-1]):row[-1] for row in f[field]}
        x.extend(lookup.get(key,-1) for key in keys)
    x.extend(f["schedule"].get(m,-1) for m in MEETINGS)
    x.extend(int(p in f["requests"]) for p in PEOPLE)
    lookup = {tuple(row[:-1]):row[-1] for row in f["summaries"]}
    x.extend(lookup.get(key,-1) for key in SUMMARY_KEYS)
    for field, keys in (("reasons",REASON_KEYS),("questions",QUESTION_KEYS)):
        present = {tuple(row) for row in f[field]}
        x.extend(int(key in present) for key in keys)
    lookup = {tuple(row[:-1]):row[-1] for row in f["evaluations"]}
    x.extend(lookup.get(key,-1) for key in EVALUATION_KEYS)
    x.extend([0]*(VECTOR_DIMENSIONS-len(x)))
    # Coordinates contain bounded exact integers. IDs never pass through float32.
    suffix = unsigned(len(f["references"])) + b"".join(unsigned(r) for r in f["references"])
    return b"ACV3" + struct.pack("<%df" % VECTOR_DIMENSIONS,*x) + suffix


def vector_decode(wire):
    size = 4 + VECTOR_DIMENSIONS*4
    if not wire.startswith(b"ACV3") or len(wire) <= size:
        raise ValueError("Invalid fixed-feature vector")
    floats = struct.unpack("<%df" % VECTOR_DIMENSIONS,wire[4:size])
    if any(not math.isfinite(v) or v != int(v) for v in floats):
        raise ValueError("Vector features must be exact finite integers")
    x = [int(v) for v in floats]
    if sorted(x[:len(KINDS)]) != [0]*(len(KINDS)-1)+[1] or any(x[VECTOR_FEATURES:]):
        raise ValueError("Invalid vector kind or padding")
    f = empty_frame(KINDS[x[:len(KINDS)].index(1)])
    offset = len(KINDS)
    for key in FACT_KEYS:
        value = x[offset]; offset += 1
        if value != -1: f["facts"].append(list(key)+[value])
    for m in MEETINGS:
        value = x[offset]; offset += 1
        if value != -1: f["schedule"][m] = value
    for p in PEOPLE:
        value = x[offset]; offset += 1
        if value not in (0,1): raise ValueError("Invalid request feature")
        if value: f["requests"].append(p)
    for key in SUMMARY_KEYS:
        value = x[offset]; offset += 1
        if value != -1: f["summaries"].append(list(key)+[value])
    for field, keys in (("reasons",REASON_KEYS),("questions",QUESTION_KEYS)):
        for key in keys:
            value = x[offset]; offset += 1
            if value not in (0,1): raise ValueError("Invalid presence feature")
            if value: f[field].append(list(key))
    for key in EVALUATION_KEYS:
        value = x[offset]; offset += 1
        if value != -1: f["evaluations"].append(list(key)+[value])
    count, offset = read_unsigned(wire,size)
    for _ in range(count):
        reference, offset = read_unsigned(wire,offset)
        f["references"].append(reference)
    if offset != len(wire): raise ValueError("Trailing vector bytes")
    return canonical_frame(f)


def compile_bytecode(text):
    f = parse_assembly(text)
    wire = bytearray(b"ACB3" + bytes([KINDS.index(f["kind"])]))
    for r,p,s,v in f["facts"]:
        wire.extend([1 if r == "available" else 2,PEOPLE.index(p),s,v])
    for m,s in f["schedule"].items(): wire.extend([3,MEETINGS.index(m),s])
    for p in f["requests"]: wire.extend([4,PEOPLE.index(p)])
    for r,t,m,s,v in f["summaries"]: wire.extend([5 if r == "available" else 6,TEAMS.index(t),MEETINGS.index(m),s,v])
    for r,m,t,s in f["reasons"]: wire.extend([7 if r == "unavailable" else 8,MEETINGS.index(m),(PEOPLE if r == "unavailable" else MEETINGS).index(t),s])
    for q in f["questions"]:
        if q[0] == "fact": wire.extend([9,int(q[1]=="preference"),PEOPLE.index(q[2]),q[3]])
        elif q[0] == "summary": wire.extend([10,int(q[1]=="preference"),TEAMS.index(q[2]),MEETINGS.index(q[3]),q[4]])
        else: wire.extend([11 if q[0]=="valid" else 12]+q[1:])
    for e in f["evaluations"]: wire.extend([13 if e[0]=="valid" else 14]+e[1:])
    for ref in f["references"]: wire.extend(bytes([15])+unsigned(ref))
    wire.append(255)
    return bytes(wire)


def parse_assembly(text):
    """Read the sender's assertions independently of the binary encoder/VM."""
    rows = [line.split() for line in text.splitlines() if line.strip()]
    if not rows or len(rows[0]) != 2 or rows[0][0] != "KIND":
        raise ValueError("First instruction must be KIND")
    f = empty_frame(rows[0][1])
    for args in rows[1:]:
        op = args[0]
        if op in ("AV", "PREF") and len(args) == 4:
            f["facts"].append(["available" if op == "AV" else "preference", args[1], int(args[2]), int(args[3])])
        elif op == "AT" and len(args) == 3:
            if args[1] in f["schedule"]:
                raise ValueError("Duplicate meeting")
            f["schedule"][args[1]] = int(args[2])
        elif op == "ASK" and len(args) == 2:
            f["requests"].append(args[1])
        elif op in ("TAV", "TPREF") and len(args) == 5:
            f["summaries"].append(["available" if op == "TAV" else "preference", args[1], args[2], int(args[3]), int(args[4])])
        elif op == "QFACT" and len(args) == 4:
            f["questions"].append(["fact",args[1],args[2],int(args[3])])
        elif op == "QSUMMARY" and len(args) == 5:
            f["questions"].append(["summary",args[1],args[2],args[3],int(args[4])])
        elif op in ("QVALID","QSCORE") and len(args) == 4:
            f["questions"].append(["valid" if op=="QVALID" else "score"]+[int(x) for x in args[1:]])
        elif op in ("VALID","SCORE") and len(args) == 5:
            f["evaluations"].append([op.lower()]+[int(x) for x in args[1:]])
        elif op == "RECHECK" and len(args) == 2:
            f["references"].append(int(args[1]))
        elif op in ("WHY_UNAVAILABLE", "WHY_OVERLAP") and len(args) == 4:
            f["reasons"].append(["unavailable" if op == "WHY_UNAVAILABLE" else "overlap", args[1], args[2], int(args[3])])
        else:
            raise ValueError("Unknown instruction or arity")
    return canonical_frame(f)


def source_frame(stage, text, language=None):
    if stage in (2,4):
        return canonical_frame(strict_json(text))
    if stage in (3,6):
        return parse_logic(text, language if stage == 6 else None)
    if stage == 5:
        return parse_assembly(text)
    return None


def wire_frame(stage, wire, language=None):
    if stage in (2,3,6):
        return source_frame(stage, wire.decode("utf-8"), language)
    if stage == 4:
        return vector_decode(wire)
    if stage == 5:
        return decode_bytecode(wire)
    return None


def decode_bytecode(wire):
    if len(wire) < 6 or not wire.startswith(b"ACB3") or wire[4] >= len(KINDS):
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
            elif op in (5,6):
                frame["summaries"].append(["available" if op == 5 else "preference", TEAMS[wire[i]], MEETINGS[wire[i+1]], wire[i+2], wire[i+3]])
                i += 4
            elif op in (7,8):
                targets = PEOPLE if op == 7 else MEETINGS
                frame["reasons"].append(["unavailable" if op == 7 else "overlap", MEETINGS[wire[i]], targets[wire[i+1]], wire[i+2]])
                i += 3
            elif op == 9:
                if wire[i] not in (0,1): raise ValueError("Invalid relation")
                frame["questions"].append(["fact",("available","preference")[wire[i]],PEOPLE[wire[i+1]],wire[i+2]])
                i += 3
            elif op == 10:
                if wire[i] not in (0,1): raise ValueError("Invalid relation")
                frame["questions"].append(["summary",("available","preference")[wire[i]],TEAMS[wire[i+1]],MEETINGS[wire[i+2]],wire[i+3]])
                i += 4
            elif op in (11,12):
                frame["questions"].append(["valid" if op==11 else "score",wire[i],wire[i+1],wire[i+2]])
                i += 3
            elif op in (13,14):
                frame["evaluations"].append(["valid" if op==13 else "score",wire[i],wire[i+1],wire[i+2],wire[i+3]])
                i += 4
            elif op == 15:
                ref,i = read_unsigned(wire,i)
                frame["references"].append(ref)
            else:
                raise ValueError("Unknown bytecode opcode")
    except IndexError as exc:
        raise ValueError("Truncated bytecode or invalid identifier") from exc
    raise ValueError("Missing END byte")


def render_assembly(f):
    f = canonical_frame(f)
    lines = ["KIND " + f["kind"]]
    lines += ["%s %s %d %d" % ("AV" if r=="available" else "PREF",p,s,v) for r,p,s,v in f["facts"]]
    lines += ["AT %s %d" % (m,s) for m,s in f["schedule"].items()]
    lines += ["ASK " + p for p in f["requests"]]
    lines += ["%s %s %s %d %d" % ("TAV" if r=="available" else "TPREF",t,m,s,v) for r,t,m,s,v in f["summaries"]]
    lines += ["%s %s %s %d" % ("WHY_UNAVAILABLE" if r=="unavailable" else "WHY_OVERLAP",m,t,s) for r,m,t,s in f["reasons"]]
    for q in f["questions"]:
        lines.append({"fact":"QFACT","summary":"QSUMMARY","valid":"QVALID","score":"QSCORE"}[q[0]]+" "+" ".join(map(str,q[1:])))
    lines += [e[0].upper()+" "+" ".join(map(str,e[1:])) for e in f["evaluations"]]
    lines += ["RECHECK %d" % ref for ref in f["references"]]
    return "\n".join(lines)


@dataclass
class Packet:
    wire: bytes
    receiver_text: str
    cpu_seconds: float
    wall_seconds: float
    frame: object = None
    encoding_cpu_seconds: float = 0.0
    decoding_cpu_seconds: float = 0.0
    encoding_wall_seconds: float = 0.0
    decoding_wall_seconds: float = 0.0


def transmit(stage, payload, language=None):
    if (stage is not None and stage not in STAGES) or not isinstance(payload,str) or not payload.strip():
        raise ValueError("Unknown stage or empty payload")
    began_cpu,began_wall = time.thread_time(),time.perf_counter()
    if stage in (None,1):
        if stage==1 and payload.lstrip().startswith(("{","[","```")):
            raise ValueError("Natural-language stage requires prose, not structured JSON or code blocks")
        wire = payload.encode("utf-8")
    elif stage==4:
        wire = vector_encode(strict_json(payload))
    elif stage==5:
        wire = compile_bytecode(payload)
    else:
        if stage==6 and language is None:
            raise ValueError("Shared language has not been agreed")
        source_frame(stage,payload,language)
        wire = payload.encode("utf-8")
    encoding_cpu,encoding_wall = time.thread_time()-began_cpu,time.perf_counter()-began_wall
    began_cpu,began_wall = time.thread_time(),time.perf_counter()
    frame = wire_frame(stage,wire,language)
    received = compact(frame) if stage in (4,5) else wire.decode("utf-8")
    decoding_cpu,decoding_wall = time.thread_time()-began_cpu,time.perf_counter()-began_wall
    return Packet(wire,received,encoding_cpu+decoding_cpu,encoding_wall+decoding_wall,frame,
                  encoding_cpu,decoding_cpu,encoding_wall,decoding_wall)


def instructions(stage, language=None):
    if stage is None:
        return ("Choose your own message content and format in payload. The channel delivers your UTF-8 text unchanged to your peer. "
                "No message representation or communication strategy is prescribed. Keep language empty; setup actions are unavailable.")
    example = empty_frame()
    example["facts"] = [["available", "A1", 0, 1], ["preference", "A1", 0, 2]]
    meaning = ("You may share arbitrary individual facts, team meeting summaries, questions, proposals, acceptances and conflict reasons. "
               "Choose what to share yourself; full raw data or summaries are optional. A team summary concerns only that team's attendees of one meeting at one slot. "
               "Its available value is 1 iff all those attendees are available; its preference is their sum (even when unavailable). "
               "An unavailable reason asserts that the named meeting's attendee cannot attend that slot. An overlap reason asserts the two meetings would share attendees if both used that slot. "
               "Slots are 0..11, availability is 0/1, individual preferences are 0..3, team preference sums are 0..9. "
               "Examples demonstrate syntax only; they are not verified task facts. ")
    meaning += ("Candidate validity is 0/1 and total score is 0..54. Questions can identify a fact, a team summary or a complete candidate. "
                "Recheck references use positive IDs already observed; never invent a future ID. Neither questions nor evaluation assertions are answered by the codec. ")
    syntax = (" Additional predicates: askfact(available,A1,0). asksummary(preference,A,M1,0). askvalid(0,1,2). askscore(0,1,2). valid(0,1,2,1). score(0,1,2,9). recheck(1).")
    if stage == 1:
        return meaning + "Use English natural-language sentences in payload. Do not use JSON, code blocks, or formal programs as the communication format."
    frame = ('Frame: {"kind":"inform|request|propose|accept|reject","facts":[["available|preference","A1|A2|A3|B1|B2|B3",slot,value]],"schedule":{"M1":slot},"requests":["A1"]}. '
             'The four fields above are required. Optional summaries=[["available|preference","A|B","M1|M2|M3",slot,value]] and reasons=[["unavailable","M3","B3",slot],["overlap","M1","M2",slot]]. Optional questions=[["fact","available","A1",0],["summary","preference","A","M1",0],["valid",0,1,2],["score",0,1,2]], evaluations=[["valid",0,1,2,1],["score",0,1,2,9]], references=[1]. A candidate lists M1,M2,M3 slots in order. references asks the peer to recheck already observed message IDs. No other fields. '
             'Collections may be empty. Slots 0..11, individual preferences 0..3, team preferences 0..9, availability 0/1. No duplicate semantic keys within one message. Example: ' + compact(example))
    if stage == 2:
        return meaning + "Put a JSON frame in payload. " + frame
    if stage == 3:
        return meaning + ("Use one predicate per line ending in a period. Begin with exactly one inform()., request()., propose()., accept()., or reject().\n"
                "Facts: available(A1,0,1). preference(A1,0,2). Schedule: at(M1,0). Requests: ask(A1).\n"
                "Summaries: teamavailable(A,M1,0,1). teampreference(A,M1,0,3). Reasons: unavailable(M1,A1,0). overlap(M1,M2,0).\n"
                "Only the documented predicates and IDs are allowed. Choose what to communicate yourself." + syntax)
    if stage == 4:
        return meaning + ("Put a JSON semantic frame in payload for the fixed encoder. Its fixed %d-coordinate float32 vector plus lossless integer reference suffix is sent;" % VECTOR_DIMENSIONS + " the peer sees the inverse-decoded semantic frame. This is a fixed feature-vector codec, not a learned embedding or hidden model state. " + frame)
    if stage == 5:
        return meaning + ("Write bytecode assembly in payload. First line KIND inform|request|propose|accept|reject. Subsequent lines may be AV A1 0 1, PREF A1 0 2, AT M1 0, ASK A1, TAV A M1 0 1, TPREF A M1 0 3, WHY_UNAVAILABLE M1 A1 0, or WHY_OVERLAP M1 M2 0. "
                "Additional instructions: QFACT available A1 0; QSUMMARY preference A M1 0; QVALID 0 1 2; QSCORE 0 1 2; VALID 0 1 2 1; SCORE 0 1 2 9; RECHECK 1. One instruction per line. Compiler transmits actual binary bytecode; the receiver VM constructs a semantic frame. Only these instructions exist. No host code or solving oracle exists.")
    if not language:
        return "First negotiate a dictionary using define_language / accept_language. Meanings: " + compact(MEANINGS)
    return meaning + ("Use this agreed dictionary for predicate names: " + compact(language)
            + ". Message starts with the symbol for one kind and empty parentheses, ending in a period. available/preference take (person,slot,value); at takes (meeting,slot); ask takes (person). One predicate per line. "
            "teamavailable/teampreference take (team,meeting,slot,value); unavailable takes (meeting,person,slot); overlap takes (meeting,other_meeting,slot). "
            + syntax + " Use the agreed symbols for ALL these predicate names. The grammar and IDs remain fixed; only the dictionary is negotiated. Example syntax: " + render_logic(example, language))
