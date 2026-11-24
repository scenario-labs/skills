#!/usr/bin/env python3
"""max_batch: run a script in 3ds Max without the UI through 3dsmaxbatch.exe (Windows only).

Runner side: plain Python 3.10+, never imports pymxs. Commands are argument lists, never shell
strings, so Windows paths with spaces survive. Checked against scripting-pipeline__3dsmaxbatch-2020.md
(options, -mxsString/-mxsValue, exit codes). Status of the batch run itself: not yet run in 3ds Max.

    command(script, scene=None, args=None, exe=None, listener_log=None, log=None,
            verbosity=3, dialog_monitor=True) -> list[str]
    run_batch(script, scene=None, args=None, timeout=1800, log_dir=None, exe=None) -> dict

`script` is a .ms/.mxs/.py file, or code text (a string containing a newline), which run_batch
writes to log_dir first. Code that came from max_wrap.wrap() reports through result_path, which
run_batch passes as -mxsString result_path:"..." and reads back after the run.

Batch facts the caller must know: it uses a license, it has no viewport (capture.viewport fails,
renders work), dialogs are suppressed or logged with -dm on, and MCP is not available in batch.
The scene file passed with -sceneFile is opened, never saved, unless the script saves it: save
under a new name (_v002), never over the user's file.
"""
from __future__ import annotations

__version__ = "0.1.0"

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path, PureWindowsPath

EXIT_CODES = {
    0: "ok",
    -100: "bad arguments to 3dsmaxbatch",
    -110: "3ds Max could not start",
    -120: "communication with 3ds Max lost",
    -130: "3ds Max error while executing the script (see the logs)",
}


def _mxs_string(value: str) -> str:
    """A MAXScript string literal. Verbatim @"..." when the value has a backslash and no quote."""
    s = os.fspath(value)
    if "\\" in s and '"' not in s:
        return '@"' + s + '"'
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _arg_pairs(args) -> list[str]:
    # Each pair is ONE argv item holding literal quotes (string1:"Hello"). subprocess quotes it for
    # the Windows command line. Whether 3dsmaxbatch reads argv or the raw command line is not
    # documented: if a key arrives without its quotes, compare with the doc's typed example.  # [verify]
    out: list[str] = []
    for key, value in (args or {}).items():
        if not str(key).isidentifier():
            raise ValueError(f"argument name {key!r} must be a MAXScript identifier")
        if isinstance(value, bool):
            out += ["-mxsValue", f'{key}:"{"true" if value else "false"}"']
        elif isinstance(value, (int, float)):
            out += ["-mxsValue", f'{key}:"{value!r}"']  # the doc: the value must be in quotation marks
        else:
            out += ["-mxsString", f"{key}:{_mxs_string(str(value))}"]
    return out


def find_exe() -> str | None:
    """3dsmaxbatch.exe from MAX_BATCH_EXE, PATH, or the newest standard install."""
    env = os.environ.get("MAX_BATCH_EXE")
    if env:
        return env
    hit = shutil.which("3dsmaxbatch") or shutil.which("3dsmaxbatch.exe")
    if hit:
        return hit
    try:
        from max_env import find_installs  # same folder
    except ImportError:
        return None
    for inst in find_installs():
        if inst.get("batch_exe"):
            return inst["batch_exe"]
    return None


def command(script, scene=None, args=None, exe=None, listener_log=None, log=None,
            verbosity: int = 3, dialog_monitor: bool = True) -> list[str]:
    """The argument list for one 3dsmaxbatch.exe call (pass it to subprocess without shell=True)."""
    exe = exe or find_exe() or "3dsmaxbatch.exe"
    cmd = [os.fspath(exe), os.fspath(script)]
    if scene:
        cmd += ["-sceneFile", os.fspath(scene)]
    if listener_log:
        cmd += ["-listenerlog", os.fspath(listener_log)]
    if log:
        cmd += ["-log", os.fspath(log)]
    if verbosity is not None:
        if not 0 <= int(verbosity) <= 5:
            raise ValueError("verbosity is 0..5")
        cmd += ["-v", str(int(verbosity))]
    cmd += ["-dm", "on" if dialog_monitor else "off"]
    cmd += _arg_pairs(args)
    return cmd


def _read(path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def run_batch(script, scene=None, args=None, timeout: int = 1800, log_dir=None, exe=None) -> dict:
    """Run once, wait, return {ok, exit_code, meaning, result, stdout, listener_log, log, command, seconds}."""
    log_dir = Path(log_dir) if log_dir else Path(tempfile.mkdtemp(prefix="maxbatch_"))
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    text = os.fspath(script) if not isinstance(script, Path) else None
    if text is not None and "\n" in text:
        is_py = re.search(r"(?m)^\s*(import \w|from \w[\w.]* import |def \w|class \w)", text) is not None
        suffix = ".py" if is_py else ".ms"
        path = log_dir / f"job_{stamp}{suffix}"
        path.write_text(text, encoding="utf-8")
        script = path
    result_path = log_dir / f"result_{stamp}.json"
    listener = log_dir / f"listener_{stamp}.log"
    logf = log_dir / f"batch_{stamp}.log"
    all_args = dict(args or {})
    all_args.setdefault("result_path", str(result_path))
    cmd = command(script, scene, all_args, exe=exe, listener_log=listener, log=logf)
    if not (exe or find_exe()) or (os.name != "nt" and not exe):
        return {"ok": False, "exit_code": None, "meaning": "3dsmaxbatch.exe not found (Windows only)",
                "result": None, "stdout": "", "listener_log": "", "log": "", "command": cmd, "seconds": 0}
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        code, out = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        code, out = None, f"timeout after {timeout} s: {exc}"
    if isinstance(code, int) and code > 2**31:  # Windows reports negative codes as unsigned
        code -= 2**32
    result = None
    if result_path.exists():
        try:
            result = json.loads(_read(result_path))
        except ValueError:
            result = {"ok": False, "error": "result file is not JSON", "raw": _read(result_path)[:2000]}
    meaning = EXIT_CODES.get(code, "timeout" if code is None else f"user exit code {code}")
    ok = code == 0 and (result is None or bool(result.get("ok", True)))
    return {"ok": ok, "exit_code": code, "meaning": meaning, "result": result, "stdout": out[-4000:],
            "listener_log": _read(listener)[-4000:], "log": _read(logf)[-4000:], "command": cmd,
            "seconds": round(time.time() - t0, 1)}


def as_windows(path) -> str:
    """Render a path with backslashes (for logs and reports; the command list does not need it)."""
    return str(PureWindowsPath(os.fspath(path)))


if __name__ == "__main__":  # python max_batch.py script.ms [scene.max] [key=value ...]
    import sys
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        raise SystemExit(2)
    scene = a[1] if len(a) > 1 and "=" not in a[1] else None
    kv = dict(x.split("=", 1) for x in a[1:] if "=" in x)
    print(json.dumps(run_batch(a[0], scene, kv), indent=2))
