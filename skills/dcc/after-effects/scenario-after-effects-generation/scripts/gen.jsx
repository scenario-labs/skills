// gen.jsx: AEX.gen, landing generated media in After Effects 27.0. Requires the AEK kit (core, build, xio, motion, audit).
// Load with: ae.py run job.jsx --lib skills/scenario-after-effects-generation/scripts/gen.jsx
var AEX = AEX || {};
AEX.gen = (function () {
    // note(prov): one provenance string, one field per line. prov {job, asset, model, seed, prompt}
    function note(p) {
        var keys = ["job", "asset", "model", "seed", "prompt"], out = [], i;
        for (i = 0; i < keys.length; i++) { if (p && p[keys[i]] !== undefined && p[keys[i]] !== "") { out.push(keys[i] + "=" + String(p[keys[i]])); } }
        return "scenario " + out.join("\n");
    }
    // land(path, {name, bin, alpha: "straight"|"premultiplied", matte:[r,g,b], fps, prov}): import, interpret, tag. Returns the item.
    function land(path, o) {
        o = o || {};
        var it = AEK.xio.importItem(path, { name: o.name, bin: o.bin || "generated", fps: o.fps, alpha: o.alpha });
        if (o.alpha === "premultiplied" && o.matte && it.mainSource.hasAlpha) { it.mainSource.premulColor = o.matte; }
        if (o.prov) { it.comment = note(o.prov); }
        return it;
    }
    // place(comp, item, {fit: "contain"|"cover", anchorPx:[x, y] in source pixels, at:[x, y], scale, start, name}): add, anchor, size, tag
    function place(c, it, o) {
        o = o || {};
        var l = c.layers.add(it), tg = l.property("ADBE Transform Group"), s;
        if (o.name) { l.name = o.name; }
        if (o.start !== undefined) { l.startTime = o.start; }
        if (o.anchorPx) { tg.property("ADBE Anchor Point").setValue(o.anchorPx); }
        if (o.scale) { s = o.scale; }
        else if (o.fit && it.width && it.height) { s = (o.fit === "cover" ? Math.max(c.width / it.width, c.height / it.height) : Math.min(c.width / it.width, c.height / it.height)) * 100; }
        if (s) { tg.property("ADBE Scale").setValue([s, s]); }
        if (o.at) { tg.property("ADBE Position").setValue(o.at); }
        if (it.comment) { l.comment = it.comment; }
        return l;
    }
    // upscaled(comp): layers the audit flags as enlarged past 105 % of their pixels
    function upscaled(c) {
        var f = AEK.audit.comp(c), out = [], i;
        for (i = 0; i < f.length; i++) { if (f[i].rule === "layer.upscaled") { out.push(f[i].where + ": " + f[i].message); } }
        return out;
    }
    // loopCrossfade(item, overlapFrames, name): a precomp that loops without a jump, (clip - overlap) frames long plus one.
    // The top copy plays the clip tail over the first frames and fades out. The extra last frame equals frame 0,
    // and loopLayer(..., true) skips it, so every frame of the cycle is used once.
    function loopCrossfade(it, ov, name) {
        var fps = it.frameRate, d = it.duration, L = d - ov / fps;
        var c = AEK.build.comp(name || (it.name + " loop"), { width: it.width, height: it.height, fps: fps, duration: L + 1 / fps });
        var base = c.layers.add(it), top = c.layers.add(it), op = top.property("ADBE Transform Group").property("ADBE Opacity");
        base.startTime = 0; top.startTime = -L;
        AEK.motion.key(op, 0, 100); AEK.motion.key(op, ov / fps, 0);
        top.outPoint = ov / fps; top.name = "tail fade"; base.name = "body";
        return c;
    }
    // loopLayer(comp, footage or precomp, seconds, skipLast): time remap plus loopOut("cycle"), period set explicitly.
    // The default end key is not reliable (a footage layer got it at its duration, a precomp one frame earlier), so the
    // end key is placed here: n frames for the whole clip, n - 1 to skip a last frame that repeats the first.
    function loopLayer(c, src, seconds, skipLast) {
        var l = c.layers.add(src), tr, f = 1 / src.frameRate, n = Math.round(src.duration / f), P = (skipLast ? n - 1 : n) * f;
        l.timeRemapEnabled = true;
        l.outPoint = seconds;
        tr = l.property("ADBE Time Remapping");
        tr.setValueAtTime(P, P);
        while (tr.numKeys > 2 && tr.keyTime(tr.numKeys) > P + f / 10) { tr.removeKey(tr.numKeys); }
        while (tr.numKeys > 2) { tr.removeKey(2); }
        tr.expression = "loopOut(\"cycle\")";
        return l;
    }
    // cues(comp, [{path, at (frames), gainDb, name, prov}]): one audio layer per cue, the same file imported once
    function cues(c, list) {
        var cache = {}, out = [], i, q, it, l;
        for (i = 0; i < list.length; i++) {
            q = list[i];
            it = cache[q.path] || land(q.path, { name: q.name, prov: q.prov, bin: "generated audio" });
            cache[q.path] = it;
            l = c.layers.add(it); l.name = q.name || it.name;
            l.startTime = q.at / c.frameRate;
            if (q.gainDb !== undefined) { l.property("ADBE Audio Group").property("ADBE Audio Levels").setValue([q.gainDb, q.gainDb]); }
            if (it.comment) { l.comment = it.comment; }
            out.push({ name: l.name, index: l.index, inPoint: l.inPoint, outPoint: l.outPoint });
        }
        return out;
    }
    // Punctuation and spaces in ASCII, Latin-1, General Punctuation, Arabic, Hebrew, Devanagari, CJK and fullwidth forms.
    // ExtendScript regular expressions have no Unicode property escapes, so the ranges are explicit.
    var PUNCT_ONLY = new RegExp("^[\\s\\x21-\\x2F\\x3A-\\x40\\x5B-\\x60\\x7B-\\x7E\\u00A1-\\u00A9\\u00AB-\\u00B1\\u00B4\\u00B6-\\u00B8" +
        "\\u00BB\\u00BF\\u00D7\\u00F7\\u055A-\\u055F\\u0589\\u05BE\\u05C0\\u05C3\\u05C6\\u05F3\\u05F4\\u060C\\u061B\\u061F" +
        "\\u066A-\\u066D\\u06D4\\u0964\\u0965\\u2000-\\u206F\\u2E00-\\u2E7F\\u3000-\\u303F\\u30FB\\uFE10-\\uFE1F\\uFE30-\\uFE4F" +
        "\\uFF01-\\uFF0F\\uFF1A-\\uFF20\\uFF3B-\\uFF40\\uFF5B-\\uFF65]*$");
    // wordMarkers(layer, sentences, {offset seconds, skipPunct}): one layer marker per word, duration = word length.
    // sentences: [{text, words:[{word, startTime, endTime}]}] in seconds, as the speech model returns them.
    // skipPunct (default on) drops a word made only of punctuation and spaces; words in any script stay.
    function wordMarkers(l, sentences, o) {
        o = o || {};
        var mk = l.property("ADBE Marker"), n = 0, i, j, w, m, off = o.offset || 0;
        for (i = 0; i < sentences.length; i++) {
            for (j = 0; j < sentences[i].words.length; j++) {
                w = sentences[i].words[j];
                if (o.skipPunct !== false && PUNCT_ONLY.test(String(w.word))) { continue; }
                m = new MarkerValue(w.word); m.duration = Math.max(0, w.endTime - w.startTime);
                mk.setValueAtTime(l.startTime + off + w.startTime, m); n++;
            }
        }
        return n;
    }
    return { note: note, land: land, place: place, upscaled: upscaled, loopCrossfade: loopCrossfade, loopLayer: loopLayer, cues: cues, wordMarkers: wordMarkers };
})();
