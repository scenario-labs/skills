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
  ae.py aerender --project P.aep --comp "Comp" --out FILE [--template T]
  ae.py probe FILE                     ffprobe summary of a delivered file
  ae.py windows [--shot DIR]           After Effects windows (a second window usually means a dialog)
  ae.py key return|escape|tab          press one key in After Effects without bringing it forward

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
            apps = glob.glob(os.path.join(d, "Adobe After Effects *.app"))
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
        r = subprocess.run(["pgrep", "-f", "MacOS/After Effects"], capture_output=True, text=True)
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


def wrap(body, kit="all", undo=None, job_id=None, args=None, libs=None):
    """Build a self-reporting job. Returns (job_id, text, first_body_line). The job writes outbox/<id>.json itself."""
    job_id = job_id or "j%d_%s" % (int(time.time() * 1000), uuid.uuid4().hex[:6])
    out = os.path.join(bridge_dir(), "outbox", job_id + ".json").replace("\\", "/")
    head = "// job %s (ae.py)\n(function () {\nvar __res = { ok: true, id: %s }, __t0 = (new Date()).getTime();\n" % (job_id, json.dumps(job_id))
    # alert(), confirm() and prompt() would open a modal window that blocks every later job: inside a job they only log
    head += ("var __said = [];\nvar alert = function (m) { __said.push(\"alert: \" + m); };\n"
             "var confirm = function (m) { __said.push(\"confirm (answered true): \" + m); return true; };\n"
             "var prompt = function (m, d) { __said.push(\"prompt (answered default): \" + m); return d === undefined ? \"\" : d; };\n")
    head += kit_source(kit)
    for lib in libs or []:
        head += _read_text(lib).rstrip() + "\n"
    head += "var ARGS = %s;\n" % json.dumps(args if args is not None else {})
    head += "var __undo = %s;\nif (__undo) { app.beginUndoGroup(__undo); }\ntry {\n__res.result = (function () {\n" % json.dumps(undo or "")
    first = head.count("\n") + 1
    tail = (
        "\n})();\n} catch (__e) { __res.ok = false; __res.error = __e.toString(); __res.line = (__e.line || 0) - %d; }\n"
        "if (__undo) { app.endUndoGroup(); }\n"
        "if (__said.length) { __res.dialogs = __said; }\n"
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
        info["error"] = ("After Effects has not polled for %.0f s: it is busy (render, import, heavy script) or a modal dialog is open." % s["age_s"]) + \
            (" %d extra window(s) on screen: run `ae.py windows --shot DIR`, look at the picture, then `ae.py key return` or `escape`." % len(extra) if extra else "")
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
    if channel == "bridge":
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
    while time.time() - t0 < timeout:
        if os.path.exists(out):
            time.sleep(0.05)
            try:
                return _read_json(out)
            except Exception:
                time.sleep(0.2)
                try:
                    return _read_json(out)
                except Exception as e:
                    return {"ok": False, "error": "unreadable result %s: %s" % (out, e)}
        time.sleep(0.15)
    blocked = explain_block()
    blocked["job"] = job_id
    blocked["note"] = "The job file may still run when After Effects is free again. Check outbox/%s.json before sending it twice." % job_id
    return blocked


def run_js(body, kit="all", undo=None, timeout=120, channel="bridge", args=None, libs=None):
    job_id, text, first = wrap(body, kit=kit, undo=undo, args=args, libs=libs)
    res = submit(text, job_id, timeout=timeout, channel=channel)
    if res.get("ok") is False and res.get("line"):
        lines = body.split("\n")
        n = res["line"]
        if 1 <= n <= len(lines):
            res["source"] = lines[n - 1].strip()
    return res


# ---------- ready-made jobs ----------
def js(s):
    return json.dumps(s)


def frames(comp, out_dir, times=None, spread=None, prefix=None, sheet=False, timeout=600, channel="bridge", columns=None):
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    if times:
        body = "var c = AEK.core.comp(%s); return { fps: c.frameRate, frames: AEK.capture.frames(c, %s, %s, %s) };" % (js(comp), json.dumps(times), js(out_dir), js(prefix or ""))
    else:
        body = "var c = AEK.core.comp(%s); return { fps: c.frameRate, frames: AEK.capture.spread(c, %d, %s, %s) };" % (js(comp), spread or 6, js(out_dir), js(prefix or ""))
    res = run_js(body, kit="core,capture", timeout=timeout, channel=channel)
    if res.get("ok") and sheet:
        fr = res["result"]["frames"]
        res["sheet"] = contact_sheet([f["path"] for f in fr], os.path.join(out_dir, (prefix or "sheet") + "_sheet.jpg"),
                                     labels=["F%d  %.2fS" % (f["frame"], f["time"]) for f in fr], columns=columns)
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


def contact_sheet(paths, out, labels=None, columns=None, tile_width=640, gain=None):
    """One JPEG with every frame in reading order, each labeled. Read this instead of the single frames.
    Frames of different sizes are fitted into one tile box (the most common shape) with dark bars.
    gain multiplies the pixel values: 10 for frames saved from a 32 bpc project."""
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
            if gain:
                ch += "lutrgb=r='clip(val*%s,0,maxval)':g='clip(val*%s,0,maxval)':b='clip(val*%s,0,maxval)'," % (gain, gain, gain)
            ch += "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=0x101010,setsar=1,format=rgb24" % (tile_width, tile_height, tile_width, tile_height)
            if labels:
                cmd += ["-i", label_png(labels[i], os.path.join(tmp, "l%03d.png" % i))]
                chains.append(ch + "[s%d]" % i)
                chains.append("[s%d][%d:v]overlay=8:8[t%d]" % (i, n + i, i))
            else:
                chains.append(ch + "[t%d]" % i)
        chains.append("".join("[t%d]" % i for i in range(n)) + "concat=n=%d:v=1:a=0,tile=%dx%d:padding=6:margin=6:color=0x202020" % (n, cols, rows))
        r = subprocess.run(cmd + ["-filter_complex", ";".join(chains), "-frames:v", "1", "-q:v", "3", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("contact sheet failed: %s\n" % r.stderr.strip()[-400:])
    return out if r.returncode == 0 and os.path.exists(out) else None


def probe(path):
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
        out["streams"].append(e)
    return out


def render(comp, out, template=None, render_settings=None, start=None, duration=None, timeout=3600, channel="bridge"):
    out = os.path.abspath(out)
    opts = {k: v for k, v in {"template": template, "renderSettings": render_settings, "start": start, "duration": duration}.items() if v is not None}
    body = "var c = AEK.core.comp(%s); return AEK.capture.queue(c, %s, %s);" % (js(comp), js(out), json.dumps(opts))
    res = run_js(body, kit="core,capture", timeout=timeout, channel=channel)
    if res.get("ok") and os.path.exists(res["result"]["path"]):
        res["probe"] = probe(res["result"]["path"])
    return res


def aerender(project, comp, out, template=None, render_settings=None, start=None, end=None, extra=None):
    inst = installs()
    if not inst or not os.path.exists(inst[0]["aerender"]):
        return {"ok": False, "error": "aerender not found"}
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
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().split("\n")[-12:]
    ok = r.returncode == 0 and not any("ERROR" in line.upper() and "aerender" in line.lower() for line in tail)
    res = {"ok": ok, "returncode": r.returncode, "seconds": round(time.time() - t0, 1), "command": cmd, "tail": tail}
    if ok and os.path.exists(os.path.abspath(out)):
        res["probe"] = probe(os.path.abspath(out))
    return res


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
    q = sub.add_parser("render")
    q.add_argument("comp")
    q.add_argument("--out", required=True)
    q.add_argument("--template")
    q.add_argument("--render-settings")
    q.add_argument("--start", type=float)
    q.add_argument("--duration", type=float)
    t = sub.add_parser("templates")
    t.add_argument("comp")
    a = sub.add_parser("aerender")
    a.add_argument("--project", required=True)
    a.add_argument("--comp", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--template")
    a.add_argument("--render-settings")
    a.add_argument("--start", type=int, help="first frame")
    a.add_argument("--end", type=int, help="last frame")
    p = sub.add_parser("probe")
    p.add_argument("file")
    w = sub.add_parser("windows")
    w.add_argument("--shot")
    k = sub.add_parser("key")
    k.add_argument("key")
    s = sub.add_parser("sheet")
    s.add_argument("out")
    s.add_argument("images", nargs="+")
    s.add_argument("--columns", type=int)
    s.add_argument("--gain", type=float, help="multiply pixel values: 10 for frames saved from a 32 bpc project")
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
        res = run_js(body, kit=args.kit, undo=args.undo, timeout=args.timeout or 120, channel=args.channel, args=jargs, libs=args.lib)
    elif args.cmd == "info":
        res = run_js("return AEK.core.info();", kit="core")
    elif args.cmd == "audit":
        res = run_js("var f = AEK.audit.all(); return { summary: AEK.audit.summary(f), findings: f };", kit="core,audit", timeout=300)
    elif args.cmd == "stats":
        res = run_js("return AEK.stats.snapshot();", kit="core,stats", timeout=300)
    elif args.cmd == "frames":
        times = [float(x) for x in args.times.split(",")] if args.times else None
        res = frames(args.comp, args.out, times=times, spread=args.spread, prefix=args.prefix, sheet=args.sheet,
                     timeout=args.timeout or 600, channel=args.channel, columns=args.columns)
    elif args.cmd == "render":
        res = render(args.comp, args.out, template=args.template, render_settings=args.render_settings, start=args.start,
                     duration=args.duration, timeout=args.timeout or 3600, channel=args.channel)
    elif args.cmd == "templates":
        res = run_js("return AEK.capture.templates(AEK.core.comp(%s));" % js(args.comp), kit="core,capture", timeout=args.timeout or 60, channel=args.channel)
    elif args.cmd == "aerender":
        res = aerender(args.project, args.comp, args.out, template=args.template, render_settings=args.render_settings, start=args.start, end=args.end)
    elif args.cmd == "probe":
        res = probe(args.file)
    elif args.cmd == "windows":
        res = {"ok": True, "windows": windows(args.shot)}
    elif args.cmd == "key":
        res = press(args.key)
    elif args.cmd == "sheet":
        made = contact_sheet(args.images, args.out, labels=[os.path.basename(i) for i in args.images], columns=args.columns, gain=args.gain)
        res = {"ok": made is not None, "sheet": made}
        if made is None:
            res["error"] = "no sheet written: see stderr (ffmpeg missing, an unreadable image, or no images)"
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if res.get("ok", True) is not False else 1


if __name__ == "__main__":
    sys.exit(main())
