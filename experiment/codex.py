"""Small stdio App Server client, pinned to an explicit model and tool-free sessions."""
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from collections import deque

from .protocols import compact, strict_json, MEANINGS

class CodexError(RuntimeError):
    pass


ACTION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["action", "payload", "schedule", "language"],
    "properties": {
        "action": {"type": "string", "enum": ["send", "wait", "submit", "define_language", "accept_language"]},
        "payload": {"type": "string"},
        "schedule": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "required": ["meeting", "slot"], "properties": {
                "meeting": {"type": "string", "enum": ["M1", "M2", "M3"]},
                "slot": {"type": "integer", "minimum": 0, "maximum": 11}}}},
        "language": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "required": ["meaning", "symbol"], "properties": {
                "meaning": {"type": "string", "enum": MEANINGS}, "symbol": {"type": "string"}}}}
    }
}

ISOLATION_CONFIG = {
    "features.shell_tool": False, "features.unified_exec": False,
    "features.code_mode": False, "features.code_mode_host": False,
    "features.multi_agent": False, "features.multi_agent_v2": False,
    "features.apps": False, "features.enable_mcp_apps": False,
    "features.plugins": False, "features.remote_plugin": False,
    "features.memories": False, "features.skill_search": False,
    "features.skip_host_skill_discovery": True,
    "features.tool_suggest": False, "features.sleep_tool": False,
    "features.in_app_browser": False,
    "mcp_servers": {}, "plugins": {}, "web_search": "disabled",
    "tools.view_image": False, "project_doc_max_bytes": 0,
    "project_doc_fallback_filenames": [], "suppress_unstable_features_warning": True
}


def validate_action(a):
    if not isinstance(a, dict) or set(a) != {"action", "payload", "schedule", "language"}:
        raise ValueError("Action requires action, payload, schedule, language")
    if a["action"] not in ACTION_SCHEMA["properties"]["action"]["enum"]:
        raise ValueError("Unknown action")
    if not isinstance(a["payload"], str) or not isinstance(a["schedule"], list) or not isinstance(a["language"], list):
        raise ValueError("Invalid action field type")
    if a["action"] != "send" and a["payload"]:
        raise ValueError("Only send can contain a payload")
    if a["action"] != "submit" and a["schedule"]:
        raise ValueError("Only submit can contain a schedule")
    if a["action"] != "define_language" and a["language"]:
        raise ValueError("Only define_language can contain a dictionary")
    return a


def toml_value(v):
    if v == {}:
        return "{}"
    return json.dumps(v, ensure_ascii=False)


class AppServer:
    def __init__(self, config, event_sink=None):
        self.config = config
        self.event_sink = event_sink or (lambda event: None)
        self.proc = None
        self.counter = 0
        self.queue = queue.Queue()
        self.pending = {}
        self.notifications = deque()
        self.usage = {}
        self.usage_turn_ids = {}
        self.thread_settings = {}
        self.stderr_tail = []
        self.tmp = None
        self.reader = None

    def __enter__(self):
        executable = shutil.which("codex")
        if not executable:
            raise CodexError("Codex CLI not found")
        self.tmp = tempfile.TemporaryDirectory(prefix="agent-communication-")
        args = [executable, "app-server", "--stdio"]
        for key, value in ISOLATION_CONFIG.items():
            args += ["-c", key + "=" + toml_value(value)]
        args += ["-c", "model=" + toml_value(self.config["model"]),
                 "-c", "model_reasoning_effort=" + toml_value(self.config["reasoning_effort"]),
                 "-c", "sqlite_home=" + toml_value(self.tmp.name),
                 "-c", "log_dir=" + toml_value(self.tmp.name),
                 "-c", 'history.persistence="none"']
        # Keep the user's existing login; never read/copy credentials or rewrite global configuration.
        self.proc = subprocess.Popen(args, cwd=self.tmp.name, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1, env=dict(os.environ))
        def read_stdout():
            try:
                for line in self.proc.stdout:
                    try:
                        self.queue.put(json.loads(line))
                    except json.JSONDecodeError:
                        self.queue.put({"_invalid": line[:500]})
            finally:
                self.queue.put({"_closed": True})
        def read_stderr():
            for line in self.proc.stderr:
                self.stderr_tail.append(line.rstrip())
                del self.stderr_tail[:-20]
        self.reader = threading.Thread(target=read_stdout, daemon=True)
        self.reader.start()
        threading.Thread(target=read_stderr, daemon=True).start()
        try:
            self.rpc("initialize", {"clientInfo": {"name": "agent_communication_lab", "version": "1.0.0"},
                                    "capabilities": {"experimentalApi": True}}, timeout=30)
            self.send({"method": "initialized", "params": {}})
        except BaseException:
            self.close()
            raise
        return self

    def send(self, obj):
        if self.proc is None or self.proc.poll() is not None:
            raise CodexError("Codex App Server is not running")
        self.proc.stdin.write(compact(obj) + "\n")
        self.proc.stdin.flush()

    def next_event(self, deadline):
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Codex request timed out")
        try:
            obj = self.queue.get(timeout=remaining)
        except queue.Empty:
            raise TimeoutError("Codex request timed out")
        if obj.get("_closed"):
            raise CodexError("Codex App Server closed: " + "\n".join(self.stderr_tail[-4:]))
        if "_invalid" in obj:
            raise CodexError("Invalid App Server response")
        method = obj.get("method")
        if method == "thread/tokenUsage/updated":
            params = obj["params"]
            self.usage[params["threadId"]] = params["tokenUsage"]
            self.usage_turn_ids[params["threadId"]] = params["turnId"]
        # Do not collect private internal reasoning blocks or authentication events.
        if method and (method.startswith(("turn/", "item/", "thread/tokenUsage", "model/"))):
            record = json.loads(json.dumps(obj))
            if record.get("params", {}).get("item", {}).get("type") == "reasoning":
                record["params"]["item"] = {"id": record["params"]["item"].get("id"), "type": "reasoning"}
            if "reasoning" not in method.lower():
                self.event_sink(record)
        return obj

    def rpc(self, method, params, timeout=30):
        self.counter += 1
        ident = self.counter
        self.send({"id": ident, "method": method, "params": params})
        deadline = time.monotonic()+timeout
        while True:
            event = self.pending.pop(ident, None) or self.next_event(deadline)
            if "id" in event and "method" not in event:
                if event["id"] != ident:
                    self.pending[event["id"]] = event
                    continue
                if "error" in event:
                    raise CodexError(method + ": " + str(event["error"]))
                return event.get("result", {})
            if "id" in event and "method" in event:
                self.send({"id": event["id"], "error": {"code": -32601, "message": "No tools or approvals are available in this experiment"}})
            elif "method" in event:
                self.notifications.append(event)

    def new_session(self, agent, base_instructions, timeout=45):
        cwd = os.path.join(self.tmp.name, agent + "-" + str(self.counter))
        os.makedirs(cwd)
        params = {"model": self.config["model"], "allowProviderModelFallback": False,
                  "cwd": cwd, "ephemeral": True, "environments": [],
                  "selectedCapabilityRoots": [], "runtimeWorkspaceRoots": [],
                  "approvalPolicy": "never", "sandbox": "read-only",
                  "baseInstructions": base_instructions,
                  "developerInstructions": "This is an isolated communication experiment. Use only the supplied inputs and messages. No tools, files, memory, other sessions or external data.",
                  "config": {"model_reasoning_effort": self.config["reasoning_effort"]},
                  "serviceTier": self.config["service_tier"],
                  "personality": "none", "experimentalRawEvents": False}
        result = self.rpc("thread/start", params, timeout)
        if result.get("model") != self.config["model"]:
            raise CodexError("Requested model was not confirmed: " + str(result.get("model")))
        effort = result.get("reasoningEffort")
        if effort != self.config["reasoning_effort"]:
            raise CodexError("Requested reasoning effort was not confirmed: " + str(effort))
        sources = result.get("instructionSources", [])
        if sources:
            raise CodexError("Unexpected instruction sources in isolated session: " + str(sources))
        thread_id = result["thread"]["id"]
        self.thread_settings[thread_id] = {k: result.get(k) for k in ("model", "modelProvider", "reasoningEffort", "serviceTier", "instructionSources")}
        self.event_sink({"method": "experiment/session", "params": {"agent": agent, "thread_id": thread_id, **self.thread_settings[thread_id]}})
        return thread_id

    def turn(self, thread_id, text, timeout=None):
        timeout = timeout or self.config["turn_timeout_seconds"]
        deadline = time.monotonic()+timeout
        result = self.rpc("turn/start", {"threadId": thread_id, "model": self.config["model"],
                    "effort": self.config["reasoning_effort"], "serviceTier": self.config["service_tier"],
                    "environments": [], "runtimeWorkspaceRoots": [],
                    "input": [{"type": "text", "text": text}], "outputSchema": ACTION_SCHEMA}, timeout)
        turn_id = result["turn"]["id"]
        messages = []
        try:
            while True:
                event = self.notifications.popleft() if self.notifications else self.next_event(deadline)
                method, params = event.get("method", ""), event.get("params", {})
                if "id" in event and "method" in event:
                    self.send({"id": event["id"], "error": {"code": -32601, "message": "Tools disabled"}})
                    raise CodexError("Unexpected tool/approval request: " + method)
                if method == "model/rerouted":
                    raise CodexError("Model was rerouted; fixed-model condition violated")
                if method == "error" or (method.startswith("turn/") and params.get("error")):
                    raise CodexError(str(params.get("error", params)))
                if params.get("threadId", thread_id) != thread_id:
                    continue
                item = params.get("item", {})
                if method == "item/started" and item.get("type") in {"commandExecution", "fileChange", "mcpToolCall", "collabToolCall", "webSearch", "imageView", "dynamicToolCall"}:
                    raise CodexError("Unexpected tool in tool-free session: " + item["type"])
                if method == "item/completed" and item.get("type") == "agentMessage":
                    messages.append(item.get("text", ""))
                if method == "turn/completed" and params.get("turn", {}).get("id") == turn_id:
                    if params["turn"].get("status") != "completed":
                        raise CodexError("Turn failed: " + str(params["turn"].get("error")))
                    if not messages:
                        messages = [x.get("text", "") for x in params["turn"].get("items", []) if x.get("type") == "agentMessage"]
                    if not messages:
                        raise CodexError("No final structured response")
                    # Synchronize local event delivery before using cumulative token totals.
                    try:
                        self.rpc("thread/read", {"threadId": thread_id, "includeTurns": False}, min(5, max(.1, deadline-time.monotonic())))
                    except (CodexError, TimeoutError):
                        pass
                    if self.usage_turn_ids.get(thread_id) != turn_id:
                        self.usage.pop(thread_id, None)
                    return validate_action(strict_json(messages[-1]))
        except BaseException:
            try:
                self.rpc("turn/interrupt", {"threadId": thread_id, "turnId": turn_id}, 5)
            except Exception:
                pass
            raise

    def close(self):
        if self.proc is not None:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=5)
            for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                try:
                    stream.close()
                except Exception:
                    pass
            self.proc = None
        if self.tmp:
            self.tmp.cleanup()
            self.tmp = None

    def __exit__(self, *args):
        self.close()
