// typography.jsx: AEX.type, kinetic type helpers on top of AEK (core, text, json). ES3.
// Load with: ae.py run job.jsx --lib <skill>/scripts/typography.jsx
var AEX = AEX || {};
AEX.type = (function () {
    var BASED = { characters: 1, charactersExcludingSpaces: 2, words: 3, lines: 4 };
    var SHAPE = { square: 1, rampUp: 2, rampDown: 3, triangle: 4, round: 5, smooth: 6 };
    var GROUP = { character: 1, word: 2, line: 3, all: 4 };
    var MODE = { add: 1, subtract: 2, intersect: 3, min: 4, max: 5, difference: 6 };
    function anims(l) { return l.property("ADBE Text Properties").property("ADBE Text Animators"); }
    // animatorByName(layer, name): fresh reference every call (references die after addProperty)
    function animatorByName(l, name) {
        var a = anims(l), i;
        for (i = 1; i <= a.numProperties; i++) { if (a.property(i).name === name) { return a.property(i); } }
        throw new Error("No text animator named '" + name + "' on layer '" + l.name + "'");
    }
    // selector(layer, animatorName, {type: "range"|"wiggly"|"expression", name, basedOn, shape, easeHigh, easeLow, units, start, end, offset, mode, amount, randomize, seed, expression})
    function selector(l, an, o) {
        o = o || {};
        var mn = { range: "ADBE Text Selector", wiggly: "ADBE Text Wiggly Selector", expression: "ADBE Text Expressible Selector" }[o.type || "range"];
        var idx = animatorByName(l, an).property("ADBE Text Selectors").addProperty(mn).propertyIndex, pre;
        function S() { return animatorByName(l, an).property("ADBE Text Selectors").property(idx); }
        function A() { return S().property("ADBE Text Range Advanced"); }
        if (o.name) { S().name = o.name; }
        if (o.type === "expression") {
            if (o.basedOn) { S().property("ADBE Text Range Type2").setValue(BASED[o.basedOn]); }
            if (o.expression) { AEK.expr.set(S().property("ADBE Text Expressible Amount"), o.expression); }
            return { index: idx, ref: S };
        }
        if (o.type === "wiggly") {
            if (o.basedOn) { S().property("ADBE Text Range Type2").setValue(BASED[o.basedOn]); }
            if (o.mode) { S().property("ADBE Text Selector Mode").setValue(MODE[o.mode]); }
            if (o.max !== undefined) { S().property("ADBE Text Wiggly Max Amount").setValue(o.max); }
            if (o.min !== undefined) { S().property("ADBE Text Wiggly Min Amount").setValue(o.min); }
            if (o.wps !== undefined) { S().property("ADBE Text Temporal Freq").setValue(o.wps); }
            if (o.seed !== undefined) { S().property("ADBE Text Wiggly Random Seed").setValue(o.seed); }
            return { index: idx, ref: S };
        }
        if (o.units === "index") { A().property("ADBE Text Range Units").setValue(2); }
        if (o.basedOn) { A().property("ADBE Text Range Type2").setValue(BASED[o.basedOn]); }
        if (o.mode) { A().property("ADBE Text Selector Mode").setValue(MODE[o.mode]); }
        if (o.amount !== undefined) { A().property("ADBE Text Selector Max Amount").setValue(o.amount); }
        if (o.shape) { A().property("ADBE Text Range Shape").setValue(SHAPE[o.shape]); }
        if (o.easeHigh !== undefined) { A().property("ADBE Text Levels Max Ease").setValue(o.easeHigh); }
        if (o.easeLow !== undefined) { A().property("ADBE Text Levels Min Ease").setValue(o.easeLow); }
        if (o.randomize) { A().property("ADBE Text Randomize Order").setValue(1); }
        if (o.seed !== undefined) { A().property("ADBE Text Random Seed").setValue(o.seed); }
        pre = (o.units === "index") ? "ADBE Text Index " : "ADBE Text Percent ";
        if (o.start !== undefined) { S().property(pre + "Start").setValue(o.start); }
        if (o.end !== undefined) { S().property(pre + "End").setValue(o.end); }
        if (o.offset !== undefined) { S().property(pre + "Offset").setValue(o.offset); }
        return { index: idx, ref: S, prop: function (n) { return S().property(pre + n); } };
    }
    // amount(layer, animatorName, selectorIndex): the range selector Amount (under Advanced), fetched fresh by name.
    // AEK.text.animator(..., {amount}) sets it and returns a handle that goes stale after later addProperty calls.
    function amount(l, an, si) {
        return animatorByName(l, an).property("ADBE Text Selectors").property(si || 1).property("ADBE Text Range Advanced").property("ADBE Text Selector Max Amount");
    }
    // overshootExpr({start, stagger, peak, settle, overshoot, order, vary}): expression selector Amount. Frames from the layer in point.
    // Each unit eases out to 1 + overshoot by `peak` frames, then settles by `settle` frames. A negative Amount applies the
    // animator values inverted, which is the overshoot; Amount is clamped to -100..100.
    // order: "left" (default), "right" or "center" (units start from the middle outward). vary (0..1): the unit farthest from
    // the first one to move travels (1 - vary) of the offset, so letters stop sharing one distance.
    function overshootExpr(o) {
        o = o || {};
        var ord = o.order || "left", k;
        if (ord === "center") { k = "Math.abs(textIndex - (textTotal + 1) / 2)"; }
        else if (ord === "right") { k = "(textTotal - textIndex)"; }
        else { k = "(textIndex - 1)"; }
        var span = ord === "center" ? "Math.max(1, (textTotal - 1) / 2)" : "Math.max(1, textTotal - 1)";
        return "var f = thisComp.frameDuration, k = " + k + ", t0 = inPoint + (" + (o.start || 0) + " + k * " + (o.stagger === undefined ? 3 : o.stagger) + ") * f;\n" +
            "var tp = t0 + " + (o.peak || 10) + " * f, t1 = t0 + " + (o.settle || 18) + " * f, o = " + (o.overshoot === undefined ? 8 : o.overshoot) + " / 100;\n" +
            "var m = 1 - " + (o.vary || 0) + " * k / " + span + ";\n" +
            "var e = time < tp ? easeOut(time, t0, tp, 0, 1 + o) : ease(time, tp, t1, 1 + o, 1);\n100 * m * (1 - e);";
    }
    // overshoot(layer, {name, properties, basedOn, start, stagger, peak, settle, overshoot, order, vary}): animator whose only
    // selector is the overshoot expression selector. properties hold the hidden offset (e.g. {position: [0, 120], opacity: 0}).
    function overshoot(l, o) {
        o = o || {};
        var name = o.name || "overshoot";
        AEK.text.animator(l, { name: name, properties: o.properties || { position: [0, 120] } });
        animatorByName(l, name).property("ADBE Text Selectors").property(1).remove();
        selector(l, name, { type: "expression", name: "per-unit overshoot", basedOn: o.basedOn || "charactersExcludingSpaces", expression: overshootExpr(o) });
        return animatorByName(l, name);
    }
    // compBounds(layer, t): text bounds in comp space through toComp on the four corners of sourceRectAtTime (a temporary
    // Point Control): 3D layers, X and Y rotation, orientation and the comp camera count. AEK.text.measure walks 2D parents only.
    function compBounds(l, t) {
        var fx = l.property("ADBE Effect Parade"), idx = fx.addProperty("ADBE Point Control").propertyIndex, i, v, xs = [], ys = [];
        var corners = ["[r.left, r.top]", "[r.left + r.width, r.top]", "[r.left, r.top + r.height]", "[r.left + r.width, r.top + r.height]"];
        for (i = 0; i < 4; i++) {
            var pt = l.property("ADBE Effect Parade").property(idx).property(1);
            pt.expression = "var r = thisLayer.sourceRectAtTime(time, false); thisLayer.toComp(" + corners[i] + ");";
            v = pt.valueAtTime(t || 0, false); xs.push(v[0]); ys.push(v[1]);
        }
        l.property("ADBE Effect Parade").property(idx).remove();
        function mn(a) { return Math.min(a[0], a[1], a[2], a[3]); }
        function mx(a) { return Math.max(a[0], a[1], a[2], a[3]); }
        return { left: mn(xs), top: mn(ys), right: mx(xs), bottom: mx(ys), width: mx(xs) - mn(xs), height: mx(ys) - mn(ys) };
    }
    // inFrame(layer, comp, margin, t): AEK.text.inFrame for 2D chains; compBounds when the layer or a parent is 3D
    // (the kit reads those flat). Same answer shape, plus `via` ("kit" or "toComp").
    function inFrame(l, c, margin, t) {
        if (AEK.text.measure(l, t || 0).comp.flat) { var k = AEK.text.inFrame(l, c, margin, t || 0); k.via = "kit"; return k; }
        var m = compBounds(l, t), mx = c.width * (margin || 0), my = c.height * (margin || 0);
        return { ok: m.left >= mx && m.top >= my && m.right <= c.width - mx && m.bottom <= c.height - my, bounds: m, safe: [mx, my, c.width - mx, c.height - my], via: "toComp" };
    }
    // trackingFit(layer, animatorName, comp, {margin, t}): lowers the animator's Tracking value until the line, at time t
    // (the first frame of the tracking-in, Amount at 100), stays inside the frame minus margin (default 0.05). Tracking must be unkeyed.
    function trackingFit(l, an, c, o) {
        o = o || {};
        var tr = function () { return animatorByName(l, an).property("ADBE Text Animator Properties").property("ADBE Text Tracking Amount"); };
        if (tr().numKeys > 0) { throw new Error("trackingFit(): Tracking is keyed; key the selector Amount instead"); }
        var from = tr().value, lo = 0, hi = from, i, ok = function (v) { tr().setValue(v); return inFrame(l, c, o.margin === undefined ? 0.05 : o.margin, o.t || 0).ok; };
        if (ok(hi)) { return { from: from, value: from, changed: false }; }
        for (i = 0; i < 12; i++) { var mid = (lo + hi) / 2; if (ok(mid)) { lo = mid; } else { hi = mid; } }
        tr().setValue(Math.floor(lo));
        return { from: from, value: Math.floor(lo), changed: true, bounds: inFrame(l, c, o.margin === undefined ? 0.05 : o.margin, o.t || 0).bounds };
    }
    // grouping(layer, "character"|"word"|"line"|"all", [alignX%, alignY%]): More Options anchor grouping; [0,-50] caps, [0,-25] lowercase (Adobe help)
    function grouping(l, g, align) {
        var mo = l.property("ADBE Text Properties").property("ADBE Text More Options");
        mo.property("ADBE Text Anchor Point Option").setValue(GROUP[g]);
        if (align) { l.property("ADBE Text Properties").property("ADBE Text More Options").property("ADBE Text Anchor Point Align").setValue(align); }
        return l.property("ADBE Text Properties").property("ADBE Text More Options").property("ADBE Text Anchor Point Option").value;
    }
    // markWords(layer, words, fps): one layer marker per word at frame f0 (comment = word, duration = frames)
    function markWords(l, words, fps, offsetFrames) {
        var mk = l.property("ADBE Marker"), i, mv;
        for (i = 0; i < words.length; i++) {
            mv = new MarkerValue(words[i].word);
            mv.duration = (words[i].frames || 1) / fps;
            mk.setValueAtTime((words[i].f0 - (offsetFrames || 0)) / fps, mv);
        }
        return l.property("ADBE Marker").numKeys;
    }
    // REVEAL: expression selector Amount (Based On Words): word k hidden until layer marker k, then eases in over FR frames
    var REVEAL = "var FR = 4;\nvar m = thisLayer.marker, k = textIndex;\nif (k > m.numKeys) { 0; } else {\n  var t0 = m.key(k).time;\n  100 * (1 - ease(time, t0, t0 + FR * thisComp.frameDuration, 0, 1));\n}";
    // phraseLayers(comp, data, {font, size, fill, position, box, tail}): one text layer per phrase, word markers, reveal animator
    function phraseLayers(c, data, o) {
        o = o || {};
        var fps = data.fps, out = [], p, w, words, l, i, j, tail = o.tail === undefined ? 8 : o.tail, last;
        for (i = 0; i < data.phrases.length; i++) {
            p = data.phrases[i]; words = [];
            for (j = 0; j < data.words.length; j++) { if (data.words[j].phrase === p.p) { words.push(data.words[j]); } }
            l = AEK.text.add(c, p.text, { name: "phrase_" + (i + 1), font: o.font, size: o.size, fill: o.fill, justify: "center", box: o.box, position: o.position });
            l.inPoint = p.f0 / fps;
            last = (i + 1 < data.phrases.length) ? data.phrases[i + 1].f0 : Math.round(c.duration * fps);
            l.outPoint = Math.min(last, p.f1 + tail) / fps;
            markWords(l, words, fps, 0);
            AEK.text.animator(l, { name: "reveal", properties: { opacity: 0, position: [0, Math.round((o.size || 100) * 0.3)] } });
            // remove the default range selector so only the expression selector decides
            animatorByName(l, "reveal").property("ADBE Text Selectors").property(1).remove();
            selector(l, "reveal", { type: "expression", name: "word reveal", basedOn: "words", expression: o.reveal || REVEAL });
            out.push({ name: l.name, text: p.text, inFrame: Math.round(l.inPoint * fps), outFrame: Math.round(l.outPoint * fps), markers: l.property("ADBE Marker").numKeys });
        }
        return out;
    }
    // INOUT: range selector Offset driven by the layer's own in and out points, so trimming or sliding the layer retimes it.
    // In: easeOut (fast start, long settle). Out: easeIn (still fast on the last frame). Ramp Up swept back runs the out
    // last character first ("reverse"); a second animator with Ramp Down runs it first character first ("forward").
    function inOutExpr(inFrames, outFrames, exit) {
        var tail = exit === "forward" ? "100;" : "easeIn(time, outPoint - b, outPoint, 100, -100);";
        return "var f = thisComp.frameDuration, a = " + inFrames + " * f, b = " + outFrames + " * f;\n" +
            "if (time < outPoint - b) { easeOut(time, inPoint, inPoint + a, -100, 100); }\nelse { " + tail + " }";
    }
    // OUTFWD: Offset of the "<name> out" animator (Ramp Down): -100 selects nothing; sweeping to 100 selects from the first character
    function outForwardExpr(outFrames) {
        return "var b = " + outFrames + " * thisComp.frameDuration;\neaseIn(time, outPoint - b, outPoint, -100, 100);";
    }
    // inOut(layer, {inFrames, outFrames, properties, outProperties, basedOn, shape, easeLow, easeHigh, name, exit: "reverse"|"forward"})
    function inOut(l, o) {
        o = o || {};
        var name = o.name || "in-out", exit = o.exit || "reverse";
        AEK.text.animator(l, { name: name, properties: o.properties || { opacity: 0, position: [0, 40] }, basedOn: o.basedOn || "charactersExcludingSpaces", shape: o.shape || "rampUp", easeLow: o.easeLow === undefined ? 100 : o.easeLow, easeHigh: o.easeHigh });
        AEK.expr.set(animatorByName(l, name).property("ADBE Text Selectors").property(1).property("ADBE Text Percent Offset"), inOutExpr(o.inFrames || 12, o.outFrames || 10, exit));
        if (exit === "forward") {
            AEK.text.animator(l, { name: name + " out", properties: o.outProperties || o.properties || { opacity: 0, position: [0, 40] }, basedOn: o.basedOn || "charactersExcludingSpaces", shape: "rampDown", easeLow: o.easeLow === undefined ? 100 : o.easeLow });
            AEK.expr.set(animatorByName(l, name + " out").property("ADBE Text Selectors").property(1).property("ADBE Text Percent Offset"), outForwardExpr(o.outFrames || 10));
        }
        return animatorByName(l, name).property("ADBE Text Selectors").property(1).property("ADBE Text Percent Offset");
    }
    // balance(layer, maxWidth, maxLines): point text only. Tries every break between words (1 to maxLines lines) and keeps
    // the layout with the fewest lines that fits maxWidth (comp px), ties broken by the most even line widths.
    function balance(l, maxWidth, maxLines) {
        var p = l.property("ADBE Text Properties").property("ADBE Text Document"), d = p.value, orig = d.text.replace(/[\r\n]+/g, " ");
        var w = orig.split(" "), best = null, n = w.length, i, j, txt, width, lines;
        function tryText(t) { var dd = p.value; dd.text = t; p.setValue(dd); return AEK.text.measure(l, 0).comp.width; }
        function consider(t, nl) { width = tryText(t); if (!best || (width <= maxWidth && (best.width > maxWidth || nl < best.lines || (nl === best.lines && width < best.width))) || (best.width > maxWidth && width < best.width)) { best = { text: t, width: width, lines: nl }; } }
        consider(orig, 1);
        if ((maxLines || 2) >= 2) { for (i = 1; i < n; i++) { consider(w.slice(0, i).join(" ") + "\r" + w.slice(i).join(" "), 2); } }
        if ((maxLines || 2) >= 3) { for (i = 1; i < n - 1; i++) { for (j = i + 1; j < n; j++) { consider(w.slice(0, i).join(" ") + "\r" + w.slice(i, j).join(" ") + "\r" + w.slice(j).join(" "), 3); } } }
        tryText(best.text);
        lines = best.text.split("\r");
        return { text: lines.join(" / "), lines: best.lines, width: Math.round(best.width), fits: best.width <= maxWidth };
    }
    // luminance and WCAG contrast ratio of two [r,g,b] 0..1 colors
    function lum(c) {
        var v = [], i, x;
        for (i = 0; i < 3; i++) { x = c[i]; v.push(x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4)); }
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
    }
    function contrast(a, b) { var la = lum(a), lb = lum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); }
    // colorRuns(textDocument): runs of one fill color, read per character (TextDocument.fillColor is the FIRST character only).
    // Spaces join the run before them. Returns [{start, end, text, fill, applyFill}].
    function colorRuns(d) {
        var runs = [], i, r, key, last = null, ch;
        for (i = 0; i < d.text.length; i++) {
            ch = d.text.charAt(i);
            r = d.characterRange(i, i + 1);
            key = r.applyFill ? Math.round(r.fillColor[0] * 1000) + "," + Math.round(r.fillColor[1] * 1000) + "," + Math.round(r.fillColor[2] * 1000) : "none";
            if (last && (last.key === key || /\s/.test(ch))) { last.end = i + 1; last.text += ch; continue; }
            last = { key: key, start: i, end: i + 1, text: ch, fill: r.applyFill ? [r.fillColor[0], r.fillColor[1], r.fillColor[2]] : null, applyFill: r.applyFill };
            runs.push(last);
        }
        for (i = 0; i < runs.length; i++) { delete runs[i].key; }
        return runs;
    }
    // settled(layer, comp, {restFrame}): frames where the text is at rest and fully opaque. Works on a temporary duplicate
    // (removed before returning): every animator gets a Position probe of [0, 1000 x its index], so any selector that still
    // selects a character changes sourceRectAtTime. The rest state is the text at `restFrame`, or else the most frequent
    // state among frames at 100 % layer opacity. Parent motion (a push-in) does not count against rest.
    // Returns {frames (longest run of settled frames), first, last, total, onScreen}.
    function settled(l, c, o) {
        o = o || {};
        var fps = c.frameRate, f0 = Math.round(l.inPoint * fps), f1 = Math.round(l.outPoint * fps) - 1, d = l.duplicate(), i, j, p, sig = [], op = [], count = {}, rest = null, best = 0;
        d.enabled = false;
        var an = function () { return d.property("ADBE Text Properties").property("ADBE Text Animators"); };
        for (i = 1; i <= an().numProperties; i++) {
            if (!an().property(i).enabled) { continue; }
            if (!an().property(i).property("ADBE Text Animator Properties").property("ADBE Text Position 3D")) { an().property(i).property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D"); }
            p = an().property(i).property("ADBE Text Animator Properties").property("ADBE Text Position 3D");
            while (p.numKeys) { p.removeKey(1); }
            if (p.expression) { p.expression = ""; }
            p.setValue([0, 1000 * i, 0]);
        }
        for (j = f0; j <= f1; j++) {
            var r = d.sourceRectAtTime(j / fps, false);
            sig.push(Math.round(r.left * 2) + "," + Math.round(r.top * 2) + "," + Math.round(r.width * 2) + "," + Math.round(r.height * 2));
            op.push(l.property("ADBE Transform Group").property("ADBE Opacity").valueAtTime(j / fps, false));
        }
        d.remove();
        if (o.restFrame !== undefined && o.restFrame >= f0 && o.restFrame <= f1) { rest = sig[o.restFrame - f0]; }
        else { for (j = 0; j < sig.length; j++) { if (op[j] >= 99.9) { count[sig[j]] = (count[sig[j]] || 0) + 1; if (count[sig[j]] > best) { best = count[sig[j]]; rest = sig[j]; } } } }
        var run = 0, longest = 0, first = null, last = null, start = null, total = 0;
        for (j = 0; j < sig.length; j++) {
            if (rest !== null && sig[j] === rest && op[j] >= 99.9) {
                total++; run++; if (run === 1) { start = f0 + j; }
                if (run > longest) { longest = run; first = start; last = f0 + j; }
            } else { run = 0; }
        }
        return { frames: longest, first: first, last: last, total: total, onScreen: f1 - f0 + 1 };
    }
    // readability(comp, {bg:[r,g,b], minFrames, minPerWord, minCapRatio, safe, minContrast}): one row per text layer + findings.
    // Cap height is measured against the short side of the frame (1080 in 16:9, 9:16 and 1:1 alike); safe area through parents.
    // Contrast is checked for every color run. Dwell is the settled dwell; a word-synced phrase layer (one marker per word)
    // is read while it builds, so its dwell is its time on screen. The job adds and removes temporary layers and effects.
    // backdrop(comp, textLayer, {frames, grid}): what lies under a text box over footage. Every text layer of the comp is
    // switched off, the comp is nested in a temporary comp, and sampleImage() reads the mean color of grid cells
    // (default 4 x 2) of the layer's box at each frame (default 5 frames across its life). All is restored and removed.
    // Text over a flat color needs none of this: pass {bg}. Over footage pass {sample: true} or {sample: {frames, grid}}.
    function backdrop(c, l, s) {
        s = s === true ? {} : (s || {});
        var g = s.grid || [4, 2], fr = s.frames, i, j, k, off = [], cells = [], t;
        if (!fr) { fr = []; var a = Math.round(l.inPoint * c.frameRate), z = Math.round(l.outPoint * c.frameRate) - 1; for (i = 0; i < 5; i++) { fr.push(Math.round(a + (z - a) * i / 4)); } }
        for (i = 1; i <= c.numLayers; i++) { if (c.layer(i) instanceof TextLayer && c.layer(i).enabled) { c.layer(i).enabled = false; off.push(c.layer(i)); } }
        var tmp = app.project.items.addComp("_backdrop_probe", c.width, c.height, c.pixelAspect, c.duration, c.frameRate);
        var nest = tmp.layers.add(c); nest.name = "under";
        // one Color Control per cell; sampleImage reads back from a script only once the comp has rendered at that time,
        // so each time is rendered once (a frame saved to the temp folder) before the values are read
        var nItems = app.project.numItems, nl = tmp.layers.addNull(), nsrc = nl.source, n = g[0] * g[1], ids = [], png = Folder.temp.fsName + "/_backdrop_probe.png";
        for (i = 0; i < n; i++) { ids.push(nl.property("ADBE Effect Parade").addProperty("ADBE Color Control").propertyIndex); }
        var vw = tmp.openInViewer(); if (vw) { vw.setActive(); }
        for (k = 0; k < fr.length; k++) {
            t = fr[k] / c.frameRate;
            var b = compBounds(l, t), cw = (b.right - b.left) / g[0], chh = (b.bottom - b.top) / g[1], q = 0;
            for (i = 0; i < g[0]; i++) {
                for (j = 0; j < g[1]; j++) {
                    var x = b.left + cw * (i + 0.5), y = b.top + chh * (j + 0.5);
                    nl.property("ADBE Effect Parade").property(ids[q++]).property(1).expression = 'thisComp.layer("under").sampleImage([' + x + ',' + y + '],[' + (cw / 2) + ',' + (chh / 2) + '],true,time);';
                }
            }
            tmp.time = t; AEK.capture.frame(tmp, t, png);
            q = 0;
            for (i = 0; i < g[0]; i++) {
                for (j = 0; j < g[1]; j++) {
                    var v = nl.property("ADBE Effect Parade").property(ids[q++]).property(1).valueAtTime(t, false);
                    cells.push({ frame: fr[k], cell: [i, j], rgb: [v[0], v[1], v[2]], lum: lum([v[0], v[1], v[2]]) });
                }
            }
        }
        tmp.remove();
        // the null's solid (and a Solids folder made for it) stay in the project after the comp goes: remove them too
        var fld = nsrc.parentFolder; nsrc.remove();
        if (fld !== app.project.rootFolder && fld.numItems === 0 && app.project.numItems >= nItems) { fld.remove(); }
        for (i = 0; i < off.length; i++) { off[i].enabled = true; }
        var dk = cells[0], lt = cells[0];
        for (i = 1; i < cells.length; i++) { if (cells[i].lum < dk.lum) { dk = cells[i]; } if (cells[i].lum > lt.lum) { lt = cells[i]; } }
        function rd(cl) { return { frame: cl.frame, cell: cl.cell, rgb: [Math.round(cl.rgb[0] * 255), Math.round(cl.rgb[1] * 255), Math.round(cl.rgb[2] * 255)] }; }
        return { cells: cells, frames: fr, darkest: rd(dk), lightest: rd(lt) };
    }
    // worstOver(fill, backdrop): lowest contrast of a fill against every sampled cell.
    function worstOver(fill, u) { var w = null, i, cr; for (i = 0; i < u.cells.length; i++) { cr = contrast(fill, u.cells[i].rgb); if (w === null || cr < w) { w = cr; } } return w; }
    function readability(c, o) {
        o = o || {};
        var fps = c.frameRate, side = Math.min(c.width, c.height), rows = [], findings = [], i, j, l, d, frames, mid, inf, cap, probe, minF = o.minFrames || 18, perWord = o.minPerWord === undefined ? 6 : o.minPerWord, minCap = o.minCapRatio || 0.035, safe = o.safe === undefined ? 0.1 : o.safe, minC = o.minContrast || 4.5;
        var layers = [];
        for (i = 1; i <= c.numLayers; i++) { if (c.layer(i) instanceof TextLayer && c.layer(i).enabled) { layers.push(c.layer(i)); } }
        for (i = 0; i < layers.length; i++) {
            l = layers[i];
            d = l.property("ADBE Text Properties").property("ADBE Text Document").value;
            frames = Math.round((l.outPoint - l.inPoint) * fps);
            mid = Math.max(l.inPoint, Math.min(l.outPoint - c.frameDuration, (l.inPoint + l.outPoint) / 2));
            inf = inFrame(l, c, safe, mid);
            // cap height from a temporary "H" in the same font and size, scaled like the layer (removed at once)
            probe = c.layers.addText("H");
            var pd = probe.property("ADBE Text Properties").property("ADBE Text Document").value;
            pd.font = d.font; pd.fontSize = d.fontSize; probe.property("ADBE Text Properties").property("ADBE Text Document").setValue(pd);
            cap = probe.sourceRectAtTime(0, false).height * l.property("ADBE Transform Group").property("ADBE Scale").value[1] / 100;
            probe.remove();
            var words = d.text.split(/\s+/).length, synced = l.property("ADBE Marker").numKeys > 1;
            var st = synced ? null : settled(l, c, {});
            var dwell = synced ? frames : st.frames, need = Math.max(minF, Math.round(perWord * words));
            var under = o.sample ? backdrop(c, l, o.sample) : null;
            var runs = [], cmin = null, runs0 = (o.bg || under) ? colorRuns(d) : [];
            for (j = 0; j < runs0.length; j++) {
                if (!runs0[j].applyFill || !/\S/.test(runs0[j].text)) { continue; }
                var cr = under ? worstOver(runs0[j].fill, under) : contrast(runs0[j].fill, o.bg);
                runs.push({ text: runs0[j].text, contrast: Math.round(cr * 100) / 100 });
                if (cmin === null || cr < cmin) { cmin = cr; }
                if (cr < minC) { findings.push({ severity: cr < 3 ? "error" : "warn", rule: "contrast", where: l.name + " \"" + runs0[j].text + "\"", message: "contrast " + Math.round(cr * 100) / 100 + ":1 below " + minC + ":1" }); }
            }
            rows.push({ layer: l.name, words: words, frames: frames, settled: synced ? "synced" : st.frames, settledFrom: synced ? null : st.first, settledTo: synced ? null : st.last, font: d.font, size: d.fontSize, capPx: Math.round(cap), capRatio: Math.round(cap / side * 1000) / 1000, contrast: cmin === null ? null : Math.round(cmin * 100) / 100, runs: runs, inSafe: inf.ok, tracking: d.tracking, leadingRatio: d.autoLeading ? "auto" : Math.round(d.leading / d.fontSize * 100) / 100,
                backdrop: under ? { cells: under.cells.length, frames: under.frames, darkest: under.darkest, lightest: under.lightest } : null });
            if (dwell < need) { findings.push({ severity: "warn", rule: "dwell", where: l.name, message: (synced ? "on screen " : "settled ") + dwell + " frames, minimum " + need + " at " + fps + " fps" }); }
            if (cap / side < minCap) { findings.push({ severity: "warn", rule: "size", where: l.name, message: "cap height " + Math.round(cap) + " px is " + Math.round(cap / side * 1000) / 10 + " % of the short side of the frame" }); }
            if (!inf.ok) { findings.push({ severity: "error", rule: "safe", where: l.name, message: "text leaves the " + Math.round((1 - 2 * safe) * 100) + " % safe area at mid-life" }); }
        }
        return { rows: rows, findings: findings };
    }
    // layout(comp, {t, hold: [f0, f1]}): the layout and hold questions of the critique, as numbers. Bounds through parents
    // at time t (seconds). Findings: "stack" (every text layer centered on the vertical axis), "scale" (largest cap under 3x
    // the smallest), "hold" (no layer or parent moves across the hold frames). All are warnings: state the idea or change it.
    function layout(c, o) {
        o = o || {};
        var t = o.t || 0, rows = [], findings = [], i, l, b, caps = [], centered = 0, n = 0, moving = [];
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!(l instanceof TextLayer) || !l.enabled || l.inPoint > t || l.outPoint <= t) { continue; }
            b = inFrame(l, c, 0, t).bounds;
            var cx = (b.left + b.right) / 2, d = l.property("ADBE Text Properties").property("ADBE Text Document").value;
            var off = Math.round((cx - c.width / 2) / c.width * 1000) / 1000;
            n++; if (Math.abs(off) < 0.02) { centered++; }
            caps.push(d.fontSize * l.property("ADBE Transform Group").property("ADBE Scale").valueAtTime(t, false)[1] / 100);
            rows.push({ layer: l.name, left: Math.round(b.left), right: Math.round(b.right), top: Math.round(b.top), bottom: Math.round(b.bottom), widthRatio: Math.round((b.right - b.left) / c.width * 100) / 100, centerOffset: off });
        }
        if (n > 1 && centered === n) { findings.push({ severity: "warn", rule: "stack", message: n + " text layers all centered on the vertical axis: state the layout idea, or align to a grid line, cut one word in scale, or crop" }); }
        if (caps.length > 1) {
            var mx = Math.max.apply(null, caps), mn = Math.min.apply(null, caps);
            if (mx / mn < 3) { findings.push({ severity: "warn", rule: "scale", message: "largest to smallest type size " + Math.round(mx / mn * 100) / 100 + ":1, under 3:1" }); }
        }
        if (o.hold) {
            var a = o.hold[0] / c.frameRate, z = o.hold[1] / c.frameRate;
            for (i = 1; i <= c.numLayers; i++) {
                var L = c.layer(i), names = ["ADBE Position", "ADBE Scale", "ADBE Rotate Z"], k, q;
                for (k = 0; k < names.length; k++) {
                    q = L.property("ADBE Transform Group").property(names[k]);
                    if (!q) { continue; }
                    var va = q.valueAtTime(a, false), vz = q.valueAtTime(z, false), dv = 0, m;
                    if (va instanceof Array) { for (m = 0; m < va.length; m++) { dv = Math.max(dv, Math.abs(va[m] - vz[m])); } } else { dv = Math.abs(va - vz); }
                    if (dv > 0.5) { moving.push(L.name + " " + names[k]); }
                }
            }
            if (!moving.length) { findings.push({ severity: "warn", rule: "hold", message: "nothing moves between frames " + o.hold[0] + " and " + o.hold[1] + ": add a secondary action on a parent (push 2 to 4 %)" }); }
        }
        return { rows: rows, moving: moving, findings: findings };
    }
    // FONTS: candidates per role, ranked. Each role lists macOS names, then Windows names, then a fallback found on both.
    var FONTS = {
        display: ["AvenirNext-Bold", "HelveticaNeue-Bold", "Futura-Bold", "SegoeUI-Bold", "Arial-BoldMT"],
        text: ["AvenirNext-Medium", "HelveticaNeue-Medium", "Futura-Medium", "SegoeUI-Semibold", "ArialMT"],
        condensed: ["AvenirNextCondensed-Bold", "HelveticaNeue-CondensedBold", "ArialNarrow-Bold", "Arial-BoldMT"],
        serif: ["Georgia-Bold", "Charter-Bold", "Cambria-Bold", "TimesNewRomanPS-BoldMT"],
        cjk: ["HiraginoSans-W6", "YuGothic-Bold", "MicrosoftYaHei-Bold", "NotoSansCJKjp-Bold"]
    };
    // PAIRS: display + text in ONE family first (two weights of one design), then the fallback found on macOS and Windows.
    var PAIRS = [["AvenirNext-Bold", "AvenirNext-Medium"], ["HelveticaNeue-Bold", "HelveticaNeue-Medium"], ["Futura-Bold", "Futura-Medium"],
        ["SegoeUI-Bold", "SegoeUI-Semibold"], ["Arial-BoldMT", "ArialMT"]];
    function fontOk(ps, text) { var f = app.fonts.getFontsByPostScriptName(ps); return f.length > 0 && (!text || f[0].hasGlyphsFor(text)); }
    // pickFont(role, {text, candidates}): first installed candidate whose glyphs cover `text`. fallback true = last resort used.
    function pickFont(role, o) {
        o = o || {};
        var list = o.candidates || FONTS[role], tried = [], i;
        if (!list) { throw new Error("pickFont(): unknown role '" + role + "'"); }
        for (i = 0; i < list.length; i++) { tried.push(list[i]); if (fontOk(list[i], o.text)) { return { role: role, font: list[i], fallback: i === list.length - 1, tried: tried }; } }
        return { role: role, font: null, fallback: true, tried: tried };
    }
    // fontPair({text, pairs}): first pair whose two faces are installed and cover `text`: [display, text] of one family.
    function fontPair(o) {
        o = o || {};
        var list = o.pairs || PAIRS, i;
        for (i = 0; i < list.length; i++) { if (fontOk(list[i][0], o.text) && fontOk(list[i][1], o.text)) { return { display: list[i][0], text: list[i][1], fallback: i === list.length - 1, rank: i + 1 }; } }
        return { display: null, text: null, fallback: true, rank: 0 };
    }
    return { BASED: BASED, SHAPE: SHAPE, GROUP: GROUP, MODE: MODE, animatorByName: animatorByName, selector: selector, amount: amount,
        overshootExpr: overshootExpr, overshoot: overshoot, compBounds: compBounds, colorRuns: colorRuns, settled: settled, layout: layout, FONTS: FONTS, PAIRS: PAIRS, pickFont: pickFont, fontPair: fontPair, outForwardExpr: outForwardExpr, inFrame: inFrame, trackingFit: trackingFit, grouping: grouping, markWords: markWords, REVEAL: REVEAL, phraseLayers: phraseLayers, inOutExpr: inOutExpr, inOut: inOut, balance: balance, contrast: contrast, readability: readability };
})();
