// channel: bridge | handoff
// checked: live 27.0
function imp(path, as) {
  var io = new ImportOptions(new File(path)); if (as) { io.importAs = as; }
  app.beginSuppressDialogs(); try { return app.project.importFile(io); } finally { app.endSuppressDialogs(false); }
}
var R = {}, seen = {}, i;
// SVG as native shape layers: COMP_CROPPED_LAYERS is the only comp mode it accepts, and importFile returns null.
// Project items are not in creation order: compare ids to find the new comp.
for (i = 1; i <= app.project.numItems; i++) { seen[app.project.item(i).id] = true; }
imp(ARGS.svg, ImportAsType.COMP_CROPPED_LAYERS);
for (i = 1; i <= app.project.numItems; i++) { if (!seen[app.project.item(i).id] && app.project.item(i) instanceof CompItem) { R.svgComp = app.project.item(i).name; R.svgLayer = app.project.item(i).layer(1).matchName; } }
// Illustrator file as footage, then try Create Shapes from Vector Layer on that one selected layer
var c = AEK.core.comp(ARGS.comp), foot = imp(ARGS.ai, ImportAsType.FOOTAGE), src = c.layers.add(foot);
for (i = 1; i <= app.project.numItems; i++) { app.project.item(i).selected = false; }
var n0 = c.numLayers, v = c.openInViewer();
if (v) { v.setActive(); }
for (i = 1; i <= c.numLayers; i++) { c.layer(i).selected = false; }
src.selected = true;
app.executeCommand(app.findMenuCommandId("Create Shapes from Vector Layer"));   // id 3973 in 27.0: no dialog, but often no effect
R.converted = c.numLayers > n0;
if (!R.converted) { R.next = "GUI step: select '" + src.name + "' in comp '" + c.name + "', Layer > Create > Create Shapes from Vector Layer"; return R; }
R.newLayer = c.layer(src.index - 1).name; R.srcEnabled = src.enabled;
R.order = AEX.shapes.order(c.layer(src.index - 1));
return R;
