"""maxkit.capture: viewport grabs and renders to PNG for visual review (pymxs, main thread only).

Status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-renderer-2027.md
(viewport.getViewportDib, viewport.getType, render outputFile:, renderers),
scripting-pipeline__maxscript-bitmap-values-2027.md (filename then save, close, copy) and
scripting-pipeline__maxscript-viewport-drawing-methods-getviewportdib-2027.md.

    viewport(path, view=None, size=None) -> {"path", "width", "height", "view"}
    views(dir, views=("persp", "front", "left", "top"), size=None, stem="view") -> [dict, ...]
    render(path, camera=None, size=None) -> {"path", "renderer", "camera", "width", "height"}

Rules: no viewport exists in 3ds Max Batch (views and viewport raise there; use render).
Never overwrite: an existing path gets a _v002 style suffix (next_free). An Arnold render can
crash 3ds Max: save a new increment before render() (max-mcp-known-limitations-2027-3).
"""
from __future__ import annotations

import contextlib
import os
import re

VIEW_TYPES = {  # short name -> viewport type name  [verify] the #view_* names are not in the saved docs
    "persp": "view_persp_user", "front": "view_front", "back": "view_back", "left": "view_left",
    "right": "view_right", "top": "view_top", "bottom": "view_bottom", "camera": "view_camera",
}


def next_free(path: str) -> str:
    """Pure: path if free, else the first stem_v002.ext, stem_v003.ext ... that does not exist."""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    m = re.match(r"^(.*)_v(\d{3,})$", stem)
    base, n = (m.group(1), int(m.group(2))) if m else (stem, 1)
    while True:
        n += 1
        cand = f"{base}_v{n:03d}{ext}"
        if not os.path.exists(cand):
            return cand


def fit_size(w: int, h: int, size) -> tuple[int, int]:
    """Pure: target size. size None keeps (w, h); an int is the long side; a pair is exact."""
    if size is None:
        return int(w), int(h)
    if isinstance(size, (int, float)):
        s = float(size) / max(w, h)
        return max(1, round(w * s)), max(1, round(h * s))
    return int(size[0]), int(size[1])


def _rt():
    from pymxs import runtime as rt
    return rt


def _interactive(rt) -> bool:
    try:
        return not bool(rt.maxops.isInNonInteractiveMode())
    except Exception:
        return True


def _save_bitmap(rt, bmp, path, size=None):
    w, h = int(bmp.width), int(bmp.height)  # [verify] bitmap .width/.height
    tw, th = fit_size(w, h, size)
    out = bmp
    if (tw, th) != (w, h):
        out = rt.bitmap(tw, th)
        rt.copy(bmp, out, quality=rt.Name("high"))  # copy src dest quality: (2027)
    path = next_free(os.fspath(path))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    out.filename = path  # set format options before filename, filename before save
    rt.save(out)
    rt.close(out)
    if out is not bmp:
        rt.close(bmp)
    return path, tw, th


def viewport(path, view=None, size=None) -> dict:
    """Grab the active viewport (optionally switched to a view and framed) as PNG."""
    rt = _rt()
    if not _interactive(rt):
        raise RuntimeError("no viewport in 3ds Max Batch; use capture.render")
    if view:
        rt.viewport.setType(rt.Name(VIEW_TYPES.get(view, view)))  # [verify] viewport.setType
        rt.execute("max tool zoomextents all")
    rt.redrawViews()
    dib = rt.viewport.getViewportDib(captureAlpha=False, gammaCorrect=True)
    saved, w, h = _save_bitmap(rt, dib, path, size)
    return {"path": saved, "width": w, "height": h, "view": view or "active"}


def views(dir, views=("persp", "front", "left", "top"), size=None, stem="view") -> list:  # noqa: A002
    """Several framed views of the scene, then restore the original viewport type."""
    rt = _rt()
    if not _interactive(rt):
        raise RuntimeError("no viewport in 3ds Max Batch; use capture.render with cameras")
    original = rt.viewport.getType()
    out = []
    try:
        for v in views:
            out.append(viewport(os.path.join(os.fspath(dir), f"{stem}_{v}.png"), view=v, size=size))
    finally:
        with contextlib.suppress(Exception):
            rt.viewport.setType(original)  # [verify] viewport.setType
            rt.redrawViews()
    return out


def render(path, camera=None, size=None) -> dict:
    """Render through a camera (name or node) to a new file with the current renderer.

    Does not touch Render Setup: size goes to the render() call only. Save first."""
    rt = _rt()
    cam = rt.getNodeByName(camera) if isinstance(camera, str) else camera
    if isinstance(camera, str) and cam is None:
        raise ValueError(f"camera {camera!r} not found")
    kw = {"outputFile": next_free(os.fspath(path)), "vfb": False}  # [verify] vfb: keyword
    if cam is not None:
        kw["camera"] = cam  # [verify] camera: keyword
    if size is not None:
        w, h = fit_size(int(rt.renderWidth), int(rt.renderHeight), size)  # [verify] renderWidth/renderHeight
        kw["outputwidth"], kw["outputheight"] = w, h  # [verify] outputwidth/outputheight keywords
    os.makedirs(os.path.dirname(kw["outputFile"]) or ".", exist_ok=True)
    bmp = rt.render(**kw)
    info = {"path": kw["outputFile"], "renderer": str(rt.classOf(rt.renderers.current)),
            "camera": str(cam.name) if cam is not None else None,
            "width": int(bmp.width) if bmp is not None else None,
            "height": int(bmp.height) if bmp is not None else None}
    with contextlib.suppress(Exception):
        rt.close(bmp)
    return info
