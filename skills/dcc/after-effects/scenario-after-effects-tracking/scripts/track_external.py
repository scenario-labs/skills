"""Track a shot outside After Effects and write keys the AEX.track helpers can apply.

Requires Python 3 with OpenCV (cv2) and numpy. Reads a video file or a PNG sequence folder.

  plane : four corners of a flat surface (screen, sign) from the corners on one reference frame.
          --mode chain : frame-to-frame optical flow + homography (fast; accumulates drift)
          --mode ref   : every frame registered to the reference frame (no accumulated drift)
          --mode hybrid: chain, re-anchored to the reference every --anchor frames (default)
  shake : per-frame camera shake (dx, dy, rotation in degrees) of a mostly static scene,
          relative to the reference frame, for stabilization by keys. With --corners, only features
          inside that quad on the reference frame are used: the motion of one object (object stabilization).

  python3 track_external.py plane SHOT --corners "x,y x,y x,y x,y" --ref 0 --out plane.json
  python3 track_external.py shake SHOT --ref 0 --out shake.json
  python3 track_external.py score plane.json truth.json      (pixel error per frame vs a known path)
  python3 track_external.py banner FRAME.png [FRAME.png ...]  (analysis banner in a rendered frame:
          "analyzing" blue band, "stabilizing" orange band, or "none")
  python3 track_external.py point plane.json --point x,y --out points.json
          (a reference-frame point carried through each frame's map: exact under perspective)
  python3 track_external.py slide SHOT --track plane.json --point x,y [--patch 240 --search 128]
          (independent check: catches a track that slid or jumped to a neighbor feature)
  python3 track_external.py locate RENDER.mp4 --path points.json --color 0,255,0
          (centroid of a pure-color proof marker per frame against the path: the slide of a placed element)

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



def _sequence(src):
    return sorted(glob.glob(os.path.join(src, "*.png")) + glob.glob(os.path.join(src, "*.jpg")))


def iter_frames(src):
    """Color frames one at a time, in order: a PNG or JPG folder by file name, or a video file."""
    if os.path.isdir(src):
        for f in _sequence(src):
            yield cv2.imread(f)
        return
    cap = cv2.VideoCapture(src)
    try:
        while True:
            ok, f = cap.read()
            if not ok:
                break
            yield f
    finally:
        cap.release()


def video_fps(src):
    if os.path.isdir(src):
        return None
    cap = cv2.VideoCapture(src)
    try:
        return cap.get(cv2.CAP_PROP_FPS) or None
    finally:
        cap.release()


def frame_at(src, index):
    """One color frame by index, decoded without keeping the frames before it."""
    for i, f in enumerate(iter_frames(src)):
        if i == index:
            return f
    raise ValueError("frame %d is past the end of %s" % (index, src))


def frames(src):
    """Every color frame in memory, and the frame rate. The trackers below stream with iter_frames instead."""
    return list(iter_frames(src)), video_fps(src)


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
    """fr: color frames, any iterable. Only grayscale frames before the reference are kept (the backward pass
    needs them); after it, two working frames and the reference."""
    q0 = np.float32(corners).reshape(-1, 1, 2)
    H, inl, rep, before = {}, {}, {}, []
    st = {}

    def step(gi, gj, Hi, j):
        qi = cv2.perspectiveTransform(q0, Hi).reshape(-1, 2)
        Hc, k, e = homography(gi, gj, region_mask(gi.shape, qi, 0.95))
        Hj = Hc @ Hi if Hc is not None else Hi  # hold the last pose when lost; inliers flag it
        if mode == "ref" or (mode == "hybrid" and abs(j - ref) % anchor == 0):
            Hr, k2, e2 = refine(st["gref"], gj, st["m0"], Hj)
            if Hr is not None:
                Hj, k, e = Hr, k2, e2
        return Hj, k, e

    n, gprev = 0, None
    for i, f in enumerate(fr):  # forward from the reference frame while decoding
        n = i + 1
        g = gray(f)
        if i < ref:
            before.append(g)
        elif i == ref:
            st["gref"], st["m0"] = g, region_mask(g.shape, corners, 0.95)
            H[i], inl[i], rep[i] = np.eye(3), 0, 0.0
        else:
            H[i], inl[i], rep[i] = step(gprev, g, H[i - 1], i)
        gprev = g
    if ref >= n:
        raise ValueError("reference frame %d is past the last frame (%d frames)" % (ref, n))
    gprev = st["gref"]
    for j in range(ref - 1, -1, -1):  # then backward from the reference frame
        g = before[j]
        H[j], inl[j], rep[j] = step(gprev, g, H[j + 1], j)
        before[j] = None
        gprev = g
    out = [cv2.perspectiveTransform(q0, H[i]).reshape(-1, 2).round(3).tolist() for i in range(n)]
    return out, [inl[i] for i in range(n)], [rep[i] for i in range(n)]


def track_shake(fr, ref, quad=None, ref_frame=None):
    """fr: color frames, any iterable. ref_frame: the reference frame in color, needed before the first frame
    when fr is a stream (main reads it with frame_at); a list supplies it by index."""
    gref = gray(ref_frame if ref_frame is not None else fr[ref])
    h, w = gref.shape
    if quad:
        m = region_mask(gref.shape, quad, 1.0)
    else:
        m = np.zeros((h, w), np.uint8); m[int(h * 0.05):int(h * 0.95), int(w * 0.05):int(w * 0.95)] = 255
    pts = cv2.goodFeaturesToTrack(gref, 600, 0.01, 10, mask=m)
    res, inl = [], []
    prev = pts
    for j, f in enumerate(fr):
        # seed each frame from the previous frame's points, but measure against the reference: no accumulated drift
        guess = prev if j > 0 else pts
        p1, st, _ = cv2.calcOpticalFlowPyrLK(gref, gray(f), pts, guess.copy(), winSize=(41, 41), maxLevel=5,
                                             flags=cv2.OPTFLOW_USE_INITIAL_FLOW)
        ok = st.ravel() == 1
        A, mk = cv2.estimateAffinePartial2D(pts[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
        inl.append(int(mk.sum()) if mk is not None else 0)
        prev = p1
        rot = float(np.degrees(np.arctan2(A[1, 0], A[0, 0])))
        # shake expressed about the frame center: frame j = R(rot) about center, then shifted by (dx, dy)
        c = np.array([w / 2, h / 2])
        R = A[:, :2]; t = A[:, 2]
        d = R @ c + t - c
        res.append([round(float(d[0]), 3), round(float(d[1]), 3), round(rot, 4)])
    return res, inl


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


def mappings(trk):
    """Per-frame 3x3 maps from the reference frame to each frame, from a plane.json (homography of the
    reference quad) or a shake.json (rotation about the frame center, then shift)."""
    ref = trk.get("ref", 0)
    if "corners" in trk:
        q0 = np.float32(trk["corners"][ref])
        return [cv2.getPerspectiveTransform(q0, np.float32(q)) for q in trk["corners"]]
    w, h = trk["size"]
    c = np.array([w / 2.0, h / 2.0])
    out = []
    for dx, dy, rot in trk["shake"]:
        a = np.radians(rot)
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        t = c - R @ c + [dx, dy]
        out.append(np.array([[R[0, 0], R[0, 1], t[0]], [R[1, 0], R[1, 1], t[1]], [0, 0, 1]]))
    return out


def carry(trk, pt):
    """A point picked on the reference frame, carried through every frame's map: the path a pin,
    a callout or a marker must follow. Exact under perspective for a plane track."""
    p = np.float32([[pt]])
    return [cv2.perspectiveTransform(p, M).reshape(2).round(3).tolist() for M in mappings(trk)]


def slide(src, trk, pt, patch, search, every, ambig=0.02):
    """Independent check of a track at one point: warp each frame back to the reference with the track's own
    map, then find the reference patch (context around the point) by template matching. A good track finds it
    where it was; a tracker that slid or jumped to a similar neighbor feature finds it offset. Offsets are in
    reference-frame pixels; score is the normalized correlation of the best match (1 = identical)."""
    M = mappings(trk)
    ref = trk.get("ref", 0)
    g0 = gray(frame_at(src, ref))
    h, w = g0.shape
    x, y = int(round(pt[0])), int(round(pt[1]))
    r = patch // 2
    tpl = g0[max(y - r, 0):y + r, max(x - r, 0):x + r]
    ox, oy = x - max(x - r, 0), y - max(y - r, 0)
    rows = []
    for i, f in enumerate(iter_frames(src)):
        if i >= len(M):
            break
        if i % every:
            continue
        back = cv2.warpPerspective(gray(f), np.linalg.inv(M[i]), (w, h), flags=cv2.INTER_LINEAR)
        x0, y0 = max(x - r - search, 0), max(y - r - search, 0)
        win = back[y0:min(y + r + search, h), x0:min(x + r + search, w)]
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
        _, sc, _, loc = cv2.minMaxLoc(res)
        # repeated features (a row of identical buttons) match almost as well one period away: keep the match at
        # the tracked spot (within 3 px) unless the far match is clearly better
        cxr, cyr = x - r - x0 + (r - ox), y - r - y0 + (r - oy)
        near = res[max(cyr - 3, 0):cyr + 4, max(cxr - 3, 0):cxr + 4]
        if near.size:
            _, nsc, _, nloc = cv2.minMaxLoc(near)
            if sc - nsc <= ambig:
                sc, loc = nsc, (nloc[0] + max(cxr - 3, 0), nloc[1] + max(cyr - 3, 0))
        dx, dy = loc[0] + x0 + ox - x, loc[1] + y0 + oy - y
        rows.append([i, round(float(np.hypot(dx, dy)), 2), round(float(sc), 3)])
    off = np.array([r_[1] for r_ in rows])
    sco = np.array([r_[2] for r_ in rows])
    worst = rows[int(off.argmax())]
    return {"point": pt, "patch": patch, "search": search, "meanPx": round(float(off.mean()), 2),
            "maxPx": round(float(off.max()), 2), "worstFrame": worst[0], "minScore": round(float(sco.min()), 3),
            "over3px": [r_[0] for r_ in rows if r_[1] > 3], "jumps": runs(rows, 3.0, 3), "perFrame": rows}


def runs(rows, px, n):
    """[first, last] frame of every run of n or more checked frames over px: a slide or a jump to a neighbor feature.
    Isolated frames over px are matcher noise on repeated features."""
    out, cur = [], []
    for r_ in rows + [[None, 0.0, 0.0]]:
        if r_[1] > px:
            cur.append(r_[0])
        else:
            if len(cur) >= n:
                out.append([cur[0], cur[-1]])
            cur = []
    return out


def locate(src, rgb, tol, path):
    """Centroid of a pure-color proof marker on every frame of a render, against the expected path
    (a list of [x, y], one per frame, as `point` writes it): the slide of whatever rides the track.
    complete is true only when every frame has a marker and the frame, marker and path counts agree:
    the gate reads it before meanPx, which averages only the frames where the marker was found."""
    col = np.array(rgb[::-1], np.float32)  # frames are BGR
    rows, n = [], 0
    for i, f in enumerate(iter_frames(src)):
        n = i + 1
        d = np.abs(f.astype(np.float32) - col).max(2)
        ys, xs = np.nonzero(d <= tol)
        if len(xs) < 4:
            rows.append([i, None, None, None]); continue
        cx, cy = float(xs.mean()), float(ys.mean())
        e = float(np.hypot(cx - path[i][0], cy - path[i][1])) if i < len(path) else None
        rows.append([i, round(cx, 2), round(cy, 2), round(e, 2) if e is not None else None])
    err = np.array([r_[3] for r_ in rows if r_[3] is not None])
    missing = [r_[0] for r_ in rows if r_[1] is None]
    return {"frames": n, "found": int(len(err)), "pathFrames": len(path), "missing": missing,
            "complete": bool(n > 0 and not missing and len(err) == n == len(path)),
            "meanPx": round(float(err.mean()), 2) if len(err) else None,
            "maxPx": round(float(err.max()), 2) if len(err) else None,
            "lastPx": rows[-1][3] if rows else None, "perFrame": rows}


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
    ap.add_argument("cmd", choices=["plane", "shake", "score", "banner", "point", "slide", "locate"])
    ap.add_argument("src"); ap.add_argument("truth", nargs="*")
    ap.add_argument("--corners"); ap.add_argument("--ref", type=int, default=0)
    ap.add_argument("--mode", default="hybrid", choices=["chain", "ref", "hybrid"])
    ap.add_argument("--anchor", type=int, default=12); ap.add_argument("--out")
    ap.add_argument("--point", help="x,y on the reference frame")
    ap.add_argument("--track", help="plane.json or shake.json (slide)")
    ap.add_argument("--path", help="points.json from `point` (locate)")
    ap.add_argument("--patch", type=int, default=240); ap.add_argument("--search", type=int, default=128)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--color", default="0,255,0", help="marker r,g,b (locate)"); ap.add_argument("--tol", type=int, default=60)
    a = ap.parse_args()
    out = None
    if a.cmd == "score":
        print(json.dumps(score(a.src, a.truth[0]))); return
    if a.cmd == "point":
        trk = _read_json(a.src); pt = [float(v) for v in a.point.split(",")]
        out = {"ref": trk.get("ref", 0), "point": pt, "points": carry(trk, pt)}
    elif a.cmd == "slide":
        trk = _read_json(a.track); pt = [float(v) for v in a.point.split(",")]
        out = slide(a.src, trk, pt, a.patch, a.search, a.every)
    elif a.cmd == "locate":
        path = _read_json(a.path)["points"]
        out = locate(a.src, [int(v) for v in a.color.split(",")], a.tol, path)
    if out is not None:
        if a.out:
            _write_json(a.out, out)
        short = {k: v for k, v in out.items() if k not in ("perFrame", "points")}
        print(json.dumps(short)); return
    if a.cmd == "banner":
        for f in [a.src] + a.truth:
            print(json.dumps(banner(f)))
        return
    first = frame_at(a.src, 0)
    res = {"fps": video_fps(a.src), "size": [first.shape[1], first.shape[0]], "ref": a.ref}
    if a.cmd == "plane":
        cs = [[float(v) for v in p.split(",")] for p in a.corners.split()]
        res["mode"] = a.mode
        res["corners"], res["inliers"], res["reproj"] = track_plane(iter_frames(a.src), cs, a.ref, a.mode, a.anchor)
        res["frames"] = len(res["corners"])
    else:
        q = [[float(v) for v in p.split(",")] for p in a.corners.split()] if a.corners else None
        res["shake"], res["inliers"] = track_shake(iter_frames(a.src), a.ref, q, frame_at(a.src, a.ref))
        res["frames"] = len(res["shake"])
    _write_json(a.out, res) if a.out else print(json.dumps(res))
    print("wrote", a.out, "frames", res["frames"], file=sys.stderr)


if __name__ == "__main__":
    main()
