#!/usr/bin/env python3
"""Measure banding on one row of a rendered frame: distinct 8-bit levels and flat-run widths.

Usage: python3 band_check.py FRAME.(png|tif) [row]
Hard banding shows as few levels and long, equal runs (every run the same width). Dithered or grained output shows
a median run of 1 or 2 px. Needs ImageMagick (`magick`) on PATH. Standard library only.
"""
import subprocess
import sys


def main():
    f = sys.argv[1]
    y = int(sys.argv[2]) if len(sys.argv) > 2 else None
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


if __name__ == "__main__":
    main()
