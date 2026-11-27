-- maxkit_modeling.ms: MAXScript twin of maxkit_modeling.py for the mcp-safe channel.
-- channel: mcp-safe | bridge | handoff
-- checked against scripting-pipeline__safe-scene-script-execution-2027.md and api-names.txt
-- Uses no dotNet, macroScript, UIAccessor, setINISetting or file delete/copy.
-- Names marked [verify] are not in the saved docs.

struct mmModeling
(
	fn kindOf m =
	(
		local c = toLower ((classOf m) as string)
		local table = #(#("creaseset","crease"), #("crease","crease"), #("opensubdiv","subdiv"), #("turbosmooth","subdiv"), \
			#("ffd","ffd"), #("smartbevel","smartbevel"), #("boolean","boolean"), #("chamfer","chamfer"), \
			#("poly_select","polyselect"), #("polyselect","polyselect"), #("retopology","retopo"), #("conform","conform"), \
			#("symmetry","symmetry"), #("slice","slice"), #("subdivide","subdivide"))
		local k = c
		for t in table while k == c do if findString c t[1] != undefined do k = t[2]
		k
	),

	-- bottom to top array of #(kind, name, modifier)
	fn stackOf node =
	(
		local out = #()
		for i = node.modifiers.count to 1 by -1 do
		(
			local m = node.modifiers[i]
			append out #(kindOf m, m.name, m)
		)
		out
	),

	fn stackAudit node =
	(
		local s = stackOf node
		local kinds = for e in s collect e[1]
		local f = #()
		local sub = findItem kinds "subdiv"
		for i = 1 to s.count do
		(
			if s[i][1] == "crease" and sub > 0 and i > sub do
				append f #("error", "crease-below-subdiv", s[i][2] + " above the subdivision modifier")
			if s[i][1] == "ffd" and sub > 0 and i > sub do
				append f #("warn", "ffd-before-smooth", s[i][2] + " above the smoothing modifier")
			if i > 1 and s[i][1] == "chamfer" and s[i-1][1] == "boolean" do
				append f #("info", "chamfer-after-boolean", "consider Smart Bevel above the Boolean (2027)")
		)
		local lastChamfer = 0
		for i = 1 to kinds.count do
		(
			case kinds[i] of
			(
				"chamfer": lastChamfer = i
				"polyselect": lastChamfer = 0
				"boolean": if lastChamfer > 0 do (append f #("warn", "selection-not-cleared", "insert an empty Poly Select before the next Boolean"); lastChamfer = 0)
			)
		)
		f
	),

	-- counts on a temporary copy; the user's node is not touched
	fn meshChecks node weldTol:0.001 =
	(
		local tmp = copy node
		convertToPoly tmp -- [verify]
		local nf = polyop.getNumFaces tmp -- [verify]
		local tris = 0, quads = 0, ngons = 0
		for i = 1 to nf do
		(
			local d = polyop.getFaceDeg tmp i -- [verify]
			if d == 3 then tris += 1 else if d == 4 then quads += 1 else ngons += 1
		)
		local openE = (polyop.getOpenEdges tmp).numberSet -- [verify]
		local nv = polyop.getNumVerts tmp -- [verify]
		tmp.weldThreshold = weldTol -- [verify] weldVertsByThreshold reads this property
		polyop.weldVertsByThreshold tmp #{1..nv} -- [verify]
		local weldable = nv - (polyop.getNumVerts tmp)
		delete tmp
		#(node.name, nf, nv, tris, quads, ngons, openE, weldable)
	)
)
mm = mmModeling()
