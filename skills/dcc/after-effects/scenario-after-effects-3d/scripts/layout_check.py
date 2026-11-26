#!/usr/bin/env python3
"""layout_check.py: read two matte PNGs written by AEX.threeD.mattes and report what the front layer hides.

Usage:
  python3 layout_check.py READ.png FRONT.png [--min 0.9] [--width W]

READ.png   the layer that must read (a title, a logo)
FRONT.png  the layer in front of it (the product)
Prints one JSON line: visible fraction of READ, whether READ sits inside the frame with a 2 % margin (a camera move can
carry a title off the edge without anything covering it), the bounding box and center of both mattes, and the front
matte's center offset from the frame center in px. Exit code 1 when the visible fraction is under --min or READ leaves the frame,
2 when either matte is empty (nothing to measure).
Needs ImageMagick 7 (`magick`) on the PATH. Alpha above 50 % counts as covered.
"""
import json
import subprocess
import sys


def magick(*args):
    return subprocess.run(["magick", *args], check=True, capture_output=True, text=True).stdout.strip()


def bbox(path):
    # %@ is the trim box of the thresholded alpha: WxH+X+Y
    geo = magick(path, "-alpha", "extract", "-threshold", "50%", "-format", "%@", "info:")
    wh, x, y = geo.split("+")[0], int(geo.split("+")[1]), int(geo.split("+")[2])
    w, h = (int(v) for v in wh.split("x"))
    return {"x": x, "y": y, "w": w, "h": h, "cx": x + w / 2.0, "cy": y + h / 2.0}


def area(path):
    return float(magick(path, "-alpha", "extract", "-threshold", "50%", "-format", "%[fx:mean]", "info:"))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    read, front = argv[1], argv[2]
    minimum = float(argv[argv.index("--min") + 1]) if "--min" in argv else 0.9
    size = magick(read, "-format", "%w %h", "info:").split()
    w, h = int(size[0]), int(size[1])
    a_read = area(read)
    if a_read == 0 or area(front) == 0:
        # an empty matte gives a fallback box and a visible fraction of 1: no measurement, no pass
        print(json.dumps({"read": read, "front": front, "pass": False,
                          "error": "a matte holds no layer pixels: %s cannot be measured" % (read if a_read == 0 else front)}))
        return 2
    both = float(magick(
        "(", read, "-alpha", "extract", "-threshold", "50%", ")",
        "(", front, "-alpha", "extract", "-threshold", "50%", ")",
        "-compose", "multiply", "-composite", "-format", "%[fx:mean]", "info:"))
    visible = 1.0 - both / a_read
    fb, rb = bbox(front), bbox(read)
    mx, my = 0.02 * w, 0.02 * h
    in_frame = rb["x"] >= mx and rb["y"] >= my and rb["x"] + rb["w"] <= w - mx and rb["y"] + rb["h"] <= h - my
    out = {"read": read, "front": front, "visible": round(visible, 4), "inFrame": in_frame, "readBox": rb, "frontBox": fb,
           "frontOffset": [round(fb["cx"] - w / 2.0, 1), round(fb["cy"] - h / 2.0, 1)], "pass": visible >= minimum and in_frame}
    print(json.dumps(out))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
