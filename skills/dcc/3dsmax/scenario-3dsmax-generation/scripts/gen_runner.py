"""gen_runner: runner-side helpers for landing Scenario outputs in 3ds Max.

Plain Python 3.10+, any OS, never imports pymxs. Runs where the agent runs, next to the
Scenario MCP, and prepares files for a 3ds Max channel (batch, mcp-safe, bridge, handoff).

Checked against
reports 05 (Scenario outputs) and 01 section 6 (formats), and sources/3dsmax-version-deltas.md.

    model_format(release, needs_quads=False) -> dict    which 3D file to ask Scenario for
    splat_supported(release) -> bool                     native PLY/SPZ/LCC import (2027.2+)
    asset_dir(project_root, kind, name, day=None) -> str new folder, never reused
    download(url, folder, filename) -> str               saves once, refuses to overwrite
    write_sidecar(asset_path, record) -> str             <file>.scenario.json provenance
    seam_ratio(png_path) -> float                        equirect wrap check (needs Pillow)
    tile_sheet(png_path, out_path) -> str                2 x 2 tiling sheet (needs Pillow)
    scale_factor(measured, target) -> float              uniform scale to a known dimension

CLI:
    python gen_runner.py format 2026.1
    python gen_runner.py seam sky.png
    python gen_runner.py tile albedo.png sheet.png
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
import urllib.request

# Facts behind the rules (file 05, file 01 s6, version deltas):
# - native glTF/GLB import only from 2027.3; FBX and OBJ import natively in every release in scope
# - Scenario's own 3D models expose outputFormat glb/fbx/obj/usdz/stl/ply/blend; quads requested as GLB fail
# - USDZ is export-only in 3ds Max, so it is never an import route
# - Gaussian splat import (PLY, SPZ, LCC) from 2027.2


def _release_tuple(release: str) -> tuple[int, int]:
    m = re.match(r"^\s*(\d{4})(?:\.(\d+))?", str(release))
    if not m:
        raise ValueError(f"unrecognized 3ds Max release: {release!r}")
    return int(m.group(1)), int(m.group(2) or 0)


def model_format(release: str, needs_quads: bool = False) -> dict:
    """Return the 3D output format to request from a Scenario model that exposes `outputFormat`.

    Models without an `outputFormat` field deliver a format their schema does not state:
    check the downloaded extension instead of assuming."""
    rel = _release_tuple(release)
    if needs_quads:
        return {"format": "fbx", "why": "quad topology: GLB with quads is reported to fail; FBX imports in every release"}
    if rel >= (2027, 3):
        return {"format": "glb", "why": "native Khronos glTF importer since 2027.3 (choose the material type in its dialog)"}
    return {
        "format": "fbx",
        "why": "no native glTF import before 2027.3; FBX imports natively (the Khronos open-source plugin is the GLB alternative)",
    }


def splat_supported(release: str) -> bool:
    return _release_tuple(release) >= (2027, 2)


def _slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", text.strip()).strip("_")
    return s or "asset"


def asset_dir(project_root: str, kind: str, name: str, day: str | None = None) -> str:
    """Create <project_root>/generated/<YYYY-MM-DD>/<kind>/<name>[_v002...] and return it.

    An existing folder is never reused, so earlier downloads are never overwritten."""
    day = day or _dt.date.today().isoformat()
    base = os.path.join(project_root, "generated", day, _slug(kind), _slug(name))
    path, n = base, 1
    while os.path.exists(path):
        n += 1
        path = f"{base}_v{n:03d}"
    os.makedirs(path)
    return path


def download(url: str, folder: str, filename: str) -> str:
    """Save a Scenario asset_download URL into folder/filename (redirects followed).

    Refuses to overwrite: pick a new filename instead."""
    dest = os.path.join(folder, filename)
    if os.path.exists(dest):
        raise FileExistsError(dest)
    req = urllib.request.Request(url, headers={"User-Agent": "asset-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=600) as resp, open(dest, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    if os.path.getsize(dest) == 0:
        raise IOError(f"empty download: {dest}")
    return dest


def write_sidecar(asset_path: str, record: dict) -> str:
    """Write <asset>.scenario.json next to the file.

    Expected keys: model_id, model_name, prompt, seed, reference_asset_ids, job_id, asset_id,
    output_format, scenario_skill, generated_on, landed_in (scene file), checks (dict)."""
    out = asset_path + ".scenario.json"
    if os.path.exists(out):
        base, n = asset_path + ".scenario", 2
        while os.path.exists(f"{base}_v{n:03d}.json"):
            n += 1
        out = f"{base}_v{n:03d}.json"
    rec = dict(record)
    rec.setdefault("file", os.path.basename(asset_path))
    rec.setdefault("generated_on", _dt.date.today().isoformat())
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, ensure_ascii=False)
    return out


def seam_ratio(png_path: str) -> float:
    """Mean abs difference of the leftmost and rightmost columns divided by the difference of two
    columns a quarter turn apart. Near 0 means the 360 wraps; above about 0.3 needs a look [added]."""
    from PIL import Image  # optional dependency

    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    px = im.load()

    def coldiff(a: int, b: int) -> float:
        return sum(abs(px[a, y][c] - px[b, y][c]) for y in range(h) for c in range(3)) / (h * 3)

    edge = coldiff(0, w - 1)
    ref = coldiff(0, w // 4) or 1e-6
    return edge / ref


def tile_sheet(png_path: str, out_path: str) -> str:
    """Write a 2 x 2 repeat of a texture to judge seams and repeating blobs by eye."""
    from PIL import Image

    if os.path.exists(out_path):
        raise FileExistsError(out_path)
    im = Image.open(png_path)
    w, h = im.size
    sheet = Image.new(im.mode, (w * 2, h * 2))
    for dx in (0, w):
        for dy in (0, h):
            sheet.paste(im, (dx, dy))
    sheet.save(out_path)
    return out_path


def scale_factor(measured: float, target: float) -> float:
    if measured <= 0 or target <= 0:
        raise ValueError("measured and target must be positive, in the same unit")
    return target / measured


def _main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "format":
        print(json.dumps(model_format(argv[1], "--quads" in argv)))
        return 0
    if len(argv) == 2 and argv[0] == "seam":
        print(f"{seam_ratio(argv[1]):.3f}")
        return 0
    if len(argv) == 3 and argv[0] == "tile":
        print(tile_sheet(argv[1], argv[2]))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
