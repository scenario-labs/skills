#!/usr/bin/env python3
"""anim_wrap: wrap an animation or rigging chunk with the lead's max_wrap, plus maxkit_anim.

Runner side: plain Python 3.10+, any OS, never imports pymxs.

    wrap_anim(code, kit=(), result_path=None, label="anim change", undo=True) -> str

The chunk can call `maxkit_anim.<fn>` as well as the lead's kit modules named in `kit`
("result", "stats", "capture", "audit", "xio"). Python only: the MAXScript procedures in
references/procedures.md go to max_wrap.wrap(code, lang="maxscript") directly.

Looks for the lead skill next to this one (../../scenario-3dsmax-expert/scripts) unless
MAX_EXPERT_SCRIPTS points elsewhere.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _lead_scripts() -> Path:
    env = os.environ.get("MAX_EXPERT_SCRIPTS")
    if env:
        return Path(env)
    return HERE.parent.parent / "scenario-3dsmax-expert" / "scripts"


def wrap_anim(code: str, kit=(), result_path=None, label: str = "anim change", undo: bool = True) -> str:
    """Return one self-contained pymxs script: maxkit_anim plus the chunk inside max_wrap.

    A thin call to the lead's max_wrap.wrap with maxkit_anim found in this skill's scripts/."""
    lead = _lead_scripts()
    if str(lead) not in sys.path:
        sys.path.insert(0, str(lead))
    import max_wrap  # the lead's wrapper (scenario-3dsmax-expert)

    kit = [k for k in kit if k != "maxkit_anim"] + ["maxkit_anim"]
    return max_wrap.wrap(code, lang="python", kit=kit, result_path=result_path, label=label,
                         undo=undo, kit_dirs=[HERE])


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Wrap a pymxs chunk with maxkit_anim and the lead toolkit.")
    ap.add_argument("chunk", help="path to a .py chunk")
    ap.add_argument("out", help="path of the wrapped script to write (never overwrites)")
    ap.add_argument("--kit", default="", help="comma-separated lead kit modules, e.g. xio,capture")
    ap.add_argument("--result", default=None, help="result JSON path inside the 3ds Max machine")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"refusing to overwrite {out}; pick a new name (_v002)")
    kit = [k for k in a.kit.split(",") if k]
    out.write_text(wrap_anim(Path(a.chunk).read_text(encoding="utf-8"), kit=kit, result_path=a.result),
                   encoding="utf-8")
    print(out)
