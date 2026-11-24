#!/usr/bin/env python3
"""port_scan: find what breaks when an old 3ds Max Python tool moves to 3ds Max 2027.

Runner side: plain Python 3.10+, never imports pymxs. Scans .py files for MaxPlus,
PySide2, Python 2 syntax, dead qtmax calls, pymxs-in-thread risks and Python 3.12+
breaks (3ds Max 2027 ships Python 3.13.9 and PySide 6.8.3). A finding is a lead, not
a verdict: read the line. Rules marked [added] come from general Python and Qt 6
knowledge, not from the saved 3ds Max docs.

Usage:
    python port_scan.py <file_or_folder> [--json]
Exit code: 0 nothing found, 1 findings, 2 path not found.
"""
import argparse
import ast
import json
import os
import re
import sys
import warnings

RULES = [
    # (id, severity, regex, message)
    ("maxplus", "error", r"\bimport\s+MaxPlus\b|\bMaxPlus\.",
     "MaxPlus is gone since 3ds Max 2022; port to pymxs (from pymxs import runtime as rt)"),
    ("pyside2", "error", r"\bPySide2\b|\bshiboken2\b",
     "3ds Max 2025+ ships PySide6; import PySide6 / shiboken6"),
    ("pyside1", "error", r"\bfrom\s+PySide\s+import\b|\bimport\s+PySide\b(?!\d)",
     "PySide 1 is gone; use PySide6"),
    ("qtmax-old", "error", r"\bGetQMaxWindow\b|\bMakeQWidgetDockable\b|\bGetQMaxWindowWinId\b",
     "removed qtmax/MaxPlus helpers; use qtmax.GetQMaxMainWindow() and a QDockWidget"),
    ("mxstoken", "error", r"\bmxstoken\s*\(",
     "pymxs.mxstoken() is deprecated and does not work; keep pymxs on the main thread"),
    ("print-stmt", "error", r"^\s*print\s+[^\s(=]",
     "Python 2 print statement; use print()"),
    ("except-comma", "error", r"^\s*except\s+[\w.]+\s*,\s*\w+\s*:",
     "Python 2 except syntax; use 'except X as e:'"),
    ("py2-builtins", "error", r"\b(xrange|raw_input|unicode|basestring|execfile)\s*\(",
     "Python 2 builtin; use range/input/str/exec(open().read())"),
    ("py2-dict", "error", r"\.(iteritems|itervalues|iterkeys|has_key)\s*\(",
     "Python 2 dict method"),
    ("randint-float", "error", r"randint\s*\(\s*-?\d+\.\d*\s*,|randint\s*\([^)]*,\s*-?\d+\.\d*\s*\)",
     "random.randint with float arguments raises TypeError on Python 3.12+ (3ds Max 2027 = 3.13.9) [added]"),
    ("exec_", "warning", r"\.exec_\s*\(",
     "exec_() is the PySide2 spelling; use exec() in PySide6 [added]"),
    ("qaction-widgets", "error", r"QtWidgets\.(QAction|QShortcut|QActionGroup)\b",
     "QAction, QShortcut and QActionGroup moved to QtGui in Qt 6 [added]"),
    ("qregexp", "error", r"\bQRegExp\b",
     "QRegExp is gone in Qt 6; use QtCore.QRegularExpression [added]"),
    ("desktop", "warning", r"QApplication\.desktop\s*\(|QDesktopWidget",
     "QDesktopWidget is gone in Qt 6; use QGuiApplication.screens() [added]"),
    ("setmxsprop", "warning", r"\b(get|set)mxsprop\s*\(",
     "getmxsprop/setmxsprop are not in the saved 2027 docs; prefer node.pos / node.transform [verify]"),
    ("coding-name", "info", r"^#.*coding[:=]|__name__\s*==\s*['\"]__main__['\"]",
     "coding declarations and __name__ fail under Evaluate (Ctrl+E); run with Scripting > Run Script"),
    ("max-cmd", "warning", r"rt\.max\s*\(|runtime\.max\s*\(",
     "'max ...' commands are not callable in pymxs; use rt.execute('max tool zoomextents all')"),
    ("dollar-path", "warning", r"rt\.\$|runtime\.\$",
     "$ pathnames do not exist in pymxs; use rt.getNodeByName or rt.execute('$Box*')"),
    ("is-compare", "warning", r"\b(node|obj|n|o|sel)\w*\s+is\s+(?!None\b|not\b)\w+",
     "pymxs wrappers differ for the same node: compare with ==, not is"),
]


def scan_file(path):
    findings = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [{"file": path, "line": 0, "rule": "io", "severity": "error", "message": str(exc)}]
    lines = text.splitlines()
    for rule_id, sev, rx, msg in RULES:
        pat = re.compile(rx)
        for n, line in enumerate(lines, 1):
            if pat.search(line):
                findings.append({"file": path, "line": n, "rule": rule_id, "severity": sev,
                                 "message": msg, "code": line.strip()[:160]})
    # threads touching pymxs: flag files that use both, for a manual read
    uses_thread = re.search(r"\bthreading\.Thread\b|\bQThread\b|\bThreadPoolExecutor\b|\bQRunnable\b", text)
    uses_mxs = re.search(r"\bpymxs\b|\brt\.\w+", text)
    if uses_thread and uses_mxs:
        findings.append({"file": path, "line": 0, "rule": "thread-pymxs", "severity": "warning",
                         "message": "file mixes worker threads and pymxs: check that no thread calls rt.* "
                                    "or touches objects made with pymxs (main thread only)"})
    # syntax check with the runner's Python; a Python 2 file fails here
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            ast.parse(text, filename=path)
        except SyntaxError as exc:
            findings.append({"file": path, "line": exc.lineno or 0, "rule": "syntax", "severity": "error",
                             "message": "does not parse under Python %d.%d: %s"
                                        % (sys.version_info[0], sys.version_info[1], exc.msg)})
    return findings


def iter_files(root):
    if os.path.isfile(root):
        yield root
        return
    for d, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(d, f)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("path")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    if not os.path.exists(args.path):
        print("not found: %s" % args.path, file=sys.stderr)
        return 2
    findings = []
    for f in iter_files(args.path):
        findings.extend(scan_file(f))
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        for f in findings:
            print("%s:%d %-7s %-15s %s" % (f["file"], f["line"], f["severity"], f["rule"], f["message"]))
        print("%d finding(s)" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
