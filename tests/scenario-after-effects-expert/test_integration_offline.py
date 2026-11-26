"""Runs the integration, put-back, environment and GLB tint tools on synthetic inputs, with no After Effects installed.

- integration_check.py: the script's own planted scene (a sphere on a textured ground, sun low on the left) passes every
  gate; each planted defect fails the gate it is named for and no other; a few physical back-light renders pass the light
  gate and the same renders mirrored or flipped fail it; the command line writes the JSON and returns 0, 1 or 2.
  The script's --selftest (85 s, the full reference grid) is not run here.
- finish_putback.py: the edit mask pads to the step and opens a region that grows with --dilate; the put-back keeps the
  composite outside the region and brings the finished pixels inside; the IoU readings; the selftest.
- env_from_plate.py: size and format of the map, the peak it prints, the floor light hue against --sky-target, the sun clamp.
- glb_material.py tint and linear-store (and normal-flatten) on a minimal GLB with embedded PNG textures.

numpy and Pillow only. Each case builds its frames in a temporary folder.
"""

import argparse
import contextlib
import io
import json
import struct
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
ENV = FAMILY / "scenario-after-effects-3d" / "scripts" / "env_from_plate.py"
GLB = FAMILY / "scenario-after-effects-3d" / "scripts" / "glb_material.py"
for folder in (COMPOSITING, GENERATION):
    sys.path.insert(0, str(folder))

import finish_putback as fp  # noqa: E402
import integration_check as ic  # noqa: E402


def run(script, *args):
    p = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


# ---------------------------------------------------------------- integration_check

_SHARED = tempfile.TemporaryDirectory()
_CACHE = {}


def tearDownModule():
    # a cleanup registered at import time runs after the first module of a whole-folder run, not after this one
    _SHARED.cleanup()


def save_png(path, a):
    ic._save(str(path), a)


def planted_paths(variant, folder):
    """Writes the planted scene's frames for a variant and returns (scene, {name: path})."""
    sc = ic._scene(variant)
    paths = {}
    for k in ("comp", "plate", "elem", "neutral", "matte", "shadow"):
        paths[k] = str(Path(folder) / ("%s_%s.png" % (variant, k)))
        save_png(paths[k], sc[k])
    return sc, paths


def run_inproc(ns):
    """ic.run with its JSON line swallowed; returns (exit code, result read back from --out)."""
    with contextlib.redirect_stdout(io.StringIO()):
        rc = ic.run(ns)
    with open(ns.out) as f:
        return rc, json.load(f)


def planted(variant, rendered=False, comp_rim=False):
    """Every gate of the script on one planted variant, cached: the frames and the run take about a second."""
    key = (variant, rendered, comp_rim)
    if key not in _CACHE:
        sc, p = planted_paths(variant, _SHARED.name)
        tag = "%s_%s_%s" % key
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
            out=str(Path(_SHARED.name) / (tag + ".json")),
            selftest=None,
            rendered=rendered,
            comp_rim=comp_rim,
            ground_shadow=None,
            ground_albedo=0.35,
        )
        _CACHE[key] = run_inproc(ns)
    return _CACHE[key]


GATES = ("light", "shade", "rim", "density", "hue", "length", "softness", "contact", "finish", "material")


class IntegrationGates(unittest.TestCase):
    def test_good_scene_passes_every_gate(self):
        rc, r = planted("good")
        self.assertEqual(rc, 0, r["failed"])
        self.assertEqual(r["failed"], [])
        self.assertEqual(r.get("skipped", []), [])
        self.assertEqual(sorted(r["gates"]), sorted(GATES))
        for name, g in r["gates"].items():
            self.assertTrue(g["pass"], (name, g))

    def test_good_scene_values_sit_inside_the_documented_limits(self):
        _, r = planted("good")
        g = r["gates"]
        self.assertLessEqual(g["shade"]["value"], ic.LIMITS["shade"])
        self.assertLessEqual(g["density"]["value"], ic.LIMITS["density"])
        self.assertGreaterEqual(g["softness"]["value"], ic.LIMITS["softness"])
        self.assertLessEqual(g["material"]["value"], ic.LIMITS["material"])
        self.assertGreaterEqual(g["rim"]["value"], ic.LIMITS["rim"])

    def test_front_lit_element_fails_light_shade_and_rim(self):
        rc, r = planted("frontlit")
        self.assertEqual(rc, 1)
        self.assertEqual(sorted(r["failed"]), ["light", "rim", "shade"])
        self.assertGreater(r["gates"]["shade"]["value"], ic.LIMITS["shade"])

    def test_pale_shadow_fails_density_only(self):
        rc, r = planted("pale")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["density"])
        # the shadow is lighter than the plate's own (gap beyond the limit)
        self.assertGreater(r["gates"]["density"]["value"], ic.LIMITS["density"])

    def test_crushed_blacks_fail_finish_only(self):
        rc, r = planted("crushed")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["finish"])

    def test_neutral_shadow_hue_fails_hue_only(self):
        rc, r = planted("neutralhue")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["hue"])

    def test_short_shadow_fails_length_only(self):
        rc, r = planted("short")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["length"])

    def test_uniform_penumbra_fails_softness_only(self):
        rc, r = planted("uniform")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["softness"])
        self.assertLess(r["gates"]["softness"]["value"], ic.LIMITS["softness"])

    def test_wide_contact_shadow_fails_contact_only(self):
        rc, r = planted("wide")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["contact"])

    def test_off_color_material_fails_material_only(self):
        rc, r = planted("offcolor")
        self.assertEqual(rc, 1)
        self.assertEqual(r["failed"], ["material"])
        self.assertGreater(r["gates"]["material"]["value"], ic.LIMITS["material"])

    def test_hard_outline_fails_rim_on_a_keyed_relight_and_is_read_when_rendered(self):
        rc, r = planted("stroke")
        self.assertEqual(r["failed"], ["rim"])
        self.assertEqual(rc, 1)
        # a 3D render is read, not gated, on the rim (the selftest's own expectation)
        rc, r = planted("stroke", rendered=True)
        self.assertEqual(r["failed"], [])
        self.assertEqual(rc, 0)
        # the comp-rim flag says a rim layer was added over the render: its hardness is gated again
        rc, r = planted("stroke", rendered=True, comp_rim=True)
        self.assertEqual(r["failed"], ["rim"])
        self.assertEqual(rc, 1)

    def test_no_shadow_marks_the_shadow_gates_na_and_not_skipped(self):
        sc, p = planted_paths("good", _SHARED.name)
        ns = argparse.Namespace(
            comp=p["comp"],
            plate=p["plate"],
            elem=p["elem"],
            matte=p["matte"],
            neutral=p["neutral"],
            shadow=None,
            sun=sc["sun"],
            plate_shadow=None,
            plate_lit=None,
            plate_length=None,
            object_height=None,
            only=None,
            no_shadow="held in the air",
            light="back",
            out=str(Path(_SHARED.name) / "noshadow.json"),
            selftest=None,
            rendered=False,
            comp_rim=False,
            ground_shadow=None,
            ground_albedo=0.35,
        )
        rc, r = run_inproc(ns)
        self.assertEqual(r["failed"], [])
        self.assertEqual(r.get("skipped", []), [])
        self.assertEqual(rc, 0)
        for name in ("density", "hue", "length", "softness", "contact"):
            self.assertEqual(r["gates"][name].get("na"), "held in the air", name)
            self.assertIsNone(r["gates"][name].get("pass"), name)


def physical_light(tag, el, ne, mt, sdir):
    """The light gate on a physical render, the way the script's selftest calls it."""
    folder = Path(_SHARED.name)
    for k, im in (("elem", el), ("neutral", ne), ("matte", mt)):
        save_png(folder / ("%s_%s.png" % (tag, k)), im)
    ys, xs = np.nonzero(mt > 0.5)
    sn = np.array(sdir) / (np.hypot(*sdir) + 1e-9)
    ns = argparse.Namespace(
        comp=str(folder / (tag + "_elem.png")),
        plate=None,
        elem=str(folder / (tag + "_elem.png")),
        matte=str(folder / (tag + "_matte.png")),
        neutral=str(folder / (tag + "_neutral.png")),
        shadow=None,
        sun="%.1f,%.1f" % (xs.mean() + 3000 * sn[0], ys.mean() + 3000 * sn[1]),
        plate_shadow=None,
        plate_lit=None,
        plate_length=None,
        object_height=None,
        only="light",
        no_shadow=None,
        light="back",
        out=str(folder / (tag + ".json")),
        selftest=None,
        rendered=True,
        comp_rim=False,
        ground_shadow=None,
        ground_albedo=0.35,
    )
    return run_inproc(ns)[1]["gates"]["light"]


class IntegrationPhysical(unittest.TestCase):
    CASES = (
        ("sphere", 70, -135, 0.5, 0),
        ("sphere", 40, -90, 0.2, 0),
        ("capsule", 20, -135, 1.0, 45),
        ("capsule", 70, -45, 0.5, 80),
    )

    def test_back_light_references_pass_the_light_gate(self):
        for shape, theta, phi, sky, yaw in self.CASES:
            with self.subTest(shape=shape, theta=theta, phi=phi, sky=sky, yaw=yaw):
                sc = ic._physical(shape, theta, phi, sky, 7, yaw)
                self.assertIsNotNone(sc)
                lg = physical_light("phys_%s%d_%d_%d" % (shape, yaw, theta, phi), *sc)
                self.assertTrue(lg["pass"], lg)

    def test_mirrored_source_fails_the_light_gate(self):
        el, ne, mt, (sx, sy) = ic._physical("sphere", 70, -135, 0.5, 7, 0)
        good = physical_light("mirror_ref", el, ne, mt, (sx, sy))
        self.assertTrue(good["pass"], good)
        wrong = physical_light("mirror_wrong", el, ne, mt, (-sx, sy))
        self.assertFalse(wrong["pass"], wrong)
        self.assertGreater(wrong["value"], good["value"])

    def test_flipped_render_fails_the_light_gate(self):
        el, ne, mt, (sx, sy) = ic._physical("capsule", 70, -135, 0.5, 7, 45)
        wrong = physical_light("flip_wrong", el[::-1], ne[::-1], mt[::-1], (sx, sy))
        self.assertFalse(wrong["pass"], wrong)

    def test_a_sun_below_the_horizon_has_no_reference(self):
        self.assertIsNone(ic._physical("sphere", 70, 90, 0.5, 7, 0))


class IntegrationCli(Temp):
    def args(self, p, sc, *extra):
        return [
            "--comp", p["comp"], "--plate", p["plate"], "--elem", p["elem"], "--matte", p["matte"],
            # "--sun", "-80,170" as two arguments: the script joins them, since argparse on Python 3.12 reads a
            # value that starts with a minus sign as a flag
            "--neutral", p["neutral"], "--shadow", p["shadow"], "--sun", sc["sun"],
            "--plate-shadow", sc["plate_shadow"], "--plate-lit", sc["plate_lit"],
            "--plate-length", sc["plate_length"], "--object-height", sc["object_height"],
            *extra,
        ]  # fmt: skip

    def test_good_frames_exit_0_and_write_the_json(self):
        sc, p = planted_paths("good", self.tmp)
        out = self.tmp / "result.json"
        rc, stdout, err = run(INTEGRATION, *self.args(p, sc, "--out", out))
        self.assertEqual(rc, 0, stdout + err)
        printed = json.loads(stdout)
        self.assertIsInstance(printed["gates"], dict)
        self.assertEqual(sorted(printed["gates"]), sorted(GATES))
        self.assertEqual(printed["failed"], [])
        self.assertEqual(json.loads(out.read_text()), printed)

    def test_a_planted_defect_exits_1_and_names_the_gate(self):
        sc, p = planted_paths("pale", self.tmp)
        rc, stdout, err = run(INTEGRATION, *self.args(p, sc))
        self.assertEqual(rc, 1, err)
        r = json.loads(stdout)
        self.assertEqual(r["failed"], ["density"])
        self.assertFalse(r["gates"]["density"]["pass"])

    def test_missing_inputs_skip_gates_and_exit_2(self):
        sc, p = planted_paths("good", self.tmp)
        rc, stdout, err = run(
            INTEGRATION, "--comp", p["comp"], "--elem", p["elem"], "--matte", p["matte"], "--neutral", p["neutral"],
            "--sun=" + sc["sun"],
        )  # fmt: skip
        self.assertEqual(rc, 2, err)
        r = json.loads(stdout)
        self.assertEqual(r["failed"], [])
        self.assertIn("density", r["skipped"])
        self.assertIn("length", r["skipped"])

    def test_only_runs_the_named_gates(self):
        sc, p = planted_paths("good", self.tmp)
        rc, stdout, err = run(INTEGRATION, *self.args(p, sc, "--only", "light,shade"))
        self.assertEqual(rc, 0, err)
        gates = set(json.loads(stdout)["gates"])
        self.assertLessEqual({"light", "shade"}, gates)
        self.assertFalse(gates & {"density", "hue", "length", "softness", "contact", "finish", "material"}, gates)

    def test_comp_is_required(self):
        rc, _, err = run(INTEGRATION, "--elem", "x.png")
        self.assertEqual(rc, 2)
        self.assertIn("--comp is required", err)


# ---------------------------------------------------------------- finish_putback


def call(argv):
    """fp.main with its printed JSON line captured: (exit code, parsed JSON or None)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fp.main(argv)
    text = buf.getvalue().strip()
    return rc, (json.loads(text) if text.startswith("{") else None)


class FinishPutback(Temp):
    H, W = 120, 200

    def frames(self):
        """A gray plate with an ellipse element; returns the arrays."""
        h, w = self.H, self.W
        yy, xx = np.mgrid[:h, :w]
        ell = ((xx - 100) / 40.0) ** 2 + ((yy - 60) / 20.0) ** 2 <= 1
        comp = np.full((h, w, 3), 0.5)
        comp[ell] = 0.3
        elem = np.zeros((h, w, 4))
        elem[ell] = [0.3, 0.3, 0.3, 1]
        return ell, comp, elem

    def write(self, name, a, mode=None):
        path = self.tmp / name
        Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), mode).save(path)
        return path

    def make_mask(self, out, *extra):
        ell, comp, elem = self.frames()
        guide = self.write("comp.png", comp)
        el = self.write("elem.png", elem, "RGBA")
        rc, res = call(["mask", str(guide), str(el), str(out), *map(str, extra)])
        self.assertEqual(rc, 0)
        return ell, res

    def test_mask_pads_to_the_step_and_cuts_the_region(self):
        out = self.tmp / "m"
        ell, res = self.make_mask(out, "--dilate", 6, "--blur", 1, "--threshold", 0.04, "--step", 16)
        self.assertEqual(res["size"], [208, 128])
        with Image.open(out / "guide.png") as g, Image.open(out / "mask.png") as m:
            self.assertEqual(g.size, (208, 128))
            self.assertEqual(m.size, (208, 128))
            self.assertEqual(m.mode, "RGBA")
            alpha = np.asarray(m.getchannel("A"))
            guide = np.asarray(g.convert("RGB")).astype(float) / 255
        self.assertEqual(alpha[60, 100], 0)  # inside the element
        self.assertEqual(alpha[60, 100 + 40 + 4], 0)  # 4 px out, inside the 6 px dilation
        self.assertEqual(alpha[60, 100 + 40 + 12], 255)  # beyond it
        self.assertEqual(alpha[5, 5], 255)
        self.assertEqual(alpha[125, 205], 255)  # the padding is outside the region
        # the pad repeats the last column and the last row
        np.testing.assert_allclose(guide[:, 205], guide[:, 199], atol=1 / 255)
        np.testing.assert_allclose(guide[125, :200], guide[119, :200], atol=1 / 255)
        self.assertEqual(res["elementPx"], int(ell.sum()))

    def test_mask_padding_is_a_multiple_of_the_step(self):
        for step in (8, 32):
            with self.subTest(step=step):
                _, res = self.make_mask(self.tmp / ("s%d" % step), "--step", step)
                self.assertEqual(res["size"][0] % step, 0)
                self.assertEqual(res["size"][1] % step, 0)
                self.assertEqual(res["size"], [-(-self.W // step) * step, -(-self.H // step) * step])

    def test_region_grows_with_dilate(self):
        sizes = []
        for px in (0, 4, 12):
            _, res = self.make_mask(self.tmp / ("d%d" % px), "--dilate", px, "--blur", 0)
            sizes.append(res["regionPx"])
        self.assertEqual(sizes[0], int(self.frames()[0].sum()))
        self.assertLess(sizes[0], sizes[1])
        self.assertLess(sizes[1], sizes[2])

    def test_dilate_follows_a_disk_of_that_radius(self):
        m = np.zeros((61, 61), bool)
        m[30, 30] = True
        d = fp.dilate(m, 10)
        ys, xs = np.nonzero(d)
        dist = np.hypot(ys - 30, xs - 30)
        # an octagon of radius 10 along the axes: the corners reach 11.18 (12 % past a disk, the docstring says 8 %)
        self.assertLessEqual(dist.max(), 10 * 1.13)
        self.assertGreaterEqual(dist.max(), 10.0)
        self.assertTrue(d[30, 40] and d[40, 30] and not d[30, 41] and not d[41, 30])
        self.assertEqual((ys.max() - ys.min(), xs.max() - xs.min()), (20, 20))

    def test_threshold_decides_which_alpha_is_the_element(self):
        ell, comp, elem = self.frames()
        elem[..., 3] *= 0.3
        guide = self.write("comp.png", comp)
        el = self.write("elem.png", elem, "RGBA")
        rc, res = call(["mask", str(guide), str(el), str(self.tmp / "t1"), "--threshold", "0.5"])
        self.assertEqual((rc, res["elementPx"]), (1, 0))
        rc, res = call(["mask", str(guide), str(el), str(self.tmp / "t2"), "--threshold", "0.2"])
        self.assertEqual(res["elementPx"], int(ell.sum()))

    def test_mask_refuses_a_guide_and_element_of_different_sizes(self):
        _, comp, elem = self.frames()
        guide = self.write("comp.png", comp[:100])
        el = self.write("elem.png", elem, "RGBA")
        with self.assertRaises(SystemExit) as cm:
            call(["mask", str(guide), str(el), str(self.tmp / "o")])
        self.assertIn("differ in size", str(cm.exception))

    def putback(self, feather=2, shift=0.02, **extra):
        ell, comp, elem = self.frames()
        out = self.tmp / "m"
        self.make_mask(out, "--dilate", 6, "--blur", 1, "--threshold", 0.04)
        fin = comp + shift
        fin[ell] = [0.8, 0.2, 0.1]
        pad = np.zeros((128, 208, 3))
        pad[: self.H, : self.W] = fin
        paths = {"fin": self.write("fin.png", pad)}
        argv = [
            "putback",
            str(self.tmp / "comp.png"),
            str(paths["fin"]),
            str(out / "region.png"),
            str(self.tmp / "out.png"),
        ]
        argv += ["--feather", str(feather)]
        if "matte" in extra:
            paths["fm"] = self.write("fm.png", extra["matte"])
            argv += ["--elem", str(self.tmp / "elem.png"), "--finish-matte", str(paths["fm"])]
        rc, res = call(argv)
        with Image.open(self.tmp / "out.png") as im:
            o = np.asarray(im.convert("RGB")).astype(float) / 255
        return rc, res, o, ell, comp

    def test_putback_keeps_the_composite_outside_and_the_finish_inside(self):
        rc, res, o, ell, comp = self.putback()
        self.assertEqual(rc, 0)
        self.assertTrue(res["pass"])
        self.assertEqual(res["outsideDiff"], 0)
        self.assertLess(res["outsideDiff"], res["outsideLimit"])
        # the model redrew the plate by 0.02: read, not carried over
        self.assertAlmostEqual(res["finishOutsideDiff"], 0.02, delta=0.002)
        # outside the dilated region the output is the composite, to the byte
        far = np.zeros(ell.shape, bool)
        far[:, :40] = True
        far[:10, :] = True
        np.testing.assert_allclose(o[far], comp[far], atol=1 / 255)
        # inside, the finished pixels
        np.testing.assert_allclose(o[60, 100], [0.8, 0.2, 0.1], atol=0.01)
        self.assertGreater(np.abs(o[60, 100] - comp[60, 100]).max(), 0.3)

    def test_putback_without_feather_switches_hard_at_the_region_edge(self):
        rc, _, o, ell, comp = self.putback(feather=0)
        self.assertEqual(rc, 0)
        np.testing.assert_allclose(o[ell][:, 0].mean(), 0.8, atol=0.01)
        # a pixel past the 6 px dilation, still near the element, is the composite
        np.testing.assert_allclose(o[60, 100 + 40 + 10], comp[60, 100 + 40 + 10], atol=1 / 255)

    def test_iou_and_coverage_of_the_finished_matte(self):
        ell, _, _ = self.frames()
        rc, res, *_ = self.putback(matte=ell.astype(float))
        self.assertEqual(rc, 0)
        self.assertEqual(res["iou"], 1.0)
        self.assertEqual(res["finishOverElement"], 1.0)
        shifted = np.roll(ell, 12, axis=1)
        rc, res, *_ = self.putback(matte=shifted.astype(float))
        want = (ell & shifted).sum() / (ell | shifted).sum()
        self.assertAlmostEqual(res["iou"], want, places=3)
        self.assertLess(res["iou"], 0.9)
        self.assertAlmostEqual(res["finishOverElement"], 1.0, places=3)
        half = ell.copy()
        half[:, 100:] = False
        rc, res, *_ = self.putback(matte=half.astype(float))
        self.assertAlmostEqual(res["finishOverElement"], half.sum() / ell.sum(), places=3)
        self.assertAlmostEqual(res["iou"], half.sum() / ell.sum(), places=3)

    def test_no_iou_without_both_matte_files(self):
        _, res, *_ = self.putback()
        self.assertNotIn("iou", res)

    def test_selftest_exits_0(self):
        rc, out, err = run(PUTBACK, "--selftest")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("selftest pass", out)

    def test_command_line_mask_then_putback(self):
        ell, comp, elem = self.frames()
        guide = self.write("comp.png", comp)
        el = self.write("elem.png", elem, "RGBA")
        rc, out, err = run(PUTBACK, "mask", guide, el, self.tmp / "cli", "--dilate", 4, "--step", 16)
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out)["size"], [208, 128])
        pad = np.zeros((128, 208, 3))
        pad[:120, :200] = comp
        fin = self.write("fin.png", pad)
        rc, out, err = run(PUTBACK, "putback", guide, fin, self.tmp / "cli" / "region.png", self.tmp / "out.png")
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out)["outsideDiff"], 0)


# ---------------------------------------------------------------- env_from_plate


def srgb_to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


class EnvFromPlate(Temp):
    ARGS = (
        "--focal", 50, "--tilt", 0, "--sun", "0,10", "--lit", "0.316,0.205,0.147", "--shadow", "0.147,0.134,0.133",
        "--sky-target", "0.234,0.214,0.212",
    )  # fmt: skip

    def plate(self, sun_value=None):
        """A 320x180 plate: sky above row 100, ground below; optionally a bright disc where the sun at 0,10 lands."""
        h, w = 180, 320
        y = np.linspace(0, 1, h)[:, None, None]
        sky = np.array([0.25, 0.45, 0.85]) * (1 - 0.4 * y) + np.array([0.9, 0.8, 0.7]) * 0.4 * y
        a = np.where(np.arange(h)[:, None, None] < 100, sky, np.array([0.3, 0.25, 0.2])) * np.ones((h, w, 3))
        if sun_value is not None:
            yy, xx = np.mgrid[:h, :w]
            a[np.hypot(xx - 160, yy - 12) < 8] = sun_value
        path = self.tmp / "plate.png"
        Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(path)
        return path

    def build(self, plate, *extra, out="env.png"):
        rc, stdout, err = run(ENV, plate, self.tmp / out, *self.ARGS, *extra)
        self.assertEqual(rc, 0, err)
        return json.loads(stdout)

    def test_writes_an_equirect_png_of_the_width_asked(self):
        for width in (256, 512):
            with self.subTest(width=width):
                res = self.build(self.plate(), "--width", width, out="e%d.png" % width)
                with Image.open(self.tmp / ("e%d.png" % width)) as im:
                    self.assertEqual(im.size, (width, width // 2))
                    self.assertEqual(im.mode, "RGB")
                    self.assertEqual(im.format, "PNG")
                self.assertEqual(res["out"], str(self.tmp / ("e%d.png" % width)))

    def test_png_is_normalized_to_its_peak_and_the_peak_is_printed(self):
        res = self.build(self.plate(), "--width", 256)
        with Image.open(self.tmp / "env.png") as im:
            a = np.asarray(im)
        self.assertEqual(int(a.max()), 255)
        self.assertGreater(res["peak"], 0)
        self.assertLessEqual(res["peak"], 4.0)
        self.assertGreater(res["seenPx"], 0)

    def test_readings_are_in_range(self):
        res = self.build(self.plate(), "--width", 256)
        for key in ("zenith", "floorLight", "sunClamp"):
            self.assertEqual(len(res[key]), 3, key)
            for v in res[key]:
                self.assertGreaterEqual(v, 0, key)
                self.assertLessEqual(v, 1.5, key)
        self.assertGreater(max(res["floorLight"]), 0)

    def test_floor_light_has_the_hue_of_the_sky_target(self):
        for tgt in ("0.234,0.214,0.212", "0.15,0.2,0.3"):
            with self.subTest(target=tgt):
                res = self.build(self.plate(), "--width", 256, "--sky-target", tgt)
                want = np.array([float(v) for v in tgt.split(",")])
                got = np.array(res["floorLight"])
                np.testing.assert_allclose(got / got.max(), want / want.max(), atol=0.03)

    def test_up_is_the_top_of_the_map_and_the_ground_is_darker_than_the_sky(self):
        self.build(self.plate(), "--width", 256)
        with Image.open(self.tmp / "env.png") as im:
            a = np.asarray(im).astype(float)
        self.assertGreater(a[:64].mean(), a[64:].mean())

    def test_the_sky_the_plate_shows_lands_where_the_orientation_note_says(self):
        self.build(self.plate(), "--width", 256)
        with Image.open(self.tmp / "env.png") as im:
            a = np.asarray(im).astype(float) / 255
        # u = 0.75 looks away from the camera: the plate's blue sky shows near the horizon of that column
        col = a[40, 192]
        self.assertGreater(col[2], col[0])
        # the opposite side (u = 0.25, toward the camera) is built, not copied: no plate pixel is seen there
        res = self.build(self.plate(), "--width", 256)
        self.assertLess(res["seenPx"], 256 * 64 // 2)

    def test_sun_disc_is_clamped_to_its_surroundings(self):
        plain = self.build(self.plate(), "--width", 512, out="plain.png")
        bright = self.build(self.plate(sun_value=1.0), "--width", 512, out="bright.png")
        # without the clamp the disc (linear 1.0) would set the peak; the clamp keeps it at the sky's level
        self.assertLess(max(bright["sunClamp"]), 0.9)
        self.assertLess(bright["peak"], 0.9 * 1.0)
        self.assertAlmostEqual(bright["peak"], plain["peak"], delta=0.15 * plain["peak"])

    def test_missing_required_option_exits_2(self):
        rc, _, err = run(ENV, self.plate(), self.tmp / "x.png", "--focal", 50)
        self.assertEqual(rc, 2)
        self.assertIn("--sun", err)


# ---------------------------------------------------------------- glb_material tint and linear-store


def s2l(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def hex_to_linear(hx):
    return [s2l(int(hx.lstrip("#")[i : i + 2], 16) / 255.0) for i in (0, 2, 4)]


def png_bytes(arr):
    buf = io.BytesIO()
    Image.fromarray(np.asarray(arr, np.uint8)).save(buf, "PNG")
    return buf.getvalue()


def glb_with_textures(path, materials, images=()):
    """A GLB with a JSON chunk and a BIN chunk holding one PNG per entry of images (uint8 arrays).
    Texture i is images[i]; materials refer to texture index i."""
    binary = b""
    views, imgs, texs = [], [], []
    for i, arr in enumerate(images):
        data = png_bytes(arr)
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
        binary += data + b"\0" * ((4 - len(data) % 4) % 4)
        imgs.append({"bufferView": i, "mimeType": "image/png"})
        texs.append({"source": i})
    doc = {"asset": {"version": "2.0"}, "materials": materials}
    if images:
        doc.update(buffers=[{"byteLength": len(binary)}], bufferViews=views, images=imgs, textures=texs)
    js = json.dumps(doc).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + (8 + len(binary) if binary else 0)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        if binary:
            f.write(struct.pack("<II", len(binary), 0x004E4942))
            f.write(binary)


def load_glb(path):
    """(json doc, {texture index: decoded uint8 array}) of a GLB, parsed here and decoded by Pillow."""
    data = Path(path).read_bytes()
    jlen = struct.unpack("<I", data[12:16])[0]
    doc = json.loads(data[20 : 20 + jlen])
    rest = data[20 + jlen :]
    binary = rest[8 : 8 + struct.unpack("<I", rest[:4])[0]] if rest else b""
    tex = {}
    for i, t in enumerate(doc.get("textures", [])):
        bv = doc["bufferViews"][doc["images"][t["source"]]["bufferView"]]
        raw = binary[bv.get("byteOffset", 0) : bv.get("byteOffset", 0) + bv["byteLength"]]
        with Image.open(io.BytesIO(raw)) as im:
            tex[i] = np.asarray(im).copy()
    return doc, tex


def checker(c1, c2, alpha=None):
    """A 4x4 checkerboard of two sRGB colors (RGB, or RGBA with the given alpha)."""
    a = np.zeros((4, 4, 3), np.uint8)
    for y in range(4):
        for x in range(4):
            a[y, x] = c1 if (x + y) % 2 == 0 else c2
    if alpha is not None:
        a = np.dstack([a, np.full((4, 4), alpha, np.uint8)])
    return a


CORAL = "#E0452C"


class GlbTintLinearStore(Temp):
    def make(self, materials, images=(), name="m.glb"):
        src = self.tmp / name
        glb_with_textures(src, materials, images)
        return src

    def glb(self, *args):
        rc, out, err = run(GLB, *args)
        return rc, out, err

    def mean_linear(self, path, name):
        rc, out, err = self.glb("list", path)
        self.assertEqual(rc, 0, err)
        return {m["name"]: m for m in json.loads(out)}[name]["baseColorLinear"]

    # tint
    def test_tint_sets_an_untextured_factor_to_the_brand_in_linear_light(self):
        src = self.make(
            [
                {
                    "name": "Fabric",
                    "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.5, 0.5, 0.8], "roughnessFactor": 0.4},
                },
                {"name": "Steel", "pbrMetallicRoughness": {"baseColorFactor": [0.3, 0.3, 0.3, 1]}},
            ]
        )
        before = src.read_bytes()
        dst = self.tmp / "m_v002.glb"
        rc, out, err = self.glb("tint", src, dst, "--brand", "Fabric=" + CORAL)
        self.assertEqual(rc, 0, err)
        self.assertEqual(src.read_bytes(), before)
        doc, _ = load_glb(dst)
        fabric, steel = doc["materials"]
        want = hex_to_linear(CORAL)
        # the factor was gray 0.5: the brand's red 0.745 is capped at 1, the others are scaled exactly
        got = fabric["pbrMetallicRoughness"]["baseColorFactor"]
        for i in range(3):
            self.assertAlmostEqual(got[i], min(1.0, want[i]), places=4)
        self.assertEqual(got[3], 0.8)
        self.assertEqual(fabric["pbrMetallicRoughness"]["roughnessFactor"], 0.4)
        self.assertEqual(steel["pbrMetallicRoughness"]["baseColorFactor"], [0.3, 0.3, 0.3, 1])
        self.assertEqual([c["name"] for c in json.loads(out)["changed"]], ["Fabric"])

    def test_tint_caps_the_factor_at_one_and_keeps_a_black_channel_black(self):
        src = self.make(
            [
                {"name": "Dim", "pbrMetallicRoughness": {"baseColorFactor": [0.1, 0.1, 0.1, 1]}},
                {"name": "NoRed", "pbrMetallicRoughness": {"baseColorFactor": [0.0, 0.5, 0.5, 1]}},
            ]
        )
        dst = self.tmp / "o.glb"
        rc, _, err = self.glb("tint", src, dst, "--brand", "Dim=#FFFFFF", "--brand", "NoRed=" + CORAL)
        self.assertEqual(rc, 0, err)
        doc, _ = load_glb(dst)
        self.assertEqual(doc["materials"][0]["pbrMetallicRoughness"]["baseColorFactor"][:3], [1.0, 1.0, 1.0])
        self.assertEqual(doc["materials"][1]["pbrMetallicRoughness"]["baseColorFactor"][0], 0.0)

    def test_tint_a_textured_material_reaches_the_brand_mean_and_keeps_the_pattern(self):
        tex = checker((120, 70, 50), (170, 100, 80))
        src = self.make(
            [{"name": "Weave", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}, {"name": "Other"}], [tex]
        )
        dst = self.tmp / "t.glb"
        rc, out, err = self.glb("tint", src, dst, "--brand", "Weave=" + CORAL)
        self.assertEqual(rc, 0, err)
        want = hex_to_linear(CORAL)
        got = self.mean_linear(dst, "Weave")
        for i in range(3):
            self.assertAlmostEqual(got[i], want[i], delta=max(0.01, 0.06 * want[i]))
        # the pattern survives: the ratio of the two squares in linear red is the same before and after
        _, tex_after = load_glb(dst)
        a0 = srgb_to_linear(tex[0, 0, 0] / 255.0) / srgb_to_linear(tex[0, 1, 0] / 255.0)
        a1 = srgb_to_linear(tex_after[0][0, 0, 0] / 255.0) / srgb_to_linear(tex_after[0][0, 1, 0] / 255.0)
        self.assertAlmostEqual(a1, a0, delta=0.05 * a0)
        self.assertEqual(json.loads(out)["changed"][0]["name"], "Weave")
        self.assertLess(json.loads(out)["changed"][0]["after"]["brand"]["deltaE76"], 3.0)

    def test_tint_keeps_the_texture_alpha(self):
        tex = checker((120, 70, 50), (170, 100, 80), alpha=137)
        src = self.make([{"name": "Weave", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}], [tex])
        dst = self.tmp / "a.glb"
        rc, _, err = self.glb("tint", src, dst, "--brand", "Weave=" + CORAL)
        self.assertEqual(rc, 0, err)
        _, after = load_glb(dst)
        self.assertEqual(after[0].shape, (4, 4, 4))
        self.assertTrue((after[0][..., 3] == 137).all())
        self.assertFalse((after[0][..., :3] == tex[..., :3]).all())

    def test_tint_refuses_unknown_names_the_source_as_target_and_a_missing_brand(self):
        src = self.make([{"name": "Fabric"}])
        rc, _, err = self.glb("tint", src, self.tmp / "o.glb", "--brand", "Glass=#112233")
        self.assertNotEqual(rc, 0)
        self.assertIn("Glass", err)
        self.assertFalse((self.tmp / "o.glb").exists())
        rc, _, err = self.glb("tint", src, src, "--brand", "Fabric=#112233")
        self.assertNotEqual(rc, 0)
        self.assertIn("new file", err)
        rc, _, err = self.glb("tint", src, self.tmp / "o.glb")
        self.assertEqual(rc, 2)
        self.assertIn("--brand", err)
        rc, _, err = self.glb("tint", src, self.tmp / "o.glb", "--brand", "Fabric")
        self.assertNotEqual(rc, 0)
        self.assertIn("MATERIAL=#RRGGBB", err)

    def test_list_reports_a_brand_gap_that_tint_closes(self):
        tex = checker((120, 70, 50), (170, 100, 80))
        src = self.make([{"name": "Weave", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}], [tex])
        rc, out, _ = self.glb("list", src, "--brand", "Weave=" + CORAL)
        before = json.loads(out)[0]["brand"]
        self.assertGreater(before["deltaE76"], 10)
        dst = self.tmp / "t.glb"
        self.glb("tint", src, dst, "--brand", "Weave=" + CORAL)
        rc, out, _ = self.glb("list", dst, "--brand", "Weave=" + CORAL)
        after = json.loads(out)[0]["brand"]
        self.assertLess(after["deltaE76"], 3.0)
        self.assertAlmostEqual(after["luminanceRatio"], 1.0, delta=0.06)

    # linear-store
    def test_linear_store_decodes_factors_and_keeps_alpha_and_other_fields(self):
        src = self.make(
            [
                {
                    "name": "A",
                    "pbrMetallicRoughness": {
                        "baseColorFactor": [0.5, 0.35, 1.0, 0.8],
                        "roughnessFactor": 0.3,
                        "metallicFactor": 0.1,
                    },
                },
                {"name": "B", "pbrMetallicRoughness": {"roughnessFactor": 0.9}},
            ]
        )
        before = src.read_bytes()
        dst = self.tmp / "lin.glb"
        rc, out, err = self.glb("linear-store", src, dst)
        self.assertEqual(rc, 0, err)
        self.assertEqual(src.read_bytes(), before)
        doc, _ = load_glb(dst)
        a, b = (m["pbrMetallicRoughness"] for m in doc["materials"])
        for got, srgb in zip(a["baseColorFactor"][:3], (0.5, 0.35, 1.0)):
            self.assertAlmostEqual(got, s2l(srgb), places=5)
        self.assertEqual(a["baseColorFactor"][3], 0.8)
        self.assertEqual((a["roughnessFactor"], a["metallicFactor"]), (0.3, 0.1))
        # a material with no base color factor gets none added (glTF default white stays white)
        self.assertNotIn("baseColorFactor", b)
        self.assertEqual(b["roughnessFactor"], 0.9)
        self.assertEqual(json.loads(out)["changed"], ["A", "B"])

    def test_linear_store_writes_texture_bytes_as_linear_values(self):
        tex = checker((128, 255, 0), (64, 200, 255), alpha=200)
        src = self.make([{"name": "T", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}], [tex])
        dst = self.tmp / "lin.glb"
        rc, _, err = self.glb("linear-store", src, dst)
        self.assertEqual(rc, 0, err)
        doc, after = load_glb(dst)
        want = np.rint(255 * srgb_to_linear(tex[..., :3] / 255.0))
        np.testing.assert_allclose(after[0][..., :3], want, atol=1)
        self.assertEqual(int(after[0][0, 0, 0]), 55)  # sRGB 128 is linear 0.216
        self.assertTrue((after[0][..., 3] == 200).all())
        # the buffer length in the JSON matches what was written, and the old view is still in place
        self.assertEqual(len(doc["bufferViews"]), 2)
        self.assertGreater(doc["buffers"][0]["byteLength"], 0)

    def test_linear_store_converts_a_shared_texture_once(self):
        tex = checker((128, 128, 128), (128, 128, 128))
        mats = [
            {"name": "One", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}},
            {
                "name": "Two",
                "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "baseColorFactor": [1, 1, 1, 1]},
            },
        ]
        src = self.make(mats, [tex])
        dst = self.tmp / "lin.glb"
        rc, _, err = self.glb("linear-store", src, dst)
        self.assertEqual(rc, 0, err)
        _, after = load_glb(dst)
        self.assertTrue((after[0][..., :3] == 55).all(), after[0][0, 0])  # decoded twice would read about 10

    def test_linear_store_refuses_to_overwrite_the_source(self):
        src = self.make([{"name": "A"}])
        rc, _, err = self.glb("linear-store", src, src)
        self.assertNotEqual(rc, 0)
        self.assertIn("new file", err)

    # normal-flatten
    def test_normal_flatten_scales_the_tilt_of_the_normal_texture(self):
        n = np.zeros((2, 2, 3), np.uint8)
        n[...] = (230, 128, 200)  # tilted to +x
        src = self.make([{"name": "Weave", "normalTexture": {"index": 0}}], [n])
        out = []
        for k in (0.0, 0.5, 1.0):
            dst = self.tmp / ("n%s.glb" % k)
            rc, _, err = self.glb("set", src, dst, "--material", "Weave", "--normal-flatten", k)
            self.assertEqual(rc, 0, err)
            out.append(load_glb(dst)[1][0][0, 0].astype(int))
        np.testing.assert_array_equal(out[0], [128, 128, 255])  # flat
        self.assertAlmostEqual(out[1][0], round((0.5 * (230 / 127.5 - 1) + 1) * 127.5), delta=1)
        self.assertLess(out[1][0], 230)
        self.assertGreater(out[1][0], out[0][0])
        self.assertAlmostEqual(out[2][0], 230, delta=1)  # k = 1 keeps the tilt


if __name__ == "__main__":
    unittest.main()
