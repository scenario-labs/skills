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
            if (!values.hasOwnProperty(k)) { continue; }
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
    // lottie(comp): features a Lottie export drops or changes, per the LottieFiles compatibility matrix and the expert notes
    function lottie(c) {
        var f = [], i, l, fx;
        function flag(sev, where, what) { f.push({ severity: sev, where: where, what: what }); }
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!l.enabled) { flag("info", l.name, "layer switched off: confirm the exporter skips hidden layers, or delete it in the export copy"); continue; }
            if (l instanceof CameraLayer) { flag("drop", l.name, "camera layer"); continue; }
            if (l instanceof LightLayer) { flag("drop", l.name, "light layer"); continue; }
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
        }
        return f;
    }
    // strokes(comp, {width, cap, join, scaleAware}): every Stroke and Gradient Stroke in the comp's shape layers against a house style.
    // Reports the on-screen width (stroke x layer and parent scale, measured with toComp at time 0) next to the stored width.
    function strokes(c, want) {
        var out = [], i, l, caps = { 1: "butt", 2: "round", 3: "projecting" }, joins = { 1: "miter", 2: "round", 3: "bevel" };
        want = want || {};
        function screenScale(layer) {
            var a = [0, 0], b = [1, 0], k, s = 1, cur = layer;
            while (cur) { k = cur.property("ADBE Transform Group").property("ADBE Scale").value; s *= Math.abs(k[0]) / 100; cur = cur.parent; }
            return s;
        }
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (l.matchName !== "ADBE Vector Layer") { continue; }
            AEK.core.walk(l.property("ADBE Root Vectors Group"), function (p) {
                if (p.matchName !== "ADBE Vector Graphic - Stroke" && p.matchName !== "ADBE Vector Graphic - G-Stroke") { return; }
                var w = p.property("ADBE Vector Stroke Width").value, cap = caps[p.property("ADBE Vector Stroke Line Cap").value],
                    join = joins[p.property("ADBE Vector Stroke Line Join").value], onScreen = w * screenScale(l), issues = [];
                if (want.width !== undefined && Math.abs((want.scaleAware ? onScreen : w) - want.width) > 0.01) { issues.push("width " + (want.scaleAware ? onScreen : w)); }
                if (want.cap && cap !== want.cap) { issues.push("cap " + cap); }
                if (want.join && join !== want.join) { issues.push("join " + join); }
                if (p.property("ADBE Vector Stroke Width").expression && p.property("ADBE Vector Stroke Width").expressionEnabled) { issues.push("width driven by expression"); }
                out.push({ layer: l.name, stroke: p.name, width: w, onScreen: Math.round(onScreen * 100) / 100, cap: cap, join: join, issues: issues });
            });
        }
        return out;
    }
    return { contents: contents, add: add, group: group, set: set, makeShape: makeShape, path: path, stroke: stroke, fill: fill,
        dump: dump, order: order, resample: resample, firstVertex: firstVertex, reverse: reverse, lottie: lottie, strokes: strokes };
})();
