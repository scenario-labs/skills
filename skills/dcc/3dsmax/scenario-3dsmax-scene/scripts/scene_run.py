"""scene_run: runner side for scenario-3dsmax-scene (plain Python 3.10+, never imports pymxs).

Builds wrapped scripts that carry maxkit_scene.py, through the lead toolkit
(scenario-3dsmax-expert/scripts: max_wrap.wrap, max_batch.run_batch).

    from scene_run import make, audit_script
    script = make('result = {"scene": audit_scene()}', result_path="out/audit.json")

CLI, headless intake audit of one .max file (channel batch):
    python scene_run.py audit <scene.max> <out_dir> [--far-cm 100000]
        (far cm = the spec's max_far_m x 100; exits 1 unless out_dir/scene_audit.json reads ok)
    python scene_run.py write-audit <out_dir>        # handoff: write the script only

checked against the toolkit contract of scenario-3dsmax-expert (wrap, run_batch, result protocol).
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEAD = HERE.parents[1] / "scenario-3dsmax-expert" / "scripts"
if LEAD.is_dir() and str(LEAD) not in sys.path:
    sys.path.insert(0, str(LEAD))


def kit_source():
    """maxkit_scene.py source, prepended to every chunk (works whatever wrap inlines)."""
    return (HERE / "maxkit_scene.py").read_text(encoding="utf-8")


def make(body, kit=("audit", "stats"), result_path=None, lang="python"):
    """Return one self-contained script: maxkit_scene + body, wrapped by the lead."""
    if lang != "python":
        raise ValueError("maxkit_scene is pymxs; for mcp-safe use scripts/mxs/*.ms")
    from max_wrap import wrap  # lead toolkit
    return wrap(kit_source() + "\n" + body, lang="python", kit=list(kit),
                result_path=result_path)


def audit_script(out_dir, far_cm=100000.0):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    body = (
        "result = {'scene': audit_scene(far_cm=%r)}\n"
        "try:\n"
        "    result['audit'] = audit.all()\n"
        "    result['stats'] = stats.snapshot()\n"
        "except NameError:\n"
        "    result['kit'] = 'lead maxkit not inlined'\n" % float(far_cm)
    )
    return make(body, result_path=str(out / "scene_audit.json"))


def mxs_audit_script(kit=("audit",)):
    """mcp-safe form: scripts/mxs/scene_audit.ms inside the lead's MAXScript result protocol.
    The block's string becomes `result`; the wrapper returns the JSON envelope as its value."""
    from max_wrap import wrap  # lead toolkit
    lines = (HERE / "mxs" / "scene_audit.ms").read_text(encoding="utf-8").splitlines()
    block = "\n".join(s for s in lines if not s.lstrip().startswith("--") or s.startswith("\t"))
    return wrap("result = " + block.strip(), lang="maxscript", kit=list(kit),
                label="scene audit (read only)", undo=False)


def audit_exit_code(res, envelope_path):
    """0 only when run_batch succeeded and the envelope the audit script wrote reads ok."""
    if not (isinstance(res, dict) and res.get("ok")):
        return 1
    try:
        with open(envelope_path, encoding="utf-8") as fh:
            env = json.load(fh)
    except (OSError, ValueError) as exc:
        print("audit result unreadable: %s" % exc)
        return 1
    if not (isinstance(env, dict) and env.get("ok") is True):
        print("audit failed: %s" % (env.get("error") if isinstance(env, dict) else env))
        return 1
    return 0


def main(argv):
    if len(argv) >= 3 and argv[1] == "write-audit":
        out = pathlib.Path(argv[2])
        script = audit_script(out)
        path = out / "scene_audit_handoff.py"
        if path.exists():
            raise SystemExit("refusing to overwrite %s" % path)
        path.write_text(script, encoding="utf-8")
        print(path)
        return 0
    if len(argv) >= 4 and argv[1] == "audit":
        far = float(argv[argv.index("--far-cm") + 1]) if "--far-cm" in argv else 100000.0
        envelope = pathlib.Path(argv[3]) / "scene_audit.json"
        if envelope.exists():  # a stale result would read as this run's
            raise SystemExit("refusing to overwrite %s" % envelope)
        from max_batch import run_batch  # lead toolkit
        res = run_batch(audit_script(argv[3], far), scene=argv[2], log_dir=argv[3],
                        args={"result_path": str(envelope)}, require_result=True)
        print(res)
        return audit_exit_code(res, envelope)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
