// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var before = AEX.shapes.lottie(c);
var dup = c.duplicate(); dup.name = c.name + "_lottie";          // never fix the master
for (var i = 1; i <= dup.numLayers; i++) {
  AEK.core.walk(dup.layer(i), function (p) {
    if (p.propertyType === PropertyType.PROPERTY && p.canSetExpression && p.expression && p.expressionEnabled) { AEK.expr.bake(p, dup, 0, dup.duration); }
  });
}
return { before: before, after: AEX.shapes.lottie(dup) };
