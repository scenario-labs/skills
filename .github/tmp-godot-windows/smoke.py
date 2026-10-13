"""Temporary Windows smoke test for issue #210: drop before merge.

Runs the Godot toolkit on a GitHub-hosted Windows runner and prints one JSON line per step.
Exit code 1 when any required step fails; informational steps never fail the run.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
G = REPO / "skills" / "game-engines" / "godot"
EXPERT = G / "scenario-godot-expert" / "scripts"
sys.path[:0] = [str(EXPERT), str(G / "scenario-godot-multiplayer" / "scripts"), str(G / "scenario-godot-architecture" / "scripts")]

import gd_env  # noqa: E402
import gd_run  # noqa: E402  the import the issue reports as failing

NAME = sys.argv[1]
TMP = Path(tempfile.mkdtemp(prefix="gd_smoke_"))
results = {}


def step(label, fn, required=True):
    t = time.time()
    try:
        v = fn()
        r = {"ok": True, "value": v}
    except Exception as e:  # noqa: BLE001
        r = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    r["required"], r["s"] = required, round(time.time() - t, 1)
    results[label] = r
    print(f"STEP {label} " + json.dumps(r, default=str)[:4000], flush=True)
    return r


def env():
    return {"python": sys.version, "utf8_mode": sys.flags.utf8_mode, "godot": gd_env.find_godot(),
            "version": gd_env.version(), "lock_dir": str(gd_run.LOCK_DIR), "tmp": str(TMP)}


def child(code, extra_env=None):
    e = dict(os.environ, **(extra_env or {}))
    pre = f"import sys; sys.path.insert(0, {str(EXPERT)!r}); import gd_run\n"
    return subprocess.run([sys.executable, "-c", pre + code], capture_output=True, text=True, env=e, timeout=60)


def locks():
    proj = TMP / "lockproj"
    proj.mkdir()
    probe = (f"try:\n    with gd_run.godot_slot({str(proj)!r}, wait=0): print('GOT')\n"
             "except gd_run.GodotBusy as e: print('BUSY', e)")
    pool = ("try:\n    with gd_run.godot_slot(None, wait=0): print('GOT')\n"
            "except gd_run.GodotBusy as e: print('BUSY', e)")
    with gd_run.godot_slot(proj):
        held = child(probe)
        pool_held = child(pool, {"GD_MAX": "1"})
    free = child(probe)
    pool_free = child(pool, {"GD_MAX": "1"})
    out = {k: (v.stdout.strip() or v.stderr.strip()[-500:]) for k, v in
           {"held": held, "free": free, "pool_held": pool_held, "pool_free": pool_free}.items()}
    assert out["held"].startswith("BUSY") and out["free"] == "GOT", out
    assert out["pool_held"].startswith("BUSY") and out["pool_free"] == "GOT", out
    return out


state = {}


def new_project():
    p = gd_env.new_project(TMP / NAME, template="3d", isolate_user=True)
    state["proj"] = p
    assert (p / "main.tscn").exists()
    return {"project": str(p), "files": sorted(x.name for x in p.iterdir())}


def audit():
    r = gd_run.audit(state["proj"], "project")
    assert r["ok"], r["error"]
    assert gd_stat_tag() in r["log"], "no AGENT_RESULT line in the captured stdout"
    return {"log_chars": len(r["log"]), "counts": r["counts"], "cmd": r["cmd"]}


def gd_stat_tag():
    import gd_stat
    return gd_stat.RESULT_TAG


def unicode_job():
    job = state["proj"] / "unicode_job.gd"
    job.write_text('extends "res://addons/agentkit/agent_job.gd"\n\nfunc run() -> Dictionary:\n'
                   '\tprint("UNICODE_PROBE Ё ✓ Проект")\n'
                   '\treturn {"ok": true, "text": "Ё ✓ Проект"}\n', encoding="utf-8")
    r = gd_run.run_script(state["proj"], "unicode_job.gd", timeout=120)
    assert r["ok"], r["error"]
    assert r["result"]["text"] == "Ё ✓ Проект", r["result"]
    assert "UNICODE_PROBE Ё" in r["log"], r["log"][-500:]
    return r["result"]


def check_all():
    r = gd_run.check_all(state["proj"])
    assert r["ok"], r["error"]
    return {"files_checked": r["files_checked"]}


def headless_listed():
    p = subprocess.Popen([gd_env.find_godot(), "--headless", "-e", "--path", str(state["proj"])],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(10)
        procs = gd_run.running_godot()
        gui = gd_run.gui_editor_pids(state["proj"])
    finally:
        p.kill()
        p.wait()
    mine = [x for x in procs if x["pid"] == p.pid]
    assert mine and mine[0]["headless"] and mine[0]["editor"], procs
    assert p.pid not in gui, gui
    return {"pid": p.pid, "procs": procs}


def gui_detected():
    fake = Path(sys.executable).with_name("godot_fake.exe")
    shutil.copy2(sys.executable, fake)
    arg = str(state["proj"]).replace("\\", "/").upper()
    p = subprocess.Popen([str(fake), "-c", "import time; time.sleep(120)", "--path", arg, "-e"])
    try:
        time.sleep(3)
        pids = gd_run.gui_editor_pids(state["proj"])
        try:
            gd_run.run_script(state["proj"], "agent_audit.gd:project", timeout=60)
            refused = None
        except gd_run.GodotBusy as e:
            refused = str(e)
    finally:
        p.kill()
        p.wait()
    assert p.pid in pids, (p.pid, pids, gd_run.running_godot())
    assert refused, "run_script did not refuse a project with a GUI Godot open"
    return {"pid": p.pid, "pids": pids, "refused": refused}


def typing_gate():
    import gd_architecture
    dest = TMP / "gate" / NAME
    r = gd_architecture.typing_gate(state["proj"], dest=dest)
    assert (dest / "project.godot").exists()
    return {k: r.get(k) for k in ("ok", "error", "by_rule") if k in r}


def role_clone():
    import gd_net
    root = TMP / "roles"
    d = gd_net.role_clone(state["proj"], "server", clone_root=root)
    (state["proj"] / "after.txt").write_text("x")
    (state["proj"] / ".agent_out" / "after_out.txt").write_text("x")
    gd_net.role_clone(state["proj"], "server", clone_root=root, refresh=True)
    assert (d / "after.txt").exists(), "refresh did not copy a new file"
    assert not (d / ".agent_out" / "after_out.txt").exists(), "refresh copied .agent_out"
    return str(d)


def capture():
    r = gd_run.capture_scene(state["proj"], "res://main.tscn", out=str(Path(os.environ.get("CAPTURE_DIR", TMP)) / "shot.png"), size=(320, 180), review=False, timeout=120)
    return {"ok": r["ok"], "error": r["error"], "result": r.get("result"), "log_tail": r["log"][-1500:]}


step("env", env)
step("locks", locks)
if step("new_project", new_project)["ok"]:
    step("audit_stdout", audit)
    step("unicode_job", unicode_job)
    step("check_all", check_all)
    step("headless_listed", headless_listed)
    step("gui_detected", gui_detected)
    step("typing_gate", typing_gate)
    step("role_clone", role_clone)
    step("capture_windowed", capture, required=False)

failed = [k for k, v in results.items() if v["required"] and not v["ok"]]
print("SUMMARY " + json.dumps({"failed": failed, "passed": [k for k, v in results.items() if v["ok"]]}))
sys.exit(1 if failed else 0)
