"""build_passes.py: picture and sound payloads, music splits, the layer cap, and the local sum."""

import io
import json
import math
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

import helpers

bp = helpers.load("build_passes")

TRACKS = {"fps": 30, "canvas": [1080, 1920], "layers": {
    "hand": {"file": "hand.mov", "frames": [3, 28], "layer": {
        "type": "video", "source": "hand.mov", "x": "720", "y": "680", "width": "360", "height": "460", "fit": "fill",
        "mute": True, "startTime": 0.1, "endTime": 0.933}},
    "pop": {"file": "pop.mov", "frames": [333, 338], "layer": {}, "still": {
        "type": "image", "source": "icon.png", "x": "287", "y": "271", "width": "506", "height": "506", "fit": "fill",
        "startTime": 11.266, "endTime": 15.0}}}}


class Case(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        bp._audio.clear()

    def plan(self, **raw):
        data = {"fps": 30, "canvas": [1080, 1920], "duration": 15.0, **raw}
        helpers.write_json(self.dir / "plan.json", data)
        return bp.Plan(self.dir / "plan.json")


class TimeTests(unittest.TestCase):
    def test_times_round_down_to_the_millisecond(self):
        self.assertEqual(bp.frame_ms(185, 30), 6.166)
        self.assertEqual(bp.floor_ms(6.1667), 6.166)
        self.assertEqual(bp.floor_ms(0.3), 0.3)

    def test_volume_is_linear_with_three_decimals_and_capped(self):
        self.assertEqual(bp.volume(-6), 0.501)
        self.assertEqual(bp.volume(-10), 0.316)
        self.assertEqual(bp.volume(0), 1.0)
        self.assertEqual(bp.volume(10), 2.0)


class PictureTests(Case):
    def setUp(self):
        super().setUp()
        helpers.write_json(self.dir / "layers.json", TRACKS)
        helpers.rect_png(self.dir / "fail.png", (591, 355), (0, 0, 591, 355))
        helpers.rect_png(self.dir / "small.png", (750, 107), (0, 0, 750, 107))

    def test_picture_payload_maps_uploads_and_mutes_every_video(self):
        plan = self.plan(tracks="layers.json", assets={"fail.mp4": "A1", "hand.mov": "A2", "fail.png": "A3", "icon.png": "A4",
                                                         "small.png": "A5"},
                         picture=[{"file": "clips/fail.mp4", "type": "video", "start": 0, "end": 185, "trimEnd": 2.8},
                                  {"track": "hand", "zIndex": 20},
                                  {"file": "fail.png", "type": "image", "x": 244, "y": 400, "start": 72, "end": 108,
                                   "transitionIn": "zoomin", "transitionDuration": 0.2},
                                  {"still": "pop"},
                                  {"file": "small.png", "type": "image", "x": 165, "y": 659, "start": 339, "end": 450}])
        payload, notes = bp.picture_payload(plan)
        clip, hand, word, still, small = payload["layers"]
        self.assertEqual(clip, {"source": "A1", "startTime": 0.0, "endTime": 6.166, "x": "0", "y": "0", "width": "1080",
                                "height": "1920", "fit": "cover", "type": "video", "trimEnd": 2.8, "mute": True, "zIndex": 0})
        self.assertEqual((hand["source"], hand["zIndex"], hand["startTime"], hand["mute"]), ("A2", 20, 0.1, True))
        self.assertEqual([word[k] for k in ("source", "x", "y", "width", "height", "fit", "startTime", "endTime")],
                         ["A3", "244", "400", "591", "355", "fill", 2.4, 3.6])
        self.assertEqual((still["source"], still["startTime"], still["zIndex"]), ("A4", 11.266, 3))
        self.assertEqual((small["width"], small["height"]), ("750", "107"))
        self.assertTrue(any("under 300 px" in n for n in notes))
        self.assertEqual((payload["compressionLevel"], payload["duration"], payload["canvasHeight"]), (15, 15.0, 1920))
        self.assertFalse(any(lay["type"] == "audio" for lay in payload["layers"]))

    def test_a_layer_with_no_upload_fails_with_its_name(self):
        helpers.write_json(self.dir / "plan.json", {"duration": 15, "tracks": "layers.json", "assets": {},
                                                    "picture": [{"track": "hand"}]})
        result = helpers.run("build_passes.py", "picture", self.dir / "plan.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no asset id for hand.mov", result.stderr)


@unittest.skipUnless(helpers.HAS_FFMPEG, "needs ffmpeg")
class SoundTests(Case):
    def setUp(self):
        super().setUp()
        helpers.write_wav(self.dir / "music.wav", helpers.tone(4.0, amp=0.1))
        helpers.write_wav(self.dir / "bed.wav", helpers.tone(2.0, amp=0.05, freq=200))
        helpers.write_wav(self.dir / "hit.wav", helpers.burst(0.2, amp=0.5))
        self.assets = {"music.wav": "M", "bed.wav": "B", "hit.wav": "H"}

    def test_music_splits_at_each_gain_step_with_offsets_and_10_ms_fades(self):
        plan = self.plan(assets=self.assets, sound={"master_db": -2, "music": [
            {"file": "music.wav", "offset": 0.5, "end": 3.0, "gains": [[0, -4], [1.0, -8], [2.0, -10]], "fade_out_s": 0.6}],
            "hits": []})
        rows, _ = bp.sound_rows(plan)
        layers = [lay for _, _, _, lay in rows]
        self.assertEqual([(lay["startTime"], lay["endTime"], lay["trimStart"]) for lay in layers],
                         [(0.0, 1.0, 0.5), (1.0, 2.0, 1.5), (2.0, 3.0, 2.5)])
        self.assertEqual([lay["volume"] for lay in layers], [0.501, 0.316, 0.251])
        self.assertEqual([(lay["audioFadeIn"], lay["audioFadeOut"]) for lay in layers], [(0.01, 0.01), (0.01, 0.01), (0.01, 0.6)])
        self.assertEqual({lay["source"] for lay in layers}, {"M"})

    def test_hits_take_frame_times_trims_and_their_own_length(self):
        plan = self.plan(assets=self.assets, sound={"master_db": -4, "hits": [
            {"label": "tap", "file": "hit.wav", "frame": 185, "gain_db": -2, "trim_db": -1, "trimStart": 0.06}]})
        (_, label, _, lay), = bp.sound_rows(plan)[0]
        self.assertEqual(label, "tap")
        self.assertEqual(lay, {"source": "H", "type": "audio", "startTime": 6.166, "endTime": 6.306, "volume": 0.447,
                               "trimStart": 0.06})

    def test_past_49_audio_layers_the_bed_is_dropped_first(self):
        hits = [{"file": "hit.wav", "t": 0.25 * k} for k in range(48)]
        plan = self.plan(assets=self.assets, sound={"music": [{"file": "music.wav", "gains": [[0, -10]]}],
                                                    "beds": [{"file": "bed.wav", "t": 1.0}], "hits": hits})
        rows, notes = bp.sound_rows(plan)
        self.assertEqual(len(rows), 49)
        self.assertNotIn("bed", [role for role, _, _, _ in rows])
        self.assertTrue(any("bed" in n for n in notes))
        payload, cues, _ = bp.sound_payload(plan, "SILENT")
        self.assertEqual(len(payload["layers"]), 50)
        self.assertEqual(payload["layers"][0]["source"], "SILENT")

    def test_more_hits_than_the_cap_fail(self):
        plan = self.plan(assets=self.assets, sound={"hits": [{"file": "hit.wav", "t": 0.2 * k} for k in range(50)]})
        with self.assertRaises(bp.PlanError):
            bp.sound_rows(plan)

    def test_hit_margin_honors_the_per_hit_trim(self):
        def margin(**hit):
            plan = self.plan(sound={"master_db": -3, "music": [{"file": "music.wav", "gains": [[0, 0]]}],
                                    "hits": [{"label": "hit", "file": "hit.wav", "t": 1.0, **hit}]})
            with redirect_stdout(io.StringIO()):
                return bp.simulate(plan, self.dir / "sim.wav")["hits"][0]["margin_db"]

        plain = margin()
        self.assertAlmostEqual(plain, 20 * math.log10(0.5 / 0.1), delta=0.3)
        self.assertAlmostEqual(margin(trim_db=-3), plain - 3, delta=0.05)
        self.assertAlmostEqual(margin(gain_db=-2, trim_db=-1.5), plain - 3.5, delta=0.05)

    def test_simulate_sums_with_no_limiter(self):
        plan = self.plan(duration=2.0, sound={"hits": [{"label": "a", "file": "hit.wav", "t": 0.5, "gain_db": 1.584},
                                                       {"label": "b", "file": "hit.wav", "t": 0.5, "gain_db": 1.584}]})
        out = io.StringIO()
        with redirect_stdout(out):
            report = bp.simulate(plan, self.dir / "sim.wav")
        peak = float(np.abs(bp.load_audio(self.dir / "sim.wav")).max())
        self.assertAlmostEqual(peak, 1.2, delta=0.01)
        self.assertGreater(report["true_peak"], 1.0)
        self.assertIn("over -1 dBFS at   0.50 s: a, b", out.getvalue())

    def test_sound_command_writes_the_payload_and_cues(self):
        helpers.write_json(self.dir / "plan.json", {"duration": 5, "sections": [0, 2], "assets": self.assets, "sound": {
            "hits": [{"label": "tap", "file": "hit.wav", "frame": 30, "trimStart": 0.02}]}})
        result = helpers.run("build_passes.py", "sound", self.dir / "plan.json", "SILENT")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads((self.dir / "payload_sound.json").read_text())
        cues = json.loads((self.dir / "cues.json").read_text())
        self.assertEqual([lay["type"] for lay in payload["layers"]], ["video", "audio"])
        self.assertEqual(payload["compressionLevel"], 18)
        self.assertEqual(cues["sections"], [0, 2])
        (cue,) = cues["cues"]
        self.assertEqual((cue["t"], cue["trimStart"], cue["role"]), (1.0, 0.02, "hit"))
        self.assertTrue(Path(cue["file"]).is_absolute())


if __name__ == "__main__":
    unittest.main()
