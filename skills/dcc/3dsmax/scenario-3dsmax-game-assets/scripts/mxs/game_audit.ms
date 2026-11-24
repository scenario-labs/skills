-- game_audit.ms: read-only engine-asset audit for scenario-3dsmax-game-assets.
-- channel: mcp-safe | bridge | batch | handoff
-- checked against notes/game-assets digests (rules),
--         scripting-pipeline__pymxs-using-2027.md and scenario-3dsmax-expert/references/api-names.txt (names)
-- Changes nothing in the scene and writes no file. Uses none of the Safe Scene Script Execution
-- blocked commands. The last expression sets `result` to a JSON string that
-- scripts/game_rules.py reads (python game_rules.py report <file> --target unreal).
-- Scope: the current selection, or every object when nothing is selected.
-- Names not in the saved docs carry [verify] on their line.

fn gaJsonStr s = (
    s = s as string
    local out = ""
    for i = 1 to s.count do (
        local c = s[i]
        if c == "\"" then out += "\\\""
        else if c == "\\" then out += "\\\\"
        else out += c
    )
    "\"" + out + "\""
)

fn gaJoin arr sep = (
    local out = ""
    for i = 1 to arr.count do (
        if i > 1 do out += sep
        out += arr[i]
    )
    out
)

fn gaNum v = (
    -- float to JSON number; MAXScript may print 1e-06 style, which JSON accepts
    local s = v as string
    if (findString s "#") != undefined then "null" else s   -- NaN or infinity prints with #
)

fn gaP3 p = "[" + (gaNum p.x) + "," + (gaNum p.y) + "," + (gaNum p.z) + "]"

-- Convexity of a collision hull: count vertices lying outside any face plane (tolerance in system units).
fn gaConvexViolations m tol = (
    local bad = 0
    local nf = getNumFaces m                              -- [verify]
    local nv = getNumVerts m                              -- [verify]
    for f = 1 to nf do (
        local fn3 = getFaceNormal m f                     -- [verify]
        local fv = getFace m f                            -- [verify] point3 of vertex indices
        local p0 = getVert m (fv.x as integer)            -- [verify]
        for v = 1 to nv do (
            if (dot fn3 ((getVert m v) - p0)) > tol do bad += 1   -- [verify] dot
        )
    )
    bad
)

fn gaAuditNode n faceCap:500000 = (
    local m = snapshotAsMesh n                            -- [verify] world-space TriMesh of the stack result
    local nf = getNumFaces m                              -- [verify]
    local nv = getNumVerts m                              -- [verify]
    local sg0 = -1
    if nf <= faceCap do (
        sg0 = 0
        for f = 1 to nf do if (getFaceSmoothGroup m f) == 0 do sg0 += 1   -- [verify]
    )
    local openE = (meshop.getOpenEdges m).numberSet       -- [verify]
    local isoV = (meshop.getIsoVerts m).numberSet         -- [verify]
    local maps = #()
    for ch = -2 to ((meshop.getNumMaps m) - 1) do (      -- [verify] -2 alpha, -1 illum, 0 vertex color, 1+ UV
        if (meshop.getMapSupport m ch) do append maps (ch as string)   -- [verify]
    )
    local ngons = -1
    if classOf n == Editable_Poly do (                    -- [verify] Editable_Poly class name
        ngons = 0
        for f = 1 to (polyop.getNumFaces n) do if (polyop.getFaceDeg n f) > 4 do ngons += 1   -- [verify]
    )
    local mn = n.min
    local mx = n.max
    local s = n.scale                                     -- [verify]
    local negScale = (s.x * s.y * s.z) < 0
    local mods = for md in n.modifiers collect gaJsonStr (classOf md)   -- [verify] node.modifiers
    local matCls = if n.material == undefined then "null" else gaJsonStr (classOf n.material)
    local subCount = 0
    if n.material != undefined and (classOf n.material) == Multimaterial do subCount = n.material.numsubs   -- [verify]
    local convexBad = -1
    if (matchPattern n.name pattern:"UCX_*") and nf <= 2000 do convexBad = gaConvexViolations m 0.01
    "{" + \
        "\"name\":" + (gaJsonStr n.name) + \
        ",\"class\":" + (gaJsonStr (classOf n)) + \
        ",\"tris\":" + (nf as string) + \
        ",\"verts\":" + (nv as string) + \
        ",\"ngons\":" + (ngons as string) + \
        ",\"open_edges\":" + (openE as string) + \
        ",\"iso_verts\":" + (isoV as string) + \
        ",\"sg0_faces\":" + (sg0 as string) + \
        ",\"map_channels\":[" + (gaJoin maps ",") + "]" + \
        ",\"bbox_min\":" + (gaP3 mn) + \
        ",\"bbox_max\":" + (gaP3 mx) + \
        ",\"pos\":" + (gaP3 n.pos) + \
        ",\"pivot\":" + (gaP3 n.pivot) + \
        ",\"scale\":" + (gaP3 s) + \
        ",\"rotation_identity\":" + ((n.rotation == (quat 0 0 0 1)) as string) + \
        ",\"negative_scale\":" + (negScale as string) + \
        ",\"parent\":" + (if n.parent == undefined then "null" else gaJsonStr n.parent.name) + \
        ",\"modifiers\":[" + (gaJoin mods ",") + "]" + \
        ",\"material_class\":" + matCls + \
        ",\"sub_materials\":" + (subCount as string) + \
        ",\"convex_violations\":" + (convexBad as string) + \
    "}"
)

fn gaAuditScene = (
    local sel = if selection.count > 0 then (selection as array) else (objects as array)
    local geo = #()
    local others = #()
    for n in sel do (
        if (superClassOf n == GeometryClass) and (canConvertTo n TriMeshGeometry) then (   -- [verify] canConvertTo
            append geo (gaAuditNode n)
        ) else (
            append others ("{\"name\":" + (gaJsonStr n.name) + ",\"class\":" + (gaJsonStr (classOf n)) + \
                ",\"pos\":" + (gaP3 n.pos) + ",\"parent\":" + \
                (if n.parent == undefined then "null" else gaJsonStr n.parent.name) + "}")
        )
    )
    "{\"units\":" + (gaJsonStr units.SystemType) + \
        ",\"system_scale\":" + (gaNum units.SystemScale) + \
        ",\"nodes\":[" + (gaJoin geo ",") + "]" + \
        ",\"helpers\":[" + (gaJoin others ",") + "]}"
)

result = gaAuditScene()
result
