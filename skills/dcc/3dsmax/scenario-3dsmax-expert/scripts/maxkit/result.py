"""maxkit.result: turn pymxs values into JSON-safe data and write the result envelope.

Checked against scripting-pipeline__pymxs-using-2027.md.

    to_jsonable(value, depth=0) -> JSON-safe value
    envelope(ok, result, error, log, max_version) -> dict
    write(payload, path) -> str
    max_version() -> str | None

Pure Python apart from max_version(); safe to import outside 3ds Max.
"""
from __future__ import annotations

import contextlib
import json
import os

_MAX_DEPTH = 8


def to_jsonable(value, depth: int = 0):
    """Convert pymxs wrappers (Point3, Name, MAXScript arrays, nodes) to plain JSON values.

    Point3-like objects (x, y, z attributes) become [x, y, z]; color-like (r, g, b) become
    [r, g, b]; nodes become their name; other wrappers become str(value)."""
    if depth > _MAX_DEPTH:
        return str(value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if value == value and value not in (float("inf"), float("-inf")) else str(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v, depth + 1) for v in value]
    for attrs in (("x", "y", "z"), ("r", "g", "b")):
        try:
            vals = [getattr(value, a) for a in attrs]
        except Exception:
            continue
        if all(isinstance(v, (int, float)) for v in vals):
            return [float(v) for v in vals]
    name = getattr(value, "name", None)
    if isinstance(name, str) and hasattr(value, "parent"):
        return name  # a scene node
    with contextlib.suppress(Exception):
        if not isinstance(value, (str, bytes)) and hasattr(value, "__iter__"):
            return [to_jsonable(v, depth + 1) for v in list(value)]
    return str(value)


def max_version():
    """3ds Max version string, or None outside 3ds Max."""
    try:
        from pymxs import runtime as rt
        return str(to_jsonable(rt.maxVersion()))  # [verify] maxVersion() not in the saved docs
    except Exception:
        return None


def envelope(ok, result=None, error=None, log=None, max_version=None) -> dict:
    """The result protocol shared by every channel: {ok, result, error, log, max_version}."""
    return {"ok": bool(ok), "result": to_jsonable(result), "error": error,
            "log": [str(x) for x in (log or [])], "max_version": max_version}


def write(payload: dict, path) -> str:
    """Write the envelope as UTF-8 JSON; creates the parent folder. Returns the path."""
    path = os.fspath(path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
    return path
