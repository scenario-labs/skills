"""
gen_toolset_map: turn an Epic MCP catalog snapshot (ue_mcp.snapshot) into compact tool signatures,
so an agent can call a toolset without paying for its describe_toolset payload.

STATUS: run against the 5.8.3 snapshot (tests/arena/mcp-catalog-5.8.3 of the build project) on 2026-10-21.
Signatures are API facts read from the engine; the purpose notes in the skills' references are ours.

  python3 gen_toolset_map.py <catalog dir> [toolset substring ...] > out.md
  import gen_toolset_map as G; G.signature(tool_dict); G.render(catalog_dir, ["MaterialTools"])

One line per tool:  short_name(arg: type, optional?: type) -> return
Types: str, int, float, bool, [T] arrays, Ref<Class> for object references (pass {"refPath": "/Game/..."}
or an actor/component path), {..} for a struct (see the toolset's own describe for its fields), enum(a|b).
"""

__version__ = "0.2.1"  # Unreal Engine Expert Skills v0.2.1

import json
import os
import sys


def _short_class(title):
    return (title or "").split(".")[-1].split("/")[-1]


def _type(schema, depth=0):
    if not isinstance(schema, dict):
        return "any"
    if "enum" in schema:
        vals = [str(x) for x in schema["enum"]]
        return "enum(%s)" % ("|".join(vals) if len(vals) <= 4 else "|".join(vals[:3]) + "|+%d" % (len(vals) - 3))
    t = schema.get("type")
    if t == "array":
        return "[%s]" % _type(schema.get("items", {}), depth + 1)
    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        if "refPath" in props:
            return "Ref<%s>" % (_short_class(schema.get("title")) or "Object")
        if schema.get("title"):
            return "{%s}" % _short_class(schema["title"])
        if depth < 1 and props:
            return "{%s}" % ", ".join("%s: %s" % (k, _type(v, depth + 1)) for k, v in list(props.items())[:6])
        return "{..}"
    return {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}.get(t, t or "any")


def signature(tool):
    name = tool.get("name", "").split(".")[-1]
    sch = tool.get("inputSchema", {}) or {}
    req = set(sch.get("required", []))
    args = []
    for k, v in (sch.get("properties", {}) or {}).items():
        args.append("%s%s: %s" % (k, "" if k in req else "?", _type(v)))
    out = (tool.get("outputSchema", {}) or {}).get("properties", {}) or {}
    ret = _type(out["returnValue"]) if "returnValue" in out else ("{%s}" % ", ".join(out)) if out else "None"
    return "%s(%s) -> %s" % (name, ", ".join(args), ret)


def _walk(schema, found):
    if not isinstance(schema, dict):
        return
    props = schema.get("properties")
    if props and schema.get("title") and "refPath" not in props:
        found.setdefault(_short_class(schema["title"]), [schema, 0])[1] += 1
    for v in (props or {}).values():
        _walk(v, found)
    _walk(schema.get("items"), found)


def struct_legend(catalog_dir, top=30):
    """The most used struct shapes in the catalog, one line each, so signatures that say {Vector} can be
    called without a describe: e.g. ToolsetTransform {location: {Vector}, rotation: {Rotator}, scale: {Vector}}."""
    found = {}
    for fn in os.listdir(catalog_dir):
        if fn.endswith(".json") and fn != "index.json":
            with open(os.path.join(catalog_dir, fn)) as fh:
                d = json.load(fh)
            for t in d.get("tools", []):
                _walk(t.get("inputSchema"), found)
                _walk(t.get("outputSchema"), found)
    rows = sorted(found.items(), key=lambda kv: -kv[1][1])[:top]
    out = []
    for name, (sch, n) in rows:
        fields = ", ".join("%s: %s" % (k, _type(v, 1)) for k, v in sch.get("properties", {}).items())
        out.append("- `%s {%s}` (used %d times)" % (name, fields, n))
    return "\n".join(out)


def render(catalog_dir, names=None, heading_level=3):
    with open(os.path.join(catalog_dir, "index.json")) as fh:
        index = json.load(fh)["toolsets"]
    lines = []
    for ts in sorted(index):
        if names and not any(n in ts for n in names):
            continue
        info = index[ts]
        with open(os.path.join(catalog_dir, ts + ".json")) as fh:
            d = json.load(fh)
        lines.append("%s `%s` (%d tools, describe is about %d tokens)" % ("#" * heading_level, ts, info["tools"],
                                                                         info["payload_tokens"]))
        for t in sorted(d.get("tools", []), key=lambda t: t["name"]):
            lines.append("- `%s`" % signature(t))
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[2:3] == ["--structs"]:
        print(struct_legend(sys.argv[1]))
    else:
        print(render(sys.argv[1], sys.argv[2:]))
