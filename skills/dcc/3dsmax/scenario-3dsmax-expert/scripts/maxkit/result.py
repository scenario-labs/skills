"""maxkit.result: turn pymxs values into JSON-safe data and write the result envelope.

Checked against scripting-pipeline__pymxs-using-2027.md.

    to_jsonable(value, depth=0) -> JSON-safe value
    envelope(ok, result, error, log, max_version) -> dict
    write(payload, path, overwrite=None) -> str
    max_version() -> str | None

Pure Python apart from max_version(); safe to import outside 3ds Max.
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import tempfile

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
        return value if math.isfinite(value) else str(value)
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
            return [to_jsonable(float(v), depth + 1) for v in vals]
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


_ENVELOPE_KEYS = {"ok", "result", "error", "log", "max_version"}


def _is_envelope(path) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and set(data) == _ENVELOPE_KEYS


def _publish_new(tmp: str, path: str) -> None:
    """Put tmp at path only when nothing is there: the test and the creation are one step."""
    try:
        os.link(tmp, path)
    except FileExistsError:
        raise FileExistsError(f"{path} exists; pick a new result_path") from None
    except OSError:  # a volume without hard links: exclusive creation, then the copy
        with open(tmp, encoding="utf-8") as src, open(path, "x", encoding="utf-8") as out:
            out.write(src.read())
    os.remove(tmp)


def write(payload: dict, path, overwrite=None) -> str:
    """Write the envelope as UTF-8 JSON; creates the parent folder. Returns the path.

    overwrite None replaces only an earlier result envelope, True replaces any file, False never
    replaces: it creates the file in one step, so a file that appears meanwhile is kept. A refused
    path raises FileExistsError and leaves the file untouched."""
    path = os.fspath(path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(path) and not (overwrite or (overwrite is None and _is_envelope(path))):
        raise FileExistsError(f"{path} exists and is not a result envelope; pick a new result_path")
    # Serialize to a sibling temporary file, then publish it in one step: an interrupted write
    # never leaves partial JSON at path, so a retry is not refused by the envelope check.
    fd, tmp = tempfile.mkstemp(prefix=".mxk_result_", suffix=".tmp", dir=parent or None)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)
        if overwrite is False:
            _publish_new(tmp, path)
        else:
            if overwrite is None and os.path.exists(path) and not _is_envelope(path):
                raise FileExistsError(f"{path} exists and is not a result envelope; pick a new result_path")
            os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise
    return path
