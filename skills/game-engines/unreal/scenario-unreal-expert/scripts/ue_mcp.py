"""
ue_mcp: a small MCP client for Epic's Unreal MCP server (system python3, stdlib only).

STATUS: run against Unreal Engine 5.8.3 (macOS, launcher build) on 2026-10-21: initialize,
tools/list, list_toolsets, describe_toolset, call_tool, error shapes and the catalog snapshot.
Everything else in this file is logic on top of those calls.

What the live server does (5.8.3, plugins ModelContextProtocol + AllToolsets):
  - `tools/list` returns exactly three tools: list_toolsets, describe_toolset, call_tool.
  - Every tool result is `{"content": [{"type": "text", "text": "<json>"}], "isError": bool}`;
    the text of a toolset tool is JSON with the value under `returnValue`.
  - Toolset names are `Module.Class` for C++ toolsets, from the class path /Script/<Module>
    (NiagaraToolsets.NiagaraToolset_System), and the Python module path for Python toolsets
    (editor_toolset.toolsets.actor.ActorTools).
    `describe_toolset` lists tools with fully qualified names; `call_tool` takes the short name.
  - The agent's own MCP client (from .mcp.json) is the normal channel. Use this module for
    scripted health checks, catalog snapshots and tests, or when no MCP client is available.

Library:
  import ue_mcp as M
  m = M.Mcp()                       # http://127.0.0.1:8000/mcp (ModelContextProtocol default)
  m.connect()
  m.toolsets()                      # [(name, description), ...]
  m.describe("editor_toolset.toolsets.actor.ActorTools")   # dict: name, tools [{name, inputSchema}]
  r = m.call("ToolsetRegistry.AgentSkillToolset", "ListSkills"); r.ok, r.value
  M.snapshot(m, "catalog/5.8.3")    # one JSON per toolset + index.json (sizes in tokens)
  M.diff("catalog/5.8.3", "catalog/5.8.4")   # added, removed, changed toolsets and tools
  M.reachable(m)                    # True only after a real read-only call succeeds
"""

__version__ = "0.2.1"  # Unreal Engine Expert Skills v0.2.1

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

MCP_URL = "http://127.0.0.1:8000/mcp"
MCP_PROTOCOL = "2025-06-18"


class McpError(RuntimeError):
    """Transport or protocol failure (not a tool reporting isError)."""


def parse_sse(text):
    """Parse a text/event-stream body into a list of decoded JSON `data:` payloads."""
    events = []
    for line in text.splitlines():
        if line.startswith("data:"):
            raw = line[5:].strip()
            if raw:
                try:
                    events.append(json.loads(raw))
                except ValueError:
                    continue  # not JSON, so not a JSON-RPC message: skip the line
    return events


class Result(object):
    """One tool result. ok is False when the server set isError or the call failed."""

    def __init__(self, raw):
        self.raw = raw or {}
        res = self.raw.get("result", {}) if isinstance(self.raw, dict) else {}
        self.is_error = bool(res.get("isError")) or "error" in self.raw
        parts = res.get("content") or []
        self.text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))
        if "error" in self.raw and not self.text:
            self.text = json.dumps(self.raw["error"])
        self.json = None
        try:
            self.json = json.loads(self.text)
        except ValueError:
            self.json = None  # plain-text tool output: keep it in .text

    @property
    def ok(self):
        return not self.is_error

    @property
    def value(self):
        """The `returnValue` of a toolset tool when the text is JSON, else the parsed JSON or text."""
        if isinstance(self.json, dict) and "returnValue" in self.json:
            return self.json["returnValue"]
        return self.json if self.json is not None else self.text


class Mcp(object):
    """Streamable-HTTP MCP client for one server. Not thread safe: use one per thread."""

    def __init__(self, url=MCP_URL, timeout=120.0, client="ue_mcp"):
        self.url, self.timeout, self.client = url, timeout, client
        self.session = None
        self._id = 0
        self.last_ms = 0.0
        self.server_info = None

    def _post(self, msg, retry=True):
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": MCP_PROTOCOL}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, data=json.dumps(msg).encode("utf-8"),
                                     headers=headers, method="POST")
        started = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    self.session = sid
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:  # before URLError, its base class
            try:
                detail = exc.read().decode("utf-8", "replace")
            except OSError:
                detail = ""
            if exc.code == 404 and self.session and retry:
                # The server dropped the session (an editor restart does): the MCP spec says
                # start a new one with initialize, then send the request again.
                self.connect()
                return self._post(msg, retry=False)
            raise McpError("HTTP %d from %s: %s" % (exc.code, self.url, detail[:300] or exc.reason))
        except (urllib.error.URLError, OSError) as exc:
            raise McpError("cannot reach %s: %s (is the editor running with the MCP server "
                           "started? ModelContextProtocol.StartServer)" % (self.url, exc))
        self.last_ms = (time.time() - started) * 1000.0
        if "id" not in msg:
            return None
        if "text/event-stream" in ctype:
            for ev in parse_sse(body):
                if isinstance(ev, dict) and ev.get("id") == msg["id"]:
                    return ev
            raise McpError("no response for id %s in the event stream" % msg["id"])
        if not body.strip():
            return None
        try:
            return json.loads(body)
        except ValueError:
            raise McpError("not JSON from %s: %s" % (self.url, body[:300]))

    def rpc(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        resp = self._post(msg)
        if resp is None:
            raise McpError("empty response to %s" % method)
        return resp

    def connect(self):
        self.session = None  # initialize never carries a session id
        resp = self.rpc("initialize", {"protocolVersion": MCP_PROTOCOL, "capabilities": {},
                                       "clientInfo": {"name": self.client, "version": __version__}})
        if "error" in resp:
            raise McpError("initialize failed: %s" % resp["error"])
        self.server_info = resp.get("result", {})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, retry=False)
        return self.server_info

    def top_level_tools(self):
        """Names of `tools/list`: three meta-tools when tool search is on (the default)."""
        resp = self.rpc("tools/list")
        return [t["name"] for t in resp.get("result", {}).get("tools", [])]

    def call_top(self, name, arguments=None):
        return Result(self.rpc("tools/call", {"name": name, "arguments": arguments or {}}))

    def toolsets(self):
        """[(name, description)] from list_toolsets. Names are `Module.Class` or a module path.
        A toolset with no description is listed as `- Name` and comes back with ""."""
        res = self.call_top("list_toolsets")
        if not res.ok:
            raise McpError("list_toolsets failed: %s" % res.text[:200])
        out = []
        for m in re.finditer(r"^- (\w+\.[\w.]+)(?::|[ \t]*$)(.*?)(?=^- \w+\.[\w.]+(?::|[ \t]*$)|\Z)",
                             res.text, re.M | re.S):
            out.append((m.group(1), m.group(2).strip()))
        return out

    def describe(self, toolset):
        """Parsed describe_toolset payload: {name, version, description, tools: [...]}."""
        res = self.call_top("describe_toolset", {"toolset_name": toolset})
        if not res.ok or not isinstance(res.json, dict):
            raise McpError("describe_toolset(%s) failed: %s" % (toolset, res.text[:200]))
        return res.json

    def call(self, toolset, tool, arguments=None):
        """Call one toolset tool by its SHORT name. Check `.ok` before using `.value`."""
        return Result(self.rpc("tools/call", {"name": "call_tool", "arguments": {
            "toolset_name": toolset, "tool_name": tool, "arguments": arguments or {}}}))


def reachable(m):
    """True only when a read-only call succeeds now. A proxy session or a cached catalog does
    not prove the editor is up; this does."""
    try:
        return m.call_top("list_toolsets").ok
    except McpError:
        return False


def _tokens(nbytes):
    return int(nbytes / 4)  # rough: four bytes per token for JSON schemas


def snapshot(m, outdir):
    """Write one describe_toolset JSON per toolset plus index.json. Returns the index.

    The index lists, per toolset, its tools and the payload size in tokens (estimate), so
    a skill can warn before describing a very large toolset. Re-run after enabling plugins."""
    os.makedirs(outdir, exist_ok=True)
    index = {"engine_note": "run on the editor that served it; compare with diff()",
             "taken": time.strftime("%Y-%m-%d %H:%M:%S"), "toolsets": {}}
    for name, desc in m.toolsets():
        try:
            d = m.describe(name)
        except McpError as exc:
            index["toolsets"][name] = {"error": str(exc)[:200]}
            continue
        blob = json.dumps(d, indent=1, sort_keys=True)
        with open(os.path.join(outdir, name + ".json"), "w") as fh:
            fh.write(blob)
        tools = d.get("tools", [])
        index["toolsets"][name] = {
            "description": desc.split("\n")[0][:160], "tools": len(tools),
            "tool_names": sorted(t.get("name", "").split(".")[-1] for t in tools),
            "payload_tokens": _tokens(len(blob)),
            "sha": hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]}
    with open(os.path.join(outdir, "index.json"), "w") as fh:
        json.dump(index, fh, indent=1, sort_keys=True)
    return index


def diff(old_dir, new_dir):
    """Compare two snapshots: {added, removed, changed: {toolset: {added, removed}}}."""
    def load(d):
        with open(os.path.join(d, "index.json")) as fh:
            return json.load(fh)["toolsets"]
    a, b = load(old_dir), load(new_dir)
    out = {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)), "changed": {}}
    for name in sorted(set(a) & set(b)):
        if a[name].get("sha") != b[name].get("sha"):
            ta, tb = set(a[name].get("tool_names", [])), set(b[name].get("tool_names", []))
            out["changed"][name] = {"added": sorted(tb - ta), "removed": sorted(ta - tb)}
    return out


def big_toolsets(index, over_tokens=4000):
    """[(name, tokens)] of toolsets whose describe payload is large; describe these only when
    the task needs them, and prefer `describe_toolset` on the narrowest toolset."""
    rows = [(n, v.get("payload_tokens", 0)) for n, v in index["toolsets"].items()]
    return sorted([r for r in rows if r[1] >= over_tokens], key=lambda r: -r[1])
