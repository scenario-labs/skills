#!/usr/bin/env python3
"""Check rendered deliverables against a spec: expected versus measured, PASS or FAIL per row.

Usage:
  python3 delivery_check.py spec.json [--json report.json]

spec.json is a list of deliverables. Every key except "file" is optional; only the keys given are checked.
  {"file": "<path>.mp4" | "<folder>/name_%05d.png",
   "codec": "h264", "profile": "High", "width": 1920, "height": 1080, "fps": 30, "frames": 60,
   "duration": 2.0, "pix_fmt": "yuv420p", "alpha": false,
   "color": {"primaries": "bt709", "trc": "bt709", "space": "bt709", "range": "tv"},
   "faststart": true, "max_mb": 20,
   "audio": {"codec": "aac", "rate": 48000, "channels": 2, "lufs": -14, "lufs_tol": 1.0, "true_peak_max": -1.0},
   "no_audio": true,
   "sequence_start": 0,
   "levels": {"every": 1, "min8": 16, "max8": 235}}
"levels" checks the Y (luminance) floor and ceiling with ffmpeg signalstats. Limits are given in 8-bit units and scaled to the
file's bit depth read by ffprobe (16 to 235 becomes 64 to 940 at 10 bits, 256 to 3760 at 12 bits). YUV files only.
Needs ffprobe and ffmpeg on PATH. Standard library only. Exit code 1 when any row fails.
"""
import glob
import json
import os
import re
import struct
import subprocess
import sys


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, data, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, **kw)


ALPHA_PREFIXES = ("yuva", "gbrap", "rgba", "bgra", "argb", "abgr", "ayuv", "ya", "pal8")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe(path):
    p = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "ffprobe failed on " + path)
    return json.loads(p.stdout)


def rate(s):
    try:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else 0.0
    except Exception:
        return 0.0


def moov_first(path):
    """True when the moov atom comes before mdat (MP4 or MOV 'fast start')."""
    order = []
    with open(path, "rb") as f:
        size_total = os.path.getsize(path)
        pos = 0
        while pos < size_total and len(order) < 50:
            f.seek(pos)
            head = f.read(16)
            if len(head) < 8:
                break
            size, kind = struct.unpack(">I4s", head[:8])
            if size == 1:
                size = struct.unpack(">Q", head[8:16])[0]
            elif size == 0:
                size = size_total - pos
            order.append(kind.decode("latin-1"))
            if size < 8:
                break
            pos += size
    if "moov" not in order or "mdat" not in order:
        return None
    return order.index("moov") < order.index("mdat")


def loudness(path):
    """Integrated loudness (LUFS) and true peak (dBTP) from ffmpeg's ebur128 filter."""
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"])
    text = p.stderr
    summary = text[text.rfind("Summary:"):] if "Summary:" in text else text
    i = re.search(r"I:\s+(-?[\d.]+|-inf)\s+LUFS", summary)
    tp = re.search(r"True peak:\s*\n\s*Peak:\s+(-?[\d.]+|-inf)\s+dBFS", summary)
    val = lambda m: (float("-inf") if m.group(1) == "-inf" else float(m.group(1))) if m else None
    return val(i), val(tp)


def bit_depth(stream):
    """Bits per component of a video stream: bits_per_raw_sample, else the pix_fmt suffix (yuv422p10le -> 10), else 8."""
    raw = stream.get("bits_per_raw_sample")
    if raw and str(raw).isdigit():
        return int(raw)
    m = re.search(r"p(\d{2})(le|be)$", stream.get("pix_fmt", ""))
    return int(m.group(1)) if m else 8


def luma_range(path, every):
    """Lowest YMIN and highest YMAX from ffmpeg signalstats, sampling one frame in `every`. Values are in the file's own bit depth."""
    vf = "select=not(mod(n\\,%d)),signalstats,metadata=print" % max(1, int(every))
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:v:0", "-vf", vf, "-f", "null", "-"])
    lo = [int(float(x)) for x in re.findall(r"signalstats\.YMIN=([\d.]+)", p.stderr)]
    hi = [int(float(x)) for x in re.findall(r"signalstats\.YMAX=([\d.]+)", p.stderr)]
    return (min(lo), max(hi), len(lo)) if lo and hi else (None, None, 0)


def row(rows, name, expected, measured, ok):

    rows.append({"check": name, "expected": expected, "measured": measured, "pass": bool(ok)})


def check(spec):
    rows = []
    path = spec["file"]
    is_seq = "%" in path
    files = []
    if is_seq:
        pattern = re.sub(r"%0?(\d*)d", lambda m: "[0-9]" * int(m.group(1) or 1), path)
        files = sorted(glob.glob(pattern))
        if not files:
            row(rows, "exists", "sequence", "no files", False)
            return rows
        nums = [int(re.findall(r"(\d+)\D*$", os.path.basename(f))[0]) for f in files]
        gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)]
        row(rows, "gaps", 0, len(gaps), not gaps)
        if "sequence_start" in spec:
            row(rows, "first number", spec["sequence_start"], nums[0], nums[0] == spec["sequence_start"])
        probe_path = files[0]
        frames = len(files)
        size_mb = sum(os.path.getsize(f) for f in files) / 1048576.0
    else:
        if not os.path.exists(path):
            row(rows, "exists", True, False, False)
            return rows
        probe_path = path
        size_mb = os.path.getsize(path) / 1048576.0
        frames = None
    info = ffprobe(probe_path)
    v = next((s for s in info["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    if v is None:
        row(rows, "video stream", True, False, False)
        return rows
    if frames is None:
        frames = int(v.get("nb_frames") or 0)
        if not frames:
            c = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path])
            frames = int((c.stdout.strip() or "0").split(",")[0])
    fps = rate(v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1")
    duration = float(info.get("format", {}).get("duration") or 0) if not is_seq else None
    pix = v.get("pix_fmt", "")
    simple = [("codec", v.get("codec_name")), ("profile", v.get("profile")), ("width", v.get("width")),
              ("height", v.get("height")), ("pix_fmt", pix)]
    for key, meas in simple:
        if key in spec:
            row(rows, key, spec[key], meas, str(meas).lower() == str(spec[key]).lower())
    if "fps" in spec and not is_seq:
        row(rows, "fps", spec["fps"], round(fps, 3), abs(fps - spec["fps"]) < 0.01)
    if "frames" in spec:
        row(rows, "frames", spec["frames"], frames, frames == spec["frames"])
    if "duration" in spec and duration is not None:
        tol = 1.0 / fps if fps else 0.05
        row(rows, "duration", spec["duration"], round(duration, 3), abs(duration - spec["duration"]) <= tol + 1e-6)
    if "alpha" in spec:
        has = pix.startswith(ALPHA_PREFIXES)
        row(rows, "alpha", spec["alpha"], has, has == spec["alpha"])
    if "color" in spec:
        tags = {"primaries": v.get("color_primaries"), "trc": v.get("color_transfer"), "space": v.get("color_space"), "range": v.get("color_range")}
        for k, exp in spec["color"].items():
            row(rows, "color " + k, exp, tags.get(k), tags.get(k) == exp)
    if "levels" in spec and not is_seq:
        # Legal (video) range is 16 to 235 at 8 bits, scaled by 2^(bits - 8): 64 to 940 at 10 bits, 256 to 3760 at 12 bits.
        lv = spec["levels"] if isinstance(spec["levels"], dict) else {}
        bits = bit_depth(v)
        scale = 2 ** (bits - 8)
        lo_lim, hi_lim = lv.get("min8", 16) * scale, lv.get("max8", 235) * scale
        if not pix.startswith("yuv"):
            row(rows, "Y levels", "YUV file", pix, False)
        else:
            lo, hi, n = luma_range(path, lv.get("every", 1))
            row(rows, "Y min (%d-bit)" % bits, ">= %d" % lo_lim, lo, lo is not None and lo >= lo_lim)
            row(rows, "Y max (%d-bit)" % bits, "<= %d" % hi_lim, hi, hi is not None and hi <= hi_lim)
    if "faststart" in spec and not is_seq:
        fs = moov_first(path)
        row(rows, "faststart (moov before mdat)", spec["faststart"], fs, fs == spec["faststart"])
    if "max_mb" in spec:
        row(rows, "size MB", "<= %s" % spec["max_mb"], round(size_mb, 2), size_mb <= spec["max_mb"])
    if spec.get("no_audio"):
        row(rows, "audio stream", "none", a.get("codec_name") if a else "none", a is None)
    if "audio" in spec:
        exp = spec["audio"]
        if a is None:
            row(rows, "audio stream", "present", "none", False)
        else:
            if "codec" in exp:
                row(rows, "audio codec", exp["codec"], a.get("codec_name"), a.get("codec_name") == exp["codec"])
            if "rate" in exp:
                row(rows, "audio rate", exp["rate"], int(a.get("sample_rate", 0)), int(a.get("sample_rate", 0)) == exp["rate"])
            if "channels" in exp:
                row(rows, "audio channels", exp["channels"], a.get("channels"), a.get("channels") == exp["channels"])
            if "lufs" in exp or "true_peak_max" in exp:
                i_lufs, tp = loudness(path)
                if "lufs" in exp:
                    tol = exp.get("lufs_tol", 1.0)
                    row(rows, "integrated LUFS", "%s +/- %s" % (exp["lufs"], tol), i_lufs, i_lufs is not None and abs(i_lufs - exp["lufs"]) <= tol)
                if "true_peak_max" in exp:
                    row(rows, "true peak dBTP", "<= %s" % exp["true_peak_max"], tp, tp is not None and tp <= exp["true_peak_max"])
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    specs = _read_json(sys.argv[1])
    report, failed = [], 0
    for spec in specs:
        try:
            rows = check(spec)
        except Exception as e:
            rows = [{"check": "probe", "expected": "readable", "measured": str(e), "pass": False}]
        ok = all(r["pass"] for r in rows)
        failed += 0 if ok else 1
        report.append({"file": spec["file"], "pass": ok, "rows": rows})
        print("%s  %s" % ("PASS" if ok else "FAIL", spec["file"]))
        for r in rows:
            print("    %-4s %-28s expected %-18s measured %s" % ("ok" if r["pass"] else "FAIL", r["check"], r["expected"], r["measured"]))
    if "--json" in sys.argv:
        _write_json(sys.argv[sys.argv.index("--json") + 1], report, indent=1)
    print("%d of %d deliverables pass" % (len(specs) - failed, len(specs)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
