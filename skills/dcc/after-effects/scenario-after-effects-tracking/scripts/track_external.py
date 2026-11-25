"""Track a shot outside After Effects and write keys the AEX.track helpers can apply.

Requires Python 3 with OpenCV (cv2) and numpy. Reads a video file or a PNG sequence folder.

  plane : four corners of a flat surface (screen, sign) from the corners on one reference frame.
          --mode chain : frame-to-frame optical flow + homography (fast; accumulates drift)
          --mode ref   : every frame registered to the reference frame (no accumulated drift)
          --mode hybrid: chain, re-anchored to the reference every --anchor frames (default)
  shake : per-frame camera shake (dx, dy, rotation in degrees) of a mostly static scene,
          relative to the reference frame, for stabilization by keys.

  python3 track_external.py plane SHOT --corners "x,y x,y x,y x,y" --ref 0 --out plane.json
  python3 track_external.py shake SHOT --ref 0 --out shake.json
  python3 track_external.py score plane.json truth.json      (pixel error per frame vs a known path)
  python3 track_external.py banner FRAME.png [FRAME.png ...]  (analysis banner in a rendered frame:
          "analyzing" blue band, "stabilizing" orange band, or "none")

Corners are given UL UR LR LL. Output JSON: {"fps", "size", "ref", "mode", "corners": [[[x,y]x4] per frame],
"inliers": [...], "reproj": [...]} or {"shake": [[dx, dy, rot] per frame]}.
"""
import argparse, glob, json, os, sys
import numpy as np
import cv2


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, data, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, **kw)



def frames(src):
    if os.path.isdir(src):
        files = sorted(glob.glob(os.path.join(src, "*.png")) + glob.glob(os.path.join(src, "*.jpg")))
        return [cv2.imread(f) for f in files], None
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or None
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f)
    return out, fps


def gray(f):
    return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)


def region_mask(shape, quad, grow=1.0):
    m = np.zeros(shape[:2], np.uint8)
    q = np.float32(quad)
    c = q.mean(0)
    q = c + (q - c) * grow
    cv2.fillConvexPoly(m, q.astype(np.int32), 255)
    return m


def homography(g0, g1, mask0, H0=None):
    """Homography mapping frame g0 to frame g1, from features of g0 inside mask0."""
    pts = cv2.goodFeaturesToTrack(g0, 400, 0.01, 6, mask=mask0)
    if pts is None or len(pts) < 8:
        return None, 0, None
    guess = None
    flags = 0
    if H0 is not None:  # predict positions so large motion still converges
        guess = cv2.perspectiveTransform(pts, H0).astype(np.float32)
        flags = cv2.OPTFLOW_USE_INITIAL_FLOW
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, pts, guess, winSize=(31, 31), maxLevel=4, flags=flags,
                                         criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
    back, st2, _ = cv2.calcOpticalFlowPyrLK(g1, g0, p1, pts.copy(), winSize=(31, 31), maxLevel=4,
                                            flags=cv2.OPTFLOW_USE_INITIAL_FLOW)
    good = (st.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm((back - pts).reshape(-1, 2), axis=1) < 1.0)
    if good.sum() < 8:
        return None, int(good.sum()), None
    H, inl = cv2.findHomography(pts[good], p1[good], cv2.RANSAC, 2.0)
    if H is None:
        return None, 0, None
    a = pts[good][inl.ravel() == 1]; b = p1[good][inl.ravel() == 1]
    err = float(np.linalg.norm(cv2.perspectiveTransform(a, H) - b, axis=2).mean()) if len(a) else None
    return H, int(inl.sum()), err


def refine(gref, gj, mref, Hpred):
    """Register frame j to the reference: warp j back with the prediction, measure the small residual."""
    h, w = gref.shape
    back = cv2.warpPerspective(gj, np.linalg.inv(Hpred), (w, h), flags=cv2.INTER_LINEAR)
    Hr, k, e = homography(gref, back, mref)
    if Hr is None:
        return None, k, e
    return Hpred @ Hr, k, e


def track_plane(fr, corners, ref, mode, anchor):
    n = len(fr)
    g = [gray(f) for f in fr]
    q0 = np.float32(corners).reshape(-1, 1, 2)
    m0 = region_mask(g[ref].shape, corners, 0.95)
    H = [None] * n; H[ref] = np.eye(3); inl = [0] * n; rep = [0.0] * n
    for step in (1, -1):  # forward then backward from the reference frame
        i = ref
        while 0 <= i + step < n:
            j = i + step
            qi = cv2.perspectiveTransform(q0, H[i]).reshape(-1, 2)
            Hc, k, e = homography(g[i], g[j], region_mask(g[i].shape, qi, 0.95))
            Hj = Hc @ H[i] if Hc is not None else H[i]  # hold the last pose when lost; inliers flag it
            if mode == "ref" or (mode == "hybrid" and abs(j - ref) % anchor == 0):
                Hr, k2, e2 = refine(g[ref], g[j], m0, Hj)
                if Hr is not None:
                    Hj, k, e = Hr, k2, e2
            H[j], inl[j], rep[j] = Hj, k, e
            i = j
    out = [cv2.perspectiveTransform(q0, h).reshape(-1, 2).round(3).tolist() for h in H]
    return out, inl, rep


def track_shake(fr, ref):
    g = [gray(f) for f in fr]
    h, w = g[ref].shape
    m = np.zeros((h, w), np.uint8); m[int(h * 0.05):int(h * 0.95), int(w * 0.05):int(w * 0.95)] = 255
    pts = cv2.goodFeaturesToTrack(g[ref], 600, 0.01, 10, mask=m)
    res = []
    for j in range(len(g)):
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g[ref], g[j], pts, None, winSize=(41, 41), maxLevel=5)
        ok = st.ravel() == 1
        A, _ = cv2.estimateAffinePartial2D(pts[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
        rot = float(np.degrees(np.arctan2(A[1, 0], A[0, 0])))
        # shake expressed about the frame center: frame j = R(rot) about center, then shifted by (dx, dy)
        c = np.array([w / 2, h / 2])
        R = A[:, :2]; t = A[:, 2]
        d = R @ c + t - c
        res.append([round(float(d[0]), 3), round(float(d[1]), 3), round(rot, 4)])
    return res


def score(track, truth):
    t = _read_json(truth); a = _read_json(track)
    if "corners" in a:
        e = np.linalg.norm(np.array(a["corners"]) - np.array(t["corners"]), axis=2)  # frames x 4
        per = e.mean(1)
        return {"meanPx": round(float(per.mean()), 3), "maxPx": round(float(e.max()), 3),
                "worstFrame": int(per.argmax()), "perFrame": [round(float(x), 2) for x in per]}
    s = np.array(a["shake"]); u = np.array(t["shake"]); u = u - u[a.get("ref", 0)]
    # truth is absolute shake; tracked is relative to ref: compare relative motion
    d = s - u
    return {"meanPx": round(float(np.linalg.norm(d[:, :2], axis=1).mean()), 3),
            "maxPx": round(float(np.linalg.norm(d[:, :2], axis=1).max()), 3),
            "meanRotDeg": round(float(np.abs(d[:, 2]).mean()), 4)}


def banner(path):
    """Warp Stabilizer and 3D Camera Tracker draw a full-width band across the middle of the frame while
    they work: blue for "Analyzing in background", orange for "Stabilizing". Scripts cannot read the status."""
    img = cv2.imread(path).astype(np.float32)
    h = img.shape[0]
    band = img[int(h * 0.41):int(h * 0.55)]
    d = float((band[:, :, 0] - band[:, :, 2]).mean())  # blue minus red
    return {"file": os.path.basename(path), "state": "analyzing" if d > 100 else ("stabilizing" if d < -80 else "none"), "blueMinusRed": round(d, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plane", "shake", "score", "banner"])
    ap.add_argument("src"); ap.add_argument("truth", nargs="*")
    ap.add_argument("--corners"); ap.add_argument("--ref", type=int, default=0)
    ap.add_argument("--mode", default="hybrid", choices=["chain", "ref", "hybrid"])
    ap.add_argument("--anchor", type=int, default=12); ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "score":
        print(json.dumps(score(a.src, a.truth[0]))); return
    if a.cmd == "banner":
        for f in [a.src] + a.truth:
            print(json.dumps(banner(f)))
        return
    fr, fps = frames(a.src)
    res = {"fps": fps, "size": [fr[0].shape[1], fr[0].shape[0]], "ref": a.ref, "frames": len(fr)}
    if a.cmd == "plane":
        cs = [[float(v) for v in p.split(",")] for p in a.corners.split()]
        res["mode"] = a.mode
        res["corners"], res["inliers"], res["reproj"] = track_plane(fr, cs, a.ref, a.mode, a.anchor)
    else:
        res["shake"] = track_shake(fr, a.ref)
    _write_json(a.out, res) if a.out else print(json.dumps(res))
    print("wrote", a.out, "frames", len(fr), file=sys.stderr)


if __name__ == "__main__":
    main()
