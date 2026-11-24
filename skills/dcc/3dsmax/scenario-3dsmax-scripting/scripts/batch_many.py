#!/usr/bin/env python3
"""batch_many: run one in-Max job over many .max files, one 3dsmaxbatch process per file.

Runner side: plain Python 3.10+, never imports pymxs. Uses the lead toolkit
(scenario-3dsmax-expert/scripts: max_wrap.wrap, max_batch.run_batch) and adds what a
studio batch needs: a file list, skip-existing, parallel workers, one retry, a
summary JSON and CSV. One process per file keeps a crash, a modal dialog or a leak to
one file.

status: not yet run against 3ds Max; checked against scripting-pipeline__3dsmaxbatch-2020.md
and the toolkit contract in skills/_SKILL_WRITING_BRIEF.md.

Usage:
    python batch_many.py --job job_chunk.py --kit audit,xio,capture,maxkit_scripting \
        --out <out_dir> [--workers 2] [--timeout 1800] [--dry-run] <scene.max or folder> ...
The job chunk is a pymxs snippet that sets `result`; it reads its arguments with
cmd_args() from maxkit_scripting (keys: outdir, stem). Each file gets <out>/<stem>.json.
Lead kit names go to max_wrap; maxkit_scripting (this skill) is prepended to the chunk.
A failed file is retried once unless the exit code says a retry cannot help (-100, -130).
"""
import argparse
import concurrent.futures as cf
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = os.path.normpath(os.path.join(HERE, "..", "..", "scenario-3dsmax-expert", "scripts"))
sys.path.insert(0, LEAD)


def _toolkit():
    try:
        import max_wrap  # noqa: F401
        import max_batch  # noqa: F401
    except ImportError as exc:
        raise SystemExit("lead toolkit not found in %s (%s); install scenario-3dsmax-expert" % (LEAD, exc))
    return max_wrap, max_batch


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for d, _, files in os.walk(p):
                out += [os.path.join(d, f) for f in files if f.lower().endswith(".max")]
        elif p.lower().endswith(".max"):
            out.append(p)
    return sorted(set(os.path.abspath(p) for p in out))


LOCAL_KIT = {"maxkit_scripting"}  # this skill's in-Max modules; max_wrap only knows the lead's kit


def split_kit(kit):
    """Return (lead kit names for max_wrap, source text of this skill's modules to prepend)."""
    lead, local = [], []
    for k in kit:
        if k in LOCAL_KIT:
            with open(os.path.join(HERE, k + ".py"), encoding="utf-8") as fh:
                local.append(fh.read())
        else:
            lead.append(k)
    return lead, "\n\n".join(local)


def _read_result(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def run_one(scene, chunk, kit, out_dir, timeout, dry_run):
    max_wrap, max_batch = _toolkit()
    stem = os.path.splitext(os.path.basename(scene))[0]
    result_path = os.path.join(out_dir, stem + ".json")
    if os.path.exists(result_path):
        return {"scene": scene, "status": "skipped", "result": result_path}
    lead_kit, prelude = split_kit(kit)
    code = (prelude + "\n\n" + chunk) if prelude else chunk
    script_path = os.path.join(out_dir, "_jobs", stem + "_job.py")
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(max_wrap.wrap(code, lang="python", kit=lead_kit, result_path=result_path))
    args = {"outdir": out_dir, "stem": stem}
    if dry_run:
        return {"scene": scene, "status": "dry-run",
                "command": max_batch.command(script_path, scene=scene, args=args)}
    t0 = time.time()
    res, payload, attempt = {}, None, 0
    for attempt in (1, 2):
        # one log folder per file: run_batch names logs by the second, parallel workers would collide
        res = max_batch.run_batch(script_path, scene=scene, args=args, timeout=timeout,
                                  log_dir=os.path.join(out_dir, "_logs", stem))
        payload = _read_result(result_path)
        if res.get("exit_code") == 0 and payload is not None:
            break
        if res.get("exit_code") in (-100, -130) or "not found" in str(res.get("meaning")):
            # bad arguments, a script error or no 3dsmaxbatch: a retry repeats it
            break
    ok = res.get("exit_code") == 0 and bool(payload and payload.get("ok"))
    return {"scene": scene, "status": "ok" if ok else "failed", "attempts": attempt,
            "seconds": round(time.time() - t0, 1), "result": result_path if payload else None,
            "error": (payload or {}).get("error") or res.get("meaning"), "exit_code": res.get("exit_code")}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("inputs", nargs="+")
    p.add_argument("--job", required=True, help="pymxs chunk that sets `result`")
    p.add_argument("--kit", default="maxkit_scripting")
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=1,
                   help="parallel 3dsmaxbatch processes; each uses a license and RAM")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    with open(a.job, encoding="utf-8") as fh:
        chunk = fh.read()
    kit = [k for k in a.kit.split(",") if k]
    a.out = os.path.abspath(a.out)  # 3ds Max runs elsewhere: never pass a relative path
    os.makedirs(a.out, exist_ok=True)
    scenes = collect(a.inputs)
    rows = []
    with cf.ThreadPoolExecutor(max_workers=max(1, a.workers)) as pool:
        futs = {pool.submit(run_one, s, chunk, kit, a.out, a.timeout, a.dry_run): s for s in scenes}
        for f in cf.as_completed(futs):
            try:
                rows.append(f.result())
            except Exception as exc:
                rows.append({"scene": futs[f], "status": "failed", "error": repr(exc)})
    rows.sort(key=lambda r: r["scene"])
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in ("ok", "skipped", "failed", "dry-run")}
    summary = {"total": len(scenes), "counts": counts, "files": rows}
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(a.out, "summary.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["scene", "status", "attempts", "seconds", "exit_code", "error", "result"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("Done. %(ok)d converted, %(skipped)d skipped, %(failed)d failed, %(dry-run)d dry-run." % counts)
    return 0 if counts["failed"] == 0 and len(rows) == len(scenes) else 1


if __name__ == "__main__":
    sys.exit(main())
