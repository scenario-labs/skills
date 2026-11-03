#!/usr/bin/env python3
"""Check a composed master against the cue sheet of its sound pass.

Usage: python3 check_master.py master.mp4 cues.json [-o OUTDIR] [--sections 0 5 11]

cues.json is the file `build_passes.py sound` writes. Prints:
- the ffprobe summary, against the planned length and canvas;
- integrated loudness and true peak (ffmpeg ebur128=peak=true);
- the mean (RMS) and max level of each section (cues.json "sections", or --sections);
- an onset table: where each hit landed in the master against its planned time.
Writes OUTDIR/sheet_2fps.jpg (a 2 fps contact sheet, for timing only: judge game logic on
full-resolution frames) and OUTDIR/onsets.json. OUTDIR defaults to <master>_check beside it.

Each hit is found by cross-correlating the master with the hit's own sound, read from its
trimStart. The search runs from 0.15 s before to 0.35 s after the planned time, but never past
halfway to a repeat of the same sound, so a hit repeated within 0.35 s is not matched to its
neighbor. A hit more than 0.1 s off, or matching under 0.3, reads CHECK.

Exit status 1 when a hit reads CHECK, the true peak is over -1 dBTP, the loudness is outside
-16 to -14 LUFS, or the file's length or canvas differs from the plan.
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

import build_passes as bp

SR = bp.SR
PRE, POST, REF = 0.15, 0.35, 0.25


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels"
                          ":format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    return info.get("streams", []), float(info["format"]["duration"])


def mono(path):
    return bp.load_audio(path).mean(axis=1)


def levels(x, start, end):
    seg = x[round(start * SR):round(end * SR)]
    if not seg.size:
        return float("-inf"), float("-inf")
    return bp.db(float(np.sqrt(np.mean(seg.astype(np.float64) ** 2)))), bp.db(float(np.abs(seg).max()))


def search_windows(hits):
    """Lag range per hit, cut halfway to the nearest repeat of the same sound on either side."""
    windows = []
    for h in hits:
        same = [o["t"] for o in hits if o is not h and (o["file"], o.get("trimStart", 0)) == (h["file"], h.get("trimStart", 0))]
        before = [h["t"] - t for t in same if t < h["t"]]
        after = [t - h["t"] for t in same if t > h["t"]]
        windows.append((-min([PRE] + [d / 2 for d in before]), min([POST] + [d / 2 for d in after])))
    return windows


def onset(render, ref, t, lo, hi):
    """Offset (s) of the best match of ref in render for lags lo..hi around t, and its score."""
    a = max(0, round((t + lo) * SR))
    seg = render[a:round((t + hi) * SR) + len(ref)].astype(np.float64)
    ref = ref.astype(np.float64)
    if len(seg) < len(ref) or not ref.any():
        return None, 0.0
    nf = 1 << (len(seg) + len(ref) - 1).bit_length()
    xc = np.fft.irfft(np.fft.rfft(seg, nf) * np.conj(np.fft.rfft(ref, nf)), nf)[:len(seg) - len(ref) + 1]
    energy = np.concatenate([[0.0], np.cumsum(seg ** 2)])
    energy = np.sqrt(np.maximum(energy[len(ref):] - energy[:-len(ref)], 0))
    score = xc / (energy * np.linalg.norm(ref) + 1e-12)
    k = int(score.argmax())
    return (a + k) / SR - t, float(score[k])


def onset_table(render, hits):
    rows = []
    for h, (lo, hi) in zip(hits, search_windows(hits)):
        trim = h.get("trimStart", 0)
        ref = mono(h["file"])[round(trim * SR):round((trim + min(REF, h.get("end", h["t"] + REF) - h["t"])) * SR)]
        off, score = onset(render, ref, h["t"], lo, hi)
        rows.append({"label": h["label"], "t": h["t"], "offset": off, "score": score,
                     "check": off is None or abs(off) > 0.1 or score < 0.3})
    return rows


def contact_sheet(master, out, duration):
    rows = math.ceil((int(duration * 2) + 1) / 10)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-vf", f"fps=2,scale=216:-2,tile=10x{rows}",
                    "-frames:v", "1", str(out)], check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("master", type=Path)
    ap.add_argument("cues", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--sections", type=float, nargs="+", help="section start times in seconds")
    args = ap.parse_args(argv)
    plan = json.loads(args.cues.read_text())
    out = args.out or args.master.with_name(f"{args.master.stem}_check")
    out.mkdir(parents=True, exist_ok=True)
    failed = []

    streams, duration = probe(args.master)
    for s in streams:
        if s["codec_type"] == "video":
            print(f"video: {s['codec_name']} {s['width']}x{s['height']} {s.get('pix_fmt', '')} {s['r_frame_rate']} fps")
            if plan.get("canvas") and [s["width"], s["height"]] != plan["canvas"]:
                failed.append(f"canvas {s['width']}x{s['height']}, planned {plan['canvas'][0]}x{plan['canvas'][1]}")
        elif s["codec_type"] == "audio":
            print(f"audio: {s['codec_name']} {s.get('sample_rate')} Hz, {s.get('channels')} channels")
    print(f"duration: {duration:.3f} s")
    if "duration" in plan and abs(duration - plan["duration"]) > 1 / plan.get("fps", 30):
        failed.append(f"length {duration:.3f} s, planned {plan['duration']} s")
    if not any(s["codec_type"] == "audio" for s in streams):
        failed.append("no audio stream")
        lufs = tp = None
    else:
        lufs, tp = bp.loudness(args.master)
        print(f"loudness: {lufs:.1f} LUFS integrated, true peak {tp:+.1f} dBTP")
        if tp > -1:
            failed.append(f"true peak {tp:+.1f} dBTP, over -1")
        if not -16 <= lufs <= -14:
            failed.append(f"{lufs:.1f} LUFS, outside -16 to -14: run the loudness pass")

    rows = []
    if lufs is not None:
        render = mono(args.master)
        starts = args.sections or plan.get("sections") or [0]
        for a, b in zip(starts, list(starts[1:]) + [duration]):
            mean, peak = levels(render, a, b)
            print(f"section {a:g}-{b:g} s: mean {mean:.1f} dB, max {peak:.1f} dB")
        rows = onset_table(render, [c for c in plan["cues"] if c.get("role", "hit") == "hit"])
        for r in rows:
            landed = "no match" if r["offset"] is None else f"{r['offset'] * 1000:+6.1f} ms"
            print(f"  {r['t']:7.3f} s  {r['label']:24s} lands {landed}  match {r['score']:.2f}  {'CHECK' if r['check'] else ''}")
        failed += [f"hit {r['label']} at {r['t']} s" for r in rows if r["check"]]

    contact_sheet(args.master, out / "sheet_2fps.jpg", duration)
    (out / "onsets.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(f"wrote {out / 'sheet_2fps.jpg'} and {out / 'onsets.json'}")
    for f in failed:
        print(f"FAIL {f}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
