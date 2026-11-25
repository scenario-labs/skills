"""Minimal fake pymxs for offline tests. NEVER shipped in the skill.

It models only what maxkit reads: a scene of FakeNode objects, units, renderer, layers, bitmaps,
viewport capture into FakeBitmap (written as a real PNG through Pillow when available), render,
importFile/exportFile, maxOps.mxsCmdLineArgs. Its behavior is a guess at 3ds Max, not a spec:
passing tests here prove the Python logic, not the 3ds Max API.
"""
from __future__ import annotations

import copy as _copy

import contextlib
import itertools
import os
import types


class Name(str):
    """Stand-in for a MAXScript name value (#foo)."""


class Point3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __iter__(self):
        return iter((self.x, self.y, self.z))


class _Cls:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __call__(self, *a, **k):
        return FakeBitmap(*a) if self.name == "bitmap" else None


GeometryClass = _Cls("GeometryClass")
light = _Cls("light")
camera = _Cls("camera")
helper = _Cls("helper")
BitmapTexture = _Cls("BitmapTexture")
FBXEXP = _Cls("FBXEXP")

_handles = itertools.count(1)


class FakeLayer:
    def __init__(self, name):
        self.name = name


class FakeMaterial:
    def __init__(self, name, cls="PhysicalMaterial"):
        self.name, self.cls = name, cls


class FakeNode:
    def __init__(self, name, cls="Editable_Poly", superclass=GeometryClass, faces=12, verts=8,
                 pos=(0, 0, 0), scale=(1, 1, 1), layer="Geo", material=None, size=10.0,
                 base=None, modifiers=0, parent=None, group_head=False):
        self.name = name
        self.cls = cls
        self.superclass = superclass
        self.faces, self.verts = faces, verts
        self.pos = Point3(*pos)
        self.scale = Point3(*scale)
        self.layer = FakeLayer(layer)
        self.material = material
        self.size = size
        self.handle = next(_handles)
        self.baseObject = base if base is not None else object()
        self.modifiers = [object()] * modifiers
        self.parent = parent
        self.isHidden = False
        self.group_head = group_head


class FakeBitmap:
    def __init__(self, width=64, height=48, color=(90, 120, 160)):
        self.width, self.height, self.color = width, height, color
        self.filename = None
        self.closed = False


class _Units:
    SystemType = Name("centimeters")
    SystemScale = 1.0


class _Renderers:
    current = types.SimpleNamespace(cls="Arnold")


class _LayerManager:
    names = ["0", "Geo"]

    @property
    def count(self):
        return len(self.names)

    def getLayer(self, i):
        return FakeLayer(self.names[i])


class _MaxOps:
    def __init__(self):
        self.mxsCmdLineArgs = {}
        self.batch = False

    def isInNonInteractiveMode(self):
        return self.batch


class _Viewport:
    def __init__(self, rt):
        self._rt = rt
        self.type = Name("view_persp_user")
        self.calls = []

    def getType(self, index=None):
        return self.type

    def setType(self, t):
        self.calls.append(("setType", str(t)))
        self.type = t

    def getViewportDib(self, captureAlpha=False, gammaCorrect=True):
        self.calls.append(("dib", captureAlpha, gammaCorrect))
        return FakeBitmap(320, 200)


class _PluginManager:
    def __init__(self):
        self.loaded = []
        self.fail = False

    def loadClass(self, cls):
        self.loaded.append(cls)
        return not self.fail


class _Runtime:
    BitmapTexture = BitmapTexture
    FBXEXP = FBXEXP
    GeometryClass = GeometryClass

    def __init__(self):
        self.reset()

    def reset(self):
        self.objects = []
        self.selection = []
        self.units = _Units()
        self.units.SystemType = Name("centimeters")
        self.units.SystemScale = 1.0
        self.renderers = _Renderers()
        self.renderers.current = types.SimpleNamespace(cls="Arnold")
        self.LayerManager = _LayerManager()
        self.LayerManager.names = ["0", "Geo"]
        self.maxops = _MaxOps()
        self.maxOps = self.maxops
        self.viewport = _Viewport(self)
        self.bitmaps = []
        self.existing_files = set()
        self.maxFilePath = "C:\\Projects\\Lobby\\"
        self.maxFileName = "lobby_v001.max"
        self.save_required = False
        self.sceneMaterials = []
        self.pluginManager = _PluginManager()
        self.save_fails = False
        self.renderWidth, self.renderHeight = 1920, 1080
        self.executed = []
        self.import_adds = []
        self.last_merge = None
        self.undo_labels = []
        self.redraws = 0

    # class queries
    def superClassOf(self, o):
        return o.superclass

    def classOf(self, o):
        if isinstance(o, FakeNode):
            return o.cls
        if isinstance(o, FakeMaterial):
            return o.cls
        return getattr(o, "cls", type(o).__name__)

    def getHandleByAnim(self, o):
        return o.handle if isinstance(o, FakeNode) else id(o)

    def getPolygonCount(self, o):
        return [o.faces, o.verts]

    def matrix3(self, _):
        return "identity"

    def nodeGetBoundingBox(self, o, _m):
        h = o.size / 2.0
        return [Point3(o.pos.x - h, o.pos.y - h, o.pos.z - h), Point3(o.pos.x + h, o.pos.y + h, o.pos.z + h)]

    def isGroupHead(self, o):
        return o.group_head

    def getClassInstances(self, cls):
        return list(self.bitmaps) if cls is BitmapTexture else []

    def doesFileExist(self, f):
        return f in self.existing_files or os.path.exists(f)

    def getSaveRequired(self):
        return self.save_required

    def maxVersion(self):
        return [29000, 0, 0, 2027, 3, 0]

    def redrawViews(self):
        self.redraws += 1

    def execute(self, s):
        self.executed.append(s)

    def name(self, s):
        return Name(s)

    Name = Name

    def bitmap(self, w, h):
        return FakeBitmap(w, h)

    def copy(self, src, dest=None, quality=None):
        if dest is None:  # one-argument copy returns a copy of the value
            return _copy.copy(src)
        dest.color = src.color

    def save(self, bmp):
        if self.save_fails:
            return False
        _write_png(bmp)
        return True

    def close(self, bmp):
        if bmp is not None:
            bmp.closed = True

    def getNodeByName(self, n):
        return next((o for o in self.objects if o.name == n), None)

    def render(self, outputFile=None, vfb=True, camera=None, outputwidth=None, outputheight=None,
               frame=None, cancelled=None, renderElements=None):
        bmp = FakeBitmap(outputwidth or self.renderWidth // 10, outputheight or self.renderHeight // 10)
        bmp.filename = outputFile
        _write_png(bmp)
        return bmp

    def importFile(self, path, *flags, quiet=False, using=None):
        self.objects.extend(self.import_adds)
        return True

    def mergeMAXFile(self, path, *flags, quiet=False, ignoreFileUnits=None, layers=None,
                     mergeNodesByLayer=None):
        self.last_merge = {"flags": [str(f) for f in flags], "quiet": quiet,
                           "ignoreFileUnits": ignoreFileUnits, "layers": layers,
                           "mergeNodesByLayer": mergeNodesByLayer}
        self.objects.extend(self.import_adds)
        return True

    def exportFile(self, path, *flags, selectedOnly=False, using=None):
        with open(path, "wb") as fh:
            fh.write(b"fake export " + str(path).encode())
        return True

    def FBXExporterSetParam(self, k, v=None):
        self.executed.append(("fbx", k, v))


def _write_png(bmp):
    if not bmp.filename:
        raise RuntimeError("bitmap has no filename")
    os.makedirs(os.path.dirname(bmp.filename) or ".", exist_ok=True)
    try:
        from PIL import Image  # type: ignore
        img = Image.new("RGB", (bmp.width, bmp.height), bmp.color)
        for x in range(bmp.width // 4, bmp.width // 2):  # a lighter block so the image is not uniform
            for y in range(bmp.height // 4, bmp.height // 2):
                img.putpixel((x, y), (230, 220, 200))
        img.save(bmp.filename)
    except ImportError:
        with open(bmp.filename, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n")


runtime = _Runtime()


@contextlib.contextmanager
def undo(on, label=None):
    runtime.undo_labels.append((on, label))
    yield


@contextlib.contextmanager
def animate(on):
    yield
