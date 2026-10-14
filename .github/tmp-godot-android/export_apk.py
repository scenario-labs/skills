"""Temporary: one real Android debug export through the ported gd_perf helpers. Drop before merge."""

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
G = REPO / "skills" / "game-engines" / "godot"
sys.path[:0] = [str(G / "scenario-godot-expert" / "scripts"), str(G / "scenario-godot-performance-export" / "scripts")]

import gd_env  # noqa: E402
import gd_perf  # noqa: E402
import gd_run  # noqa: E402


def step(label, value):
    print(f"STEP {label} " + json.dumps(value, default=str)[:3000], flush=True)
    return value


work = Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()) / "apk"
P = gd_env.new_project(work / "Apk3D", template="3d", isolate_user=True)
gd_env.set_project_setting(P, "rendering/textures/vram_compression/import_etc2_astc", "true")
step("import", gd_run.import_project(P)["ok"])
step("templates", str(gd_env.install_templates()))
assert gd_env.templates_ok(platforms=("android",))
a = step("find_android", gd_perf.find_android())
assert a["ok"], a["problems"]
k = step("keystore", gd_perf.make_keystore(work / "keys" / "debug.keystore", "androiddebugkey", "android", jdk=a["jdk"]))
assert k["ok"], k
pr = gd_run.ensure_preset(P, "Android", "Android", options={
    "gradle_build/use_gradle_build": False, "architectures/arm64-v8a": True,
    "package/unique_name": "com.example.apk3d", "version/code": 1, "version/name": "0.1.0"})
assert step("preset", pr["ok"]), pr["error"]
gd_perf.preset_fields(P, "Android", exclude_filter='"*.agent_out/*, addons/agentkit/*"')
home = gd_perf.private_home(work / "home")
r = gd_perf.export_android(P, "Android", work / "builds" / "apk3d-debug.apk", debug=True,
                           keystore={"path": k["path"], "alias": "androiddebugkey", "password": "android"}, home=home, android=a)
step("export", {key: v for key, v in r.items() if key not in ("export", "prints")})
config = gd_perf._godot_dirs(home)[0]
step("private_settings", sorted(p.name for p in config.iterdir()))
apk = r.get("apk") or {}
summary = {"ok": bool(r.get("ok") and apk.get("ok") and apk.get("signer_sha256") == k["sha256"]),
           "bytes": apk.get("bytes"), "package": apk.get("package"), "abis": apk.get("abis"),
           "schemes": apk.get("schemes"), "debuggable": apk.get("debuggable"),
           "signer_matches_keystore": apk.get("signer_sha256") == k["sha256"]}
print("SUMMARY " + json.dumps(summary))
sys.exit(0 if summary["ok"] else 1)
