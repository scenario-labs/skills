-- channel: mcp-safe | bridge | handoff | batch
-- status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-bitmap-values-2027.md
-- Read-only look-dev audit: material classes, texture color spaces, file tags, debug red.
-- No dotNet, no file writes, no INI: the result is the returned string (Safe Scene Script Execution).

(
	local out = stringStream ""
	local dataWords = #("rough", "gloss", "metal", "normal", "nrm", "height", "disp", "bump", "ao", "occlusion", "opacity", "mask", "alpha", "orm")
	fn roleOf f dataWords = (
		local toks = filterString (toLower (getFilenameFile f)) "_-. "
		local r = undefined
		for i = toks.count to 1 by -1 while r == undefined do (
			for w in dataWords while r == undefined do (
				if (findString toks[i] w) == 1 do r = #data
			)
		)
		r
	)
	-- 1. class counts
	local counts = #()
	local names = #()
	for m in sceneMaterials do ( -- [verify] sceneMaterials
		local c = (classOf m) as string
		local k = findItem names c
		if k == 0 then (append names c; append counts 1) else counts[k] += 1
	)
	format "CLASSES\n" to:out
	for i = 1 to names.count do format "%\t%\n" names[i] counts[i] to:out
	-- 2. Bitmaptexture color spaces (properties are read-only, documented since 2024)
	format "TEXTURES\n" to:out
	for t in getClassInstances Bitmaptexture do ( -- [verify] getClassInstances
		local f = t.filename
		if f == undefined or not (doesFileExist f) then (
			format "ERROR missing_map\t%\t%\n" t.name f to:out
		) else (
			local b = t.bitmap -- [verify] Bitmaptexture .bitmap
			local cs = if b != undefined then b.colorSpace else "unreadable"
			local src = if b != undefined then b.colorSpaceSource else #notSet
			local st = if b != undefined then b.colorSpaceStatus else #notSet
			local isRaw = (findString (toLower (cs as string)) "raw") != undefined or (findString (toLower (cs as string)) "data") != undefined
			local role = roleOf f dataWords
			local flag = "ok"
			if role == #data and not isRaw do flag = "ERROR data_map_as_color"
			if st == #forcedDefault or st == #invalid do flag = "ERROR colorspace_failed"
			format "%\t%\t%\t%\t%\n" flag (filenameFromPath f) cs src st to:out
		)
	)
	-- 3. debug red left in a shipped scene
	format "DEBUG_RED\n" to:out
	for m in sceneMaterials do (
		for p in getPropNames m do ( -- [verify] getPropNames
			local v = try (getProperty m p) catch undefined
			if classOf v == Color and v.r == 255 and v.g == 0 and v.b == 0 do format "ERROR debug_red_left\t%\t%\n" m.name p to:out
		)
	)
	out as string
)
