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
   "no_audio": true, "no_data": true,
   "sequence_start": 0,
   "levels": {"every": 1, "min8": 16, "max8": 235}}
"levels" checks the Y (luminance) floor and ceiling with ffmpeg signalstats. With "max_out_pct" (example 0.01) it passes on area
instead: the worst frame's share of pixels outside the broadcast range (signalstats BRNG, Y, U or V) must stay under it, and
Y min and max are printed for information. Grain encoded by x264 leaves a few isolated overshoot pixels that a per-pixel limit fails. Limits are given in 8-bit units and scaled to the
file's bit depth read by ffprobe (16 to 235 becomes 64 to 940 at 10 bits, 256 to 3760 at 12 bits). YUV files only.
"no_data" fails on any data stream, such as the timecode (tmcd) track ffmpeg writes from an After Effects QuickTime.
An image sequence is probed frame by frame: one frame off the spec fails its row. A sequence has no frame rate, duration or
moov atom, so "fps", "duration" and "faststart" fail on it; check them on the encoded movie.
An empty spec list, or a deliverable with no key besides "file", fails.
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
    if p.returncode != 0:
        raise RuntimeError("ffmpeg loudness analysis failed on %s: %s" % (path, p.stderr.strip()[-300:]))
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


def luma_range(path, every, input_args=()):
    """Lowest YMIN and highest YMAX from ffmpeg signalstats, sampling one frame in `every`. Values are in the file's own bit depth."""
    vf = "select=not(mod(n\\,%d)),signalstats=stat=brng,metadata=print" % max(1, int(every))
    p = run(["ffmpeg", "-hide_banner", "-nostats"] + list(input_args) + ["-i", path, "-map", "0:v:0", "-vf", vf, "-f", "null", "-"])
    if p.returncode != 0:
        raise RuntimeError("ffmpeg levels analysis failed on %s: %s" % (path, p.stderr.strip()[-300:]))
    lo = [int(float(x)) for x in re.findall(r"signalstats\.YMIN=([\d.]+)", p.stderr)]
    hi = [int(float(x)) for x in re.findall(r"signalstats\.YMAX=([\d.]+)", p.stderr)]
    # BRNG: share of the frame's pixels outside the broadcast range (Y, U or V), worst frame
    br = [float(x) for x in re.findall(r"signalstats\.BRNG=([\d.e+-]+)", p.stderr)]
    return (min(lo), max(hi), len(lo), max(br) if br else None) if lo and hi else (None, None, 0, None)


def row(rows, name, expected, measured, ok):

    rows.append({"check": name, "expected": expected, "measured": measured, "pass": bool(ok)})


SEQ_NA = "not measurable on an image sequence"


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
        present = set(nums)
        gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in present]
        row(rows, "gaps", 0, len(gaps), not gaps)
        if "sequence_start" in spec:
            row(rows, "first number", spec["sequence_start"], nums[0], nums[0] == spec["sequence_start"])
        frames = len(files)
        size_mb = sum(os.path.getsize(f) for f in files) / 1048576.0
    else:
        if not os.path.exists(path):
            row(rows, "exists", True, False, False)
            return rows
        files = [path]
        size_mb = os.path.getsize(path) / 1048576.0
        frames = None
    # every member of a sequence is probed: one odd frame fails the row
    members = []
    for f in files:
        info = ffprobe(f)
        streams = info.get("streams", [])
        v = next((s for s in streams if s.get("codec_type") == "video"), None)
        if v is None:
            row(rows, "video stream", True, "none in " + os.path.basename(f), False)
            return rows
        members.append((f, info, v))
    info, v = members[0][1], members[0][2]
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)

    def per_member(name, expected, measure, ok):
        bad = [(f, measure(f_info, f_v)) for f, f_info, f_v in members if not ok(measure(f_info, f_v))]
        if not bad:
            row(rows, name, expected, measure(info, v), True)
        elif not is_seq:
            row(rows, name, expected, bad[0][1], False)
        else:
            row(rows, name, expected, "%s in %d of %d frames, first %s" % (bad[0][1], len(bad), len(members), os.path.basename(bad[0][0])), False)

    if frames is None:
        frames = int(v.get("nb_frames") or 0)
        if not frames:
            c = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path])
            if c.returncode != 0:
                raise RuntimeError(c.stderr.strip() or "ffprobe could not count the frames of " + path)
            frames = int((c.stdout.strip() or "0").split(",")[0])
    fps = rate(v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1")
    duration = float(info.get("format", {}).get("duration") or 0) if not is_seq else None
    for key, field in (("codec", "codec_name"), ("profile", "profile"), ("width", "width"), ("height", "height"), ("pix_fmt", "pix_fmt")):
        if key in spec:
            per_member(key, spec[key], lambda i, s, field=field: s.get(field),
                       lambda m, key=key: str(m).lower() == str(spec[key]).lower())
    if "fps" in spec:
        if is_seq:
            row(rows, "fps", spec["fps"], SEQ_NA, False)
        else:
            row(rows, "fps", spec["fps"], round(fps, 3), abs(fps - spec["fps"]) < 0.01)
    if "frames" in spec:
        row(rows, "frames", spec["frames"], frames, frames == spec["frames"])
    if "duration" in spec:
        if is_seq:
            row(rows, "duration", spec["duration"], SEQ_NA, False)
        else:
            tol = 1.0 / fps if fps else 0.05
            row(rows, "duration", spec["duration"], round(duration, 3), abs(duration - spec["duration"]) <= tol + 1e-6)
    if "alpha" in spec:
        per_member("alpha", spec["alpha"], lambda i, s: s.get("pix_fmt", "").startswith(ALPHA_PREFIXES),
                   lambda m: m == spec["alpha"])
    if "color" in spec:
        names = {"primaries": "color_primaries", "trc": "color_transfer", "space": "color_space", "range": "color_range"}
        for k, exp in spec["color"].items():
            per_member("color " + k, exp, lambda i, s, k=k: s.get(names.get(k, "")), lambda m, exp=exp: m == exp)
    if "levels" in spec:
        # Legal (video) range is 16 to 235 at 8 bits, scaled by 2^(bits - 8): 64 to 940 at 10 bits, 256 to 3760 at 12 bits.
        lv = spec["levels"] if isinstance(spec["levels"], dict) else {}
        bits = bit_depth(v)
        scale = 2 ** (bits - 8)
        lo_lim, hi_lim = lv.get("min8", 16) * scale, lv.get("max8", 235) * scale
        not_yuv = [m[2].get("pix_fmt", "") for m in members if not m[2].get("pix_fmt", "").startswith("yuv")]
        if not_yuv:
            row(rows, "Y levels", "YUV file", not_yuv[0], False)
        else:
            # ffmpeg reads the printf pattern itself; its image2 demuxer needs the first number
            lo, hi, n, brng = luma_range(path, lv.get("every", 1), ["-start_number", str(nums[0])] if is_seq else [])
            if "max_out_pct" in lv:
                # area tolerance: a few encoder overshoot pixels on grain pass, a clipped or lifted picture does not
                pct = None if brng is None else brng * 100
                row(rows, "Y min / max (%d-bit), information" % bits, "%d to %d" % (lo_lim, hi_lim), "%s to %s" % (lo, hi), True)
                row(rows, "pixels outside legal range, worst frame %", "<= %s" % lv["max_out_pct"],
                    None if pct is None else round(pct, 5), pct is not None and pct <= lv["max_out_pct"])
            else:
                row(rows, "Y min (%d-bit)" % bits, ">= %d" % lo_lim, lo, lo is not None and lo >= lo_lim)
                row(rows, "Y max (%d-bit)" % bits, "<= %d" % hi_lim, hi, hi is not None and hi <= hi_lim)
    if "faststart" in spec:
        if is_seq:
            row(rows, "faststart (moov before mdat)", spec["faststart"], SEQ_NA, False)
        else:
            fs = moov_first(path)
            row(rows, "faststart (moov before mdat)", spec["faststart"], fs, fs == spec["faststart"])
    if "max_mb" in spec:
        row(rows, "size MB", "<= %s" % spec["max_mb"], round(size_mb, 2), size_mb <= spec["max_mb"])
    if spec.get("no_audio"):
        per_member("audio stream", "none",
                   lambda i, s: next((x.get("codec_name") for x in i["streams"] if x.get("codec_type") == "audio"), "none"),
                   lambda m: m == "none")
    if spec.get("no_data"):
        per_member("data streams", "none",
                   lambda i, s: ", ".join(x.get("codec_tag_string") or x.get("codec_name") or "data" for x in i["streams"] if x.get("codec_type") == "data") or "none",
                   lambda m: m == "none")
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
    if not rows:
        row(rows, "requirements", "at least one key besides file", "none", False)
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    specs = _read_json(sys.argv[1])
    if not isinstance(specs, list) or not specs or not all(isinstance(s, dict) and "file" in s for s in specs):
        print("FAIL  %s: expected a non-empty list of deliverables, each with a \"file\" key" % sys.argv[1])
        sys.exit(1)
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
