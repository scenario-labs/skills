// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, c = AEK.core.comp(ARGS.comp), N = ARGS.copies || 12;
var l = c.layers.addShape(); l.name = "burst";
l.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
var gp = S.group(l, [], "spoke");
S.path(l, gp, [[0, -50], [0, -170]], null, null, false);             // one spoke, pointing out from the center
S.add(l, gp, "ADBE Vector Filter - Trim", "chase");
S.add(l, gp, "ADBE Vector Filter - Repeater", "ring").property("ADBE Vector Repeater Copies").setValue(N);
S.contents(l, gp).property("ring").property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Rotation").setValue(360 / N);
S.stroke(l, gp, { color: [0.95, 0.35, 0.1, 1], width: 10, cap: "round" });
var e = S.contents(l, gp).property("chase").property("ADBE Vector Trim End");
AEK.motion.bezier(e, AEK.motion.key(e, 0, 0), AEK.motion.key(e, AEK.core.time(c, 8), 100), [0.2, 0.8, 0.2, 1]);
var s = S.contents(l, gp).property("chase").property("ADBE Vector Trim Start");
AEK.motion.bezier(s, AEK.motion.key(s, AEK.core.time(c, 4), 0), AEK.motion.key(s, AEK.core.time(c, 14), 100), [0.5, 0, 0.3, 1]);
return AEX.shapes.order(l);
