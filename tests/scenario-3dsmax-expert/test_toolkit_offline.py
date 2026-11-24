"""Offline tests for the scenario-3dsmax-expert toolkit, with no 3ds Max installed.

The fake pymxs in fakes/ is put on sys.path here only; it is never shipped in the skill.
Its behavior is a guess at 3ds Max: passing tests prove the Python logic and the generated
text, not the 3ds Max API. Three tests need Pillow (requirements.txt) and skip without it.
Every file goes to a temporary folder removed at exit.
"""
from __future__ import annotations

import atexit
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-expert"
SCRIPTS = SKILL / "scripts"
TMP_ROOT = Path(tempfile.mkdtemp(prefix="max_tests_"))
atexit.register(shutil.rmtree, TMP_ROOT, ignore_errors=True)
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import pymxs  # noqa: E402  (the fake)
import max_batch  # noqa: E402
import max_check  # noqa: E402
import max_env  # noqa: E402
import max_review  # noqa: E402
import max_wrap  # noqa: E402
from maxkit import audit, capture, result, stats, xio  # noqa: E402
from pymxs import FakeMaterial, FakeNode, Name  # noqa: E402

rt = pymxs.runtime
HAVE_PIL = importlib.util.find_spec("PIL") is not None


def tmpdir() -> Path:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="max_", dir=TMP_ROOT))


def exec_generated(script: str):
    """Run a generated pymxs script against the fake; return (payload, stdout)."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(script, "<generated>", "exec"), {"__name__": "__generated__"})
    out = buf.getvalue()
    line = next(ln for ln in out.splitlines() if ln.startswith("MXK_RESULT "))
    return json.loads(line[len("MXK_RESULT "):]), out


def scene_basic():
    rt.reset()
    mat = FakeMaterial("Oak", "PhysicalMaterial")
    base = object()
    rt.objects = [
        FakeNode("Lobby - Desk", material=mat, base=base),
        FakeNode("Lobby - Desk Copy", material=mat, base=base),
        FakeNode("Box001", layer="0", material=None),
        FakeNode("Chair", scale=(1, 1, 2), material=FakeMaterial("Old", "Standardmaterial")),
        FakeNode("Chair", scale=(-1, 1, 1), material=mat),
        FakeNode("Far Tree", pos=(500000, 0, 0), material=mat),
        FakeNode("Empty", faces=0, verts=0, material=mat),
        FakeNode("Key Light", cls="Physical_Light", superclass=pymxs.light, faces=0, verts=0),
    ]
    rt.LayerManager.names = ["0", "Geo", "Unused"]
    bm_ok, bm_bad = mock.Mock(), mock.Mock()
    bm_ok.filename, bm_bad.filename = "C:\\maps\\oak.png", "C:\\maps\\missing_rough.png"
    rt.existing_files = {"C:\\maps\\oak.png"}
    rt.bitmaps = [bm_ok, bm_bad]
    rt.save_required = True


# ------------------------------------------------------------------ max_wrap
class WrapTests(unittest.TestCase):
    def test_python_compiles_and_inlines_kit(self):
        s = max_wrap.wrap("result = audit.all()['tally']", kit=["audit"])
        compile(s, "<w>", "exec")
        for name in ("'result'", "'stats'", "'audit'"):
            self.assertIn(name, s.split("_MXK_SOURCES = ")[1][:400] + s)
        self.assertIn("pymxs.undo(True, _MXK_LABEL)", s)
        self.assertIn("status: not yet run in 3ds Max", s)
        self.assertNotIn("from maxkit", s.split("_MXK_SOURCES")[0])  # nothing imported from disk

    def test_python_runs_against_fake_and_writes_result(self):
        scene_basic()
        d = tmpdir()
        rp = d / "res.json"
        s = max_wrap.wrap("""
            snap = stats.snapshot()
            log("objects", snap["objects"])
            result = {"objects": snap["objects"], "tally": audit.all()["tally"]}
        """, kit=["audit", "stats"], result_path=rp, label="probe")
        payload, _ = exec_generated(s)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["result"]["objects"], 8)
        self.assertEqual(json.loads(rp.read_text())["result"], payload["result"])
        self.assertEqual(payload["log"], ["objects 8"])
        self.assertIn((True, "probe"), rt.undo_labels)
        self.assertIn("2027", payload["max_version"])

    def test_python_error_is_reported_not_raised(self):
        rt.reset()
        payload, _ = exec_generated(max_wrap.wrap("raise ValueError('boom')"))
        self.assertFalse(payload["ok"])
        self.assertIn("boom", payload["error"])

    def test_python_reads_result_path_from_batch_args(self):
        rt.reset()
        d = tmpdir()
        rt.maxops.mxsCmdLineArgs = {Name("result_path"): str(d / "from_args.json")}
        exec_generated(max_wrap.wrap("result = 42"))
        self.assertEqual(json.loads((d / "from_args.json").read_text())["result"], 42)

    def test_python_syntax_error_in_chunk_fails_early(self):
        with self.assertRaises(SyntaxError):
            max_wrap.wrap("def broken(:\n  pass")

    def test_maxscript_form(self):
        s = max_wrap.wrap("result = mxk_stats_snapshot()", lang="maxscript", kit=["stats"])
        self.assertTrue(s.rstrip().endswith(")"))
        self.assertIn('undo "agent change" on (', s)
        self.assertIn("fn mxk_toJson", s)
        self.assertIn("fn mxk_stats_snapshot", s)
        self.assertLess(s.index("fn mxk_dict"), s.index("fn mxk_stats_snapshot"))
        self.assertTrue(s.rstrip()[:-1].rstrip().endswith("mxk_json"), "JSON is the script's value")
        self.assertNotIn("createFile", s)  # no file write unless asked
        self.assertNotRegex(s, r"(?im)^(?!\s*--).*\bpython\s*\.")  # no python.* call outside comments
        r = max_check.check(code=s, lang="maxscript", channel="mcp-safe")
        self.assertEqual(r["errors"], [], r["errors"])

    def test_maxscript_with_result_path_avoids_block_list(self):
        s = max_wrap.wrap("result = 1", lang="maxscript", kit=["audit", "capture"],
                          result_path="C:\\Out Dir\\r.json")
        self.assertIn('createFile @"C:\\Out Dir\\r.json"', s)
        r = max_check.check(code=s, lang="maxscript", channel="mcp-safe")
        self.assertEqual(r["errors"], [])
        self.assertTrue(any("createFile" in w["message"] for w in r["warnings"]))

    def test_unknown_kit_rejected(self):
        with self.assertRaises(ValueError):
            max_wrap.wrap("result = 1", kit=["nope"])
        with self.assertRaises(ValueError):
            max_wrap.wrap("result = 1", lang="maxscript", kit=["xio"])

    def test_domain_helpers_by_path_and_kit_dirs(self):
        d = tmpdir()
        (d / "maxkit_demo.py").write_text(textwrap.dedent('''
            """Status: not yet run in 3ds Max"""
            from maxkit import stats
            def objects():
                return stats.snapshot()["objects"]
        '''))
        (d / "mxs").mkdir()
        (d / "mxs" / "maxkit_demo.ms").write_text(
            "fn mxk_demo_count = (local s = mxk_stats_snapshot(); GetDictValue s \"objects\")\n")
        scene_basic()
        # by name through kit_dirs: lead dependency (stats) is pulled in automatically
        s = max_wrap.wrap("import maxkit_demo as m2\nresult = [maxkit_demo.objects(), m2.objects()]",
                          kit=["maxkit_demo"], kit_dirs=[d])
        payload, _ = exec_generated(s)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["result"], [8, 8])
        # by path
        s2 = max_wrap.wrap("result = maxkit_demo.objects()", kit=[str(d / "maxkit_demo.py")])
        self.assertTrue(exec_generated(s2)[0]["ok"])
        # MAXScript: by name in kit_dirs (mxs/ subfolder) and by path; stats twin added
        for entry, dirs in (("maxkit_demo", [d]), (str(d / "mxs" / "maxkit_demo.ms"), None)):
            m = max_wrap.wrap("result = mxk_demo_count()", lang="maxscript", kit=[entry], kit_dirs=dirs)
            self.assertIn("-- kit: maxkit_demo", m)
            self.assertIn("fn mxk_stats_snapshot", m)
            self.assertLess(m.index("fn mxk_stats_snapshot"), m.index("fn mxk_demo_count"))
        with self.assertRaises(ValueError):
            max_wrap.wrap("result = 1", kit=[str(d / "mxs" / "maxkit_demo.ms")])  # wrong language
        with self.assertRaises(ValueError):
            max_wrap.wrap("result = 1", kit=["maxkit_missing"], kit_dirs=[d])


# ------------------------------------------------------------------ max_batch
class BatchTests(unittest.TestCase):
    def test_command_list_and_args(self):
        cmd = max_batch.command(r"C:\Jobs\My Job\audit.ms", scene=r"C:\Projects\Lobby Scene\lobby v001.max",
                                args={"result_path": r"C:\Out Dir\r.json", "frames": 10, "fast": True,
                                      "label": 'say "hi"'},
                                exe=r"C:\Program Files\Autodesk\3ds Max 2027\3dsmaxbatch.exe",
                                listener_log=r"C:\Out Dir\l.log")
        self.assertIsInstance(cmd, list)
        self.assertEqual(cmd[0], r"C:\Program Files\Autodesk\3ds Max 2027\3dsmaxbatch.exe")
        self.assertEqual(cmd[1], r"C:\Jobs\My Job\audit.ms")
        self.assertEqual(cmd[cmd.index("-sceneFile") + 1], r"C:\Projects\Lobby Scene\lobby v001.max")
        self.assertIn('result_path:@"C:\\Out Dir\\r.json"', cmd)
        self.assertIn('frames:"10"', cmd)
        self.assertIn('fast:"true"', cmd)
        self.assertIn('label:"say \\"hi\\""', cmd)
        self.assertEqual(cmd[cmd.index("-dm") + 1], "on")

    def test_windows_quoting_round_trip(self):
        cmd = max_batch.command(r"C:\Jobs\My Job\a.ms", scene=r"C:\A B\s.max",
                                args={"out": r"C:\Out Dir\x.png"}, exe=r"C:\Program Files\x\3dsmaxbatch.exe")
        line = subprocess.list2cmdline(cmd)
        self.assertIn('"C:\\Program Files\\x\\3dsmaxbatch.exe"', line)
        self.assertIn('"C:\\A B\\s.max"', line)
        # parse back with the Windows rules (CommandLineToArgvW-like) and compare
        self.assertEqual(_argv_windows(line), cmd)

    def test_bad_values(self):
        with self.assertRaises(ValueError):
            max_batch.command("a.ms", args={"bad key": "x"}, exe="x")
        with self.assertRaises(ValueError):
            max_batch.command("a.ms", verbosity=9, exe="x")

    def test_run_batch_without_max(self):
        if os.name == "nt":
            self.skipTest("Windows host")
        d = tmpdir()
        r = max_batch.run_batch("print 1\n", log_dir=d)
        self.assertFalse(r["ok"])
        self.assertIn("not found", r["meaning"])
        self.assertTrue(any(p.suffix == ".ms" for p in d.iterdir()))


def _argv_windows(line: str) -> list[str]:
    """Minimal MS C runtime argv parser (backslash and quote rules) for the round-trip test."""
    args, cur, i, inq, have = [], [], 0, False, False
    while i < len(line):
        c = line[i]
        if c == "\\":
            j = i
            while j < len(line) and line[j] == "\\":
                j += 1
            n = j - i
            if j < len(line) and line[j] == '"':
                cur.append("\\" * (n // 2))
                if n % 2:
                    cur.append('"')
                    i = j + 1
                else:
                    i = j
                have = True
                continue
            cur.append("\\" * n)
            i = j
            have = True
            continue
        if c == '"':
            inq = not inq
            have = True
        elif c in " \t" and not inq:
            if have or cur:
                args.append("".join(cur))
            cur, have = [], False
        else:
            cur.append(c)
            have = True
        i += 1
    if have or cur:
        args.append("".join(cur))
    return args


# ------------------------------------------------------------------ max_check
class CheckTests(unittest.TestCase):
    def test_python_syntax_error(self):
        r = max_check.check(code="from pymxs import runtime as rt\nrt.box(\n", lang="python")
        self.assertFalse(r["ok"])
        self.assertIn("syntax", r["errors"][0]["message"])

    def test_maxscript_syntax_error(self):
        r = max_check.check(code='(\n  b = box()\n  print "x\n', lang="maxscript")
        self.assertFalse(r["ok"])
        msgs = " ".join(e["message"] for e in r["errors"])
        self.assertIn("unclosed string", msgs)
        r2 = max_check.check(code="(\n  b = box())\n)", lang="maxscript")
        self.assertTrue(any("unexpected ')'" in e["message"] for e in r2["errors"]))
        r3 = max_check.check(code='-- a ( comment\n s = @"C:\\a\\" \n /* ( */ print s', lang="maxscript")
        self.assertTrue(r3["ok"], r3["errors"])

    def test_each_block_list_item_flagged_in_mcp_safe(self):
        samples = {
            "dotNetObject": 'x = dotNetObject "System.Text.StringBuilder"',
            "dotNetClass": 'x = dotNetClass "System.IO.File"',
            "dotNet.": 'dotNet.addEventHandler b "Click" f',
            "macroScript": 'macroScript Foo category:"X" (print 1)',
            "UIAccessor": "UIAccessor.PressButton h",
            "windows.sendMessage": "windows.sendMessage h 16 0 0",
            "globalVars.remove": "globalVars.remove #foo",
            "setINISetting": 'setINISetting "a.ini" "s" "k" "v"',
            "deleteFile": 'deleteFile "C:\\\\a.txt"',
            "copyFile": 'copyFile "a" "b"',
            "python.Execute": 'python.Execute "print(1)"',
            "python.ExecuteFile": 'python.ExecuteFile "a.py"',
            "python.Import": 'python.Import "os"',
            "DOSCommand": 'DOSCommand "dir"',
            "HiddenDOSCommand": 'HiddenDOSCommand "dir"',
            "ShellLaunch": 'ShellLaunch "notepad.exe" ""',
        }
        self.assertEqual(sorted(samples), sorted(n for n, _ in max_check.BLOCKED))
        for name, line in samples.items():
            r = max_check.check(code=line, lang="maxscript", channel="mcp-safe")
            self.assertTrue(any(e["message"].startswith(name + " is blocked") for e in r["errors"]),
                            f"{name} not flagged: {r['errors']}")
            r_batch = max_check.check(code=line, lang="maxscript", channel="batch")
            self.assertFalse(any("blocked" in e["message"] for e in r_batch["errors"]))

    def test_block_list_ignores_comments_and_strings(self):
        r = max_check.check(code='-- deleteFile is blocked\nprint "copyFile"', lang="maxscript", channel="mcp-safe")
        self.assertEqual(r["errors"], [])

    def test_python_in_mcp_safe_is_error(self):
        r = max_check.check(code="from pymxs import runtime as rt\nrt.redrawViews()", lang="python",
                            channel="mcp-safe")
        self.assertFalse(r["ok"])

    def test_unknown_names(self):
        code = textwrap.dedent("""\
            from pymxs import runtime as rt
            rt.redrawViews()
            rt.importFile("a.fbx")
            rt.totallyMadeUpThing.foo()
            rt.LayerManager.count  # [verify]
        """)
        r = max_check.check(code=code, lang="python")
        names = {u["name"]: u for u in r["unknown_names"]}
        self.assertIn("totallyMadeUpThing.foo", names)
        self.assertFalse(names["totallyMadeUpThing.foo"]["marked"])
        self.assertTrue(names["LayerManager.count"]["marked"])
        self.assertNotIn("redrawViews", names)
        self.assertNotIn("importFile", names)
        m = max_check.check(code="local b = box()\nb.pos = [0,0,0]\nfooBar.baz 1 -- [verify]\n", lang="maxscript")
        mn = {u["name"]: u for u in m["unknown_names"]}
        self.assertIn("fooBar.baz", mn)
        self.assertTrue(mn["fooBar.baz"]["marked"])
        self.assertNotIn("b.pos", mn)

    def test_hygiene(self):
        r = max_check.check(code="import MaxPlus\n", lang="python")
        self.assertFalse(r["ok"])
        r = max_check.check(code="import threading\nt = threading.Thread(target=print)\n", lang="python")
        self.assertTrue(any("main thread" in w["message"] for w in r["warnings"]))

    def test_shipped_scripts_pass(self):
        files = sorted(str(p) for p in SCRIPTS.rglob("*") if p.suffix in (".py", ".ms"))
        r = max_check.check(files)
        self.assertEqual(r["errors"], [], r["errors"])
        mxs = sorted(str(p) for p in (SCRIPTS / "maxkit" / "mxs").glob("*.ms"))
        r2 = max_check.check(mxs, channel="mcp-safe")
        self.assertEqual(r2["errors"], [], r2["errors"])


# ------------------------------------------------------------------ max_env
class EnvTests(unittest.TestCase):
    def test_doctor_without_max(self):
        env = {k: v for k, v in os.environ.items() if k not in max_env.ENV_KEYS}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(max_env, "_open", return_value=False), \
                mock.patch.object(max_env.platform, "system", return_value="Darwin"):
            d = max_env.doctor()
        for key in ("os", "installs", "batch_exe", "mcp_ports", "bridge", "channel"):
            self.assertIn(key, d)
        self.assertEqual(d["channel"], "handoff")
        self.assertEqual(d["installs"], [])
        self.assertIsNone(d["batch_exe"])
        self.assertEqual(d["mcp_ports"], [])
        self.assertTrue(any("Windows only" in n for n in d["notes"]))
        json.dumps(d)

    def test_doctor_sees_mcp_port(self):
        with mock.patch.object(max_env, "_open", side_effect=lambda h, p, timeout=0.25: p == 27201), \
                mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MAX_CHANNEL", None)
            os.environ.pop("MAX_BRIDGE", None)
            d = max_env.doctor()
        self.assertEqual(d["mcp_ports"], [27201])
        self.assertEqual(d["channel"], "mcp-safe")

    def test_doctor_real_probe_runs(self):
        d = max_env.doctor()  # real sockets on 127.0.0.1, nothing sent
        self.assertIn(d["channel"], ("bridge", "mcp-safe", "batch", "handoff"))

    def test_forced_channel(self):
        with mock.patch.dict(os.environ, {"MAX_CHANNEL": "batch"}):
            self.assertEqual(max_env.doctor()["channel"], "batch")


# ------------------------------------------------------------------ max_review
@unittest.skipUnless(HAVE_PIL, "Pillow not installed")
class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import Image, ImageDraw
        cls.d = tmpdir()
        Image.new("RGB", (200, 120), (0, 0, 0)).save(cls.d / "black.png")
        Image.new("RGB", (200, 120), (255, 255, 255)).save(cls.d / "white.png")
        img = Image.new("RGB", (200, 120), (60, 70, 90))
        dr = ImageDraw.Draw(img)
        dr.rectangle([70, 35, 130, 85], fill=(220, 200, 170))
        dr.line([0, 119, 199, 0], fill=(140, 140, 140), width=3)
        img.save(cls.d / "scene.png")
        img2 = img.copy()
        ImageDraw.Draw(img2).rectangle([10, 10, 40, 40], fill=(255, 0, 0))
        img2.save(cls.d / "scene_b.png")

    def test_flags(self):
        self.assertIn("all_black", max_review.image_checks(str(self.d / "black.png"))["flags"])
        self.assertIn("all_white", max_review.image_checks(str(self.d / "white.png"))["flags"])
        good = max_review.image_checks(str(self.d / "scene.png"))
        self.assertNotIn("all_black", good["flags"])
        self.assertNotIn("uniform", good["flags"])
        self.assertEqual((good["width"], good["height"]), (200, 120))

    def test_compare(self):
        same = max_review.compare(str(self.d / "scene.png"), str(self.d / "scene.png"))
        self.assertTrue(same["identical"])
        diff = max_review.compare(str(self.d / "scene.png"), str(self.d / "scene_b.png"))
        self.assertFalse(diff["identical"])
        self.assertGreater(diff["changed_fraction"], 0)

    def test_contact_sheet(self):
        out = max_review.contact_sheet([str(self.d / n) for n in ("black.png", "white.png", "scene.png")],
                                       str(self.d / "sheet.png"), cols=2, thumb=100)
        self.assertTrue(Path(out).exists())


# ------------------------------------------------------------------ maxkit against the fake scene
class AuditTests(unittest.TestCase):
    def setUp(self):
        scene_basic()

    def test_stats_snapshot_and_diff(self):
        a = stats.snapshot()
        self.assertEqual(a["objects"], 8)
        self.assertEqual(a["geometry"], 7)
        self.assertEqual(a["instances"], 2)
        self.assertEqual(a["missing_maps"], ["C:\\maps\\missing_rough.png"])
        self.assertEqual(a["layers"]["Unused"], 0)
        self.assertEqual(a["system_unit"], "centimeters")
        rt.objects.append(FakeNode("New Bench", faces=100, verts=60))
        b = stats.snapshot()
        dd = stats.diff(a, b)
        self.assertEqual(dd["objects"], {"before": 8, "after": 9, "delta": 1})
        self.assertEqual(dd["faces"]["delta"], 100)
        self.assertEqual(stats.diff(a, a), {})

    def test_rules(self):
        rep = audit.all(expect={"units": "meters", "renderer": "V_Ray", "max_faces": 10})
        f = rep["findings"]

        def has(rule, node=None, text=""):
            return any(x["rule"] == rule and (node is None or x["node"] == node) and text in x["message"]
                       for x in f)
        self.assertTrue(has("units", None, "project expects meters"))
        self.assertTrue(has("units", "Far Tree", "from the origin"))
        self.assertTrue(has("names", "Box001", "default name"))
        self.assertTrue(has("names", "Chair", "2 nodes share"))
        self.assertTrue(has("transforms", "Chair", "non-uniform"))
        self.assertTrue(has("transforms", "Chair", "negative"))
        self.assertTrue(has("geometry", "Empty", "0 faces"))
        self.assertTrue(has("geometry", "Lobby - Desk", "budget"))
        self.assertTrue(has("materials", "Box001", "no material"))
        self.assertTrue(has("materials", "Chair", "legacy"))
        self.assertTrue(has("maps", None, "missing_rough.png"))
        self.assertTrue(has("layers", None, "layer 0 holds 1"))
        self.assertTrue(has("layers", "Unused", "empty layer"))
        self.assertTrue(has("render", None, "project expects V_Ray"))
        self.assertTrue(has("render", None, "unsaved"))
        self.assertFalse(has("names", "Key Light"))
        self.assertEqual(sum(rep["tally"].values()), len(f))
        self.assertGreater(rep["tally"]["error"], 0)

    def test_clean_scene_has_no_errors(self):
        rt.reset()
        rt.objects = [FakeNode("Lobby - Wall", material=FakeMaterial("Plaster", "PhysicalMaterial"))]
        rep = audit.all(expect={"units": "centimeters", "renderer": "Arnold"})
        self.assertEqual(rep["tally"]["error"], 0, rep)
        self.assertEqual(rep["tally"]["warn"], 0, rep)

    def test_gltf_precheck_runs(self):
        out = xio.gltf_precheck()
        self.assertIsInstance(out, list)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        scene_basic()

    def test_next_free_and_fit(self):
        d = tmpdir()
        p = d / "shot.png"
        self.assertEqual(capture.next_free(str(p)), str(p))
        p.write_bytes(b"x")
        self.assertEqual(capture.next_free(str(p)), str(d / "shot_v002.png"))
        (d / "shot_v002.png").write_bytes(b"x")
        self.assertEqual(capture.next_free(str(d / "shot_v002.png")), str(d / "shot_v003.png"))
        self.assertEqual(capture.fit_size(1920, 1080, 960), (960, 540))
        self.assertEqual(capture.fit_size(100, 50, (10, 20)), (10, 20))

    @unittest.skipUnless(HAVE_PIL, "Pillow not installed")
    def test_views_never_overwrite_and_restore(self):
        d = tmpdir()
        out = capture.views(str(d), size=160)
        self.assertEqual([o["view"] for o in out], ["persp", "front", "left", "top"])
        self.assertEqual(rt.viewport.type, Name("view_persp_user"))
        again = capture.viewport(str(d / "view_persp.png"))
        self.assertTrue(again["path"].endswith("view_persp_v002.png"))
        checks = max_review.image_checks(out[0]["path"])
        self.assertEqual(checks["width"], 160)

    def test_viewport_refuses_batch(self):
        rt.maxops.batch = True
        with self.assertRaises(RuntimeError):
            capture.viewport(str(tmpdir() / "x.png"))

    @unittest.skipUnless(HAVE_PIL, "Pillow not installed")
    def test_render(self):
        d = tmpdir()
        rt.objects.append(FakeNode("Cam - Lobby", cls="Physical", superclass=pymxs.camera))
        r = capture.render(str(d / "r.png"), camera="Cam - Lobby", size=480)
        self.assertEqual((r["width"], r["height"]), (480, 270))
        self.assertEqual(r["camera"], "Cam - Lobby")
        with self.assertRaises(ValueError):
            capture.render(str(d / "r.png"), camera="nope")


class XioTests(unittest.TestCase):
    def test_import_reports_new_nodes(self):
        scene_basic()
        d = tmpdir()
        f = d / "chair.fbx"
        f.write_bytes(b"x")
        rt.import_adds = [FakeNode("Chair_Imported", faces=500, verts=300, size=90)]
        rep = xio.import_any(str(f))
        self.assertEqual(rep["nodes"], ["Chair_Imported"])
        self.assertEqual(rep["size"], [90.0, 90.0, 90.0])
        with self.assertRaises(FileNotFoundError):
            xio.import_any(str(d / "missing.fbx"))

    def test_merge_max_renames_material_dups_and_passes_units(self):
        scene_basic()
        d = tmpdir()
        f = d / "sofa.max"
        f.write_bytes(b"x")
        rt.import_adds = [FakeNode("Sofa", faces=800, verts=500, size=200)]
        rep = xio.import_any(str(f), ignore_file_units=True, layers=["Furniture"])
        self.assertEqual(rep["nodes"], ["Sofa"])
        m = rt.last_merge
        self.assertIn("renameMtlDups", m["flags"])
        self.assertIn("neverReparent", m["flags"])
        self.assertNotIn("useSceneMtlDups", m["flags"])
        self.assertTrue(m["quiet"])
        self.assertIs(m["ignoreFileUnits"], True)
        self.assertEqual(m["layers"], ["Furniture"])
        self.assertIsNone(m["mergeNodesByLayer"])

    def test_exports_never_overwrite(self):
        scene_basic()
        d = tmpdir()
        a = xio.export_gltf(str(d / "lobby.glb"))
        b = xio.export_gltf(str(d / "lobby.glb"))
        self.assertTrue(a["ok"] and b["ok"])
        self.assertNotEqual(a["path"], b["path"])
        fbx = xio.export_fbx(str(d / "lobby.fbx"), preset={"UpAxis": "Z"})
        self.assertEqual(fbx["preset"], {"UpAxis": "Z"})
        with self.assertRaises(ValueError):
            xio.export_gltf(str(d / "lobby.fbx"))
        u = xio.export_usd(str(d / "lobby.usdc"))
        self.assertTrue(u["ok"])


class ResultTests(unittest.TestCase):
    def test_envelope_and_jsonable(self):
        e = result.envelope(True, {"p": pymxs.Point3(1, 2, 3), "n": FakeNode("A"), "s": {1, 2}}, None, ["x"], "2027")
        json.dumps(e)
        self.assertEqual(e["result"]["p"], [1.0, 2.0, 3.0])
        self.assertEqual(e["result"]["n"], "A")


class StatusLineTests(unittest.TestCase):
    def test_in_max_modules_carry_status(self):
        for p in list((SCRIPTS / "maxkit").glob("*.py")) + list((SCRIPTS / "maxkit" / "mxs").glob("*.ms")):
            head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:6])
            self.assertIn("not yet run in 3ds Max", head, p.name)

    def test_no_em_dash_or_local_path_in_skill(self):
        for p in SKILL.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".ms", ".md", ".txt"):
                t = p.read_text(encoding="utf-8")
                self.assertNotIn("\u2014", t, p.name)
                self.assertNotIn("/Users/", t, p.name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
