"""Review round 1, group B: the 3D specialist's scripts.

- env_from_plate.py: --sun with a negative azimuth in both argument forms; the zenith solve against the sky that
  build() changes (floor light on the target hue; a planted uniform sky solved back).
- focus_check.py and layout_check.py: an empty matte is not a pass.
- glb_material.py: exclusive output, textures shared between materials, gray and gray-alpha textures.
"""

import io
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "after-effects" / "scenario-after-effects-3d" / "scripts"
ENV = SCRIPTS / "env_from_plate.py"
FOCUS = SCRIPTS / "focus_check.py"
GLB = SCRIPTS / "glb_material.py"
LAYOUT = SCRIPTS / "layout_check.py"


def run(script, *args, cwd=None):
    p = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def s2l(a):
    a = np.asarray(a, float)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


# ---------------------------------------------------------------- env_from_plate


class EnvFromPlateReview(Temp):
    COMMON = ("--lit", "0.316,0.205,0.147", "--shadow", "0.147,0.134,0.133", "--width", 256)

    def plate(self, sky_bytes, name="plate.png"):
        """A 320x180 plate: one uniform sky color above the horizon row (90 at tilt 0), a brown ground below."""
        a = np.zeros((180, 320, 3), np.uint8)
        a[:90] = sky_bytes
        a[90:] = (90, 75, 60)
        path = self.tmp / name
        Image.fromarray(a).save(path)
        return path

    def build(self, plate, *extra, out="env.png"):
        rc, stdout, err = run(ENV, plate, self.tmp / out, *self.COMMON, *extra)
        self.assertEqual(rc, 0, err)
        return json.loads(stdout)

    def test_a_negative_sun_azimuth_parses_in_both_forms_and_gives_one_map(self):
        p = self.plate((90, 140, 200))
        tgt = ("--sky-target", "0.234,0.214,0.212")
        two = self.build(p, "--sun", "-17,4", *tgt, out="two.png")
        eq = self.build(p, "--sun=-17,4", *tgt, out="eq.png")
        self.assertEqual(two["zenith"], eq["zenith"])
        self.assertEqual(two["sunClamp"], eq["sunClamp"])
        with Image.open(self.tmp / "two.png") as a, Image.open(self.tmp / "eq.png") as b:
            self.assertTrue((np.asarray(a) == np.asarray(b)).all())

    def test_floor_light_has_the_target_hue_when_the_plate_sky_has_another(self):
        # a wide lens shows much of the sky: its blue stays in the floor light, the zenith must offset it exactly
        p = self.plate((60, 120, 230))
        for tgt in ("0.4,0.3,0.2", "0.234,0.214,0.212"):
            with self.subTest(target=tgt):
                res = self.build(p, "--focal", 18, "--sun", "0,10", "--sky-target", tgt)
                want = np.array([float(v) for v in tgt.split(",")])
                got = np.array(res["floorLight"])
                np.testing.assert_allclose(got / got.max(), want / want.max(), atol=2e-3)

    def test_the_solved_zenith_reproduces_a_planted_uniform_sky(self):
        # A plate whose sky is one color Z, extended with no falloff (--far-gain 1), is a uniform sky when the zenith
        # is Z; its floor light is then Z. The first run reads the share of the sky the zenith reaches; the second
        # sets the margin that asks for floor light Z, and the solve must return Z itself.
        sky = (90, 140, 200)
        z = s2l(np.array(sky) / 255.0)
        p = self.plate(sky)
        args = ("--focal", 24, "--sun", "0,10", "--far-gain", 1, "--sky-target", ",".join("%.6f" % v for v in z))
        first = self.build(p, *args, "--zenith-margin", 1.25, out="first.png")
        seen_share = float(np.mean(np.array(first["floorLight"]) / (1.25 * z)))  # floor light = margin x seen share x Z
        second = self.build(p, *args, "--zenith-margin", 1 / seen_share, out="second.png")
        np.testing.assert_allclose(second["zenith"], z, rtol=0.01)
        np.testing.assert_allclose(second["floorLight"], z, rtol=0.01)


# ---------------------------------------------------------------- focus_check


@unittest.skipUnless(shutil.which("magick"), "needs ImageMagick 7")
class FocusCheckReview(Temp):
    def matte(self, name, box=None, blur=0):
        a = np.zeros((120, 160, 4), np.uint8)
        if box:
            x0, y0, x1, y1 = box
            a[y0:y1, x0:x1] = 255
        im = Image.fromarray(a, "RGBA")
        path = self.tmp / name
        im.save(path)
        if blur:
            subprocess.run(["magick", str(path), "-channel", "A", "-blur", "0x%g" % blur, str(path)], check=True)
        return path

    def test_an_empty_sharp_matte_is_not_a_pass(self):
        empty = self.matte("sharp.png")
        soft = self.matte("soft.png")
        rc, out, err = run(FOCUS, empty, soft)
        self.assertEqual(rc, 2, out + err)
        r = json.loads(out)
        self.assertFalse(r["pass"])
        self.assertIn("cannot be measured", r["error"])

    def test_a_matte_with_foreground_is_still_measured(self):
        sharp = self.matte("sharp.png", (50, 40, 110, 80))
        soft = self.matte("soft.png", (50, 40, 110, 80), blur=4)
        rc, out, err = run(FOCUS, sharp, soft, "--limit", 2.0, "--height", 1080)
        self.assertEqual(rc, 1, out + err)
        r = json.loads(out)
        self.assertGreaterEqual(r["sigmaPx"], 3.0)
        self.assertFalse(r["pass"])

    def test_layout_check_refuses_an_empty_matte(self):
        title = self.matte("title.png", (40, 30, 120, 50))
        empty = self.matte("empty.png")
        for read, front in ((empty, title), (title, empty)):
            with self.subTest(empty="read" if read == empty else "front"):
                rc, out, err = run(LAYOUT, read, front)
                self.assertEqual(rc, 2, out + err)
                r = json.loads(out)
                self.assertFalse(r["pass"])
                self.assertIn("cannot be measured", r["error"])
        product = self.matte("product.png", (70, 60, 100, 110))
        rc, out, err = run(LAYOUT, title, product)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(json.loads(out)["visible"], 1.0)


# ---------------------------------------------------------------- glb_material


def png_bytes(arr, mode=None):
    buf = io.BytesIO()
    Image.fromarray(np.asarray(arr, np.uint8), mode).save(buf, "PNG")
    return buf.getvalue()


def write_glb(path, materials, pngs=(), textures=None):
    """A GLB with one image per PNG in pngs; textures defaults to one texture per image."""
    binary = b""
    views, imgs = [], []
    for i, data in enumerate(pngs):
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
        binary += data + b"\0" * ((4 - len(data) % 4) % 4)
        imgs.append({"bufferView": i, "mimeType": "image/png"})
    doc = {"asset": {"version": "2.0"}, "materials": materials}
    if pngs:
        texs = textures if textures is not None else [{"source": i} for i in range(len(pngs))]
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


def checker(c1, c2):
    a = np.zeros((4, 4, 3), np.uint8)
    for y in range(4):
        for x in range(4):
            a[y, x] = c1 if (x + y) % 2 == 0 else c2
    return a


def base(i):
    return {"baseColorTexture": {"index": i}}


def tex_of(doc, tex, name, slot="base"):
    m = {m["name"]: m for m in doc["materials"]}[name]
    i = m["pbrMetallicRoughness"]["baseColorTexture"]["index"] if slot == "base" else m["normalTexture"]["index"]
    return tex[i]


CORAL = "#E0452C"


class GlbReview(Temp):
    # exclusive output
    def test_an_existing_destination_is_refused_and_left_as_it_was(self):
        src = self.tmp / "m.glb"
        write_glb(src, [{"name": "A", "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.5, 0.5, 1]}}])
        dst = self.tmp / "taken.glb"
        dst.write_bytes(b"not mine")
        rc, _, err = run(GLB, "tint", src, dst, "--brand", "A=" + CORAL)
        self.assertNotEqual(rc, 0)
        self.assertIn("exists", err)
        self.assertEqual(dst.read_bytes(), b"not mine")

    def test_an_alias_of_the_source_is_refused_and_the_source_survives(self):
        src = self.tmp / "m.glb"
        write_glb(src, [{"name": "A", "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.5, 0.5, 1]}}])
        before = src.read_bytes()
        for cmd in (("tint", "--brand", "A=" + CORAL), ("linear-store",), ("set", "--all", "--roughness", 0.2)):
            with self.subTest(cmd=cmd[0]):
                rc, _, err = run(GLB, cmd[0], "m.glb", "./m.glb", *cmd[1:], cwd=self.tmp)
                self.assertNotEqual(rc, 0, err)
                self.assertEqual(src.read_bytes(), before)

    def test_the_same_source_path_still_names_a_new_file(self):
        src = self.tmp / "m.glb"
        write_glb(src, [{"name": "A"}])
        rc, _, err = run(GLB, "linear-store", src, src)
        self.assertNotEqual(rc, 0)
        self.assertIn("new file", err)

    # textures shared between materials
    def test_tint_changes_only_the_named_material_when_a_texture_is_shared(self):
        orig = checker((120, 70, 50), (170, 100, 80))
        src = self.tmp / "m.glb"
        mats = [{"name": "A", "pbrMetallicRoughness": base(0)}, {"name": "B", "pbrMetallicRoughness": base(0)}]
        write_glb(src, mats, [png_bytes(orig)])
        dst = self.tmp / "t.glb"
        rc, _, err = run(GLB, "tint", src, dst, "--brand", "A=" + CORAL)
        self.assertEqual(rc, 0, err)
        doc, tex = load_glb(dst)
        self.assertTrue((tex_of(doc, tex, "B") == orig).all())
        self.assertFalse((tex_of(doc, tex, "A") == orig).all())

    def test_tint_gives_each_named_material_its_own_brand_on_a_shared_texture(self):
        orig = checker((120, 70, 50), (170, 100, 80))
        src = self.tmp / "m.glb"
        mats = [{"name": "A", "pbrMetallicRoughness": base(0)}, {"name": "B", "pbrMetallicRoughness": base(0)}]
        write_glb(src, mats, [png_bytes(orig)])
        dst = self.tmp / "t.glb"
        rc, _, err = run(GLB, "tint", src, dst, "--brand", "A=" + CORAL, "--brand", "B=#2C6BE0")
        self.assertEqual(rc, 0, err)
        doc, tex = load_glb(dst)
        a, b = tex_of(doc, tex, "A").astype(float), tex_of(doc, tex, "B").astype(float)
        self.assertGreater(a[..., 0].mean(), a[..., 2].mean())
        self.assertGreater(b[..., 2].mean(), b[..., 0].mean())

    def test_an_image_shared_by_two_textures_is_copied_before_the_edit(self):
        orig = checker((120, 70, 50), (170, 100, 80))
        src = self.tmp / "m.glb"
        mats = [{"name": "A", "pbrMetallicRoughness": base(0)}, {"name": "B", "pbrMetallicRoughness": base(1)}]
        write_glb(src, mats, [png_bytes(orig)], textures=[{"source": 0}, {"source": 0}])
        dst = self.tmp / "t.glb"
        rc, _, err = run(GLB, "tint", src, dst, "--brand", "A=" + CORAL)
        self.assertEqual(rc, 0, err)
        doc, tex = load_glb(dst)
        self.assertTrue((tex_of(doc, tex, "B") == orig).all())
        self.assertFalse((tex_of(doc, tex, "A") == orig).all())

    def test_normal_flatten_leaves_an_unselected_material_and_flattens_a_shared_map_once(self):
        nm = np.zeros((4, 4, 3), np.uint8)
        nm[..., 0], nm[..., 1], nm[..., 2] = 200, 128, 220
        src = self.tmp / "m.glb"
        mats = [{"name": "A", "normalTexture": {"index": 0}}, {"name": "B", "normalTexture": {"index": 0}}]
        write_glb(src, mats, [png_bytes(nm)])
        one = self.tmp / "one.glb"
        rc, _, err = run(GLB, "set", src, one, "--material", "A", "--normal-flatten", 0.5)
        self.assertEqual(rc, 0, err)
        doc, tex = load_glb(one)
        self.assertTrue((tex_of(doc, tex, "B", "normal") == nm).all())
        flat_a = tex_of(doc, tex, "A", "normal")
        self.assertLess(int(flat_a[0, 0, 0]), 200)
        both = self.tmp / "both.glb"
        rc, _, err = run(GLB, "set", src, both, "--all", "--normal-flatten", 0.5)
        self.assertEqual(rc, 0, err)
        doc, tex = load_glb(both)
        # flattened once: the same bytes as the single-material edit, for both materials
        self.assertTrue((tex_of(doc, tex, "A", "normal") == flat_a).all())
        self.assertTrue((tex_of(doc, tex, "B", "normal") == flat_a).all())

    def test_linear_store_keeps_a_texture_shared_with_another_slot(self):
        orig = checker((128, 255, 0), (64, 200, 255))
        src = self.tmp / "m.glb"
        mats = [{"name": "A", "pbrMetallicRoughness": base(0)}, {"name": "B", "emissiveTexture": {"index": 0}}]
        write_glb(src, mats, [png_bytes(orig)])
        dst = self.tmp / "lin.glb"
        rc, _, err = run(GLB, "linear-store", src, dst)
        self.assertEqual(rc, 0, err)
        doc, tex = load_glb(dst)
        self.assertTrue((tex[doc["materials"][1]["emissiveTexture"]["index"]] == orig).all())
        self.assertEqual(int(tex_of(doc, tex, "A")[0, 0, 0]), 55)

    # gray textures
    def test_linear_store_keeps_gray_alpha_and_decodes_the_gray(self):
        la = np.zeros((4, 4, 2), np.uint8)
        la[..., 0], la[..., 1] = 128, 128
        src = self.tmp / "m.glb"
        write_glb(src, [{"name": "A", "pbrMetallicRoughness": base(0)}], [png_bytes(la, "LA")])
        dst = self.tmp / "lin.glb"
        rc, _, err = run(GLB, "linear-store", src, dst)
        self.assertEqual(rc, 0, err)
        _, tex = load_glb(dst)
        t = tex[0]
        self.assertEqual(t.shape, (4, 4, 4))
        self.assertTrue((t[..., 3] == 128).all())
        self.assertTrue((t[..., :3] == 55).all())

    def test_tint_gives_a_gray_texture_the_brand_hue(self):
        g = np.full((4, 4), 150, np.uint8)
        g[::2, ::2] = 110
        src = self.tmp / "m.glb"
        write_glb(src, [{"name": "A", "pbrMetallicRoughness": base(0)}], [png_bytes(g, "L")])
        dst = self.tmp / "t.glb"
        rc, out, err = run(GLB, "tint", src, dst, "--brand", "A=" + CORAL)
        self.assertEqual(rc, 0, err)
        _, tex = load_glb(dst)
        t = tex[0].astype(float)
        self.assertEqual(t.shape, (4, 4, 3))
        self.assertGreater(t[..., 0].mean(), t[..., 1].mean() + 40)
        self.assertLess(json.loads(out)["changed"][0]["after"]["brand"]["deltaE76"], 3.0)


if __name__ == "__main__":
    unittest.main()
