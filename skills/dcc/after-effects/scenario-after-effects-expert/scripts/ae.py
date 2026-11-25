#!/usr/bin/env python3
"""ae.py: drive a running After Effects from a terminal. Standard library only.

  ae.py doctor                         what is installed, which channel works, what blocks scripts
  ae.py install-bridge                 copy ae_bridge.jsx to the user Scripts/Startup folder
  ae.py run job.jsx [--kit all]        run ExtendScript in the open project, print the result as JSON
  ae.py run -e "return app.project.numItems"
  ae.py run job.jsx --undo "Agent: retime titles" --lib ../../other-skill/scripts/helper.jsx --args '{"comp": "Main"}'
  ae.py info | audit | stats           project facts, read-only checks, counts
  ae.py frames "Comp" --spread 6 --out DIR [--sheet]     PNG frames (+ one labeled contact sheet)
  ae.py render "Comp" --out FILE --template "H.264 - Match Render Settings - 15 Mbps"
  ae.py templates "Comp"               output module and render settings templates on this machine
  ae.py aerender --project P.aep --comp "Comp" --out FILE [--template T] [--min-free-gb 10] [--stall 300] [--frames N]
  ae.py probe FILE                     ffprobe summary of a delivered file
  ae.py windows [--shot DIR]           After Effects windows (a second window usually means a dialog)
  ae.py key return|escape|tab          press one key in After Effects without bringing it forward
  ae.py restart --test-session         unattended test sessions only: stop and relaunch a blocked After Effects (lock, cooldown)
  ae.py sheet OUT.jpg --video FILE --at 0,12,30    contact sheet of frames cut from a delivered movie

A job is the BODY of a function: use `return` to send a value back. The kit modules (aekit/*.jsx)
are inlined in front of it under the AEK namespace. Channels: the resident mailbox bridge
(default, no system permission needed), `--channel osascript` on macOS, `--channel exe` on
Windows, `--channel handoff` to print a file for a person to run from File > Scripts.
"""
import argparse, glob, json, os, platform, re, shutil, struct, subprocess, sys, time, uuid


def _read_text(path, **kw):
    with open(path, encoding=kw.pop("encoding", "utf-8"), **kw) as fh:
        return fh.read()


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _write_bytes(path, data):
    with open(path, "wb") as fh:
        fh.write(data)


HERE = os.path.dirname(os.path.abspath(__file__))
KIT_DIR = os.path.join(HERE, "aekit")
KIT_ORDER = ["json", "core", "stats", "audit", "capture", "xio", "motion", "build", "text", "expr", "session"]
MAC = platform.system() == "Darwin"
WIN = platform.system() == "Windows"
KEYS = {"return": 36, "enter": 36, "escape": 53, "esc": 53, "tab": 48, "space": 49}


# ---------- locations ----------
def bridge_dir():
    """Folder.userData of ExtendScript: where the bridge keeps inbox, outbox, done and status.json."""
    if MAC:
        return os.path.expanduser("~/Library/Application Support/AEAgentBridge")
    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AEAgentBridge")


def installs():
    """Installed After Effects versions, newest first: [{name, app, aerender, year}]."""
    out = []
    if MAC:
        for d in sorted(glob.glob("/Applications/Adobe After Effects *"), reverse=True):
            apps = sorted(a for a in glob.glob(os.path.join(d, "Adobe After Effects *.app")) if "Render Engine" not in a)   # the Render Engine app is the aerender host, not the editor
            if apps:
                out.append({"name": os.path.basename(d), "app": apps[0], "aerender": os.path.join(d, "aerender")})
    elif WIN:
        base = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Adobe")
        for d in sorted(glob.glob(os.path.join(base, "Adobe After Effects *")), reverse=True):
            exe = os.path.join(d, "Support Files", "AfterFX.exe")
            if os.path.exists(exe):
                out.append({"name": os.path.basename(d), "app": exe, "aerender": os.path.join(d, "Support Files", "aerender.exe")})
    return out


def prefs_dirs():
    """User preference folders, one per version number (27.0, 26.5...), newest first."""
    root = os.path.expanduser("~/Library/Preferences/Adobe/After Effects") if MAC else \
        os.path.join(os.environ.get("APPDATA", ""), "Adobe", "After Effects")
    dirs = [d for d in glob.glob(os.path.join(root, "*")) if re.match(r"^\d+\.\d+$", os.path.basename(d))]
    return sorted(dirs, key=lambda d: float(os.path.basename(d)), reverse=True)


def ae_pid():
    if MAC:
        # the editor only: an aerender instance runs from the Render Engine app and must never be stopped here
        r = subprocess.run(["pgrep", "-f", r"After Effects 20[0-9][0-9]\.app/Contents/MacOS/After Effects$"], capture_output=True, text=True)
        pids = [int(x) for x in r.stdout.split()]
        return pids[0] if pids else None
    if WIN:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq AfterFX.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True)
        m = re.search(r'"AfterFX\.exe","(\d+)"', r.stdout)
        return int(m.group(1)) if m else None
    return None


def status():
    """Heartbeat of the bridge: {bridge, ae, state, time, jobs, last, project, dirty, age_s} or None."""
    p = os.path.join(bridge_dir(), "status.json")
    try:
        s = _read_json(p)
    except Exception:
        return None
    s["age_s"] = round(time.time() - s.get("time", 0) / 1000.0, 1)
    return s


# ---------- windows and keys (macOS) ----------
JXA_WINDOWS = r"""
ObjC.import('CoreGraphics'); ObjC.import('Foundation');
function run(argv) {
  var pid = parseInt(argv[0], 10), out = [];
  var list = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo($.kCGWindowListOptionOnScreenOnly, 0)));
  for (var i = 0; i < list.length; i++) { var w = list[i]; if (w.kCGWindowOwnerPID !== pid) continue;
    out.push({ id: w.kCGWindowNumber, name: w.kCGWindowName || "", layer: w.kCGWindowLayer, w: w.kCGWindowBounds.Width, h: w.kCGWindowBounds.Height }); }
  return JSON.stringify(out);
}"""
JXA_KEY = r"""
ObjC.import('CoreGraphics');
function run(argv) {
  var pid = parseInt(argv[0], 10), code = parseInt(argv[1], 10);
  $.CGEventPostToPid(pid, $.CGEventCreateKeyboardEvent(null, code, true)); delay(0.08);
  $.CGEventPostToPid(pid, $.CGEventCreateKeyboardEvent(null, code, false));
  return "sent";
}"""


def windows(shot_dir=None):
    """On-screen windows of After Effects. One main window is normal; anything else is a dialog or a panel."""
    pid = ae_pid()
    if not pid or not MAC:
        return []
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA_WINDOWS, str(pid)], capture_output=True, text=True, timeout=20)
    try:
        wins = json.loads(r.stdout)
    except Exception:
        return []
    wins = [w for w in wins if w["w"] > 60 and w["h"] > 40]
    main = max(wins, key=lambda w: w["w"] * w["h"]) if wins else None
    for w in wins:
        w["main"] = w is main
        if shot_dir:
            os.makedirs(shot_dir, exist_ok=True)
            w["shot"] = os.path.join(shot_dir, "window_%d.png" % w["id"])
            subprocess.run(["screencapture", "-x", "-o", "-l", str(w["id"]), w["shot"]], capture_output=True)
    return wins


def press(key):
    pid = ae_pid()
    if not pid:
        return {"ok": False, "error": "After Effects is not running"}
    if not MAC:
        return {"ok": False, "error": "key posting is implemented for macOS only"}
    code = KEYS.get(str(key).lower())
    if code is None:
        return {"ok": False, "error": "unknown key %r (use %s)" % (key, ", ".join(sorted(KEYS)))}
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA_KEY, str(pid), str(code)], capture_output=True, text=True, timeout=20)
    return {"ok": r.returncode == 0, "key": key, "stderr": r.stderr.strip()}


# ---------- wrapping and running jobs ----------
def kit_source(names):
    if names in (None, "", "none"):
        names = ["json"]
    elif names == "all":
        names = [n for n in KIT_ORDER if os.path.exists(os.path.join(KIT_DIR, n + ".jsx"))]
    else:
        asked = [n.strip() for n in names.split(",") if n.strip()]
        names = [n for n in KIT_ORDER if n in asked or n == "json" or (n == "core" and asked)]
        unknown = [n for n in asked if n not in KIT_ORDER]
        if unknown:
            raise SystemExit("unknown kit module(s): %s (have: %s)" % (", ".join(unknown), ", ".join(KIT_ORDER)))
    parts = []
    for n in names:
        parts.append(_read_text(os.path.join(KIT_DIR, n + ".jsx")).rstrip() + "\n")
    return "".join(parts)


SEGMENTS = {}


def kit_parts(names):
    """[(module file name, source)] in the order kit_source() inlines them."""
    if names in (None, "", "none"):
        names = ["json"]
    elif names == "all":
        names = [n for n in KIT_ORDER if os.path.exists(os.path.join(KIT_DIR, n + ".jsx"))]
    else:
        asked = [n.strip() for n in names.split(",") if n.strip()]
        names = [n for n in KIT_ORDER if n in asked or n == "json" or (n == "core" and asked)]
    return [("aekit/" + n + ".jsx", _read_text(os.path.join(KIT_DIR, n + ".jsx")).rstrip() + "\n") for n in names]


def wrap(body, kit="all", undo=None, job_id=None, args=None, libs=None):
    """Build a self-reporting job. Returns (job_id, text, first_body_line). The job writes outbox/<id>.json itself.
    SEGMENTS[job_id] keeps where each kit module and --lib file starts, so an error thrown inside one is mapped back."""
    job_id = job_id or "j%d_%s" % (int(time.time() * 1000), uuid.uuid4().hex[:6])
    out = os.path.join(bridge_dir(), "outbox", job_id + ".json").replace("\\", "/")
    head = "// job %s (ae.py)\n(function () {\nvar __res = { ok: true, id: %s }, __t0 = (new Date()).getTime();\n" % (job_id, json.dumps(job_id))
    # alert(), confirm() and prompt() would open a modal window that blocks every later job: inside a job they only log
    head += ("var __said = [];\nvar alert = function (m) { __said.push(\"alert: \" + m); };\n"
             "var confirm = function (m) { __said.push(\"confirm (answered true): \" + m); return true; };\n"
             "var prompt = function (m, d) { __said.push(\"prompt (answered default): \" + m); return d === undefined ? \"\" : d; };\n")
    kit_source(kit)  # validates the module names
    segs = []
    parts = kit_parts(kit) + [(os.path.basename(lib), _read_text(lib).rstrip() + "\n") for lib in libs or []]
    for name, src in parts:
        segs.append((head.count("\n") + 1, name, src))
        head += src
    head += "var ARGS = %s;\n" % json.dumps(args if args is not None else {})
    head += "var __undo = %s;\nif (__undo) { app.beginUndoGroup(__undo); }\ntry {\n__res.result = (function () {\n" % json.dumps(undo or "")
    first = head.count("\n") + 1
    SEGMENTS[job_id] = {"first": first, "parts": segs}
    tail = (
        "\n})();\n} catch (__e) { __res.ok = false; __res.error = __e.toString(); __res.line = (__e.line || 0) - %d; __res.rawLine = __e.line || 0; }\n"
        "if (__undo) { app.endUndoGroup(); }\n"
        "__res.dialogs = __said;\n"
        "__res.log = AEK._log || []; __res.ms = (new Date()).getTime() - __t0; __res.ae = app.version;\n"
        "try { __res.project = app.project.file ? app.project.file.fsName : \"\"; __res.dirty = app.project.dirty; } catch (__e2) {}\n"
        "var __f = new File(%s + \".tmp\"); __f.encoding = \"UTF-8\";\n"
        "if (__f.open(\"w\")) { __f.write(AEK.json.stringify(__res)); __f.close(); var __d = new File(%s); if (__d.exists) { __d.remove(); } __f.rename(__d.name); }\n"
        "return __res.ok ? \"ok\" : \"error\";\n})();\n"
    ) % (first - 1, json.dumps(out), json.dumps(out))
    return job_id, head + body.rstrip() + tail, first


def explain_block():
    """Why a job got no answer: heartbeat age, open windows."""
    s = status()
    info = {"ok": False, "status": s, "windows": windows()}
    if not ae_pid():
        info["error"] = "After Effects is not running. Start it (a person, or `open -a` on macOS), then retry."
    elif s is None:
        info["error"] = "No bridge heartbeat. Run ae_bridge.jsx once from File > Scripts > Run Script File, or `ae.py install-bridge` and restart After Effects."
    elif s["age_s"] > 6:
        extra = [w for w in info["windows"] if not w.get("main")]
        panel = [w for w in info["windows"] if re.search(r"save|open|import|export|alert|script", w.get("name", ""), re.I)]
        info["error"] = ("After Effects has not polled for %.0f s: it is busy (render, import, heavy script) or a modal dialog is open." % s["age_s"])
        if panel:
            info["error"] += (" A system panel is open (%s). Keys posted to a background app do not close it. In a person's session, tell them. "
                              "In an unattended test session, wait until the heartbeat is 180 s old, then `ae.py restart --test-session`." % ", ".join(repr(w["name"]) for w in panel))
        elif extra:
            info["error"] += (" %d extra window(s) on screen: run `ae.py windows --shot DIR` and look. A dialog drawn by After Effects (Crash Repair, disk cache, Home) "
                              "takes `ae.py key return`; a script alert or a Save panel does not." % len(extra))
    else:
        info["error"] = "Bridge is alive but the job did not answer in time: raise --timeout, or split the job."
    return info


def submit(text, job_id, timeout=120, channel="bridge"):
    root = bridge_dir()
    out = os.path.join(root, "outbox", job_id + ".json")
    if channel == "handoff":
        os.makedirs(os.path.join(root, "handoff"), exist_ok=True)
        path = os.path.join(root, "handoff", job_id + ".jsx")
        _write_text(path, text)
        return {"ok": None, "handoff": path, "result_file": out,
                "say": "In After Effects: File > Scripts > Run Script File..., choose %s. The result lands in %s." % (path, out)}
    for sub in ("inbox", "outbox", "done", "jobs"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    pid0 = ae_pid()
    if channel == "bridge":
        s = status()
        for _ in range(4):
            if s is not None:
                break
            time.sleep(0.4)  # status.json is rewritten every 2 s: a read during the rename can fail once
            s = status()
        if s is None or s["age_s"] > 30:
            blocked = explain_block()
            if s is None or not ae_pid():
                return blocked
        tmp = os.path.join(root, "inbox", job_id + ".jsx.tmp")
        _write_text(tmp, text)
        os.replace(tmp, os.path.join(root, "inbox", job_id + ".jsx"))
    else:
        path = os.path.join(root, "jobs", job_id + ".jsx")
        _write_text(path, text)
        if channel == "osascript":
            inst = installs()
            name = os.path.splitext(os.path.basename(inst[0]["app"]))[0] if inst else "Adobe After Effects 2027"
            script = 'with timeout of %d seconds\ntell application "%s" to DoScriptFile "%s"\nend timeout' % (timeout, name, path)
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if r.returncode != 0 and not os.path.exists(out):
                return {"ok": False, "error": "osascript: " + r.stderr.strip(),
                        "hint": "-1712 or -1743 means macOS has not granted this terminal Automation control of After Effects (System Settings > Privacy & Security > Automation). The bridge channel needs no permission."}
        elif channel == "exe":
            inst = installs()
            if not inst:
                return {"ok": False, "error": "AfterFX.exe not found"}
            subprocess.Popen([inst[0]["app"], "-r", path])
        else:
            return {"ok": False, "error": "unknown channel " + channel}
    t0 = time.time()
    swept = None
    while time.time() - t0 < timeout:
        if os.path.exists(out):
            time.sleep(0.05)
            res = read_result(out)
            # An instance started by aerender (or a second copy of the bridge) can sweep running/ and report this job as
            # stopped while the application goes on with it. Same process alive: wait for the job's own result file.
            if res.get("interrupted") and pid0 and ae_pid() == pid0:
                swept = swept or res
                if time.time() - t0 < timeout - 0.5:
                    time.sleep(0.5)
                    continue
                return dict(swept, note="Reported as stopped by another instance's startup sweep while the same After Effects process kept running; no result arrived before the timeout. Check outbox/%s.json later." % job_id)
            if swept and not res.get("interrupted"):
                res["recovered_after_sweep"] = True
            return res
        time.sleep(0.15)
    blocked = explain_block()
    blocked["job"] = job_id
    blocked["note"] = "The job file may still run when After Effects is free again. Check outbox/%s.json before sending it twice." % job_id
    return blocked


def read_result(path):
    """The result JSON, read again once if the writer was still renaming it."""
    for wait in (0, 0.2, 0.5):
        time.sleep(wait)
        try:
            return _read_json(path)
        except Exception as e:
            err = e
    return {"ok": False, "error": "unreadable result %s: %s" % (path, err)}


def checker():
    """ae_check.py from the same folder (standard library only)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ae_check", os.path.join(HERE, "ae_check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def preflight(body, libs=None):
    """Dialog-class findings of ae_check.py in the job and its --lib files. A Save As or file panel opened by one job
    blocks every agent on the application, so the runner refuses such a job before sending it."""
    chk = checker()
    found = [f for f in chk.scan(body, chk.ES3, "job") if f["severity"] == "error" and f["message"].startswith(chk.DIALOG_PREFIX)]
    for lib in libs or []:
        found += [f for f in chk.scan(_read_text(lib), chk.ES3, os.path.basename(lib))
                  if f["severity"] == "error" and f["message"].startswith(chk.DIALOG_PREFIX)]
    return found


LOOKUP = re.compile(r"(\.(?:property|layer|item|byName|itemByID|layerByID)\s*\(\s*([^()]*?)\s*\))")


def explain_null(res, body, n=None, label="line"):
    """'null is not an object' names nothing: point at the lookups that can return null on the failing line, or on the
    line that assigned the variable the failing line reads, and flag a misspelled match name."""
    err = str(res.get("error", ""))
    if "Object is invalid" in err:
        res["hint"] = ("A reference taken before an addProperty (a new mask, effect, shape group, text animator) or a precompose on the same layer "
                       "is invalid: fetch it again by match name or name after the add.")
        return
    if not re.search(r"(null|undefined) is not an object|is undefined|is null", err):
        return
    lines = body.split("\n")
    n = n if n is not None else (res.get("line") or 0)
    if not 1 <= n <= len(lines):
        return
    src = lines[n - 1]
    where = [(n, src)]
    m = re.match(r"\s*(?:return\s+|var\s+)?(?:[\w$.]+\s*=\s*)?([A-Za-z_$][\w$]*)\s*\.", src)
    if m and not LOOKUP.search(src.split("=", 1)[-1]):
        var = m.group(1)
        for k in range(n - 1, 0, -1):
            if re.search(r"(^|[^\w$.])" + re.escape(var) + r"\s*=[^=]", lines[k - 1]):
                where.append((k, lines[k - 1]))
                break
    hints, typos = [], []
    chk = checker()
    for k, text in where:
        for w in chk.match_name_warnings(text, "job", k):
            typos.append("%s %d: %s" % (label, k, w["message"]))
        for call, arg in LOOKUP.findall(text):
            hints.append("%s %d: %s can return null" % (label, k, call.lstrip(".")))
    hints = typos + hints
    if hints:
        res["null_from"] = hints
        res["hint"] = ("A lookup returned null. " + "; ".join(hints[:4]) +
                       ". AEK.core.layer(comp, name) and AEK.core.prop(layer, [matchNames]) throw with the name that failed and list what exists.")


def map_error(res, body, job_id):
    """Map the error line to the job body, or to the kit module or --lib file it fell in, with the job lines calling it."""
    seg = SEGMENTS.get(job_id)
    raw = res.get("rawLine")
    lines = body.split("\n")
    n = res.get("line") or 0
    if 1 <= n <= len(lines):
        res["source"] = lines[n - 1].strip()
        explain_null(res, body)
        return
    if not seg or not raw:
        return
    for start, name, src in reversed(seg["parts"]):
        if raw >= start:
            k = raw - start + 1
            mod = src.split("\n")
            fn = None
            for j in range(min(k, len(mod)) - 1, -1, -1):
                m = re.search(r"function\s+([\w$]+)\s*\(|([\w$]+)\s*[:=]\s*function\s*\(", mod[j])
                if m:
                    fn = m.group(1) or m.group(2)
                    break
            res["in"] = "%s:%d%s" % (name, k, (" (function %s)" % fn) if fn else "")
            res["in_source"] = mod[k - 1].strip()[:200] if 1 <= k <= len(mod) else ""
            explain_null(res, src, k, name + " line")
            calls = [i + 1 for i, l in enumerate(lines) if fn and re.search(r"\.\s*" + re.escape(fn) + r"\s*\(", l)]
            if len(calls) == 1:
                res["line"] = calls[0]
                res["source"] = lines[calls[0] - 1].strip()
            else:
                res["line"] = None
                if calls:
                    res["job_lines"] = calls
            res["note_line"] = "The error was thrown inside %s; 'line' is the job line that calls %s%s." % (
                name, fn or "it", "" if len(calls) == 1 else " (several or none: see job_lines)")
            return


def run_js(body, kit="all", undo=None, timeout=120, channel="bridge", args=None, libs=None, check=True):
    if check:
        bad = preflight(body, libs)
        if bad:
            return {"ok": False, "refused": True, "error": "Not sent: this job can open a dialog that blocks After Effects for every agent.",
                    "findings": bad, "hint": "Fix the lines above (AEK.core.open, AEK.core.fresh(path), AEK.core.save(path)), or pass --no-preflight if you are sure the project is saved."}
    job_id, text, first = wrap(body, kit=kit, undo=undo, args=args, libs=libs)
    res = submit(text, job_id, timeout=timeout, channel=channel)
    if res.get("ok") is False and (res.get("line") or res.get("rawLine")):
        map_error(res, body, job_id)
    if res.get("dirty") and res.get("project") == "":
        res["warning"] = ("The job left an untitled project with unsaved changes. In a shared or test session end the job with "
                          "AEK.core.save(<abs>.aep): a raw app.open or app.newProject by the next job would raise a Save As panel.")
    return res


# ---------- ready-made jobs ----------
def js(s):
    return json.dumps(s)


def frames(comp, out_dir, times=None, spread=None, prefix=None, sheet=False, timeout=600, channel="bridge", columns=None, project=None):
    """PNG frames of COMP in the project that is open NOW. On a shared After Effects another job may have opened a
    different project since your last call: pass project= (absolute .aep path) to refuse a mismatch, or better, capture
    the frames inside the job that opened or built the project (AEK.capture.spread)."""
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    guard = ""
    if project:
        guard = ("var __pf = app.project.file ? app.project.file.fsName : \"\"; if (__pf !== %s) { throw new Error(\"Open project is '\" + __pf + \"', not %s: "
                 "another job changed it. Capture the frames inside the job that opens the project.\"); }\n") % (js(os.path.realpath(project)), os.path.basename(project).replace('"', ""))
    if times:
        body = guard + "var c = AEK.core.comp(%s); return { fps: c.frameRate, frames: AEK.capture.frames(c, %s, %s, %s) };" % (js(comp), json.dumps(times), js(out_dir), js(prefix or ""))
    else:
        body = guard + "var c = AEK.core.comp(%s); return { fps: c.frameRate, frames: AEK.capture.spread(c, %d, %s, %s) };" % (js(comp), spread or 6, js(out_dir), js(prefix or ""))
    res = run_js(body, kit="core,capture", timeout=timeout, channel=channel)
    if res.get("ok") and sheet:
        fr = res["result"]["frames"]
        res["sheet"] = contact_sheet([f["path"] for f in fr], os.path.join(out_dir, (prefix or "sheet") + "_sheet.jpg"),
                                     labels=["F%d  %.2fS" % (f["frame"], f["time"]) for f in fr], columns=columns, bg=fr[0].get("bg") if fr else None)
    return res


FONT = {" ": "0000000000", "-": "0808080808", ".": "0060600000", "/": "2010080402", "0": "3E5149453E", "1": "00427F4000", "2": "4261514946",
        "3": "2141454B31", "4": "1814127F10", "5": "2745454539", "6": "3C4A494930", "7": "0171090503", "8": "3649494936", "9": "064949291E",
        ":": "0036360000", "A": "7E1111117E", "B": "7F49494936", "C": "3E41414122", "D": "7F4141221C", "E": "7F49494941", "F": "7F09090901",
        "G": "3E4149497A", "H": "7F0808087F", "I": "00417F4100", "J": "2040413F01", "K": "7F08142241", "L": "7F40404040", "M": "7F020C027F",
        "N": "7F0408107F", "O": "3E4141413E", "P": "7F09090906", "Q": "3E4151215E", "R": "7F09192946", "S": "4649494931", "T": "01017F0101",
        "U": "3F4040403F", "V": "1F2040201F", "W": "3F4038403F", "X": "6314081463", "Y": "0708700807", "Z": "6151494543", "_": "4040404040",
        "%": "2313086462", "(": "001C224100", ")": "0041221C00", "+": "08083E0808", "=": "1414141414", "#": "147F147F14"}


def label_png(text, path, scale=3):
    """A small yellow-on-black label as a PNG, drawn with a built-in 5x7 font (no font library, no ffmpeg drawtext needed)."""
    import struct, zlib
    text = text.upper()[:48]
    pad = 2
    w, h = (len(text) * 6 + pad * 2 - 1) * scale, (7 + pad * 2) * scale
    rows = [[0] * (w // scale) for _ in range(h // scale)]
    for i, ch in enumerate(text):
        cols = bytes.fromhex(FONT.get(ch, FONT["-"]))
        for x in range(5):
            for y in range(7):
                if cols[x] >> y & 1:
                    rows[pad + y][pad + i * 6 + x] = 1
    raw = b""
    for r in rows:
        line = b"\x00" + b"".join((b"\xff\xe1\x1a\xff" if v else b"\x00\x00\x00\xb4") * scale for v in r)
        raw += line * scale

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

    _write_bytes(path, b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    return path


def image_size(path):
    """(width, height) of a PNG from its header, of anything else through ffprobe."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
    except OSError:
        return None
    if shutil.which("ffprobe"):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True)
        try:
            w, h = r.stdout.strip().split(",")[:2]
            return int(w), int(h)
        except ValueError:
            return None
    return None


def contact_sheet(paths, out, labels=None, columns=None, tile_width=640, gain=None, max_width=1600, bg=None):
    """One JPEG with every frame in reading order, each labeled. Read this instead of the single frames.
    The sheet is scaled down to max_width pixels wide (1600 by default; 0 keeps the full width).
    Frames of different sizes are fitted into one tile box (the most common shape) with dark bars.
    gain multiplies the pixel values: 10 for frames saved from a 32 bpc project.
    saveFrameToPng writes the comp background as transparent (alpha 0, the comp color kept in RGB): bg ("RRGGBB", the
    `bg` field of AEK.capture.frame) flattens each frame onto that color first, so the sheet shows what a render shows.
    Without it alpha is dropped: soft edges (feather, glow, motion blur) read too bright and too hard."""
    import tempfile
    if not shutil.which("ffmpeg") or not paths:
        return None
    n = len(paths)
    cols = columns or (n if n <= 3 else (3 if n <= 9 else 4))
    rows = -(-n // cols)
    shapes = {}
    for p in paths:
        s = image_size(p)
        if s and s[0]:
            k = round(s[1] / float(s[0]), 3)
            shapes[k] = shapes.get(k, 0) + 1
    ratio = sorted(shapes.items(), key=lambda kv: -kv[1])[0][0] if shapes else 0.5625
    tile_height = max(2, int(round(tile_width * ratio / 2.0)) * 2)
    with tempfile.TemporaryDirectory() as tmp:
        cmd, chains = ["ffmpeg", "-y", "-v", "error"], []
        for p in paths:
            cmd += ["-i", p]
        for i in range(n):
            ch = "[%d:v]format=rgb48le," % i
            if bg:
                sz = image_size(paths[i]) or (1920, 1080)
                chains.append("color=c=0x%s:s=%dx%d,format=rgba[bg%d]" % (str(bg).lstrip("#"), sz[0], sz[1], i))
                chains.append("[%d:v]format=rgba[fg%d]" % (i, i))
                chains.append("[bg%d][fg%d]overlay=0:0:shortest=1:format=auto[fl%d]" % (i, i, i))
                ch = "[fl%d]format=rgb48le," % i
            if gain:
                ch += "lutrgb=r='clip(val*%s,0,maxval)':g='clip(val*%s,0,maxval)':b='clip(val*%s,0,maxval)'," % (gain, gain, gain)
            ch += "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=0x101010,setsar=1,format=rgb24" % (tile_width, tile_height, tile_width, tile_height)
            if labels:
                cmd += ["-i", label_png(labels[i], os.path.join(tmp, "l%03d.png" % i))]
                chains.append(ch + "[s%d]" % i)
                chains.append("[s%d][%d:v]overlay=8:8[t%d]" % (i, n + i, i))
            else:
                chains.append(ch + "[t%d]" % i)
        chains.append("".join("[t%d]" % i for i in range(n)) + "concat=n=%d:v=1:a=0,tile=%dx%d:padding=6:margin=6:color=0x202020" % (n, cols, rows)
                      + (",scale='min(iw,%d)':-2" % int(max_width) if max_width else ""))
        r = subprocess.run(cmd + ["-filter_complex", ";".join(chains), "-frames:v", "1", "-q:v", "3", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("contact sheet failed: %s\n" % r.stderr.strip()[-400:])
    return out if r.returncode == 0 and os.path.exists(out) else None


def has_alpha_png(path):
    """True for an RGBA or grey+alpha PNG (IHDR color type 6 or 4)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
        return head[:8] == b"\x89PNG\r\n\x1a\n" and head[25] in (4, 6)
    except OSError:
        return False


def count_frames(path):
    """Video packets actually in the file (reads the whole stream; header counts can describe frames that were never written)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        return None


def probe(path, count=False):
    if not shutil.which("ffprobe"):
        return {"ok": False, "error": "ffprobe not found"}
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], capture_output=True, text=True)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip()}
    d = json.loads(r.stdout)
    out = {"ok": True, "file": path, "size_mb": round(os.path.getsize(path) / 1048576.0, 2),
           "duration": float(d["format"].get("duration", 0) or 0), "bitrate_mbps": round(float(d["format"].get("bit_rate", 0) or 0) / 1e6, 2), "streams": []}
    for s in d["streams"]:
        e = {"type": s.get("codec_type"), "codec": s.get("codec_name"), "profile": s.get("profile")}
        if s.get("codec_type") == "video":
            num, den = (s.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
            e.update({"width": s.get("width"), "height": s.get("height"), "fps": round(float(num) / float(den or 1), 3), "pix_fmt": s.get("pix_fmt"),
                      "frames": int(s["nb_frames"]) if str(s.get("nb_frames", "")).isdigit() else None,
                      "color": [s.get("color_range"), s.get("color_space"), s.get("color_transfer"), s.get("color_primaries")],
                      "alpha": bool(re.match(r"(yuva|gbrap|rgba|bgra|argb|abgr|ayuv|ya\d)", s.get("pix_fmt", "")))})
        elif s.get("codec_type") == "audio":
            e.update({"sample_rate": s.get("sample_rate"), "channels": s.get("channels")})
        elif s.get("codec_type") == "data":
            # the "High Quality" output modules write a timecode track (tmcd); ffmpeg copies it unless -dn -write_tmcd 0
            e.update({"tag": s.get("codec_tag_string"), "timecode": s.get("codec_tag_string") == "tmcd" or "timecode" in (s.get("tags") or {})})
        out["streams"].append(e)
    if count and any(e["type"] == "video" for e in out["streams"]):
        out["frames_counted"] = count_frames(path)
    return out


def render(comp, out, template=None, render_settings=None, start=None, duration=None, timeout=3600, channel="bridge"):
    out = os.path.abspath(out)
    opts = {k: v for k, v in {"template": template, "renderSettings": render_settings, "start": start, "duration": duration}.items() if v is not None}
    body = "var c = AEK.core.comp(%s); return AEK.capture.queue(c, %s, %s);" % (js(comp), js(out), json.dumps(opts))
    res = run_js(body, kit="core,capture", timeout=timeout, channel=channel)
    if res.get("ok") and os.path.exists(res["result"]["path"]):
        res["probe"] = probe(res["result"]["path"])
    return res


def stop_tree(proc):
    """Stop aerender and the processes it started (same process group on macOS and Linux)."""
    import signal
    for sig in (signal.SIGTERM, getattr(signal, "SIGKILL", signal.SIGTERM)):
        try:
            if WIN:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
            else:
                os.killpg(os.getpgid(proc.pid), sig)
        except (OSError, ProcessLookupError):
            return
        try:
            proc.wait(15)
            return
        except subprocess.TimeoutExpired:
            continue


AERENDER_FAIL = re.compile(r"disk full|not enough (disk )?space|no space left|\(9988\)|9988|output module failed|unable to write|could not write|can not create a file|error while writing|error: ", re.I)
AERENDER_RETRY = "rerun once, alone, or give each aerender that runs at the same time its own output folder"


def span_frames(lines):
    """Frames of the rendered span from the log's "Duration: H:MM:SS:FF" (or "Duration: 00060" when the time display is frames) and "Frame Rate: N" lines (None when absent)."""
    dur = fps = None
    for l in lines:
        m = re.search(r"Duration:\s+(\d+):(\d+):(\d+)[:;](\d+)", l)
        if m and dur is None:
            dur = [int(g) for g in m.groups()]
        m = re.search(r"Duration:\s+(\d+)\s*$", l)   # time display in frames: "Duration: 00060"
        if m and dur is None:
            dur = int(m.group(1))
        m = re.search(r"Frame Rate:\s+([\d.]+)", l)
        if m and fps is None:
            fps = float(m.group(1))
    if isinstance(dur, int):
        return dur
    if dur is None or not fps:
        return None
    return int(round((dur[0] * 3600 + dur[1] * 60 + dur[2]) * round(fps))) + dur[3]


def free_gb(path):
    """Free space in GB on the volume that will hold path (its nearest existing parent)."""
    p = os.path.abspath(path)
    while p and not os.path.exists(p):
        p = os.path.dirname(p)
    try:
        return round(shutil.disk_usage(p or "/").free / 1e9, 1)
    except OSError:
        return None


def aerender(project, comp, out, template=None, render_settings=None, start=None, end=None, extra=None, min_free_gb=10.0, stall=300, frames_expected=None):
    """Render out of process. Fails (ok false, with "why") on: under min_free_gb free before the start, a "Disk Full" or
    output module error line (9988), no new output line for `stall` seconds (aerender is stopped), and a movie whose
    counted frames differ from the frames aerender reported or from frames_expected."""
    inst = installs()
    if not inst or not os.path.exists(inst[0]["aerender"]):
        return {"ok": False, "error": "aerender not found"}
    out_abs = os.path.abspath(out)
    created = None
    folder = os.path.dirname(out_abs)
    if not os.path.isdir(folder):
        # aerender does not create it: "Directory does not exist" after a full launch (about 15 s)
        try:
            os.makedirs(folder)
            created = folder
        except OSError as e:
            return {"ok": False, "why": "folder", "error": "Cannot create the output folder %s: %s" % (folder, e)}
    gb = free_gb(out_abs)
    if min_free_gb and gb is not None and gb < min_free_gb:
        return {"ok": False, "why": "disk", "free_gb": gb, "error": "Only %.1f GB free on the output volume (floor %.1f GB): free space or lower --min-free-gb. A full disk makes aerender fail with 'Disk Full' (9988), hang, or leave a short file." % (gb, min_free_gb)}
    cmd = [inst[0]["aerender"], "-project", os.path.abspath(project), "-comp", comp, "-output", os.path.abspath(out)]
    if template:
        cmd += ["-OMtemplate", template]
    if render_settings:
        cmd += ["-RStemplate", render_settings]
    if start is not None:
        cmd += ["-s", str(start)]
    if end is not None:
        cmd += ["-e", str(end)]
    cmd += extra or []
    import threading
    t0 = time.time()
    lines, last = [], [time.time()]
    # its own process group: aerender starts a second aerender and aerendercore, and a stop must reach all three
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
                            **({"start_new_session": True} if not WIN else {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}))

    def reader():
        for line in proc.stdout:
            lines.append(line.rstrip("\n"))
            last[0] = time.time()
    th = threading.Thread(target=reader, daemon=True)
    th.start()
    stalled = False
    while proc.poll() is None:
        if stall and time.time() - last[0] > stall:
            stalled = True
            stop_tree(proc)
            break
        time.sleep(0.5)
    th.join(5)
    rc = proc.wait()
    # "(n)" counts the frames of the span from 1 (also with -s and -e): the highest n is the number of frames rendered
    rendered = [int(m.group(1)) for l in lines for m in re.finditer(r"PROGRESS:\s+[\d:;]+\s+\((\d+)\)", l)]
    failed = [l for l in lines if AERENDER_FAIL.search(l)]
    span = span_frames(lines)
    res = {"ok": True, "returncode": rc, "seconds": round(time.time() - t0, 1), "command": cmd, "tail": lines[-12:],
           "frames_rendered": max(rendered) if rendered else None, "frames_span": span, "free_gb_before": gb, "free_gb_after": free_gb(out_abs)}
    if created:
        res["created_folder"] = created
    # every check by name: "ok", "failed: ...", or "skipped: ..."; the first failure becomes "why"
    checks = res["checks"] = {"free_space": "ok", "stall": "failed" if stalled else "ok", "log_errors": "failed: %d line(s)" % len(failed) if failed else "ok",
                              "returncode": "ok" if rc == 0 else "failed: %d" % rc, "file": "ok" if os.path.exists(out_abs) or "[#" in out_abs else "failed: missing",
                              "frames": "skipped: an earlier check failed"}
    if os.path.splitext(out_abs)[1].lower() not in (".mp4", ".mov", ".m4v", ".avi", ".mxf"):
        checks["frames"] = "not counted: audio or image output (no video stream to count)"
    why = None
    if stalled:
        why = ("stall", "aerender wrote nothing for %d s and was stopped (a full disk can hang it)." % stall)
    elif failed and re.search(r"directory does not exist", " ".join(failed), re.I):
        why = ("folder", "aerender reported: " + " | ".join(failed[:3]) + ". Create the output folder, then render again.")
    elif failed:
        why = ("disk" if re.search(r"disk|space|9988", " ".join(failed), re.I) else "render", "aerender reported: " + " | ".join(failed[:3]))
    elif rc != 0:
        why = ("render", "aerender exited with code %d" % rc)
    elif not os.path.exists(out_abs) and "[#" not in out_abs:
        why = ("missing", "no output file at " + out_abs)
    if not why and os.path.exists(out_abs) and os.path.splitext(out_abs)[1].lower() in (".mp4", ".mov", ".m4v", ".avi", ".mxf"):
        res["probe"] = probe(out_abs, count=True)
        n = res["probe"].get("frames_counted")
        # reference: the caller's count, else the span from the log header, else the highest PROGRESS frame. A file holding
        # MORE frames than PROGRESS lines show is not a failure (a line can be missed); fewer always is.
        want = frames_expected or span or res["frames_rendered"]
        xmp = any("failed to write xmp" in l.lower() for l in lines)
        hint = " (the log also says 'Failed to write XMP metadata': a disk-full sign)" if xmp else ""
        if res["probe"].get("ok") is False or not n:
            why = ("short", "the output file has no readable video frames" + hint)
        elif want and (n < want or ((frames_expected or span) and n != want)):
            why = ("short", "the file holds %d frames, %d were expected: treat it as failed (a disk that filled during the write does this while aerender exits 0)%s" % (n, want, hint))
        checks["frames"] = ("failed: %s" % why[1]) if why else ("ok: %d of %d" % (n, want) if want else "ok: %d counted, no reference to compare" % n)
        if not why and not want:
            res["warning"] = "no frame reference (no span in the log, no PROGRESS lines): pass frames_expected to check the count"
    left = free_gb(out_abs)
    if why and why[0] != "disk" and left is not None and left < 0.05:
        why = ("disk", "the output volume is full (%.2f GB left): %s" % (left, why[1]))
    if why:
        res.update({"ok": False, "why": why[0], "error": why[1]})
        if why[0] not in ("disk", "folder"):
            res["retry"] = AERENDER_RETRY
    return res


def restart(test_session=False, min_stale=180, cooldown=300, wait=180):
    """Unattended TEST sessions only: stop a blocked After Effects and start it again in the background.
    Refuses without --test-session, while the heartbeat is younger than min_stale seconds, while another agent restarts
    (lock folder in the bridge folder), and within `cooldown` seconds of the last restart. Never in a person's session:
    the stop discards their unsaved work and is treated as a crash (Crash Repair at the next launch, answered here)."""
    if not test_session:
        return {"ok": False, "error": "refused: pass --test-session. A restart discards unsaved work: never in a person's session; tell the person which window is open instead."}
    root = bridge_dir()
    s = status()
    if s is not None and s["age_s"] < min_stale:
        return {"ok": False, "error": "refused: the heartbeat is %.0f s old (floor %d s). A render or another agent's long job also stops it: wait, then retry." % (s["age_s"], min_stale), "status": s}
    lock, last = os.path.join(root, "restart.lock"), os.path.join(root, "restart.last")
    if os.path.exists(last) and time.time() - os.path.getmtime(last) < cooldown:
        return {"ok": False, "error": "refused: another agent restarted After Effects %.0f s ago. Wait for the heartbeat (`ae.py doctor`)." % (time.time() - os.path.getmtime(last))}
    try:
        os.makedirs(lock)
    except OSError:
        if time.time() - os.path.getmtime(lock) < 300:
            return {"ok": False, "error": "refused: another restart is running. Wait 60 s and read `ae.py doctor`."}
        os.rmdir(lock)
        os.makedirs(lock)
    import signal
    log = []
    try:
        _write_text(last, str(time.time()))
        inst = installs()
        if not inst:
            return {"ok": False, "error": "After Effects not found"}
        pid = ae_pid()
        if pid:
            if WIN:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
                for _ in range(20):
                    time.sleep(1)
                    if not ae_pid():
                        break
                if ae_pid():
                    os.kill(pid, signal.SIGKILL)
                    log.append("SIGKILL")
            log.append("stopped %d" % pid)
            # LaunchServices keeps a killed app registered for a moment: an `open` sent 1 s after SIGKILL did nothing (measured)
            for _ in range(15):
                if not ae_pid():
                    break
                time.sleep(1)
            time.sleep(3)
        t0, pressed = time.time(), 0
        for attempt in range(3):
            if MAC:
                r = subprocess.run(["open", "-g", "-a", inst[0]["app"]], capture_output=True, text=True)   # -g: does not take focus
                log.append("open rc %d%s at %.0f s" % (r.returncode, (": " + r.stderr.strip()[:120]) if r.stderr.strip() else "", time.time() - t0))
            else:
                subprocess.Popen([inst[0]["app"]])
            for _ in range(20):
                time.sleep(1)
                if ae_pid() and ae_pid() != pid:
                    break
            if ae_pid() and ae_pid() != pid:
                log.append("new process %d at %.0f s" % (ae_pid(), time.time() - t0))
                break
            time.sleep(5)
        else:
            return {"ok": False, "error": "After Effects did not start after three `open` calls", "log": log}
        while time.time() - t0 < wait:
            time.sleep(3)
            st = status()
            if st is not None and st["age_s"] < 6 and st.get("pid") != str(pid):
                return {"ok": True, "seconds": round(time.time() - t0, 1), "status": st, "log": log,
                        "next": "Read the result of the job that was running (interrupted: true), then check the project state before sending anything else."}
            # Crash Repair Options (default button Continue) and the Home screen take a posted Return; 10 s after launch, then every 20 s
            if ae_pid() and time.time() - t0 > 10 + pressed * 20:
                press("return")
                pressed += 1
                log.append("return at %.0f s" % (time.time() - t0))
        return {"ok": False, "error": "no heartbeat %d s after the relaunch: run `ae.py doctor` and `ae.py windows --shot DIR`" % wait, "log": log}
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


def video_frames(path, at, out_dir):
    """PNG frames cut from a movie at frame numbers `at` (accurate seek, full range)."""
    os.makedirs(out_dir, exist_ok=True)
    outs = []
    for n in at:
        o = os.path.join(out_dir, "%s_f%05d.png" % (os.path.splitext(os.path.basename(path))[0], n))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-vf", "select=eq(n\\,%d),scale=in_range=tv:out_range=pc" % n, "-frames:v", "1", o], capture_output=True)
        if os.path.exists(o):
            outs.append((n, o))
    return outs


def doctor():
    d = {"os": platform.platform(), "installs": installs(), "prefs": prefs_dirs(), "pid": ae_pid(), "bridge_dir": bridge_dir(),
         "status": status(), "ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "checks": []}
    c = d["checks"]
    if not d["installs"]:
        c.append("FAIL no After Effects found in the default location")
    if not d["pid"]:
        c.append("FAIL After Effects is not running (the bridge lives inside the application)")
    for p in d["prefs"][:1]:
        startup = os.path.join(p, "Scripts", "Startup", "ae_bridge.jsx")
        d["bridge_installed"] = os.path.exists(startup)
        c.append(("ok   " if d["bridge_installed"] else "WARN ") + "startup bridge: " + startup)
        for pf in glob.glob(os.path.join(p, "Adobe After Effects * Prefs.txt")):
            try:
                txt = _read_text(pf, errors="replace")
            except Exception:
                continue
            m = re.search(r'"Pref_SCRIPTING_FILE_NETWORK_SECURITY"\s*=\s*"(\d)"', txt)
            d["allow_file_network"] = (m.group(1) == "1") if m else None
            c.append(("ok   " if d["allow_file_network"] else "FAIL ") + "Allow Scripts to Write Files and Access Network (Settings > Scripting & Expressions)")
    s = d["status"]
    if s is None:
        c.append("FAIL no bridge heartbeat: run ae_bridge.jsx once from File > Scripts > Run Script File")
    elif s["age_s"] > 6:
        c.append("WARN bridge heartbeat is %.0f s old: After Effects is busy, closed, or showing a dialog" % s["age_s"])
    else:
        c.append("ok   bridge %s alive, After Effects %s, %d jobs so far" % (s.get("bridge"), s.get("ae"), s.get("jobs", 0)))
    d["windows"] = windows()
    extra = [w for w in d["windows"] if not w.get("main")]
    if extra:
        c.append("WARN %d extra window(s): %s" % (len(extra), ", ".join(repr(w["name"]) for w in extra)))
    for tool in ("ffmpeg", "ffprobe"):
        if not d[tool]:
            c.append("WARN %s not found: no contact sheets, no checks on delivered files" % tool)
    return d


def install_bridge():
    dirs = prefs_dirs()
    if not dirs:
        return {"ok": False, "error": "no After Effects preference folder found: start After Effects once first"}
    dst_dir = os.path.join(dirs[0], "Scripts", "Startup")
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, "ae_bridge.jsx")
    if os.path.exists(dst):
        shutil.copy2(dst, dst + ".previous")
    shutil.copy2(os.path.join(HERE, "ae_bridge.jsx"), dst)
    return {"ok": True, "installed": dst,
            "next": "Restart After Effects, or run the file once now from File > Scripts > Run Script File. Settings > Scripting & Expressions > Allow Scripts to Write Files and Access Network must be on."}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("install-bridge")
    r = sub.add_parser("run")
    r.add_argument("file", nargs="?")
    r.add_argument("-e", "--eval")
    r.add_argument("--kit", default="all", help="all, none, or a comma list: " + ",".join(KIT_ORDER))
    r.add_argument("--undo", help="name of ONE undo step that wraps the whole job")
    r.add_argument("--args", help="JSON given to the job as ARGS")
    r.add_argument("--lib", action="append", help="extra .jsx file inlined after the kit (repeatable): a sibling skill's helper module")
    r.add_argument("--print-job", action="store_true", help="print the wrapped job and stop")
    r.add_argument("--no-preflight", action="store_true", help="send the job even when it calls app.open, app.newProject or app.project.save() raw")
    for name in ("info", "audit", "stats"):
        sub.add_parser(name)
    f = sub.add_parser("frames")
    f.add_argument("comp")
    f.add_argument("--out", required=True)
    f.add_argument("--times", help="seconds, comma separated")
    f.add_argument("--spread", type=int, help="n frames spread over the work area (default 6)")
    f.add_argument("--prefix")
    f.add_argument("--sheet", action="store_true")
    f.add_argument("--columns", type=int)
    f.add_argument("--project", help="absolute .aep path the open project must be; refuses to capture another agent's project")
    q = sub.add_parser("render")
    q.add_argument("comp")
    q.add_argument("--out", required=True)
    q.add_argument("--template")
    q.add_argument("--render-settings")
    q.add_argument("--start", type=float)
    q.add_argument("--duration", type=float)
    t = sub.add_parser("templates")
    t.add_argument("comp")
    t.add_argument("--project", help="absolute .aep path the open project must be; refuses to read another agent's project")
    a = sub.add_parser("aerender")
    a.add_argument("--project", required=True)
    a.add_argument("--comp", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--template")
    a.add_argument("--render-settings")
    a.add_argument("--start", type=int, help="first frame")
    a.add_argument("--end", type=int, help="last frame")
    a.add_argument("--min-free-gb", type=float, default=10.0, help="refuse to start under this much free space on the output volume (default 10)")
    a.add_argument("--stall", type=int, default=300, help="stop aerender after this many seconds without a new output line (default 300, 0 = never)")
    a.add_argument("--frames", type=int, help="frames the file must hold (default: the frames aerender reported)")
    p = sub.add_parser("probe")
    p.add_argument("file")
    p.add_argument("--count", action="store_true", help="also count the video frames actually in the file")
    w = sub.add_parser("windows")
    w.add_argument("--shot")
    k = sub.add_parser("key")
    k.add_argument("key")
    rs = sub.add_parser("restart", help="unattended test sessions only: relaunch a blocked After Effects")
    rs.add_argument("--test-session", action="store_true", help="required: confirms no person works in this After Effects")
    rs.add_argument("--min-stale", type=int, default=180, help="refuse while the heartbeat is younger than this (s, default 180)")
    s = sub.add_parser("sheet")
    s.add_argument("out")
    s.add_argument("images", nargs="*")
    s.add_argument("--video", help="cut the frames from this movie instead of PNG files")
    s.add_argument("--at", help="frame numbers for --video, comma separated")
    s.add_argument("--bg", help="RRGGBB: flatten transparent PNG frames on this color (the comp background) before tiling")
    s.add_argument("--columns", type=int)
    s.add_argument("--gain", type=float, help="multiply pixel values: 10 for frames saved from a 32 bpc project")
    s.add_argument("--max-width", type=int, default=1600, help="scale the sheet down to this width in pixels (0 keeps the full width)")
    for x in (r, f, q, t):
        x.add_argument("--timeout", type=int, default=None)
        x.add_argument("--channel", default="bridge", choices=["bridge", "osascript", "exe", "handoff"])
    args = ap.parse_args()

    if args.cmd == "doctor":
        res = doctor()
    elif args.cmd == "install-bridge":
        res = install_bridge()
    elif args.cmd == "run":
        body = args.eval if args.eval else _read_text(args.file)
        jargs = json.loads(args.args) if args.args else None
        if args.print_job:
            print(wrap(body, kit=args.kit, undo=args.undo, args=jargs, libs=args.lib)[1])
            return 0
        res = run_js(body, kit=args.kit, undo=args.undo, timeout=args.timeout or 120, channel=args.channel, args=jargs, libs=args.lib, check=not args.no_preflight)
    elif args.cmd == "info":
        res = run_js("return AEK.core.info();", kit="core")
    elif args.cmd == "audit":
        res = run_js("var f = AEK.audit.all(); return { summary: AEK.audit.summary(f), findings: f };", kit="core,audit", timeout=300)
    elif args.cmd == "stats":
        res = run_js("return AEK.stats.snapshot();", kit="core,stats", timeout=300)
    elif args.cmd == "frames":
        times = [float(x) for x in args.times.split(",")] if args.times else None
        res = frames(args.comp, args.out, times=times, spread=args.spread, prefix=args.prefix, sheet=args.sheet,
                     timeout=args.timeout or 600, channel=args.channel, columns=args.columns, project=args.project)
    elif args.cmd == "render":
        res = render(args.comp, args.out, template=args.template, render_settings=args.render_settings, start=args.start,
                     duration=args.duration, timeout=args.timeout or 3600, channel=args.channel)
    elif args.cmd == "templates":
        guard = ""
        if args.project:
            guard = ("var __pf = app.project.file ? app.project.file.fsName : \"\"; if (__pf !== %s) { throw new Error(\"Open project is '\" + __pf + \"', not %s: "
                     "read the templates inside a job that opens your project (AEK.capture.templates).\"); }\n") % (js(os.path.realpath(args.project)), os.path.basename(args.project).replace('"', ""))
        res = run_js(guard + "return AEK.capture.templates(AEK.core.comp(%s));" % js(args.comp), kit="core,capture", timeout=args.timeout or 60, channel=args.channel)
    elif args.cmd == "aerender":
        res = aerender(args.project, args.comp, args.out, template=args.template, render_settings=args.render_settings, start=args.start, end=args.end,
                       min_free_gb=args.min_free_gb, stall=args.stall, frames_expected=args.frames)
    elif args.cmd == "probe":
        res = probe(args.file, count=args.count)
    elif args.cmd == "windows":
        res = {"ok": True, "windows": windows(args.shot)}
    elif args.cmd == "key":
        res = press(args.key)
    elif args.cmd == "restart":
        res = restart(test_session=args.test_session, min_stale=args.min_stale)
    elif args.cmd == "sheet":
        images, labels = list(args.images), [os.path.basename(i) for i in args.images]
        if args.video:
            import tempfile
            cut = video_frames(args.video, [int(x) for x in (args.at or "0").split(",")], tempfile.mkdtemp(prefix="ae_sheet_"))
            images, labels = [p for _, p in cut], ["F%d" % n for n, _ in cut]
        made = contact_sheet(images, args.out, labels=labels, columns=args.columns, gain=args.gain, max_width=args.max_width, bg=args.bg)
        res = {"ok": made is not None, "sheet": made}
        if not args.bg and any(has_alpha_png(i) for i in images):
            res["warning"] = ("PNG frames with alpha: the comp background is transparent in them. Pass --bg RRGGBB (the `bg` field "
                              "of AEK.capture.frame) or feathered and glowing edges read too bright on the sheet.")
        if made is None:
            res["error"] = "no sheet written: see stderr (ffmpeg missing, an unreadable image, or no images)"
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if res.get("ok", True) is not False else 1


if __name__ == "__main__":
    sys.exit(main())
