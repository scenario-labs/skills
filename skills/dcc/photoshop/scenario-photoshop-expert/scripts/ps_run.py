"""
ps_run: run one ExtendScript (JSX) job inside a live Adobe Photoshop on macOS and return one
machine-readable result. The shared entry point for every scenario-photoshop-* skill.

Why ExtendScript through AppleScript: it needs no plugin install, answers as soon as Photoshop
runs, reaches the whole Action Manager (executeAction takes the same descriptors that UXP batchPlay
sends), and keeps the skills independent of any third-party bridge. UXP-only features (the imaging
API, executeAsModal, secure storage) are out of its reach.

Shell:
  python3 ps_run.py job.jsx [--undo "Scenario: name"] [--timeout 120] [--json out.json]
  python3 ps_run.py -e "return app.documents.length"
  python3 ps_run.py --find       # Photoshop app path, AppleScript name and version (exit 5 if none)
  python3 ps_run.py --launch     # start Photoshop without stealing focus, wait until it answers
  python3 ps_run.py --ping       # {"ok": true, "result": {"version": ..., "documents": n}}

Job protocol:
  A job is the BODY of a JavaScript function. It may `return` any JSON-able value. Ruler and type
  units are set to pixels and points for the job and restored after; dialogs are suppressed
  (DialogModes.NO) and restored. With undo="Scenario: name" and an open document, the job runs
  inside app.activeDocument.suspendHistory, so all its edits are ONE history state (one Ctrl+Z).
  Helpers defined before the body (the prelude):
    psr_log(msg)                         adds a line to result["log"]
    psr_new_doc(w, h, name, opts)        new document the job owns; opts: {mode: "rgb"|"gray"|
                                         "cmyk"|"lab", bits: 8|16|32, fill: "white"|"transparent",
                                         ppi: 72}
    psr_dup(doc, name, merged)           duplicate the job owns (merged=true flattens the copy)
    psr_close(doc)                       close WITHOUT saving, only a document this job created
    psr_export(doc, path, fmt, opts)     save a COPY as png|jpg|tif|psd|tga (never the doc's own file),
                                         creating the folder; tga with opts.alpha writes 32-bit
                                         with the alpha channel
    psr_owned(doc)                       true when this job created the document
    __json(value)                        JSON text of a value (UnitValue becomes a number of px)
  The result dict: {"ok", "result", "error", "line", "log", "ms", "exit"}.

Guards (a lint over the job body, not a sandbox): the body may not call .save(, .saveAs(, .close(
or app.quit, nor send the "save" or "close" Action Manager events. Use psr_export and psr_close,
which refuse documents the job did not create. allow_unsafe=True lifts the lint for a test you
wrote yourself; never use it on the user's documents.

Exit codes: 0 ok, 1 job raised, 2 usage or lint refusal, 3 Photoshop not running or not answering,
4 timeout (a modal dialog is often open in Photoshop), 5 Photoshop not found, 6 macOS refused
automation (System Settings > Privacy & Security > Automation: allow your terminal to control
Adobe Photoshop).
"""

import glob
import json
import os
import plistlib
import re
import subprocess
import sys
import tempfile
import time

RESULT_TAG = "PS_RESULT "

PRELUDE = r"""
var __psr_log = [];
var __psr_created = [];
function psr_log(m) { __psr_log.push(String(m)); }
function __json(v) {
  // ExtendScript's regex engine rejects \u escapes in character classes: escape by code point.
  function esc(s) {
    s = String(s);
    var out = '"';
    for (var i = 0; i < s.length; i++) {
      var c = s.charAt(i), n = s.charCodeAt(i);
      if (c === '"') out += '\\"';
      else if (c === "\\") out += "\\\\";
      else if (c === "\n") out += "\\n";
      else if (c === "\r") out += "\\r";
      else if (c === "\t") out += "\\t";
      else if (n < 32 || (n >= 127 && n < 160) || n === 8232 || n === 8233)
        out += "\\u" + ("0000" + n.toString(16)).slice(-4);
      else out += c;
    }
    return out + '"';
  }
  function enc(x, depth) {
    if (depth > 40) return '"<depth>"';
    // UnitValue first: a zero UnitValue compares equal to null in ExtendScript.
    if (typeof UnitValue !== "undefined" && x instanceof UnitValue) {
      try { return String(Number(x.as("px"))); } catch (e) { return esc(x.toString()); }
    }
    if (x === null || x === undefined) return "null";
    if (typeof x === "number") return isFinite(x) ? String(x) : "null";
    if (typeof x === "boolean") return x ? "true" : "false";
    if (typeof x === "string") return esc(x);
    if (x instanceof Array) {
      var a = [];
      for (var i = 0; i < x.length; i++) a.push(enc(x[i], depth + 1));
      return "[" + a.join(",") + "]";
    }
    if (typeof x === "object") {
      var o = [];
      for (var k in x) {
        if (x.hasOwnProperty && !x.hasOwnProperty(k)) continue;
        if (typeof x[k] === "function") continue;
        o.push(esc(k) + ":" + enc(x[k], depth + 1));
      }
      return "{" + o.join(",") + "}";
    }
    return esc(String(x));
  }
  return enc(v, 0);
}
function psr_owned(doc) {
  for (var i = 0; i < __psr_created.length; i++) if (__psr_created[i] === doc.id) return true;
  return false;
}
function psr_new_doc(w, h, name, opts) {
  opts = opts || {};
  var modes = {rgb: NewDocumentMode.RGB, gray: NewDocumentMode.GRAYSCALE,
               cmyk: NewDocumentMode.CMYK, lab: NewDocumentMode.LAB};
  var bits = {8: BitsPerChannelType.EIGHT, 16: BitsPerChannelType.SIXTEEN,
              32: BitsPerChannelType.THIRTYTWO};
  var fill = opts.fill === "transparent" ? DocumentFill.TRANSPARENT : DocumentFill.WHITE;
  var d = app.documents.add(UnitValue(w, "px"), UnitValue(h, "px"), opts.ppi || 72,
                            name || "psr_temp", modes[opts.mode || "rgb"], fill, 1,
                            bits[opts.bits || 8]);
  __psr_created.push(d.id);
  return d;
}
function psr_dup(doc, name, merged) {
  var d = doc.duplicate(name || (doc.name + " copy"), merged === true);
  __psr_created.push(d.id);
  return d;
}
function psr_close(doc) {
  if (!psr_owned(doc)) throw new Error("psr_close refused: document '" + doc.name +
                                       "' was not created by this job");
  doc.close(SaveOptions.DONOTSAVECHANGES);
}
function psr_export(doc, path, fmt, opts) {
  opts = opts || {};
  var f = new File(path);
  try {
    if (doc.fullName && f.fsName === doc.fullName.fsName) {
      throw new Error("psr_export refused: target is the document's own file");
    }
  } catch (e) { if (String(e).indexOf("refused") >= 0) throw e; }
  // A missing folder fails as "General Photoshop error ... not available in this version".
  if (!f.parent.exists && !f.parent.create()) throw new Error("psr_export: cannot create folder " + f.parent.fsName);
  var so;
  fmt = String(fmt || "png").toLowerCase();
  if (fmt === "png") { so = new PNGSaveOptions(); so.compression = opts.compression || 6; }
  else if (fmt === "jpg" || fmt === "jpeg") { so = new JPEGSaveOptions(); so.quality = opts.quality === undefined ? 10 : opts.quality; }
  else if (fmt === "tif" || fmt === "tiff") { so = new TiffSaveOptions(); so.layers = opts.layers === true; }
  else if (fmt === "psd") { so = new PhotoshopSaveOptions(); so.layers = true; }
  else if (fmt === "tga") {
    // PNG keeps transparency, not alpha channels; a packed texture's 4th channel needs TGA.
    so = new TargaSaveOptions(); so.alphaChannels = opts.alpha === true; so.rleCompression = false;
    if (opts.alpha === true) so.resolution = TargaBitsPerPixels.THIRTYTWO;
    else so.resolution = TargaBitsPerPixels.TWENTYFOUR;
  }
  else throw new Error("psr_export: unknown format " + fmt);
  doc.saveAs(f, so, true, Extension.LOWERCASE);
  return f.fsName;
}
"""

WRAPPER = r"""
var __psr_res = null, __psr_err = null, __psr_line = null;
function __psr_main() {
  try { __psr_res = (function () {
%BODY%
  })(); } catch (e) { __psr_err = String(e); __psr_line = e.line || null; }
}
(function () {
  var t0 = new Date().getTime();
  var ru = app.preferences.rulerUnits, tu = app.preferences.typeUnits, dm = app.displayDialogs;
  app.preferences.rulerUnits = Units.PIXELS;
  app.preferences.typeUnits = TypeUnits.POINTS;
  app.displayDialogs = DialogModes.NO;
  try {
    var undo = %UNDO%;
    if (undo && app.documents.length > 0) app.activeDocument.suspendHistory(undo, "__psr_main()");
    else __psr_main();
  } catch (e) { if (!__psr_err) { __psr_err = String(e); __psr_line = e.line || null; } }
  if (__psr_err !== null) {
    // A failed job closes the temp documents it created, so no copy is left in front of the user.
    for (var i = app.documents.length - 1; i >= 0; i--) {
      try { var d = app.documents[i];
            for (var k = 0; k < __psr_created.length; k++)
              if (__psr_created[k] === d.id) { d.close(SaveOptions.DONOTSAVECHANGES); __psr_log.push("closed temp " + d.name); break; } }
      catch (e2) {}
    }
  }
  app.preferences.rulerUnits = ru;
  app.preferences.typeUnits = tu;
  app.displayDialogs = dm;
  return "%TAG%" + __json({ok: __psr_err === null, result: __psr_res, error: __psr_err,
                           line: __psr_line, log: __psr_log, ms: new Date().getTime() - t0});
})();
"""

UNSAFE = [
    (r"\.\s*save\s*\(", "calls .save()"),
    (r"\.\s*saveAs\s*\(", "calls .saveAs() (use psr_export)"),
    (r"\.\s*close\s*\(", "calls .close() (use psr_close on a document the job created)"),
    (r"app\s*\.\s*quit", "quits Photoshop"),
    (r"(charIDToTypeID|stringIDToTypeID)\s*\(\s*['\"](save|Sv  |close|Cls )['\"]",
     "sends a save or close Action Manager event"),
]


def lint(body):
    """Return the list of guard violations in a job body (empty list = allowed)."""
    return [why for pat, why in UNSAFE if re.search(pat, body)]


def find_photoshop():
    """Newest installed Photoshop: {"path", "name", "version"} or None."""
    found = []
    for app in glob.glob("/Applications/Adobe Photoshop*/Adobe Photoshop*.app"):
        try:
            with open(os.path.join(app, "Contents", "Info.plist"), "rb") as f:
                info = plistlib.load(f)
        except OSError:
            continue
        ver = info.get("CFBundleShortVersionString", "0")
        key = tuple(int(x) for x in re.findall(r"\d+", ver)[:3])
        found.append((key, {"path": app, "name": os.path.basename(app)[:-4], "version": ver}))
    return max(found)[1] if found else None


def is_running(ps=None):
    ps = ps or find_photoshop()
    if not ps:
        return False
    exe = os.path.join(ps["path"], "Contents", "MacOS")
    out = subprocess.run(["pgrep", "-f", exe], capture_output=True, text=True)
    return out.returncode == 0


def _osascript(script, timeout):
    try:
        p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True,
                           timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        return None, "timeout", 4
    err = p.stderr.strip()
    if p.returncode != 0:
        if "-1743" in err or "Not authorized" in err:
            return None, err, 6
        if "-1712" in err or "timed out" in err:
            return None, err, 4
        if "-600" in err or "isn’t running" in err or "isn't running" in err:
            return None, err, 3
        return None, err, 1
    return p.stdout.rstrip("\n"), err, 0


def build(body, undo=None):
    """The full JSX text for a job body (prelude + wrapper)."""
    undo_js = json.dumps(undo) if undo else "null"
    return (PRELUDE + WRAPPER.replace("%UNDO%", undo_js).replace("%TAG%", RESULT_TAG)
            .replace("%BODY%", body))


_counter = [0]


def run(body, undo=None, timeout=120, allow_unsafe=False, ps=None, launch=False):
    """Run a job body in the live Photoshop. Returns the result dict (see module docstring)."""
    t0 = time.time()
    ps = ps or find_photoshop()
    if not ps:
        return {"ok": False, "error": "Photoshop not found in /Applications", "exit": 5}
    if not allow_unsafe:
        bad = lint(body)
        if bad:
            return {"ok": False, "error": "guard refused the job: " + "; ".join(bad), "exit": 2}
    if not is_running(ps):
        if not launch:
            return {"ok": False, "error": "Photoshop is not running (ps_run.py --launch)",
                    "exit": 3}
        launched = launch_photoshop(ps)
        if not launched.get("ok"):
            return launched
    tmpdir = os.path.join(tempfile.gettempdir(), "scenario-ps-run")
    os.makedirs(tmpdir, exist_ok=True)
    _counter[0] += 1
    path = os.path.join(tmpdir, "job_%d_%d.jsx" % (os.getpid(), _counter[0]))
    with open(path, "w", encoding="utf-8") as f:
        f.write(build(body, undo))
    # Photoshop 2026 (27.11, measured) fails with error 8800 when `do javascript` is given a file
    # alias, while the same file runs through $.evalFile from an inline call. Inline it is.
    js = "$.evalFile(new File(%s))" % json.dumps(path)
    script = ('with timeout of %d seconds\n tell application "%s" to do javascript %s\n'
              'end timeout' % (timeout, ps["name"], json.dumps(js)))
    out, err, code = _osascript(script, timeout)
    ms = int((time.time() - t0) * 1000)
    if code != 0:
        hints = {3: "Photoshop is not answering", 4: "timed out; a modal dialog may be open "
                 "in Photoshop", 6: "macOS refused automation: allow the terminal to control "
                 "Photoshop in System Settings > Privacy & Security > Automation"}
        return {"ok": False, "error": hints.get(code, "osascript failed") + ": " + err[-400:],
                "exit": code, "ms": ms, "jsx": path}
    tagged = out[out.find(RESULT_TAG):] if RESULT_TAG in out else None
    if not tagged:
        return {"ok": False, "error": "no result line from Photoshop: " + out[-400:], "exit": 1,
                "ms": ms, "jsx": path}
    res = json.loads(tagged[len(RESULT_TAG):])
    res["exit"] = 0 if res.get("ok") else 1
    offset = (PRELUDE + WRAPPER.split("%BODY%")[0]).count("\n")
    if isinstance(res.get("line"), int) and res["line"] > offset:
        res["body_line"] = res["line"] - offset
    res["ms_total"] = ms
    if not res.get("ok"):
        res["jsx"] = path
    return res


def run_file(path, **kw):
    with open(path, encoding="utf-8") as f:
        return run(f.read(), **kw)


def launch_photoshop(ps=None, wait=240):
    """Start Photoshop in the background (no focus steal) and wait until it answers a ping."""
    ps = ps or find_photoshop()
    if not ps:
        return {"ok": False, "error": "Photoshop not found", "exit": 5}
    if not is_running(ps):
        subprocess.run(["open", "-g", "-a", ps["path"]], check=False)
    t_end = time.time() + wait
    last = None
    while time.time() < t_end:
        time.sleep(3)
        if not is_running(ps):
            continue
        last = run("return {version: app.version};", ps=ps, timeout=20)
        if last.get("ok"):
            return {"ok": True, "result": last["result"], "exit": 0}
        if last.get("exit") == 6:
            return last
    return {"ok": False, "error": "Photoshop did not answer within %ds: %s" %
            (wait, (last or {}).get("error")), "exit": 3}


PING = ("var docs = [];\nfor (var i = 0; i < app.documents.length; i++) "
        "docs.push(app.documents[i].name);\n"
        "return {version: app.version, documents: app.documents.length, names: docs,\n"
        "        active: app.documents.length ? app.activeDocument.name : null};")


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Run a JSX job in the live Photoshop (macOS).")
    ap.add_argument("job", nargs="?", help="file with a job body")
    ap.add_argument("-e", dest="code", help="job body given inline")
    ap.add_argument("--undo", help="history state name (one undo step)")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--json", dest="json_out", help="also write the result JSON here")
    ap.add_argument("--allow-unsafe", action="store_true", help="lift the save/close lint")
    ap.add_argument("--find", action="store_true")
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--ping", action="store_true")
    a = ap.parse_args(argv)
    if a.find:
        ps = find_photoshop()
        print(json.dumps(ps or {"error": "not found"}))
        return 0 if ps else 5
    if a.launch:
        res = launch_photoshop()
    elif a.ping:
        res = run(PING, timeout=a.timeout)
    elif a.code or a.job:
        body = a.code if a.code else open(a.job, encoding="utf-8").read()
        res = run(body, undo=a.undo, timeout=a.timeout, allow_unsafe=a.allow_unsafe)
    else:
        ap.print_usage()
        return 2
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
    print(RESULT_TAG + json.dumps(res))
    return res.get("exit", 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
