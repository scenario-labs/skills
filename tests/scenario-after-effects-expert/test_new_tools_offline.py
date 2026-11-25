"""Runs the newer host-side tools on synthetic inputs, with no After Effects installed.

- the offline checker's dialog and reserved-word rules (raw app.open, app.newProject,
  app.project.save(), a reserved word as a key or a name);
- what each effects builder returns, through vfx_returns.cjs under node with a stand-in object model;
- the beat finder on a synthetic click track (needs ffmpeg and ffprobe);
- the layout and seat checks on synthetic mattes and plates (need ImageMagick 7, `magick`);
- glb_material.py on a minimal GLB: factors change in a new file, the source stays as it was.

Each case that needs a missing tool skips, naming it.
"""

import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
LEAD = FAMILY / "scenario-after-effects-expert" / "scripts"
ADTOOLS = FAMILY / "scenario-after-effects-motion-production" / "scripts"
LAYOUT = FAMILY / "scenario-after-effects-3d" / "scripts" / "layout_check.py"
GLB = FAMILY / "scenario-after-effects-3d" / "scripts" / "glb_material.py"
SEAT = FAMILY / "scenario-after-effects-generation" / "scripts" / "seat_check.py"
VFX_RETURNS = HERE / "vfx_returns.cjs"
for folder in (LEAD, ADTOOLS):
    sys.path.insert(0, str(folder))

import adtools  # noqa: E402
import ae_check as chk  # noqa: E402

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
HAS_MAGICK = bool(shutil.which("magick"))
HAS_NODE = bool(shutil.which("node"))


def errors(src):
    return [f["message"] for f in chk.scan(src, chk.ES3, "job") if f["severity"] == "error"]


def run(script, *args):
    p = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class CheckerDialogAndReservedRules(unittest.TestCase):
    def test_raw_app_open_is_a_dialog_error(self):
        found = errors('var p = app.open(new File("/x/a.aep"));\n')
        self.assertTrue(any(m.startswith(chk.DIALOG_PREFIX) and "app.open" in m for m in found), found)

    def test_app_open_after_do_not_save_or_as_a_method_name_passes(self):
        self.assertEqual(errors("app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); app.open(f);\n"), [])
        self.assertEqual(errors("var AEK = { open: function open(p) { return p; } };\n"), [])

    def test_app_new_project_is_a_dialog_error(self):
        found = errors("app.newProject();\n")
        self.assertTrue(any("app.newProject" in m for m in found), found)

    def test_bare_project_save_is_a_dialog_error_but_a_path_is_not(self):
        self.assertTrue(any("app.project.save()" in m for m in errors("app.project.save();\n")))
        self.assertEqual(errors('app.project.save(new File("/x/a.aep"));\n'), [])

    def test_reserved_word_as_key_or_name_is_an_error(self):
        self.assertTrue(any("reserved word" in m for m in errors("var o = { a: 1, class: 2 };\n")))
        self.assertTrue(any("reserved word" in m for m in errors("var o = { a: 1, default: 2 };\n")))
        self.assertTrue(any("reserved word" in m for m in errors("var final = 3;\n")))

    def test_quoted_key_and_dotted_property_pass(self):
        self.assertEqual(errors('var o = { a: 1, "default": 2 }; var x = M.final;\n'), [])


@unittest.skipUnless(HAS_NODE, "node not installed")
class EffectsBuilderReturns(unittest.TestCase):
    def test_every_builder_returns_what_its_comment_says(self):
        p = subprocess.run(["node", str(VFX_RETURNS)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("all builders match", p.stdout)

    def test_a_planted_mismatch_fails(self):
        src = (FAMILY / "scenario-after-effects-vfx" / "scripts" / "vfx.jsx").read_text(encoding="utf-8")
        planted = src.replace("return { comps: [r.grey], layers: [r.layer], layer: r.layer, grey: r.grey };",
                              "return { comps: [r.grey], layers: [r.layer], layer: r.layer };", 1)
        self.assertNotEqual(planted, src, "the smoke.build return line moved: update the plant")
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "vfx.jsx"
            copy.write_text(planted, encoding="utf-8")
            p = subprocess.run(["node", str(VFX_RETURNS), str(copy)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("smoke.build", p.stdout)


def click_track(path, bpm=120.0, offset=0.25, seconds=12.0, rate=44100):
    """A mono WAV with a short decaying 1 kHz burst on every beat."""
    n = int(seconds * rate)
    data = np.zeros(n, np.float32)
    period = 60.0 / bpm
    t = np.arange(int(0.03 * rate)) / rate
    burst = (np.sin(2 * math.pi * 1000 * t) * np.exp(-t * 120)).astype(np.float32)
    k = 0
    while offset + k * period < seconds - 0.05:
        i = int(round((offset + k * period) * rate))
        data[i:i + len(burst)] += burst[: n - i]
        k += 1
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(data, -1, 1) * 32000).astype("<i2").tobytes())


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg or ffprobe not installed")
class BeatFinder(Temp):
    def test_click_track_tempo_and_phase(self):
        wav = self.tmp / "click.wav"
        click_track(wav)
        res = adtools.detect_onsets(str(wav), 30, seconds=12)
        self.assertNotIn("error", res)
        self.assertAlmostEqual(res["bpm"], 120.0, delta=1.0)
        # the first beat sits on a click: 0.25 s, within a frame at 30 fps
        self.assertAlmostEqual(res["beats_s"][0] % 0.5, 0.25, delta=1 / 30)
        self.assertNotIn("warning", res)

    def test_too_short_is_an_error_not_a_guess(self):
        wav = self.tmp / "short.wav"
        click_track(wav, seconds=1.5)
        self.assertIn("error", adtools.detect_onsets(str(wav), 30, seconds=12))


def rgba(path, w, h, box=None, color=(255, 255, 255)):
    a = np.zeros((h, w, 4), np.uint8)
    if box:
        x0, y0, x1, y1 = box
        a[y0:y1, x0:x1, :3] = color
        a[y0:y1, x0:x1, 3] = 255
    Image.fromarray(a, "RGBA").save(path)


@unittest.skipUnless(HAS_MAGICK, "ImageMagick 7 (magick) not installed")
class LayoutCheck(Temp):
    def test_title_clear_of_the_product_passes(self):
        rgba(self.tmp / "read.png", 400, 200, (40, 20, 360, 60))
        rgba(self.tmp / "front.png", 400, 200, (150, 100, 250, 190))
        rc, out, err = run(LAYOUT, self.tmp / "read.png", self.tmp / "front.png")
        res = json.loads(out)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(res["visible"], 1.0)
        self.assertTrue(res["inFrame"])
        self.assertEqual(res["frontOffset"], [0.0, 45.0])

    def test_half_covered_title_fails(self):
        rgba(self.tmp / "read.png", 400, 200, (40, 20, 360, 60))
        rgba(self.tmp / "front.png", 400, 200, (200, 0, 400, 200))
        rc, out, _ = run(LAYOUT, self.tmp / "read.png", self.tmp / "front.png")
        self.assertEqual(rc, 1)
        self.assertAlmostEqual(json.loads(out)["visible"], 0.5, delta=0.02)

    def test_title_off_the_frame_edge_fails_even_uncovered(self):
        rgba(self.tmp / "read.png", 400, 200, (0, 20, 300, 60))
        rgba(self.tmp / "front.png", 400, 200, (150, 120, 250, 190))
        rc, out, _ = run(LAYOUT, self.tmp / "read.png", self.tmp / "front.png")
        self.assertEqual(rc, 1)
        self.assertFalse(json.loads(out)["inFrame"])


@unittest.skipUnless(HAS_MAGICK, "ImageMagick 7 (magick) not installed")
class SeatCheck(Temp):
    def plate(self, ground):
        a = np.zeros((200, 400, 3), np.uint8)
        a[:100] = (120, 160, 230)   # sky, excluded by --floor-top
        a[100:] = ground
        Image.fromarray(a, "RGB").save(self.tmp / "plate.png")

    def test_same_light_color_passes(self):
        self.plate((230, 200, 160))
        rgba(self.tmp / "cut.png", 200, 200, (50, 50, 150, 150), (230, 200, 160))
        rc, out, err = run(SEAT, self.tmp / "cut.png", self.tmp / "plate.png", "--floor-top", 100)
        self.assertEqual(rc, 0, out + err)
        self.assertLessEqual(abs(json.loads(out)["warmthGap"]), 0.15)

    def test_cold_cutout_on_a_warm_plate_fails(self):
        self.plate((240, 190, 130))
        rgba(self.tmp / "cut.png", 200, 200, (50, 50, 150, 150), (130, 170, 250))
        rc, out, _ = run(SEAT, self.tmp / "cut.png", self.tmp / "plate.png", "--floor-top", 100)
        self.assertEqual(rc, 1)
        self.assertGreater(json.loads(out)["warmthGap"], 0.15)

    def test_contact_gap_gates_a_floating_object(self):
        rgba(self.tmp / "obj.png", 200, 200, (60, 40, 140, 120))
        rgba(self.tmp / "touch.png", 200, 200, (50, 120, 150, 130))
        rgba(self.tmp / "float.png", 200, 200, (50, 130, 150, 140))
        rc, out, err = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "touch.png")
        self.assertEqual(rc, 0, out + err)
        rc, out, _ = run(SEAT, "--contact", self.tmp / "obj.png", self.tmp / "float.png")
        self.assertEqual(rc, 1, out)


def minimal_glb(path, materials):
    doc = {"asset": {"version": "2.0"}, "materials": materials}
    js = json.dumps(doc).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)


class GlbMaterial(Temp):
    def test_set_writes_a_new_file_and_leaves_the_source(self):
        src, dst = self.tmp / "m.glb", self.tmp / "m_v002.glb"
        minimal_glb(src, [{"name": "Rubber", "pbrMetallicRoughness": {"roughnessFactor": 0.8}}, {"name": "Steel"}])
        before = src.read_bytes()
        rc, out, err = run(GLB, "set", src, dst, "--material", "Rubber", "--roughness-scale", "0.5")
        self.assertEqual(rc, 0, err)
        self.assertEqual(src.read_bytes(), before)
        rc, out, _ = run(GLB, "list", dst)
        mats = {m["name"]: m for m in json.loads(out)}
        self.assertAlmostEqual(mats["Rubber"]["roughness"], 0.4)
        self.assertEqual(mats["Steel"]["roughness"], 1.0)

    def test_refuses_to_overwrite_the_source_and_unknown_names(self):
        src = self.tmp / "m.glb"
        minimal_glb(src, [{"name": "Rubber"}])
        rc, _, err = run(GLB, "set", src, src, "--all", "--roughness", "0.2")
        self.assertNotEqual(rc, 0)
        self.assertIn("new file", err)
        rc, _, err = run(GLB, "set", src, self.tmp / "o.glb", "--material", "Glass", "--roughness", "0.2")
        self.assertNotEqual(rc, 0)
        self.assertIn("Glass", err)

    def test_not_a_glb_is_refused(self):
        bad = self.tmp / "m.glb"
        bad.write_bytes(b"OBJ\x00" + b"\x00" * 16)
        rc, _, err = run(GLB, "list", bad)
        self.assertNotEqual(rc, 0)
        self.assertIn("not a GLB", err)


if __name__ == "__main__":
    unittest.main()
