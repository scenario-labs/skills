// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var before = AEX.shapes.lottie(c);
// never fix a master: the comp and every comp nested in it get an export copy, rewired to the other copies
var copies = {}, made = [], id, k;
function exportCopy(src) {
  if (copies[src.id]) { return copies[src.id]; }
  var d = src.duplicate(), i, s;
  d.name = src.name + "_lottie"; copies[src.id] = d; made.push(d.name);
  for (i = 1; i <= d.numLayers; i++) {
    s = null; try { s = d.layer(i).source; } catch (e) {}
    if (s instanceof CompItem) { d.layer(i).replaceSource(exportCopy(s), false); }
  }
  return d;
}
var dup = exportCopy(c);
for (id in copies) {
  if (!copies.hasOwnProperty(id)) { continue; }
  for (k = 1; k <= copies[id].numLayers; k++) {
    AEK.core.walk(copies[id].layer(k), function (p) {
      if (p.propertyType === PropertyType.PROPERTY && p.canSetExpression && p.expression && p.expressionEnabled) { AEK.expr.bake(p, copies[id], 0, copies[id].duration); }
    });
  }
}
return { before: before, after: AEX.shapes.lottie(dup), copies: made };
