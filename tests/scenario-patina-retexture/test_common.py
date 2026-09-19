import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import helpers

common = helpers.load("common")


class ConfigTests(unittest.TestCase):
    def read(self, folder, **overrides):
        return common.read_config(helpers.write_config(folder, **overrides))

    def test_defaults_and_path_resolution(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "assets").mkdir()
            (Path(folder) / "assets" / "Before.blend").write_bytes(b"b")
            (Path(folder) / "assets" / "PATINA.blend").write_bytes(b"a")
            config, path = self.read(folder, project_root="assets")
            self.assertEqual(path, Path(folder).resolve() / "film.json")
            self.assertEqual(config["project_root"], str(Path(folder).resolve() / "assets"))
            self.assertEqual(config["before"], str(Path(folder).resolve() / "assets/Before.blend"))
            for key, value in common.DEFAULTS.items():
                if key != "project_root":
                    self.assertEqual(config[key], value, key)
            self.assertNotIn("blender", config)
            self.assertNotIn("font", config)

    def test_env_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = helpers.write_config(folder)
            with mock.patch.dict(os.environ, {"PATINA_CONFIG": str(path)}):
                config, _ = common.read_config()
            self.assertEqual(len(config["shots"]), 2)
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(common.ConfigError):
                    common.read_config()

    def assert_problem(self, fragment, **overrides):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(common.ConfigError) as caught:
                self.read(folder, **overrides)
        self.assertIn(fragment, str(caught.exception))

    def test_fps_pairing(self):
        self.assert_problem("fps/source_fps", source_fps=10)
        self.assert_problem("fps/source_fps", fps=30, source_fps=30)
        self.assert_problem("fps/source_fps", source_fps=0)
        with tempfile.TemporaryDirectory() as folder:
            config, _ = self.read(folder, source_fps=24)
            self.assertEqual(config["source_fps"], 24)

    def test_shot_seconds_hold_whole_source_frames(self):
        self.assert_problem("whole number of source frames", shot_seconds=5.55)
        self.assert_problem("shot_seconds: must be a positive", shot_seconds=0)

    def test_transition_bounds(self):
        self.assert_problem("transition", transition=-0.1)
        self.assert_problem("transition", transition=5.5)
        self.assert_problem("transition", shot_seconds=2, transition=2)
        self.assert_problem("transition", transition="fast")

    def test_workers(self):
        self.assert_problem("workers: must be 1 or 2", workers=3)
        self.assert_problem("workers: must be 1 or 2", workers=0)

    def test_even_dimensions(self):
        self.assert_problem("width: must be a positive even integer", width=2367)
        self.assert_problem("height: must be a positive even integer", height=1331)
        self.assert_problem("height: must be a positive even integer", height=0)

    def test_shot_endpoint_shape(self):
        bad = helpers.shot("Bad")
        bad["start"][1] = [0, 0, 0]
        self.assert_problem("shots[0].start", shots=[bad])
        bad = helpers.shot("Bad")
        bad["end"][2] = 0
        self.assert_problem("shots[0].end", shots=[bad])
        bad = helpers.shot("Bad")
        bad["end"][0] = [1, 2]
        self.assert_problem("shots[0].end", shots=[bad])
        bad = helpers.shot("Bad")
        del bad["start"]
        self.assert_problem("shots[0].start", shots=[bad])
        self.assert_problem("shots[1]: needs a name", shots=[helpers.shot("Ok"), {"start": 1}])
        self.assert_problem("shots: at least one", shots=[])

    def test_every_problem_is_listed_at_once(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(common.ConfigError) as caught:
                self.read(folder, workers=5, width=3, transition=-1, source_fps=7)
        message = str(caught.exception)
        for fragment in ("workers", "width", "transition", "fps/source_fps"):
            self.assertIn(fragment, message)

    def test_required_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "film.json"
            path.write_text(json.dumps({"shots": [helpers.shot("A")]}))
            with self.assertRaises(common.ConfigError) as caught:
                common.read_config(path)
        self.assertIn("before: required", str(caught.exception))
        self.assertIn("after: required", str(caught.exception))


class FrameTests(unittest.TestCase):
    def config(self, **overrides):
        config = {"shot_seconds": 1.0, "fps": 24, "source_fps": 12, "shots": [1, 2]}
        config.update(overrides)
        return config

    def test_pilot_renders_both_endpoints_of_every_shot(self):
        self.assertEqual(common.expected(self.config(), "pilot"), [1, 24, 25, 48])
        self.assertEqual(common.shot_frames(self.config()), 24)

    def test_run_follows_source_cadence(self):
        self.assertEqual(common.expected(self.config(), "run"), list(range(1, 49, 2)))
        self.assertEqual(common.expected(self.config(source_fps=24), "run"), list(range(1, 49)))
        self.assertEqual(len(common.expected(self.config(shot_seconds=5.5), "run")), 132)


class FingerprintTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.scripts = Path(self.folder.name) / "scripts"
        self.scripts.mkdir()
        (self.scripts / "a.py").write_text("print(1)\n")
        (self.scripts / "notes.txt").write_text("ignored\n")

    def tearDown(self):
        self.folder.cleanup()

    def fingerprint(self, **overrides):
        config, _ = common.read_config(helpers.write_config(self.folder.name, **overrides))
        return common.run_directory(config, self.scripts)

    def test_identical_inputs_give_identical_folder(self):
        first = self.fingerprint()
        self.assertEqual(first, self.fingerprint())
        self.assertEqual(first.parent, Path(self.folder.name).resolve() / "video/automatic")
        self.assertEqual(len(first.name), 16)

    def test_config_change_moves_the_folder(self):
        self.assertNotEqual(self.fingerprint(), self.fingerprint(title="OTHER"))
        self.assertNotEqual(self.fingerprint(), self.fingerprint(samples=48))

    def test_excluded_keys_do_not_move_the_folder(self):
        base = self.fingerprint()
        self.assertEqual(base, self.fingerprint(workers=2))
        self.assertEqual(base, self.fingerprint(blender="/somewhere/blender"))
        self.assertEqual(base, self.fingerprint(ffmpeg="/usr/local/bin/ffmpeg"))

    def test_input_change_moves_the_folder(self):
        base = self.fingerprint()
        (Path(self.folder.name) / "Before.blend").write_bytes(b"edited scene")
        self.assertNotEqual(base, self.fingerprint())

    def test_script_change_moves_the_folder(self):
        base = self.fingerprint()
        (self.scripts / "a.py").write_text("print(2)\n")
        self.assertNotEqual(base, self.fingerprint())
        # Non-Python files next to the scripts do not count.
        (self.scripts / "notes.txt").write_text("changed\n")
        self.assertEqual(self.fingerprint(), self.fingerprint())


class BlenderResolutionTests(unittest.TestCase):
    def test_config_key_wins(self):
        with tempfile.NamedTemporaryFile() as handle:
            with mock.patch.dict(os.environ, {"BLENDER": "/nope"}):
                self.assertEqual(common.resolve_blender({"blender": handle.name}), handle.name)

    def test_configured_but_missing_is_an_error(self):
        with self.assertRaises(FileNotFoundError) as caught:
            common.resolve_blender({"blender": "/definitely/not/here"})
        self.assertIn("/definitely/not/here", str(caught.exception))

    def test_environment_then_path_then_bundle(self):
        with tempfile.NamedTemporaryFile() as handle:
            with mock.patch.dict(os.environ, {"BLENDER": handle.name}):
                self.assertEqual(common.resolve_blender({}), handle.name)
            with mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch.object(common.shutil, "which", return_value=handle.name):
                    self.assertEqual(common.resolve_blender({}), handle.name)
                with mock.patch.object(common.shutil, "which", return_value=None):
                    with mock.patch.object(common, "MACOS_BLENDER", handle.name):
                        self.assertEqual(common.resolve_blender({}), handle.name)

    def test_error_names_every_route(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(common.shutil, "which", return_value=None):
                with mock.patch.object(common, "MACOS_BLENDER", "/Applications/None/Blender"):
                    with self.assertRaises(FileNotFoundError) as caught:
                        common.resolve_blender({})
        message = str(caught.exception)
        for fragment in ("--blender", "BLENDER environment", "PATH", "/Applications/None/Blender"):
            self.assertIn(fragment, message)


def stub_object(name, vertices, polygons, matrix=None):
    identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    return SimpleNamespace(
        name=name,
        matrix_world=matrix or identity,
        data=SimpleNamespace(
            vertices=[SimpleNamespace(co=v) for v in vertices],
            polygons=[SimpleNamespace(vertices=p) for p in polygons],
        ),
    )


class GeometryHashTests(unittest.TestCase):
    def test_hash_tracks_geometry_only(self):
        a = stub_object("Cube", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
        b = stub_object("Cube", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
        self.assertEqual(common.geometry_hash([a]), common.geometry_hash([b]))
        moved = stub_object("Cube", [(0, 0, 0), (1, 0, 0), (0, 1, 0.5)], [(0, 1, 2)])
        self.assertNotEqual(common.geometry_hash([a]), common.geometry_hash([moved]))
        renamed = stub_object("Box", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
        self.assertNotEqual(common.geometry_hash([a]), common.geometry_hash([renamed]))
        other = stub_object("Other", [(2, 2, 2)], [])
        self.assertEqual(common.geometry_hash([a, other]), common.geometry_hash([other, a]))


class DumpTests(unittest.TestCase):
    def test_compact_sorted_json(self):
        self.assertEqual(common.dump({"b": 1, "a": [1, 2]}), '{"a":[1,2],"b":1}')


if __name__ == "__main__":
    unittest.main()
