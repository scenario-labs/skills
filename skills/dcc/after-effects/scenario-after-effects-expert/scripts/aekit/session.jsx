// aekit/session.jsx: working inside a project someone else has open. Requires core.jsx.
var AEK = AEK || {};
AEK.session = (function () {
    function rqStatus(s) {
        var names = ["WILL_CONTINUE", "NEEDS_OUTPUT", "UNQUEUED", "QUEUED", "RENDERING", "USER_STOPPED", "ERR_STOPPED", "DONE"], i;
        for (i = 0; i < names.length; i++) { if (s === RQItemStatus[names[i]]) { return names[i]; } }
        return String(s);
    }
    // state(): what the person is looking at and what they queued. Take it before any change, give it to restore() last.
    function state() {
        var p = app.project, a = p.activeItem, s, i, rq = p.renderQueue, it;
        s = { project: p.file ? p.file.fsName : "", dirty: p.dirty, items: p.numItems, activeId: a ? a.id : null, activeName: a ? a.name : "",
            time: null, workArea: null, selected: [], queue: [] };
        if (a instanceof CompItem) {
            s.time = a.time; s.workArea = [a.workAreaStart, a.workAreaDuration];
            for (i = 0; i < a.selectedLayers.length; i++) { s.selected.push(a.selectedLayers[i].index); }
        }
        for (i = 1; i <= rq.numItems; i++) {
            it = rq.item(i);
            s.queue.push({ index: i, comp: it.comp.name, status: rqStatus(it.status), render: it.render });
        }
        return s;
    }
    // restore(state): current time, work area, layer selection and the render flags of the queue. Layer indices
    // are the ones recorded by state(): call it only when the job did not reorder layers in the active comp.
    function restore(s) {
        var p = app.project, a = s.activeId ? p.itemByID(s.activeId) : null, i, rq = p.renderQueue, done = [];
        if (a instanceof CompItem) {
            if (s.time !== null && a.time !== s.time) { a.time = s.time; done.push("time"); }
            if (s.workArea && (a.workAreaStart !== s.workArea[0] || a.workAreaDuration !== s.workArea[1])) {
                a.workAreaStart = s.workArea[0]; a.workAreaDuration = s.workArea[1]; done.push("workArea");
            }
            for (i = 1; i <= a.numLayers; i++) { if (a.layer(i).selected) { a.layer(i).selected = false; } }
            for (i = 0; i < s.selected.length; i++) { if (s.selected[i] <= a.numLayers) { a.layer(s.selected[i]).selected = true; } }
            done.push("selection");
        }
        for (i = 0; i < s.queue.length && i < rq.numItems; i++) {
            // render can only be set on items that are queued or unqueued, never on finished ones
            try { if (rq.item(i + 1).render !== s.queue[i].render) { rq.item(i + 1).render = s.queue[i].render; done.push("queue " + (i + 1)); } } catch (e) {}
        }
        return done;
    }
    // print(layer): what must survive a change. Compare two prints with changed().
    function print(l) {
        var f = { index: l.index, name: l.name, enabled: l.enabled, inPoint: l.inPoint, outPoint: l.outPoint, startTime: l.startTime,
            stretch: l.stretch, parent: l.parent ? l.parent.name : "", threeD: !!l.threeDLayer, effects: [], masks: 0, keys: 0, expressions: 0,
            matte: "", source: "", sourceId: null, width: null, height: null }, fx, i;
        try { if (l.source) { f.source = l.source.name; f.sourceId = l.source.id; f.width = l.source.width; f.height = l.source.height; } } catch (e0) {}
        try { fx = l.property("ADBE Effect Parade"); for (i = 1; i <= fx.numProperties; i++) { f.effects.push(fx.property(i).matchName); } } catch (e1) {}
        try { f.masks = l.property("ADBE Mask Parade").numProperties; } catch (e2) {}
        try { if (l.hasTrackMatte && l.trackMatteLayer) { f.matte = l.trackMatteLayer.name; } } catch (e3) {}
        AEK.core.walk(l, function (p) {
            if (p.propertyType !== PropertyType.PROPERTY) { return; }
            try { f.keys += p.numKeys; } catch (e4) {}
            try { if (p.canSetExpression && p.expression !== "") { f.expressions++; } } catch (e5) {}
        });
        return f;
    }
    // changed(a, b, ignore): names of the fields that differ. ignore defaults to the fields a source swap is meant to change.
    function changed(a, b, ignore) {
        var out = [], k, skip = {}, i;
        ignore = ignore || ["source", "sourceId", "width", "height"];
        for (i = 0; i < ignore.length; i++) { skip[ignore[i]] = true; }
        for (k in a) {
            if (!a.hasOwnProperty(k) || skip[k]) { continue; }
            if (k === "effects") { if (a.effects.join("|") !== b.effects.join("|")) { out.push(k); } }
            else if (typeof a[k] === "number" && typeof b[k] === "number") { if (Math.abs(a[k] - b[k]) > 0.0005) { out.push(k + " " + a[k] + " -> " + b[k]); } }
            else if (a[k] !== b[k]) { out.push(k + " " + a[k] + " -> " + b[k]); }
        }
        return out;
    }
    // named(prefix): every layer whose name starts with prefix, in every comp
    function named(prefix) {
        var all = AEK.core.comps(), out = [], i, j, l;
        for (i = 0; i < all.length; i++) {
            for (j = 1; j <= all[i].numLayers; j++) {
                l = all[i].layer(j);
                if (l.name.indexOf(prefix) === 0) { out.push({ comp: all[i].name, compId: all[i].id, index: j, name: l.name, locked: l.locked }); }
            }
        }
        return out;
    }
    // matchFiles(names, folder, extensions): {name: absolute path | null}; compares without case and without extension
    function matchFiles(names, folder, exts) {
        var dir = new Folder(folder), files, map = {}, res = {}, i, f, base, dot;
        if (!dir.exists) { throw new Error("Folder not found: " + folder); }
        exts = exts || ["mov", "mp4", "mxf", "png", "jpg", "jpeg", "exr", "tif", "tiff", "psd", "ai", "webp", "wav", "mp3", "glb", "gltf", "obj", "fbx"];
        files = dir.getFiles();
        for (i = 0; i < files.length; i++) {
            f = files[i];
            if (!(f instanceof File)) { continue; }
            base = decodeURI(f.name); dot = base.lastIndexOf(".");
            if (dot < 1 || (" " + exts.join(" ") + " ").indexOf(" " + base.substring(dot + 1).toLowerCase() + " ") < 0) { continue; }
            base = base.substring(0, dot).toLowerCase();
            if (map[base]) { map[base].push(f.fsName); } else { map[base] = [f.fsName]; }
        }
        for (i = 0; i < names.length; i++) { res[names[i]] = map[names[i].toLowerCase()] || null; }
        return res;
    }
    // swap(layer, item, opts): put item behind a placeholder layer and keep everything on the layer.
    // Same size and long enough: the source is replaced directly. Otherwise the item goes into a fit comp of the
    // placeholder's size and length, so the layer's transform, keys, effects, masks and out point keep their meaning
    // (replaceSource with a shorter clip pulls the out point in). opts: {fit: "cover"|"contain", bin}
    function swap(l, it, opts) {
        opts = opts || {};
        // k maps layer time to source time: a layer at 50 % stretch plays 10 s of comp time from 20 s of source
        var c = l.containingComp, before = print(l), wasLocked = l.locked, pw = before.width, ph = before.height, res, fitComp, inner, s,
            k = Math.abs(l.stretch) ? 100 / Math.abs(l.stretch) : 1,
            span = (l.outPoint - l.inPoint) * k, offset = Math.max(0, l.inPoint - l.startTime) * k, srcEnd = (l.outPoint - l.startTime) * k,
            named = l.name, clipDur;
        if (!pw || !ph) { throw new Error("Layer '" + l.name + "' has no source size: not a placeholder that can be swapped"); }
        if (wasLocked) { l.locked = false; }
        res = { layer: named, comp: c.name, item: it.name, mode: "direct", fitComp: "", scale: 100, shortByFrames: 0 };
        clipDur = (it.mainSource && it.mainSource.isStill) ? span : it.duration;
        if (it.width === pw && it.height === ph && offset === 0 && clipDur + 0.0005 >= srcEnd) {
            l.replaceSource(it, false);
        } else {
            fitComp = app.project.items.addComp("FIT_" + named + "_" + c.name, pw, ph, 1, Math.max(c.frameDuration, srcEnd), c.frameRate);
            if (opts.bin) { fitComp.parentFolder = (typeof opts.bin === "string") ? AEK.core.bin(opts.bin) : opts.bin; }
            inner = fitComp.layers.add(it);
            inner.startTime = offset;
            s = (opts.fit === "contain") ? Math.min(pw / it.width, ph / it.height) : Math.max(pw / it.width, ph / it.height);
            inner.property("ADBE Transform Group").property("ADBE Scale").setValue([s * 100, s * 100]);
            l.replaceSource(fitComp, false);
            res.mode = "fitComp"; res.fitComp = fitComp.name; res.scale = Math.round(s * 10000) / 100;
        }
        l.name = named;
        if (Math.abs(l.inPoint - before.inPoint) > 0.0005 || Math.abs(l.outPoint - before.outPoint) > 0.0005) {
            l.inPoint = before.inPoint; l.outPoint = before.outPoint;
        }
        if (clipDur + 0.0005 < span) { res.shortByFrames = Math.round((span - clipDur) / k * c.frameRate); }
        if (wasLocked) { l.locked = true; }
        res.changed = changed(before, print(l));
        res.upscaled = res.scale > 105;
        return res;
    }
    // fontRuns(textDocument): fonts used along the text, in order, e.g. ["Inter-Bold", "Inter-Regular"]
    function fontRuns(td) {
        var runs = [], i, f, n = td.text.length;
        try {
            for (i = 0; i < n; i++) { f = td.characterRange(i, i + 1).font; if (!runs.length || runs[runs.length - 1] !== f) { runs.push(f); } }
        } catch (e) { runs = [td.font]; }
        return runs;
    }
    // setFont(postScriptName, opts): every text layer, every Source Text key. opts: {comps: [CompItem], map: {oldPs: newPs}}
    // With map, each run keeps its own weight (bold stays bold). Returns the width change per layer.
    function setFont(ps, opts) {
        opts = opts || {};
        var all = opts.comps || AEK.core.comps(), out = [], i, j, l, st, k, td, runs, r0, r1, row, wasLocked;
        // a reopened project can keep a stand-in object under a missing font's name: isSubstitute tells it apart
        function exists(name) { var f = app.fonts.getFontsByPostScriptName(name); return !!(f && f.length) && f[0].isSubstitute !== true; }
        function target(old) { return (opts.map && opts.map[old]) ? opts.map[old] : ps; }
        function apply(td) {
            var n = td.text.length, a = 0, b, f;
            if (!opts.map) { td.font = ps; return td; }
            while (a < n) {
                f = td.characterRange(a, a + 1).font; b = a + 1;
                while (b < n && td.characterRange(b, b + 1).font === f) { b++; }
                td.characterRange(a, b).font = target(f);
                a = b;
            }
            return td;
        }
        if (!exists(ps)) { throw new Error("Font not installed: " + ps); }
        if (opts.map) { for (k in opts.map) { if (opts.map.hasOwnProperty(k) && !exists(opts.map[k])) { throw new Error("Font not installed: " + opts.map[k]); } } }
        for (i = 0; i < all.length; i++) {
            for (j = 1; j <= all[i].numLayers; j++) {
                l = all[i].layer(j);
                if (l.matchName !== "ADBE Text Layer") { continue; }
                st = l.property("ADBE Text Properties").property("ADBE Text Document");
                td = st.value; runs = fontRuns(td);
                r0 = l.sourceRectAtTime(l.inPoint, false);
                row = { comp: all[i].name, layer: l.name, index: j, from: runs, keys: st.numKeys, expression: st.expression !== "", widthBefore: Math.round(r0.width) };
                wasLocked = l.locked; if (wasLocked) { l.locked = false; }
                if (st.numKeys === 0) { st.setValue(apply(td)); }
                else { for (k = 1; k <= st.numKeys; k++) { st.setValueAtKey(k, apply(st.keyValue(k))); } }
                if (wasLocked) { l.locked = true; }
                r1 = l.sourceRectAtTime(l.inPoint, false);
                row.to = fontRuns(st.value); row.widthAfter = Math.round(r1.width);
                row.growthPct = r0.width ? Math.round((r1.width / r0.width - 1) * 1000) / 10 : 0;
                out.push(row);
            }
        }
        return out;
    }
    return { state: state, restore: restore, print: print, changed: changed, named: named, matchFiles: matchFiles, swap: swap, fontRuns: fontRuns, setFont: setFont };
})();
