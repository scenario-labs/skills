-- scene_audit.ms: read-only scene-assembly audit for the live session.
-- channel: mcp-safe | bridge | handoff
-- status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md and fundamentals-scene__system-unit-setup.md
-- Changes nothing. Avoids dotNet, file writes and INI calls (Safe Scene Script Execution).
-- Returns one string (JSON-like) as the last expression; the client reads it back.
(
	local farCm = 100000.0 -- 1 km [added] archviz default; pass a larger value for site models
	local cmPer = (case units.SystemType of ( -- [verify] units struct names
		#inches: 2.54
		#feet: 30.48
		#miles: 160934.4
		#millimeters: 0.1
		#centimeters: 1.0
		#meters: 100.0
		#kilometers: 100000.0
		default: 1.0
	)) * units.SystemScale -- [verify]
	local ss = stringStream ""
	local nObj = objects.count
	local nDefault = 0
	local nFar = 0
	local farMax = 0.0
	local nHeads = 0
	local maxDepth = 0
	local onLayer0 = 0
	local farList = #()
	local rx = "^(Box|Object|Line|Plane|Cylinder|Sphere|Rectangle|Shape|Group|Mesh|Point|Dummy|Teapot)\\s?\\d{2,}$"
	for o in objects do
	(
		if (findString o.name rx useRegex:true) != undefined do nDefault += 1 -- useRegex: 2027.2 and later
		local c = (o.min + o.max) / 2.0 -- [verify] node.min/max are world bbox
		local d = (length c) * cmPer
		if d > farCm do
		(
			nFar += 1
			if d > farMax do farMax = d
			if farList.count < 30 do append farList o.name
		)
		if isGroupHead o do -- [verify]
		(
			nHeads += 1
			local depth = 1
			local p = o.parent
			while p != undefined do (if isGroupHead p do depth += 1; p = p.parent)
			if depth > maxDepth do maxDepth = depth
		)
		if o.layer.name == "0" do onLayer0 += 1 -- [verify]
	)
	local nMissing = 0
	local missing = #()
	for b in getClassInstances BitmapTexture do -- [verify]; renderer bitmaps follow below
	(
		if b.filename != undefined and b.filename != "" and not (doesFileExist b.filename) do
		(
			nMissing += 1
			if missing.count < 30 do appendIfUnique missing b.filename
		)
	)
	-- Renderer bitmaps: class and property names [verify]; an uninstalled renderer leaves the class undefined.
	for pair in #(#(VRayBitmap, "HDRIMapName"), #(CoronaBitmap, "filename"), #(ai_image, "filename")) do
	(
		if pair[1] != undefined do
		(
			for b in getClassInstances pair[1] do
			(
				local f = try (getProperty b pair[2]) catch undefined
				if f != undefined and f != "" and not (doesFileExist f) do
				(
					nMissing += 1
					if missing.count < 30 do appendIfUnique missing f
				)
			)
		)
	)
	local nScale = 0
	for o in geometry do (local s = o.scale; if (abs (s.x - 1.0) > 1e-4) or (abs (s.y - 1.0) > 1e-4) or (abs (s.z - 1.0) > 1e-4) do nScale += 1) -- [verify] node scale
	format "{\"objects\":%, \"non_unit_scale\":%, " nObj nScale to:ss
	format "\"system\":\"% x %\", \"display\":\"%\", " units.SystemType units.SystemScale units.DisplayType to:ss -- [verify] units.DisplayType
	format "\"default_named\":%, \"far_count\":%, \"far_max_m\":%, \"group_heads\":%, \"group_max_depth\":%, " nDefault nFar (farMax / 100.0) nHeads maxDepth to:ss
	format "\"layers\":%, \"on_layer_0\":%, \"xref_scenes\":%, \"missing_bitmaps\":%, " LayerManager.count onLayer0 (xrefs.getXRefFileCount()) nMissing to:ss -- [verify] LayerManager, xrefs
	format "\"far_sample\":%, \"missing_sample\":%}" (farList as string) (missing as string) to:ss
	ss as string
)
