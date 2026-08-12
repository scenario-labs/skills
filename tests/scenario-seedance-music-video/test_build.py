"""The delivery contract: full coverage, exact frames, untouched master."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import make_clip, make_master, probe_json, write_edit

import build


class BuildTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.master = make_master(self.root / "master.mp3", 4.0)
        self.a = make_clip(self.root / "a.mp4", 3.0, "blue")
        self.b = make_clip(self.root / "b.mp4", 3.0, "red")

    def tearDown(self) -> None:
        self._temp.cleanup()

    def plan_for(self, shots: list[dict], **extra) -> dict:
        edit = write_edit(self.root / "edit.json", "master.mp3", shots, **extra)
        return build.plan(build.load_edit(edit), self.root)

    # planning

    def test_spans_cover_the_master_with_no_gaps(self) -> None:
        job = self.plan_for([{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 2.0}])
        spans = [shot["span"] for shot in job["shots"]]
        self.assertEqual(sum(spans), job["total_frames"])
        self.assertEqual(job["shots"][0]["start_frame"], 0)
        self.assertEqual(job["shots"][1]["start_frame"], spans[0])

    def test_visuals_cover_a_master_that_ends_mid_frame(self) -> None:
        job = self.plan_for([{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 2.0}])
        # Ceiling, so the picture may end under one frame after the audio, never before it.
        self.assertGreaterEqual(job["total_frames"] / job["fps"], job["master_duration"])
        self.assertLess(job["total_frames"] / job["fps"] - job["master_duration"], 1 / job["fps"])

    def test_first_shot_must_start_at_zero(self) -> None:
        with self.assertRaisesRegex(build.BuildError, "must start at 0"):
            self.plan_for([{"clip": "a.mp4", "at": 0.5}])

    def test_shot_times_must_increase(self) -> None:
        with self.assertRaisesRegex(build.BuildError, "must increase"):
            self.plan_for([{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 0}])

    def test_last_shot_cannot_start_after_the_master_ends(self) -> None:
        with self.assertRaisesRegex(build.BuildError, "end of the master"):
            self.plan_for([{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 99.0}])

    def test_a_clip_too_short_for_its_slot_is_rejected(self) -> None:
        short = make_clip(self.root / "short.mp4", 0.5)
        with self.assertRaisesRegex(build.BuildError, "needs"):
            self.plan_for([{"clip": short.name, "at": 0}, {"clip": "b.mp4", "at": 3.0}])

    def test_head_trim_is_counted_against_available_frames(self) -> None:
        with self.assertRaisesRegex(build.BuildError, "needs"):
            self.plan_for([{"clip": "a.mp4", "at": 0, "in": 2.5}, {"clip": "b.mp4", "at": 2.0}])

    def test_missing_clip_is_reported(self) -> None:
        with self.assertRaisesRegex(build.BuildError, "clip not found"):
            self.plan_for([{"clip": "nope.mp4", "at": 0}])

    def test_missing_master_is_reported(self) -> None:
        edit = write_edit(self.root / "edit.json", "nope.mp3", [{"clip": "a.mp4", "at": 0}])
        with self.assertRaisesRegex(build.BuildError, "master not found"):
            build.plan(build.load_edit(edit), self.root)

    def test_edit_file_needs_shots(self) -> None:
        edit = self.root / "empty.json"
        edit.write_text('{"master": "master.mp3", "shots": []}')
        with self.assertRaisesRegex(build.BuildError, "at least one shot"):
            build.load_edit(edit)

    # building

    def test_end_to_end_copies_the_master_bit_for_bit(self) -> None:
        edit = write_edit(
            self.root / "edit.json", "master.mp3",
            [{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 2.0}],
        )
        out = self.root / "out.mp4"
        report = build.build(edit, out, self.root)

        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["detail"]["audio_mode"], "copy")
        self.assertTrue(report["checks"]["audio_bit_exact"])
        self.assertTrue(report["checks"]["master_untouched"])
        self.assertEqual(report["detail"]["frames"], report["detail"]["expected_frames"])

        info = probe_json(out)
        kinds = [s["codec_type"] for s in info["streams"]]
        self.assertEqual(sorted(kinds), ["audio", "video"])

    def test_head_trim_shifts_which_frames_are_used(self) -> None:
        edit = write_edit(
            self.root / "edit.json", "master.mp3",
            [{"clip": "a.mp4", "at": 0, "in": 0.5}, {"clip": "b.mp4", "at": 2.0}],
        )
        report = build.build(edit, self.root / "out.mp4", self.root)
        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["shots"][0]["head_trim_frames"], 12)

    def test_a_master_mp4_cannot_carry_is_encoded_once(self) -> None:
        make_master(self.root / "master.wav", 4.0, codec="wav")
        edit = write_edit(
            self.root / "edit.json", "master.wav",
            [{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 2.0}],
        )
        report = build.build(edit, self.root / "out.mp4", self.root)
        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["detail"]["audio_mode"], "aac_320k")
        self.assertTrue(report["checks"]["audio_encoded_once"])

    def test_clips_of_a_different_size_are_conformed(self) -> None:
        odd = make_clip(self.root / "odd.mp4", 3.0, "green", size="640x360")
        edit = write_edit(
            self.root / "edit.json", "master.mp3",
            [{"clip": "a.mp4", "at": 0}, {"clip": odd.name, "at": 2.0}],
        )
        out = self.root / "out.mp4"
        report = build.build(edit, out, self.root)
        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["detail"]["size"], "320x240")

    def test_cli_returns_zero_and_writes_the_file(self) -> None:
        edit = write_edit(
            self.root / "edit.json", "master.mp3",
            [{"clip": "a.mp4", "at": 0}, {"clip": "b.mp4", "at": 2.0}],
        )
        out = self.root / "cli.mp4"
        self.assertEqual(build.main([str(edit), str(out)]), 0)
        self.assertTrue(out.is_file())

    def test_cli_reports_a_bad_edit_without_raising(self) -> None:
        edit = write_edit(self.root / "edit.json", "master.mp3", [{"clip": "a.mp4", "at": 1.0}])
        self.assertEqual(build.main([str(edit), str(self.root / "cli.mp4")]), 1)


if __name__ == "__main__":
    unittest.main()
