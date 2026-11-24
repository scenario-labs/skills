#!/usr/bin/env python3
"""max_wrap: turn a chunk of pymxs or MAXScript into one self-contained, reportable script.

Runner side: plain Python 3.10+, any OS, never imports pymxs. The generated script runs inside
3ds Max. Status of the generated code: not yet run in 3ds Max; checked against the saved 2027 docs.

    wrap(code, lang="python", kit=(), result_path=None, label="agent change", undo=True,
         kit_dirs=None) -> str

kit: each entry is a lead module name (Python: result, stats, capture, audit, xio; MAXScript:
result, stats, audit, capture), a path to a .py file (lang="python") or .ms file
(lang="maxscript"), or a bare name found as <name>.py or <name>.ms (or mxs/<name>.ms) in one of
kit_dirs. Sibling skills pass their own helpers this way, for example
kit=["audit", "maxkit_archviz"], kit_dirs=[<their scripts folder>]. In Python each file is
inlined as a module object bound to its file stem (a global of the chunk, also importable as
`import <stem>` and `from maxkit import <stem>`); lead modules it imports (`from maxkit import
stats`) are added automatically. In MAXScript the file's functions are inlined in the same outer
block; lead twins it calls (mxk_stats_*, mxk_audit_*, mxk_capture_*) are added automatically.

The chunk runs inside ONE undo record and the result protocol: the chunk sets `result` (and may
call `log(...)` in Python, `mxk_note "..."` in MAXScript); the wrapper builds {ok, result, error, log, max_version}, writes it as JSON to
result_path (Python form; MAXScript form only if result_path is given) and prints one line
"MXK_RESULT <json>". The MAXScript form also returns the JSON text as the script's value, so an
mcp-safe client sees it even if Safe mode refuses the file write (undocumented).

lang="python": for batch, bridge and handoff. kit names (result, stats, audit, capture, xio) are
inlined from scripts/maxkit/ and bound as globals of the chunk (audit.all(), stats.snapshot()...).
When result_path is None, the Python form reads `result_path` from maxOps.mxsCmdLineArgs
(max_batch passes it with -mxsString).

lang="maxscript": the form to propose through mcp-safe (no Python, no dotNet, no file delete or
copy, no INI writes). kit names map to scripts/maxkit/mxs/*.ms (result, stats, audit, capture);
their functions are named mxk_<module>_<fn> (mxk_stats_snapshot, mxk_audit_all, ...).
"""
from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path

__version__ = "0.1.0"

HERE = Path(__file__).resolve().parent
KIT_DIR = HERE / "maxkit"
MXS_DIR = KIT_DIR / "mxs"
PY_KIT = ("result", "stats", "capture", "audit", "xio")  # load order respects dependencies
PY_DEPS = {"audit": ("stats",), "xio": ("stats", "capture")}
MXS_KIT = ("result", "stats", "audit", "capture")
_PY_IMPORT = re.compile(r"\bmaxkit\.(\w+)|\bfrom\s+maxkit\s+import\s+([\w\s,()]+)")
_MXS_CALL = re.compile(r"\bmxk_(stats|audit|capture)_\w+")


def _resolve(entry, ext: str, kit_dirs) -> tuple[str, Path | None]:
    """(module name, source path) for one kit entry. Path None means a lead module."""
    lead = PY_KIT if ext == ".py" else MXS_KIT
    raw = os.fspath(entry)
    if raw in lead:
        return raw, None
    p = Path(raw)
    if p.suffix.lower() in (".py", ".ms"):
        if p.suffix.lower() != ext:
            raise ValueError(f"kit file {raw!r} does not match lang (expected {ext})")
        if not p.is_file():
            raise ValueError(f"kit file not found: {raw}")
        return p.stem, p
    for d in kit_dirs or ():
        d = Path(d)
        for cand in (d / f"{raw}{ext}", d / "mxs" / f"{raw}{ext}"):
            if cand.is_file():
                return raw, cand
    raise ValueError(f"unknown kit entry {raw!r}: not a lead module {lead}, not a {ext} path, "
                     f"and not found in kit_dirs={list(kit_dirs or [])}")


def _lead_deps_py(src: str) -> set[str]:
    out = set()
    for a, b in _PY_IMPORT.findall(src):
        names = [a] if a else re.findall(r"\w+", b)
        out |= {n for n in names if n in PY_KIT}
    return out


def _py_modules(kit, kit_dirs) -> list[tuple[str, str]]:
    """[(module name, source)] in load order: lead modules first (with dependencies), then domain files."""
    want, domain = {"result"}, []
    for entry in kit:
        name, path = _resolve(entry, ".py", kit_dirs)
        if path is None:
            want.add(name)
        elif name not in [n for n, _ in domain]:
            src = path.read_text(encoding="utf-8")
            compile(src, str(path), "exec")
            domain.append((name, src))
            want |= _lead_deps_py(src)
    for k in list(want):
        want |= set(PY_DEPS.get(k, ()))
    lead = [(k, (KIT_DIR / f"{k}.py").read_text(encoding="utf-8")) for k in PY_KIT if k in want]
    return lead + domain


def _mxs_modules(kit, kit_dirs) -> list[tuple[str, str]]:
    want, domain = {"result"}, []
    for entry in kit:
        name, path = _resolve(entry, ".ms", kit_dirs)
        if path is None:
            want.add(name)
        elif name not in [n for n, _ in domain]:
            src = path.read_text(encoding="utf-8")
            domain.append((name, src))
            want |= set(_MXS_CALL.findall(src))
    lead = [(k, (MXS_DIR / f"{k}.ms").read_text(encoding="utf-8")) for k in MXS_KIT if k in want]
    return lead + domain


_PY_TEMPLATE = '''\
# max_wrap {version}: generated pymxs script
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-using-2027.md and scripting-pipeline__3dsmaxbatch-2020.md
# Main thread only: never call pymxs from a thread (scripting-pipeline__python-threading-2027.md).
import json
import sys
import traceback
import types

import pymxs
from pymxs import runtime as rt

_MXK_LABEL = {label!r}
_MXK_UNDO = {undo!r}
_MXK_RESULT_PATH = {result_path!r}
_MXK_ORDER = {order!r}
_MXK_SOURCES = {sources}
_MXK_CODE = {code!r}
_MXK_LOG = []


def log(*parts):
    _MXK_LOG.append(" ".join(str(p) for p in parts))


def _mxk_load():
    pkg = types.ModuleType("maxkit")
    pkg.__path__ = []
    sys.modules["maxkit"] = pkg
    mods = {{}}
    for name in _MXK_ORDER:
        mod = types.ModuleType("maxkit." + name)
        mod.__file__ = "<maxkit." + name + ">"
        sys.modules["maxkit." + name] = mod
        sys.modules.setdefault(name, mod)  # domain helpers may `import stats` or `import maxkit_fx`
        setattr(pkg, name, mod)
        exec(compile(_MXK_SOURCES[name], mod.__file__, "exec"), mod.__dict__)
        mods[name] = mod
    return mods


def _mxk_result_path():
    if _MXK_RESULT_PATH:
        return _MXK_RESULT_PATH
    try:
        return str(rt.maxops.mxsCmdLineArgs[rt.name("result_path")])
    except Exception:
        return None


_mxk_ok, _mxk_err, _mxk_ns = True, None, {{}}
try:
    _mxk_mods = _mxk_load()
    _mxk_ns.update(_mxk_mods)
    _mxk_ns.update({{"rt": rt, "pymxs": pymxs, "log": log, "result": None, "__name__": "__mxk_chunk__"}})
    _mxk_chunk = compile(_MXK_CODE, "<agent chunk>", "exec")
    if _MXK_UNDO:
        with pymxs.undo(True, _MXK_LABEL):  # one undo record for the whole chunk  # [verify] pymxs.undo(on, label)
            exec(_mxk_chunk, _mxk_ns)
    else:
        exec(_mxk_chunk, _mxk_ns)
except Exception:
    _mxk_ok, _mxk_err = False, traceback.format_exc(limit=6)
try:
    rt.redrawViews()  # the viewport does not refresh while a script runs
except Exception:
    pass
_mxk_res_mod = sys.modules.get("maxkit.result")
if _mxk_res_mod is not None:
    _mxk_payload = _mxk_res_mod.envelope(_mxk_ok, _mxk_ns.get("result"), _mxk_err, _MXK_LOG,
                                         _mxk_res_mod.max_version())
else:
    _mxk_payload = {{"ok": _mxk_ok, "result": str(_mxk_ns.get("result")), "error": _mxk_err,
                    "log": _MXK_LOG, "max_version": None}}
_mxk_path = _mxk_result_path()
if _mxk_path:
    try:
        _mxk_res_mod.write(_mxk_payload, _mxk_path)
    except Exception as _mxk_exc:
        _mxk_payload["log"].append("result file not written: %s" % _mxk_exc)
print("MXK_RESULT " + json.dumps(_mxk_payload, ensure_ascii=False))
'''

_MXS_HEAD = '''\
-- max_wrap {version}: generated MAXScript
-- channel: mcp-safe | batch | bridge | handoff
-- status: not yet run in 3ds Max; checked against scripting-pipeline__max-mcp-known-limitations-2027-3.md (block list avoided)
-- The value of this script is the JSON result text.
(
'''


def _indent(text: str, n: int) -> str:
    return textwrap.indent(text.rstrip() + "\n", " " * n)


def wrap(code: str, lang: str = "python", kit=(), result_path=None, label: str = "agent change",
         undo: bool = True, kit_dirs=None) -> str:
    """Return one self-contained script (see module docstring).

    kit entries: a lead module name ("audit"), a path to a .py (Python) or .ms (MAXScript) file,
    or a name looked up as <name>.py / <name>.ms (also mxs/<name>.ms) in kit_dirs."""
    code = textwrap.dedent(code).strip("\n")
    if result_path is not None:
        result_path = os.fspath(result_path)
    if lang in ("python", "py", "pymxs"):
        compile(code, "<agent chunk>", "exec")  # fail early on a syntax error in the chunk
        mods = _py_modules(kit, kit_dirs)
        order = [n for n, _ in mods]
        sources = "{\n" + "".join(f"    {n!r}: {src!r},\n" for n, src in mods) + "}"
        return _PY_TEMPLATE.format(version=__version__, label=label, undo=bool(undo),
                                   result_path=result_path, order=tuple(order), sources=sources, code=code)
    if lang in ("maxscript", "mxs", "ms"):
        parts = [_MXS_HEAD.format(version=__version__)]
        for name, src in _mxs_modules(kit, kit_dirs):
            parts.append(f"    -- kit: {name}\n" + _indent(src, 4))
        lab = label.replace("\\", "\\\\").replace('"', '\\"')
        body = _indent(code, 12)
        parts.append(
            "    local mxk_log = #()\n"
            "    fn mxk_note s = (append mxk_log (s as string); ok)  -- log a line (MAXScript log is the logarithm)\n"
            "    local result = undefined\n"
            "    local mxk_ok = true\n"
            "    local mxk_err = undefined\n"
            "    try (\n")
        if undo:
            parts.append(f'        undo "{lab}" on (\n{body}        )\n')
        else:
            parts.append(f"        (\n{body}        )\n")
        parts.append(
            "    ) catch (\n"
            "        mxk_ok = false\n"
            "        mxk_err = getCurrentException()  -- [verify] getCurrentException\n"
            "    )\n"
            "    try (redrawViews()) catch ()\n"
            "    local mxk_ver = try ((maxVersion()) as string) catch (undefined)  -- [verify] maxVersion\n"
            "    local mxk_json = mxk_toJson (mxk_dict #(#(\"ok\", mxk_ok), #(\"result\", result), "
            "#(\"error\", mxk_err), #(\"log\", mxk_log), #(\"max_version\", mxk_ver)))\n")
        if result_path:
            rp = result_path.replace('"', "")
            parts.append(
                "    -- file write from Safe mode is undocumented: the returned value carries the same JSON\n"
                f'    try (local mxk_fh = createFile @"{rp}"; format "%" mxk_json to:mxk_fh; close mxk_fh) catch ()'
                "  -- [verify] createFile\n")
        parts.append('    format "MXK_RESULT %\\n" mxk_json\n    mxk_json\n)\n')
        return "".join(parts)
    raise ValueError(f"lang must be 'python' or 'maxscript', not {lang!r}")


if __name__ == "__main__":  # python3 max_wrap.py chunk.py [--lang maxscript] [--kit audit,stats] [--out f]
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("chunk")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--kit", default="")
    ap.add_argument("--result", default=None)
    ap.add_argument("--label", default="agent change")
    ap.add_argument("--kit-dir", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    src = Path(a.chunk).read_text(encoding="utf-8")
    lang = a.lang or ("maxscript" if a.chunk.lower().endswith(".ms") else "python")
    out = wrap(src, lang, [k for k in a.kit.split(",") if k], a.result, a.label, kit_dirs=a.kit_dir)
    if a.out:
        Path(a.out).write_text(out, encoding="utf-8")
        print(a.out)
    else:
        print(out)
