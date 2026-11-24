"""Runner-side planning math for archviz production (plain Python 3.10+, never imports pymxs).

channel: runner (no 3ds Max needed)
status: runner-side only; checked against gMUKCmaeQhc (Vantage frame budget), ZHCVMQeWPEg (frames x minutes / 60),
        iIYYzosZ1Mo (photo size and EXIF to camera). Not a 3ds Max script.

Functions
- frames_for(seconds, fps) -> int
- shot_ranges(durations_s, fps, start=0, pause_s=0.0) -> list of (first, last) frame ranges
- render_budget(frames, sec_per_frame, nodes=1, margin=1.2) -> dict with hours and a verdict hint
- exif_camera(photo_path) -> dict with render size, focal length, film width, altitude, timestamp (needs exiftool on PATH)
- aerial_camera(width_px, height_px, focal_35mm, altitude_m, ...) -> dict (no exiftool needed)
- chunk(code, args=None) -> str: ARGS + maxkit_archviz.py + code, ready for max_wrap.wrap()

CLI
  python archviz_plan.py budget --seconds 20 --fps 25 --spf 540 --nodes 4
  python archviz_plan.py shots --fps 30 2.5 3 2 4
  python archviz_plan.py exif drone.jpg
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys


def frames_for(seconds: float, fps: float) -> int:
    """Frame count for a clip. 20 s at 25 fps is 500 frames (0..499)."""
    return int(round(seconds * fps))


def shot_ranges(durations_s, fps: float, start: int = 0, pause_s: float = 0.0):
    """Consecutive (first, last) frame ranges for a list of shot durations in seconds."""
    ranges = []
    cursor = start
    for d in durations_s:
        n = frames_for(d + pause_s, fps)
        ranges.append((cursor, cursor + n - 1))
        cursor += n
    return ranges


def render_budget(frames: int, sec_per_frame: float, nodes: int = 1, margin: float = 1.2) -> dict:
    """Total wall time from a measured test frame.

    margin covers frames heavier than the test frame [added]; measure the test frame on the
    heaviest part of the shot, as the experts measure frame 1 before launching
    (gMUKCmaeQhc 00:08:59; ZHCVMQeWPEg 00:09:01).
    """
    total_h = frames * sec_per_frame * margin / 3600.0 / max(nodes, 1)
    if total_h <= 12:
        hint = "local overnight"
    elif total_h <= 48:
        hint = "local only if the deadline allows; consider a farm or a lighter setup"
    else:
        hint = "farm, real-time engine, or cut frames/resolution"
    return {
        "frames": frames,
        "sec_per_frame": sec_per_frame,
        "nodes": nodes,
        "margin": margin,
        "hours": round(total_h, 2),
        "hint": hint,
    }


def aerial_camera(width_px: int, height_px: int, focal_35mm: float, altitude_m: float,
                  film_width_mm: float = 36.0, timestamp: str | None = None) -> dict:
    """Camera plan for matching a drone photo (iIYYzosZ1Mo 00:03:54 to 00:07:21).

    The expert typed the 35 mm-equivalent focal length with a 35 mm film width; pairing the
    35 mm-equivalent focal with a 36 mm film width (full-frame width) is the exact form [added].
    """
    hfov = 2.0 * math.degrees(math.atan(film_width_mm / (2.0 * focal_35mm)))
    return {
        "render_width": int(width_px),
        "render_height": int(height_px),
        "focal_mm": float(focal_35mm),
        "film_width_mm": float(film_width_mm),
        "horizontal_fov_deg": round(hfov, 3),
        "camera_height_m": float(altitude_m),
        "sun_timestamp": timestamp,
        "check": "overlay the render on the photo; adjust only position and rotation, never focal",
    }


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().split(" ")[0].lstrip("+")
    try:
        return float(s)
    except ValueError:
        return None


def exif_camera(photo_path: str) -> dict:
    """Read EXIF with exiftool (must be installed) and return aerial_camera() input and result."""
    exe = shutil.which("exiftool")
    if not exe:
        raise RuntimeError("exiftool not found: read size, 35 mm focal, altitude and time from the photo by hand")
    out = subprocess.run([exe, "-json", "-n", photo_path], capture_output=True, text=True, check=True)
    tags = json.loads(out.stdout)[0]
    w = tags.get("ImageWidth") or tags.get("ExifImageWidth")
    h = tags.get("ImageHeight") or tags.get("ExifImageHeight")
    f35 = _num(tags.get("FocalLengthIn35mmFormat"))
    # DJI writes RelativeAltitude (above takeoff) in XMP; GPSAltitude is above sea level.
    alt = _num(tags.get("RelativeAltitude")) or _num(tags.get("GPSAltitude"))
    ts = tags.get("DateTimeOriginal")
    missing = [k for k, v in {"width": w, "height": h, "focal_35mm": f35, "altitude": alt}.items() if v is None]
    result = {"tags_missing": missing}
    if not missing:
        result.update(aerial_camera(int(w), int(h), f35, alt, timestamp=ts))
    return result


def chunk(code: str, args: dict | None = None, helpers: bool = True) -> str:
    """Build a chunk for max_wrap.wrap(): ARGS literal, then maxkit_archviz.py, then the agent code.

    The lead's wrap() inlines only its own maxkit modules (stats, capture, audit, xio, result) and
    binds them as globals, so this skill's helpers are pasted as plain source above the code.
    Usage: max_wrap.wrap(chunk(code, {"out_dir": d}), kit=["stats", "capture"])
    """
    import textwrap
    from pathlib import Path

    parts = []
    if args is not None:
        parts.append("import json as _json\nARGS = _json.loads(" + repr(json.dumps(args)) + ")\n")
    if helpers:
        parts.append((Path(__file__).resolve().parent / "maxkit_archviz.py").read_text(encoding="utf-8"))
    parts.append(textwrap.dedent(code).strip("\n") + "\n")
    out = "\n".join(parts)
    compile(out, "<archviz chunk>", "exec")  # fail on the runner, not inside 3ds Max
    return out


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("budget")
    b.add_argument("--frames", type=int)
    b.add_argument("--seconds", type=float)
    b.add_argument("--fps", type=float, default=30)
    b.add_argument("--spf", type=float, required=True, help="measured seconds per frame")
    b.add_argument("--nodes", type=int, default=1)
    b.add_argument("--margin", type=float, default=1.2)
    s = sub.add_parser("shots")
    s.add_argument("--fps", type=float, default=30)
    s.add_argument("--pause", type=float, default=0.0)
    s.add_argument("durations", type=float, nargs="+")
    e = sub.add_parser("exif")
    e.add_argument("photo")
    a = p.parse_args(argv)
    if a.cmd == "budget":
        frames = a.frames if a.frames else frames_for(a.seconds or 0, a.fps)
        print(json.dumps(render_budget(frames, a.spf, a.nodes, a.margin), indent=2))
    elif a.cmd == "shots":
        print(json.dumps(shot_ranges(a.durations, a.fps, pause_s=a.pause)))
    else:
        print(json.dumps(exif_camera(a.photo), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
