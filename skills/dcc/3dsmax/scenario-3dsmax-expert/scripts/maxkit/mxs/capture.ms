-- maxkit/mxs/capture.ms: viewport grab and render to a new file (twin of maxkit/capture.py)
-- Checked against
-- scripting-pipeline__maxscript-viewport-drawing-methods-getviewportdib-2027.md (gw.getViewportDib),
-- scripting-pipeline__maxscript-bitmap-values-2027.md (filename before save, close) and
-- scripting-pipeline__pymxs-renderer-2027.md (render outputFile:).
-- Whether Safe Scene Script Execution lets these write files is not documented: read the result,
-- and if "saved" is false ask the user for a manual capture. Never overwrites (mxk_nextFree).

fn mxk_nextFree p = (
    if not (doesFileExist p) then p else (
        local dir = getFilenamePath p, stem = getFilenameFile p, ext = getFilenameType p  -- [verify] getFilename*
        local i = 2
        local cand = dir + stem + "_v" + (formattedPrint i format:"03d") + ext  -- [verify] formattedPrint
        while doesFileExist cand do (i += 1; cand = dir + stem + "_v" + (formattedPrint i format:"03d") + ext)
        cand
    )
)

fn mxk_capture_viewport p view:undefined = (
    if maxOps.isInNonInteractiveMode() do return (mxk_dict #(#("saved", false), #("error", "no viewport in batch")))
    if view != undefined do (
        viewport.setType view  -- [verify] viewport.setType with #view_persp_user, #view_front, #view_left, #view_top
        max tool zoomextents all
    )
    redrawViews()  -- [verify] MAXScript redrawViews
    local dib = gw.getViewportDib captureAlpha:false gammaCorrect:true
    local outPath = mxk_nextFree p
    local ok = false
    try (dib.filename = outPath; ok = save dib) catch (ok = false)
    local w = dib.width, h = dib.height
    close dib
    mxk_dict #(#("path", outPath), #("saved", ok), #("width", w), #("height", h), #("view", (if view == undefined then "active" else view as string)))
)

fn mxk_capture_views dir views:#(#view_persp_user, #view_front, #view_left, #view_top) = (
    local original = viewport.getType()  -- [verify] viewport.getType in MAXScript
    local out = for v in views collect (mxk_capture_viewport (dir + "\\view_" + (v as string) + ".png") view:v)
    try (viewport.setType original; redrawViews()) catch ()
    out
)

-- The color of a bitmap whose sampled pixels all match, else undefined. An aborted render is flat.
-- rows:0 step:1 reads every pixel: confirm a flat sample with it before failing a render.
fn mxk_flatColor bmp rows:16 step:4 = (
    local w = bmp.width, h = bmp.height, seen = undefined, flat = true
    if rows < 2 or rows > h do rows = h
    for i = 0 to rows - 1 while flat do (
        local y = if rows == h then i else (i * (h - 1) / (rows - 1))
        local row = getPixels bmp [0, y] w
        for j = 1 to row.count by step while flat do (
            local k = [(row[j].r as integer), (row[j].g as integer), (row[j].b as integer)]
            if seen == undefined then seen = k else if k != seen do flat = false
        )
    )
    if flat then seen else undefined
)

fn mxk_capture_render p cam:undefined w:undefined h:undefined = (
    local outPath = mxk_nextFree p
    local bmp = undefined
    if maxOps.isInNonInteractiveMode() and (matchPattern ((classOf renderers.current) as string) pattern:"*arnold*") do
        return (mxk_dict #(#("path", outPath), #("saved", false), #("error", "Arnold crashes 3ds Max Batch (2027.3): render in a live session or switch to Default_Scanline_Renderer")))
    local sized = w != undefined and h != undefined
    if (w == undefined) != (h == undefined) or (sized and (w < 1 or h < 1)) do
        return (mxk_dict #(#("path", outPath), #("saved", false), #("error", "pass w: and h: together, each 1 or more")))
    if not maxOps.isInNonInteractiveMode() do (
        local missing = #()
        for t in getClassInstances BitmapTexture where t.filename != undefined and t.filename != "" and not (doesFileExist t.filename) do appendIfUnique missing t.filename
        if missing.count > 0 do
            return (mxk_dict #(#("path", outPath), #("saved", false), #("missing_maps", missing), #("error", "missing maps: a live render stops on the modal Missing Map Files dialog; relink or remove them first")))
    )
    try (
        if cam != undefined and sized then
            bmp = render camera:cam outputwidth:w outputheight:h outputFile:outPath vfb:false  -- [verify] camera:, outputwidth:, outputheight:, vfb:
        else if cam != undefined then
            bmp = render camera:cam outputFile:outPath vfb:false
        else if sized then
            bmp = render outputwidth:w outputheight:h outputFile:outPath vfb:false
        else
            bmp = render outputFile:outPath vfb:false
    ) catch ()
    local flat = if bmp != undefined then mxk_flatColor bmp else undefined
    if flat != undefined do flat = mxk_flatColor bmp rows:0 step:1  -- the sample can miss a small subject
    local pairs = #(#("path", outPath), #("saved", (doesFileExist outPath) and flat == undefined), \
        #("renderer", ((classOf renderers.current) as string)), \
        #("camera", (if cam == undefined then undefined else cam.name)))
    if flat != undefined do (
        append pairs #("flat_color", flat)
        append pairs #("error", "one flat color: the render most likely aborted (read the render log), or the camera sees nothing")
    )
    if bmp != undefined do close bmp
    mxk_dict pairs
)
