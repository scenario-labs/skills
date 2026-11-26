"""Review round 1, group G: track_external.py streams frames, and its locate gate fails closed.

- The streaming trackers (plane in chain, ref and hybrid modes, shake with and without a quad, slide, locate) give the
  same results as the former implementation, which held every color frame and every grayscale frame at once. The
  former orchestration is kept below verbatim as the reference; it calls the same OpenCV helpers.
- locate reports complete only when every frame has the marker and the frame, marker and path counts agree.

numpy and OpenCV only. Each case builds a planted clip (a textured plate moving 2 px right and 1 px down per frame,
with a green proof marker riding it) in a temporary folder.
"""

import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
TRACKING = FAMILY / "scenario-after-effects-tracking" / "scripts"
sys.path.insert(0, str(TRACKING))

import track_external as te  # noqa: E402

CORNERS = [[40, 30], [150, 30], [150, 110], [40, 110]]
N, W, H, REF = 10, 192, 144, 3


def plant_clip(folder, n=N, drop_marker=None):
    """PNG sequence; returns the marker path. drop_marker: a frame index drawn without the marker."""
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    tex = cv2.GaussianBlur((rng.random((H * 2, W * 2)) * 255).astype(np.uint8), (5, 5), 1.2)
    tex = cv2.cvtColor(tex, cv2.COLOR_GRAY2BGR)
    path = []
    for i in range(n):
        dx, dy = 2.0 * i, 1.0 * i
        f = cv2.warpAffine(tex, np.float32([[1, 0, -W / 2 + dx], [0, 1, -H / 2 + dy]]), (W, H), flags=cv2.INTER_LINEAR)
        cx, cy = int(60 + dx), int(50 + dy)
        if i != drop_marker:
            f[cy - 3:cy + 4, cx - 3:cx + 4] = (0, 255, 0)
        path.append([cx, cy])
        cv2.imwrite(str(folder / ("f%03d.png" % i)), f)
    return path


# ---------------------------------------------------------------- the former implementation (reference)

def old_frames(src):
    import glob
    import os
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


def old_track_plane(fr, corners, ref, mode, anchor):
    n = len(fr)
    g = [te.gray(f) for f in fr]
    q0 = np.float32(corners).reshape(-1, 1, 2)
    m0 = te.region_mask(g[ref].shape, corners, 0.95)
    H_ = [None] * n; H_[ref] = np.eye(3); inl = [0] * n; rep = [0.0] * n
    for step in (1, -1):
        i = ref
        while 0 <= i + step < n:
            j = i + step
            qi = cv2.perspectiveTransform(q0, H_[i]).reshape(-1, 2)
            Hc, k, e = te.homography(g[i], g[j], te.region_mask(g[i].shape, qi, 0.95))
            Hj = Hc @ H_[i] if Hc is not None else H_[i]
            if mode == "ref" or (mode == "hybrid" and abs(j - ref) % anchor == 0):
                Hr, k2, e2 = te.refine(g[ref], g[j], m0, Hj)
                if Hr is not None:
                    Hj, k, e = Hr, k2, e2
            H_[j], inl[j], rep[j] = Hj, k, e
            i = j
    out = [cv2.perspectiveTransform(q0, h).reshape(-1, 2).round(3).tolist() for h in H_]
    return out, inl, rep


def old_track_shake(fr, ref, quad=None):
    g = [te.gray(f) for f in fr]
    h, w = g[ref].shape
    if quad:
        m = te.region_mask(g[ref].shape, quad, 1.0)
    else:
        m = np.zeros((h, w), np.uint8); m[int(h * 0.05):int(h * 0.95), int(w * 0.05):int(w * 0.95)] = 255
    pts = cv2.goodFeaturesToTrack(g[ref], 600, 0.01, 10, mask=m)
    res, inl = [], []
    prev = pts
    for j in range(len(g)):
        guess = prev if j > 0 else pts
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g[ref], g[j], pts, guess.copy(), winSize=(41, 41), maxLevel=5,
                                             flags=cv2.OPTFLOW_USE_INITIAL_FLOW)
        ok = st.ravel() == 1
        A, mk = cv2.estimateAffinePartial2D(pts[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
        inl.append(int(mk.sum()) if mk is not None else 0)
        prev = p1
        rot = float(np.degrees(np.arctan2(A[1, 0], A[0, 0])))
        c = np.array([w / 2, h / 2])
        d = A[:, :2] @ c + A[:, 2] - c
        res.append([round(float(d[0]), 3), round(float(d[1]), 3), round(rot, 4)])
    return res, inl


def old_module():
    """track_external with frames() swapped for the former eager one: slide and locate as they ran before."""
    src = (TRACKING / "track_external.py").read_text(encoding="utf-8")
    mod = types.ModuleType("track_external_eager")
    exec(compile(src, "track_external_eager", "exec"), mod.__dict__)
    mod.frames = old_frames
    mod.iter_frames = lambda s: iter(old_frames(s)[0])
    mod.frame_at = lambda s, i: old_frames(s)[0][i]
    return mod


def as_json(x):
    return json.loads(json.dumps(x))


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class StreamingMatchesFormer(Temp):
    def setUp(self):
        super().setUp()
        self.clip = self.tmp / "clip"
        self.path = plant_clip(self.clip)
        self.fr, _ = old_frames(str(self.clip))

    def test_iter_frames_is_lazy(self):
        it = te.iter_frames(str(self.clip))
        self.assertIsInstance(it, types.GeneratorType)
        self.assertEqual(sum(1 for _ in it), N)
        self.assertTrue(np.array_equal(te.frame_at(str(self.clip), REF), self.fr[REF]))

    def test_plane_every_mode(self):
        for mode in ("chain", "ref", "hybrid"):
            new = te.track_plane(te.iter_frames(str(self.clip)), CORNERS, REF, mode, 4)
            old = old_track_plane(self.fr, CORNERS, REF, mode, 4)
            self.assertEqual(as_json(new), as_json(old), mode)

    def test_plane_accepts_a_list_and_rejects_a_ref_past_the_end(self):
        self.assertEqual(as_json(te.track_plane(self.fr, CORNERS, REF, "hybrid", 4)),
                         as_json(old_track_plane(self.fr, CORNERS, REF, "hybrid", 4)))
        with self.assertRaises(ValueError):
            te.track_plane(te.iter_frames(str(self.clip)), CORNERS, N + 2, "hybrid", 4)

    def test_shake_with_and_without_quad(self):
        for quad in (None, CORNERS):
            new = te.track_shake(te.iter_frames(str(self.clip)), REF, quad, te.frame_at(str(self.clip), REF))
            self.assertEqual(as_json(new), as_json(old_track_shake(self.fr, REF, quad)), quad)

    def test_slide_and_locate(self):
        trk = {"ref": REF, "corners": old_track_plane(self.fr, CORNERS, REF, "hybrid", 4)[0]}
        old = old_module()
        self.assertEqual(as_json(te.slide(str(self.clip), trk, [95, 70], 40, 16, 1)),
                         as_json(old.slide(str(self.clip), trk, [95, 70], 40, 16, 1)))
        self.assertEqual(as_json(te.slide(str(self.clip), trk, [95, 70], 40, 16, 3)),
                         as_json(old.slide(str(self.clip), trk, [95, 70], 40, 16, 3)))
        new = te.locate(str(self.clip), [0, 255, 0], 40, self.path)
        ref = old.locate(str(self.clip), [0, 255, 0], 40, self.path)
        for k in ("frames", "found", "meanPx", "maxPx", "lastPx", "perFrame"):
            self.assertEqual(as_json(new[k]), as_json(ref[k]), k)

    def test_video_file(self):
        mov = self.tmp / "clip.avi"
        wr = cv2.VideoWriter(str(mov), cv2.VideoWriter_fourcc(*"MJPG"), 24, (W, H))
        if not wr.isOpened():
            self.skipTest("no MJPG writer in this OpenCV build")
        for f in self.fr:
            wr.write(f)
        wr.release()
        fr, fps = old_frames(str(mov))
        if len(fr) != N:
            self.skipTest("this OpenCV build does not read back its own MJPG file")
        self.assertEqual(te.video_fps(str(mov)), fps)
        self.assertEqual(as_json(te.track_plane(te.iter_frames(str(mov)), CORNERS, REF, "hybrid", 4)),
                         as_json(old_track_plane(fr, CORNERS, REF, "hybrid", 4)))

    def test_command_line_plane(self):
        out = self.tmp / "plane.json"
        p = subprocess.run([sys.executable, str(TRACKING / "track_external.py"), "plane", str(self.clip),
                            "--corners", " ".join("%d,%d" % tuple(c) for c in CORNERS), "--ref", str(REF),
                            "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        res = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(res["frames"], N)
        self.assertEqual(res["size"], [W, H])
        self.assertEqual(res["corners"], old_track_plane(self.fr, CORNERS, REF, "hybrid", 12)[0])


class LocateGate(Temp):
    def test_complete_when_every_frame_has_the_marker(self):
        path = plant_clip(self.tmp / "ok")
        res = te.locate(str(self.tmp / "ok"), [0, 255, 0], 40, path)
        self.assertTrue(res["complete"])
        self.assertEqual((res["frames"], res["found"], res["pathFrames"], res["missing"]), (N, N, N, []))

    def test_a_frame_without_the_marker_fails_and_keeps_its_row(self):
        path = plant_clip(self.tmp / "gap", drop_marker=5)
        res = te.locate(str(self.tmp / "gap"), [0, 255, 0], 40, path)
        self.assertFalse(res["complete"])
        self.assertEqual(res["missing"], [5])
        self.assertEqual(res["perFrame"][5], [5, None, None, None])
        self.assertEqual(len(res["perFrame"]), N)
        self.assertEqual(res["meanPx"], 0.0)  # the mean alone would have passed

    def test_path_and_frame_counts_must_agree(self):
        path = plant_clip(self.tmp / "len")
        self.assertFalse(te.locate(str(self.tmp / "len"), [0, 255, 0], 40, path[:-2])["complete"])
        self.assertFalse(te.locate(str(self.tmp / "len"), [0, 255, 0], 40, path + [[0, 0]])["complete"])

    def test_empty_render_is_not_complete(self):
        (self.tmp / "empty").mkdir()
        res = te.locate(str(self.tmp / "empty"), [0, 255, 0], 40, [])
        self.assertFalse(res["complete"])
        self.assertIsNone(res["lastPx"])


if __name__ == "__main__":
    unittest.main()
