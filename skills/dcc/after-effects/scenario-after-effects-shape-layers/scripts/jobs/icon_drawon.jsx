// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, c = AEK.core.comp(ARGS.comp);
var l = c.layers.addShape(); l.name = ARGS.name || "icon_home";
l.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
var U = (ARGS.size || 160) / 24; // 24-unit icon grid
function pts(a) { var o = [], i; for (i = 0; i < a.length; i++) { o.push([a[i][0] * U, a[i][1] * U]); } return o; }
var parts = [{ name: "roof", v: [[-10, -1], [0, -9], [10, -1]] }, { name: "walls", v: [[-7, -3], [-7, 9], [7, 9], [7, -3]] }, { name: "door", v: [[-2, 9], [-2, 3], [2, 3], [2, 9]] }];
var STAGGER = 3, DRAW = 12; // frames
for (var i = 0; i < parts.length; i++) {
  var gp = S.group(l, [], parts[i].name);
  S.path(l, gp, pts(parts[i].v), null, null, false);
  S.add(l, gp, "ADBE Vector Filter - Trim", "draw");     // operator after the path, before the paint
  S.stroke(l, gp, { color: [0.08, 0.08, 0.1, 1], width: 2, cap: "round", join: "round" });
  var end = S.contents(l, gp).property("draw").property("ADBE Vector Trim End");
  var f0 = i * STAGGER, k1 = AEK.motion.key(end, AEK.core.time(c, f0), 0), k2 = AEK.motion.key(end, AEK.core.time(c, f0 + DRAW), 100);
  AEK.motion.bezier(end, k1, k2, [0.2, 0, 0, 1]);
}
return { order: AEX.shapes.order(l), walls: AEK.motion.sample(S.contents(l, ["walls"]).property("draw").property("ADBE Vector Trim End"), c, 0, AEK.core.time(c, 20)) };
