#!/usr/bin/env python3
"""glb_material.py: read and change a GLB's materials before After Effects imports it.

After Effects 27.0 refuses Roughness and Metallic on a model layer by script ("hidden"); the importer reads the
glTF factors and textures, so edit them in the file. The source is never overwritten: the result goes to a new path.

  python3 glb_material.py list model.glb [--brand Fabric_Coral=#E0452C]
  python3 glb_material.py set model.glb model_v002.glb --material Rubber_Cream --roughness 0.25
  python3 glb_material.py set model.glb model_v002.glb --all --roughness-scale 0.5
  python3 glb_material.py set model.glb model_v002.glb --material Fabric_Coral --normal-flatten 0.35
  python3 glb_material.py tint model.glb model_v002.glb --brand Fabric_Coral=#E0452C
  python3 glb_material.py linear-store model.glb model_ae.glb

list: per material, the factors, which textures it uses, and its mean base color in linear light (factor times
the texture's mean, the texture decoded from sRGB). With --brand NAME=#RRGGBB it adds the brand color in linear.
It also gives the per-channel scale from the model to the brand, the luminance ratio and the CIE76 color distance.

tint: scales the base color per channel in linear light so its mean equals the brand color. A texture keeps its
pattern (each pixel gets the same per-channel scale); a material without texture gets a new factor.

set --normal-flatten K: rewrites the normal texture with its tilt scaled by K (0..1), so a weave keeps its pattern
with less depth. Use it when a back light lights the camera-facing side through a strong normal map.

linear-store: Advanced 3D in a linearized 27.0 project shades with base colors as stored. It skips the sRGB decode a
glTF texture needs and encodes the factors. Measured: a 0.35 factor and a coral texture rendered at their sRGB
encoded values, about 1.8 and 2.1 times too bright. This writes the textures as linear bytes and the factors
decoded, so the render shades with the model's real albedo. Do the same to a calibration floor.

roughnessFactor and metallicFactor multiply any metallicRoughness texture (glTF 2.0), so a scale works on textured
materials too. Standard library only (PNG textures, 8 bit, not interlaced).
"""
import argparse
import json
import math
import struct
import sys
import zlib


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read_glb(path):
    data = _read_bytes(path)
    magic, _version, _length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        sys.exit("%s is not a GLB (magic %r): check the download, a 3D asset can arrive as another format" % (path, magic))
    jlen, jtype = struct.unpack("<II", data[12:20])
    if jtype != 0x4E4F534A:
        sys.exit("first chunk is not JSON")
    doc = json.loads(data[20:20 + jlen].decode("utf-8"))
    rest = data[20 + jlen:]
    binary = b""
    if len(rest) >= 8:
        blen, _btype = struct.unpack("<II", rest[:8])
        binary = rest[8:8 + blen]
    return doc, binary


def write_glb(path, doc, binary):
    js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    binary = binary + b"\0" * ((4 - len(binary) % 4) % 4)
    if doc.get("buffers"):
        doc["buffers"][0]["byteLength"] = len(binary)
        js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
        js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + (8 + len(binary) if binary else 0)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        if binary:
            f.write(struct.pack("<II", len(binary), 0x004E4942))
            f.write(binary)


# ---------- PNG, 8 bit, standard library ----------

def png_decode(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG texture (only PNG is read here)")
    pos, idat, w = 8, [], 0
    h = depth = ctype = 0
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace or ctype not in (0, 2, 4, 6):
                raise ValueError("PNG must be 8 bit, not interlaced, gray or RGB(A)")
        elif typ == b"IDAT":
            idat.append(body)
        pos += 12 + ln
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ft == 1:
            for x in range(ch, stride):
                line[x] = (line[x] + line[x - ch]) & 255
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(stride):
                left = line[x - ch] if x >= ch else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(stride):
                a = line[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def png_encode(w, h, ch, pixels):
    ctype = {1: 0, 2: 4, 3: 2, 4: 6}[ch]
    stride = w * ch
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]

    def chunk(t, body):
        return struct.pack(">I", len(body)) + t + body + struct.pack(">I", zlib.crc32(t + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def s2l(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def l2s(v):
    v = max(0.0, min(1.0, v))
    return v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


DEC = [s2l(i / 255.0) for i in range(256)]


def image_bytes(doc, binary, tex_index):
    img = doc["images"][doc["textures"][tex_index]["source"]]
    bv = doc["bufferViews"][img["bufferView"]]
    off = bv.get("byteOffset", 0)
    return img, binary[off:off + bv["byteLength"]]


def replace_image(doc, binary, tex_index, new_bytes):
    """Append the new image at the end of the buffer and point the image at a new bufferView."""
    img = doc["images"][doc["textures"][tex_index]["source"]]
    binary = binary + b"\0" * ((4 - len(binary) % 4) % 4)
    doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(new_bytes)})
    img["bufferView"] = len(doc["bufferViews"]) - 1
    img["mimeType"] = "image/png"
    return binary + new_bytes


def texture_mean_linear(doc, binary, tex_index):
    _img, data = image_bytes(doc, binary, tex_index)
    w, h, ch, px = png_decode(data)
    n = w * h
    sums = [0.0, 0.0, 0.0]
    for k in range(3):
        c = k if ch >= 3 else 0
        hist = [0] * 256
        for v in px[c::ch]:
            hist[v] += 1
        sums[k] = sum(DEC[i] * hist[i] for i in range(256)) / n
    return sums


def map_texture(doc, binary, tex_index, fn):
    """fn(list of 3 channel byte tables) -> rewrite texture through per-channel 256-entry tables."""
    _img, data = image_bytes(doc, binary, tex_index)
    w, h, ch, px = png_decode(data)
    tables = fn()
    out = bytearray(px)
    for k in range(min(3, ch)):
        t = tables[k]
        out[k::ch] = bytes(t[v] for v in px[k::ch])
    return replace_image(doc, binary, tex_index, png_encode(w, h, ch, out))


def hex_linear(hx):
    hx = hx.lstrip("#")
    return [s2l(int(hx[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]


def lab(rgb):
    m = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]
    xyz = [sum(m[r][c] * rgb[c] for c in range(3)) for r in range(3)]
    wp = [0.95047, 1.0, 1.08883]

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = (f(xyz[i] / wp[i]) for i in range(3))
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)]


def lum(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def mean_base(doc, binary, m):
    p = m.get("pbrMetallicRoughness", {})
    fac = p.get("baseColorFactor", [1, 1, 1, 1])[:3]
    if "baseColorTexture" in p:
        t = texture_mean_linear(doc, binary, p["baseColorTexture"]["index"])
        return [fac[i] * t[i] for i in range(3)]
    return list(fac)


def describe(doc, binary, m, brands):
    p = m.get("pbrMetallicRoughness", {})
    d = {
        "name": m.get("name"),
        "roughness": p.get("roughnessFactor", 1.0),
        "metallic": p.get("metallicFactor", 1.0),
        "roughnessTexture": "metallicRoughnessTexture" in p,
        "baseColorTexture": "baseColorTexture" in p,
        "normalTexture": "normalTexture" in m,
        "extensions": sorted(m.get("extensions", {}).keys()),
    }
    try:
        mb = mean_base(doc, binary, m)
        d["baseColorLinear"] = [round(v, 4) for v in mb]
        d["luminance"] = round(lum(mb), 4)
        if m.get("name") in brands:
            br = brands[m.get("name")]
            la, lb = lab(mb), lab(br)
            d["brand"] = {"linear": [round(v, 4) for v in br], "luminance": round(lum(br), 4),
                          "scaleToBrand": [round(br[i] / mb[i], 3) if mb[i] > 0 else None for i in range(3)],
                          "luminanceRatio": round(lum(mb) / lum(br), 3) if lum(br) > 0 else None,
                          "deltaE76": round(math.sqrt(sum((la[i] - lb[i]) ** 2 for i in range(3))), 1)}
    except ValueError as e:
        d["baseColorLinear"] = "unread: %s" % e
    return d


def parse_brands(items):
    out = {}
    for it in items:
        if "=" not in it:
            sys.exit("--brand takes MATERIAL=#RRGGBB")
        name, hx = it.split("=", 1)
        out[name] = hex_linear(hx)
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("src")
    ls.add_argument("--brand", action="append", default=[], help="MATERIAL=#RRGGBB, repeatable")
    st = sub.add_parser("set")
    st.add_argument("src")
    st.add_argument("dst")
    st.add_argument("--material", action="append", default=[], help="material name, repeatable")
    st.add_argument("--all", action="store_true")
    st.add_argument("--roughness", type=float)
    st.add_argument("--roughness-scale", type=float)
    st.add_argument("--metallic", type=float)
    st.add_argument("--normal-flatten", type=float, help="scale the normal texture's tilt by K (0..1)")
    tn = sub.add_parser("tint")
    tn.add_argument("src")
    tn.add_argument("dst")
    tn.add_argument("--brand", action="append", required=True, help="MATERIAL=#RRGGBB, repeatable")
    lsx = sub.add_parser("linear-store")
    lsx.add_argument("src")
    lsx.add_argument("dst")
    a = ap.parse_args()
    doc, binary = read_glb(a.src)
    mats = doc.get("materials", [])
    if a.cmd == "list":
        brands = parse_brands(a.brand)
        print(json.dumps([describe(doc, binary, m, brands) for m in mats], indent=1))
        return
    if a.dst == a.src:
        sys.exit("write to a new file (model_v002.glb): the source stays as it was")
    changed = []
    if a.cmd == "tint":
        brands = parse_brands(a.brand)
        missing = set(brands) - set(m.get("name") for m in mats)
        if missing:
            sys.exit("no material named: %s" % ", ".join(sorted(missing)))
        for m in mats:
            if m.get("name") not in brands:
                continue
            br, mb = brands[m["name"]], mean_base(doc, binary, m)
            sc = [br[i] / mb[i] if mb[i] > 0 else 1.0 for i in range(3)]
            p = m.setdefault("pbrMetallicRoughness", {})
            if "baseColorTexture" in p:
                binary = map_texture(doc, binary, p["baseColorTexture"]["index"],
                                     lambda sc=sc: [[int(round(255 * l2s(DEC[v] * sc[k]))) for v in range(256)] for k in range(3)])
            else:
                f = p.get("baseColorFactor", [1, 1, 1, 1])
                p["baseColorFactor"] = [min(1.0, f[i] * sc[i]) for i in range(3)] + [f[3] if len(f) > 3 else 1]
            changed.append({"name": m["name"], "scale": [round(v, 3) for v in sc], "after": describe(doc, binary, m, brands)})
    elif a.cmd == "linear-store":
        done = set()
        for m in mats:
            p = m.setdefault("pbrMetallicRoughness", {})
            if "baseColorFactor" in p:
                f = p["baseColorFactor"]
                p["baseColorFactor"] = [s2l(f[i]) for i in range(3)] + [f[3] if len(f) > 3 else 1]
            if "baseColorTexture" in p and p["baseColorTexture"]["index"] not in done:
                done.add(p["baseColorTexture"]["index"])
                binary = map_texture(doc, binary, p["baseColorTexture"]["index"],
                                     lambda: [[int(round(255 * DEC[v])) for v in range(256)] for _k in range(3)])
            changed.append(m.get("name"))
    else:
        names = set(a.material)
        missing = names - set(m.get("name") for m in mats)
        if missing:
            sys.exit("no material named: %s" % ", ".join(sorted(missing)))
        for m in mats:
            if not a.all and m.get("name") not in names:
                continue
            p = m.setdefault("pbrMetallicRoughness", {})
            if a.roughness is not None:
                p["roughnessFactor"] = max(0.0, min(1.0, a.roughness))
            if a.roughness_scale is not None:
                p["roughnessFactor"] = max(0.0, min(1.0, p.get("roughnessFactor", 1.0) * a.roughness_scale))
            if a.metallic is not None:
                p["metallicFactor"] = max(0.0, min(1.0, a.metallic))
            if a.normal_flatten is not None and "normalTexture" in m:
                k = max(0.0, min(1.0, a.normal_flatten))
                binary = flatten_normal(doc, binary, m["normalTexture"]["index"], k)
            changed.append(m.get("name"))
    write_glb(a.dst, doc, binary)
    print(json.dumps({"written": a.dst, "changed": changed}, indent=1))


def flatten_normal(doc, binary, tex_index, k):
    _img, data = image_bytes(doc, binary, tex_index)
    w, h, ch, px = png_decode(data)
    out = bytearray(px)
    for i in range(0, len(px), ch):
        x = (px[i] / 127.5 - 1) * k
        y = (px[i + 1] / 127.5 - 1) * k
        z = math.sqrt(max(0.0, 1 - x * x - y * y))
        out[i] = int(round((x + 1) * 127.5))
        out[i + 1] = int(round((y + 1) * 127.5))
        out[i + 2] = int(round((z + 1) * 127.5))
    return replace_image(doc, binary, tex_index, png_encode(w, h, ch, out))


if __name__ == "__main__":
    main()
