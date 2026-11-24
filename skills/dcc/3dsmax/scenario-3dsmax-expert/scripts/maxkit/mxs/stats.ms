-- maxkit/mxs/stats.ms: scene numbers (twin of maxkit/stats.py), read-only
-- Checked against
-- scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (maxFilePath,
-- maxFileName, getSaveRequired, doesFileExist) and scripting-pipeline__pymxs-renderer-2027.md (renderers).
-- Needs mxk_dict from result.ms (max_wrap inlines it first). Safe for mcp-safe: no blocked command.

fn mxk_stats_snapshot = (
    local nObj = 0, nGeo = 0, nFaces = 0, nVerts = 0, nMods = 0
    local bases = #(), baseCounts = #()
    local layerNames = #(), layerCounts = #()
    for o in objects do (  -- [verify] objects
        nObj += 1
        nMods += o.modifiers.count  -- [verify] node.modifiers
        local ln = o.layer.name  -- [verify] node.layer
        local li = findItem layerNames ln  -- [verify] findItem
        if li == 0 then (append layerNames ln; append layerCounts 1) else layerCounts[li] += 1
        if superClassOf o == GeometryClass do (  -- [verify] superClassOf, GeometryClass
            nGeo += 1
            local pc = getPolygonCount o  -- [verify] getPolygonCount -> #(faces, verts)
            nFaces += pc[1]
            nVerts += pc[2]
        )
        local b = getHandleByAnim o.baseObject  -- [verify] getHandleByAnim, baseObject
        local bi = findItem bases b
        if bi == 0 then (append bases b; append baseCounts 1) else baseCounts[bi] += 1
    )
    local inst = 0
    for c in baseCounts where c > 1 do inst += c
    local missing = #()
    for t in getClassInstances BitmapTexture do (  -- [verify] getClassInstances, BitmapTexture
        if t.filename != undefined and t.filename != "" and not (doesFileExist t.filename) do appendIfUnique missing t.filename  -- [verify] appendIfUnique
    )
    local layers = Dictionary #string  -- [verify]
    for i = 1 to layerNames.count do PutDictValue layers layerNames[i] layerCounts[i]  -- [verify] PutDictValue
    local f = maxFilePath + maxFileName
    mxk_dict #( \
        #("objects", nObj), #("geometry", nGeo), #("faces", nFaces), #("vertices", nVerts), \
        #("instances", inst), #("modifiers", nMods), #("materials", sceneMaterials.count), \
        #("missing_maps", missing), \
        #("file_size", (if f != "" and doesFileExist f then getFileSize f else undefined)), \
        #("layers", layers), \
        #("system_unit", (units.SystemType as string)), #("system_scale", units.SystemScale), \
        #("renderer", ((classOf renderers.current) as string)), \
        #("file", (if f != "" then f else undefined)), #("save_required", getSaveRequired()) )
    -- [verify] sceneMaterials, getFileSize, units.SystemType, units.SystemScale
)
