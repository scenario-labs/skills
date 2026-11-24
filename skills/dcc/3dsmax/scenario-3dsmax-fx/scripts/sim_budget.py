"""sim_budget: runner-side simulation time and cache checks (plain Python 3.10+, no pymxs).

status: not yet run against a real 3ds Max cache; estimates are linear extrapolations [added].

Usage
  python sim_budget.py estimate --sec-per-frame 0.8 --frames 150 --load-ratio 4
  python sim_budget.py cache DIR --pattern "*.tyc" --first 0 --last 150

estimate: scales a measured preview cost to the final run. load_ratio is final load over
preview load (particles, voxels or cloth vertices). Linear scaling is an assumption: re-measure
after each doubling instead of trusting a long extrapolation.

cache: counts files, total size, and missing frame numbers parsed from the trailing digits of
each file name. The Particle Export file naming is not in the saved docs, so pass the pattern
you see on disk.
"""
import argparse
import json
import re
import statistics
from pathlib import Path


def estimate(sec_per_frame, frames, load_ratio=1.0, safety=1.5):
    base = sec_per_frame * frames * load_ratio
    return {
        "estimate_s": round(base, 1),
        "with_safety_s": round(base * safety, 1),
        "with_safety_h": round(base * safety / 3600.0, 2),
        "assumption": "linear in frames and load; re-measure after each 2x increase",
    }


def cache_report(folder, pattern="*", first=None, last=None):
    root = Path(folder)
    files = sorted(p for p in root.glob(pattern) if p.is_file())
    sizes = [p.stat().st_size for p in files]
    frames = set()
    for p in files:
        m = re.search(r"(\d+)(?!.*\d)", p.stem)
        if m:
            frames.add(int(m.group(1)))
    missing = []
    if first is not None and last is not None and frames:
        missing = [f for f in range(first, last + 1) if f not in frames]
    zero = [p.name for p, s in zip(files, sizes) if s == 0]
    return {
        "folder": str(root),
        "files": len(files),
        "total_gb": round(sum(sizes) / 1e9, 3),
        "median_mb": round(statistics.median(sizes) / 1e6, 3) if sizes else 0,
        "zero_byte_files": zero[:50],
        "missing_frames": missing[:200],
        "ok": bool(files) and not zero and not missing,
    }


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate")
    e.add_argument("--sec-per-frame", type=float, required=True)
    e.add_argument("--frames", type=int, required=True)
    e.add_argument("--load-ratio", type=float, default=1.0)
    e.add_argument("--safety", type=float, default=1.5)
    c = sub.add_parser("cache")
    c.add_argument("folder")
    c.add_argument("--pattern", default="*")
    c.add_argument("--first", type=int)
    c.add_argument("--last", type=int)
    a = ap.parse_args()
    if a.cmd == "estimate":
        out = estimate(a.sec_per_frame, a.frames, a.load_ratio, a.safety)
    else:
        out = cache_report(a.folder, a.pattern, a.first, a.last)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
