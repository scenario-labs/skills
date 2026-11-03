"""render_tracks.py: frame timing, crop boxes, alpha, fresh renders, safe zone, and element geometry."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import helpers

rt = helpers.load("render_tracks")

CANVAS = [240, 400]
ZONE = {"top": 40, "bottom": 360, "left": 10, "right": 230, "text_right": 200}


def red_tip_hand(path):
    """A 100 px glove stand-in: white disc with a red marker at its fingertip (30, 20)."""
    im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 90, 90], fill=(255, 255, 255, 255))
    d.rectangle([29, 19, 31, 21], fill=(255, 0, 0, 255))
    im.save(path)


class Case(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)

    def ctx(self, **spec):
        return rt.Ctx({"canvas": CANVAS, "safe_zone": ZONE, **spec}, self.dir)

    def render_cli(self, elements, **spec):
        helpers.write_json(self.dir / "spec.json", {"fps": 30, "canvas": CANVAS, "safe_zone": ZONE, "elements": elements, **spec})
        result = helpers.run("render_tracks.py", self.dir / "spec.json", self.dir / "out")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.dir / "out/layers.json").read_text())["layers"], result


class TimingTests(unittest.TestCase):
    def test_frame_times_floor_to_the_millisecond(self):
        self.assertEqual(rt.floor_ms(185, 30), 6.166)
        self.assertEqual(rt.floor_ms(3, 30), 0.1)
        self.assertEqual(rt.floor_ms(333, 30), 11.1)
        self.assertEqual(rt.floor_ms(450, 30), 15.0)


class GeometryTests(Case):
    def test_counter_bump_stays_inside_the_safe_top(self):
        for i in range(2):
            helpers.rect_png(self.dir / f"c{i}.png", CANVAS, (60, 42, 160 + 10 * i, 72), (30, 60, 180, 255))
        el = {"type": "counter", "name": "counter", "values": ["c0.png", "c1.png"], "steps": [3], "start": 0, "end": 10}
        first, frames, meta, warnings = rt.render(el, self.ctx())
        rest_box = rt.union(frames[:3], rt.VISIBLE)
        bump_box = rt.union(frames[3:8], rt.VISIBLE)
        self.assertEqual(warnings, [])
        self.assertEqual(meta["bump_shift"][0], 0)
        self.assertGreater(meta["bump_shift"][1], 0)
        self.assertGreaterEqual(bump_box[1], ZONE["top"])
        self.assertGreater(bump_box[2] - bump_box[0], rest_box[2] - rest_box[0])
        self.assertEqual(rt.union(frames[8:], rt.VISIBLE)[1], 42)  # back at rest after 0.15 s
        _, free, _, _ = rt.render({**el, "safe": "none"}, self.ctx())
        self.assertLess(rt.union(free[3:8], rt.VISIBLE)[1], ZONE["top"])

    def test_counter_holds_each_bump_for_0_15_s(self):
        for i in range(2):
            helpers.rect_png(self.dir / f"c{i}.png", CANVAS, (60, 100, 120, 130))
        el = {"type": "counter", "name": "counter", "values": ["c0.png", "c1.png"], "steps": [4], "start": 0, "end": 14}
        _, frames, _, _ = rt.render(el, self.ctx())
        widths = [f[0].width for f in frames]
        self.assertEqual([w > widths[0] for w in widths], [False] * 4 + [True] * 5 + [False] * 5)

    def test_counter_draws_supplied_bump_pngs_as_given(self):
        for i in range(2):
            helpers.rect_png(self.dir / f"c{i}.png", CANVAS, (60, 100, 120, 130), (30, 60, 180, 255))
            helpers.rect_png(self.dir / f"b{i}.png", CANVAS, (56, 97, 124, 133), (255, 255, 255, 255))
        el = {"type": "counter", "name": "counter", "values": ["c0.png", "c1.png"], "bumps": ["b0.png", "b1.png"],
              "steps": [2], "start": 0, "end": 8}
        _, frames, meta, _ = rt.render(el, self.ctx())
        im, offset = frames[2]
        self.assertEqual((offset, im.size), ((56, 97), (68, 36)))
        self.assertEqual(im.getpixel((10, 10)), (255, 255, 255, 255))
        self.assertEqual(meta, {})

    def test_hand_fingertip_lands_on_the_target_while_pressed(self):
        red_tip_hand(self.dir / "hand.png")
        el = {"type": "hand_tap", "name": "tap", "png": "hand.png", "tip": [30, 20], "height": 100, "at": [150, 250],
              "in": 0, "press": 8, "out": 20}
        first, frames, _, _ = rt.render(el, self.ctx())
        for n in (8, 12):  # pressed at 92%, then released on the target
            im, (x, y) = frames[n - first]
            a = np.asarray(im).astype(int)
            ys, xs = np.nonzero((a[..., 0] > 200) & (a[..., 1] < 80) & (a[..., 3] > 200))
            self.assertAlmostEqual(x + xs.mean(), 150, delta=1.5)
            self.assertAlmostEqual(y + ys.mean(), 250, delta=1.5)
        self.assertLess(frames[8][0].width, frames[12][0].width)
        # Squared ramps: 1/3 in on the first frame, (3/5)^3 out two frames into the 5-frame retreat, after the ring.
        self.assertAlmostEqual(np.asarray(frames[0][0])[..., 3].max(), 255 / 9, delta=1)
        self.assertAlmostEqual(np.asarray(frames[17][0])[..., 3].max(), 255 * 0.6 ** 6, delta=1)

    def test_icon_pop_ends_on_the_still_with_no_overlap(self):
        helpers.rect_png(self.dir / "icon.png", (40, 30), (0, 0, 40, 30), (250, 200, 0, 255))
        layers, _ = self.render_cli([{"type": "icon_pop", "name": "pop", "png": "icon.png", "x": 100, "y": 150,
                                      "frame": 10, "until": 40}])
        pop = layers["pop"]
        self.assertEqual(pop["frames"], [10, 15])
        self.assertEqual(pop["still"]["startTime"], pop["layer"]["endTime"])
        self.assertEqual((pop["still"]["startTime"], pop["still"]["endTime"]), (0.5, 1.333))
        self.assertEqual([pop["still"][k] for k in ("x", "y", "width", "height")], ["100", "150", "40", "30"])
        _, frames, _, _ = rt.render({"type": "icon_pop", "name": "pop", "png": "icon.png", "x": 100, "y": 150, "frame": 0},
                                    self.ctx())
        last, offset = frames[-1]
        self.assertEqual(offset, (100, 150))
        self.assertEqual(np.asarray(last).tolist(), np.asarray(Image.open(self.dir / "icon.png")).tolist())

    def test_fly_to_hud_reports_the_first_landing(self):
        helpers.rect_png(self.dir / "coin.png", (20, 20), (2, 2, 18, 18), (250, 200, 0, 255))
        el = {"type": "fly_to_hud", "name": "fly", "icon": "coin.png", "frame": 30, "from": [120, 330], "to": [60, 60],
              "icon_px": 20}
        first, frames, meta, _ = rt.render(el, self.ctx())
        self.assertEqual(meta["land"], 42)  # 0.4 s flight at 30 fps
        self.assertEqual(len(frames), round((2 * 0.045 + 0.4 + 0.24) * 30))
        box = rt.union(frames)
        self.assertTrue(box[0] <= 60 and box[1] <= 60 and box[2] >= 120 and box[3] >= 330)

    def test_progress_bar_fills_after_a_step(self):
        el = {"type": "progress", "name": "bar", "box": [40, 100, 160, 24], "fractions": [0.1, 0.9], "steps": [5],
              "start": 0, "end": 20}
        first, frames, _, _ = rt.render(el, self.ctx())

        def fill(n):
            a = np.asarray(frames[n][0]).astype(int)
            return int(((a[..., 1] > 150) & (a[..., 0] < 230) & (a[..., 2] < 120)).sum())

        self.assertGreater(fill(19), 4 * fill(4))
        self.assertGreater(fill(19), fill(7))

    def test_floater_out_of_the_zone_warns(self):
        helpers.rect_png(self.dir / "plus.png", (30, 20), (0, 0, 30, 20))
        el = {"type": "floater", "name": "plus", "png": "plus.png", "events": [[0, 220, 120]]}
        _, _, _, warnings = rt.render(el, self.ctx())
        self.assertTrue(any("right of the safe edge 200" in w for w in warnings), warnings)
        self.assertTrue(any("above the safe top 40" in w for w in warnings), warnings)

    def test_group_draws_its_children_into_one_track(self):
        helpers.rect_png(self.dir / "plus.png", (20, 20), (0, 0, 20, 20))
        els = [{"type": "group", "name": "grp", "elements": [
            {"type": "floater", "name": "a", "png": "plus.png", "events": [[0, 40, 300]], "rise": 10},
            {"type": "floater", "name": "b", "png": "plus.png", "events": [[6, 200, 300]], "rise": 10}]}]
        layers, _ = self.render_cli(els)
        lay = layers["grp"]["layer"]
        self.assertEqual(layers["grp"]["frames"], [0, 24])
        self.assertLessEqual(int(lay["x"]), 30)
        self.assertGreaterEqual(int(lay["x"]) + int(lay["width"]), 210)


@unittest.skipUnless(helpers.HAS_FFMPEG, "needs ffmpeg and ffprobe")
class EncodeTests(Case):
    def counter(self, start, end):
        helpers.rect_png(self.dir / "c.png", CANVAS, (41, 51, 61, 63))
        return [{"type": "counter", "name": "counter", "values": ["c.png"], "steps": [], "start": start, "end": end}]

    def test_layer_is_floored_and_cropped_to_the_even_box(self):
        layers, _ = self.render_cli(self.counter(185, 298))
        lay = layers["counter"]["layer"]
        self.assertEqual((lay["startTime"], lay["endTime"]), (6.166, 9.933))
        self.assertEqual([lay[k] for k in ("x", "y", "width", "height")], ["40", "50", "22", "14"])
        self.assertEqual((lay["type"], lay["fit"], lay["mute"], lay["source"]), ("video", "fill", True, "counter.mov"))

    def test_track_is_prores_4444_with_alpha(self):
        self.render_cli(self.counter(0, 6))
        stream = helpers.video_stream(self.dir / "out/counter.mov")
        self.assertEqual(stream["codec_name"], "prores")
        self.assertTrue(stream["pix_fmt"].startswith("yuva"), stream["pix_fmt"])
        self.assertEqual((stream["width"], stream["height"], int(stream["nb_read_frames"])), (22, 14, 6))

    def test_a_shorter_rerender_keeps_no_stale_frames(self):
        self.render_cli(self.counter(0, 12))
        layers, _ = self.render_cli(self.counter(0, 4))
        self.assertEqual(int(helpers.video_stream(self.dir / "out/counter.mov")["nb_read_frames"]), 4)
        self.assertEqual(layers["counter"]["frames"], [0, 4])
        self.assertEqual(sorted(p.name for p in (self.dir / "out").iterdir()), ["counter.mov", "layers.json"])

    def test_only_rerenders_the_named_element_and_keeps_the_rest(self):
        helpers.rect_png(self.dir / "plus.png", (20, 20), (0, 0, 20, 20))
        els = self.counter(0, 6) + [{"type": "floater", "name": "plus", "png": "plus.png", "events": [[0, 100, 300]]}]
        self.render_cli(els)
        helpers.write_json(self.dir / "spec.json", {"canvas": CANVAS, "safe_zone": ZONE, "elements": els})
        result = helpers.run("render_tracks.py", self.dir / "spec.json", self.dir / "out", "--only", "plus")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("counter:", result.stdout)
        layers = json.loads((self.dir / "out/layers.json").read_text())["layers"]
        self.assertEqual(sorted(layers), ["counter", "plus"])

    def test_rays_background_is_opaque_h264(self):
        Image.new("RGB", CANVAS, (20, 60, 200)).save(self.dir / "bg.png")
        layers, _ = self.render_cli([{"type": "rays", "name": "rays", "background": "bg.png", "center": [120, 150],
                                      "start": 30, "end": 36}])
        stream = helpers.video_stream(self.dir / "out/rays.mp4")
        self.assertEqual((stream["codec_name"], stream["pix_fmt"], int(stream["nb_read_frames"])), ("h264", "yuv420p", 6))
        lay = layers["rays"]["layer"]
        self.assertEqual((lay["fit"], lay["width"], lay["height"], lay["startTime"], lay["endTime"]),
                         ("cover", "240", "400", 1.0, 1.2))

    def test_missing_key_fails_with_the_element_name(self):
        helpers.write_json(self.dir / "spec.json", {"canvas": CANVAS, "elements": [{"type": "burst", "name": "boom", "frame": 3}]})
        result = helpers.run("render_tracks.py", self.dir / "spec.json", self.dir / "out")
        self.assertEqual(result.returncode, 2)
        self.assertIn("boom: missing key 'center'", result.stderr)


class HelpTests(unittest.TestCase):
    def test_every_script_has_help(self):
        for script in ("render_tracks.py", "build_passes.py", "check_master.py", "make_patch.py"):
            result = helpers.run(script, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
