"""Runs the specialists' host-side Python on planted inputs, with no After Effects installed.

These scripts read what After Effects renders or what a person hands over (a transcript, a beat
list, a cut sheet, a delivered file, PNG frames, a tracked path) and write numbers a job applies
or a person reads. ffmpeg, ffprobe and ImageMagick answers are canned where the parsing is what
counts; the ffmpeg cases that need a real file skip without ffmpeg.
"""

import contextlib
import gc
import io
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import warnings
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
SCRIPTS = {
    "word_timings": FAMILY / "scenario-after-effects-typography" / "scripts",
    "adtools": FAMILY / "scenario-after-effects-motion-production" / "scripts",
    "delivery_check": FAMILY / "scenario-after-effects-color-delivery" / "scripts",
    "audio_to_mouth": FAMILY / "scenario-after-effects-character-rigging" / "scripts",
    "matte_metrics": FAMILY / "scenario-after-effects-compositing" / "scripts",
    "track_external": FAMILY / "scenario-after-effects-tracking" / "scripts",
}
for folder in sorted(set(SCRIPTS.values())):
    sys.path.insert(0, str(folder))

import adtools  # noqa: E402
import audio_to_mouth  # noqa: E402
import delivery_check  # noqa: E402
import matte_metrics  # noqa: E402
import track_external  # noqa: E402


def resource_warnings(fn, *args, **kw):
    """Call fn, collect garbage, and return (ResourceWarning texts, result or the SystemExit code)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        try:
            result = fn(*args, **kw)
        except SystemExit as stop:
            result = stop.code
        gc.collect()
    return [str(w.message) for w in caught if issubclass(w.category, ResourceWarning)], result


def call_main(module, *argv):
    """Run module.main() with argv; return (leaks, exit code or result, stdout)."""
    out = io.StringIO()
    with unittest.mock.patch.object(sys, "argv", [module.__name__ + ".py", *argv]), contextlib.redirect_stdout(out):
        leaks, code = resource_warnings(module.main)
    return leaks, code, out.getvalue()


class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ae_specialists_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write_json(self, name, data):
        path = self.tmp / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)


class WordTimings(Temp):
    TRANSCRIPT = {"segments": [
        {"words": [{"word": " Meet", "start": 0.10, "end": 0.40}, {"word": " the", "start": 0.42, "end": 0.50},
                   {"word": " new", "start": 0.52, "end": 0.80}, {"word": " phone.", "start": 0.82, "end": 1.30}]},
        {"words": [{"word": " Order", "start": 1.90, "end": 2.20}, {"word": " today", "start": 2.22, "end": 2.70}]},
    ]}

    def run_script(self, *argv):
        script = SCRIPTS["word_timings"] / "word_timings.py"
        return subprocess.run([sys.executable, "-W", "error::ResourceWarning", str(script), *argv],
                              capture_output=True, text=True, timeout=60)

    def test_words_become_frames_with_a_one_frame_lead_and_phrases(self):
        src = self.write_json("t.json", self.TRANSCRIPT)
        run = self.run_script(src, "--fps", "30")
        self.assertEqual(run.returncode, 0, run.stderr)
        res = json.loads(run.stdout)
        self.assertEqual([w["f0"] for w in res["words"]], [2, 12, 15, 24, 56, 66])
        self.assertEqual([p["text"] for p in res["phrases"]], ["Meet the new phone.", "Order today"])
        self.assertTrue(res["checks"]["increasing"])
        self.assertEqual(res["checks"]["short"], ["the"])
        self.assertEqual(res["words"][-1]["frames"], 81 - 66)

    def test_out_file_and_silence_cross_check(self):
        src = self.write_json("t.json", self.TRANSCRIPT)
        log = self.tmp / "silence.log"
        log.write_text("[silencedetect @ 0x1] silence_start: 1.35\n[silencedetect @ 0x1] silence_end: 1.88 | silence_duration: 0.53\n",
                       encoding="utf-8")
        out = self.tmp / "timings.json"
        run = self.run_script(src, "--fps", "30", "--silence", str(log), "--out", str(out))
        self.assertEqual(run.returncode, 0, run.stderr)
        checks = json.loads(run.stdout)
        self.assertEqual(checks["phrase_onset_vs_silence_end_frames"], [0.6])
        self.assertTrue(checks["silence_agrees"])
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["checks"], checks)

    def test_flat_word_list_and_empty_transcript(self):
        flat = self.write_json("flat.json", [{"word": "Hi", "start": 0, "end": 0.5}])
        self.assertEqual(json.loads(self.run_script(flat, "--fps", "24", "--lead", "0").stdout)["words"][0]["f1"], 12)
        empty = self.write_json("empty.json", {"segments": []})
        run = self.run_script(empty)
        self.assertEqual(run.returncode, 1)
        self.assertIn("no words with timestamps", run.stderr)


class AdTools(Temp):
    def test_grid_beats_in_seconds_and_frames(self):
        g = adtools.grid(120, 0.1, 2.0, 30)
        self.assertEqual(g["beats_s"], [0.1, 0.6, 1.1, 1.6])
        self.assertEqual(g["beats_f"], [3.0, 18.0, 33.0, 48.0])

    def test_detect_reads_silencedetect_onsets(self):
        log = "silence_start: 0.2\nsilence_end: 0.5 | x\nsilence_start: 0.7\nsilence_end: 1.0 | x\nsilence_start: 1.2\nsilence_end: 1.5 | x\n"
        with unittest.mock.patch.object(adtools, "run", return_value=log) as run:
            res = adtools.detect("drums.wav", 30)
        self.assertIn("silencedetect=noise=-30.0dB:d=0.05", run.call_args[0][0])
        self.assertEqual(res["beats_s"], [0.0, 0.5, 1.0, 1.5])
        self.assertEqual(res["bpm_est"], 120.0)

    def test_snap_moves_cuts_onto_beats_within_limits(self):
        sheet = {"frames": 120, "shots": [{"id": "a", "f0": 0, "f1": 31}, {"id": "b", "f0": 31, "f1": 62}, {"id": "c", "f0": 62, "f1": 100}],
                 "endcard": {"f0": 100}}
        beats = {"beats_f": [0.0, 30.0, 60.0, 90.0, 99.0]}
        snapped, rows = adtools.snap(sheet, beats, max_shift=8, min_shot=18)
        self.assertEqual([r["to"] for r in rows], [30, 60, 99])
        self.assertTrue(all(r["snapped"] for r in rows))
        self.assertEqual(snapped["shots"][0]["f1"], 30)
        self.assertEqual(snapped["shots"][-1]["f1"], 99)

    def test_snap_refuses_a_shift_past_the_limit(self):
        sheet = {"frames": 90, "shots": [{"id": "a", "f0": 0, "f1": 40}, {"id": "b", "f0": 40, "f1": 90}]}
        _, rows = adtools.snap(sheet, {"beats_f": [0.0, 30.0, 60.0]}, max_shift=8)
        self.assertEqual(rows[0]["to"], 40)
        self.assertFalse(rows[0]["snapped"])

    def test_loudness_summary_is_parsed(self):
        text = "...\nSummary:\n\n  Integrated loudness:\n    I:         -14.3 LUFS\n  Loudness range:\n    LRA:         5.1 LU\n" \
               "  True peak:\n    Peak:       -1.4 dBFS\n"
        with unittest.mock.patch.object(adtools, "run", return_value=text):
            res = adtools.loud("mix.wav")
        self.assertEqual((res["integrated_lufs"], res["lra_lu"], res["true_peak_dbtp"]), (-14.3, 5.1, -1.4))

    def test_zone_from_a_platform_overlay(self):
        with unittest.mock.patch.object(adtools, "run", return_value="880x1300+100+250 1080 1920\n"):
            res = adtools.zone("overlay.png", "feed", "test overlay")
        self.assertEqual(res["feed"]["px"], [100, 250, 980, 1550])
        self.assertEqual(res["feed"]["top"], round(250 / 1920, 5))

    def test_review_scores_a_report_and_the_cli_writes_json(self):
        rep = {"comp": "AD_30", "fps": 30, "hook_text_frame": 2, "first_cut_f": 40,
               "texts": [{"text": "Tap to play", "words": 3, "frames": 45}, {"text": "A very long line of seven words here", "words": 8, "frames": 40}],
               "cuts_per_10s": [{"window": "0-10 s", "cuts": 6}], "logo_first_f": 10, "cta_frames": 75, "endcard_frames": 90,
               "beat_offsets": [{"offset": 0.5}, {"offset": -2}], "zone_violations": [{"layer": "CTA", "zone": "feed"}]}
        res = adtools.review(rep)
        failed = sorted(r["check"].split(" (")[0] for r in res["rows"] if not r["pass"])
        self.assertEqual(failed, ["logo first frame", "safe-zone violations", "text 'A very long line of seven words here' frames",
                                  "worst cut-to-beat offset"])
        self.assertEqual(res["total"], 10)
        path = self.write_json("report.json", {"result": {"report": rep}})
        leaks, code, out = call_main(adtools, "review", path)
        self.assertEqual((leaks, code), ([], None))
        self.assertEqual(json.loads(out)["passed"], res["passed"])

    def test_snap_cli_reads_and_writes_files_closed(self):
        sheet = self.write_json("sheet.json", {"frames": 60, "shots": [{"id": "a", "f0": 0, "f1": 31}, {"id": "b", "f0": 31, "f1": 60}]})
        beats = self.write_json("beats.json", {"beats_f": [0.0, 30.0]})
        out = self.tmp / "snapped.json"
        leaks, code, stdout = call_main(adtools, "snap", sheet, beats, "--out", str(out), "--min-shot", "10")
        self.assertEqual((leaks, code), ([], None))
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["shots"][1]["f0"], 30)
        self.assertEqual(json.loads(stdout)["out"], str(out))


def mp4_atoms(*kinds):
    """A minimal ISO media file: one 16-byte box per kind, in order."""
    return b"".join(struct.pack(">I4s", 16, kind.encode()) + b"\0" * 8 for kind in kinds)


VIDEO = {"codec_type": "video", "codec_name": "h264", "profile": "High", "width": 1080, "height": 1920,
         "avg_frame_rate": "30/1", "pix_fmt": "yuv420p", "nb_frames": "60",
         "color_primaries": "bt709", "color_transfer": "bt709", "color_space": "bt709", "color_range": "tv"}


class DeliveryCheck(Temp):
    def test_fast_start_order_from_the_atoms(self):
        cases = {"fast.mp4": (("ftyp", "moov", "mdat"), True), "slow.mp4": (("ftyp", "mdat", "moov"), False), "none.mp4": (("ftyp",), None)}
        for name, (kinds, expected) in cases.items():
            path = self.tmp / name
            path.write_bytes(mp4_atoms(*kinds))
            leaks, found = resource_warnings(delivery_check.moov_first, str(path))
            self.assertEqual((leaks, found), ([], expected), name)

    def test_rate_and_bit_depth(self):
        self.assertAlmostEqual(delivery_check.rate("30000/1001"), 29.97, places=2)
        self.assertEqual(delivery_check.rate("0/0"), 0.0)
        self.assertEqual(delivery_check.bit_depth({"pix_fmt": "yuv422p10le"}), 10)
        self.assertEqual(delivery_check.bit_depth({"bits_per_raw_sample": "12", "pix_fmt": "yuv420p"}), 12)
        self.assertEqual(delivery_check.bit_depth({"pix_fmt": "yuv420p"}), 8)

    def test_spec_rows_pass_and_fail_on_a_canned_probe(self):
        path = self.tmp / "ad.mp4"
        path.write_bytes(mp4_atoms("ftyp", "moov", "mdat"))
        info = {"streams": [VIDEO], "format": {"duration": "2.0"}}
        spec = {"file": str(path), "codec": "h264", "width": 1080, "height": 1920, "fps": 30, "frames": 60, "duration": 2.0,
                "alpha": False, "color": {"primaries": "bt709", "range": "pc"}, "faststart": True, "max_mb": 1, "no_audio": True}
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=info):
            rows = delivery_check.check(spec)
        failed = [r["check"] for r in rows if not r["pass"]]
        self.assertEqual(failed, ["color range"])
        self.assertEqual(len(rows), 12)

    def test_image_sequence_gaps_and_first_number(self):
        for n in (1, 2, 4):
            (self.tmp / ("shot_%05d.png" % n)).write_bytes(b"png")
        spec = {"file": str(self.tmp / "shot_%05d.png"), "sequence_start": 0, "alpha": True}
        info = {"streams": [dict(VIDEO, codec_name="png", pix_fmt="rgba")], "format": {}}
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=info):
            rows = {r["check"]: r for r in delivery_check.check(spec)}
        self.assertEqual(rows["gaps"]["measured"], 1)
        self.assertEqual(rows["first number"]["measured"], 1)
        self.assertTrue(rows["alpha"]["pass"])

    def test_main_reports_and_exits_1_on_a_missing_file(self):
        spec = self.write_json("spec.json", [{"file": str(self.tmp / "missing.mov")}])
        report = self.tmp / "report.json"
        leaks, code, out = call_main(delivery_check, spec, "--json", str(report))
        self.assertEqual((leaks, code), ([], 1))
        self.assertIn("0 of 1 deliverables pass", out)
        self.assertFalse(json.loads(report.read_text(encoding="utf-8"))[0]["pass"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg and ffprobe")
    def test_real_render_through_ffprobe(self):
        path = self.tmp / "real.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=64x64:r=30:d=1", "-pix_fmt", "yuv420p",
                        "-c:v", "libx264", "-movflags", "+faststart", str(path)], check=True, timeout=120)
        rows = delivery_check.check({"file": str(path), "codec": "h264", "width": 64, "fps": 30, "frames": 30,
                                     "faststart": True, "levels": {"every": 10}})
        self.assertEqual([r["check"] for r in rows if not r["pass"]], [])


class AudioToMouth(Temp):
    def test_percentile_picks_from_sorted_values(self):
        self.assertEqual(audio_to_mouth.pct([], 50), 0.0)
        self.assertEqual(audio_to_mouth.pct([-40.0, -30.0, -20.0, -10.0, 0.0], 50), -20.0)

    def test_sample_rate_must_divide_into_frames(self):
        with self.assertRaises(SystemExit):
            audio_to_mouth.rms_per_frame("voice.wav", 23.976)

    def test_rms_levels_become_hold_keys(self):
        levels = [-120.0, -120.0, -20.0, -20.0, -20.0, -8.0, -8.0, -8.0, -60.0, -60.0]
        with unittest.mock.patch.object(audio_to_mouth, "rms_per_frame", return_value=levels):
            leaks, code, out = call_main(audio_to_mouth, "voice.wav", "--fps", "24", "--shapes", "3", "--lead", "1")
        self.assertEqual((leaks, code), ([], None))
        res = json.loads(out)
        # the one-frame lead pulls the first open shape onto frame 0: the later sound wins
        self.assertEqual(res["keys"], [[0, 1], [4, 2], [7, 0]])
        self.assertEqual(res["counts"], {"0": 4, "1": 3, "2": 3})


class MatteMetrics(Temp):
    def png(self, name, array):
        path = self.tmp / name
        Image.fromarray(array.astype(np.uint8)).save(path)
        return str(path)

    def args(self, **kw):
        return unittest.mock.Mock(**kw)

    def test_alpha_error_against_a_reference(self):
        ref = np.zeros((20, 20, 3))
        ref[5:15, 5:15] = 255
        render = ref.copy()
        render[0, 0] = 255
        res = matte_metrics.cmd_alpha(self.args(render=self.png("r.png", render), ref=self.png("t.png", ref), labels=None))
        self.assertEqual(res["stray_bg_pct"], round(1 / 300 * 100, 3))
        self.assertEqual(res["holes_core_pct"], 0.0)

    def test_spill_levels_and_diff_on_a_box(self):
        img = np.zeros((10, 10, 3))
        img[..., 1] = 200
        img[..., 0] = img[..., 2] = 100
        path = self.png("green.png", img)
        spill = matte_metrics.cmd_spill(self.args(img=path, labels=None, box="0,0,10,10"))
        self.assertAlmostEqual(spill["green_excess"], 100 / 255, places=3)
        levels = matte_metrics.cmd_levels(self.args(img=path, box="0,0,10,10"))
        self.assertEqual(levels["g"][1], round(200 / 255, 4))
        diff = matte_metrics.cmd_diff(self.args(a=path, b=self.png("black.png", np.zeros((10, 10, 3))), box=None))
        self.assertEqual(diff["max"], 200.0)

    def test_edge_width_of_a_ramp(self):
        row = np.tile(np.clip((np.arange(40) - 10) * 255 / 20, 0, 255), (3, 1))
        img = np.repeat(row[:, :, None], 3, axis=2)
        res = matte_metrics.cmd_edge(self.args(img=self.png("ramp.png", img), row=1, x0=0, x1=40))
        self.assertEqual(res["width_px"], 16)


class TrackExternal(Temp):
    def test_score_of_a_plane_track_against_truth(self):
        truth = [[[0, 0], [10, 0], [10, 10], [0, 10]], [[1, 0], [11, 0], [11, 10], [1, 10]]]
        track = [[[0, 0], [10, 0], [10, 10], [0, 10]], [[1, 3], [11, 4], [11, 10], [1, 10]]]
        leaks, res = resource_warnings(track_external.score, self.write_json("track.json", {"corners": track}),
                                       self.write_json("truth.json", {"corners": truth}))
        self.assertEqual(leaks, [])
        self.assertEqual(res["worstFrame"], 1)
        self.assertEqual(res["maxPx"], 4.0)
        self.assertEqual(res["perFrame"], [0.0, 1.75])

    def test_score_of_shake_is_relative_to_the_reference_frame(self):
        truth = {"shake": [[5, 5, 0.1], [7, 4, 0.3]]}
        track = {"shake": [[0, 0, 0], [2, -1, 0.2]], "ref": 0}
        res = track_external.score(self.write_json("s.json", track), self.write_json("u.json", truth))
        self.assertEqual((res["meanPx"], res["meanRotDeg"]), (0.0, 0.0))

    def test_analysis_banner_colors(self):
        frames = {"analyzing": (255, 0, 0), "stabilizing": (0, 128, 255), "none": (90, 90, 90)}
        for state, bgr in frames.items():
            img = np.zeros((100, 200, 3), np.uint8)
            img[45:52] = bgr
            path = self.tmp / (state + ".png")
            Image.fromarray(img[..., ::-1]).save(path)
            self.assertEqual(track_external.banner(str(path))["state"], state)


@unittest.skipUnless(shutil.which("magick"), "needs ImageMagick 7 (magick)")
class BandCheck(Temp):
    def test_hard_steps_show_few_levels_and_wide_runs(self):
        img = np.repeat(np.repeat(np.arange(0, 256, 32, dtype=np.uint8), 20)[None, :], 4, axis=0)
        path = self.tmp / "steps.png"
        Image.fromarray(img).save(path)
        script = SCRIPTS["delivery_check"] / "band_check.py"
        run = subprocess.run([sys.executable, str(script), str(path), "1"], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("8 levels", run.stdout)
        self.assertIn("widest flat run 20 px", run.stdout)


if __name__ == "__main__":
    unittest.main()
