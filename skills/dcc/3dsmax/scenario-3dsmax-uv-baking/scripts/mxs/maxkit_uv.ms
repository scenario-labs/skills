-- maxkit_uv.ms: MAXScript twin of maxkit_uv.py for the mcp-safe channel (per object, no shells, no raster).
-- channel: mcp-safe | handoff | bridge | batch
-- status: not yet run in 3ds Max; checked against notes/uv-baking-texturing digests (sR1sAWWT2x8 texel density definition)
-- Uses no dotNet, no file delete or copy, no INI writes. Returns a string; the caller prints or saves it.

fn uvk_unitToCm =
(
    local t = units.SystemType -- [verify] units.SystemType
    local f = case t of
    (
        #inches: 2.54
        #feet: 30.48
        #miles: 160934.4
        #millimeters: 0.1
        #centimeters: 1.0
        #meters: 100.0
        #kilometers: 100000.0
        default: 1.0
    )
    f * units.SystemScale -- [verify] units.SystemScale
)

fn uvk_signedArea pts =
(
    local a = 0.0
    for i = 1 to pts.count do
    (
        local p = pts[i]
        local q = pts[((mod i pts.count) as integer) + 1]
        a += p.x * q.y - q.x * p.y
    )
    a * 0.5
)

-- Returns "node|channel|faces|td_px_cm|flipped|outside_faces|note"
fn uvk_auditNode nd channel texSize =
(
    local tmp = copy nd
    local line = ""
    convertToPoly tmp -- [verify] convertToPoly
    if not (polyop.getMapSupport tmp channel) then -- [verify] polyop.getMapSupport
        line = nd.name + "|" + channel as string + "|0|0|0|0|no UVs on this channel"
    else
    (
        local cm = uvk_unitToCm()
        local worldA = 0.0
        local uvA = 0.0
        local flipped = 0
        local outside = 0
        local nf = polyop.getNumFaces tmp -- [verify] polyop.getNumFaces
        for f = 1 to nf do
        (
            worldA += (polyop.getFaceArea tmp f) * cm * cm -- [verify] polyop.getFaceArea
            local ids = polyop.getMapFace tmp channel f -- [verify] polyop.getMapFace
            local pts = for i in ids collect (polyop.getMapVert tmp channel i) -- [verify] polyop.getMapVert
            local sa = uvk_signedArea pts
            if sa < 0 do flipped += 1
            uvA += abs sa
            local out = false
            for p in pts do if p.x < 0 or p.x > 1 or p.y < 0 or p.y > 1 do out = true
            if out do outside += 1
        )
        local td = if worldA > 0 then texSize * sqrt (uvA / worldA) else 0.0
        local note = if nd.scale != [1,1,1] then "node scale not 1: Reset XForm first" else ""
        line = nd.name + "|" + channel as string + "|" + nf as string + "|" + td as string + "|" + flipped as string + "|" + outside as string + "|" + note
    )
    delete tmp
    line
)

fn uvk_auditNodes nodes channel texSize =
(
    local ss = stringStream ""
    format "node|channel|faces|td_px_cm|flipped|outside_faces|note\n" to:ss
    for n in nodes where (superClassOf n == GeometryClass) do format "%\n" (uvk_auditNode n channel texSize) to:ss
    ss as string
)

-- example: uvk_auditNodes (selection as array) 1 2048
