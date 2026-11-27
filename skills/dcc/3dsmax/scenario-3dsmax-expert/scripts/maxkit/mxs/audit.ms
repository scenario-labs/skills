-- maxkit/mxs/audit.ms: read-only scene audit (twin of maxkit/audit.py, same rule names)
-- Rules follow maxkit/audit.py; scene reads marked [verify].
-- Needs mxk_dict from result.ms (inlined first). Safe for mcp-safe: no blocked command.
-- Returns a Dictionary: findings (array of {severity, rule, node, message}) and tally.

fn mxk_audit_f sev rule nodeName msg = (
    mxk_dict #(#("severity", sev), #("rule", rule), #("node", nodeName), #("message", msg))
)

fn mxk_audit_isDefaultName n = (
    local pats = #("Box###*", "Sphere###*", "Cylinder###*", "Plane###*", "Teapot###*", "Object###*", \
                   "Line###*", "Rectangle###*", "Circle###*", "Group###*", "Camera###*", "Dummy###*", \
                   "Point###*", "Corona_Camera###*")
    local hit = false
    for p in pats while not hit do hit = matchPattern n pattern:(substituteString p "#" "?")  -- [verify] matchPattern
    hit
)

fn mxk_audit_all expectUnits:undefined expectRenderer:undefined farLimit:undefined = (
    local out = #()
    -- units
    local u = units.SystemType as string  -- [verify] units.SystemType
    if expectUnits != undefined and (toLower u) != (toLower (expectUnits as string)) do  -- [verify] toLower
        append out (mxk_audit_f "error" "units" undefined ("system unit is " + u + ", project expects " + (expectUnits as string)))
    if units.SystemScale != 1.0 do  -- [verify] units.SystemScale
        append out (mxk_audit_f "warn" "units" undefined ("system scale is " + (units.SystemScale as string)))
    local perMeter = case (toLower u) of ("millimeters": 1000.0; "centimeters": 100.0; "meters": 1.0; "kilometers": 0.001; "inches": 39.3701; "feet": 3.28084; "miles": 0.000621371; default: 100.0)
    local far = if farLimit != undefined then farLimit else (1000.0 * perMeter / (if units.SystemScale > 0 then units.SystemScale else 1.0))
    local seen = #(), counts = #(), layer0 = 0
    for o in objects do (  -- [verify] objects
        local n = o.name
        local si = findItem seen n
        if si == 0 then (append seen n; append counts 1) else counts[si] += 1
        if mxk_audit_isDefaultName n do append out (mxk_audit_f "warn" "names" n "generic default name")
        local s = o.scale  -- [verify] node.scale
        if s.x < 0 or s.y < 0 or s.z < 0 then append out (mxk_audit_f "warn" "transforms" n "negative scale: Reset XForm")
        else if (amax #(s.x, s.y, s.z)) - (amin #(s.x, s.y, s.z)) > 0.0001 do  -- [verify] amax, amin
            append out (mxk_audit_f "warn" "transforms" n "non-uniform scale: Reset XForm")
        if o.layer.name == "0" do layer0 += 1  -- [verify] node.layer
        if superClassOf o == GeometryClass do (  -- [verify] superClassOf, GeometryClass
            if o.material == undefined do append out (mxk_audit_f "warn" "materials" n "no material")  -- [verify] node.material
            local c = (o.min + o.max) / 2.0  -- [verify] node.min, node.max
            if (length c) > far do append out (mxk_audit_f "error" "units" n ((length c) as string + " units from the origin"))  -- [verify] length
        )
    )
    for i = 1 to seen.count where counts[i] > 1 do
        append out (mxk_audit_f "warn" "names" seen[i] ((counts[i] as string) + " nodes share this name"))
    if layer0 > 0 do append out (mxk_audit_f "warn" "layers" undefined ("layer 0 holds " + (layer0 as string) + " nodes"))
    for t in getClassInstances BitmapTexture do (  -- [verify] getClassInstances, BitmapTexture
        if t.filename != undefined and t.filename != "" and not (doesFileExist t.filename) do
            append out (mxk_audit_f "error" "maps" undefined ("missing map: " + t.filename))
    )
    local r = (classOf renderers.current) as string
    if expectRenderer != undefined and (findString (toLower r) (toLower expectRenderer)) == undefined do  -- [verify] findString
        append out (mxk_audit_f "error" "render" undefined ("renderer is " + r + ", project expects " + expectRenderer))
    if getSaveRequired() do append out (mxk_audit_f "info" "render" undefined "unsaved changes in the open scene")
    local tally = mxk_dict #(#("error", 0), #("warn", 0), #("info", 0))
    for f in out do (
        local sev = GetDictValue f "severity"
        PutDictValue tally sev ((GetDictValue tally sev) + 1)  -- [verify] PutDictValue
    )
    mxk_dict #(#("findings", out), #("tally", tally))
)
