-- render_audit.ms: read-only render and lighting audit, MAXScript twin of maxkit_render for mcp-safe.
-- channel: mcp-safe | batch | bridge | handoff
-- status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-renderer-2027.md and scripting-pipeline__maxscript-bitmap-values-2027.md
-- Changes nothing. Avoids every command on the Safe Scene Script Execution block list (no dotNet, no file ops).
-- Returns one string (the last expression) and prints it to the Listener.
(
    local ss = "" as stringStream  -- [verify] stringStream constructor form
    local r = renderers.current
    format "renderer=%\n" (classOf r) to:ss
    format "production=%\n" (classOf renderers.production) to:ss
    format "size=%x%\n" renderWidth renderHeight to:ss  -- [verify] renderWidth, renderHeight globals
    format "output=% save=%\n" rendOutputFilename rendSaveFile to:ss  -- [verify] globals
    -- renderer properties that matter for sampling, denoise, override and limits
    local keys = #("noise","sample","subdiv","denois","override","limit","threshold","adaptiv","depth","lock","exposure","progressive","bucket","clamp")
    for p in (getPropNames r) do
    (
        local pn = toLower (p as string)
        local hit = false
        for k in keys while not hit do if (findString pn k) != undefined do hit = true
        if hit do
        (
            local v = try (getProperty r p) catch ("<unreadable>")  -- [verify] getProperty
            format "prop %=%\n" p v to:ss
        )
    )
    -- render elements
    local mgr = maxOps.GetCurRenderElementMgr()  -- [verify] research report section 8
    local n = mgr.NumRenderElements()  -- [verify]
    for i = 0 to n - 1 do format "element %=%\n" i (classOf (mgr.GetRenderElement i)) to:ss  -- [verify]
    -- lights: class, name, on/enabled state when the property exists
    for l in lights do
    (
        local st = try (getProperty l #on) catch (try (getProperty l #enabled) catch "?")  -- [verify] property names
        format "light % class=% on=%\n" l.name (classOf l) st to:ss
    )
    -- OCIO displays and views (documented functions)
    local displays = try (ColorPipelineMgr.GetDisplayList()) catch #()
    for d in displays do format "display % views=%\n" d (colorPipelineMgr.GetViewList d) to:ss
    local out = ss as string
    format "%" out
    out
)
