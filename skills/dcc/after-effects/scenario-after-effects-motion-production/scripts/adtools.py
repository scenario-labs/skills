#!/usr/bin/env python3
"""adtools.py: beat grid, cut snapping and loudness for commercial motion edits (Python 3 standard library + ffmpeg).

  adtools.py detect MUSIC.wav --fps 30 [--noise -30] [--min 0.05]   beats from a percussive stem (ffmpeg silencedetect)
  adtools.py grid --bpm 124 --offset 0.1 --seconds 20 --fps 30        beats from a known tempo and first-beat offset
  adtools.py snap SHEET.json BEATS.json [--max 8] [--min-shot 18] [--out SNAPPED.json]
  adtools.py loud FILE                                                 integrated loudness (LUFS), LRA and true peak (dBTP)
  adtools.py review AE_REPORT.json [--render FILE] [--rules RULES.json]  creative-lead scorecard (numbers only)
  adtools.py zone OVERLAY.png --name NAME [--source TEXT]           safe rectangle from a platform overlay PNG (ImageMagick)

Beat lists are {"fps", "beats_s": [...], "beats_f": [...]} with float frames; snapping rounds to whole frames.
"""
import argparse, json, re, subprocess, sys


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, data, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, **kw)



def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.stdout + p.stderr


def detect(path, fps, noise=-30.0, min_d=0.05):
    # silence_end marks the next onset on a stem whose hits decay below the threshold between beats
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
               "silencedetect=noise=%sdB:d=%s" % (noise, min_d), "-f", "null", "-"])
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    beats = list(ends)
    if starts and (not ends or starts[0] > 0.01) and starts[0] > 0.01:
        beats.insert(0, 0.0)   # audio starts loud: the first beat is at 0
    beats = sorted(set(round(b, 4) for b in beats))
    iv = [b - a for a, b in zip(beats, beats[1:])]
    med = sorted(iv)[len(iv) // 2] if iv else 0
    return {"source": path, "method": "silencedetect", "fps": fps, "beats_s": beats,
            "beats_f": [round(b * fps, 2) for b in beats], "median_interval_s": round(med, 4),
            "bpm_est": round(60.0 / med, 2) if med else None}


def grid(bpm, offset, seconds, fps):
    p = 60.0 / bpm
    beats, t = [], offset
    while t < seconds:
        beats.append(round(t, 4))
        t += p
    return {"method": "grid", "bpm": bpm, "offset_s": offset, "fps": fps, "beats_s": beats,
            "beats_f": [round(b * fps, 2) for b in beats]}


def nearest(f, beats_f):
    return min(beats_f, key=lambda b: abs(b - f))


def snap(sheet, beats, max_shift=8, min_shot=18):
    shots = sheet["shots"]
    bf = beats["beats_f"]
    rows = []
    for i in range(1, len(shots) + (1 if "endcard" in sheet else 0)):
        cur = shots[i] if i < len(shots) else sheet["endcard"]
        prev = shots[i - 1]
        old = cur["f0"]
        b = nearest(old, bf)
        new = int(round(b))
        lo = prev["f0"] + min_shot
        nxt = shots[i + 1]["f0"] if i + 1 < len(shots) else (sheet["endcard"]["f0"] if i < len(shots) and "endcard" in sheet else sheet["frames"])
        hi = nxt - min_shot
        ok = abs(new - old) <= max_shift and lo <= new <= hi
        if ok:
            cur["f0"] = new
            prev["f1"] = new
        rows.append({"cut": cur.get("id", "endcard"), "from": old, "to": cur["f0"], "beat_f": b,
                     "offset_before": round(old - b, 2), "offset_after": round(cur["f0"] - b, 2), "snapped": ok})
    if "endcard" in sheet:
        shots[-1]["f1"] = sheet["endcard"]["f0"]
    return sheet, rows


def loud(path):
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = out[out.rfind("Summary:"):] if "Summary:" in out else out
    def grab(pat):
        m = re.search(pat, tail)
        return float(m.group(1)) if m else None
    return {"file": path, "integrated_lufs": grab(r"I:\s+(-?[0-9.]+) LUFS"), "lra_lu": grab(r"LRA:\s+(-?[0-9.]+) LU"),
            "true_peak_dbtp": grab(r"Peak:\s+(-?[0-9.]+) dBFS")}


def zone(png, name, source=""):
    # platform templates paint the unsafe area and leave the safe area transparent: bounding box of the transparent pixels
    out = run(["magick", png, "-alpha", "extract", "-negate", "-format", "%@ %w %h", "info:"]).strip().split()
    m = re.match(r"(\d+)x(\d+)\+(\d+)\+(\d+)", out[0])
    w, h, x, y = [int(v) for v in m.groups()]
    W, H = int(out[1]), int(out[2])
    return {name: {"top": round(y / H, 5), "bottom": round(1 - (y + h) / H, 5), "left": round(x / W, 5),
                   "right": round(1 - (x + w) / W, 5), "source": source or png, "px": [x, y, x + w, y + h], "size": [W, H]}}


DEFAULT_RULES = {
    "hook_text_by_frame": 3,          # [added] the hook line is on screen within the first 3 frames
    "first_cut_max_f": 45,            # [added] the opening shot changes within 1.5 s at 30 fps
    "min_text_frames": 30,            # 1 s minimum on screen (Plainly caption guidance: 1 to 7 s)
    "frames_per_word": 9,             # [added] reading-rate floor at 30 fps, plus the base below
    "text_base_frames": 12,           # [added]
    "max_words": 7,                   # [added] words per on-screen line set
    "cuts_per_10s_min": 4,            # [added] fast social cut, game ads
    "cuts_per_10s_max": 12,           # [added]
    "logo_not_before_f": 30,          # Derek Lieu: an unknown logo does not open the piece
    "cta_min_frames": 60,             # [added] CTA readable and tappable for 2 s or more
    "endcard_min_frames": 75,         # [added] 2.5 s hold at 30 fps
    "max_beat_offset_f": 1,           # cuts within 1 frame of a beat
    "lufs_target": -14.0, "lufs_tol": 1.0, "true_peak_max": -1.0
}


def review(rep, render=None, rules=None):
    r = dict(DEFAULT_RULES)
    r.update(rules or {})
    fps = rep["fps"]
    rows = []
    def add(name, value, ok, note=""):
        rows.append({"check": name, "value": value, "pass": bool(ok), "note": note})
    add("hook text on screen by frame", rep["hook_text_frame"], rep["hook_text_frame"] is not None and rep["hook_text_frame"] <= r["hook_text_by_frame"])
    add("first cut frame", rep["first_cut_f"], rep["first_cut_f"] <= r["first_cut_max_f"])
    for t in rep["texts"]:
        need = max(r["min_text_frames"], r["text_base_frames"] + r["frames_per_word"] * t["words"])
        add("text '%s' frames (%d words, needs %d)" % (t["text"], t["words"], need), t["frames"],
            t["frames"] >= need and t["words"] <= r["max_words"])
    for w in rep["cuts_per_10s"]:
        add("cuts in %s" % w["window"], w["cuts"], r["cuts_per_10s_min"] <= w["cuts"] <= r["cuts_per_10s_max"])
    add("logo first frame", rep["logo_first_f"], rep["logo_first_f"] is None or rep["logo_first_f"] >= r["logo_not_before_f"])
    add("CTA visible frames", rep["cta_frames"], rep["cta_frames"] >= r["cta_min_frames"])
    add("end card hold frames", rep["endcard_frames"], rep["endcard_frames"] >= r["endcard_min_frames"])
    if rep.get("beat_offsets") is not None:
        worst = max([abs(x["offset"]) for x in rep["beat_offsets"]] or [0])
        add("worst cut-to-beat offset (frames)", worst, worst <= r["max_beat_offset_f"])
    add("safe-zone violations", len(rep["zone_violations"]), len(rep["zone_violations"]) == 0,
        "; ".join(sorted(set(v["layer"] + "@" + v["zone"] for v in rep["zone_violations"])))[:300])
    if render:
        L = loud(render)
        add("integrated loudness (LUFS)", L["integrated_lufs"], L["integrated_lufs"] is not None and abs(L["integrated_lufs"] - r["lufs_target"]) <= r["lufs_tol"])
        add("true peak (dBTP)", L["true_peak_dbtp"], L["true_peak_dbtp"] is not None and L["true_peak_dbtp"] <= r["true_peak_max"])
    return {"comp": rep.get("comp"), "fps": fps, "passed": sum(1 for x in rows if x["pass"]), "total": len(rows),
            "rows": rows, "person_judges": [
                "Does frame 0 stop the scroll with the sound off?",
                "Is the one thing a viewer would tell a friend visible in the first 3 s?",
                "Does each shot pass clear, interesting, new, pretty (in that order)?",
                "Does the intensity curve dip before the payoff and rise again?",
                "Do sound hits feel on the picture at full frame rate?",
                "Is the call to action the only ask on the end card?"]}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect"); d.add_argument("file"); d.add_argument("--fps", type=float, default=30); d.add_argument("--noise", type=float, default=-30); d.add_argument("--min", type=float, default=0.05)
    g = sub.add_parser("grid"); g.add_argument("--bpm", type=float, required=True); g.add_argument("--offset", type=float, default=0); g.add_argument("--seconds", type=float, required=True); g.add_argument("--fps", type=float, default=30)
    s = sub.add_parser("snap"); s.add_argument("sheet"); s.add_argument("beats"); s.add_argument("--max", type=int, default=8); s.add_argument("--min-shot", type=int, default=18); s.add_argument("--out")
    l = sub.add_parser("loud"); l.add_argument("file")
    z = sub.add_parser("zone"); z.add_argument("png"); z.add_argument("--name", required=True); z.add_argument("--source", default="")
    v = sub.add_parser("review"); v.add_argument("report"); v.add_argument("--render"); v.add_argument("--rules")
    a = ap.parse_args()
    if a.cmd == "detect":
        res = detect(a.file, a.fps, a.noise, a.min)
    elif a.cmd == "grid":
        res = grid(a.bpm, a.offset, a.seconds, a.fps)
    elif a.cmd == "snap":
        sheet = _read_json(a.sheet); beats = _read_json(a.beats)
        sheet, rows = snap(sheet, beats, a.max, a.min_shot)
        if a.out:
            _write_json(a.out, sheet, indent=1)
        res = {"cuts": rows, "out": a.out}
    elif a.cmd == "loud":
        res = loud(a.file)
    elif a.cmd == "zone":
        res = zone(a.png, a.name, a.source)
    else:
        rep = _read_json(a.report)
        rep = rep.get("result", rep)
        rep = rep.get("report", rep)
        res = review(rep, a.render, _read_json(a.rules) if a.rules else None)
    json.dump(res, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
