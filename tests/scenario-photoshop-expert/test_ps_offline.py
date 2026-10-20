"""Offline tests for the Photoshop toolkits: the job guard, the JSX builder, delivery profiles,
the ExtendScript each toolkit sends, and their pure helpers.

None of these talk to Photoshop. Live behavior is recorded in the family README.
"""

import contextlib
import io
import os
import re
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAMILY = os.path.join(ROOT, "skills", "dcc", "photoshop")
SCRIPTS = os.path.join(FAMILY, "scenario-photoshop-expert", "scripts")
sys.path.insert(0, SCRIPTS)
for skill in ("compositing", "game-art", "generative-edit", "key-art", "mockups", "upscale-restore"):
    sys.path.insert(0, os.path.join(FAMILY, "scenario-photoshop-" + skill, "scripts"))

import ps_audit  # noqa: E402
import ps_composite  # noqa: E402
import ps_gameart  # noqa: E402
import ps_gates  # noqa: E402
import ps_generative  # noqa: E402
import ps_io  # noqa: E402
import ps_keyart  # noqa: E402
import ps_mockup  # noqa: E402
import ps_retouch  # noqa: E402
import ps_review  # noqa: E402
import ps_run  # noqa: E402
import ps_upscale  # noqa: E402

TOOLKITS = (ps_audit, ps_composite, ps_gameart, ps_gates, ps_generative, ps_io, ps_keyart, ps_mockup, ps_retouch,
            ps_review, ps_upscale)
# ES3 reserves the Java keywords too; ExtendScript rejects them as bare object keys
# ("Illegal use of reserved word 'native'", measured on 27.11).
# ExtendScript evaluates a ? b : c ? d : e as (a ? b : c) ? d : e (measured on 27.11: a left
# alignment came out right-aligned). Parenthesize or use if/else.
CHAINED_TERNARY = re.compile(r"\?[^;()\n]*:[^;()\n]*\?")
RESERVED_KEY = re.compile(
    r"[{,]\s*(abstract|boolean|byte|char|class|const|double|enum|export|extends|final|float|goto|"
    r"implements|import|int|interface|long|native|package|private|protected|public|short|static|"
    r"super|synchronized|throws|transient|volatile)\s*:")


class GuardTest(unittest.TestCase):
    def test_refuses_save_close_quit(self):
        for body in (
            "app.activeDocument.save();",
            "doc.saveAs(new File('/tmp/x.psd'));",
            "app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);",
            "d . close ( );",
            "app.quit();",
            "executeAction(charIDToTypeID('save'), d, DialogModes.NO);",
            'executeAction(stringIDToTypeID("close"), d, DialogModes.NO);',
        ):
            self.assertTrue(ps_run.lint(body), body)

    def test_allows_helpers_and_reads(self):
        for body in (
            "var d = psr_new_doc(10, 10); psr_close(d); return 1;",
            "psr_export(app.activeDocument, '/tmp/a.png', 'png');",
            "return app.activeDocument.layers.length;",
            "var closed = false; return closed;",
        ):
            self.assertEqual(ps_run.lint(body), [], body)

    def test_run_refuses_before_touching_photoshop(self):
        res = ps_run.run("app.activeDocument.save();", ps={"path": "/nonexistent", "name": "x",
                                                          "version": "0"})
        self.assertEqual(res["exit"], 2)
        self.assertIn("guard refused", res["error"])


class BuildTest(unittest.TestCase):
    def test_body_and_undo_name_are_embedded(self):
        js = ps_run.build("return 41 + 1;", undo='Scenario: "fill"')
        self.assertIn("return 41 + 1;", js)
        self.assertIn('"Scenario: \\"fill\\""', js)
        self.assertIn("suspendHistory", js)
        self.assertIn(ps_run.RESULT_TAG, js)

    def test_no_undo_is_null(self):
        self.assertIn("var undo = null;", ps_run.build("return 1;"))

    def test_failed_job_closes_its_temp_documents(self):
        js = ps_run.build("throw new Error('x');")
        self.assertIn("__psr_created", js.split("%BODY%")[0] if "%BODY%" in js else js)
        self.assertIn("DONOTSAVECHANGES", js)

    def test_prelude_avoids_unicode_class_escapes(self):
        # ExtendScript's regex engine rejects \u escapes in character classes (measured, 27.11).
        self.assertNotRegex(ps_run.PRELUDE, r"\[[^\]]*\\u[0-9a-fA-F]{4}")


def state(**kw):
    base = {"open": True, "width": 1920, "height": 1080, "ppi": 72, "mode": "rgb", "bits": 8,
            "profile": "sRGB IEC61966-2.1", "layers": []}
    base.update(kw)
    return base


class DeliverableTest(unittest.TestCase):
    def test_web_pass(self):
        self.assertEqual(ps_audit.deliverable("web", state()), [])

    def test_web_wrong_profile_and_bits(self):
        probs = ps_audit.deliverable("web", state(profile="Display P3", bits=16))
        self.assertTrue(any("profile" in p for p in probs))
        self.assertTrue(any("bit depth" in p for p in probs))

    def test_print_needs_ppi(self):
        self.assertTrue(ps_audit.deliverable("print", state(width=3000, height=2000, ppi=72)))
        self.assertEqual(ps_audit.deliverable("print", state(width=3000, height=2000, ppi=300)),
                         [])

    def test_game_texture_power_of_two(self):
        self.assertTrue(ps_audit.deliverable("game-texture", state(width=1000, height=1000)))
        self.assertEqual(ps_audit.deliverable("game-texture", state(width=1024, height=512)), [])

    def test_handoff_flags_names_hidden_empty_outside(self):
        layers = [
            {"name": "Layer 3", "kind": "pixel", "visible": True, "bounds": [0, 0, 10, 10]},
            {"name": "Hidden", "kind": "pixel", "visible": False, "bounds": [0, 0, 10, 10]},
            {"name": "Empty", "kind": "pixel", "visible": True, "bounds": [0, 0, 0, 0]},
            {"name": "Title", "kind": "text", "visible": True, "bounds": [100, 100, 2500, 300]},
            {"name": "Grp", "kind": "group", "visible": True, "bounds": [0, 0, 5, 5],
             "children": [{"name": "Group 2", "kind": "group", "visible": True, "bounds": None}]},
        ]
        probs = ps_audit.deliverable("psd-handoff", state(layers=layers))
        text = " | ".join(probs)
        self.assertIn("default layer names", text)
        self.assertIn("hidden", text)
        self.assertIn("empty", text)
        self.assertIn("past the canvas", text)

    def test_unknown_profile(self):
        self.assertIn("unknown profile", ps_audit.deliverable("nope", state())[0])

    def test_handoff_keeps_hidden_takes_in_a_takes_group(self):
        takes = {"name": "Takes", "kind": "group", "visible": False, "bounds": [0, 0, 5, 5],
                 "path": "/Takes", "children": [
                     {"name": "Iris, take 2", "kind": "smart_object", "visible": False,
                      "bounds": [0, 0, 5, 5], "path": "/Takes/Iris, take 2"}]}
        self.assertEqual(ps_audit.deliverable("psd-handoff", state(layers=[takes])), [])
        other = {"name": "Old", "kind": "pixel", "visible": False, "bounds": [0, 0, 5, 5], "path": "/Old"}
        probs = ps_audit.deliverable("psd-handoff", state(layers=[takes, other]))
        self.assertEqual(len(probs), 1)
        self.assertIn("1 hidden layers", probs[0])


def hist(index, name, prev, count, full=False, limit=50, id_=None, prev_id=None):
    return {"index": index, "name": name, "prev": prev, "count": count, "limit": limit,
            "full": full, "id": id_, "prev_id": prev_id}


class HistoryGateTest(unittest.TestCase):
    """The History gate reads the active state, never the list length (ps_audit.history_problems)."""

    def test_new_state_below_the_limit(self):
        h0 = hist(3, "Select", "Fill", 6)               # two redo states above the mark
        self.assertEqual(ps_audit.history_problems(h0, hist(4, "Scenario: Edit", "Select", 5), "Scenario: Edit"), [])

    def test_index_must_rise_below_the_limit(self):
        h0 = hist(3, "Select", "Fill", 4)
        self.assertTrue(ps_audit.history_problems(h0, hist(2, "Scenario: Edit", "Select", 3), "Scenario: Edit"))

    def test_at_the_limit_the_index_holds_still(self):
        h0 = hist(49, "Select", "Fill", 50, full=True)
        h1 = hist(49, "Scenario: Edit", "Select", 50, full=True)
        self.assertEqual(ps_audit.history_problems(h0, h1, "Scenario: Edit"), [])

    def test_missing_edit_fails(self):
        h0 = hist(49, "Select", "Fill", 50, full=True)
        self.assertTrue(ps_audit.history_problems(h0, h0, "Scenario: Edit"))
        with_ids = hist(49, "Scenario: Edit", "Scenario: Edit", 50, full=True, id_=7, prev_id=6)
        self.assertTrue(ps_audit.history_problems(with_ids, with_ids, "Scenario: Edit"))

    def test_twice_or_without_undo_fails(self):
        h0 = hist(10, "Select", "Fill", 11)
        twice = hist(12, "Scenario: Edit", "Scenario: Edit", 13)
        self.assertTrue(ps_audit.history_problems(h0, twice, "Scenario: Edit"))
        no_undo = hist(11, "New Layer", "Select", 12)
        self.assertTrue(ps_audit.history_problems(h0, no_undo, "Scenario: Edit"))

    def test_ids_decide_when_readable(self):
        h0 = hist(49, "Scenario: Edit", "Scenario: Edit", 50, full=True, id_=7, prev_id=6)
        ok = hist(49, "Scenario: Edit", "Scenario: Edit", 50, full=True, id_=8, prev_id=7)
        self.assertEqual(ps_audit.history_problems(h0, ok, "Scenario: Edit"), [])
        moved = hist(49, "Scenario: Edit", "Scenario: Edit", 50, full=True, id_=9, prev_id=8)
        self.assertTrue(ps_audit.history_problems(h0, moved, "Scenario: Edit"))

    def test_back_at_the_mark(self):
        h0 = hist(49, "Select", "Fill", 50, full=True)
        self.assertEqual(ps_audit.history_problems(h0, hist(47, "Select", "Fill", 50)), [])
        self.assertTrue(ps_audit.history_problems(h0, hist(48, "Fill", "Fill 2", 50)))
        below = hist(5, "Select", "Fill", 9)
        self.assertTrue(ps_audit.history_problems(below, hist(4, "Select", "Fill", 9)))
        self.assertEqual(ps_audit.history_problems(hist(5, "A", "B", 9, id_=3), hist(2, "A", "B", 9, id_=3)), [])


class FakeHistory:
    """A History panel behind ps_run.run, for ps_audit's own history and step_back jobs."""

    def __init__(self, states):
        self.states = [dict(s) for s in states]        # [{"name", "id"}], oldest first
        self.active = len(self.states) - 1

    def push(self, name, id_):
        del self.states[self.active + 1:]
        self.states.append({"name": name, "id": id_})
        self.active = len(self.states) - 1

    def _state(self):
        i = self.active
        prev = self.states[i - 1] if i > 0 else None
        return {"index": i, "name": self.states[i]["name"], "prev": prev and prev["name"],
                "id": self.states[i]["id"], "prev_id": prev and prev["id"], "count": len(self.states),
                "limit": 50, "full": False}

    def run(self, js, timeout=120, **kw):
        if "step_back:" in js:                           # STEP_BACK_JS: name check, one step down
            if self.states[self.active]["name"] not in js:
                return {"ok": False, "error": "step_back: the active History state is another"}
            self.active -= 1
        return {"ok": True, "result": self._state()}


def recover(h0, undo):
    """The lead's recovery rule (scenario-photoshop-expert SKILL.md, Quality gates)."""
    probs = ps_audit.history_gate(h0, undo)
    if probs == []:
        ps_audit.step_back(h0, undo)
        return "stepped back"
    if any("no new History state" in p for p in probs):
        return "run again"
    return "stop"


class RecoveryTest(unittest.TestCase):
    """Two calls with the same undo name, the second failing: History decides, never the name."""

    UNDO = "Scenario: Match grain"

    def setUp(self):
        self.saved = ps_audit.ps_run.run
        self.h = FakeHistory([{"name": "Lasso", "id": 209}, {"name": self.UNDO, "id": 330}])
        ps_audit.ps_run.run = self.h.run

    def tearDown(self):
        ps_audit.ps_run.run = self.saved

    def test_a_failure_before_any_change_keeps_the_finished_edit(self):
        h0 = ps_audit.history()                          # the first element's grain, finished
        # The second match_grain raises before any state (a refused name, a timeout in a read).
        self.assertEqual(ps_audit.history()["name"], self.UNDO, "a name check alone would step back")
        self.assertIn("no new History state: the marked state is still active",
                      ps_audit.history_gate(h0, self.UNDO))
        self.assertEqual(recover(h0, self.UNDO), "run again")
        self.assertEqual(ps_audit.history()["id"], 330, "the first edit is still active")
        # Stepping back here undoes the finished edit, and only then raises.
        with self.assertRaises(RuntimeError):
            ps_audit.step_back(h0, self.UNDO)
        self.assertEqual(ps_audit.history()["name"], "Lasso")

    def test_a_failure_that_left_its_state_steps_back_to_the_mark(self):
        h0 = ps_audit.history()
        self.h.push(self.UNDO, 331)                      # the second call left a partial state
        self.assertEqual(recover(h0, self.UNDO), "stepped back")
        self.assertEqual(ps_audit.history()["id"], h0["id"])

    def test_anything_else_stops(self):
        h0 = ps_audit.history()
        self.h.push(self.UNDO, 331)
        self.h.push("Brush Tool", 332)                   # the user painted meanwhile
        self.assertEqual(recover(h0, self.UNDO), "stop")
        self.assertEqual(ps_audit.history()["id"], 332, "nothing undone")


class ProvenanceTest(unittest.TestCase):
    def test_round_trip_escapes_markup(self):
        fields = {"assetId": "asset_x", "prompt": 'a "red" ball & <box>', "seed": "1"}
        xmp = ps_io.provenance_xmp(fields)
        self.assertNotIn('"red"', xmp)
        self.assertNotIn("<box>", xmp)
        self.assertEqual(ps_io.parse_xmp(xmp), dict(fields, schema="1"))

    def test_snake_case_keys_are_renamed_to_camel_case(self):
        xmp = ps_io.provenance_xmp({"asset_id": "a", "job_id": "j", "model": "m", "date": "d",
                                    "negative_prompt": "n"})
        self.assertEqual(ps_io.parse_xmp(xmp), {"schema": "1", "assetId": "a", "jobId": "j",
                                                "modelId": "m", "createdAt": "d",
                                                "negativePrompt": "n"})

    def test_skips_unsafe_keys_and_none(self):
        xmp = ps_io.provenance_xmp({"ok": "1", "bad key": "2", "x=y": "3", "none": None})
        self.assertEqual(ps_io.parse_xmp(xmp), {"schema": "1", "ok": "1"})

    def test_place_rejects_unknown_fit(self):
        with self.assertRaises(ValueError):
            ps_io.place("/nonexistent.png", "x", fit="stretch")


def job_scripts():
    for mod in TOOLKITS:
        for name, value in vars(mod).items():
            if name.endswith("_JS") and isinstance(value, str):
                yield "%s.%s" % (mod.__name__, name), value


class ToolkitJsTest(unittest.TestCase):
    def test_every_job_passes_the_guard(self):
        found = 0
        for where, js in job_scripts():
            found += 1
            self.assertEqual(ps_run.lint(js), [], where)
        self.assertGreater(found, 30)

    def test_no_reserved_word_keys(self):
        for where, js in job_scripts():
            self.assertIsNone(RESERVED_KEY.search(js), where)

    def test_no_chained_ternary(self):
        for where, js in job_scripts():
            self.assertIsNone(CHAINED_TERNARY.search(js), where)

    def test_every_toolkit_prints_help(self):
        for mod in TOOLKITS:
            if hasattr(mod, "main"):
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(mod.main(["--help"]), 0, mod.__name__)
                self.assertIn("Library", out.getvalue(), mod.__name__)


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, size = 8, b"", None
    while pos < len(data):
        n, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            size = struct.unpack(">II", body[:8])
        elif tag == b"IDAT":
            idat += body
        pos += 12 + n
    return size, zlib.decompress(idat)


class MockupHelpersTest(unittest.TestCase):
    def test_quad_size_averages_opposite_sides(self):
        self.assertEqual(ps_mockup.quad_size([[0, 0], [400, 0], [400, 300], [0, 300]]), (400, 300))
        self.assertEqual(ps_mockup.quad_size([[0, 0], [100, 0], [80, 50], [20, 50]]), (80, 54))

    def test_quad_needs_four_corners(self):
        with self.assertRaises(ValueError):
            ps_mockup.quad_size([[0, 0], [1, 0], [1, 1]])

    def test_cylinder_angle_and_colors_are_checked_before_photoshop(self):
        for angle in (0, 181, -10):
            with self.assertRaises(ValueError):
                ps_mockup.fit_cylinder("x", [[0, 0], [1, 0], [1, 1], [0, 1]], 5, angle=angle)
        self.assertEqual(ps_mockup._rgb("#1e3278"), [30, 50, 120])
        self.assertEqual(ps_mockup._rgb((1, 2, 3)), [1, 2, 3])
        for bad in ("#12345", "navy", (1, 2)):
            with self.assertRaises(ValueError):
                ps_mockup._rgb(bad)

    def test_tone_curve_gain_when_darkening_offset_when_lightening(self):
        white = {"mid": 227.0, "p99": 242}
        navy = ps_mockup.tone_curve(white, (30, 50, 120))
        self.assertEqual(navy[0], [0, 0.0])                    # a gain: black stays black
        self.assertAlmostEqual(navy[1][1] / 255, ps_mockup._lum((30, 50, 120)) / 227.0, places=3)
        black = {"mid": 35.0, "p99": 48}
        sand = ps_mockup.tone_curve(black, (230, 210, 160))
        k = (sand[1][1] - sand[0][1]) / (sand[1][0] - sand[0][0])
        self.assertAlmostEqual(k, 1.0)                          # an offset keeps fold contrast
        self.assertAlmostEqual(sand[0][1] + 35 * k, ps_mockup._lum((230, 210, 160)), places=1)
        capped = ps_mockup.tone_curve({"mid": 35.0, "p99": 120}, (245, 245, 245))
        k = (capped[1][1] - capped[0][1]) / (capped[1][0] - capped[0][0])
        self.assertLessEqual(capped[0][1] + 120 * k, 250.01)    # highlights stay under 250
        self.assertIsNone(ps_mockup.tone_curve({"mid": 120.0, "p99": 200}, (120, 120, 120)))

    def test_swatch_check_and_delta_e(self):
        self.assertEqual(ps_mockup.delta_e((30, 50, 120), (30, 50, 120)), 0)
        self.assertAlmostEqual(ps_mockup.delta_e((255, 255, 255), (0, 0, 0)), 100, places=0)
        base = [(v, v, v) for v in range(150, 250)]
        good = [(max(0, v - 200 + 30), max(0, v - 200 + 50), max(0, v - 200 + 120)) for v in range(150, 250)]
        r = ps_mockup.swatch_check(base, good, (30, 50, 120))
        self.assertLess(r["delta_e"], 2)
        self.assertGreater(r["folds"], 0.99)
        pale = [(min(255, v - 10), v, 255) for v in range(150, 250)]
        self.assertGreater(ps_mockup.swatch_check(base, pale, (30, 50, 120))["delta_e"], 20)
        flat = [(30, 50, 120)] * 100
        self.assertEqual(ps_mockup.swatch_check(base, flat, (30, 50, 120))["folds"], 0.0)
        tones = ps_mockup.garment_tones([ps_mockup._lum(p) for p in base])
        self.assertEqual(tones["pixels"], 100)
        self.assertTrue(tones["p25"] <= tones["mid"] <= tones["p75"])

    def test_lighter_swatch_is_flagged_flat(self):
        dark = [(v, v, v) for v in range(20, 52)]
        lifted = [(v + 175, v + 175, v + 175) for v in range(20, 52)]   # an offset: same depth
        r = ps_mockup.swatch_check(dark, lifted, (210, 210, 210))
        self.assertTrue(r["flat"])
        self.assertAlmostEqual(r["spread"], 1.0)
        self.assertLess(r["contrast"][1], r["contrast"][0] * 0.3)       # far shallower, relative
        self.assertGreater(r["folds"], 0.99)                            # folds sees no difference
        light = [(v, v, v) for v in range(200, 232)]
        navy = [(round(v * 0.23), round(v * 0.23), round(v * 0.23)) for v in range(200, 232)]
        self.assertFalse(ps_mockup.swatch_check(light, navy, (52, 52, 52))["flat"])

    def test_flat_rule_on_the_stored_contrasts(self):
        """Relative fold contrast before and after, from the live F7 log and the corpus frames."""
        stored = [(0.227, 0.213, False), (0.227, 0.228, False),          # white tee colorways
                  (0.583, 0.406, False), (0.583, 0.279, False),          # black tee navy, red
                  (0.583, 0.105, True), (0.227, 0.008, True),            # black tee sand; white on white, old curve
                  (1.127, 0.569, False), (1.127, 0.394, False), (1.127, 0.142, True),   # corpus sweatshirt
                  (0.211, 0.213, False)]                                 # corpus white tee
        for before, after, flat in stored:
            got = after < min(ps_mockup.FLAT_FLOOR, ps_mockup.FLAT_SHARE * before)
            self.assertEqual(got, flat, (before, after))

    def test_white_on_a_white_blank_keeps_the_blank(self):
        white_tee = {"mid": 228.26, "p99": 241}                          # the live fixture's tones
        for rgb in ((255, 255, 255), (250, 250, 250)):
            self.assertTrue(ps_mockup.is_blank(white_tee, rgb))
            self.assertIsNone(ps_mockup.tone_curve(white_tee, rgb))
        self.assertFalse(ps_mockup.is_blank(white_tee, (230, 210, 160)))  # sand: a gain, as before
        black_tee = {"mid": 36.0, "p99": 47}
        self.assertFalse(ps_mockup.is_blank(black_tee, (255, 255, 255)))  # white from black: curved, then flat
        self.assertIsNotNone(ps_mockup.tone_curve(black_tee, (255, 255, 255)))
        base = [(v, v, v) for v in range(200, 250)]
        out = ps_mockup.swatch_check(base, base, (255, 255, 255))
        self.assertTrue(out["blank"])
        self.assertFalse(out["flat"])
        self.assertGreater(out["delta_e"], 5, "delta_e measures the blank's own shading")

    def test_black_swatch_curve_has_a_floor(self):
        pts = ps_mockup.tone_curve({"mid": 227.0, "p99": 242}, (0, 0, 0))
        self.assertEqual(pts[0], [0, 0.0])
        self.assertGreater(pts[1][1], 0)

    def test_lab_swatch(self):
        self.assertEqual(ps_mockup._rgb({"lab": [100, 0, 0]}), [255, 255, 255])
        navy = ps_mockup.lab_to_rgb([32, 10, -45])
        self.assertLess(ps_mockup.delta_e(navy, ps_mockup.lab_to_rgb(ps_mockup._lab(navy))), 1)
        for bad in ({"lab": [1, 2]}, {"rgb": [1, 2, 3]}):
            with self.assertRaises(ValueError):
                ps_mockup._rgb(bad)
        base = [(v, v, v) for v in range(150, 250)]
        red = [(255, 0, 18)] * 100                                       # the clipped swatch
        out = ps_mockup.swatch_check(base, red, ps_mockup._rgb({"lab": [60, 90, 70]}), lab=[60, 90, 70])
        self.assertGreater(out["delta_e"], 5, "an out-of-gamut Lab target fails the check")

    def test_solid_png_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ps_mockup._solid_png(os.path.join(tmp, "p.png"), 7, 3, (214, 72, 72))
            size, raw = read_png(path)
        self.assertEqual(size, (7, 3))
        self.assertEqual(len(raw), 3 * (1 + 7 * 3))
        self.assertEqual(tuple(raw[1:4]), (214, 72, 72))


class CompositeGrainTest(unittest.TestCase):
    def test_each_element_gets_its_own_grain_layer(self):
        """Two elements with the default name: two layers, never the first element's refilled."""
        calls = []
        trials = {"n": 0}

        def fake_run(js, args, undo=None, timeout=240):
            calls.append((js, dict(args), undo))
            if js == ps_composite.GRAIN_JS:
                trials["n"] += 1
            return {"layer": args.get("name")}

        def fake_texture(layer=None, region=None, radius=2):
            if "ring" in region:                 # the scene ring: first call of each match_grain
                trials["n"] = 0
                return {"energy": 10.0}
            return {"energy": 2.0 + 3 * trials["n"]}

        saved = (ps_composite._run, ps_composite.G.texture, ps_composite.A.history,
                 ps_composite.A.step_back, ps_composite.A.history_gate)
        try:
            ps_composite._run = fake_run
            ps_composite.G.texture = fake_texture
            ps_composite.A.history = lambda: {"index": 3, "name": "mark", "id": 7}
            ps_composite.A.step_back = lambda h0, undo: h0
            ps_composite.A.history_gate = lambda h0, undo=None: []
            a = ps_composite.match_grain("element")
            b = ps_composite.match_grain("patch")
            c = ps_composite.match_grain("patch", name="Grain, patch take 2")
        finally:
            (ps_composite._run, ps_composite.G.texture, ps_composite.A.history,
             ps_composite.A.step_back, ps_composite.A.history_gate) = saved
        self.assertEqual((a["layer"], b["layer"], c["layer"]),
                         ("Grain match: element", "Grain match: patch", "Grain, patch take 2"))
        grain = [args for js, args, undo in calls if js == ps_composite.GRAIN_JS]
        self.assertEqual({g["name"] for g in grain if g["layer"] == "element"}, {"Grain match: element"})
        self.assertEqual({g["name"] for g in grain if g["layer"] == "patch"},
                         {"Grain match: patch", "Grain, patch take 2"})
        # The ownership check runs before the first named state, as a job without undo.
        checks = [(args, undo) for js, args, undo in calls if js.startswith(ps_composite.GRAIN_CHECK_JS)
                  and js != ps_composite.GRAIN_JS]
        self.assertEqual(len(checks), 3)
        self.assertTrue(all(undo is None for _a, undo in checks))

    def test_grain_job_refuses_a_layer_clipped_to_another_element(self):
        self.assertTrue(ps_composite.GRAIN_JS.startswith(ps_composite.GRAIN_CHECK_JS))
        self.assertIn("pc_clip_base(g)", ps_composite.GRAIN_CHECK_JS)
        self.assertIn("is not clipped to", ps_composite.GRAIN_CHECK_JS)
        self.assertIn("function pc_clip_base", ps_composite.HELPERS_JS)


class UpscaleHelpersTest(unittest.TestCase):
    def test_match_scale_caps_the_long_side(self):
        self.assertEqual(ps_upscale._coarse(512, 512), [256, 256])
        self.assertEqual(ps_upscale._coarse(4000, 3000), [256, 192])
        self.assertEqual(ps_upscale._coarse(200, 100), [200, 100])

    def test_lock_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            ps_upscale.lock("x", mode="multiply")


class GenerativeHelpersTest(unittest.TestCase):
    def test_default_margin_is_half_the_long_side_at_least_64(self):
        self.assertEqual(ps_generative.default_margin([340, 240, 460, 360]), 64)
        self.assertEqual(ps_generative.default_margin([0, 0, 400, 100]), 200)

    def test_tiles_cover_with_overlap(self):
        tiles = ps_generative.tile_plan([0, 0, 3000, 1000], 1024, 64)
        self.assertEqual(tiles[0][:2], [0, 0])
        self.assertEqual(max(t[2] for t in tiles), 3000)
        self.assertEqual(max(t[3] for t in tiles), 1000)
        xs = sorted({t[0] for t in tiles})
        for a, b in zip(xs, xs[1:]):
            self.assertLessEqual(b - a, 1024 - 64)
        self.assertEqual(ps_generative.tile_plan([10, 20, 500, 400], 1024), [[10, 20, 500, 400]])

    def test_tile_must_exceed_overlap(self):
        with self.assertRaises(ValueError):
            ps_generative.tile_plan([0, 0, 100, 100], 64, 64)

    def test_rejects_unknown_polarity_before_photoshop(self):
        with self.assertRaises(ValueError):
            ps_generative.capture(tempfile.gettempdir(), polarity="red")

    def test_expand_needs_a_positive_side_before_photoshop(self):
        for sides in ({}, {"right": -10}):
            with self.assertRaises(ValueError):
                ps_generative.expand(tempfile.gettempdir(), **sides)


class KeyArtHelpersTest(unittest.TestCase):
    def test_cover_bounds_fills_the_canvas_and_keeps_aspect(self):
        l, t, r, b = ps_keyart.cover_bounds(512, 512, 1280, 720)
        self.assertEqual((l, r), (0, 1280))
        self.assertAlmostEqual(b - t, 1280)
        self.assertAlmostEqual(t, -280)

    def test_cover_bounds_focus_stays_inside_the_crop(self):
        top = ps_keyart.cover_bounds(512, 512, 1280, 720, focus=(0.5, 0.0))
        self.assertEqual(top[1], 0)
        bottom = ps_keyart.cover_bounds(512, 512, 1280, 720, focus=(0.5, 1.0))
        self.assertAlmostEqual(bottom[3], 720)

    def test_presets_are_well_formed(self):
        for name, p in ps_keyart.PRESETS.items():
            w, h = p["size"]
            for z in p.get("unsafe", []):
                self.assertTrue(0 <= z[0] < z[2] <= w and 0 <= z[1] < z[3] <= h, name)
            self.assertGreater(p["display"], 0, name)

    def test_rejects_bad_input_before_photoshop(self):
        with self.assertRaises(ValueError):
            ps_keyart.new_canvas("tiktok-banner")
        with self.assertRaises(ValueError):
            ps_keyart.type_layers([{"name": "a", "text": "b"}])
        with self.assertRaises(ValueError):
            ps_keyart.type_layers([{"name": "a", "text": "b", "box": [0, 0, 1, 1], "align": "justify"}])
        with self.assertRaises(ValueError):
            ps_keyart.export_under(os.path.join(tempfile.gettempdir(), "x.gif"), 1000, fmt="gif")

class GameArtHelpersTest(unittest.TestCase):
    def test_pow2(self):
        self.assertTrue(ps_gameart.pow2(1024))
        self.assertFalse(ps_gameart.pow2(1000))
        self.assertFalse(ps_gameart.pow2(0))
        self.assertEqual(ps_gameart.next_pow2(1000), 1024)
        self.assertEqual(ps_gameart.next_pow2(512), 512)

    def test_bad_inputs_raise(self):
        with self.assertRaises(ValueError):
            ps_gameart.pack_channels("x.png", "a", "b", "c", a="d", fmt="png")
        with self.assertRaises(ValueError):
            ps_gameart.export_texture("x.tga", bits=16, fmt="tga")
        with self.assertRaises(ValueError):
            ps_gameart.export_texture("x.png", resample="lanczos")
        with self.assertRaises(ValueError):
            ps_gameart.id_select("ID", [0, 300, 0])
        with self.assertRaises(ValueError):
            ps_gameart.nine_slice_check(0, 8, 8, 8)
        with self.assertRaises(ValueError):
            ps_gameart.pack_channels("x.tga", "a", 300, None)


if __name__ == "__main__":
    unittest.main()

