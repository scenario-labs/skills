"""
bx_kits: shaped and detailed proxies, color schemes, walking figures, crowds and traffic
for a bx_blockout scene. The levels these serve (density, fidelity, color) are in
references/levels.md.

Runs inside Blender beside bx_blockout, under the same rules: builders are get-or-create
by name, refuse names the user's own work holds, and tag every datablock they make.

  import sys; sys.path.append("<absolute path of this skill>/scripts")
  import bx_blockout as B, bx_kits as K
  pal = K.scheme("category")                                   # role -> color
  K.building("ENV_shop_a", (8, 6, 9), (12, 4, 0), fidelity="detailed", pal=pal, floors=3)
  K.tree("ENV_tree_01", (4, -3, 0), height=6, fidelity="shaped", pal=pal)
  K.vehicle("PRP_car_01", "car", (0, 10, 0), facing_deg=180, fidelity="shaped", rgb=pal["vehicle"])
  hero = K.figure("red", 1.75, (0, 20, 0), facing_deg=0, fidelity="shaped")
  K.walk_path(hero, [(1, (0, 20)), (120, (0, 8))])             # travel with legs that step
  K.crowd("BG", 24, area=(-6, 6, 0, 40), frames=(1, 192), fidelity="rough", pal=pal)
  van = K.vehicle("PRP_van_02", "van", (-30, 5, 0), facing_deg=-90, pal=pal)
  K.drive(van, [(1, (-30, 5)), (192, (30, 5))]); K.mark_extra(van)  # background traffic
  K.audit_budget("advanced")                                   # [] = the scene meets the level
  B.solid_view("MATERIAL")                                     # multi-color kits need Material

Fidelity is one of "rough" (boxes, cylinders, legless capsule figures), "shaped" (bevels,
composed silhouettes, jointed figures that step) or "detailed" (openings, trims, parts a
camera would read at 2 m).
A kit is one mesh with one material slot per role color, so a detailed building stays
one object; Solid view needs color type Material to show more than one color per object.
"""

import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import bx_blockout as B

FIDELITY = ("rough", "shaped", "detailed")

# -- color schemes -------------------------------------------------------------------------
# Roles a set is built from. Every scheme maps every role, so a kit can ask for any of them.
ROLES = ("ground", "road", "wall", "roof", "trim", "opening", "glass", "vegetation", "trunk",
         "water", "rock", "prop", "fabric", "metal", "vehicle", "light", "sign", "crowd")

_GRAY = {r: v for r, v in zip(ROLES, (0.30, 0.22, 0.48, 0.38, 0.55, 0.16, 0.20, 0.42, 0.34,
                                      0.26, 0.40, 0.46, 0.50, 0.36, 0.44, 0.90, 0.52, 0.58))}

SCHEMES = {
    # Neutral set, color only on tracked elements (bx_blockout's PALETTE). Lowest leak risk;
    # weakest separation of masses.
    "identity": {r: (v, v, v) for r, v in _GRAY.items()},
    # One muted hue per role: masses separate at a glance and the legend is short. Movers
    # still take saturated PALETTE colors so they stand out from any role.
    "category": {
        "ground": (0.33, 0.33, 0.35), "road": (0.20, 0.20, 0.23), "wall": (0.70, 0.62, 0.50),
        "roof": (0.55, 0.36, 0.30), "trim": (0.82, 0.80, 0.74), "opening": (0.12, 0.12, 0.14),
        "glass": (0.36, 0.52, 0.62), "vegetation": (0.38, 0.58, 0.32), "trunk": (0.42, 0.32, 0.24),
        "water": (0.28, 0.46, 0.66), "rock": (0.52, 0.50, 0.47), "prop": (0.74, 0.56, 0.30),
        "fabric": (0.66, 0.42, 0.58), "metal": (0.56, 0.60, 0.64), "vehicle": (0.62, 0.66, 0.72),
        "light": (1.00, 0.92, 0.62), "sign": (0.86, 0.70, 0.36), "crowd": (0.47, 0.46, 0.47),
    },
    # Colors close to the real material's albedo: whatever leaks into the render is already
    # right. Use when the look reference covers the whole frame.
    "material": {
        "ground": (0.36, 0.34, 0.31), "road": (0.14, 0.14, 0.15), "wall": (0.62, 0.55, 0.46),
        "roof": (0.36, 0.22, 0.18), "trim": (0.78, 0.75, 0.68), "opening": (0.08, 0.07, 0.07),
        "glass": (0.20, 0.30, 0.36), "vegetation": (0.18, 0.34, 0.14), "trunk": (0.27, 0.19, 0.13),
        "water": (0.10, 0.22, 0.30), "rock": (0.44, 0.42, 0.39), "prop": (0.48, 0.34, 0.20),
        "fabric": (0.50, 0.16, 0.14), "metal": (0.50, 0.52, 0.54), "vehicle": (0.30, 0.32, 0.36),
        "light": (1.00, 0.86, 0.55), "sign": (0.80, 0.18, 0.12), "crowd": (0.30, 0.28, 0.30),
    },
}


def scheme(name="category"):
    """Role -> RGB for a color scheme ("identity", "category" or "material")."""
    if name not in SCHEMES:
        raise ValueError(f"scheme must be one of {sorted(SCHEMES)}")
    return dict(SCHEMES[name])


def tint(rgb, seed, amount=0.07):
    """A repeatable value shift of `rgb` (one per instance), so neighbouring blocks of the
    same role still separate. amount 0.07 shifts value by up to 7 %."""
    k = 1.0 + (random.Random(seed).random() * 2.0 - 1.0) * amount
    return tuple(min(1.0, max(0.0, c * k)) for c in rgb)


def _fidelity(value):
    if value not in FIDELITY:
        raise ValueError(f"fidelity must be one of {FIDELITY}")
    return FIDELITY.index(value)


# -- one mesh from many primitives -----------------------------------------------------------


class Parts:
    """Collects primitives into one bmesh, one material slot per color. Sizes are in meters
    and a part is centered on `center` unless `base=True` puts its bottom there."""

    def __init__(self):
        self.bm = bmesh.new()
        self.colors = []

    def _slot(self, rgb):
        rgb = tuple(round(c, 4) for c in rgb)
        if rgb not in self.colors:
            self.colors.append(rgb)
        return self.colors.index(rgb)

    def add(self, kind, size, center, rgb, rot=(0.0, 0.0, 0.0), base=False, bevel=0.0, segments=12):
        """kind: box, cylinder, cone, sphere, ico, wedge (a ramp rising along +Y)."""
        sx, sy, sz = size
        cx, cy, cz = center
        if base:
            cz += sz / 2.0
        mat = Matrix.Translation((cx, cy, cz)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((sx, sy, sz, 1.0))
        before = set(self.bm.verts)
        if kind == "box":
            bmesh.ops.create_cube(self.bm, size=1.0, matrix=mat)
        elif kind in ("cylinder", "cone"):
            bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segments, radius1=0.5,
                                  radius2=0.5 if kind == "cylinder" else 0.0, depth=1.0, matrix=mat)
        elif kind == "sphere":
            bmesh.ops.create_uvsphere(self.bm, u_segments=segments, v_segments=max(6, segments // 2), radius=0.5, matrix=mat)
        elif kind == "ico":
            bmesh.ops.create_icosphere(self.bm, subdivisions=1, radius=0.5, matrix=mat)
        elif kind == "wedge":
            pts = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5)]
            v = [self.bm.verts.new(mat @ Vector(p)) for p in pts]
            for f in ((0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 5), (3, 0, 4), (2, 3, 4, 5)):
                self.bm.faces.new([v[i] for i in f])
        else:
            raise ValueError(f"unknown primitive {kind!r}")
        new = [v for v in self.bm.verts if v not in before]
        faces = {f for v in new for f in v.link_faces}
        slot = self._slot(rgb)
        for f in faces:
            f.material_index = slot
        if bevel > 0.0:
            edges = list({e for f in faces for e in f.edges})
            bmesh.ops.bevel(self.bm, geom=edges, offset=bevel, segments=2, affect="EDGES", profile=0.5)
        return self

    def to_object(self, name, location=(0.0, 0.0, 0.0), facing_deg=0.0, coll=None, parent=None):
        """Write the parts into object `name` (get-or-create, like B.box): one shared
        material per color, object color set to the first part's color."""
        obj = bpy.data.objects.get(name)
        if obj is not None:
            B._own(obj, None)
        mesh = obj.data if obj is not None else bpy.data.meshes.new(name)
        # Slots first: clearing a mesh's materials resets every face's material index.
        mesh.materials.clear()
        for rgb in self.colors:
            mesh.materials.append(B.identity_material(B.material_name_for(rgb), rgb))
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(mesh)
        self.bm.free()
        if obj is None:
            obj = B._own(None, lambda: bpy.data.objects.new(name, mesh))
            (coll or bpy.context.scene.collection).objects.link(obj)
        obj.color = (*self.colors[0], 1.0) if self.colors else (1.0, 1.0, 1.0, 1.0)
        if parent is not None:
            obj.parent = parent
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = location
        obj.rotation_euler = (0.0, 0.0, math.radians(facing_deg))
        obj.scale = (1.0, 1.0, 1.0)
        return obj


# -- set kits -------------------------------------------------------------------------------


def building(name, size, location, fidelity="shaped", pal=None, floors=None, roof="flat", facing_deg=0.0, seed=0, coll=None):
    """A building with its street face toward local -Y. size = (width, depth, height).
    rough: one box. shaped: plinth, floor bands, roof, a door. detailed: window grid with
    sills, a shop front, balconies on upper floors, rooftop units."""
    pal = pal or scheme("category")
    lvl = _fidelity(fidelity)
    w, d, h = size
    wall = tint(pal["wall"], seed)
    p = Parts()
    if lvl == 0:
        p.add("box", (w, d, h), (0, 0, 0), wall, base=True)
        return p.to_object(name, location, facing_deg, coll)
    floors = floors or max(1, int(h // 3.2))
    fh = h / floors
    p.add("box", (w, d, h), (0, 0, 0), wall, base=True, bevel=0.03)
    p.add("box", (w + 0.1, d + 0.1, 0.5), (0, 0, 0), pal["trim"], base=True)
    for i in range(1, floors):
        p.add("box", (w + 0.06, d + 0.06, 0.14), (0, 0, i * fh), pal["trim"], base=True)
    if roof == "gable":
        p.add("wedge", (w + 0.4, d / 2 + 0.2, min(3.0, d * 0.4)), (0, -d / 4, h), pal["roof"], base=True)
        p.add("wedge", (w + 0.4, d / 2 + 0.2, min(3.0, d * 0.4)), (0, d / 4, h), pal["roof"], rot=(0, 0, math.pi), base=True)
    else:
        p.add("box", (w + 0.2, d + 0.2, 0.3), (0, 0, h), pal["roof"], base=True)
    front = -d / 2
    p.add("box", (1.1, 0.2, 2.2), (-w * 0.3, front - 0.02, 0), pal["opening"], base=True)
    if lvl >= 2:
        rng = random.Random(seed)
        cols = max(1, int(w // 2.2))
        step = w / cols
        p.add("box", (w * 0.9, 0.25, 0.5), (0, front - 0.1, 2.9), pal["sign"], base=True)
        p.add("box", (w * 0.55, 0.12, 2.3), (w * 0.15, front - 0.03, 0.3), pal["glass"], base=True)
        for f in range(1, floors):
            z = f * fh + fh * 0.3
            for c in range(cols):
                x = -w / 2 + step * (c + 0.5)
                p.add("box", (step * 0.5, 0.16, fh * 0.5), (x, front - 0.04, z), pal["glass"], base=True)
                p.add("box", (step * 0.62, 0.3, 0.08), (x, front - 0.1, z - 0.06), pal["trim"], base=True)
            if f >= 1 and rng.random() < 0.5:
                bx = -w / 2 + step * (rng.randrange(cols) + 0.5)
                p.add("box", (step * 0.9, 0.9, 0.12), (bx, front - 0.45, f * fh), pal["metal"], base=True)
                p.add("box", (step * 0.9, 0.05, 0.9), (bx, front - 0.88, f * fh + 0.12), pal["metal"], base=True)
        for _ in range(rng.randint(1, 3)):
            p.add("box", (rng.uniform(0.8, 1.6), rng.uniform(0.8, 1.4), rng.uniform(0.6, 1.2)),
                  (rng.uniform(-w / 3, w / 3), rng.uniform(-d / 4, d / 4), h + 0.3), pal["metal"], base=True)
    return p.to_object(name, location, facing_deg, coll)


def tree(name, location, height=6.0, fidelity="shaped", pal=None, kind="broadleaf", seed=0, coll=None):
    """rough: trunk and one crown. shaped: trunk and three overlapping crown masses.
    detailed: branches and seven to ten crown clusters, so the outline reads as foliage,
    not a ball (a single low-poly crown against the sky renders as topiary)."""
    pal = pal or scheme("category")
    lvl = _fidelity(fidelity)
    rng = random.Random(seed)
    leaf, bark = tint(pal["vegetation"], seed), pal["trunk"]
    p = Parts()
    trunk_h = height * (0.45 if kind == "broadleaf" else 0.25)
    p.add("cylinder", (height * 0.06, height * 0.06, trunk_h + 0.3), (0, 0, 0), bark, base=True, segments=8)
    if kind == "conifer":
        tiers = 1 if lvl == 0 else (3 if lvl == 1 else 5)
        for i in range(tiers):
            t = i / max(1, tiers)
            size = height * 0.45 * (1 - t * 0.7)
            p.add("cone", (size, size, height * 0.75 / tiers * 1.6), (0, 0, trunk_h + height * 0.75 * t), leaf, base=True, segments=10)
        return p.to_object(name, location, 0.0, coll)
    r = height * 0.32
    top = trunk_h + r * 0.9
    if lvl == 0:
        p.add("sphere", (2 * r, 2 * r, 1.7 * r), (0, 0, top), leaf, segments=10)
    else:
        n = 3 if lvl == 1 else rng.randint(7, 10)
        for i in range(n):
            a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
            off = r * (0.45 if lvl == 1 else 0.7) * rng.uniform(0.6, 1.0)
            s = r * (1.25 if lvl == 1 else rng.uniform(0.6, 0.9))
            p.add("ico", (s * 1.6, s * 1.6, s * 1.3), (math.cos(a) * off, math.sin(a) * off, top + rng.uniform(-0.3, 0.5) * r), tint(leaf, seed + i, 0.1))
        if lvl == 2:
            for i in range(3):
                a = 2 * math.pi * i / 3 + 0.4
                p.add("cylinder", (0.12, 0.12, r * 1.3), (math.cos(a) * r * 0.35, math.sin(a) * r * 0.35, trunk_h + r * 0.4), bark, rot=(math.cos(a) * 0.7, -math.sin(a) * 0.7, 0), segments=6)
    return p.to_object(name, location, 0.0, coll)


def vehicle(name, kind="car", location=(0.0, 0.0, 0.0), facing_deg=0.0, fidelity="shaped", rgb=None, pal=None, coll=None):
    """Car, van, bus or scooter facing local -Y, front marked in geometry: pale headlight
    blocks and a darker grille at the front, red blocks at the rear, so the model cannot
    drive it backward. Wheels are one mesh here; spin a separate wheel object only for a
    close shot that reads rotation. rough: body, cabin, wheels. shaped: bevels, glass band,
    bumpers. detailed: mirrors, seats, wheel hubs, number plates."""
    pal = pal or scheme("category")
    lvl = _fidelity(fidelity)
    body = rgb or pal["vehicle"]
    dims = {"car": (1.8, 4.4, 1.45, 0.32), "van": (2.0, 5.2, 2.2, 0.34), "bus": (2.5, 11.0, 3.1, 0.5), "scooter": (0.7, 1.8, 1.15, 0.22)}
    if kind not in dims:
        raise ValueError(f"kind must be one of {sorted(dims)}")
    w, l, h, r = dims[kind]
    bev = 0.06 if lvl else 0.0
    p = Parts()
    if kind == "scooter":
        p.add("box", (0.5, 1.3, 0.35), (0, 0.1, r * 1.4), body, bevel=bev)
        p.add("box", (0.45, 0.35, 0.8), (0, -0.55, r * 1.4 + 0.3), body, bevel=bev)
        p.add("cylinder", (0.06, 0.06, 0.6), (0, -0.62, r * 2 + 0.75), pal["metal"], rot=(0, math.pi / 2, 0), segments=8)
        p.add("box", (0.4, 0.6, 0.12), (0, 0.35, r * 1.4 + 0.25), pal["fabric"])
    else:
        cab_l = l * (0.5 if kind == "car" else 0.92)
        p.add("box", (w, l, h * 0.5), (0, 0, r * 0.9), body, base=True, bevel=bev)
        p.add("box", (w * 0.94, cab_l, h * 0.5), (0, l * (0.06 if kind == "car" else 0.0), r * 0.9 + h * 0.5), body, base=True, bevel=bev)
        if lvl >= 1:
            p.add("box", (w * 0.96, cab_l * 0.92, h * 0.32), (0, l * (0.06 if kind == "car" else 0.0), r * 0.9 + h * 0.56), pal["glass"], base=True)
            p.add("box", (w * 1.02, 0.18, 0.22), (0, -l / 2, r * 0.9), pal["trim"], base=True)
            p.add("box", (w * 1.02, 0.18, 0.22), (0, l / 2, r * 0.9), pal["trim"], base=True)
        p.add("box", (w * 0.6, 0.06, h * 0.16), (0, -l / 2 - 0.02, r * 0.9 + h * 0.18), pal["opening"], base=True)
    front_z = r * (2.2 if kind == "scooter" else 1.9)
    for side in ((-0.32, 0.32) if kind != "scooter" else (0.0,)):
        p.add("box", (max(0.14, w * 0.18), 0.08, 0.12), (side * w, -l / 2 - 0.03, front_z), pal["light"])
        p.add("box", (max(0.14, w * 0.18), 0.08, 0.12), (side * w, l / 2 + 0.03, front_z), (0.85, 0.05, 0.05))
    axles = (-l * 0.32, l * 0.32) if kind != "scooter" else (-l * 0.36, l * 0.36)
    sides = (-w / 2 + 0.12, w / 2 - 0.12) if kind != "scooter" else (0.0,)
    for y in axles:
        for x in sides:
            p.add("cylinder", (2 * r, 2 * r, 0.22 if kind != "scooter" else 0.1), (x, y, r), (0.08, 0.08, 0.09), rot=(0, math.pi / 2, 0), segments=16)
            if lvl == 2:
                p.add("cylinder", (r, r, 0.24 if kind != "scooter" else 0.12), (x, y, r), pal["metal"], rot=(0, math.pi / 2, 0), segments=10)
    if lvl == 2 and kind != "scooter":
        for s in (-1, 1):
            p.add("box", (0.22, 0.1, 0.12), (s * (w / 2 + 0.1), -l * 0.08, r * 0.9 + h * 0.55), body)
        p.add("box", (0.5, 0.04, 0.12), (0, -l / 2 - 0.1, r * 0.9 + 0.05), pal["trim"], base=True)
        p.add("box", (0.5, 0.04, 0.12), (0, l / 2 + 0.1, r * 0.9 + 0.05), pal["trim"], base=True)
        for s in (-1, 1):
            p.add("box", (w * 0.36, 0.5, 0.5), (s * w * 0.22, l * 0.02, r * 0.9 + h * 0.5), pal["fabric"], base=True)
    return p.to_object(name, location, facing_deg, coll)


def stall(name, location, width=2.6, depth=1.8, fidelity="shaped", pal=None, facing_deg=0.0, seed=0, coll=None):
    """Market stall facing local -Y: counter, posts, awning. shaped adds a back shelf and
    goods; detailed adds hanging lanterns, a sign board and stools."""
    pal = pal or scheme("category")
    lvl = _fidelity(fidelity)
    rng = random.Random(seed)
    p = Parts()
    p.add("box", (width, depth * 0.45, 1.0), (0, -depth * 0.25, 0), tint(pal["prop"], seed), base=True, bevel=0.02 if lvl else 0.0)
    for x in (-width / 2 + 0.05, width / 2 - 0.05):
        for y in (-depth / 2 + 0.05, depth / 2 - 0.05):
            p.add("box", (0.08, 0.08, 2.4), (x, y, 0), pal["metal"], base=True)
    p.add("wedge" if lvl else "box", (width + 0.3, depth + 0.4, 0.35 if lvl else 0.08), (0, 0, 2.4), tint(pal["fabric"], seed + 7, 0.15), base=True)
    if lvl >= 1:
        p.add("box", (width * 0.9, 0.35, 1.6), (0, depth * 0.35, 0), pal["prop"], base=True)
        for i in range(rng.randint(3, 6)):
            p.add("cylinder", (0.25, 0.25, 0.25), (rng.uniform(-width / 2 + 0.2, width / 2 - 0.2), -depth * 0.25, 1.0), tint(pal["metal"], seed + i, 0.15), base=True, segments=10)
    if lvl == 2:
        p.add("box", (width * 0.7, 0.06, 0.45), (0, -depth / 2 - 0.15, 2.0), pal["sign"], base=True)
        for i in range(3):
            x = -width / 2 + width * (i + 0.5) / 3
            p.add("sphere", (0.32, 0.32, 0.4), (x, -depth / 2 - 0.2, 2.15), pal["light"], segments=10)
        for i in range(2):
            p.add("cylinder", (0.35, 0.35, 0.65), (-0.6 + 1.2 * i, -depth / 2 - 0.55, 0), pal["metal"], base=True, segments=10)
    return p.to_object(name, location, facing_deg, coll)


def street_lamp(name, location, height=4.5, fidelity="shaped", pal=None, facing_deg=0.0, coll=None):
    """Straight pole and a lamp head. Keep it straight: a curved pole proxy can render as
    a snake. detailed adds a base and an arm."""
    pal = pal or scheme("category")
    lvl = _fidelity(fidelity)
    p = Parts()
    p.add("cylinder", (0.12, 0.12, height), (0, 0, 0), pal["metal"], base=True, segments=8)
    if lvl == 2:
        p.add("cylinder", (0.3, 0.3, 0.5), (0, 0, 0), pal["metal"], base=True, segments=8)
        p.add("box", (0.08, 0.9, 0.08), (0, -0.45, height - 0.1), pal["metal"], base=True)
        p.add("box", (0.35, 0.45, 0.2), (0, -0.85, height - 0.35), pal["light"], base=True)
    else:
        p.add("box", (0.35, 0.35, 0.3), (0, 0, height), pal["light"], base=True)
    return p.to_object(name, location, facing_deg, coll)


def rock(name, location, size=1.0, fidelity="shaped", pal=None, seed=0, coll=None):
    """A boulder. rough: a flattened box. shaped and detailed: a jittered icosphere (two
    clustered at detailed). Avoid holes and faces: a holed rock can read as a skull."""
    pal = pal or scheme("category")
    lvl = _fidelity(fidelity)
    rng = random.Random(seed)
    p = Parts()
    if lvl == 0:
        p.add("box", (size, size * 0.8, size * 0.6), (0, 0, 0), tint(pal["rock"], seed), base=True)
        return p.to_object(name, location, rng.uniform(0, 360), coll)
    for i in range(1 if lvl == 1 else 2):
        s = size * (1.0 if i == 0 else 0.55)
        p.add("ico", (s, s * rng.uniform(0.7, 1.0), s * rng.uniform(0.5, 0.75)), (i * size * 0.55, i * size * 0.2, s * 0.25), tint(pal["rock"], seed + i))
    for v in p.bm.verts:
        v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.5, 0.5))) * size * 0.08
    return p.to_object(name, location, rng.uniform(0, 360), coll)


def instance(source, name, location, yaw_deg=0.0, scale=1.0, coll=None):
    """Linked duplicate of a kit object (shares its mesh and colors): repeats cost one mesh."""
    src = bpy.data.objects[source] if isinstance(source, str) else source
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = B._own(None, lambda: bpy.data.objects.new(name, src.data))
        (coll or bpy.context.scene.collection).objects.link(obj)
    else:
        B._own(obj, None)
    obj.color = src.color
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))
    obj.scale = (scale, scale, scale)
    return obj


def scatter_points(count, area, seed=0, min_dist=1.0, avoid=()):
    """Up to `count` (x, y) points in area (xmin, xmax, ymin, ymax), at least `min_dist`
    apart and outside every (x, y, radius) in `avoid` (keep the hero's lane clear)."""
    rng = random.Random(seed)
    pts = []
    for _ in range(count * 40):
        if len(pts) >= count:
            break
        x, y = rng.uniform(area[0], area[1]), rng.uniform(area[2], area[3])
        if any((x - ax) ** 2 + (y - ay) ** 2 < r * r for ax, ay, r in avoid):
            continue
        if all((x - px) ** 2 + (y - py) ** 2 >= min_dist ** 2 for px, py in pts):
            pts.append((x, y))
    return pts


# -- figures that walk ------------------------------------------------------------------------
# Joint pivots and part boxes as fractions of the height. Each limb part's origin sits on
# its joint, so rotating the part swings it like a limb. (size x, y, z), pivot, offset of
# the box center from the pivot.
_JOINTED = {
    "pelvis": ((0.20, 0.11, 0.09), (0.0, 0.0, 0.50), (0.0, 0.0, 0.0), None),
    "torso": ((0.22, 0.12, 0.30), (0.0, 0.0, 0.54), (0.0, 0.0, 0.15), "pelvis"),
    "head": ((0.12, 0.13, 0.14), (0.0, 0.0, 0.86), (0.0, 0.0, 0.07), "torso"),
    "thigh_L": ((0.085, 0.095, 0.25), (0.05, 0.0, 0.49), (0.0, 0.0, -0.125), "pelvis"),
    "thigh_R": ((0.085, 0.095, 0.25), (-0.05, 0.0, 0.49), (0.0, 0.0, -0.125), "pelvis"),
    "shin_L": ((0.075, 0.085, 0.25), (0.05, 0.0, 0.25), (0.0, 0.0, -0.125), "thigh_L"),
    "shin_R": ((0.075, 0.085, 0.25), (-0.05, 0.0, 0.25), (0.0, 0.0, -0.125), "thigh_R"),
    "foot_L": ((0.075, 0.15, 0.045), (0.05, 0.0, 0.03), (0.0, -0.05, -0.008), "shin_L"),
    "foot_R": ((0.075, 0.15, 0.045), (-0.05, 0.0, 0.03), (0.0, -0.05, -0.008), "shin_R"),
    "uparm_L": ((0.065, 0.075, 0.19), (0.14, 0.0, 0.82), (0.0, 0.0, -0.095), "torso"),
    "uparm_R": ((0.065, 0.075, 0.19), (-0.14, 0.0, 0.82), (0.0, 0.0, -0.095), "torso"),
    "forearm_L": ((0.06, 0.07, 0.19), (0.14, 0.0, 0.63), (0.0, 0.0, -0.095), "uparm_L"),
    "forearm_R": ((0.06, 0.07, 0.19), (-0.14, 0.0, 0.63), (0.0, 0.0, -0.095), "uparm_R"),
}


def figure(name, height=1.75, location=(0.0, 0.0, 0.0), facing_deg=0.0, rgb=B.PALETTE["red"], fidelity="shaped", coll=None):
    """A figure for the chosen fidelity. rough: a legless capsule with a head and a nose
    block for facing, one object; it glides and the video model invents the gait (our film
    work found this safer than any rigged walk, which the model copied as sliding feet).
    shaped: thirteen jointed parts that `walk_path` steps. detailed: shaped plus a nose
    block and a hair cap, for medium shots where head turns matter. Returns the root name."""
    lvl = _fidelity(fidelity)
    root_name = f"FIG_{name}"
    if lvl == 0:
        p = Parts()
        r = height * 0.13
        p.add("cylinder", (2 * r, 2 * r, height * 0.62), (0, 0, height * 0.10), rgb, base=True, segments=16)
        p.add("sphere", (2 * r, 2 * r, 2 * r), (0, 0, height * 0.72), rgb, segments=16)
        p.add("sphere", (2 * r, 2 * r, 1.2 * r), (0, 0, height * 0.10), rgb, segments=16)
        p.add("sphere", (height * 0.15, height * 0.16, height * 0.17), (0, 0, height * 0.90), rgb, segments=16)
        p.add("box", (height * 0.04, height * 0.05, height * 0.035), (0, -height * 0.085, height * 0.90), rgb)
        obj = p.to_object(root_name, location, facing_deg, coll)
        obj["height"] = height
        obj["capsule"] = True
        return obj.name
    existing = bpy.data.objects.get(root_name)
    root = B._own(existing, lambda: bpy.data.objects.new(root_name, None))
    if existing is None:
        root.empty_display_type, root.empty_display_size = "PLAIN_AXES", height * 0.3
        (coll or bpy.context.scene.collection).objects.link(root)
    made = {}
    for part, (size, pivot, offset, parent) in _JOINTED.items():
        p = Parts()
        p.add("box", [height * s for s in size], [height * o for o in offset], rgb, bevel=0.008 if lvl == 2 else 0.0)
        if lvl == 2 and part == "head":
            p.add("box", (height * 0.03, height * 0.04, height * 0.03), (0, -height * 0.075, height * 0.065), rgb)
            p.add("box", (height * 0.13, height * 0.14, height * 0.04), (0, height * 0.005, height * 0.14), (0.12, 0.10, 0.09))
        par = made.get(parent, root)
        pivot_world = Vector([height * c for c in pivot])
        par_pivot = Vector([height * c for c in _JOINTED[parent][1]]) if parent else Vector((0, 0, 0))
        obj = p.to_object(f"{root_name}_{part}", pivot_world - par_pivot, 0.0, coll, parent=par)
        obj.rotation_mode = "XYZ"
        made[part] = obj
    root.location = location
    root.rotation_euler = (0.0, 0.0, math.radians(facing_deg))
    root["height"] = height
    root["jointed"] = True
    return root.name


def _key_rot(obj, frame, x_deg):
    obj.rotation_euler = (math.radians(x_deg), 0.0, 0.0)
    obj.keyframe_insert("rotation_euler", index=0, frame=frame)


def walk_path(fig, path, stride=None, swing_deg=26.0, step=2, scene=None):
    """Move a figure's root along `path` [(frame, (x, y)), ...] (z stays at the ground) and
    face it along the travel. A jointed figure also gets legs and arms keyed from the
    distance covered, so every step matches the ground it crosses: no sliding feet whatever
    the speed. A capsule only glides. A pause is two path points at the same position: the
    legs come to rest. Returns key counts."""
    root = bpy.data.objects[fig] if isinstance(fig, str) else fig
    h = root.get("height", 1.75)
    stride = stride or h * 0.42  # one step
    parts = {k: bpy.data.objects[f"{root.name}_{k}"] for k in _JOINTED} if root.get("jointed") else {}
    path = sorted(path)
    f0, f1 = path[0][0], path[-1][0]

    def pos(f):
        for (fa, a), (fb, b) in zip(path, path[1:]):
            if fa <= f <= fb:
                t = 0.0 if fb == fa else (f - fa) / (fb - fa)
                return Vector((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0.0))
        return Vector((*path[-1][1], 0.0))

    dist, prev, yaw = 0.0, pos(f0), root.rotation_euler.z
    keys = 0
    for f in list(range(f0, f1 + 1, step)) + ([f1] if (f1 - f0) % step else []):
        cur = pos(f)
        moved = (cur - prev).length
        if moved > 1e-4:
            d = cur - prev
            yaw = math.atan2(d.x, -d.y)
        dist += moved
        prev = cur
        phase = 2 * math.pi * dist / (2 * stride)
        amp = swing_deg if moved > 1e-4 else 0.0
        root.location = cur
        root.rotation_euler = (0.0, 0.0, yaw)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", index=2, frame=f)
        keys += 1
        if not parts:
            continue
        s = math.sin(phase)
        _key_rot(parts["thigh_L"], f, amp * s)
        _key_rot(parts["thigh_R"], f, -amp * s)
        _key_rot(parts["shin_L"], f, amp * 1.1 * max(0.0, -math.cos(phase)))
        _key_rot(parts["shin_R"], f, amp * 1.1 * max(0.0, math.cos(phase)))
        _key_rot(parts["uparm_L"], f, -amp * 0.8 * s)
        _key_rot(parts["uparm_R"], f, amp * 0.8 * s)
        _key_rot(parts["forearm_L"], f, -amp * 0.5)
        _key_rot(parts["forearm_R"], f, -amp * 0.5)
    for obj in [root, *parts.values()]:
        for fc in B.fcurves(obj):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return {"figure": root.name, "frames": [f0, f1], "keys": keys, "distance_m": round(dist, 2)}


def crowd(prefix, count, area, frames, fidelity="rough", pal=None, speed=(1.0, 1.5), heights=(1.6, 1.9), seed=0, avoid=(), coll=None, walking=None, headings=None, keep_clear=()):
    """Background walkers crossing `area` (xmin, xmax, ymin, ymax) over `frames` (start,
    end), each on a straight line at its own speed, in the scheme's crowd color with a
    value tint per person. Rough walkers are gliding capsules, shaped and detailed ones
    step. walking=False makes a standing crowd. headings: yaw choices in degrees
    (0 walks toward -Y, 180 toward +Y) to keep walkers along a street; None is random.
    keep_clear: [(frame_a, frame_b, (xmin, xmax, ymin, ymax)), ...] zones no walker may
    enter during those frames, such as the sight line between a camera and its subject;
    a walker whose line crosses one is dropped. Every root is tagged extra=True.
    Returns the figure roots."""
    pal = pal or scheme("category")
    rng = random.Random(seed)
    walking = True if walking is None else walking
    start_pts = scatter_points(count, area, seed, min_dist=0.9, avoid=avoid)
    fps = bpy.context.scene.render.fps
    roots = []
    secs = (frames[1] - frames[0]) / fps
    for i, (x, y) in enumerate(start_pts):
        h = rng.uniform(*heights)
        yaw = math.radians(rng.choice(headings)) if headings else rng.uniform(0, 2 * math.pi)
        v = rng.uniform(*speed) if walking else 0.0
        end = (x + math.sin(yaw) * v * secs, y - math.cos(yaw) * v * secs)
        if _crosses(keep_clear, frames, (x, y), end):
            continue
        name = f"{prefix}{i:03d}"
        rgb = tint(pal["crowd"], seed * 1000 + i, 0.25)
        root = figure(name, h, (x, y, 0.0), math.degrees(yaw), rgb, fidelity, coll)
        root = bpy.data.objects[root]
        root["extra"] = True
        roots.append(root.name)
        if walking:
            walk_path(root, [(frames[0], (x, y)), (frames[1], end)], step=3)
    return roots


def _crosses(zones, frames, a, b):
    """True when a straight walk from a to b over frames enters a keep_clear zone in time."""
    for fa, fb, (x0, x1, y0, y1) in zones:
        for f in range(max(fa, frames[0]), min(fb, frames[1]) + 1, 4):
            t = (f - frames[0]) / max(1, frames[1] - frames[0])
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if x0 <= x <= x1 and y0 <= y <= y1:
                return True
    return False


def mark_extra(obj):
    """Tag a mover as an extra (background traffic, crowd): audit_budget counts heroes and
    extras separately, because only heroes carry the story and need a line in the prompt."""
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    obj["extra"] = True
    return obj.name


def drive(obj, path, scene=None):
    """Key a vehicle along `path` [(frame, (x, y)), ...] facing its travel (front = local
    -Y), one key per frame with LINEAR interpolation: vehicles keep constant speed between
    points and never ease into a turn by sliding sideways."""
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    path = sorted(path)
    keys = 0
    yaw = obj.rotation_euler.z
    for (fa, a), (fb, b) in zip(path, path[1:]):
        d = Vector((b[0] - a[0], b[1] - a[1], 0.0))
        if d.length > 1e-4:
            yaw = math.atan2(d.x, -d.y)
        for f in range(fa, fb + 1):
            t = 0.0 if fb == fa else (f - fa) / (fb - fa)
            obj.location = (a[0] + d.x * t, a[1] + d.y * t, obj.location.z)
            obj.rotation_euler = (0.0, 0.0, yaw)
            obj.keyframe_insert("location", frame=f)
            obj.keyframe_insert("rotation_euler", index=2, frame=f)
            keys += 1
    for fc in B.fcurves(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return {"vehicle": obj.name, "keys": keys}


# -- budgets ---------------------------------------------------------------------------------

# Targets per density level (references/levels.md explains each row). heroes are movers the
# story needs; extras are tagged crowd and traffic. shot_s bounds every cut, seconds the whole
# take sent in one request.
DENSITY = {
    "simple": {"footprint_m": 20, "objects": (10, 80), "heroes": (1, 2), "extras": (0, 2),
               "shots": (1, 1), "shot_s": (4, 6), "seconds": (4, 6)},
    "medium": {"footprint_m": 40, "objects": (50, 250), "heroes": (1, 2), "extras": (0, 12),
               "shots": (1, 2), "shot_s": (3, 8), "seconds": (5, 10)},
    "advanced": {"footprint_m": 80, "objects": (150, 800), "heroes": (2, 4), "extras": (10, 60),
                 "shots": (2, 4), "shot_s": (2.5, 6), "seconds": (8, 12)},
    "expert": {"footprint_m": 120, "objects": (500, 5000), "heroes": (2, 6), "extras": (50, 300),
               "shots": (3, 12), "shot_s": (2, 5), "seconds": (10, 15)},
}


def _animated(obj):
    ad = obj.animation_data
    if ad and ad.action:
        return True
    # A figure whose root stands still but whose limbs gesture still performs.
    return bool(obj.get("jointed")) and any(c.animation_data and c.animation_data.action for c in obj.children_recursive)


def _in_figure(obj):
    """True for a limb of a jointed figure, at any depth."""
    p = obj.parent
    while p is not None:
        if p.get("jointed"):
            return True
        p = p.parent
    return False


def elements(scene=None):
    """Scene elements as a viewer counts them: every tagged mesh, with a jointed figure
    counted once (its root) and not once per limb."""
    sc = scene or bpy.context.scene
    return [o.name for o in sc.objects if o.get(B.TAG) and o.visible_get() and not _in_figure(o)
            and (o.type == "MESH" or o.get("jointed"))]


def movers(scene=None):
    """(heroes, extras): animated objects that move on their own, limbs, riders parented to
    a vehicle, cameras and rigs excluded."""
    sc = scene or bpy.context.scene
    heroes, extras = [], []
    for o in sc.objects:
        if not o.get(B.TAG) or not o.visible_get() or o.name.startswith(("CAM_", "RIG_", "NULL_", "CRV_")):
            continue
        if _in_figure(o):
            continue
        if _animated(o):
            (extras if o.get("extra") else heroes).append(o.name)
    return heroes, extras


def audit_budget(density, scene=None):
    """Count what the scene holds against a density level: elements (a jointed figure counts
    once), heroes, extras,
    shots, the length of every shot, footprint and duration. Returns a list of gaps; []
    means the scene meets the level."""
    sc = scene or bpy.context.scene
    target = DENSITY[density]
    bpy.context.view_layer.update()  # new objects have no world matrix until an update
    meshes = [o for o in sc.objects if o.get(B.TAG) and o.visible_get() and o.type == "MESH"]
    count = len(elements(sc))
    heroes, extras = movers(sc)
    xs = [o.matrix_world.translation.x for o in meshes]
    ys = [o.matrix_world.translation.y for o in meshes]
    footprint = max((max(xs) - min(xs)) if xs else 0.0, (max(ys) - min(ys)) if ys else 0.0)
    cuts = B.cut_list(sc) if B._bound_markers(sc) else []
    shots = len(cuts) or 1
    seconds = (sc.frame_end - sc.frame_start + 1) / sc.render.fps
    gaps = []
    for label, value, (lo, hi) in (("objects", count, target["objects"]), ("heroes", len(heroes), target["heroes"]),
                                   ("extras", len(extras), target["extras"]), ("shots", shots, target["shots"]),
                                   ("seconds", seconds, target["seconds"])):
        if not lo <= value <= hi:
            gaps.append({"check": label, "value": round(value, 2), "target": [lo, hi]})
    lo, hi = target["shot_s"]
    for c in cuts:
        if not lo - 0.05 <= c["duration_s"] <= hi + 0.05:
            gaps.append({"check": "shot_s", "shot": c["shot"], "value": c["duration_s"], "target": [lo, hi]})
    if footprint < target["footprint_m"] * 0.5:
        gaps.append({"check": "footprint_m", "value": round(footprint, 1), "target": target["footprint_m"]})
    return gaps
