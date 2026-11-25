// aekit/stats.jsx: counts before and after a change. Requires core.jsx.
var AEK = AEK || {};
AEK.stats = (function () {
    function compStats(c) {
        var s = { name: c.name, id: c.id, width: c.width, height: c.height, fps: c.frameRate, duration: c.duration,
            layers: c.numLayers, keys: 0, expressions: 0, effects: 0, threeD: 0, text: 0, shape: 0, precomp: 0, footage: 0,
            motionBlur: c.motionBlur, renderer: c.renderer }, i, l;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (l.threeDLayer) { s.threeD++; }
            if (l.matchName === "ADBE Text Layer") { s.text++; }
            if (l.matchName === "ADBE Vector Layer") { s.shape++; }
            if (l.source instanceof CompItem) { s.precomp++; }
            if (l.source instanceof FootageItem) { s.footage++; }
            try { s.effects += l.property("ADBE Effect Parade").numProperties; } catch (e) {}
            AEK.core.walk(l, function (p) {
                if (p.propertyType !== PropertyType.PROPERTY) { return; }
                try { s.keys += p.numKeys; } catch (e1) {}
                try { if (p.canSetExpression && p.expression !== "") { s.expressions++; } } catch (e2) {}
            });
        }
        return s;
    }
    function snapshot() {
        var s = { items: app.project.numItems, comps: 0, footage: 0, folders: 0, missingFootage: 0, solids: 0,
            layers: 0, keys: 0, expressions: 0, effects: 0, renderQueue: app.project.renderQueue.numItems, perComp: {} }, i, it, cs;
        for (i = 1; i <= app.project.numItems; i++) {
            it = app.project.item(i);
            if (it instanceof CompItem) {
                s.comps++; cs = compStats(it); s.perComp[it.name] = cs;
                s.layers += cs.layers; s.keys += cs.keys; s.expressions += cs.expressions; s.effects += cs.effects;
            } else if (it instanceof FootageItem) {
                s.footage++;
                if (it.footageMissing) { s.missingFootage++; }
                if (it.mainSource instanceof SolidSource) { s.solids++; }
            } else if (it instanceof FolderItem) { s.folders++; }
        }
        return s;
    }
    function diff(a, b) {
        var d = {}, k, keys = ["items", "comps", "footage", "folders", "missingFootage", "solids", "layers", "keys", "expressions", "effects", "renderQueue"], i;
        for (i = 0; i < keys.length; i++) { k = keys[i]; if (a[k] !== b[k]) { d[k] = [a[k], b[k]]; } }
        d.compsAdded = []; d.compsRemoved = [];
        for (k in b.perComp) { if (b.perComp.hasOwnProperty(k) && !a.perComp[k]) { d.compsAdded.push(k); } }
        for (k in a.perComp) { if (a.perComp.hasOwnProperty(k) && !b.perComp[k]) { d.compsRemoved.push(k); } }
        return d;
    }
    return { comp: compStats, snapshot: snapshot, diff: diff };
})();
