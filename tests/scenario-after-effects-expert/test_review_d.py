"""Review round on the effects pixel gates (vfx_measure.py), with no After Effects installed.

Each gate that has nothing to measure is inconclusive and fails; nothing falls back to a wider region or another tile set:
- flash refuses a non-finite or out-of-range limit before reading any frame;
- grain with no flat tile the effect leaves alone, blacks with an empty far region, contour with an empty band;
- wisp pairs frames by number and refuses lists that hold different frames;
- the clip gate reads the unrounded share (one clipped pixel in 2.4 Mpx fails even though it rounds to 0.0000 %);
- the manifest: pngScale other than 1 is refused, a manifest without the version 2 fields is still measured with notes,
  and the held frames of the camera comp fail the hold when they move.

numpy and Pillow only. Each case builds its frames in a temporary folder.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "after-effects" / "scenario-after-effects-vfx" / "scripts"
MEASURE = SCRIPTS / "vfx_measure.py"
sys.path.insert(0, str(SCRIPTS))

import vfx_measure as vm  # noqa: E402

W, H = 1000, 700


def save(path, a):
    Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)).save(path)
    return str(path)


def gray(level, w=W, h=H):
    return np.full((h, w, 3), float(level))


def noisy(seed, level=76, std=2.0, w=W, h=H):
    r = np.random.default_rng(seed).normal(0, std, (h, w, 1))
    return gray(level, w, h) + r


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def manifest(self, **over):
        """A version 2 manifest whose every gate passes: flat scene, disc matte, noisy plate, a 0.83 hit, a still hold."""
        t = self.tmp
        yy, xx = np.mgrid[0:H, 0:W]
        disc = (np.hypot(xx - 500, yy - 350) < 100)[..., None] * 255.0 * np.ones(3)
        plate = [save(t / "plate_a.png", noisy(1)), save(t / "plate_b.png", noisy(2))]
        M = {
            "version": 2, "origin": [0, 0], "at": 0.5, "fps": 30, "pngScale": 1,
            "scene": {"0": save(t / "scene_0.png", gray(76))}, "matte": {"0": save(t / "matte_0.png", disc)},
            "outs": [save(t / "final_0.png", gray(76))], "calm": str(t / "final_0.png"),
            "peaks": [save(t / "final_15.png", gray(85))], "peakTimes": [],
            "plate": plate, "hold": plate,
            "plateFrame": save(t / "plate_calm.png", noisy(3)), "calmScene": save(t / "scene_calm.png", noisy(3)),
            "holdFrames": [save(t / ("hold_%d.png" % i), noisy(4)) for i in range(3)], "holdCount": 3,
        }
        M.update(over)
        p = t / "manifest.json"
        p.write_text(json.dumps(M), encoding="utf-8")
        return str(p)


class FlashLimits(unittest.TestCase):
    def test_bad_limits_are_refused_before_any_frame_is_read(self):
        for h, r in ((0, 1.45), (-1, 1.45), (float("nan"), 1.45), (float("inf"), 1.45), (0.06, 1.0), (0.06, float("nan")), (0.06, 0.5)):
            with self.subTest(h=h, r=r), self.assertRaises(SystemExit) as cm:
                vm.flash("/no/such/calm.png", ["/no/such/peak.png"], h, r)
            self.assertIn("flash:", str(cm.exception))

    def test_command_line_refuses_a_zero_headroom(self):
        p = subprocess.run([sys.executable, str(MEASURE), "flash", "--calm", "a.png", "--peak", "b.png", "--max-headroom", "0"],
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("max headroom", p.stderr)


class Inconclusive(Temp):
    def test_grain_without_an_untouched_flat_tile_is_inconclusive(self):
        plate = [save(self.tmp / "p0.png", noisy(1)), save(self.tmp / "p1.png", noisy(2))]
        shot = [save(self.tmp / "s0.png", noisy(1) + 12), save(self.tmp / "s1.png", noisy(2) + 12)]   # the effect lifts every tile
        g = vm.grain(plate, shot)
        self.assertIn("inconclusive", g)
        self.assertEqual(g["tiles"], 0)

    def test_blacks_with_no_pixel_beyond_the_radius_is_inconclusive(self):
        a = save(self.tmp / "a.png", noisy(1, w=200, h=150))
        b = vm.blacks(a, a, [100, 75], beyond=900)
        self.assertIn("inconclusive", b)
        self.assertNotIn("change", b)

    def test_contour_with_an_empty_band_is_none(self):
        frame = save(self.tmp / "f.png", gray(76, 200, 150))
        matte = save(self.tmp / "m.png", gray(255, 200, 150))   # the matte covers the frame: no pixel outside it
        self.assertIsNone(vm.contour(frame, matte))

    def test_gates_fail_on_an_empty_contour_band(self):
        full = save(self.tmp / "full.png", gray(255))
        r = vm.gates(self.manifest(matte={"0": full}))
        self.assertTrue(any(f.startswith("contour 0 (inconclusive") for f in r["fails"]), r["fails"])

    def test_gates_fail_on_inconclusive_grain_and_blacks(self):
        lifted = [save(self.tmp / "l0.png", noisy(1) + 12), save(self.tmp / "l1.png", noisy(2) + 12)]
        small = save(self.tmp / "small.png", noisy(5, w=200, h=150))
        r = vm.gates(self.manifest(hold=lifted, plateFrame=small, calmScene=small))
        self.assertIn("grain (inconclusive)", r["fails"])
        self.assertIn("blacks (inconclusive)", r["fails"])


class Wisp(Temp):
    def frames(self, side, numbers, lift):
        out = []
        for n in numbers:
            a = gray(40, 200, 150)
            if lift:
                a[20:120, 80:120] += 30
            out.append(save(self.tmp / ("%s_f%03d.png" % (side, n)), a))
        return out

    def test_lists_with_different_frames_are_refused(self):
        with self.assertRaises(SystemExit) as cm:
            vm.wisp(self.frames("w", [10, 11], True), self.frames("o", [11, 12], False), [0, 0, 200, 150])
        self.assertIn("different frames", str(cm.exception))

    def test_a_frame_twice_is_refused(self):
        w = self.frames("w", [10], True)
        with self.assertRaises(SystemExit):
            vm.wisp(w + w, self.frames("o", [10, 10], False), [0, 0, 200, 150])

    def test_frames_are_paired_by_number_not_by_position(self):
        w = self.frames("w", [10, 40], True)
        o10 = save(self.tmp / "o_f010.png", gray(40, 200, 150))
        o40 = save(self.tmp / "o_f040.png", gray(70, 200, 150))   # paired with frame 10 by position, it would cancel the wisp
        r = vm.wisp(w, [o40, o10], [0, 0, 200, 150])
        self.assertEqual([x["frame"] for x in r["frames"]], [10, 40])
        self.assertGreaterEqual(r["frames"][0]["contrast"], 25)


class ClipUnrounded(Temp):
    def test_one_clipped_pixel_fails_although_it_rounds_to_zero(self):
        big = gray(76, 2000, 1200)
        big[600, 1000] = 255
        out = save(self.tmp / "final_big.png", big)
        self.assertGreater(vm.clip_share(vm.load(out)), 0)
        self.assertEqual(round(vm.clip_share(vm.load(out)) * 100, 4), 0.0)
        r = vm.gates(self.manifest(outs=[str(self.tmp / "final_0.png"), out]))
        self.assertIn("clip", r["fails"])
        self.assertEqual(r["clip"]["final_big.png"], 0.0)


class Manifest(Temp):
    def test_the_planted_manifest_passes(self):
        r = vm.gates(self.manifest())
        self.assertEqual(r["fails"], [], r)
        self.assertEqual(r["hold"]["move"], 0.0)
        self.assertNotIn("notes", r)

    def test_a_32_bpc_capture_is_refused(self):
        with self.assertRaises(SystemExit) as cm:
            vm.gates(self.manifest(pngScale=0.1))
        self.assertIn("pngScale", str(cm.exception))

    def test_a_manifest_before_version_2_is_measured_with_notes(self):
        p = Path(self.manifest())
        M = json.loads(p.read_text(encoding="utf-8"))
        for k in ("version", "pngScale", "holdFrames", "holdCount"):
            M.pop(k)
        p.write_text(json.dumps(M), encoding="utf-8")
        r = vm.gates(str(p))
        self.assertEqual(r["fails"], [])
        self.assertNotIn("hold", r)
        self.assertEqual(len(r["notes"]), 2)

    def test_a_camera_still_moving_in_the_hold_fails(self):
        moved = save(self.tmp / "hold_moved.png", np.roll(noisy(4), 3, axis=1))
        r = vm.gates(self.manifest(holdFrames=[str(self.tmp / "hold_0.png"), moved]))
        self.assertIn("hold", r["fails"])
        # a slow push creeping through the hold: one level on 2 % of the pixels, 0.02 level on average (0.021 was read live)
        creep = np.round(noisy(4))
        creep[:14, :] += 1
        crept = save(self.tmp / "hold_creep.png", creep)
        r = vm.gates(self.manifest(holdFrames=[save(self.tmp / "hold_still.png", np.round(noisy(4))), crept]))
        self.assertIn("hold", r["fails"])
        self.assertLess(r["hold"]["move"], 0.25)

    def test_fewer_held_frames_than_asked_is_inconclusive(self):
        r = vm.gates(self.manifest(holdFrames=[str(self.tmp / "hold_0.png")], holdCount=15))
        self.assertIn("hold (inconclusive)", r["fails"])


if __name__ == "__main__":
    unittest.main()
