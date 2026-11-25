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
    // INOUT: range selector Offset driven by the layer's own in and out points, so trimming or sliding the layer retimes it
    function inOutExpr(inFrames, outFrames) {
        return "var f = thisComp.frameDuration, a = " + inFrames + " * f, b = " + outFrames + " * f;\n" +
            "if (time < outPoint - b) { linear(time, inPoint, inPoint + a, -100, 100); }\nelse { linear(time, outPoint - b, outPoint, 100, -100); }";
    }
    // inOut(layer, {inFrames, outFrames, properties, basedOn, shape, easeLow, easeHigh, name})
    function inOut(l, o) {
        o = o || {};
        var name = o.name || "in-out";
        AEK.text.animator(l, { name: name, properties: o.properties || { opacity: 0, position: [0, 40] }, basedOn: o.basedOn || "charactersExcludingSpaces", shape: o.shape || "rampUp", easeLow: o.easeLow === undefined ? 100 : o.easeLow, easeHigh: o.easeHigh });
        var off = animatorByName(l, name).property("ADBE Text Selectors").property(1).property("ADBE Text Percent Offset");
        AEK.expr.set(off, inOutExpr(o.inFrames || 12, o.outFrames || 10));
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
    // readability(comp, {bg:[r,g,b], minFrames, minCapRatio, safe, minContrast}): one row per text layer + findings
    function readability(c, o) {
        o = o || {};
        var fps = c.frameRate, rows = [], findings = [], i, l, d, frames, mid, inf, cap, cr, probe, minF = o.minFrames || 24, minCap = o.minCapRatio || 0.035, safe = o.safe === undefined ? 0.1 : o.safe, minC = o.minContrast || 4.5;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!(l instanceof TextLayer) || !l.enabled) { continue; }
            d = l.property("ADBE Text Properties").property("ADBE Text Document").value;
            frames = Math.round((l.outPoint - l.inPoint) * fps);
            mid = Math.max(l.inPoint, Math.min(l.outPoint - c.frameDuration, (l.inPoint + l.outPoint) / 2));
            inf = AEK.text.inFrame(l, c, safe, mid);
            // cap height measured from a temporary "H" in the same font and size, scaled like the layer
            probe = c.layers.addText("H");
            var pd = probe.property("ADBE Text Properties").property("ADBE Text Document").value;
            pd.font = d.font; pd.fontSize = d.fontSize; probe.property("ADBE Text Properties").property("ADBE Text Document").setValue(pd);
            cap = probe.sourceRectAtTime(0, false).height * l.property("ADBE Transform Group").property("ADBE Scale").value[1] / 100;
            probe.remove();
            cr = (o.bg && d.applyFill) ? contrast(d.fillColor, o.bg) : null;
            var words = d.text.split(/\s+/).length;
            rows.push({ layer: l.name, words: words, frames: frames, framesPerWord: Math.round(frames / words * 10) / 10, font: d.font, size: d.fontSize, capPx: Math.round(cap), capRatio: Math.round(cap / c.height * 1000) / 1000, contrast: cr === null ? null : Math.round(cr * 100) / 100, inSafe: inf.ok, tracking: d.tracking, leadingRatio: d.autoLeading ? "auto" : Math.round(d.leading / d.fontSize * 100) / 100 });
            if (frames < minF) { findings.push({ severity: "warn", rule: "dwell", where: l.name, message: frames + " frames on screen, minimum " + minF + " at " + fps + " fps" }); }
            if (cap / c.height < minCap) { findings.push({ severity: "warn", rule: "size", where: l.name, message: "cap height " + Math.round(cap) + " px is " + Math.round(cap / c.height * 1000) / 10 + " % of the frame height" }); }
            if (cr !== null && cr < minC) { findings.push({ severity: "error", rule: "contrast", where: l.name, message: "contrast " + Math.round(cr * 100) / 100 + ":1 below " + minC + ":1" }); }
            if (!inf.ok) { findings.push({ severity: "error", rule: "safe", where: l.name, message: "text leaves the " + Math.round((1 - 2 * safe) * 100) + " % safe area at mid-life" }); }
        }
        return { rows: rows, findings: findings };
    }
    return { BASED: BASED, SHAPE: SHAPE, GROUP: GROUP, MODE: MODE, animatorByName: animatorByName, selector: selector, grouping: grouping, markWords: markWords, REVEAL: REVEAL, phraseLayers: phraseLayers, inOutExpr: inOutExpr, inOut: inOut, balance: balance, contrast: contrast, readability: readability };
})();
