"""Scaffolding preserves dependency locks and stops on installation failures."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "skills" / "scenario-kinetic-music-video"


class ScaffoldTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.song = self.root / "song.wav"
        self.song.write_bytes(b"song")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        self.log = self.root / "calls.jsonl"
        self.env = {
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "SCAFFOLD_TEST_LOG": str(self.log),
        }
        for tool in ("npm", "uv", "curl", "uname"):
            path = bin_dir / tool
            path.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "tool = Path(sys.argv[0]).name\n"
                "with open(os.environ['SCAFFOLD_TEST_LOG'], 'a') as log:\n"
                "    log.write(json.dumps([tool, *sys.argv[1:]]) + '\\n')\n"
                "if tool == 'uname':\n"
                "    print('Linux')\n"
                "elif tool == 'curl':\n"
                "    Path(sys.argv[sys.argv.index('-o') + 1]).write_bytes(b'font')\n"
                "elif tool == 'npm':\n"
                "    sys.exit(int(os.environ.get('SCAFFOLD_TEST_NPM_EXIT', '0')))\n"
                "elif tool == 'uv' and sys.argv[1] == 'venv':\n"
                "    python = Path('.venv/bin/python')\n"
                "    python.parent.mkdir(parents=True, exist_ok=True)\n"
                "    python.write_text('#!/bin/sh\\nexit 0\\n')\n"
                "    python.chmod(0o755)\n"
            )
            path.chmod(0o755)

    def run_scaffold(self):
        return subprocess.run(
            ["bash", str(SKILL / "scripts/scaffold.sh"), str(self.song)],
            cwd=self.project,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_new_project_uses_shipped_lock_and_repeat_run_preserves_customizations(self):
        result = self.run_scaffold()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("package.json", "package-lock.json"):
            target = self.project / name
            self.assertEqual(target.read_bytes(), (SKILL / "assets/npm" / name).read_bytes())
            content = json.loads(target.read_text())
            content["name"] = "custom-project"
            target.write_text(json.dumps(content))
        result = self.run_scaffold()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("package.json", "package-lock.json"):
            self.assertEqual(json.loads((self.project / name).read_text())["name"], "custom-project")
        npm_calls = [call for call in self.calls() if call[0] == "npm"]
        self.assertEqual(npm_calls, [["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"]] * 2)

    def test_incomplete_dependency_pair_fails_before_copying_project_files(self):
        for name in ("package.json", "package-lock.json"):
            with self.subTest(name=name):
                target = self.project / name
                target.write_text("{}")
                result = self.run_scaffold()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Keep both", result.stderr)
                self.assertEqual(list(self.project.iterdir()), [target])
                target.unlink()

    def test_failed_npm_install_stops_before_python_setup(self):
        self.env["SCAFFOLD_TEST_NPM_EXIT"] = "1"
        result = self.run_scaffold()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(call[0] == "uv" for call in self.calls()))


if __name__ == "__main__":
    unittest.main()
