"""maxkit_scripting: helpers for tools and batch jobs inside 3ds Max 2027 (pymxs).

Runs inside 3ds Max only, on the main thread. Inline it with
max_wrap.wrap(code, kit=["maxkit_scripting"]) or import it from a package's
Contents folder (PYTHONPATH entry in PackageContents.xml).

checked against scripting-pipeline__3dsmaxbatch-2020.md,
scripting-pipeline__pymxs-renderer-2027.md, scripting-pipeline__python-threading-2027.md,
scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md

Functions
- cmd_args() -> dict                 -mxsString / -mxsValue values (batch), {} otherwise
- is_batch() -> bool                 True in 3ds Max Batch (no UI)
- log(msg)                           print, plus Max log broadcast to 3dsmaxbatch
- versioned_path(path) -> str        next free name_v###.ext, never an existing file
- save_copy(path) -> dict            saveMaxFile to a new versioned file, current scene name unchanged
- load_scene(path) -> dict           loadMaxFile without prompts, missing items logged
- io_classes() -> dict               installed importer and exporter classes with extensions
- CallbackSet                        register/unregister general callbacks by id (idempotent)
- MainThreadPump                     QTimer queue: worker threads post, main thread runs pymxs
- run_chunked(items, fn, ...)        process a long list in timer slices so the UI repaints
"""
import contextlib
import os
import re
import queue

from pymxs import runtime as rt


# ---------------------------------------------------------------- batch I/O

def cmd_args():
    """Return the 3dsmaxbatch -mxsString / -mxsValue arguments as {name: value}."""
    try:
        opts = rt.maxOps.mxsCmdLineArgs
    except Exception:
        return {}
    if opts is None:
        return {}
    out = {}
    for key in opts.keys:  # doc sample iterates `opts.keys` as a property
        out[str(key)] = opts[key]
    return out


def is_batch():
    try:
        return bool(rt.maxOps.isInNonInteractiveMode())
    except Exception:
        return False


def log(msg):
    msg = str(msg)
    print(msg)
    with contextlib.suppress(Exception):
        # broadcast:true sends the line to the 3dsmaxbatch console as well
        rt.logsystem.logEntry(msg, broadcast=True)


# ---------------------------------------------------------------- scene files

_VER = re.compile(r"^(?P<stem>.*?)(?:_v(?P<n>\d{3,}))?$")


def versioned_path(path):
    """Return path with the next free _v### suffix. Never returns an existing file."""
    folder, name = os.path.split(path)
    stem, ext = os.path.splitext(name)
    m = _VER.match(stem)
    base = m.group("stem")
    n = int(m.group("n") or 0) + 1
    while True:
        cand = os.path.join(folder, "%s_v%03d%s" % (base, n, ext))
        if not os.path.exists(cand):
            return cand
        n += 1


def save_copy(path):
    """Save the scene to a NEW file; saveMaxFile overwrites silently, so never reuse a name."""
    target = path if not os.path.exists(path) else versioned_path(path)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    # useNewFile:false keeps the current scene name and MRU list unchanged
    ok = bool(rt.saveMaxFile(target, useNewFile=False, quiet=True))
    return {"ok": ok and os.path.exists(target), "path": target}


def load_scene(path, use_file_units=None, ignore_file_units=None):
    """Load a .max file with no prompts. loadMaxFile discards unsaved changes without asking.

    Pass the unit choice explicitly in unattended runs: the defaults follow
    maxOps.GetSceneFileUnitHandlingBehavior() from 2027.1. ignoreFileUnits is 2027.1+.
    """
    if not os.path.exists(path):
        return {"ok": False, "path": path, "error": "missing file"}
    if not rt.isMaxFile(path):
        return {"ok": False, "path": path, "error": "not a 3ds Max file"}
    kw = dict(quiet=True, allowPrompts=False,
              missingExtFilesAction=rt.Name("logmsg"),
              missingDLLsAction=rt.Name("logmsg"),
              missingXRefsAction=rt.Name("logmsg"))
    if use_file_units is not None:
        kw["useFileUnits"] = bool(use_file_units)
    if ignore_file_units is not None:
        kw["ignoreFileUnits"] = bool(ignore_file_units)
    ok = bool(rt.loadMaxFile(path, **kw))
    # a file saved by a newer 3ds Max returns false here; report it, do not retry
    return {"ok": ok, "path": path,
            "scene": str(rt.maxFilePath) + str(rt.maxFileName) if ok else None}


def io_classes():
    """List importer and exporter classes with their extensions (2025+ for extensions)."""
    def describe(classes):
        rows = []
        for c in list(classes):
            try:
                exts = [str(e) for e in list(rt.getImporterExporterExtensions(c))]
            except Exception:
                exts = []
            rows.append({"class": str(c), "extensions": exts})
        return rows
    return {"importers": describe(rt.importerPlugin.classes),
            "exporters": describe(rt.exporterPlugin.classes)}


def exporter_for(ext):
    """Return the exporter class whose extension list contains ext (e.g. 'glb'), or None."""
    ext = ext.lower().lstrip(".")
    for c in list(rt.exporterPlugin.classes):
        try:
            if ext in [str(e).lower().lstrip(".*") for e in list(rt.getImporterExporterExtensions(c))]:
                return c
        except Exception:
            continue
    return None


# ---------------------------------------------------------------- callbacks

class CallbackSet:
    """General callbacks registered under one id so a re-run never stacks duplicates.

    Use a tool-specific id. Always call unregister() when the tool closes.
    """

    def __init__(self, cb_id):
        self.id = rt.Name(cb_id)

    def register(self, event, fn):
        # call reset() once before the first register: a second addScript runs fn twice
        rt.callbacks.addScript(rt.Name(event), fn, id=self.id)
        return self

    def reset(self):
        rt.callbacks.removeScripts(id=self.id)
        return self

    def unregister(self):
        rt.callbacks.removeScripts(id=self.id)


# ---------------------------------------------------------------- threads and UI

class MainThreadPump:
    """Queue drained by a QTimer on the main thread.

    Worker threads must never call pymxs; they call pump.post(fn, *args) and fn runs
    later on the main thread. Community pattern (QTimer queue), not an Autodesk API.
    """

    def __init__(self, parent=None, interval_ms=20, budget=50):
        from PySide6 import QtCore
        self._q = queue.Queue()
        self._budget = budget
        self.timer = QtCore.QTimer(parent)
        self.timer.timeout.connect(self._drain)
        self.timer.start(interval_ms)

    def post(self, fn, *args, **kwargs):
        self._q.put((fn, args, kwargs))

    def _drain(self):
        for _ in range(self._budget):
            try:
                fn, args, kwargs = self._q.get_nowait()
            except queue.Empty:
                return
            try:
                fn(*args, **kwargs)
            except Exception as exc:  # a failing job must not stop the pump
                log("pump job failed: %r" % (exc,))

    def stop(self):
        self.timer.stop()


def run_chunked(items, fn, chunk=200, on_progress=None, on_done=None, cancel=None):
    """Run fn(item) over items in slices of `chunk` per timer tick (main thread)."""
    from PySide6 import QtCore
    items = list(items)
    state = {"i": 0}

    def tick():
        if cancel is not None and cancel():
            if on_done:
                on_done(state["i"], cancelled=True)
            return
        end = min(state["i"] + chunk, len(items))
        for it in items[state["i"]:end]:
            fn(it)
        state["i"] = end
        if on_progress:
            on_progress(end, len(items))
        rt.redrawViews()
        if end < len(items):
            QtCore.QTimer.singleShot(0, tick)
        elif on_done:
            on_done(end, cancelled=False)

    QtCore.QTimer.singleShot(0, tick)
