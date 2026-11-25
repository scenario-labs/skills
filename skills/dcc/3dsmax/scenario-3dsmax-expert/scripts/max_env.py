#!/usr/bin/env python3
"""max_env: find which channel to 3ds Max exists on this machine (runner side, any OS).

    doctor() -> {os, installs, batch_exe, mcp_ports, bridge, channel, notes, env}

channel is one of "bridge", "mcp-safe", "batch", "handoff":
- bridge: a community MCP bridge answers on a known port (or MAX_BRIDGE=host:port is set).
  Python and arbitrary MAXScript are allowed; nothing asks the user before a script runs.
- mcp-safe: the Autodesk 3ds Max MCP server (2027.3, Tech Preview) answers on 127.0.0.1:27200-27209.
  The agent itself reaches it only through an MCP client that supports MCP Apps (Autodesk: it
  "doesn't work with Claude Code in the terminal"). An open port proves only that 3ds Max runs it.
- batch: 3dsmaxbatch.exe exists (Windows: MAX_BATCH_EXE, PATH or an install). No UI, no viewport capture, uses a license.
- handoff: none of the above (for example macOS or Linux): write a script, the user runs it with
  Scripting > Run Script and sends back the result file and captures.
MAX_CHANNEL forces the answer. The probe only opens TCP connections on 127.0.0.1; it sends nothing,
reads no token and installs nothing. Ports and paths are from the saved 2027.3 docs and from
public bridge READMEs (bridge ports are [added] defaults, override with MAX_BRIDGE).
"""
from __future__ import annotations

__version__ = "0.1.0"

import json
import os
import platform
import shutil
import socket
from pathlib import Path

MCP_PORTS = range(27200, 27210)          # Autodesk 3ds Max MCP server, lowest free port per instance
BRIDGE_PORTS = {47635: "Max Ultra MCP", 20228: "max-mcp (TCP)"}  # [added] seen in public material
YEARS = range(2030, 2023, -1)
ENV_KEYS = ("ADSK_3DSMAX_MCP_LEVEL", "ADSK_3DSMAX_ASSISTANT_LEVEL", "ADSK_3DSMAX_MCP_SKIP_PROPOSE",
            "ADSK_3DSMAX_ASSISTANT_SKIP_PROPOSE", "MAX_CHANNEL", "MAX_BRIDGE", "MAX_BATCH_EXE", "MAX_ROOT")
LEVELS = {0: "Off", 1: "Read-only", 2: "Read/write (undo and redo only)", 10: "Safe MAXScript",
          20: "Safe MAXScript + Python (admin only)"}


def _open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def find_installs(roots=None) -> list[dict]:
    """Standard install folders (C:\\Program Files\\Autodesk\\3ds Max <year>) plus MAX_ROOT."""
    cands = []
    if os.environ.get("MAX_ROOT"):
        cands.append(Path(os.environ["MAX_ROOT"]))
    for base in roots or [os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles"), r"C:\Program Files"]:
        if base:
            cands += [Path(base) / "Autodesk" / f"3ds Max {y}" for y in YEARS]
    seen, out = set(), []
    for c in cands:
        key = str(c).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            exists = c.is_dir()
        except OSError:
            exists = False
        if not exists:
            continue
        batch = c / "3dsmaxbatch.exe"
        out.append({"root": str(c), "year": c.name.split()[-1] if c.name[-4:].isdigit() else None,
                    "max_exe": str(c / "3dsmax.exe") if (c / "3dsmax.exe").exists() else None,
                    "batch_exe": str(batch) if batch.exists() else None})
    return out


def probe_mcp(host: str = "127.0.0.1") -> list[int]:
    return [p for p in MCP_PORTS if _open(host, p)]


def probe_bridge(host: str = "127.0.0.1"):
    env = os.environ.get("MAX_BRIDGE")
    if env:
        h, _, p = env.rpartition(":")
        h = h or host
        return {"host": h, "port": int(p), "name": "MAX_BRIDGE", "open": _open(h, int(p))}
    for port, name in BRIDGE_PORTS.items():
        if _open(host, port):
            return {"host": host, "port": port, "name": name, "open": True}
    return None


def doctor() -> dict:
    osname = platform.system()
    installs = find_installs() if osname == "Windows" or os.environ.get("MAX_ROOT") else []
    on_path = (shutil.which("3dsmaxbatch") or shutil.which("3dsmaxbatch.exe")) if osname == "Windows" else None
    batch = (os.environ.get("MAX_BATCH_EXE") or on_path   # same order as max_batch.find_exe()
             or next((i["batch_exe"] for i in installs if i["batch_exe"]), None))
    ports = probe_mcp()
    bridge = probe_bridge()
    env = {k: os.environ[k] for k in ENV_KEYS if k in os.environ}
    notes = []
    forced = os.environ.get("MAX_CHANNEL")
    if forced:
        channel = forced
        notes.append(f"channel forced by MAX_CHANNEL={forced}")
    elif bridge and bridge.get("open"):
        channel = "bridge"
    elif ports:
        channel = "mcp-safe"
    elif batch:
        channel = "batch"
    else:
        channel = "handoff"
    if ports:
        notes.append(f"Autodesk 3ds Max MCP server listening on {ports}; one port per running instance. "
                     "Connect through an MCP client with MCP Apps support; every script is proposed "
                     "to the user before it runs.")
    if "ADSK_3DSMAX_MCP_LEVEL" in env:
        try:
            lvl = int(env["ADSK_3DSMAX_MCP_LEVEL"])
            notes.append(f"admin MCP level {lvl} ({LEVELS.get(lvl, 'unknown')}); read at startup only")
        except ValueError:
            pass
    if osname != "Windows" and not forced:
        notes.append("3ds Max runs on Windows only: from this machine use handoff, or a remote Windows "
                     "machine reached through a bridge or an MCP client there")
    if channel == "batch":
        notes.append("batch: no viewport and no dialogs; renders and file work only; uses a license")
    if channel == "handoff":
        notes.append("handoff: write the script with max_wrap, ask the user to run Scripting > Run Script "
                     "and to send back the result JSON and captures")
    return {"os": osname, "installs": installs, "batch_exe": batch, "mcp_ports": ports,
            "bridge": bridge, "channel": channel, "notes": notes, "env": env}


if __name__ == "__main__":
    print(json.dumps(doctor(), indent=2))
