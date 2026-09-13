"""Atomic records, source snapshots, and immutable completed-run manifests."""
import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .contracts import compact, RECORD_VERSION

ROOT = Path(__file__).resolve().parent.parent


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def new_id(label):
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + label + "-" + uuid.uuid4().hex[:12]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def file_hashes(folder):
    folder = Path(folder)
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def source_snapshot(root=ROOT):
    root = Path(root)
    files = [root/"lab.py", root/"AGENTS.md"]
    for directory, pattern in (("experiment", "*.py"), ("scripts", "*.py"), ("config", "*.json"), ("tests", "*.py"), ("tests/fixtures", "*.json")):
        files.extend(sorted((root/directory).glob(pattern)))
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.is_file()}
    return {"files": hashes, "sha256": digest(hashes)}


def seal_run(folder):
    folder = Path(folder)
    if (folder/"seal.json").exists():
        raise ValueError("Run is already sealed")
    write_json(folder/"seal.json", {"version": RECORD_VERSION, "files": file_hashes(folder)})


def verify_seal(folder):
    folder = Path(folder)
    seal = json.loads((folder/"seal.json").read_text())
    if seal["version"] != RECORD_VERSION:
        raise ValueError("Unsupported record version")
    actual = file_hashes(folder)
    actual.pop("seal.json")
    if actual != seal["files"]:
        raise ValueError("Completed run files changed after sealing")
    return seal


class Recorder:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=False)
        (self.folder/"events.jsonl").touch()
        self.sequence = 0

    def event(self, event):
        self.sequence += 1
        with (self.folder/"events.jsonl").open("a", encoding="utf-8") as f:
            f.write(compact({"recorded_at": utcnow(), "sequence": self.sequence, **event}) + "\n")
            f.flush()


def read_events(folder):
    path = Path(folder)/"events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
