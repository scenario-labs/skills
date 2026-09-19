"""Shared helpers for the PATINA retexture scripts: film config, fingerprints, hashes.

Standard library only, so film.py can import it outside Blender and the Blender-side
scripts can import it from Blender's bundled Python. Nothing here talks to Scenario.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

MACOS_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"

# Keys that never change what gets rendered, so they stay out of the run fingerprint.
FINGERPRINT_EXCLUDED = ("workers", "blender", "ffmpeg", "ffprobe", "output")

DEFAULTS = {
    "project_root": ".",
    "output": "video/automatic",
    "title": "PBR MATERIAL STUDY",
    "before_label": "Original materials",
    "after_label": "PATINA textures",
    "width": 2368,
    "height": 1332,
    "fps": 24,
    "source_fps": 12,
    "shot_seconds": 5.5,
    "transition": 0.5,
    "samples": 24,
    "workers": 1,
    "rig_scale": 1,
    "rig_origin": [0, 0, 0],
    "ffmpeg": "ffmpeg",
    "ffprobe": "ffprobe",
}


class ConfigError(ValueError):
    """The film config is unusable; the message lists every problem found."""


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_vector3(value) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return False
    return all(is_number(v) for v in value)


def validate_config(config: dict) -> list[str]:
    """Return every problem with a config that already has its defaults applied."""
    problems = []
    for key in ("before", "after"):
        if not isinstance(config.get(key), str) or not config[key]:
            problems.append(f"{key}: required path is missing")
    fps, source_fps = config["fps"], config["source_fps"]
    if fps != 24 or not isinstance(source_fps, int) or source_fps <= 0 or fps % source_fps:
        problems.append("fps/source_fps: use 12 or 24 source fps with 24 fps output")
    shot_seconds = config["shot_seconds"]
    if not is_number(shot_seconds) or shot_seconds <= 0:
        problems.append("shot_seconds: must be a positive number")
    elif isinstance(source_fps, int) and source_fps > 0:
        source_frames = shot_seconds * source_fps
        if int(source_frames) != source_frames:
            problems.append("shot_seconds: must hold a whole number of source frames")
        if is_number(config["transition"]) and not 0 <= config["transition"] < shot_seconds:
            problems.append("transition: must be at least 0 and shorter than shot_seconds")
    if not is_number(config["transition"]):
        problems.append("transition: must be a number")
    if config["workers"] not in (1, 2):
        problems.append("workers: must be 1 or 2")
    for key in ("width", "height"):
        value = config[key]
        if not isinstance(value, int) or value <= 0 or value % 2:
            problems.append(f"{key}: must be a positive even integer")
    if not isinstance(config["samples"], int) or config["samples"] <= 0:
        problems.append("samples: must be a positive integer")
    if not is_number(config["rig_scale"]) or config["rig_scale"] <= 0:
        problems.append("rig_scale: must be a positive number")
    if not is_vector3(config["rig_origin"]):
        problems.append("rig_origin: must be three numbers")
    shots = config.get("shots")
    if not isinstance(shots, list) or not shots:
        problems.append("shots: at least one shot is required")
        return problems
    for index, shot in enumerate(shots):
        label = f"shots[{index}]"
        if not isinstance(shot, dict) or not shot.get("name"):
            problems.append(f"{label}: needs a name")
            continue
        for key in ("start", "end"):
            endpoint = shot.get(key)
            if (
                not isinstance(endpoint, (list, tuple))
                or len(endpoint) != 3
                or not is_vector3(endpoint[0])
                or not is_vector3(endpoint[1])
                or not any(endpoint[1])
                or not is_number(endpoint[2])
                or endpoint[2] <= 0
            ):
                problems.append(
                    f"{label}.{key}: expected [target_xyz, direction_xyz, visible_width > 0]"
                    " with a non-zero direction"
                )
    return problems


def read_config(path: str | os.PathLike | None = None) -> tuple[dict, Path]:
    """Load a film config, resolve its paths, apply defaults and validate it."""
    if path is None:
        path = os.environ.get("PATINA_CONFIG")
        if not path:
            raise ConfigError("Pass the config path or set PATINA_CONFIG")
    config_path = Path(path).resolve()
    config = json.loads(config_path.read_text())
    for key, value in DEFAULTS.items():
        config.setdefault(key, json.loads(json.dumps(value)))
    root = Path(config["project_root"])
    if not root.is_absolute():
        root = (config_path.parent / root).resolve()
    config["project_root"] = str(root)
    for key in ("before", "after"):
        if isinstance(config.get(key), str) and config[key]:
            file = Path(config[key])
            config[key] = str(file if file.is_absolute() else (root / file).resolve())
    problems = validate_config(config)
    if problems:
        raise ConfigError("Invalid film config:\n  " + "\n  ".join(problems))
    return config, config_path


def shot_frames(config: dict) -> int:
    return round(config["shot_seconds"] * config["fps"])


def expected(config: dict, kind: str) -> list[int]:
    """Frame numbers a pass must render: shot endpoints for a pilot, source cadence for a run."""
    count = shot_frames(config)
    shots = len(config["shots"])
    if kind == "pilot":
        return [frame for i in range(shots) for frame in (i * count + 1, (i + 1) * count)]
    return list(range(1, count * shots + 1, config["fps"] // config["source_fps"]))


def file_hash(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_directory(config: dict, scripts_dir: str | os.PathLike | None = None) -> Path:
    """Run folder fingerprinted from the config, the two input scenes and these scripts.

    Anything that changes a rendered pixel changes the folder, so a resume can only ever
    continue an identical production. Packed .blend inputs are what make the input hash
    meaningful: an external texture edit would not move it.
    """
    scripts = Path(scripts_dir) if scripts_dir else Path(__file__).parent
    evidence = {k: v for k, v in config.items() if k not in FINGERPRINT_EXCLUDED}
    evidence["inputs"] = {key: file_hash(config[key]) for key in ("before", "after")}
    evidence["scripts"] = {p.name: file_hash(p) for p in sorted(scripts.glob("*.py"))}
    digest = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()[:16]
    return Path(config["project_root"]) / config["output"] / digest


def resolve_blender(config: dict) -> str:
    """Blender executable: config or --blender, then $BLENDER, then PATH, then the macOS bundle."""
    for label, candidate in (
        ("--blender / config \"blender\"", config.get("blender")),
        ("BLENDER environment variable", os.environ.get("BLENDER")),
    ):
        if candidate:
            if Path(candidate).is_file():
                return str(candidate)
            raise FileNotFoundError(f"{label} points to {candidate}, which does not exist")
    found = shutil.which("blender")
    if found:
        return found
    if Path(MACOS_BLENDER).is_file():
        return MACOS_BLENDER
    raise FileNotFoundError(
        "No Blender executable found. Pass --blender PATH (or set \"blender\" in the config),"
        " set the BLENDER environment variable, put blender on PATH, or install the macOS"
        f" app bundle at {MACOS_BLENDER}"
    )


def geometry_hash(objects) -> str:
    """SHA-256 over every mesh object's name, vertices, polygons and world matrix.

    Material changes leave it untouched; that is the whole point.
    """
    import numpy as np

    digest = hashlib.sha256()
    for obj in sorted(objects, key=lambda o: o.name):
        digest.update(obj.name.encode())
        for vertex in obj.data.vertices:
            digest.update(np.array(vertex.co, dtype=np.float32).tobytes())
        for polygon in obj.data.polygons:
            digest.update(np.array(polygon.vertices, dtype=np.int32).tobytes())
        digest.update(np.array(obj.matrix_world, dtype=np.float32).tobytes())
    return digest.hexdigest()


def dump(data) -> str:
    """Compact JSON for stdout; the agent running the scripts reads it."""
    return json.dumps(data, separators=(",", ":"), sort_keys=True)
