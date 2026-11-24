"""Arrival check for a PBR texture set, before any of it enters 3ds Max.

Runner side: plain Python 3.10+, any OS, never imports pymxs.
status: runs outside 3ds Max.

    scan(folder)                 -> report dict (roles, color role per file, sizes, warnings)
    tagged_copy(report, out_dir) -> copies files to a NEW folder with _srgb / _raw / _lin_srgb
                                    suffixes (V-Ray bitmap name tags, QuJe2j7SHZ0 00:04:19);
                                    never renames or overwrites the originals
    seam_preview(path, out)      -> 2 x 2 tiled image to judge the seam (needs Pillow,
                                    else returns the ImageMagick command to run)

CLI: python3 pbr_set.py <folder> [--json report.json] [--tag-copy <out_dir>]
"""
from __future__ import annotations

import json
import os
import re
import shutil
import struct
import sys

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".hdr", ".tga", ".webp", ".bmp"}

# Order matters: the first matching role wins. Tokens are matched on word-ish boundaries
# of the file stem (split on _ - . space and camelCase).
ROLE_TOKENS = [
    ("orm", ["orm", "arm", "occlusionroughnessmetallic"]),
    ("normal", ["normal", "nrm", "nor", "normalgl", "normaldx", "nrm16", "norm"]),
    ("roughness", ["roughness", "rough", "rgh"]),
    ("gloss", ["gloss", "glossiness", "smoothness"]),
    ("metalness", ["metalness", "metallic", "metal", "mtl"]),
    ("height", ["height", "disp", "displacement", "disp16", "bump", "hgt"]),
    ("ao", ["ao", "ambientocclusion", "occlusion"]),
    ("opacity", ["opacity", "alpha", "mask", "cutout"]),
    ("emission", ["emission", "emissive", "emit", "illum"]),
    ("specular", ["specular", "spec", "refl", "reflection"]),
    ("base_color", ["basecolor", "base", "albedo", "diffuse", "diff", "color", "colour", "col"]),
]

# Data maps are Raw / no transfer function; color maps are sRGB (QuJe2j7SHZ0 00:06:39;
# dlwDiLsPWgI 00:07:08; aHgu1dwjzSo 00:03:59).
DATA_ROLES = {"orm", "normal", "roughness", "gloss", "metalness", "height", "ao", "opacity"}
COLOR_ROLES = {"base_color", "emission", "specular"}

TAG_SUFFIX = {"color": "_srgb", "data": "_raw", "linear_color": "_lin_srgb"}


def _tokens(stem: str) -> list[str]:
    stem = re.sub(r"([a-z])([A-Z])", r"\1_\2", stem)
    return [t for t in re.split(r"[_\-. ]+", stem.lower()) if t]


def _role(stem: str) -> str | None:
    toks = _tokens(stem)
    joined = "".join(toks)
    # The role token is usually last ("brushed_metal_basecolor_2k"), so read from the end.
    for tok in reversed(toks):
        for role, keys in ROLE_TOKENS:
            if tok in keys:
                return role
    # second pass on the joined stem for names like "woodBaseColor"
    for role, keys in ROLE_TOKENS:
        for k in keys:
            if len(k) >= 5 and k in joined:
                return role
    return None


def _existing_tag(stem: str) -> str | None:
    low = stem.lower()
    for tag in ("_lin_srgb", "_srgb", "_raw", "_acescg"):
        if low.endswith(tag):
            return tag
    return None


def _normal_convention(stem: str) -> str:
    toks = _tokens(stem)
    if "dx" in toks or "directx" in toks or "normaldx" in toks:
        return "directx"
    if "gl" in toks or "opengl" in toks or "normalgl" in toks:
        return "opengl"
    return "unknown"


def image_size(path: str) -> tuple[int, int] | None:
    """Width and height for PNG and JPEG without third-party modules; None otherwise."""
    try:
        with open(path, "rb") as f:
            head = f.read(26)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return int(w), int(h)
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        f.read(3)
                        h, w = struct.unpack(">HH", f.read(4))
                        return int(w), int(h)
                    seg_len = struct.unpack(">H", f.read(2))[0]
                    f.seek(seg_len - 2, 1)
    except (OSError, struct.error):
        return None
    try:  # optional, for TIFF, EXR via plugins, WEBP
        from PIL import Image  # type: ignore

        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def scan(folder: str) -> dict:
    files = sorted(
        os.path.join(folder, n)
        for n in os.listdir(folder)
        if os.path.splitext(n)[1].lower() in IMAGE_EXT and not n.startswith(".")
    )
    maps: dict[str, list[dict]] = {}
    unknown: list[str] = []
    warnings: list[str] = []
    for p in files:
        stem, ext = os.path.splitext(os.path.basename(p))
        role = _role(stem)
        if role is None:
            unknown.append(p)
            continue
        entry = {
            "path": p,
            "ext": ext.lower(),
            "color_role": "data" if role in DATA_ROLES else "color",
            "existing_tag": _existing_tag(stem),
            "size": image_size(p),
        }
        if role == "normal":
            entry["normal_convention"] = _normal_convention(stem)
        maps.setdefault(role, []).append(entry)

    roles = set(maps)
    if "base_color" not in roles:
        warnings.append("no base color map found: check names or the unknown list")
    if "roughness" in roles and "gloss" in roles:
        warnings.append("both roughness and gloss maps: pick one and set the material mode to match it")
    if "gloss" in roles and "roughness" not in roles:
        warnings.append("gloss only: use a glossiness-mode material (VRayMtl default, Corona Glossiness mode) or invert for OpenPBR/Physical")
    if "normal" in roles:
        for e in maps["normal"]:
            if e.get("normal_convention") == "unknown":
                warnings.append(f"normal convention unknown for {os.path.basename(e['path'])}: check green channel (DirectX vs OpenGL) on a render")
            elif e.get("normal_convention") == "directx":
                warnings.append(f"{os.path.basename(e['path'])} is DirectX: flip green in the normal node")
    if "height" in roles and "normal" in roles:
        warnings.append("height and normal both present: use normal for shading; height only for displacement on close-ups")
    if "ao" in roles:
        warnings.append("AO map present: do not multiply into base color for a path tracer by default; keep it for masks (expert practice differs, see expert-notes)")
    if "orm" in roles:
        warnings.append("packed ORM/ARM map: split channels (R=AO, G=roughness, B=metalness) before wiring, or use the glTF Material")
    if "specular" in roles and "metalness" not in roles:
        warnings.append("spec/gloss set: physical plausibility not guaranteed (autodesk-pbr-materials); prefer metal/rough")
    for role, entries in maps.items():
        if len(entries) > 1:
            warnings.append(f"{len(entries)} files for role {role}: resolution variants or a naming clash")

    sizes = {e["size"] for es in maps.values() for e in es if e["size"]}
    if len(sizes) > 1:
        warnings.append(f"mixed resolutions in set: {sorted(sizes)}")
    for s in sizes:
        w, h = s
        if w != h:
            warnings.append(f"non-square map {w}x{h}: real-world size needs two numbers")
        if w & (w - 1) or h & (h - 1):
            warnings.append(f"size {w}x{h} is not a power of two (fine for offline render, check for game engines)")
    for e in maps.get("normal", []):
        if e["ext"] in (".jpg", ".jpeg"):
            warnings.append(f"{os.path.basename(e['path'])}: 8-bit JPEG normal map, expect banding on glossy surfaces")
    if unknown:
        warnings.append(f"{len(unknown)} files with no recognised role: {[os.path.basename(u) for u in unknown]}")
    warnings.append("real-world size is not in the files: get it from the source (or decide it) before mapping")
    return {"folder": folder, "maps": maps, "unknown": unknown, "warnings": warnings}


def tagged_copy(report: dict, out_dir: str) -> dict:
    """Copy each recognised file to out_dir with a color-space tag. Never overwrites."""
    os.makedirs(out_dir, exist_ok=True)
    done, skipped = [], []
    for role, entries in report["maps"].items():
        for e in entries:
            stem, ext = os.path.splitext(os.path.basename(e["path"]))
            if e["existing_tag"]:
                new = stem + ext
            else:
                new = stem + TAG_SUFFIX[e["color_role"]] + ext
            dst = os.path.join(out_dir, new)
            if os.path.exists(dst):
                skipped.append(dst)
                continue
            shutil.copy2(e["path"], dst)
            done.append({"role": role, "src": e["path"], "dst": dst})
    return {"copied": done, "skipped_existing": skipped}


def seam_preview(path: str, out: str) -> str:
    """Write a 2 x 2 tile of the image to out. Returns out, or a command if Pillow is missing."""
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return f'magick montage "{path}" "{path}" "{path}" "{path}" -tile 2x2 -geometry +0+0 "{out}"'
    if os.path.exists(out):
        raise FileExistsError(out)
    with Image.open(path) as im:
        w, h = im.size
        sheet = Image.new(im.mode, (w * 2, h * 2))
        for x in (0, w):
            for y in (0, h):
                sheet.paste(im, (x, y))
        sheet.save(out)
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    folder = argv[0]
    rep = scan(folder)
    if "--tag-copy" in argv:
        rep["tag_copy"] = tagged_copy(rep, argv[argv.index("--tag-copy") + 1])
    text = json.dumps(rep, indent=2, default=str)
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
        if os.path.exists(out):
            raise FileExistsError(out)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
