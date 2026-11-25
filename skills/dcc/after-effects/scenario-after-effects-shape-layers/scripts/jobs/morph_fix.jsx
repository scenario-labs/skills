// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, l = AEK.core.layer(AEK.core.comp(ARGS.comp), ARGS.layer);
var p = S.contents(l, [ARGS.group]).property(ARGS.path).property("ADBE Vector Shape");
var a = p.keyValue(1), b = p.keyValue(2), report = { countA: a.vertices.length, countB: b.vertices.length };
var n = Math.max(a.vertices.length, b.vertices.length);
if (a.vertices.length < n) { p.setValueAtKey(1, S.resample(a, n)); }      // straight segments only
if (b.vertices.length < n) { p.setValueAtKey(2, S.resample(b, n)); }
if (ARGS.firstVertex) { p.setValueAtKey(2, S.firstVertex(p.keyValue(2), ARGS.firstVertex)); }
if (ARGS.reverse) { p.setValueAtKey(2, S.reverse(p.keyValue(2))); }
report.mid = p.valueAtTime((p.keyTime(1) + p.keyTime(2)) / 2, false).vertices.length;
return report;
