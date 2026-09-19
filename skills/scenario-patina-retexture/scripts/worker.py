"""Blender-side renderer for one pass of the comparison film. film.py launches it.

    blender --factory-startup --background <scene.blend> --python-exit-code 1 \
        --python scripts/worker.py -- <mode> <frames.json> <run_dir> <pilot|run> [config.json]

<mode> is "original" or "patina". The config path falls back to $PATINA_CONFIG so a manual
invocation still works. Frames already on disk are skipped, which is what makes a run
resumable.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import dump, read_config  # noqa: E402
from scene import setup  # noqa: E402


def contract_path(run_dir: Path, mode: str) -> Path:
    return run_dir / f"{mode}_contract.json"


def native_scene_path(run_dir: Path, mode: str) -> Path:
    return run_dir / f"{mode.title()} Camera Animation.blend"


def record_contract(run_dir: Path, mode: str, contract: dict) -> None:
    """First worker writes the contract; every later one must reproduce it exactly."""
    path = contract_path(run_dir, mode)
    if path.exists():
        if json.loads(path.read_text()) != contract:
            raise RuntimeError(f"{path}: contract mismatch, this run folder is another rig's")
        return
    path.write_text(json.dumps(contract, indent=2))


def render_frames(scene, frames: list[int], folder: Path, mode: str) -> int:
    import bpy

    folder.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rendered = 0
    for frame in frames:
        target = folder / f"{frame:04d}.png"
        if target.exists():
            continue
        scene.frame_set(frame)
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        rendered += 1
        elapsed = round(time.monotonic() - started, 2)
        print(dump({"pass": mode, "frame": frame, "elapsed": elapsed}), flush=True)
    return rendered


def main(argv: list[str]) -> dict:
    import bpy

    if len(argv) not in (4, 5):
        raise SystemExit(
            "usage: ... --python worker.py -- <mode> <frames.json> <run_dir> <pilot|run> [config]"
        )
    mode, frame_file, run_dir, kind = argv[:4]
    config_path = argv[4] if len(argv) == 5 else os.environ.get("PATINA_CONFIG")
    config, _ = read_config(config_path)
    run = Path(run_dir)
    scene, _, contract = setup(config, mode, preview=kind == "pilot")
    record_contract(run, mode, contract)
    native = native_scene_path(run, mode)
    if kind != "pilot" and not native.exists():
        scene.render.resolution_percentage = 100
        bpy.ops.wm.save_as_mainfile(filepath=str(native))
    frames = json.loads(Path(frame_file).read_text())
    folder = run / ("pilot" if kind == "pilot" else "frames") / mode
    rendered = render_frames(scene, frames, folder, mode)
    return {"pass": mode, "kind": kind, "requested": len(frames), "rendered": rendered}


def script_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


if __name__ == "__main__":
    print(dump(main(script_args())), flush=True)
