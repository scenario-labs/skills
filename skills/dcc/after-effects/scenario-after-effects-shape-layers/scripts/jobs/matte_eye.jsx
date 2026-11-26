// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, c = AEK.core.comp(ARGS.comp);
var E = c.layers.addShape(); E.name = "eye"; E.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
var V = [[-150, 0], [0, -90], [150, 0], [0, 90]], IT = [[0, 0], [-90, 0], [0, 0], [90, 0]], OT = [[0, 0], [90, 0], [0, 0], [-90, 0]];
var dg = S.group(E, [], "stripes");                      // first group draws on top
S.path(E, dg, V, null, null, true, "mask");
var eg = S.group(E, [], "eye white");
S.path(E, eg, V, IT, OT, true, "main");
S.fill(E, eg, [0.9, 0.9, 0.95, 1]);
AEK.expr.set(S.contents(E, ["stripes"]).property("mask").property("ADBE Vector Shape"), 'content("eye white").content("main").path', [0]);
var sg = S.group(E, ["stripes"], "design");
S.set(S.add(E, sg, "ADBE Vector Shape - Rect"), { "ADBE Vector Rect Size": [400, 14], "ADBE Vector Rect Position": [0, -80] });
S.add(E, sg, "ADBE Vector Filter - Repeater", "rows").property("ADBE Vector Repeater Copies").setValue(7);
S.contents(E, sg).property("rows").property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Position").setValue([0, 28]);
S.set(S.add(E, sg, "ADBE Vector Filter - Merge", "add"), { "ADBE Vector Merge Type": 2 });   // Add: the copies become one area before the clip
S.set(S.add(E, ["stripes"], "ADBE Vector Filter - Merge", "clip"), { "ADBE Vector Merge Type": 4 });
S.fill(E, ["stripes"], [0.95, 0.35, 0.1, 1]);
return AEX.shapes.order(E);
