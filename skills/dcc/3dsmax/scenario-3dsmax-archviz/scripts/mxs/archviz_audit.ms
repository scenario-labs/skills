-- channel: mcp-safe | bridge | batch | handoff (pass through max_wrap.wrap(code, lang="maxscript"); the chunk sets result)
-- checked against archviz digests 1 to 4 and scripting-pipeline__safe-scene-script-execution-2027.md
-- Read-only audit: units, cameras, lights per class, scatter and proxy objects, animation and output settings.
-- No dotNet, no file writes, no INI, no UIAccessor: stays inside the Safe Scene Script Execution rules.

(
	local ss = stringStream ""
	local scatterClasses = #("Forest_Pro", "Forest_Lite", "RailClone_Pro", "RailClone_Lite", "ChaosScatter", "VRayProxy", "CProxy") -- [verify] all but VRayProxy
	local camKeys = #("focal_length_mm", "film_width_mm", "auto_vertical_tilt_correction", "fov", "use_dof", "f_number") -- [verify] all

	format "units: % scale %\n" units.SystemType units.SystemScale to:ss -- [verify] SystemScale
	format "renderer: % size: %x% fps: % range: %\n" (classOf renderers.current) renderWidth renderHeight frameRate animationRange to:ss
	format "rendTimeType: % rendSaveFile: % output: %\n" rendTimeType rendSaveFile rendOutputFilename to:ss

	for c in cameras where superClassOf c == camera do
	(
		format "camera: % class: % z: %" c.name (classOf c) c.pos.z to:ss
		local names = for n in (getPropNames c) collect (n as string) -- [verify] getPropNames
		for k in camKeys where (findItem names k) > 0 do
			format " %=%" k (getProperty c (k as name)) to:ss -- [verify] getProperty
		format "\n" to:ss
	)

	-- lights per class: many unique lights after a Revit FBX link is a performance flag (file-link-revit-fbx-settings doc)
	local lightNames = #()
	local lightCounts = #()
	for l in lights where superClassOf l == light do -- [verify] light superclass filter (the collection also holds targets)
	(
		local lcn = (classOf l) as string
		local i = findItem lightNames lcn
		if i == 0 then (append lightNames lcn; append lightCounts 1) else lightCounts[i] += 1
	)
	for i = 1 to lightNames.count do format "lights: % x %\n" lightNames[i] lightCounts[i] to:ss

	for o in objects do
	(
		local cn = (classOf o) as string
		if (findItem scatterClasses cn) > 0 do
			format "scatter: % class: % layer: % hidden: %\n" o.name cn o.layer.name o.isHidden to:ss
	)

	result = ss as string
)
