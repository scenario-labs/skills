#!/usr/bin/env python3
"""Measure banding on one row of a rendered frame: distinct 8-bit levels and flat-run widths.

Usage: python3 band_check.py FRAME.(png|tif) [row] [--max-run N]
Hard banding shows as few levels and long, equal runs (every run the same width). Dithered or grained output shows
a median run of 1 or 2 px. With --max-run N, exit 1 when the median run is over 2 px or the widest run over N px
(16 = one x264 macroblock: an encoder that flattened grain over two blocks shows 32). Needs ImageMagick (`magick`) on PATH. Standard library only.
"""
import subprocess
import sys


def main():
    args = sys.argv[1:]
    max_run = None
    if "--max-run" in args:
        i = args.index("--max-run"); max_run = int(args[i + 1]); del args[i:i + 2]
    f = args[0]
    y = int(args[1]) if len(args) > 1 else None
    if y is None:
        h = int(subprocess.run(["magick", "identify", "-format", "%h", f], capture_output=True, text=True).stdout.split()[0])
        y = h // 2
    raw = subprocess.run(["magick", f, "-alpha", "off", "-colorspace", "gray", "-depth", "8", "-crop", "x1+0+%d" % y, "+repage", "gray:-"],
                         capture_output=True).stdout
    row = list(raw)
    runs, cur = [], 1
    for a, b in zip(row, row[1:]):
        if a == b:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    print("%s row %d: %d levels (min %d, max %d), widest flat run %d px, median run %d px"
          % (f, y, len(set(row)), min(row), max(row), max(runs), sorted(runs)[len(runs) // 2]))
    med = sorted(runs)[len(runs) // 2]
    if max_run is not None and (med > 2 or max(runs) > max_run):
        print("FAIL: median run %d px (limit 2), widest run %d px (limit %d)" % (med, max(runs), max_run))
        sys.exit(1)


if __name__ == "__main__":
    main()
