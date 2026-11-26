// channel: bridge | handoff
// checked: live 27.0
// ARGS: {svg} and/or {ai, comp}: absolute paths; each part runs only when its file is given
function imp(path, as) {
  var io = new ImportOptions(new File(path)); if (as) { io.importAs = as; }
  app.beginSuppressDialogs(); try { return app.project.importFile(io); } finally { app.endSuppressDialogs(false); }
}
var R = {}, seen = {}, bad = [], i, c = null, it;
// every input is checked before the first import, so a bad request leaves the project untouched
if (!ARGS.svg && !ARGS.ai) { throw new Error("vector_intake: give ARGS.svg, ARGS.ai (with ARGS.comp), or both"); }
if (ARGS.svg && !new File(ARGS.svg).exists) { bad.push("SVG not found: " + ARGS.svg); }
if (ARGS.ai && !new File(ARGS.ai).exists) { bad.push("Illustrator file not found: " + ARGS.ai); }
if (ARGS.ai) { try { c = AEK.core.comp(ARGS.comp); } catch (e) { bad.push(e.message); } }
if (bad.length) { throw new Error(bad.join("; ")); }
if (ARGS.svg) {
  // SVG as native shape layers: COMP_CROPPED_LAYERS is the only comp mode it accepts, and importFile returns null.
  // Project items are not in creation order: compare ids to find the new comp.
  for (i = 1; i <= app.project.numItems; i++) { seen[app.project.item(i).id] = true; }
  imp(ARGS.svg, ImportAsType.COMP_CROPPED_LAYERS);
  R.svgComp = null;
  for (i = 1; i <= app.project.numItems; i++) {
    it = app.project.item(i);
    if (!seen[it.id] && it instanceof CompItem) { R.svgComp = it.name; R.svgLayer = it.numLayers ? it.layer(1).matchName : ""; }
  }
}
if (ARGS.ai) {
  // Illustrator file as footage, then try Create Shapes from Vector Layer on that one selected layer
  var foot = imp(ARGS.ai, ImportAsType.FOOTAGE), src = c.layers.add(foot);
  for (i = 1; i <= app.project.numItems; i++) { app.project.item(i).selected = false; }
  var n0 = c.numLayers, v = c.openInViewer();
  if (v) { v.setActive(); }
  for (i = 1; i <= c.numLayers; i++) { c.layer(i).selected = false; }
  src.selected = true;
  app.executeCommand(app.findMenuCommandId("Create Shapes from Vector Layer"));   // id 3973 in 27.0: no dialog, but often no effect
  R.converted = c.numLayers > n0;
  if (!R.converted) { R.next = "GUI step: select '" + src.name + "' in comp '" + c.name + "', Layer > Create > Create Shapes from Vector Layer"; }
  else { R.newLayer = c.layer(src.index - 1).name; R.srcEnabled = src.enabled; R.order = AEX.shapes.order(c.layer(src.index - 1)); }
}
return R;
