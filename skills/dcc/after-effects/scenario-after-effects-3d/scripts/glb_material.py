#!/usr/bin/env python3
"""glb_material.py: list or change the PBR factors of a GLB's materials before After Effects imports it.

After Effects 27.0 refuses Roughness and Metallic on a model layer by script ("hidden"); the importer reads the
glTF factors, so edit them in the file. The source is never overwritten: the result goes to a new path.

  python3 glb_material.py list model.glb
  python3 glb_material.py set model.glb model_v002.glb --material Rubber_Cream --roughness 0.25
  python3 glb_material.py set model.glb model_v002.glb --all --roughness-scale 0.5

roughnessFactor and metallicFactor multiply any metallicRoughness texture (glTF 2.0), so a scale works on textured
materials too. Standard library only.
"""
import argparse
import json
import struct
import sys


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()



def read_glb(path):
    data = _read_bytes(path)
    magic, version, length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        sys.exit("%s is not a GLB (magic %r): check the download, a 3D asset can arrive as another format" % (path, magic))
    jlen, jtype = struct.unpack("<II", data[12:20])
    if jtype != 0x4E4F534A:
        sys.exit("first chunk is not JSON")
    doc = json.loads(data[20:20 + jlen].decode("utf-8"))
    rest = data[20 + jlen:]
    return doc, rest


def write_glb(path, doc, rest):
    js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + len(rest)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(rest)


def describe(m):
    p = m.get("pbrMetallicRoughness", {})
    return {
        "name": m.get("name"),
        "roughness": p.get("roughnessFactor", 1.0),
        "metallic": p.get("metallicFactor", 1.0),
        "roughnessTexture": "metallicRoughnessTexture" in p,
        "baseColorTexture": "baseColorTexture" in p,
        "extensions": sorted(m.get("extensions", {}).keys()),
    }


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("src")
    st = sub.add_parser("set")
    st.add_argument("src")
    st.add_argument("dst")
    st.add_argument("--material", action="append", default=[], help="material name, repeatable")
    st.add_argument("--all", action="store_true")
    st.add_argument("--roughness", type=float)
    st.add_argument("--roughness-scale", type=float)
    st.add_argument("--metallic", type=float)
    a = ap.parse_args()
    doc, rest = read_glb(a.src)
    mats = doc.get("materials", [])
    if a.cmd == "list":
        print(json.dumps([describe(m) for m in mats], indent=1))
        return
    if a.dst == a.src:
        sys.exit("write to a new file (model_v002.glb): the source stays as it was")
    names = set(a.material)
    changed = []
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
        changed.append(describe(m))
    missing = names - set(m.get("name") for m in mats)
    if missing:
        sys.exit("no material named: %s" % ", ".join(sorted(missing)))
    write_glb(a.dst, doc, rest)
    print(json.dumps({"written": a.dst, "changed": changed}, indent=1))


if __name__ == "__main__":
    main()
