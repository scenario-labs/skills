"""Offline checks of the scenario-roblox-expert toolkit: window binding and playtest kits.

No Studio runs here: a fake replaces the StudioMCP proxy and lists the windows a test sets.
"""

import pathlib
import sys
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).parents[2] / "skills/game-engines/roblox/scenario-roblox-expert/scripts"
sys.path.insert(0, str(SCRIPTS))

import rbx_env  # noqa: E402
import rbx_mcp  # noqa: E402
import rbx_play  # noqa: E402

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
