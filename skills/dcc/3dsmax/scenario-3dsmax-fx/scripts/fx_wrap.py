#!/usr/bin/env python3
"""fx_wrap: wrap a pymxs chunk with this skill's maxkit_fx helpers bound as `maxkit_fx`.

Runner side: plain Python 3.10+, any OS, never imports pymxs.
checked against scenario-3dsmax-expert/scripts/max_wrap.py 0.1.0

Thin call to the lead's max_wrap.wrap(code, kit=["maxkit_fx", ...], kit_dirs=[this scripts
folder]): max_wrap inlines scripts/maxkit_fx.py as a module bound to `maxkit_fx`, adds the lead
modules it needs, one undo record and the JSON result protocol.

    wrap_fx(code, expert_scripts, kit=(), result_path=None, label="fx change") -> str

CLI:
    python fx_wrap.py chunk.py --expert-scripts <path to scenario-3dsmax-expert/scripts>
                      [--kit stats,audit] [--result result.json] [--out wrapped.py]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def wrap_fx(code: str, expert_scripts, kit=(), result_path=None, label: str = "fx change") -> str:
    sys.path.insert(0, str(Path(expert_scripts).resolve()))
    from max_wrap import wrap  # the lead's toolkit

    return wrap(code, lang="python", kit=["maxkit_fx", *kit], result_path=result_path,
                label=label, kit_dirs=[HERE])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("chunk")
    ap.add_argument("--expert-scripts", required=True)
    ap.add_argument("--kit", default="")
    ap.add_argument("--result", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default="fx change")
    a = ap.parse_args()
    kit = [k for k in a.kit.split(",") if k]
    script = wrap_fx(Path(a.chunk).read_text(encoding="utf-8"), a.expert_scripts, kit, a.result, a.label)
    if a.out:
        Path(a.out).write_text(script, encoding="utf-8")
        print(a.out)
    else:
        print(script)


if __name__ == "__main__":
    main()
