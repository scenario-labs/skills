// shapes.jsx: shape layer helpers under AEX.shapes. Load with `ae.py run job.jsx --lib <this file>`. ES3. Requires the AEK kit.
var AEX = AEX || {};
AEX.shapes = (function () {
    // contents(layer, path): fresh "Contents" group. path = [] for the layer root, [groupNameOrIndex, ...] for nested groups.
    // Always re-fetch: after any addProperty, earlier references into the layer are invalid.
    function contents(l, path) {
        var c = l.property("ADBE Root Vectors Group"), i, g;
        path = path || [];
        for (i = 0; i < path.length; i++) {
            g = c.property(path[i]);
            if (!g || g.matchName !== "ADBE Vector Group") { throw new Error("No shape group '" + path[i] + "' in '" + l.name + "'"); }
            c = g.property("ADBE Vectors Group");
        }
        return c;
    }
    // add(layer, path, matchName, name): appends at the END of that Contents and returns a fresh reference
    function add(l, path, matchName, name) {
        var c = contents(l, path), p, idx;
        if (!c.canAddProperty(matchName)) { throw new Error("Cannot add '" + matchName + "' under " + (path.length ? path.join(" > ") : "Contents")); }
        p = c.addProperty(matchName);
        idx = p.propertyIndex;
        if (name) { contents(l, path).property(idx).name = name; }
        return contents(l, path).property(idx);
    }
    // group(layer, path, name): new empty group, returns the path to its Contents
    function group(l, path, name) {
        add(l, path, "ADBE Vector Group", name);
        return (path || []).concat([name]);
    }
    // set(prop, {matchName: value}): sets several leaves by match name
    function set(p, values) {
        var k, q;
        for (k in values) {
            if (!Object.prototype.hasOwnProperty.call(values, k)) { continue; }
            q = p.property(k);
            if (!q) { throw new Error("'" + p.matchName + "' has no property '" + k + "'"); }
            q.setValue(values[k]);
        }
        return p;
    }
    function makeShape(vertices, inT, outT, closed) {
        var s = new Shape(), n = vertices.length, z = [], i;
        for (i = 0; i < n; i++) { z.push([0, 0]); }
        s.vertices = vertices; s.inTangents = inT || z; s.outTangents = outT || z; s.closed = !!closed;
        return s;
    }
    // path(layer, groupPath, vertices, inT, outT, closed, name): Bezier path item with a Shape value
    function path(l, gp, vertices, inT, outT, closed, name) {
        var p = add(l, gp, "ADBE Vector Shape - Group", name);
        p.property("ADBE Vector Shape").setValue(makeShape(vertices, inT, outT, closed));
        return p;
    }
    // stroke(layer, groupPath, {color, width, cap, join}): cap/join names as in the GUI
    function stroke(l, gp, o) {
        var s = add(l, gp, "ADBE Vector Graphic - Stroke", o.name);
        s.property("ADBE Vector Stroke Color").setValue(o.color || [1, 1, 1, 1]);
        s.property("ADBE Vector Stroke Width").setValue(o.width === undefined ? 2 : o.width);
        s.property("ADBE Vector Stroke Line Cap").setValue({ butt: 1, round: 2, projecting: 3 }[o.cap || "round"]);
        s.property("ADBE Vector Stroke Line Join").setValue({ miter: 1, round: 2, bevel: 3 }[o.join || "round"]);
        return s;
    }
    function fill(l, gp, color, name) {
        var f = add(l, gp, "ADBE Vector Graphic - Fill", name);
        f.property("ADBE Vector Fill Color").setValue(color || [1, 1, 1, 1]);
        return f;
    }
    // dump(layerOrGroup): flat list of every property under Contents: depth, name, matchName, value for simple leaves
    function dump(base) {
        var out = [], root = base.matchName === "ADBE Vector Layer" ? base.property("ADBE Root Vectors Group") : base;
        AEK.core.walk(root, function (p, d) {
            var row = { d: d, name: p.name, mn: p.matchName }, v;
            if (p.propertyType === PropertyType.PROPERTY) {
                try {
                    if (p.propertyValueType === PropertyValueType.SHAPE) { v = "Shape(" + p.value.vertices.length + (p.value.closed ? " closed)" : " open)"); }
                    else if (p.propertyValueType !== PropertyValueType.NO_VALUE && p.propertyValueType !== PropertyValueType.CUSTOM_VALUE) { v = p.value; }
                    else { v = "custom"; }
                } catch (e) { v = "unreadable"; }
                row.v = v;
                if (p.expression) { row.expr = p.expression; }
                if (p.numKeys) { row.keys = p.numKeys; }
            }
            out.push(row);
        });
        return out;
    }
    // order(layer): per Contents level, the sequence of item kinds; flags paint above an operator (operator then has nothing to act on for that paint)
    var PATHS = { "ADBE Vector Shape - Group": 1, "ADBE Vector Shape - Rect": 1, "ADBE Vector Shape - Ellipse": 1, "ADBE Vector Shape - Star": 1 };
    var PAINT = { "ADBE Vector Graphic - Fill": 1, "ADBE Vector Graphic - Stroke": 1, "ADBE Vector Graphic - G-Fill": 1, "ADBE Vector Graphic - G-Stroke": 1 };
    function kind(mn) {
        if (PATHS[mn]) { return "path"; }
        if (PAINT[mn]) { return "paint"; }
        if (mn === "ADBE Vector Group") { return "group"; }
        if (mn.indexOf("ADBE Vector Filter - ") === 0) { return "op"; }
        return "other";
    }
    function order(l) {
        var out = [];
        function visit(c, label) {
            var seq = [], i, p, k, sawPaint = false, firstPaint = "", warn = [];
            for (i = 1; i <= c.numProperties; i++) {
                p = c.property(i); k = kind(p.matchName);
                seq.push(p.name);
                if (k === "paint" && !sawPaint) { sawPaint = true; firstPaint = p.name; }
                if (k === "op" && sawPaint && p.matchName !== "ADBE Vector Filter - Repeater") { warn.push(p.name + " sits below " + firstPaint + ": it still reshapes paths, but check intent"); }
                if (k === "path" && sawPaint) { warn.push(p.name + " sits below " + firstPaint + ": that paint does not draw it"); }
                if (k === "group") { visit(p.property("ADBE Vectors Group"), label + " > " + p.name); }
            }
            out.push({ where: label, items: seq, warnings: warn });
        }
        visit(l.property("ADBE Root Vectors Group"), l.name);
        return out;
    }
    // resample(shape, n): returns a Shape with n vertices, inserting points on the longest straight segments.
    // Straight-segment only (tangents zeroed): use it on polygons and icons built from lines.
    function resample(s, n) {
        var v = s.vertices.slice(0), i, best, bi, d, a, b, m, closed = s.closed;
        while (v.length < n) {
            best = -1; bi = 0;
            for (i = 0; i < (closed ? v.length : v.length - 1); i++) {
                a = v[i]; b = v[(i + 1) % v.length];
                d = (a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]);
                if (d > best) { best = d; bi = i; }
            }
            a = v[bi]; b = v[(bi + 1) % v.length]; m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
            v.splice(bi + 1, 0, m);
        }
        return makeShape(v, null, null, closed);
    }
    // firstVertex(shape, k): rotates a closed shape so vertex k becomes vertex 0 (the scripted "Set First Vertex")
    function firstVertex(s, k) {
        function rot(a) { return a.slice(k).concat(a.slice(0, k)); }
        return makeShape(rot(s.vertices), rot(s.inTangents), rot(s.outTangents), s.closed);
    }
    // reverse(shape): reverses the path direction (swaps in and out tangents)
    function reverse(s) {
        var v = s.vertices.slice(0).reverse(), it = s.outTangents.slice(0).reverse(), ot = s.inTangents.slice(0).reverse();
        return makeShape(v, it, ot, s.closed);
    }
    // lottie(comp): features a Lottie export drops or changes, per the LottieFiles compatibility matrix and the expert notes.
    // Nested comps are audited too (each once); `where` is the layer path from the top comp, "Outer > Precomp > layer".
    function lottie(c) {
        var f = [], seen = {};
        function audit(cc, pre) {
            var i, l, at;
            function flag(sev, where, what) { f.push({ severity: sev, where: pre + where, what: what }); }
            for (i = 1; i <= cc.numLayers; i++) {
                l = cc.layer(i);
                if (!l.enabled) { flag("info", l.name, "layer switched off: confirm the exporter skips hidden layers, or delete it in the export copy"); continue; }
                at = layerChecks(l, flag);
                if (at && !seen[at.id]) { seen[at.id] = true; audit(at, pre + l.name + " > "); }
            }
        }
        seen[c.id] = true;
        audit(c, "");
        return f;
    }
    // layerChecks(layer, flag): the per-layer Lottie checks; returns the layer's source comp, or null
    function layerChecks(l, flag) {
        var fx, sub = null;
        if (l instanceof CameraLayer) { flag("drop", l.name, "camera layer"); return null; }
        if (l instanceof LightLayer) { flag("drop", l.name, "light layer"); return null; }
        if (l.guideLayer) { flag("drop", l.name, "guide layer (skipped by design)"); }
        if (l.adjustmentLayer) { flag("drop", l.name, "adjustment layer"); }
        if (l.threeDLayer) { flag("partial", l.name, "3D layer: Z kept, X/Y rotation and Z order limited"); }
        if (l.hasAudio && !l.hasVideo) { flag("drop", l.name, "audio layer"); }
        if (l.hasTrackMatte) { flag(l.trackMatteType === TrackMatteType.ALPHA || l.trackMatteType === TrackMatteType.ALPHA_INVERTED ? "ok" : "partial", l.name, "track matte " + AEK.core.enumName(TrackMatteType, l.trackMatteType)); }
        if (l.timeRemapEnabled) { flag("partial", l.name, "time remap: linear only"); }
        if (l instanceof AVLayer && l.source && l.source.mainSource && !(l.source instanceof CompItem) && !(l.source.mainSource instanceof SolidSource)) {
            if (l.source.mainSource.isStill) { flag("size", l.name, "raster or vector footage: embedded as base64 PNG, convert vector art to shapes"); }
            else if (l.hasVideo) { flag("drop", l.name, "video footage"); }
        }
        // basic text is supported by the matrix; animators and text on a path are partial
        if (l.matchName === "ADBE Text Layer") {
            var tp = l.property("ADBE Text Properties"), an = tp.property("ADBE Text Animators"), po = tp.property("ADBE Text Path Options"), tpath = po ? po.property("ADBE Text Path") : null;
            flag("check", l.name, "text layer (basic, supported): the font is referenced by name and must exist in the runtime; for a custom font run Create Shapes from Text or ship the font");
            if (an && an.numProperties > 0) { flag("partial", l.name, "text animators: per-character animators partial, complex range selectors may drop"); }
            if (tpath && tpath.value > 0) { flag("partial", l.name, "text on a path: partial"); }
        }
        fx = l.property("ADBE Effect Parade");
        if (fx) { for (var e = 1; e <= fx.numProperties; e++) { if (!fx.property(e).enabled) { continue; } flag(fx.property(e).matchName === "ADBE Drop Shadow" || fx.property(e).matchName === "ADBE Gaussian Blur 2" || fx.property(e).matchName === "ADBE Fill" || fx.property(e).matchName === "ADBE Tint" ? "partial" : "drop", l.name, "effect " + fx.property(e).name + " (" + fx.property(e).matchName + ")"); } }
        AEK.core.walk(l, function (p) {
            var mn = p.matchName;
            if (p.propertyType === PropertyType.PROPERTY && p.canSetExpression && p.expressionEnabled && p.expression) { flag("drop", l.name, "expression on " + p.name + ": bake to keyframes"); }
            if (mn === "ADBE Vector Filter - Merge") { flag("check", l.name, "Merge Paths: not in the Lottie matrix, test in the target player or flatten the boolean"); }
            if (mn === "ADBE Vector Filter - Offset" || mn === "ADBE Vector Filter - PB" || mn === "ADBE Vector Filter - Twist" || mn === "ADBE Vector Filter - Roughen" || mn === "ADBE Vector Filter - Wiggler" || mn === "ADBE Vector Filter - Zigzag" || mn === "ADBE Vector Filter - RC") { flag("check", l.name, p.name + ": not in the Lottie matrix, test in the target player or bake the path"); }
            if (mn === "ADBE Vector Graphic - G-Fill" || mn === "ADBE Vector Graphic - G-Stroke") { flag("partial", l.name, p.name + ": two-stop linear is safest"); }
            // taper is active when a length is above 0 (the widths default to 0, which means a full point)
            if (mn === "ADBE Vector Stroke Taper" && p.property("ADBE Vector Taper Start Length") && (p.property("ADBE Vector Taper Start Length").value > 0 || p.property("ADBE Vector Taper End Length").value > 0)) { flag("check", l.name, "stroke taper in use: not in the Lottie matrix"); }
            if (mn === "ADBE Vector Stroke Wave" && p.property("ADBE Vector Taper Wave Amount") && p.property("ADBE Vector Taper Wave Amount").value !== 0) { flag("check", l.name, "stroke wave in use: not in the Lottie matrix"); }
            if (mn === "ADBE Mask Atom" && p.property("ADBE Mask Feather") && (p.property("ADBE Mask Feather").value[0] || p.property("ADBE Mask Feather").value[1])) { flag("check", l.name, "feathered mask"); }
        });
        if (l instanceof AVLayer && l.source instanceof CompItem) { sub = l.source; }
        return sub;
    }
    // chainScale(layer, t): on-screen length of one layer pixel through the layer and its parents, as {ok, s, why}.
    // Each 2D layer maps v to rotate(scale(v)), child first; composed this way the kit matched toComp to 1e-13 px.
    // A stroke has one on-screen width only when the composed map is a uniform scale: non-uniform scale anywhere
    // that survives the chain, a 3D layer, or a camera or light parent gives ok false.
    function mul2(A, B) { return [[A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]], [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]]; }
    function lin2(sx, sy, deg) { var a = deg * Math.PI / 180, co = Math.cos(a), si = Math.sin(a); return [[co * sx, -si * sy], [si * sx, co * sy]]; }
    // singular values of a 2x2 map: the longest and shortest stretch of a unit vector
    function stretch(A) {
        var e = A[0][0] * A[0][0] + A[0][1] * A[0][1] + A[1][0] * A[1][0] + A[1][1] * A[1][1], d = Math.abs(A[0][0] * A[1][1] - A[0][1] * A[1][0]);
        var hi = Math.sqrt((e + Math.sqrt(Math.max(0, e * e - 4 * d * d))) / 2);
        return [hi, hi > 0 ? d / hi : 0];
    }
    function chainScale(layer, t) {
        var A = [[1, 0], [0, 1]], cur = layer, tg, k, r, sv;
        while (cur) {
            // ShapeLayer and TextLayer are not `instanceof AVLayer` in 27.0: test for the two kinds without a 2D scale
            if (cur instanceof CameraLayer || cur instanceof LightLayer) { return { ok: false, s: null, why: "camera or light in the parent chain" }; }
            if (cur.threeDLayer) { return { ok: false, s: null, why: "3D layer '" + cur.name + "' in the chain" }; }
            tg = cur.property("ADBE Transform Group");
            k = tg.property("ADBE Scale").valueAtTime(t, false); r = tg.property("ADBE Rotate Z").valueAtTime(t, false);
            A = mul2(lin2(k[0] / 100, k[1] / 100, r), A);
            cur = cur.parent;
        }
        sv = stretch(A);
        if (sv[0] - sv[1] > 1e-4 * Math.max(sv[0], 1e-9)) { return { ok: false, s: null, why: "non-uniform scale (" + Math.round(sv[1] * 1000) / 1000 + " to " + Math.round(sv[0] * 1000) / 1000 + ")" }; }
        return { ok: true, s: sv[0], why: "" };
    }
    // strokes(comp, {width, cap, join, scaleAware, time}): every Stroke and Gradient Stroke in the comp's shape layers against a house style.
    // Reports the width after any expression and the on-screen width through layer and parent Scale and Rotation at `time`
    // (default 0). Group Scale is not included. onScreen is null when the chain is not a uniform 2D scale; with scaleAware
    // that row fails: rebuild the geometry at delivery size.
    function strokes(c, want) {
        var out = [], i, l, sc, caps = { 1: "butt", 2: "round", 3: "projecting" }, joins = { 1: "miter", 2: "round", 3: "bevel" };
        want = want || {};
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (l.matchName !== "ADBE Vector Layer") { continue; }
            sc = chainScale(l, want.time || 0);
            AEK.core.walk(l.property("ADBE Root Vectors Group"), function (p) {
                if (p.matchName !== "ADBE Vector Graphic - Stroke" && p.matchName !== "ADBE Vector Graphic - G-Stroke") { return; }
                // width after the expression (the constant on-screen width expression stores a small value); time = want.time or 0
                var wp = p.property("ADBE Vector Stroke Width"), driven = !!(wp.expression && wp.expressionEnabled);
                var w = wp.valueAtTime(want.time || 0, false), cap = caps[p.property("ADBE Vector Stroke Line Cap").value],
                    join = joins[p.property("ADBE Vector Stroke Line Join").value], onScreen = sc.ok ? w * sc.s : null, issues = [];
                if (want.scaleAware && !sc.ok) { issues.push("on-screen width not measurable: " + sc.why + "; rebuild at delivery size"); }
                else if (want.width !== undefined && Math.abs((want.scaleAware ? onScreen : w) - want.width) > 0.01) { issues.push("width " + Math.round((want.scaleAware ? onScreen : w) * 100) / 100); }
                if (want.cap && cap !== want.cap) { issues.push("cap " + cap); }
                if (want.join && join !== want.join) { issues.push("join " + join); }
                if (driven && wp.expressionError) { issues.push("width expression error: " + wp.expressionError); }
                out.push({ layer: l.name, stroke: p.name, width: Math.round(w * 1000) / 1000, onScreen: onScreen === null ? null : Math.round(onScreen * 100) / 100, expression: driven, cap: cap, join: join, issues: issues });
            });
        }
        return out;
    }
    // ripple(comp, name, {center, r0, spacing, copies, width, color, ringsPerSecond, fade, once, matte}): evenly spaced rings that
    // travel outward. Offset Paths (Amount = spacing, Copies) gives equal spacing (Repeater Scale gives geometric spacing).
    // Default: Copy Offset driven by (time * rate) % 1, a seamless endless loop. once: {start, frames, travel} keys Copy Offset
    // 0 -> travel (default: copies, so every ring leaves past the rim) from frame `start` over `frames`, eased out, no expression.
    // Repeater opacity follows the copy index, never the radius, so the fade by radius is an alpha matte. matte: "solid" (default:
    // a solid with an outer feathered mask and an inner subtracted one), "shape" (a shape layer ring blurred by `fade` px, for
    // shape-layers-only work) or "none". A mask feather spreads the edge over `feather` px on each side of the path (measured).
    function ripple(c, name, o) {
        o = o || {};
        var ctr = o.center || [c.width / 2, c.height / 2], r0 = o.r0 || 60, sp = o.spacing || 40, n = o.copies || 8, fade = o.fade || sp, mt = o.matte || "solid";
        var l = c.layers.addShape(); l.name = name;
        l.property("ADBE Transform Group").property("ADBE Position").setValue(ctr);
        var g = group(l, [], "rings");
        set(add(l, g, "ADBE Vector Shape - Ellipse", "base"), { "ADBE Vector Ellipse Size": [2 * r0, 2 * r0] });
        set(add(l, g, "ADBE Vector Filter - Offset", "spread"), { "ADBE Vector Offset Amount": sp, "ADBE Vector Offset Copies": n });
        stroke(l, g, { color: o.color || [1, 1, 1, 1], width: o.width || 4 });
        var co = function () { return contents(l, g).property("spread").property("ADBE Vector Offset Copy Offset"); }, loopFrames = null;
        if (o.once) {
            var f0 = o.once.start || 0, nf = o.once.frames || 30, tv = o.once.travel === undefined ? n : o.once.travel;
            AEK.motion.key(co(), f0 * c.frameDuration, 0); AEK.motion.key(co(), (f0 + nf) * c.frameDuration, tv);
            AEK.motion.bezier(co(), 1, 2, [0.2, 0, 0, 1]);
        } else {
            AEK.expr.set(co(), "(time * " + (o.ringsPerSecond || 1) + ") % 1");
            loopFrames = Math.round(c.frameRate / (o.ringsPerSecond || 1));
        }
        // outermost ring at Copy Offset 1 sits at r0 + n * sp; innermost at Copy Offset 0 at r0
        var rMax = r0 + n * sp, m = null;
        if (mt === "solid") {
            m = AEK.build.solid(c, name + "_fade", [1, 1, 1]);
            // outer ring of the band, then the inner disc subtracted; both feathered by `fade` (kit mask builder)
            AEK.build.mask(m, { ellipse: [ctr[0] - (rMax - fade), ctr[1] - (rMax - fade), 2 * (rMax - fade), 2 * (rMax - fade)], feather: fade });
            AEK.build.mask(m, { ellipse: [ctr[0] - (r0 + fade), ctr[1] - (r0 + fade), 2 * (r0 + fade), 2 * (r0 + fade)], feather: fade, mode: "subtract" });
        } else if (mt === "shape") {
            m = c.layers.addShape(); m.name = name + "_fade";
            m.property("ADBE Transform Group").property("ADBE Position").setValue(ctr);
            var mg = group(m, [], "band");
            set(add(m, mg, "ADBE Vector Shape - Ellipse", "outer"), { "ADBE Vector Ellipse Size": [2 * (rMax - fade), 2 * (rMax - fade)] });
            set(add(m, mg, "ADBE Vector Shape - Ellipse", "inner"), { "ADBE Vector Ellipse Size": [2 * (r0 + fade), 2 * (r0 + fade)] });
            set(add(m, mg, "ADBE Vector Filter - Merge", "cut"), { "ADBE Vector Merge Type": 3 });
            fill(m, mg, [1, 1, 1, 1]);
            AEK.build.effect(m, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": fade, "ADBE Gaussian Blur 2-0003": 0 }, "fade");
        }
        if (m) { l.setTrackMatte(m, TrackMatteType.ALPHA); }
        return { layer: l.name, matte: m ? m.name : null, rMin: r0, rMax: rMax, spacing: sp, loopFrames: loopFrames };
    }
    return { ripple: ripple, contents: contents, add: add, group: group, set: set, makeShape: makeShape, path: path, stroke: stroke, fill: fill,
        dump: dump, order: order, resample: resample, firstVertex: firstVertex, reverse: reverse, lottie: lottie, strokes: strokes };
})();
