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

from .contracts import (compact, strict_json, action_schema, validate_action, CodexError,
                        ActionFormatError, Cancelled, RECORD_VERSION)

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


def toml_value(v):
    if v == {}:
        return "{}"
    return json.dumps(v, ensure_ascii=False)


class AppServer:
    def __init__(self, config, event_sink=None, cancel_event=None):
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
        self.cancel_event = cancel_event or threading.Event()
        self.last_response = None
        self.last_turn_id = None
        self.partial_usage = {}
        self.post_response_error = None
        self.post_response_status = None

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
            self.rpc("initialize", {"clientInfo": {"name": "agent_communication_lab", "version": RECORD_VERSION},
                                    "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized", "params": {}})
        except BaseException:
            self.close()
            raise
        return self

    def send(self, obj):
        if self.post_response_error:
            raise CodexError(self.post_response_error)
        if self.proc is None or self.proc.poll() is not None:
            raise CodexError("Codex App Server is not running")
        self.proc.stdin.write(compact(obj) + "\n")
        self.proc.stdin.flush()

    def next_event(self):
        # Polling checks cancellation/process state, never imposes a response deadline.
        while True:
            if self.cancel_event.is_set():
                raise Cancelled("User cancelled the run")
            try:
                obj = self.queue.get(timeout=0.25)
                break
            except queue.Empty:
                if self.proc is not None and self.proc.poll() is not None:
                    raise CodexError("Codex App Server process exited")
        if obj.get("_closed"):
            raise CodexError("Codex App Server closed: " + "\n".join(self.stderr_tail[-4:]))
        if "_invalid" in obj:
            raise CodexError("Invalid App Server response")
        method = obj.get("method", "")
        if method == "thread/tokenUsage/updated":
            params = obj["params"]
            self.usage[params["threadId"]] = params["tokenUsage"]
            self.partial_usage[params["threadId"]] = params["tokenUsage"]
            self.usage_turn_ids[params["threadId"]] = params["turnId"]
        def sanitize(value):
            if isinstance(value, dict):
                if value.get("type") == "reasoning":
                    return {"id": value.get("id"), "type": "reasoning"}
                return {k:sanitize(v) for k,v in value.items()}
            if isinstance(value, list):
                return [sanitize(v) for v in value]
            return value
        if method.startswith(("turn/", "item/", "thread/tokenUsage", "model/")) or method == "error":
            if "reasoning" not in method.lower():
                self.event_sink(sanitize(obj))
        return obj

    def rpc(self, method, params):
        self.counter += 1
        ident = self.counter
        self.send({"id": ident, "method": method, "params": params})
        while True:
            event = self.pending.pop(ident, None)
            if event is None:
                event = self.next_event()
            if "id" in event and "method" not in event:
                if event["id"] != ident:
                    self.pending[event["id"]] = event
                    continue
                if "error" in event:
                    raise CodexError(method + ": " + str(event["error"]))
                return event.get("result", {})
            if "id" in event and "method" in event:
                self.send({"id": event["id"], "error": {"code": -32601, "message": "Tools disabled"}})
                raise CodexError("Unexpected tool/approval request: " + event["method"])
            if event.get("method") == "model/rerouted":
                raise CodexError("Model rerouted; fixed-model condition violated")
            if event.get("method") == "error":
                raise CodexError(str(event.get("params")))
            if "method" in event:
                self.notifications.append(event)

    def new_session(self, agent, base_instructions):
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
        result = self.rpc("thread/start", params)
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

    def turn(self, thread_id, text, schema=None, request_id=None):
        self.last_response = None
        self.last_turn_id = None
        # Retain prior totals only as a labelled partial amount, never as this call's total.
        self.usage.pop(thread_id, None)
        result = self.rpc("turn/start", {"threadId": thread_id, "model": self.config["model"],
                    "effort": self.config["reasoning_effort"], "serviceTier": self.config["service_tier"],
                    "environments": [], "runtimeWorkspaceRoots": [],
                    "input": [{"type": "text", "text": text}], "outputSchema": schema or action_schema()})
        turn_id = self.last_turn_id = result["turn"]["id"]
        self.event_sink({"method":"experiment/turn_started", "params":{
            "request_id":request_id, "thread_id":thread_id, "turn_id":turn_id}})
        messages, deferred = [], []
        try:
            while True:
                event = self.notifications.popleft() if self.notifications else self.next_event()
                method, params = event.get("method", ""), event.get("params", {})
                if "id" in event and "method" not in event:
                    self.pending[event["id"]] = event
                    continue
                if "id" in event and "method" in event:
                    self.send({"id": event["id"], "error": {"code": -32601, "message": "Tools disabled"}})
                    raise CodexError("Unexpected tool/approval request: " + method)
                if method == "model/rerouted":
                    raise CodexError("Model was rerouted; fixed-model condition violated")
                if params.get("threadId", thread_id) != thread_id or (params.get("turnId") and params["turnId"] != turn_id):
                    deferred.append(event)
                    continue
                if method == "error" or (method.startswith("turn/") and params.get("error")):
                    raise CodexError(str(params.get("error", params)))
                item = params.get("item", {})
                if method in ("item/started", "item/completed") and item.get("type") in {"commandExecution", "fileChange", "mcpToolCall", "collabToolCall", "webSearch", "imageView", "dynamicToolCall"}:
                    raise CodexError("Unexpected tool in tool-free session: " + item["type"])
                if method == "item/completed" and item.get("type") == "agentMessage":
                    messages.append(item.get("text", ""))
                if method == "turn/completed" and params.get("turn", {}).get("id") == turn_id:
                    if params["turn"].get("status") != "completed":
                        raise CodexError("Turn failed: " + str(params["turn"].get("error")))
                    if not messages:
                        messages = [x.get("text", "") for x in params["turn"].get("items", []) if x.get("type") == "agentMessage"]
                    if not messages:
                        raise ActionFormatError("response_parse", "No final response", "")
                    self.last_response = messages[-1]
                    # Consume only already queued events. A usage lookup must not stall or discard a valid response.
                    while not self.queue.empty():
                        try:
                            late = self.next_event()
                        except (CodexError,Cancelled) as exc:
                            self.post_response_error = str(exc)
                            self.post_response_status = "cancelled" if isinstance(exc,Cancelled) else "infrastructure_error"
                            self.event_sink({"method":"experiment/post_response_error","params":{
                                "request_id":request_id,"thread_id":thread_id,"turn_id":turn_id,"error":str(exc)}})
                            break
                        late_method = late.get("method", "")
                        late_item = late.get("params",{}).get("item",{})
                        if late_method == "model/rerouted" or (late_method in ("item/started","item/completed") and
                            late_item.get("type") in {"commandExecution","fileChange","mcpToolCall","collabToolCall","webSearch","imageView","dynamicToolCall"}):
                            raise CodexError("Fixed-model/tool-free condition violated after response: " + late_method)
                        deferred.append(late)
                    if self.usage_turn_ids.get(thread_id) != turn_id:
                        self.usage.pop(thread_id, None)
                    try:
                        return strict_json(self.last_response)
                    except (ValueError, TypeError) as exc:
                        raise ActionFormatError("response_parse", str(exc), self.last_response) from exc
        except (Cancelled, KeyboardInterrupt, CodexError):
            # Fire-and-forget cancellation; waiting for its acknowledgement would impose another deadline.
            try:
                self.counter += 1
                self.send({"id":self.counter, "method":"turn/interrupt", "params":{"threadId":thread_id, "turnId":turn_id}})
            except (CodexError, OSError):
                pass
            raise
        finally:
            self.notifications.extend(deferred)

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
