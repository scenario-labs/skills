#!/usr/bin/env python3
"""max_check: offline checks on pymxs and MAXScript before anything reaches 3ds Max (runner side).

    check(paths=None, code=None, lang=None, channel=None) -> dict
      {ok, errors, warnings, unknown_names, python}

- Python: compiles with this interpreter and, when found, with python3.13 (3ds Max 2027 ships
  Python 3.13.9); flags MaxPlus (removed), pymxs from threads, pymxs.mxstoken (deprecated).
- MAXScript: bracket and string balance with line numbers (handles "\\" escapes, @"verbatim",
  -- and /* */ comments).
- channel="mcp-safe": each command on the Safe Scene Script Execution block list is an error
  (scripting-pipeline__max-mcp-known-limitations-2027-3.md); file writes, import, export and render,
  whose status in Safe mode is not documented, are warnings. Python is an error at level 10.
- unknown_names: rt.X chains (Python) and dotted MAXScript names not in references/api-names.txt,
  the list extracted from the saved docs. Each carries `marked` = the line already says [verify].
  An unknown name is not wrong: it is unverified. Mark it `# [verify]` or `-- [verify]`.
"""
from __future__ import annotations

__version__ = "0.1.0"

import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES_FILE = HERE.parent / "references" / "api-names.txt"

BLOCKED = [  # Safe Scene Script Execution block list, 2027.3 known limitations
    ("dotNetObject", r"\bdotNetObject\b"),
    ("dotNetClass", r"\bdotNetClass\b"),
    ("dotNet.", r"\bdotNet\s*\."),
    ("macroScript", r"\bmacroScript\b"),
    ("UIAccessor", r"\bUIAccessor\b"),
    ("windows.sendMessage", r"\bwindows\s*\.\s*sendMessage\b"),
    ("globalVars.remove", r"\bglobalVars\s*\.\s*remove\b"),
    ("setINISetting", r"\bsetINISetting\b"),
    ("deleteFile", r"\bdeleteFile\b"),
    ("copyFile", r"\bcopyFile\b"),
    # below: not named in the doc's list; Python "can also be blocked" (doc) and is not allowed at
    # level 10; shell launches are what the doc says external clients wrongly suggest  [added]
    ("python.Execute", r"\bpython\s*\.\s*Execute\b"),
    ("python.ExecuteFile", r"\bpython\s*\.\s*ExecuteFile\b"),
    ("python.Import", r"\bpython\s*\.\s*Import\b"),
    ("DOSCommand", r"\bDOSCommand\b"),
    ("HiddenDOSCommand", r"\bHiddenDOSCommand\b"),
    ("ShellLaunch", r"\bShellLaunch\b"),
]
DOC_BLOCKED = {"dotNetObject", "dotNetClass", "dotNet.", "macroScript", "UIAccessor", "windows.sendMessage",
               "globalVars.remove", "setINISetting", "deleteFile", "copyFile"}
UNDOCUMENTED_IN_SAFE = [
    ("renameFile", r"\brenameFile\b"),
    ("createFile", r"\bcreateFile\b"),
    ("openFile", r"\bopenFile\b"),
    ("importFile", r"\bimportFile\b"),
    ("exportFile", r"\bexportFile\b"),
    ("render outputFile", r"\brender\b[^\n]*outputFile\s*:"),
    ("saveMaxFile", r"\bsaveMaxFile\b"),
    ("save (bitmap)", r"\bsave\s+\w+"),
]
MXS_KEYWORDS = set("""
about and as at by case catch collect continue coordsys do else exit false fn for from function global
if in local mapped max not of off ok on or parameters plugin private public return rollout set struct
then throw to tool true try undefined undo when where while with dontcollect animate redraw quiet
""".split())


def load_names(path=NAMES_FILE) -> set[str]:
    try:
        return {ln.strip().lower() for ln in Path(path).read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")}
    except OSError:
        return set()


def _known(name: str, names: set[str]) -> bool:
    n = name.lower()
    if n in names:
        return True
    parts = n.split(".")
    # a chain is known when its head is known and every longer prefix seen in the docs matches
    return parts[0] in names and (len(parts) == 1 or ".".join(parts[:2]) in names)


def _guess_lang(path: str | None, code: str) -> str:
    if path:
        ext = Path(path).suffix.lower()
        if ext in (".py",):
            return "python"
        if ext in (".ms", ".mcr", ".mse", ".mxs"):
            return "maxscript"
    if re.search(r"^\s*(import |from \w+ import|def |class )", code, re.M):
        return "python"
    return "maxscript"


# ---------------------------------------------------------------- MAXScript lexing
def _strip_mxs(code: str):
    """Return (clean_text_same_length, errors). Strings and comments become spaces; newlines kept."""
    out = list(code)
    errs = []
    i, n, line = 0, len(code), 1
    while i < n:
        c = code[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if code.startswith("--", i):
            j = code.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            if j < 0:
                errs.append({"line": line, "message": "unclosed /* comment"})
                j = n - 2
            for k in range(i, j + 2):
                if code[k] != "\n":
                    out[k] = " "
                else:
                    line += 1
            i = j + 2
            continue
        if c == '"' or (c == "@" and code.startswith('@"', i)):
            verbatim = c == "@"
            start_line = line
            j = i + (2 if verbatim else 1)
            closed = False
            while j < n:
                if code[j] == "\n":
                    line += 1
                if not verbatim and code[j] == "\\":
                    j += 2
                    continue
                if code[j] == '"':
                    if verbatim and code.startswith('""', j):
                        j += 2
                        continue
                    closed = True
                    break
                j += 1
            if not closed:
                errs.append({"line": start_line, "message": "unclosed string"})
                j = n - 1
            for k in range(i, min(j + 1, n)):
                if code[k] != "\n":
                    out[k] = " "
            i = j + 1
            continue
        i += 1
    return "".join(out), errs


def _brackets(clean: str):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack, errs, line = [], [], 1
    for ch in clean:
        if ch == "\n":
            line += 1
        elif ch in "([{":
            stack.append((ch, line))
        elif ch in pairs:
            if not stack or stack[-1][0] != pairs[ch]:
                errs.append({"line": line, "message": f"unexpected '{ch}'"})
            else:
                stack.pop()
    for ch, ln in stack:
        errs.append({"line": ln, "message": f"'{ch}' is never closed"})
    return errs


def _mxs_locals(clean: str) -> set[str]:
    loc = set()
    for m in re.finditer(r"\b(?:local|global|persistent\s+global)\s+([^\n;]+)", clean, re.I):
        for part in m.group(1).split(","):
            name = re.match(r"\s*([A-Za-z_]\w*)", part)
            if name:
                loc.add(name.group(1).lower())
    for m in re.finditer(r"\b(?:fn|function|struct|rollout|mapped\s+fn)\s+([A-Za-z_]\w*)([^=\n]*)=?", clean, re.I):
        loc.add(m.group(1).lower())
        for p in re.findall(r"([A-Za-z_]\w*)\s*:?", m.group(2)):
            loc.add(p.lower())
    for m in re.finditer(r"\bfor\s+([A-Za-z_]\w*)\s+(?:in|=)", clean, re.I):
        loc.add(m.group(1).lower())
    for m in re.finditer(r"(?m)^\s*([A-Za-z_]\w*)\s*(?:=|\+=|-=)(?!=)", clean):
        loc.add(m.group(1).lower())
    return loc


def _mxs_names(code: str, clean: str, names: set[str]) -> list[dict]:
    loc = _mxs_locals(clean)
    lines = code.splitlines()
    out, seen = [], set()
    for ln_no, ln in enumerate(clean.splitlines(), 1):
        for m in re.finditer(r"(?<![\w.#])([A-Za-z_]\w*(?:\s*\.\s*[A-Za-z_]\w*)+)", ln):
            chain = re.sub(r"\s+", "", m.group(1))
            head = chain.split(".")[0].lower()
            if head in loc or head in MXS_KEYWORDS or head.startswith("mxk_") or chain.lower() in seen:
                continue
            if not _known(chain, names):
                seen.add(chain.lower())
                raw = lines[ln_no - 1] if ln_no - 1 < len(lines) else ""
                out.append({"name": chain, "line": ln_no, "marked": "[verify]" in raw})
    return out


# ---------------------------------------------------------------- Python
def _py_rt_names(tree: ast.AST, code: str, names: set[str]) -> list[dict]:
    rt_aliases = {"rt"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "pymxs":
            for a in node.names:
                if a.name == "runtime":
                    rt_aliases.add(a.asname or "runtime")
    lines = code.splitlines()
    out, seen = [], set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        chain, cur = [], node
        while isinstance(cur, ast.Attribute):
            chain.append(cur.attr)
            cur = cur.value
        if not isinstance(cur, ast.Name):
            continue
        chain.reverse()
        if cur.id in rt_aliases:
            full = chain
        elif cur.id == "pymxs" and chain[:1] == ["runtime"]:
            full = chain[1:]
        else:
            continue
        if not full:
            continue
        name = ".".join(full[:2])
        if name.lower() in seen or _known(name, names):
            continue
        seen.add(name.lower())
        raw = lines[node.lineno - 1] if node.lineno - 1 < len(lines) else ""
        out.append({"name": name, "line": node.lineno, "marked": "[verify]" in raw})
    # keep only outermost chains (rt.a.b reported once as a.b)
    return sorted(out, key=lambda d: d["line"])


def _py313(code: str):
    exe = shutil.which("python3.13")
    if not exe:
        return None
    try:
        p = subprocess.run([exe, "-c", "import sys; compile(sys.stdin.read(), '<chunk>', 'exec')"],
                           input=code, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"interpreter": exe, "ok": False, "message": str(exc)}
    return {"interpreter": exe, "ok": p.returncode == 0, "message": p.stderr.strip()[-500:]}


def _scan(code: str, label: str, lang: str, channel: str | None, names: set[str], res: dict):
    def err(line, msg):
        res["errors"].append({"file": label, "line": line, "message": msg})

    def warn(line, msg):
        res["warnings"].append({"file": label, "line": line, "message": msg})

    if lang == "python":
        try:
            tree = ast.parse(code)
            compile(code, label, "exec")
        except SyntaxError as exc:
            err(exc.lineno, f"syntax error: {exc.msg}")
            return
        p313 = _py313(code)
        if p313 is not None:
            res["python"].append({"file": label, **p313})
            if not p313["ok"]:
                err(None, f"python3.13 rejects it: {p313['message']}")
        for i, ln in enumerate(code.splitlines(), 1):
            if re.search(r"\bimport\s+MaxPlus\b|\bfrom\s+MaxPlus\b", ln):
                err(i, "MaxPlus was removed: use pymxs")
            if "mxstoken" in ln:
                warn(i, "pymxs.mxstoken is deprecated")
            if re.search(r"\b(threading\.Thread|concurrent\.futures|QThread)\b", ln):
                warn(i, "pymxs must run on the main thread only")
        res["unknown_names"] += [{"file": label, **d} for d in _py_rt_names(tree, code, names)]
        if channel == "mcp-safe":
            err(None, "Python does not run in mcp-safe below level 20 (admin only): send MAXScript")
        clean = code
    else:
        clean, serr = _strip_mxs(code)
        for e in serr + _brackets(clean):
            err(e["line"], e["message"])
        res["unknown_names"] += [{"file": label, **d} for d in _mxs_names(code, clean, names)]
    if channel == "mcp-safe":
        text = clean if lang != "python" else code
        for i, ln in enumerate(text.splitlines(), 1):
            for name, pat in BLOCKED:
                if re.search(pat, ln, re.I):
                    src = "" if name in DOC_BLOCKED else " [added]"
                    err(i, f"{name} is blocked{src} in mcp-safe (Safe Scene Script Execution); a blocked "
                           f"command stays blocked for the rest of the session")
            for name, pat in UNDOCUMENTED_IN_SAFE:
                if re.search(pat, ln, re.I):
                    warn(i, f"{name}: not documented as allowed in Safe mode; return data as the "
                            f"script's value and expect the user may have to do this step")


def check(paths=None, code=None, lang=None, channel=None) -> dict:
    """Check files and/or a code string. ok is False when any error is found."""
    names = load_names()
    res = {"ok": True, "errors": [], "warnings": [], "unknown_names": [], "python": [],
           "names_loaded": len(names)}
    if not names:
        res["errors"].append({"file": str(NAMES_FILE), "line": None,
                              "message": "API names reference missing, unreadable or empty"})
    items = []
    for p in ([paths] if isinstance(paths, (str, Path)) else (paths or [])):
        try:
            items.append((str(p), Path(p).read_text(encoding="utf-8", errors="replace"), lang))
        except OSError as exc:
            res["errors"].append({"file": str(p), "line": None, "message": f"cannot read: {exc}"})
    if code is not None:
        items.append(("<code>", code, lang))
    for label, text, lg in items:
        lg = lg or _guess_lang(None if label == "<code>" else label, text)
        _scan(text, label, "python" if lg in ("python", "py", "pymxs") else "maxscript", channel, names, res)
    res["ok"] = not res["errors"]
    return res


if __name__ == "__main__":  # python3 max_check.py file.ms [file.py ...] [--channel mcp-safe]
    args = sys.argv[1:]
    ch = None
    if "--channel" in args:
        k = args.index("--channel")
        ch = args[k + 1]
        args = args[:k] + args[k + 2:]
    r = check(args, channel=ch)
    print(json.dumps(r, indent=2))
    raise SystemExit(0 if r["ok"] else 1)
