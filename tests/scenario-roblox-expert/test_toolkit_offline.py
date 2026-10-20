"""Offline checks of the Roblox toolkit: window binding, playtest kits, and merging a user's place.

No Studio runs here: a fake replaces the StudioMCP proxy and lists the windows a test sets.
"""

import pathlib
import sys
import tempfile
import unittest
from unittest import mock

FAMILY = pathlib.Path(__file__).parents[2] / "skills/game-engines/roblox"
sys.path.insert(0, str(FAMILY / "scenario-roblox-expert/scripts"))
sys.path.insert(0, str(FAMILY / "scenario-roblox-tooling/scripts"))
sys.path.insert(0, str(FAMILY / "scenario-roblox-networking/scripts"))

import rbx_env  # noqa: E402
import rbx_mcp  # noqa: E402
import rbx_net  # noqa: E402
import rbx_play  # noqa: E402
import rbx_tooling  # noqa: E402

USER = {"studio_id": "user-1", "name": "MyObby"}


class FakeStudio(rbx_mcp.Studio):
    """A Studio whose list_roblox_studios answer is the `windows` list."""

    def __init__(self, *args, windows=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.windows = windows if windows is not None else []

    def open(self):
        return self

    def close(self):
        pass

    def studios(self):
        return list(self.windows)


@mock.patch("rbx_mcp.time.sleep", lambda _s: None)
class Bind(unittest.TestCase):
    def test_place_never_binds_a_window_that_only_contains_its_name(self):
        s = FakeStudio(place="Obby.rbxl", windows=[USER])
        with self.assertRaises(rbx_mcp.MCPError):
            s.bind()

    def test_place_binds_its_own_window_by_name_or_stem(self):
        own = {"studio_id": "agent-1", "name": "Obby"}
        self.assertEqual(FakeStudio(place="Obby.rbxl", windows=[USER, own]).bind(), "agent-1")
        self.assertEqual(FakeStudio(place="MyObby.rbxl", windows=[USER, own]).bind(), "user-1")

    def test_studio_flag_keeps_the_substring_fallback(self):
        self.assertEqual(FakeStudio(studio="obby", windows=[USER]).bind(), "user-1")


@mock.patch("rbx_mcp.time.sleep", lambda _s: None)
@mock.patch("rbx_env.time.sleep", lambda _s: None)
@mock.patch("rbx_env.wait_for_gpu", lambda: {})
class OpenPlace(unittest.TestCase):
    def test_opens_the_agent_place_beside_a_user_window_sharing_its_name(self):
        windows = [USER]
        made = []

        def studio(**kwargs):
            made.append(FakeStudio(windows=windows, **kwargs))
            return made[-1]

        def launch(cmd, check):
            windows.append({"studio_id": "agent-1", "name": "Obby"})

        with mock.patch("rbx_env.Studio", studio), mock.patch("rbx_env.subprocess.run", launch):
            s = rbx_env.open_place("/tmp/agent/Obby.rbxl", timeout=30)
        self.assertEqual(s.studio_id, "agent-1")


class MergePlace(unittest.TestCase):
    """The lead routes existing games through merge_place, so it must run in an unscaffolded repo."""

    def run_merge(self, root):
        seen = {}

        def lune(cmd, cwd, **_kwargs):
            script = pathlib.Path(cwd, cmd[2])
            seen.update(cmd=cmd, cwd=cwd, script=script.exists(), shipcheck=(script.parent / "testkit/ShipCheck.luau").exists())
            return mock.Mock(returncode=0, stdout='{"replaced": []}\n', stderr="")

        with mock.patch("rbx_tooling.subprocess.run", lune):
            report = rbx_tooling.merge_place(root, base="base.rbxl", code="code.rbxl", out="out.rbxl",
                                             project="default.project.json")
        return report, seen

    def test_unscaffolded_repo_runs_the_template_script_with_shipcheck(self):
        with tempfile.TemporaryDirectory() as root:
            report, seen = self.run_merge(root)
        self.assertEqual(report["exit"], 0)
        self.assertEqual(seen["cwd"], pathlib.Path(root).resolve())
        self.assertTrue(seen["script"] and seen["shipcheck"], seen)

    def test_scaffolded_repo_keeps_its_own_script(self):
        with tempfile.TemporaryDirectory() as root:
            (pathlib.Path(root) / "tools").mkdir()
            (pathlib.Path(root) / "tools/merge_place.luau").write_text("")
            _report, seen = self.run_merge(root)
        self.assertEqual(seen["cmd"][:3], ["lune", "run", "tools/merge_place"])


class VendorKit(unittest.TestCase):
    def test_copies_netkit_into_the_repository_with_paths_inside_it(self):
        with tempfile.TemporaryDirectory() as root:
            tree = rbx_net.vendor_kit(root, dest="src/server/NetKit")
            for name, node in tree.items():
                if name == "$className":
                    continue
                self.assertEqual(node["$path"], f"src/server/NetKit/{name}.luau")
                self.assertTrue((pathlib.Path(root) / node["$path"]).is_file(), name)
            self.assertIn("Net", tree)


class PlaytestKit(unittest.TestCase):
    def test_server_and_client_forward_kit(self):
        calls = []
        with mock.patch("rbx_play.run", lambda *a: calls.append(a) or {"ok": True}):
            pt = rbx_play.Playtest(FakeStudio())
            pt.server("return 1", kit=["Spec"])
            pt.client("return 2", kit=["Stats"])
        self.assertEqual([(c[2], tuple(c[4])) for c in calls], [("Server", ("Spec",)), ("Client", ("Stats",))])


if __name__ == "__main__":
    unittest.main()
