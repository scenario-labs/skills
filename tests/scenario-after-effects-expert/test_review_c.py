"""Review round 1, group C: compositing and generation scripts fail closed and never wrap or overwrite.

integration_check.py: unknown --only names, empty selections, a matte that fills the frame, resting columns with no
shadow, the material gate without a neutral. matte_metrics.py: no neighborhood wraps across the frame edge, empty
plate selections. finish_putback.py: no write over an input or a file it did not write, size and emptiness checks.
seat_check.py: resting columns from the object matte, mattes of different sizes.

numpy and Pillow only (seat_check.py needs ImageMagick 7). Each case builds its frames in a temporary folder.
"""

import argparse
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
COMPOSITING = FAMILY / "scenario-after-effects-compositing" / "scripts"
GENERATION = FAMILY / "scenario-after-effects-generation" / "scripts"
INTEGRATION = COMPOSITING / "integration_check.py"
PUTBACK = GENERATION / "finish_putback.py"
SEAT = GENERATION / "seat_check.py"
for folder in (COMPOSITING, GENERATION):
    sys.path.insert(0, str(folder))

import finish_putback as fp  # noqa: E402
import integration_check as ic  # noqa: E402
import matte_metrics as mm  # noqa: E402

HAS_MAGICK = shutil.which("magick") is not None


def run(script, *args, timeout=120):
    p = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def save(path, a, mode=None):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), mode).save(path)
    return path


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


# ---------------------------------------------------------------- integration_check


def namespace(p, sc, out, **over):
    ns = argparse.Namespace(
        comp=p["comp"],
        plate=p["plate"],
        elem=p["elem"],
        matte=p["matte"],
        neutral=p["neutral"],
        shadow=p["shadow"],
        sun=sc["sun"],
        plate_shadow=sc["plate_shadow"],
        plate_lit=sc["plate_lit"],
        plate_length=sc["plate_length"],
        object_height=sc["object_height"],
        only=None,
        no_shadow=None,
        light="back",
        out=str(out),
        selftest=None,
        rendered=False,
        comp_rim=False,
        ground_shadow=None,
        ground_albedo=0.35,
    )
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def run_inproc(ns):
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = ic.run(ns)
    return rc, json.loads(buf.getvalue())


class IntegrationFailsClosed(Temp):
    def planted(self, variant="good", **arrays):
        sc = ic._scene(variant)
        sc.update(arrays)
        p = {}
        for k in ("comp", "plate", "elem", "neutral", "matte", "shadow"):
            p[k] = str(save(self.tmp / ("%s.png" % k), sc[k]))
        return sc, p

    def test_unknown_or_empty_only_exits_2_without_a_gate(self):
        sc, p = self.planted()
        for only in ("ligth", "light,shdae", ",", ""):
            with self.subTest(only=only):
                rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json", only=only))
                self.assertEqual(rc, 2, r)
                self.assertEqual(r["verdict"], "incomplete")
                self.assertIn("error", r)
                self.assertNotIn("gates", r)

    def test_unknown_only_on_the_command_line_exits_2(self):
        sc, p = self.planted()
        rc, out, err = run(
            INTEGRATION, "--comp", p["comp"], "--elem", p["elem"], "--matte", p["matte"], "--neutral", p["neutral"],
            "--sun=" + sc["sun"], "--only", "ligth",
        )  # fmt: skip
        self.assertEqual(rc, 2, out + err)
        self.assertNotEqual(json.loads(out)["verdict"], "pass")

    def test_light_shade_selection_still_returns_the_rim(self):
        sc, p = self.planted()
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json", only="light,shade"))
        self.assertEqual(rc, 0, r["failed"])
        self.assertEqual(sorted(r["gates"]), ["light", "rim", "shade"])

    def test_material_selected_without_a_neutral_is_skipped_not_passed(self):
        sc, p = self.planted()
        p["neutral"] = None
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json", only="material"))
        self.assertEqual(rc, 2, r)
        self.assertEqual(r["skipped"], ["material"])
        self.assertEqual(r["verdict"], "incomplete")

    def test_every_gate_is_reported_without_a_neutral(self):
        sc, p = self.planted()
        p["neutral"] = None
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json"))
        self.assertIn("material", r["skipped"])
        self.assertEqual(sorted(r["gates"]), sorted(ic.GATES))
        self.assertNotEqual(rc, 0)

    def test_empty_matte_exits_2_with_an_error(self):
        sc, p = self.planted(matte=np.zeros((540, 960), np.float32))
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json"))
        self.assertEqual(rc, 2, r)
        self.assertIn("error", r)

    def test_a_matte_too_small_for_a_core_skips_instead_of_raising(self):
        m = np.zeros((540, 960), np.float32)
        m[300:306, 400:406] = 1.0
        sc, p = self.planted(matte=m)
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json"))
        for name in ("light", "shade", "rim", "finish", "material"):
            self.assertIsNone(r["gates"][name]["pass"], name)
            self.assertIn("skipped", r["gates"][name], name)
        self.assertNotEqual(rc, 0)

    def test_a_matte_that_fills_the_frame_ends_and_does_not_pass_light(self):
        h, w = 120, 160
        yy, xx = np.mgrid[:h, :w]
        lit = np.repeat((0.3 + 0.5 * xx / w)[..., None], 3, -1)
        for k, a in (("elem", lit), ("comp", lit), ("neutral", np.full((h, w, 3), 0.6)), ("matte", np.ones((h, w)))):
            save(self.tmp / (k + ".png"), a)
        rc, out, err = run(
            INTEGRATION, "--comp", self.tmp / "comp.png", "--elem", self.tmp / "elem.png", "--matte", self.tmp / "matte.png",
            "--neutral", self.tmp / "neutral.png", "--sun", "400,-200", "--only", "light", timeout=60,
        )  # fmt: skip
        r = json.loads(out)
        self.assertNotEqual(rc, 0, out + err)
        self.assertNotEqual(r["verdict"], "pass")
        self.assertIsNone(r["gates"]["light"]["pass"])
        self.assertIn("fills the frame", r["gates"]["light"]["skipped"])

    def test_shadow_under_part_of_the_footprint_fails_contact(self):
        sc = ic._scene("good")
        good_s = sc["shadow"]
        # the planted shadow removed under the left half of the resting footprint (and everywhere left of it)
        cut = good_s.copy()
        cut[380:, :425] = 0
        _, p = self.planted(shadow=cut)
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json", only="contact"))
        c = r["gates"]["contact"]
        self.assertFalse(c["pass"], c)
        self.assertLess(c["coverage"], ic.LIMITS["contactCoverage"])
        self.assertLessEqual(c["value"], ic.LIMITS["gap"])  # the covered columns alone would pass
        self.assertEqual(rc, 1)

    def test_reference_scene_passes_contact_with_its_coverage_reported(self):
        sc, p = self.planted()
        rc, r = run_inproc(namespace(p, sc, self.tmp / "r.json", only="contact"))
        c = r["gates"]["contact"]
        self.assertTrue(c["pass"], c)
        self.assertGreaterEqual(c["coverage"], ic.LIMITS["contactCoverage"])
        self.assertLessEqual(c["columns"], c["restingColumns"])
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------- matte_metrics


class MatteMetricsNoWrap(Temp):
    def test_dilation_does_not_reach_the_opposite_edge(self):
        m = np.zeros((20, 30), bool)
        m[0, 0] = True
        d = mm.shift_or(m, 2)
        self.assertTrue(d[2, 2])
        self.assertFalse(d[-1].any())
        self.assertFalse(d[:, -1].any())

    def test_erosion_keeps_a_subject_cut_by_the_frame_edge(self):
        m = np.ones((20, 30), bool)
        m[:, 0] = False
        e = mm.erode(m, 1)
        self.assertTrue(e[:, -1].all())  # the right frame edge is not an outline
        self.assertFalse(e[:, 1].any())  # one px from the real outline at column 0

    def test_depth_counts_from_the_outline_not_from_the_frame_edge(self):
        m = np.zeros((40, 30), bool)
        m[20:] = True
        d = mm.depth_in(m, 5)
        self.assertEqual(d[-1, 15], 5)
        self.assertEqual(d[20, 15], 0)
        self.assertEqual(d[21, 15], 1)

    def test_local_mean_reads_nothing_from_the_opposite_edge(self):
        v = np.zeros((20, 30), np.float32)
        v[:, :2] = 1.0
        out = mm.local_mean(v, np.ones((20, 30), bool), 3)
        np.testing.assert_allclose(out[:, -1], 0.0)
        self.assertGreater(out[10, 0], 0.0)

    def test_light_reports_unavailable_plate_levels_and_keeps_the_subject(self):
        h, w = 80, 120
        fg = np.zeros((h, w, 4))
        fg[20:60, 40:80] = [0.5, 0.4, 0.3, 1.0]
        save(self.tmp / "fg.png", fg, "RGBA")
        save(self.tmp / "bg.png", np.ones((h, w, 3)))
        res = mm.cmd_light(argparse.Namespace(fg=str(self.tmp / "fg.png"), bg=str(self.tmp / "bg.png"), alpha=None, ring=3))
        self.assertIsNone(res["plate_near_luma_p1_p99"])
        self.assertIsNone(res["plate_luma_p1_p99"])
        self.assertEqual(len(res["subject_luma_p1_p99"]), 2)
        json.dumps(res)

    def test_light_on_an_empty_subject_returns_an_error(self):
        save(self.tmp / "fg.png", np.zeros((40, 40, 4)), "RGBA")
        save(self.tmp / "bg.png", np.full((40, 40, 3), 0.5))
        res = mm.cmd_light(argparse.Namespace(fg=str(self.tmp / "fg.png"), bg=str(self.tmp / "bg.png"), alpha=None, ring=3))
        self.assertIn("error", res)


# ---------------------------------------------------------------- finish_putback


def call(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fp.main(argv)
    text = buf.getvalue().strip()
    return rc, (json.loads(text) if text.startswith("{") else None)


class PutbackNeverOverwrites(Temp):
    H, W = 120, 200

    def frames(self):
        yy, xx = np.mgrid[: self.H, : self.W]
        ell = ((xx - 100) / 40.0) ** 2 + ((yy - 60) / 20.0) ** 2 <= 1
        comp = np.full((self.H, self.W, 3), 0.5)
        comp[ell] = 0.3
        elem = np.zeros((self.H, self.W, 4))
        elem[ell] = [0.3, 0.3, 0.3, 1]
        guide = save(self.tmp / "comp.png", comp)
        el = save(self.tmp / "elem.png", elem, "RGBA")
        return ell, comp, guide, el

    def test_mask_refuses_a_file_it_did_not_write_unless_replace(self):
        _, _, guide, el = self.frames()
        out = self.tmp / "m"
        out.mkdir()
        (out / "guide.png").write_bytes(b"user file")
        with self.assertRaises(SystemExit) as cm:
            call(["mask", str(guide), str(el), str(out)])
        self.assertIn("--replace", str(cm.exception))
        self.assertEqual((out / "guide.png").read_bytes(), b"user file")
        self.assertFalse((out / "region.png").exists())  # nothing written before the check
        rc, res = call(["mask", str(guide), str(el), str(out), "--replace"])
        self.assertEqual(rc, 0)
        self.assertNotEqual((out / "guide.png").read_bytes(), b"user file")

    def test_mask_rewrites_its_own_outputs(self):
        _, _, guide, el = self.frames()
        out = self.tmp / "m"
        for _ in range(2):
            rc, _ = call(["mask", str(guide), str(el), str(out)])
            self.assertEqual(rc, 0)

    def test_mask_refuses_to_write_over_its_input(self):
        _, comp, _, el = self.frames()
        guide = save(self.tmp / "guide.png", comp)
        before = guide.read_bytes()
        for flags in ([], ["--replace"]):
            with self.subTest(flags=flags), self.assertRaises(SystemExit) as cm:
                call(["mask", str(guide), str(el), str(self.tmp), *flags])
            self.assertIn("is the input", str(cm.exception))
        self.assertEqual(guide.read_bytes(), before)

    def test_mask_with_no_element_writes_nothing(self):
        _, comp, guide, _ = self.frames()
        el = save(self.tmp / "empty.png", np.zeros((self.H, self.W, 4)), "RGBA")
        rc, res = call(["mask", str(guide), str(el), str(self.tmp / "m")])
        self.assertEqual((rc, res["elementPx"]), (1, 0))
        self.assertIn("error", res)
        self.assertFalse((self.tmp / "m").exists())

    def mask(self):
        ell, comp, guide, el = self.frames()
        rc, _ = call(["mask", str(guide), str(el), str(self.tmp / "m")])
        self.assertEqual(rc, 0)
        return ell, comp, guide

    def test_putback_refuses_an_output_that_is_an_input(self):
        _, comp, guide = self.mask()
        fin = save(self.tmp / "fin.png", comp)
        before = guide.read_bytes()
        with self.assertRaises(SystemExit) as cm:
            call(["putback", str(guide), str(fin), str(self.tmp / "m" / "region.png"), str(guide), "--replace"])
        self.assertIn("is the input", str(cm.exception))
        self.assertEqual(guide.read_bytes(), before)

    def test_putback_refuses_an_existing_user_file(self):
        _, comp, guide = self.mask()
        fin = save(self.tmp / "fin.png", comp)
        (self.tmp / "out.png").write_bytes(b"keep me")
        with self.assertRaises(SystemExit):
            call(["putback", str(guide), str(fin), str(self.tmp / "m" / "region.png"), str(self.tmp / "out.png")])
        self.assertEqual((self.tmp / "out.png").read_bytes(), b"keep me")

    def test_putback_refuses_a_finished_frame_smaller_than_the_composite(self):
        _, comp, guide = self.mask()
        fin = save(self.tmp / "fin.png", comp[:100, :150])
        with self.assertRaises(SystemExit) as cm:
            call(["putback", str(guide), str(fin), str(self.tmp / "m" / "region.png"), str(self.tmp / "out.png")])
        self.assertIn("smaller than COMP", str(cm.exception))
        self.assertFalse((self.tmp / "out.png").exists())

    def test_putback_accepts_a_padded_finished_frame(self):
        _, comp, guide = self.mask()
        pad = np.zeros((128, 208, 3))
        pad[: self.H, : self.W] = comp
        fin = save(self.tmp / "fin.png", pad)
        rc, res = call(["putback", str(guide), str(fin), str(self.tmp / "m" / "region.png"), str(self.tmp / "out.png")])
        self.assertEqual(rc, 0)
        self.assertTrue(res["pass"])

    def test_putback_with_an_empty_region_fails_and_writes_nothing(self):
        _, comp, guide = self.mask()
        fin = save(self.tmp / "fin.png", comp)
        region = save(self.tmp / "region0.png", np.zeros((self.H, self.W)))
        rc, res = call(["putback", str(guide), str(fin), str(region), str(self.tmp / "out.png")])
        self.assertEqual(rc, 1)
        self.assertFalse(res["pass"])
        self.assertFalse((self.tmp / "out.png").exists())

    def test_command_line_documents_replace(self):
        rc, out, _ = run(PUTBACK, "mask", "--help")
        self.assertEqual(rc, 0)
        self.assertIn("--replace", out)


# ---------------------------------------------------------------- seat_check


def rgba(path, w, h, box):
    a = np.zeros((h, w, 4), np.uint8)
    x0, y0, x1, y1 = box
    a[y0:y1, x0:x1] = (200, 200, 200, 255)
    Image.fromarray(a, "RGBA").save(path)


@unittest.skipUnless(HAS_MAGICK, "ImageMagick 7 (magick) not installed")
class SeatContactCoverage(Temp):
    def test_shadow_under_part_of_the_resting_columns_fails(self):
        rgba(self.tmp / "obj.png", 200, 200, (60, 40, 140, 120))
        rgba(self.tmp / "half.png", 200, 200, (50, 120, 100, 130))  # touches, but only under the left part
        rc, out, err = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "half.png")
        r = json.loads(out)
        self.assertEqual(rc, 1, out + err)
        self.assertLess(r["coverage"], 0.9)
        self.assertLessEqual(r["gapMax"], 2)  # the covered columns alone would pass

    def test_full_shadow_passes_with_full_coverage(self):
        rgba(self.tmp / "obj.png", 200, 200, (60, 40, 140, 120))
        rgba(self.tmp / "touch.png", 200, 200, (50, 120, 150, 130))
        rc, out, err = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "touch.png")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(json.loads(out)["coverage"], 1.0)

    def test_mattes_of_different_sizes_fail(self):
        rgba(self.tmp / "obj.png", 200, 200, (60, 40, 140, 120))
        rgba(self.tmp / "small.png", 100, 200, (0, 120, 100, 130))
        rc, out, _ = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "small.png")
        r = json.loads(out)
        self.assertEqual(rc, 1)
        self.assertFalse(r["pass"])
        self.assertIn("100x200", r["error"])

    def test_empty_object_matte_fails(self):
        rgba(self.tmp / "obj.png", 200, 200, (0, 0, 0, 0))
        rgba(self.tmp / "touch.png", 200, 200, (50, 120, 150, 130))
        rc, out, _ = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "touch.png")
        self.assertEqual(rc, 1)
        self.assertIn("empty", json.loads(out)["error"])


if __name__ == "__main__":
    unittest.main()
