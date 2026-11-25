#!/usr/bin/env python3
"""adtools.py: beat grid, cut snapping and loudness for commercial motion edits (Python 3 standard library + ffmpeg).

  adtools.py detect MUSIC --fps 30 [--seconds 60] [--bpm-range 70,180]  tempo and beat grid from a full mix (onset envelope + autocorrelation)
  adtools.py detect STEM.wav --method silence [--noise -30] [--min 0.05]  onsets of a percussive stem (ffmpeg silencedetect)
  adtools.py grid --bpm 124 --offset 0.1 --seconds 20 --fps 30        beats from a known tempo and first-beat offset
  adtools.py snap SHEET.json BEATS.json [--max 8] [--min-shot 18] [--out SNAPPED.json]
  adtools.py loud FILE                                                 integrated loudness (LUFS), LRA and true peak (dBTP)
  adtools.py review AE_REPORT.json [--render MIX] [--picture MOVIE] [--rules RULES.json]  creative-lead scorecard (numbers only)
  adtools.py occupancy MOVIE [--fps 30]                               share of each frame that carries content (near-empty stretches)
  adtools.py contrast FRAME.png --box x,y,w,h --fill RRGGBB           contrast ratio of a text color against the plate behind it
  adtools.py zone OVERLAY.png --name NAME [--source TEXT]           safe rectangle from a platform overlay PNG (ImageMagick)

Beat lists are {"fps", "beats_s": [...], "beats_f": [...]} with float frames; snapping rounds to whole frames.
"""
import argparse, array, json, math, re, subprocess, sys


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, data, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, **kw)



def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.stdout + p.stderr


SR, HOP = 22050, 256          # 11.6 ms per envelope step: about a third of a frame at 30 fps
BANDS = ["lowpass=f=150", "bandpass=f=1500:width_type=o:w=2", "highpass=f=6000"]   # kick, snare and body, hats


def band_envelope(path, filt, seconds, start):
    """Log energy per hop of one band, as a list. ffmpeg decodes to mono float at SR."""
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(seconds), "-i", path, "-ac", "1", "-ar", str(SR), "-af", filt, "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    a = array.array("f")
    a.frombytes(raw[:len(raw) - len(raw) % 4])
    env = []
    for i in range(0, len(a) - HOP, HOP):
        e = 0.0
        for v in a[i:i + HOP]:
            e += v * v
        env.append(math.log10(1e-10 + e / HOP))
    return env


def onset_envelope(path, seconds, start=0.0):
    """Half-wave rectified rise of log energy, summed over three bands, then mean-removed: high where a hit starts."""
    total = None
    for filt in BANDS:
        env = band_envelope(path, filt, seconds, start)
        d = [max(0.0, env[i] - env[i - 1]) if i else 0.0 for i in range(len(env))]
        m = sum(d) / len(d) if d else 0
        sd = math.sqrt(sum((x - m) ** 2 for x in d) / len(d)) if d else 1
        d = [(x - m) / (sd or 1) for x in d]
        total = d if total is None else [a + b for a, b in zip(total, d)]
    return [max(0.0, x) for x in (total or [])]


def tempo_fit(env, lo=70.0, hi=180.0):
    """Tempo by autocorrelation of the onset envelope, weighted toward 120 BPM (log-normal, 1 octave), with the
    peak-to-median ratio as confidence. Returns bpm, period in hops, confidence and the two octave alternatives."""
    hps = SR / float(HOP)
    n = len(env)
    m = sum(env) / n
    x = [v - m for v in env]
    lag_lo, lag_hi = int(60 * hps / hi), int(math.ceil(60 * hps / lo))
    acf = {}
    for lag in range(max(1, lag_lo - 2), min(n - 1, lag_hi + 3)):
        acf[lag] = sum(x[i] * x[i + lag] for i in range(n - lag)) / (n - lag)
    def score(lag):
        bpm = 60 * hps / lag
        return acf[lag] * math.exp(-0.5 * (math.log2(bpm / 120.0) / 1.0) ** 2)
    lags = [l for l in range(lag_lo, lag_hi + 1) if l in acf]
    best = max(lags, key=score)
    # parabolic refinement of the peak
    if best - 1 in acf and best + 1 in acf:
        a, b, c = acf[best - 1], acf[best], acf[best + 1]
        den = a - 2 * b + c
        shift = 0.5 * (a - c) / den if den else 0.0
    else:
        shift = 0.0
    period = best + max(-0.5, min(0.5, shift))
    var = sum(v * v for v in x) / n or 1e-9
    conf = acf[best] / var          # normalized autocorrelation at the beat period: 0 none, 1 a perfect pulse
    return {"bpm": 60 * hps / period, "period_hops": period, "confidence": round(conf, 3),
            "alternatives": [round(60 * hps / period / 2, 2), round(60 * hps / period * 2, 2)]}


def comb(env, period, ph):
    """Mean onset strength on the grid ph + k * period (linear interpolation between hops)."""
    n, s, t, cnt = len(env), 0.0, ph, 0
    while t < n - 1:
        i = int(t)
        f = t - i
        s += env[i] * (1 - f) + env[i + 1] * f
        cnt += 1
        t += period
    return s / max(1, cnt)


def phase_fit(env, period):
    """First-beat offset (in hops) that puts the most onset energy on the grid."""
    best, best_s = 0.0, -1.0
    for k in range(int(math.ceil(period * 4))):
        sc = comb(env, period, k / 4.0)
        if sc > best_s:
            best, best_s = k / 4.0, sc
    return best, best_s


def comb_fit(env, period):
    """Tempo and phase together: the autocorrelation peak is only good to about 0.5 %, which drifts a quarter beat over
    a minute. Scan the period within 1.5 % in 0.05 % steps and keep the grid that collects the most onset energy."""
    best = (period, 0.0, -1.0)
    for j in range(-30, 31):
        p = period * (1 + j * 0.0005)
        ph, sc = phase_fit(env, p)
        if sc > best[2]:
            best = (p, ph, sc)
    return best


def detect_onsets(path, fps, seconds=60.0, start=0.0, lo=70.0, hi=180.0):
    """Tempo and a beat grid from a full mix: no stem, no silence between beats needed."""
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip().split()[0])
    span = min(seconds, max(0.0, dur - start))
    env = onset_envelope(path, span, start)
    if len(env) < 200:
        return {"source": path, "method": "onset", "error": "under 3 s of audio: give at least 8 s, or pass a known tempo to `grid`"}
    hps = SR / float(HOP)
    tf = tempo_fit(env, lo, hi)
    tf["period_hops"], ph, ph_score = comb_fit(env, tf["period_hops"])
    tf["bpm"] = 60 * hps / tf["period_hops"]
    period_s = tf["period_hops"] / hps
    offset = start + ph / hps
    # refine: least-squares line through the onset peaks found near each grid beat (sub-hop, parabolic), so a
    # 1 % tempo error does not drift 60 ms over a minute
    pts, k, t = [], 0, ph
    while t < len(env) - 4:
        i = int(round(t))
        lo_i = max(1, i - 2)
        w = env[lo_i:i + 3]
        j = lo_i + w.index(max(w))
        if env[j] > 1.0 and 0 < j < len(env) - 1:
            a, b, c = env[j - 1], env[j], env[j + 1]
            den = a - 2 * b + c
            pts.append((k, j + (0.5 * (a - c) / den if den else 0.0)))
        k += 1
        t += tf["period_hops"]
    if len(pts) >= 8:
        mk = sum(p[0] for p in pts) / len(pts)
        mt = sum(p[1] for p in pts) / len(pts)
        sxx = sum((p[0] - mk) ** 2 for p in pts)
        slope = sum((p[0] - mk) * (p[1] - mt) for p in pts) / sxx if sxx else tf["period_hops"]
        if abs(slope / tf["period_hops"] - 1) < 0.03:
            period_s = slope / hps
            offset = start + (mt - slope * mk) / hps
            tf["bpm"] = 60.0 / period_s
    while offset - period_s >= -1e-6:
        offset -= period_s
    beats, t = [], offset
    while t < dur:
        if t >= 0:
            beats.append(round(t, 4))
        t += period_s
    # how close real onsets sit to the grid inside the analysed span: median distance to the local peak, in ms
    dev = []
    for b in beats:
        if start <= b < start + span:
            i = int(round((b - start) * hps))
            w = env[max(0, i - 3):i + 4]
            if w and max(w) > 0.5:
                dev.append(abs(w.index(max(w)) - min(3, i)) / hps * 1000)
    dev.sort()
    res = {"source": path, "method": "onset", "fps": fps, "bpm": round(tf["bpm"], 3), "offset_s": round(offset, 4),
           "period_s": round(period_s, 5), "confidence": tf["confidence"], "octave_alternatives": tf["alternatives"],
           "analysed_s": [round(start, 2), round(start + span, 2)], "median_onset_offset_ms": round(dev[len(dev) // 2], 1) if dev else None,
           "beats_s": beats, "beats_f": [round(b * fps, 2) for b in beats]}
    if tf["confidence"] < 0.2 or not dev or dev[len(dev) // 2] > 25:
        res["warning"] = ("Low confidence: no steady pulse found in the analysed span (ambient score, rubato, or a long intro). Check two bars by ear "
                          "against a click, try --start past the intro, or pass a known tempo to `grid`. Octave alternatives: %s BPM." % tf["alternatives"])
    return res


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
    "lufs_target": -14.0, "lufs_tol": 1.0, "true_peak_max": -1.0,
    "hook_shows_product": True,       # [added] the shot under the hook line is tagged product: true in the sheet
    "min_occupancy": 0.03,            # [added] a frame with under 3 % of its area carrying content reads as empty
    "max_low_frames": 9,              # [added] no stretch of near-empty frames longer than 0.3 s at 30 fps
    "endcard_min_occupancy": 0.08,    # [added] end-card hold: at least 8 % of the frame carries content (median)
    "short_spot_s": 10,               # [added] under 10 s: holds below replace the 15 to 30 s ones
    "short_endcard_min_frames": 45, "short_cta_min_frames": 45
}


def occupancy(path, fps=None, w=96, h=54):
    """Share of each frame (0 to 1) whose pixels differ by more than 12 levels from the frame's median, on a 96x54 grey
    copy: a flat background reads 0, a full photo about 0.5. One value per frame of the movie."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"], capture_output=True).stdout
    n, out = len(raw) // (w * h), []
    for i in range(n):
        fr = raw[i * w * h:(i + 1) * w * h]
        med = sorted(fr)[len(fr) // 2]
        out.append(round(sum(1 for v in fr if abs(v - med) > 12) / float(w * h), 4))
    return out


def low_runs(occ, floor, min_len):
    runs, start = [], None
    for i, v in enumerate(occ + [1.0]):
        if v < floor and start is None:
            start = i
        elif v >= floor and start is not None:
            if i - start >= min_len:
                runs.append([start, i - 1])
            start = None
    return runs


def contrast(png, box, fill):
    """WCAG contrast ratio between a text color and the median luminance of the plate inside the text box (pixels within
    40 levels of the fill are text and are left out). 4.5 is the floor for body text, 3 for large type."""
    x, y, bw, bh = [int(v) for v in box.split(",")]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-vf", "crop=%d:%d:%d:%d,format=rgb24" % (bw, bh, x, y), "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = [int(fill[i:i + 2], 16) for i in (0, 2, 4)]
    def lum(rgb):
        c = [v / 255.0 for v in rgb]
        c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    plate = []
    for i in range(0, len(raw) - 2, 3):
        px = raw[i:i + 3]
        if max(abs(px[k] - fr[k]) for k in range(3)) > 40:
            plate.append(lum(px))
    if not plate:
        return {"error": "no plate pixels in the box"}
    plate.sort()
    pl, p90, lf = plate[len(plate) // 2], plate[int(len(plate) * 0.9)], lum(fr)
    ratio = lambda a, b: (max(a, b) + 0.05) / (min(a, b) + 0.05)
    return {"ratio_median": round(ratio(lf, pl), 2), "ratio_worst10": round(ratio(lf, p90 if lf < p90 else plate[int(len(plate) * 0.1)]), 2), "plate_pixels": len(plate)}


def review(rep, render=None, rules=None, picture=None):
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
        # a window shorter than 10 s (a 5 s spot, the tail of a 25 s ad) gets the range scaled to its length
        a, b = [int(v) for v in w["window"].split("-")]
        k = (b - a) / (10.0 * fps)
        if k < 0.3:
            continue
        lo, hi = int(math.floor(r["cuts_per_10s_min"] * k)), int(math.ceil(r["cuts_per_10s_max"] * k))
        add("cuts in %s (range %d to %d for %.1f s)" % (w["window"], lo, hi, k * 10), w["cuts"], lo <= w["cuts"] <= hi)
    short = rep.get("frames", 0) < r["short_spot_s"] * fps
    add("logo first frame", rep["logo_first_f"], rep["logo_first_f"] is None or rep["logo_first_f"] >= r["logo_not_before_f"])
    add("CTA visible frames", rep["cta_frames"], rep["cta_frames"] >= (r["short_cta_min_frames"] if short else r["cta_min_frames"]), "short spot" if short else "")
    add("end card hold frames", rep["endcard_frames"], rep["endcard_frames"] >= (r["short_endcard_min_frames"] if short else r["endcard_min_frames"]), "short spot" if short else "")
    if r["hook_shows_product"] and "hook_shot" in rep:
        hs = rep["hook_shot"] or {}
        add("hook line over a product shot", hs.get("layer"), bool(hs.get("product")),
            "tag the shot product: true in the sheet when it shows the product or its use; a mood image under the hook is a cold open the brief must ask for")
    if rep.get("beat_offsets") is not None:
        worst = max([abs(x["offset"]) for x in rep["beat_offsets"]] or [0])
        add("worst cut-to-beat offset (frames)", worst, worst <= r["max_beat_offset_f"])
    add("safe-zone violations", len(rep["zone_violations"]), len(rep["zone_violations"]) == 0,
        "; ".join(sorted(set(v["layer"] + "@" + v["zone"] for v in rep["zone_violations"])))[:300])
    if picture:
        occ = occupancy(picture)
        runs = [x for x in low_runs(occ, r["min_occupancy"], r["max_low_frames"]) if x[0] > 0]
        add("near-empty stretches (frames under %d %% content, %d+ frames)" % (r["min_occupancy"] * 100, r["max_low_frames"]), runs, not runs)
        ef = rep.get("frames", len(occ)) - rep.get("endcard_frames", 0)
        hold = sorted(occ[ef + 6:]) if rep.get("endcard_frames") else []
        if hold:
            med = hold[len(hold) // 2]
            add("end-card content (median share of the frame)", med, med >= r["endcard_min_occupancy"], "a lone small wordmark on a flat ground reads as an empty frame")
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
    d.add_argument("--method", choices=["onset", "silence"], default="onset", help="onset: full mix (default); silence: a percussive stem with silence between hits")
    d.add_argument("--seconds", type=float, default=60, help="analysed span for --method onset (default 60 s)")
    d.add_argument("--start", type=float, default=0, help="start of the analysed span, past an intro (s)")
    d.add_argument("--bpm-range", default="70,180", help="lowest,highest tempo considered (default 70,180)")
    g = sub.add_parser("grid"); g.add_argument("--bpm", type=float, required=True); g.add_argument("--offset", type=float, default=0); g.add_argument("--seconds", type=float, required=True); g.add_argument("--fps", type=float, default=30)
    s = sub.add_parser("snap"); s.add_argument("sheet"); s.add_argument("beats"); s.add_argument("--max", type=int, default=8); s.add_argument("--min-shot", type=int, default=18); s.add_argument("--out")
    l = sub.add_parser("loud"); l.add_argument("file")
    z = sub.add_parser("zone"); z.add_argument("png"); z.add_argument("--name", required=True); z.add_argument("--source", default="")
    v = sub.add_parser("review"); v.add_argument("report"); v.add_argument("--render", help="mix (AIFF or the movie) for loudness"); v.add_argument("--rules")
    v.add_argument("--picture", help="the rendered movie: near-empty stretches and end-card content")
    o = sub.add_parser("occupancy"); o.add_argument("file")
    ct = sub.add_parser("contrast"); ct.add_argument("png"); ct.add_argument("--box", required=True); ct.add_argument("--fill", required=True)
    a = ap.parse_args()
    if a.cmd == "detect" and a.method == "onset":
        lo, hi = [float(v) for v in a.bpm_range.split(",")]
        res = detect_onsets(a.file, a.fps, a.seconds, a.start, lo, hi)
    elif a.cmd == "detect":
        res = detect(a.file, a.fps, a.noise, a.min)
        if len(res["beats_s"]) < 4:
            res["warning"] = "silencedetect found %d onsets: the track never falls below %s dB between hits. Use --method onset on a full mix." % (len(res["beats_s"]), a.noise)
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
    elif a.cmd == "occupancy":
        occ = occupancy(a.file)
        res = {"file": a.file, "frames": len(occ), "occupancy": occ, "low_runs_3pct_9f": low_runs(occ, 0.03, 9)}
    elif a.cmd == "contrast":
        res = contrast(a.png, a.box, a.fill.lstrip("#"))
    else:
        rep = _read_json(a.report)
        rep = rep.get("result", rep)
        rep = rep.get("report", rep)
        res = review(rep, a.render, _read_json(a.rules) if a.rules else None, a.picture)
    json.dump(res, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
