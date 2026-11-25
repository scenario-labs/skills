"""Offline tests for scenario-3dsmax-lighting-rendering scripts, with no 3ds Max installed.

render_metrics needs numpy and Pillow (requirements.txt); its tests skip without them.
maxkit_render runs against a stand-in runtime: passing tests prove the Python logic only.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-lighting-rendering" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

HAVE_DEPS = all(importlib.util.find_spec(m) is not None for m in ("numpy", "PIL"))

import maxkit_render  # noqa: E402  (imports the fake pymxs)

if HAVE_DEPS:
    import numpy as np
    from PIL import Image

    import render_metrics


class _TmpCase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="max_lr_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def png(self, name, arr):
        p = self.dir / name
        Image.fromarray(np.asarray(arr, dtype=np.uint8)).save(p)
        return str(p)


@unittest.skipUnless(HAVE_DEPS, "needs numpy and Pillow")
class RenderMetrics(_TmpCase):
    def test_noise_measures_image_smaller_than_a_tile(self):
        rng = np.random.default_rng(1)
        path = self.png("small.png", rng.integers(0, 256, (32, 32, 3)))
        self.assertGreater(render_metrics.noise(path)["sigma"], 0.0)

    def test_noise_keeps_zero_for_a_constant_image(self):
        path = self.png("flat.png", np.full((32, 32, 3), 128))
        self.assertEqual(render_metrics.noise(path)["sigma"], 0.0)

    def test_noise_reads_edge_tiles(self):
        arr = np.full((64, 96, 3), 128)
        arr[:, 64:] = np.random.default_rng(2).integers(0, 256, (64, 32, 3))
        res = render_metrics.noise(self.png("edge.png", arr))
        self.assertGreater(res["worst_tiles"][0]["sigma"], 0.0)
        self.assertEqual(res["worst_tiles"][0]["x"], 64)

    def test_noise_refuses_an_unmeasurable_image(self):
        with self.assertRaises(ValueError):
            render_metrics.noise(self.png("tiny.png", np.full((2, 2, 3), 9)))

    def test_flicker_finds_a_jump_when_the_median_step_is_zero(self):
        paths = [self.png(f"f{i}.png", np.full((8, 8, 3), v)) for i, v in enumerate((51, 51, 204, 204, 204))]
        self.assertEqual(render_metrics.flicker(paths)["jumps"], [2])

    def test_flicker_unchanged_sequence_has_no_jump(self):
        paths = [self.png(f"c{i}.png", np.full((8, 8, 3), 90)) for i in range(4)]
        self.assertEqual(render_metrics.flicker(paths)["jumps"], [])

    def test_crops_never_replace_an_existing_file(self):
        src = self.png("beauty.png", np.full((64, 64, 3), 100))
        out = self.dir / "out"
        out.mkdir()
        keep = out / "beauty_crop_tl.png"
        keep.write_bytes(b"user edit")
        with self.assertRaises(FileExistsError):
            render_metrics.crops(src, str(out), size=16)
        self.assertEqual(keep.read_bytes(), b"user edit")
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["beauty_crop_tl.png"])

    def test_crops_write_six_new_files(self):
        src = self.png("beauty.png", np.full((64, 64, 3), 100))
        paths = render_metrics.crops(src, str(self.dir / "fresh"), size=16)
        self.assertEqual(len(paths), 6)
        self.assertTrue(all(Path(p).is_file() for p in paths))

    def test_crops_remove_their_own_files_when_one_fails(self):
        src = self.png("beauty.png", np.full((64, 64, 3), 100))
        out = self.dir / "partial"
        real_save = Image.Image.save
        calls = []

        def flaky(img, fp, *a, **k):
            calls.append(1)
            if len(calls) == 3:
                raise OSError("disk full")
            return real_save(img, fp, *a, **k)

        with mock.patch.object(Image.Image, "save", flaky), self.assertRaises(OSError):
            render_metrics.crops(src, str(out), size=16)
        self.assertEqual(list(out.iterdir()), [])

    def test_downscale_refuses_source_and_existing_destination(self):
        src = self.png("big.png", np.full((16, 16, 3), 50))
        with self.assertRaises(ValueError):
            render_metrics.downscale(src, src)
        other = self.dir / "other.png"
        other.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            render_metrics.downscale(src, str(other))
        self.assertEqual(other.read_bytes(), b"keep")

    def test_downscale_refuses_a_hard_link_to_the_source(self):
        src = self.png("big.png", np.full((16, 16, 3), 50))
        alias = self.dir / "alias.png"
        try:
            alias.hardlink_to(src)
        except (OSError, AttributeError):
            self.skipTest("hard links unavailable")
        with self.assertRaises(ValueError):
            render_metrics.downscale(src, str(alias))


class _Rt:
    """Stand-in runtime for the few calls the tested helpers make."""

    def __init__(self, names=None, textures=(), render_writes=True):
        self._names = names
        self._textures = list(textures)
        self._render_writes = render_writes
        self.closed = []
        self.BitmapTexture = object()
        self.renderSceneDialog = mock.Mock(isOpen=mock.Mock(return_value=False))

    def getPropNames(self, obj):
        if self._names is None:
            raise RuntimeError("no property list")
        return self._names

    def getClassInstances(self, cls):
        return self._textures

    def render(self, **kw):
        if self._render_writes:
            Path(kw["outputFile"]).write_bytes(b"png")
        return "bitmap"

    def close(self, bmp):
        self.closed.append(bmp)

    def Point2(self, w, h):
        return (w, h)


class MaxkitRender(unittest.TestCase):
    def test_prop_dump_reports_unreadable_names(self):
        with mock.patch.object(maxkit_render, "rt", _Rt(names=None)):
            self.assertIn("_error", maxkit_render.prop_dump(object(), ("noise",)))
            rep = maxkit_render.set_props(object(), {"a": 1}, dry_run=False)
        self.assertIn("error", rep)
        self.assertEqual(rep["missing"], ["a"])

    def test_prop_dump_empty_match_stays_empty(self):
        with mock.patch.object(maxkit_render, "rt", _Rt(names=["other"])):
            self.assertEqual(maxkit_render.prop_dump(object(), ("noise",)), {})

    def test_bitmap_audit_reads_all_or_marks_truncation(self):
        texs = [mock.Mock(filename=f"c:/t/wood_{i}_normal.png") for i in range(3)]
        for t in texs:
            t.bitmap.colorSpace, t.bitmap.colorSpaceSource, t.bitmap.colorSpaceStatus = "sRGB", "rule", "#normal"
        with mock.patch.object(maxkit_render, "rt", _Rt(textures=texs)):
            self.assertEqual(len(maxkit_render.bitmap_color_spaces()), 3)
            cut = maxkit_render.bitmap_color_spaces(limit=2)
        self.assertEqual(len(cut), 3)
        self.assertTrue(cut[-1]["status"].startswith("truncated"))

    def test_test_render_closes_bitmap_and_checks_output(self):
        with tempfile.TemporaryDirectory() as d:
            fake = _Rt()
            with mock.patch.object(maxkit_render, "rt", fake):
                rep = maxkit_render.test_render(str(Path(d) / "t_v001.png"))
            self.assertEqual(fake.closed, ["bitmap"])
            self.assertIn("seconds", rep)
            fake = _Rt(render_writes=False)
            with mock.patch.object(maxkit_render, "rt", fake), self.assertRaises(RuntimeError):
                maxkit_render.test_render(str(Path(d) / "t_v002.png"))
            self.assertEqual(fake.closed, ["bitmap"])


if __name__ == "__main__":
    unittest.main()
