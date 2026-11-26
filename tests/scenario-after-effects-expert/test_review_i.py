"""Offline tests for the second review round, the Python tools.

- delivery_check.py: an image sequence with no key besides "file" fails, although its discovery adds a "gaps" row.
- matte_metrics.py: a command whose result carries "error" exits 1 and still prints the reason.
- seat_check.py: the object's height is read from the sampled columns, so a thin matte gives a verdict.
- vfx_measure.py: the hold verdict reads the unrounded motion, and the flash frames are read for clipping.

numpy and Pillow only (seat_check.py needs ImageMagick 7). Each case builds its frames in a temporary folder.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
DELIVERY = FAMILY / "scenario-after-effects-color-delivery" / "scripts"
MATTE = FAMILY / "scenario-after-effects-compositing" / "scripts" / "matte_metrics.py"
SEAT = FAMILY / "scenario-after-effects-generation" / "scripts" / "seat_check.py"
VFX = FAMILY / "scenario-after-effects-vfx" / "scripts"
for folder in (DELIVERY, VFX):
    sys.path.insert(0, str(folder))

import delivery_check  # noqa: E402
import vfx_measure as vm  # noqa: E402

HAS_MAGICK = shutil.which("magick") is not None
W, H = 1000, 700


def run(script, *args, timeout=120):
    p = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def save(path, a):
    Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)).save(path)
    return str(path)


def gray(level, w=W, h=H):
    return np.full((h, w, 3), float(level))


def noisy(seed, level=76, std=2.0, w=W, h=H):
    return gray(level, w, h) + np.random.default_rng(seed).normal(0, std, (h, w, 1))


def png_info():
    return {"streams": [{"codec_type": "video", "codec_name": "png", "width": 1920, "height": 1080, "pix_fmt": "rgba",
                         "avg_frame_rate": "25/1"}], "format": {}}


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


# ---------------------------------------------------------------- delivery_check


class SequenceRequirements(Temp):
    def check(self, **keys):
        for n in (0, 1):
            (self.tmp / ("shot_%05d.png" % n)).write_bytes(b"png")
        spec = dict({"file": str(self.tmp / "shot_%05d.png")}, **keys)
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=png_info()):
            return {r["check"]: r for r in delivery_check.check(spec)}

    def test_a_contiguous_sequence_with_no_requirement_fails(self):
        rows = self.check()
        self.assertTrue(rows["gaps"]["pass"])
        self.assertIn("requirements", rows)
        self.assertFalse(rows["requirements"]["pass"])

    def test_a_sequence_with_a_requested_property_is_accepted(self):
        rows = self.check(width=1920)
        self.assertNotIn("requirements", rows)
        self.assertTrue(all(r["pass"] for r in rows.values()), rows)

    def test_a_requested_first_number_counts_as_a_requirement(self):
        rows = self.check(sequence_start=0)
        self.assertNotIn("requirements", rows)
        self.assertTrue(rows["first number"]["pass"])


# ---------------------------------------------------------------- matte_metrics


class MatteMetricsExitCode(Temp):
    def test_light_without_an_opaque_subject_exits_1_and_prints_the_reason(self):
        fg = np.zeros((40, 60, 4), np.uint8)
        fg[..., :3] = 120
        fg[10:30, 20:40, 3] = 100   # alpha 0.39 at most: no pixel over 0.9
        Image.fromarray(fg, "RGBA").save(self.tmp / "fg.png")
        save(self.tmp / "bg.png", gray(90, 60, 40))
        rc, out, err = run(MATTE, "light", self.tmp / "fg.png", self.tmp / "bg.png")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("alpha over 0.9", json.loads(out)["error"])

    def test_a_measured_result_still_exits_0(self):
        a = save(self.tmp / "a.png", gray(90, 60, 40))
        rc, out, err = run(MATTE, "diff", a, a)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(json.loads(out)["mean"], 0.0)


# ---------------------------------------------------------------- seat_check


def matte(path, w, h, boxes):
    a = np.zeros((h, w, 4), np.uint8)
    for x0, y0, x1, y1 in boxes:
        a[y0:y1, x0:x1] = (200, 200, 200, 255)
    Image.fromarray(a, "RGBA").save(path)


@unittest.skipUnless(HAS_MAGICK, "ImageMagick 7 (magick) not installed")
class SeatContactThinMatte(Temp):
    def test_a_matte_whose_sampled_columns_sit_above_the_others_gives_a_verdict(self):
        # column 0 is low in the frame, columns 1 to 3 and 10 are high: the sampled columns (1, 5, 9) see only the high part
        matte(self.tmp / "obj.png", 12, 120, [(0, 90, 1, 100), (1, 10, 4, 20), (10, 10, 11, 20)])
        matte(self.tmp / "shadow.png", 12, 120, [(0, 20, 12, 24)])
        rc, out, err = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "shadow.png")
        self.assertNotIn("ZeroDivisionError", err)
        r = json.loads(out)
        self.assertEqual(r["objectBottom"], 19)
        self.assertEqual(r["restingColumns"], 1)
        self.assertEqual(rc, 0 if r["pass"] else 1)

    def test_a_rectangular_matte_reads_as_before(self):
        matte(self.tmp / "obj.png", 200, 200, [(60, 40, 140, 120)])
        matte(self.tmp / "touch.png", 200, 200, [(50, 120, 150, 130)])
        rc, out, err = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "touch.png")
        r = json.loads(out)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual((r["objectBottom"], r["coverage"], r["gapMax"]), (119, 1.0, 1))


# ---------------------------------------------------------------- vfx_measure gates


class Gates(Temp):
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

    def held(self, moved_pixels):
        """Two held frames: the second has `moved_pixels` pixels one level brighter (mean change = moved / (W * H) levels)."""
        a = gray(76)
        b = a.copy()
        b.reshape(-1, 3)[:moved_pixels] += 1
        return [save(self.tmp / "held_a.png", a), save(self.tmp / "held_b.png", b)]


class HoldVerdict(Gates):
    def test_the_base_manifest_passes(self):
        self.assertEqual(vm.gates(self.manifest())["fails"], [])

    def test_a_motion_just_over_the_limit_fails_although_it_rounds_to_the_limit(self):
        r = vm.gates(self.manifest(holdFrames=self.held(3780), holdCount=2))   # 0.0054 levels against 0.005
        self.assertIn("hold", r["fails"], r["hold"])
        self.assertGreater(r["hold"]["move"], vm.LIMITS["holdMove"])

    def test_a_motion_under_the_limit_passes(self):
        r = vm.gates(self.manifest(holdFrames=self.held(3400), holdCount=2))   # 0.0049 levels
        self.assertNotIn("hold", r["fails"], r["hold"])

    def test_identical_held_frames_pass(self):
        r = vm.gates(self.manifest(holdFrames=self.held(0), holdCount=2))
        self.assertEqual(r["hold"]["move"], 0)
        self.assertNotIn("hold", r["fails"])


class FlashFramesAreReadForClipping(Gates):
    def test_a_white_core_on_a_flash_only_frame_fails_clip(self):
        hot = gray(85)
        hot[340:360, 490:510] = 255   # 400 px at 255 in all three channels, on a frame that is in peaks and not in outs
        peak = save(self.tmp / "final_7.png", hot)
        r = vm.gates(self.manifest(peaks=[peak, str(self.tmp / "final_15.png")]))
        self.assertIn("final_7.png", r["clip"])
        self.assertGreater(r["clip"]["final_7.png"], 0)
        self.assertIn("clip", r["fails"])

    def test_a_frame_listed_in_both_is_read_once_and_clean_frames_pass(self):
        out0 = str(self.tmp / "final_0.png")
        r = vm.gates(self.manifest(peaks=[out0, save(self.tmp / "final_15.png", gray(85))]))
        self.assertEqual(sorted(r["clip"]), ["final_0.png", "final_15.png"])
        self.assertNotIn("clip", r["fails"])


if __name__ == "__main__":
    unittest.main()
