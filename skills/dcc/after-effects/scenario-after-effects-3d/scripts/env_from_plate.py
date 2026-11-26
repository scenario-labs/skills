#!/usr/bin/env python3
"""env_from_plate.py: an equirect environment map for an Advanced 3D environment light, built from the plate itself.

The sky comes from the plate where the camera sees it, with the sun disc clamped (the parallel light carries the
sun). Outside the frame the sky follows the plate's own horizon profile by angle from the sun, mirrored about the
sun's azimuth, and blends up to a zenith color. The ground below is the plate's lit ground (toward the sun) and its
shadowed ground (near the nadir and away from the sun). The zenith color is solved so the map's light on an
up-facing floor has the hue of --sky-target. That target is the uniform sky solved on the plate's shadowed ground.

  python3 env_from_plate.py plate.png env.png --focal 50 --tilt 6.5 --sun=-17,4 \
      --lit 0.316,0.205,0.147 --shadow 0.147,0.134,0.133 --sky-target 0.234,0.214,0.212

Orientation, measured on After Effects 27.0 with a model under probe maps: the top of the map is up; u = 0.75 looks
away from the camera (into the plate), u = 0.5 to the left, u = 0 to the right, u = 0.25 toward the camera. Azimuth
here is in degrees from straight away from the camera, negative to the left. Colors are linear. The PNG is written
sRGB-encoded and normalized to its peak; the peak is printed. numpy and Pillow.
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image


def s2l(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def l2s(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def triple(s):
    return np.array([float(v) for v in s.split(",")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plate")
    ap.add_argument("out")
    ap.add_argument("--focal", type=float, default=50.0, help="mm, 36 mm film width")
    ap.add_argument("--tilt", type=float, default=0.0, help="degrees the camera looks down")
    ap.add_argument("--sun", required=True, help="azimuth,elevation in degrees")
    ap.add_argument("--lit", required=True, help="plate's sunlit ground, linear R,G,B")
    ap.add_argument("--shadow", required=True, help="plate's shadowed ground, linear R,G,B")
    ap.add_argument("--sky-target", required=True, help="hue of the light the sky gives an up-facing floor, linear R,G,B")
    ap.add_argument("--clamp-deg", type=float, default=4.0, help="radius around the sun replaced by its surroundings")
    ap.add_argument("--fall-deg", type=float, default=15.0, help="angle over which the sky above the frame reaches the zenith color")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--far-gain", type=float, default=0.75, help="horizon opposite the sun, over the last horizon value the plate shows")
    ap.add_argument("--far-deg", type=float, default=30.0, help="angle over which the horizon falls to that value")
    ap.add_argument("--zenith-margin", type=float, default=1.25, help="above 1: the zenith keeps some of every channel")
    ap.add_argument("--ground-gain", type=float, default=0.557, help="ground radiance over the plate ground value, in the sky's units")
    # "--sun -17,4" as two arguments: argparse on Python 3.12 reads a value starting with a minus sign as a flag
    argv = sys.argv[1:]
    for i in range(len(argv) - 1):
        if argv[i] == "--sun":
            argv[i:i + 2] = ["--sun=" + argv[i + 1]]
            break
    a = ap.parse_args(argv)

    with Image.open(a.plate) as im:
        plate = s2l(np.asarray(im.convert("RGB")).astype(np.float64) / 255.0)
    ph, pw = plate.shape[:2]
    zoom = pw * a.focal / 36.0
    t = np.radians(a.tilt)
    saz, sel = (float(v) for v in a.sun.split(","))
    lit, shd, tgt = triple(a.lit), triple(a.shadow), triple(a.sky_target)

    W, H = a.width, a.width // 2
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    az = (u - 0.75) * 360.0
    az = (az + 180.0) % 360.0 - 180.0
    el = 90.0 - v * 180.0
    AZ, EL = np.meshgrid(np.radians(az), np.radians(el))
    dx, dy, dz = np.sin(AZ) * np.cos(EL), -np.sin(EL), np.cos(AZ) * np.cos(EL)
    yc, zc = np.cos(t) * dy - np.sin(t) * dz, np.sin(t) * dy + np.cos(t) * dz
    with np.errstate(divide="ignore", invalid="ignore"):
        px, py = pw / 2 + zoom * dx / zc, ph / 2 + zoom * yc / zc
    horizon = ph / 2 - zoom * np.tan(t)
    seen = (zc > 0) & (px >= 0) & (px < pw - 1) & (py >= 0) & (py < horizon - 2) & (EL > 0)
    sky = np.zeros((H, W, 3))
    xi, yi = np.clip(px, 0, pw - 1).astype(int), np.clip(py, 0, ph - 1).astype(int)
    sky[seen] = plate[yi[seen], xi[seen]]

    # sun disc: clamp to the 90th percentile of the ring just outside it
    gam = np.degrees(np.arccos(np.clip(np.sin(EL) * np.sin(np.radians(sel)) + np.cos(EL) * np.cos(np.radians(sel)) * np.cos(AZ - np.radians(saz)), -1, 1)))
    ring = seen & (gam > a.clamp_deg) & (gam < 2 * a.clamp_deg)
    cap = np.percentile(sky[ring], 90, axis=0) if ring.any() else sky[seen].max(0)
    disc = seen & (gam <= a.clamp_deg)
    sky[disc] = np.minimum(sky[disc], cap)

    # horizon profile by azimuth distance from the sun, from the seen band, mirrored about the sun
    daz = np.abs(((az - saz) + 180.0) % 360.0 - 180.0)
    band = seen & (np.degrees(EL) < 3.5)
    prof_d = np.arange(0, 181)
    prof = np.zeros((181, 3))
    have = np.zeros(181, bool)
    Dg = np.broadcast_to(daz[None, :], (H, W))
    for d in prof_d:
        m = band & (np.abs(Dg - d) < 0.5)
        if m.any():
            prof[d] = sky[m].mean(0)
            have[d] = True
    last = prof_d[have].max()
    far = prof[last] * a.far_gain
    for d in prof_d[~have]:
        if d < last:
            prof[d] = prof[have][np.argmin(np.abs(prof_d[have] - d))]
        else:
            prof[d] = far + (prof[last] - far) * np.exp(-(d - last) / a.far_deg)
    hz = prof[np.clip(np.round(Dg).astype(int), 0, 180)]

    # above the band: the profile blends up to the zenith color with elevation
    k = np.exp(-np.clip(np.degrees(EL), 0, None) / a.fall_deg)
    base = np.where(seen[..., None], sky, 0)

    def build(zen):
        model = zen + (hz - zen) * k[..., None]
        up = np.where(seen[..., None], base, model)
        return np.where((EL > 0)[..., None], up, 0)

    # solve the zenith so the up-facing floor's light has the hue of the target
    cosw = np.clip(np.sin(EL), 0, None) * np.cos(EL)
    wsum = cosw.sum()
    E0 = (build(np.zeros(3)) * cosw[..., None]).sum((0, 1)) / wsum
    # the zenith reaches only the sky the plate does not show, with weight 1 - k (build above)
    C = (np.where(seen, 0.0, 1 - k) * cosw).sum() / wsum
    if C < 1e-6:
        sys.exit("the plate shows the whole upper sky: no zenith to solve")
    zen_dir = tgt / tgt.max()
    s = max((E0 / zen_dir).max() * a.zenith_margin, 1e-6)
    zen = (s * zen_dir - E0) / C
    zen = np.clip(zen, 0, None)
    up = build(zen)
    E = (up * cosw[..., None]).sum((0, 1)) / wsum

    # ground: lit toward the sun at low angles, shadowed near the nadir and away from the sun
    toward = np.clip(np.cos(AZ - np.radians(saz)), 0, None)
    near_h = np.clip(1 + np.degrees(EL) / 45.0, 0, 1)
    wl = (toward * near_h)[..., None]
    ground = shd + (lit - shd) * wl
    scale = float((E / tgt).mean()) * a.ground_gain
    env = np.where((EL > 0)[..., None], up, ground * scale)

    peak = env.max()
    Image.fromarray((l2s(env / peak) * 255 + 0.5).astype(np.uint8)).save(a.out)
    print(json.dumps({"out": a.out, "peak": round(float(peak), 5), "zenith": [round(float(x), 4) for x in zen],
                      "floorLight": [round(float(x), 4) for x in E], "sunClamp": [round(float(x), 4) for x in cap],
                      "seenPx": int(seen.sum())}))


if __name__ == "__main__":
    main()
