#!/usr/bin/env python3
"""ledger.py BUILD.json GUARD.txt STATUS.csv: the status ledger of a batch, written after the guarded render.

BUILD.json is the output of `ae.py run build.jsx` (or the bare result object). Its result holds
`rows`: one {id, status: "built" | "failed", file, reason} per data row, in data order.
GUARD.txt is the output of render_guarded.sh: one "<file name> <frames found> of <frames expected>" line per output.
A row is `done` only when its file decoded every expected frame; otherwise `failed` with the reason.
Writes id,status,file,frames,reason (UTF-8, quoted where needed). Prints a JSON summary. Exit 1 when a row failed.
Python standard library only.
"""
import csv
import json
import os
import re
import sys


def main(build_path, guard_path, out_path):
    with open(build_path, encoding="utf-8") as f:
        build = json.load(f)
    res = build.get("result", build)
    if build.get("ok") is False:
        raise SystemExit("build job failed: " + str(build.get("error")))
    rows = res.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("BUILD.json has no result.rows list")
    seen = {}
    guard_result = ""
    with open(guard_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r"^(.+) (\d+) of (\d+)$", line)
            if m:
                seen[m.group(1)] = (int(m.group(2)), int(m.group(3)))
            elif line.startswith("RESULT"):
                guard_result = line
    out, done, failed = [], 0, 0
    for r in rows:
        name = os.path.basename(r.get("file") or "")
        row = {"id": r.get("id", ""), "status": "failed", "file": name, "frames": "", "reason": r.get("reason", "")}
        if r.get("status") == "built":
            if name in seen:
                got, want = seen[name]
                row["frames"] = "%d of %d" % (got, want)
                if want > 0 and got == want:
                    row["status"], row["reason"] = "done", ""
                else:
                    row["reason"] = "decoded %d of %d frames" % (got, want)
            else:
                row["reason"] = "not in the render log: %s" % (guard_result or "no RESULT line")
        elif not row["reason"]:
            row["reason"] = "build failed"
        if row["status"] == "done":
            done += 1
        else:
            failed += 1
        out.append(row)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "status", "file", "frames", "reason"], lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(json.dumps({"rows": len(out), "done": done, "failed": failed, "guard": guard_result, "status": out_path}))
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    sys.exit(main(*sys.argv[1:]))
