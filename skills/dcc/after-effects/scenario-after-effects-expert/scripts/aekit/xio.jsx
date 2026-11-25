// aekit/xio.jsx: bring files in and say what arrived. Requires core.jsx. All paths absolute.
var AEK = AEK || {};
AEK.xio = (function () {
    function describe(it) {
        var d = { name: it.name, id: it.id, type: it.typeName }, s;
        try { d.width = it.width; d.height = it.height; d.duration = it.duration; d.fps = it.frameRate; d.hasVideo = it.hasVideo; d.hasAudio = it.hasAudio; } catch (e) {}
        try {
            s = it.mainSource;
            d.file = it.file ? it.file.fsName : "";
            d.isStill = s.isStill; d.hasAlpha = s.hasAlpha; d.alphaMode = s.alphaMode === AlphaMode.STRAIGHT ? "straight" : (s.alphaMode === AlphaMode.PREMULTIPLIED ? "premultiplied" : "ignore");
            d.nativeFps = s.nativeFrameRate; d.conformFps = s.conformFrameRate; d.fields = s.fieldSeparationType === FieldSeparationType.OFF ? "off" : (s.fieldSeparationType === FieldSeparationType.UPPER_FIELD_FIRST ? "upper" : "lower");
            d.missing = it.footageMissing;
        } catch (e1) {}
        return d;
    }
    // importFile(path, opts): opts {sequence, fps, alpha: "straight"|"premultiplied"|"ignore", bin, name}
    function importFile(path, opts) {
        opts = opts || {};
        var f = AEK.core.abs(path), io, it;
        if (!f.exists) { throw new Error("File not found: " + path); }
        io = new ImportOptions(f);
        if (opts.sequence) { io.sequence = true; io.forceAlphabetical = true; }
        it = app.project.importFile(io);
        if (opts.fps && it.mainSource && !it.mainSource.isStill) { it.mainSource.conformFrameRate = opts.fps; }
        if (opts.alpha && it.mainSource && it.mainSource.hasAlpha) {
            if (opts.alpha === "straight") { it.mainSource.alphaMode = AlphaMode.STRAIGHT; }
            else if (opts.alpha === "premultiplied") { it.mainSource.alphaMode = AlphaMode.PREMULTIPLIED; }
            else if (opts.alpha === "ignore") { it.mainSource.alphaMode = AlphaMode.IGNORE; }
        }
        if (opts.bin) { it.parentFolder = (typeof opts.bin === "string") ? AEK.core.bin(opts.bin) : opts.bin; }
        if (opts.name) { it.name = opts.name; }
        return describe(it);
    }
    // importItem(path, opts): same as importFile, returns the project item itself (for layers.add)
    function importItem(path, opts) { return AEK.core.itemById(importFile(path, opts).id); }
    // importMany([{path, ...opts}]): never stops on one bad file; returns {imported: [...], failed: [{path, error}]}
    function importMany(list) {
        var res = { imported: [], failed: [] }, i;
        for (i = 0; i < list.length; i++) {
            try { res.imported.push(importFile(list[i].path, list[i])); }
            catch (e) { res.failed.push({ path: list[i].path, error: e.toString() }); }
        }
        return res;
    }
    // replace(item, path): swaps the file behind a footage item; every layer using it follows
    function replace(it, path) {
        var f = AEK.core.abs(path);
        if (!f.exists) { throw new Error("File not found: " + path); }
        it.replace(f);
        return describe(it);
    }
    // addToComp(comp, item, opts): opts {fit: "contain"|"cover", start, name}
    function addToComp(c, it, opts) {
        opts = opts || {};
        var l = c.layers.add(it), s;
        if (opts.name) { l.name = opts.name; }
        if (opts.start !== undefined) { l.startTime = opts.start; }
        if (opts.fit && it.width && it.height && l.matchName === "ADBE AV Layer") {
            s = (opts.fit === "cover") ? Math.max(c.width / it.width, c.height / it.height) : Math.min(c.width / it.width, c.height / it.height);
            l.property("ADBE Transform Group").property("ADBE Scale").setValue([s * 100, s * 100]);
        }
        return { layer: l.name, index: l.index, matchName: l.matchName, inPoint: l.inPoint, outPoint: l.outPoint };
    }
    return { describe: describe, importFile: importFile, importItem: importItem, importMany: importMany, replace: replace, addToComp: addToComp };
})();
