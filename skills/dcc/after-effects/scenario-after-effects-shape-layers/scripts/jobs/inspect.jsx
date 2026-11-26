// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = AEK.core.layer(c, ARGS.layer);
return { order: AEX.shapes.order(l), tree: AEX.shapes.dump(l) };
