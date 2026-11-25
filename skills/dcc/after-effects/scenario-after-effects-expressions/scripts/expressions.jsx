// expressions.jsx: measuring helpers for expression rigs. Load with `ae.py run job.jsx --lib <this file>`. Requires the AEK kit.
var AEX = AEX || {};
AEX.expressions = (function () {
    function esc(s) { return String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"'); }

    // probe(comp, body, times): evaluates an expression body (JavaScript engine, ends with `return`) at each time
    // on a temporary text layer and returns the parsed results. The probe layer is removed afterwards.
    function probe(c, body, times) {
        var t = times || [c.time], out = [], i, p, l, err;
        l = c.layers.addText("probe");
        l.name = "__probe";
        l.enabled = false;
        p = l.property("ADBE Text Properties").property("ADBE Text Document");
        p.expression = "JSON.stringify((function(){\n" + body + "\n})())";
        for (i = 0; i < t.length; i++) {
            var v = p.valueAtTime(t[i], false).text;
            err = p.expressionError;
            if (err !== "") { l.remove(); throw new Error("probe failed: " + err.replace(/\s+/g, " ").substring(0, 300)); }
            out.push(AEK.json.parse(v));
        }
        l.remove();
        return out;
    }

    // compRect(comp, layerName, t, extents): the layer's sourceRectAtTime corners mapped through toComp, as an axis-aligned box in comp pixels.
    // Parenting, scale and rotation are included because toComp is evaluated by the engine itself.
    function compRect(c, name, t, extents) {
        var body = 'const L = thisComp.layer("' + esc(name) + '"); const r = L.sourceRectAtTime(time, ' + (extents ? "true" : "false") + ');' +
            'const p = [L.toComp([r.left, r.top]), L.toComp([r.left + r.width, r.top]), L.toComp([r.left, r.top + r.height]), L.toComp([r.left + r.width, r.top + r.height])];' +
            'const xs = p.map(q => q[0]), ys = p.map(q => q[1]);' +
            'const o = {left: Math.min(...xs), top: Math.min(...ys), right: Math.max(...xs), bottom: Math.max(...ys)};' +
            'o.width = o.right - o.left; o.height = o.bottom - o.top; return o;';
        return probe(c, body, [t])[0];
    }

    // margins(outer, inner): distance from each inner edge to the outer edge, rounded to 0.01 px
    function margins(o, i) {
        function r(x) { return Math.round(x * 100) / 100; }
        return { left: r(i.left - o.left), right: r(o.right - i.right), top: r(i.top - o.top), bottom: r(o.bottom - i.bottom) };
    }

    // atFrames(prop, comp, [frames]): post-expression values at whole frames
    function atFrames(p, c, frames) {
        var out = [], i;
        for (i = 0; i < frames.length; i++) { out.push(p.valueAtTime(frames[i] * c.frameDuration, false)); }
        return out;
    }

    function dist(a, b) {
        if (!(a instanceof Array)) { return Math.abs(a - b); }
        var s = 0, i; for (i = 0; i < a.length; i++) { s += (a[i] - b[i]) * (a[i] - b[i]); } return Math.sqrt(s);
    }

    // seam(prop, comp, periodFrames, startFrame): the step across the loop point (frame start+P-1 to start+P) against the
    // steps on each side of it (P-2 to P-1, and P to P+1) and the median step inside the loop.
    // ratio = seam step / max(step before, step after, median): about 1 for a loop that repeats exactly, whatever its phase
    // at the seam (fastest or slowest); a jump stands out of its own neighbors. repeat = distance between frame start and
    // frame start+P (0 for an exact loop). medianRatio = seam step / median, kept for reference: it fails an exact loop whose
    // seam falls on its fastest phase.
    function seam(p, c, period, start) {
        var f0 = start || 0, steps = [], f, sorted, med, seamStep, before, after, fd = c.frameDuration;
        function v(fr) { return p.valueAtTime(fr * fd, false); }
        for (f = f0 + 1; f < f0 + period; f++) { steps.push(dist(v(f - 1), v(f))); }
        sorted = steps.slice(0).sort(function (x, y) { return x - y; });
        med = sorted[Math.floor(sorted.length / 2)];
        seamStep = dist(v(f0 + period - 1), v(f0 + period));
        before = dist(v(f0 + period - 2), v(f0 + period - 1));
        after = dist(v(f0 + period), v(f0 + period + 1));
        var ref = Math.max(before, after, med);
        function r3(x) { return Math.round(x * 1000) / 1000; }
        return { medianStep: r3(med), maxStep: r3(sorted[sorted.length - 1]), seamStep: r3(seamStep), stepBefore: r3(before), stepAfter: r3(after),
            ratio: ref > 0 ? Math.round(seamStep / ref * 100) / 100 : (seamStep > 0 ? 999 : 0),
            medianRatio: med > 0 ? Math.round(seamStep / med * 100) / 100 : null,
            repeat: r3(dist(v(f0), v(f0 + period))) };
    }

    // lagFrames(leader, follower, comp, maxLag, from, to): the frame shift that best matches follower(t) to leader(t - lag)
    function lagFrames(lead, fol, c, maxLag, from, to) {
        var best = -1, bestErr = 1e12, k, f, e;
        // compares motion, not positions: each property minus its own value at frame 0, so a constant offset does not bias the match
        var f0 = fol.valueAtTime(0, false), l0 = lead.valueAtTime(0, false);
        function sub(a, b) { if (!(a instanceof Array)) { return a - b; } var o = [], j; for (j = 0; j < a.length; j++) { o.push(a[j] - b[j]); } return o; }
        for (k = 0; k <= maxLag; k++) {
            e = 0;
            for (f = from; f <= to; f++) { e += dist(sub(fol.valueAtTime(f * c.frameDuration, false), f0), sub(lead.valueAtTime((f - k) * c.frameDuration, false), l0)); }
            if (e < bestErr) { bestErr = e; best = k; }
        }
        return { lag: best, error: Math.round(bestErr * 1000) / 1000 };
    }

    // timeEval(prop, comp, n): milliseconds to evaluate the expression at n distinct frames (cache-busting by distinct times)
    function timeEval(p, c, n) {
        // $.hiresTimer returns microseconds since its previous read: read once to reset it
        var i, us, reset = $.hiresTimer;
        for (i = 0; i < n; i++) { p.valueAtTime((i % Math.max(1, Math.floor(c.duration / c.frameDuration))) * c.frameDuration, false); }
        us = $.hiresTimer;
        return Math.round(us / 100) / 10;
    }

    // CODE: the lower-third rig expressions (JavaScript engine). Layer and control names are the rig's contract.
    var CODE = {
        // BOX > Rectangle Path > Size. BOX is parented to TXT_1 with anchor [0,0] at position [0,0]; padding divided by the text scale stays constant on screen
        boxSize: 'const t = thisComp.layer("TXT_1");\nconst c = thisComp.layer("CTRL");\nconst r = t.sourceRectAtTime(time, false);\nconst s = t.transform.scale / 100;\nconst w = r.width > 0 ? r.width + 2 * c.effect("Pad X")(1) / s[0] : 0;\nconst h = r.height > 0 ? r.height + 2 * c.effect("Pad Y")(1) / s[1] : 0;\n[w, h]',
        // BOX > Rectangle Path > Position: centers the rect on the ink box, so font, size and justification changes stay inside
        boxPos: 'const r = thisComp.layer("TXT_1").sourceRectAtTime(time, false);\n[r.left + r.width / 2, r.top + r.height / 2]',
        // TXT_2 > Position: under the ink bottom of TXT_1 plus Gap, left on the TXT_1 origin; any parent
        line2: 'const a = thisComp.layer("TXT_1");\nconst gap = thisComp.layer("CTRL").effect("Gap")(1);\nconst r = a.sourceRectAtTime(time, false);\nconst x = a.toComp([0, 0])[0];\nconst y = a.toComp([0, r.top + r.height])[1] + gap;\nconst me = sourceRectAtTime(time, false);\nconst s = transform.scale / 100;\nconst p = [x + anchorPoint[0] * s[0], y + (anchorPoint[1] - me.top) * s[1]];\nhasParent ? parent.fromComp(p) : p',
        // Bar N > Position: follows MOVE with N x Lag frames of delay; the number comes from the layer name
        follow: 'const lead = thisComp.layer("MOVE").transform.position;\nconst lag = thisComp.layer("CTRL").effect("Lag (frames)")(1);\nconst i = parseInt(thisLayer.name.replace(/\\D/g, ""), 10);\nconst d = i * Math.round(lag) * thisComp.frameDuration;\nvalue + (lead.valueAtTime(time - d) - lead.valueAtTime(0))',
        // DOT > Position: seamless idle, period in frames, noise sampled on a circle so frame 0 and frame T are the same point
        idle: 'const T = thisComp.layer("CTRL").effect("Idle (frames)")(1) * thisComp.frameDuration;\nconst amp = thisComp.layer("CTRL").effect("Idle Amp")(1);\nconst a = 2 * Math.PI * (time - inPoint) / T, r = 1.2;\nvalue + [noise([Math.cos(a) * r, Math.sin(a) * r, 0]), noise([Math.cos(a) * r, Math.sin(a) * r, 7])] * amp',
        // COUNT > Source Text
        counter: 'const end = 1250000;\nconst dur = thisComp.layer("CTRL").effect("Count (s)")(1);\nconst v = Math.round(ease(time - inPoint, 0, dur, 0, end));\nString(v).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",")',
        // any Fill Color: palette row picked by the Theme dropdown (1-based), column by the layer's role
        theme: function (role) { return 'const th = thisComp.layer("CTRL").effect("Theme")("Menu");\nconst pal = [\n  {bg: [0.96, 0.96, 0.94, 1], fg: [0.08, 0.09, 0.12, 1], accent: [0.93, 0.27, 0.13, 1]},\n  {bg: [0.08, 0.09, 0.12, 1], fg: [0.96, 0.96, 0.94, 1], accent: [0.25, 0.75, 1, 1]},\n  {bg: [0.93, 0.27, 0.13, 1], fg: [1, 1, 1, 1], accent: [0.08, 0.09, 0.12, 1]}\n];\npal[Math.min(Math.max(th, 1), pal.length) - 1].' + role; }
    };

    function shapeFill(l) { return l.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color"); }

    // rig(comp, {name, title, x, y}): builds the lower-third rig in an existing comp and returns a report of every expression set
    function rig(c, o) {
        o = o || {};
        var x = o.x || 160, y = o.y || 820, rep = [], i, b, txtFill;
        function set(p, code, label) { var r = AEK.expr.set(p, code, [0, c.duration / 2]); rep.push(label); return r; }
        var ctrl = AEK.build.nullLayer(c, "CTRL"); ctrl.guideLayer = true;
        AEK.expr.controls(ctrl, [
            { type: "slider", name: "Pad X", value: 32 }, { type: "slider", name: "Pad Y", value: 18 }, { type: "slider", name: "Gap", value: 14 },
            { type: "slider", name: "Lag (frames)", value: 3 }, { type: "slider", name: "Idle (frames)", value: Math.round(c.frameRate * 2) },
            { type: "slider", name: "Idle Amp", value: 12 }, { type: "slider", name: "Count (s)", value: 2 },
            { type: "dropdown", name: "Theme", items: ["Light", "Dark", "Brand"], value: 2 }
        ]);
        var move = AEK.build.nullLayer(c, "MOVE", { position: [x - 400, y - 120] });
        var mp = move.property("ADBE Transform Group").property("ADBE Position");
        AEK.motion.key(mp, 0, [x - 400, y - 120]); AEK.motion.key(mp, 0.6, [x, y - 120]); AEK.motion.ease(mp, 1, 0.1, 80); AEK.motion.ease(mp, 2, 80, 0.1);
        var t1 = AEK.text.add(c, o.name || "Ada Lovelace", { name: "TXT_1", font: "Helvetica-Bold", size: 64, fill: [1, 1, 1], justify: "left", position: [x, y] });
        var t2 = AEK.text.add(c, o.title || "Mathematician", { name: "TXT_2", font: "Helvetica", size: 36, fill: [1, 1, 1], justify: "left", position: [x, y + 60] });
        var box = AEK.build.shape(c, "BOX", { name: "plate", type: "rect", size: [100, 100], fill: [1, 1, 1] });
        box.moveAfter(t1);
        box.property("ADBE Transform Group").property("ADBE Anchor Point").setValue([0, 0]);
        box.parent = t1;
        box.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0]);
        var rect = function () { return box.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Shape - Rect"); };
        set(rect().property("ADBE Vector Rect Size"), CODE.boxSize, "BOX size");
        set(rect().property("ADBE Vector Rect Position"), CODE.boxPos, "BOX position");
        set(shapeFill(box), CODE.theme("bg"), "BOX fill");
        set(t2.property("ADBE Transform Group").property("ADBE Position"), CODE.line2, "TXT_2 position");
        for (i = 1; i <= 2; i++) {
            var tl = i === 1 ? t1 : t2;
            // Fill Color of a text layer without an animator: a text style expression. setFillColor takes [R, G, B];
            // setApplyFill(true) first, or a layer with Fill off shows no color. A text animator Fill Color runs after it and wins on its range.
            set(tl.property("ADBE Text Properties").property("ADBE Text Document"), 'const th = thisComp.layer("CTRL").effect("Theme")("Menu");\nconst fg = [[0.08, 0.09, 0.12], [0.96, 0.96, 0.94], [1, 1, 1]][Math.min(Math.max(th, 1), 3) - 1];\ntext.sourceText.style.setApplyFill(true).setFillColor(fg)', tl.name + " fill");
        }
        for (i = 1; i <= 5; i++) {
            b = AEK.build.shape(c, "Bar " + i, { type: "rect", size: [16, 90], fill: [1, 1, 1] }, { position: [x - 420 - i * 22, y - 30] });
            set(b.property("ADBE Transform Group").property("ADBE Position"), CODE.follow, b.name + " follow");
            set(shapeFill(b), CODE.theme("accent"), b.name + " fill");
        }
        var dot = AEK.build.shape(c, "DOT", { type: "ellipse", size: [28, 28], fill: [1, 1, 1] }, { position: [x - 60, y + 40] });
        set(dot.property("ADBE Transform Group").property("ADBE Position"), CODE.idle, "DOT idle");
        set(shapeFill(dot), CODE.theme("accent"), "DOT fill");
        var cnt = AEK.text.add(c, "0", { name: "COUNT", font: "Helvetica-Bold", size: 96, fill: [1, 1, 1], justify: "right", position: [c.width - x, 200] });
        set(cnt.property("ADBE Text Properties").property("ADBE Text Document"), CODE.counter, "COUNT text");
        return { expressions: rep.length, set: rep };
    }

    // renameLayer(comp, oldName, newName): renames a layer AND rewrites layer("oldName") in every expression of every comp.
    // A rename by script leaves the expression text unchanged, so references break.
    function renameLayer(c, oldName, newName) {
        var l = AEK.core.layer(c, oldName), comps = AEK.core.comps(), i, j, edited = [];
        var pat = 'layer("' + esc(oldName) + '")', rep = 'layer("' + esc(newName) + '")';
        l.name = newName;
        for (i = 0; i < comps.length; i++) {
            for (j = 1; j <= comps[i].numLayers; j++) {
                AEK.core.walk(comps[i].layer(j), function (p) {
                    if (p.propertyType !== PropertyType.PROPERTY) { return; }
                    var ex = ""; try { if (p.canSetExpression) { ex = p.expression; } } catch (e) { return; }
                    if (ex === "" || ex.indexOf(pat) < 0) { return; }
                    p.expression = ex.split(pat).join(rep);
                    edited.push(comps[i].name + " > " + comps[i].layer(j).name + " > " + p.name);
                });
            }
        }
        return { renamed: oldName + " -> " + newName, edited: edited };
    }

    // LEVEL: CTRL > Level slider. Normalized amplitude (Audio Floor to Audio Ceiling), rise over Attack frames, exponential
    // Release in frames (peak hold). It reads K = attack + ceil(4.6 x release) samples per frame: the tail is cut at 1 %.
    CODE.level = 'const a = thisComp.layer("Audio Amplitude").effect("Both Channels")(1);\nconst fl = effect("Audio Floor")(1), ce = effect("Audio Ceiling")(1);\nconst atk = Math.max(1, Math.round(effect("Attack (frames)")(1)));\nconst rel = Math.max(0.5, effect("Release (frames)")(1));\nconst fd = thisComp.frameDuration, K = atk + Math.ceil(rel * 4.6);\nlet m = 0;\nfor (let k = 0; k < K; k++) {\n  const n = clamp((a.valueAtTime(time - k * fd) - fl) / Math.max(ce - fl, 0.001), 0, 1);\n  const w = k < atk ? (k + 1) / atk : Math.exp(-(k - atk + 1) / rel);\n  m = Math.max(m, n * w);\n}\nm';

    // levelStats(prop, comp, from, to, low): the audio gates in numbers, on whole frames from..to. max and min; valleys =
    // local minima (a fall then a rise); valleysUnder = valleys under `low` (default 0.2); directionChanges = rises turning
    // to falls and back (about 2 per hit for a clean Level; raw amplitude many more). Read it on CTRL > Level and, to
    // compare, on "Audio Amplitude" > Both Channels.
    function levelStats(p, c, from, to, low) {
        var v = [], f, i, d0 = 0, d, changes = 0, valleys = 0, under = 0, mx = -1e9, mn = 1e9;
        low = (low === undefined) ? 0.2 : low;
        for (f = from; f <= to; f++) { v.push(p.valueAtTime(f * c.frameDuration, false)); }
        for (i = 0; i < v.length; i++) { mx = Math.max(mx, v[i]); mn = Math.min(mn, v[i]); }
        for (i = 1; i < v.length; i++) {
            d = v[i] > v[i - 1] + 1e-6 ? 1 : (v[i] < v[i - 1] - 1e-6 ? -1 : 0);
            if (d === 0) { continue; }
            if (d0 !== 0 && d !== d0) { changes++; if (d0 === -1) { valleys++; if (v[i - 1] < low) { under++; } } }
            d0 = d;
        }
        return { frames: v.length, max: Math.round(mx * 1000) / 1000, min: Math.round(mn * 1000) / 1000, valleys: valleys, valleysUnder: under,
            low: low, directionChanges: changes };
    }

    // audioLevel(comp, audioLayer, {floorPct: 25, ceilPct: 97, attack: 2, release: 6, beat, from, to (frames of the shot window), ctrl: "CTRL"}):
    // beat (frames between hits): sets the release to (beat - attack) / 2, so the Level falls under 0.2 before the next hit.
    // Convert Audio to Keyframes by its menu label (comp opened in the viewer, only the audio layer selected), floor and ceiling
    // from percentiles of Both Channels over the window, a guide null with the controls and the Level expression.
    // The "Audio Amplitude" layer is switched off; expressions still read it.
    function audioLevel(c, al, o) {
        o = o || {};
        var cmd = app.findMenuCommandId("Convert Audio to Keyframes"), i, k, vals = [], fd = c.frameDuration;
        if (!cmd) { throw new Error("audioLevel(): menu item Convert Audio to Keyframes not found"); }
        if (!al.hasAudio) { throw new Error("audioLevel(): layer '" + al.name + "' has no audio"); }
        c.openInViewer();
        for (i = 1; i <= c.numLayers; i++) { c.layer(i).selected = false; }
        al.selected = true;
        app.executeCommand(cmd);
        var amp = c.layer("Audio Amplitude");
        if (!amp) { throw new Error("audioLevel(): Convert Audio to Keyframes made no Audio Amplitude layer"); }
        var both = amp.property("ADBE Effect Parade").property("Both Channels").property(1);
        var f0 = o.from || 0, f1 = (o.to === undefined) ? Math.round(c.duration / fd) - 1 : o.to;
        for (k = f0; k <= f1; k++) { vals.push(both.valueAtTime(k * fd, false)); }
        vals.sort(function (a, b) { return a - b; });
        var fl = vals[Math.floor((vals.length - 1) * (o.floorPct === undefined ? 25 : o.floorPct) / 100)];
        var ce = vals[Math.floor((vals.length - 1) * (o.ceilPct === undefined ? 97 : o.ceilPct) / 100)];
        amp.enabled = false;
        var rel = o.release || (o.beat ? Math.max(2, Math.round((o.beat - (o.attack || 2)) / 2 * 10) / 10) : 6);
        var ctrl = c.layer(o.ctrl || "CTRL") || AEK.build.nullLayer(c, o.ctrl || "CTRL", { position: [c.width / 2, c.height / 2] });
        ctrl.guideLayer = true;
        AEK.expr.controls(ctrl, [{ type: "slider", name: "Audio Floor", value: fl }, { type: "slider", name: "Audio Ceiling", value: ce },
            { type: "slider", name: "Attack (frames)", value: o.attack || 2 }, { type: "slider", name: "Release (frames)", value: rel },
            { type: "slider", name: "Level", value: 0 }]);
        AEK.expr.set(ctrl.property("ADBE Effect Parade").property("Level").property(1), CODE.level, [f0 * fd, f1 * fd]);
        return { ctrl: ctrl.name, floor: fl, ceiling: ce, release: rel, keys: both.numKeys, samples: vals.length };
    }

    return { probe: probe, compRect: compRect, margins: margins, atFrames: atFrames, seam: seam, lagFrames: lagFrames, timeEval: timeEval, levelStats: levelStats, CODE: CODE, rig: rig, renameLayer: renameLayer, audioLevel: audioLevel };
})();
