#!/usr/bin/env python3
"""finish_putback.py: the edit mask for a render-to-real finish, and the put-back of the finished region.

Usage:
  python3 finish_putback.py mask GUIDE.png ELEM.png OUT_DIR [--dilate 22] [--blur 3] [--threshold 0.5] [--step 16]
  python3 finish_putback.py putback COMP.png FINISHED.png REGION.png OUT.png [--feather 6] [--elem ELEM.png]
                            [--finish-matte MATTE.png]
  python3 finish_putback.py --selftest

mask     GUIDE.png is the composite frame that becomes the edit's layout guide. ELEM.png is the element alone
         over black with its alpha (the render's matte). Writes to OUT_DIR:
           region.png  the element matte (alpha over --threshold), dilated by --dilate px, blurred by --blur.
                       The edit fills the region it is given, and draws contact and bounce in the room
                       around the outline. The dilation is a per-model test: stay under a fifth of the
                       object's smaller dimension and read each take's outline against the matte.
           guide.png   the guide padded at the right and bottom to a multiple of --step (the size the edit model takes)
           mask.png    the padded guide with alpha 0 over the region (transparent = edited)
COMP.png  the composite the finish goes back into (the same frame as the guide, before padding)
FINISHED.png  the edit result: cropped to COMP's size from the top left, so a padded result fits
REGION.png    region.png from the mask step
putback  writes OUT.png = COMP outside the region, FINISHED inside it, the region's edge feathered by --feather px.
         Only the masked region comes back: an edit model redraws the whole frame a little.

Prints one JSON line:
  finishOutsideDiff   mean absolute difference (0-1, RGB) between FINISHED and COMP outside the dilated region:
                      how much the model redrew what it was told to keep (reading)
  outsideDiff         the same between OUT, read back from the written file, and COMP: 0 when the file kept the
                      plate (pass under 0.004)
  iou                 with --elem and --finish-matte: the finished silhouette (alpha or gray over half) against the
                      element matte (reading; the cast shadow still comes from the render's silhouette)
Exit code 1 when outsideDiff fails. numpy and Pillow only. Pillow reads a 16-bit RGBA PNG as 8-bit: pass 8-bit
display-referred frames (the frame as delivered), not linear 16-bit captures.
"""
import argparse
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFilter

LIMIT_OUTSIDE = 0.004


def rgb(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB")).astype(float) / 255.0


def alpha(path):
    """Alpha of an RGBA file, else its gray values, 0-1."""
    with Image.open(path) as im:
        if im.mode in ("RGBA", "LA"):
            return np.asarray(im.getchannel("A")).astype(float) / 255.0
        return np.asarray(im.convert("L")).astype(float) / 255.0


def dilate(mask, px):
    """Binary dilation by about a disk of radius px: one-pixel steps alternating the 4- and 8-neighborhoods
    (an octagon within 12 % of the disk)."""
    m = mask.copy()
    for i in range(int(px)):
        n = m.copy()
        n[1:, :] |= m[:-1, :]
        n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]
        n[:, :-1] |= m[:, 1:]
        if i % 2:
            n[1:, 1:] |= m[:-1, :-1]
            n[1:, :-1] |= m[:-1, 1:]
            n[:-1, 1:] |= m[1:, :-1]
            n[:-1, :-1] |= m[1:, 1:]
        m = n
    return m


def blur(a, radius):
    if radius <= 0:
        return a
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius))).astype(float) / 255.0


def save_gray(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def cmd_mask(guide, elem, out, dilate_px, blur_px, threshold, step):
    os.makedirs(out, exist_ok=True)
    g = rgb(guide)
    h, w = g.shape[:2]
    m = alpha(elem) > threshold
    if m.shape != (h, w):
        raise SystemExit("ELEM and GUIDE differ in size")
    region = blur(dilate(m, dilate_px).astype(float), blur_px)
    ph, pw = -(-h // step) * step, -(-w // step) * step
    pad = np.zeros((ph, pw, 3))
    pad[:h, :w] = g
    pad[h:, :w] = g[-1:, :, :]
    pad[:, w:] = pad[:, w - 1:w, :]
    reg = np.zeros((ph, pw))
    reg[:h, :w] = region
    save_gray(region, os.path.join(out, "region.png"))
    Image.fromarray((pad * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, "guide.png"))
    rgba = np.dstack([pad, 1 - (reg > 0.01)])
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(out, "mask.png"))
    res = {"size": [pw, ph], "regionPx": int((region > 0.5).sum()), "elementPx": int(m.sum()), "dilate": dilate_px}
    print(json.dumps(res))
    return 0


def cmd_putback(comp, finished, region, out, feather, elem=None, finish_matte=None):
    c = rgb(comp)
    h, w = c.shape[:2]
    f = rgb(finished)[:h, :w]
    r = alpha(region)[:h, :w]
    inside = r > 0.01
    outside = ~dilate(inside, 2)
    a = blur((r > 0.5).astype(float), feather) if feather > 0 else (r > 0.5).astype(float)
    a = np.where(inside, a, 0.0)
    o = c * (1 - a[..., None]) + f * a[..., None]
    Image.fromarray((o * 255 + 0.5).astype(np.uint8)).save(out)
    written = rgb(out)
    same_size = written.shape == c.shape
    res = {"finishOutsideDiff": round(float(np.abs(f - c)[outside].mean()), 5),
           "outsideDiff": round(float(np.abs(written - c)[outside].mean()), 5) if same_size else 1.0,
           "outsideLimit": LIMIT_OUTSIDE}
    if elem and finish_matte:
        e = alpha(elem)[:h, :w] > 0.5
        fm = alpha(finish_matte)[:h, :w] > 0.5
        res["iou"] = round(float((e & fm).sum() / max((e | fm).sum(), 1)), 4)
        res["finishOverElement"] = round(float(fm.sum() / max(e.sum(), 1)), 4)
    res["pass"] = bool(res["outsideDiff"] < LIMIT_OUTSIDE)
    print(json.dumps(res))
    return 0 if res["pass"] else 1


def selftest():
    """Planted frames: a gray plate with an ellipse element; the 'finish' redraws the element red and shifts the
    whole plate by 0.02. The put-back must keep the plate (outsideDiff 0), read the redraw (finishOutsideDiff 0.02),
    and an IoU of 1 for the same silhouette."""
    h, w = 120, 200
    yy, xx = np.mgrid[:h, :w]
    ell = ((xx - 100) / 40.0) ** 2 + ((yy - 60) / 20.0) ** 2 <= 1
    plate = np.full((h, w, 3), 0.5)
    comp = plate.copy()
    comp[ell] = [0.3, 0.3, 0.3]
    elem = np.zeros((h, w, 4))
    elem[ell] = [0.3, 0.3, 0.3, 1]
    fin = plate + 0.02
    fin[ell] = [0.8, 0.2, 0.1]
    ok = True
    with tempfile.TemporaryDirectory() as d:
        Image.fromarray((comp * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, "comp.png"))
        Image.fromarray((elem * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(d, "elem.png"))
        pad = np.zeros((128, 208, 3))
        pad[:h, :w] = fin
        Image.fromarray((pad * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, "fin.png"))
        save_gray(ell.astype(float), os.path.join(d, "fmatte.png"))
        cmd_mask(os.path.join(d, "comp.png"), os.path.join(d, "elem.png"), d, 6, 1, 0.04, 16)
        with Image.open(os.path.join(d, "mask.png")) as im:
            ok &= im.size == (208, 128) and im.mode == "RGBA"
            ma = np.asarray(im.getchannel("A"))
        ok &= ma[60, 100] == 0 and ma[5, 5] == 255 and ma[60, 100 + 40 + 4] == 0 and ma[60, 100 + 40 + 12] == 255
        rc = cmd_putback(os.path.join(d, "comp.png"), os.path.join(d, "fin.png"), os.path.join(d, "region.png"),
                         os.path.join(d, "out.png"), 2, os.path.join(d, "elem.png"), os.path.join(d, "fmatte.png"))
        o = rgb(os.path.join(d, "out.png"))
        ok &= rc == 0 and abs(o[60, 100, 0] - 0.8) < 0.01 and abs(o[5, 5, 0] - 0.5) < 0.01
    print("selftest", "pass" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None):
    if argv and argv[0] == "--selftest":
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mask")
    m.add_argument("guide")
    m.add_argument("elem")
    m.add_argument("out")
    m.add_argument("--dilate", type=int, default=22)
    m.add_argument("--blur", type=float, default=3.0)
    m.add_argument("--threshold", type=float, default=0.5)
    m.add_argument("--step", type=int, default=16)
    p = sub.add_parser("putback")
    p.add_argument("comp")
    p.add_argument("finished")
    p.add_argument("region")
    p.add_argument("out")
    p.add_argument("--feather", type=float, default=6)
    p.add_argument("--elem")
    p.add_argument("--finish-matte")
    a = ap.parse_args(argv)
    if a.cmd == "mask":
        return cmd_mask(a.guide, a.elem, a.out, a.dilate, a.blur, a.threshold, a.step)
    return cmd_putback(a.comp, a.finished, a.region, a.out, a.feather, a.elem, a.finish_matte)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
