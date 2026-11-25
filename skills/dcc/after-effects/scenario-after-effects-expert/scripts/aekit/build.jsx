// aekit/build.jsx: create comps and layers with explicit settings. Requires core.jsx.
var AEK = AEK || {};
AEK.build = (function () {
    // comp(name, {width, height, fps, duration, bg:[r,g,b], pixelAspect, bin, reuse})
    function comp(name, o) {
        o = o || {};
        var existing = AEK.core.items(function (it) { return it instanceof CompItem && it.name === name; });
        if (existing.length) { if (o.reuse) { return existing[0]; } throw new Error("A comp named '" + name + "' already exists (pass reuse: true to get it)"); }
        var c = app.project.items.addComp(name, o.width || 1920, o.height || 1080, o.pixelAspect || 1, o.duration || 10, o.fps || 30);
        if (o.bg) { c.bgColor = o.bg; }
        // renderer: "classic" (ADBE Advanced 3d, what a new comp starts on), "advanced" (ADBE Calder), "c4d" (ADBE Ernst), or a match name
        if (o.renderer) { c.renderer = ({ classic: "ADBE Advanced 3d", advanced: "ADBE Calder", c4d: "ADBE Ernst" })[o.renderer] || o.renderer; }
        if (o.bin) { c.parentFolder = (typeof o.bin === "string") ? AEK.core.bin(o.bin) : o.bin; }
        return c;
    }
    function solid(c, name, color, o) {
        o = o || {};
        var l = c.layers.addSolid(color || [0, 0, 0], name, o.width || c.width, o.height || c.height, c.pixelAspect, o.duration || c.duration);
        if (o.adjustment) { l.adjustmentLayer = true; }
        return l;
    }
    function adjustment(c, name) { return solid(c, name || "Adjustment", [1, 1, 1], { adjustment: true }); }
    function nullLayer(c, name, o) {
        o = o || {};
        var l = c.layers.addNull(c.duration);
        l.name = name || "Null";
        if (o.threeD) { l.threeDLayer = true; }
        if (o.position) { l.property("ADBE Transform Group").property("ADBE Position").setValue(o.position); }
        return l;
    }
    // shapeGroup(layer, spec): spec {name, type: "rect"|"ellipse"|"star"|"path", size:[w,h], roundness, position:[x,y] (inside the group),
    //   points, outerRadius, innerRadius, vertices, inTangents, outTangents, closed,
    //   fill:[r,g,b] | null, stroke:{color:[r,g,b], width, cap:"butt"|"round"|"projecting", join:"miter"|"round"|"bevel"}, trim:{start, end, offset}}
    function shapeGroup(l, s) {
        var root = l.property("ADBE Root Vectors Group"), g = root.addProperty("ADBE Vector Group"), name = s.name || "Shape";
        var gc = l.property("ADBE Root Vectors Group").property(root.numProperties).property("ADBE Vectors Group"), p, sh, st, tr, i;
        root.property(root.numProperties).name = name;
        if (s.type === "ellipse") {
            p = gc.addProperty("ADBE Vector Shape - Ellipse");
            p.property("ADBE Vector Ellipse Size").setValue(s.size || [200, 200]);
            if (s.position) { p.property("ADBE Vector Ellipse Position").setValue(s.position); }
        } else if (s.type === "star") {
            p = gc.addProperty("ADBE Vector Shape - Star");
            p.property("ADBE Vector Star Points").setValue(s.points || 5);
            p.property("ADBE Vector Star Outer Radius").setValue(s.outerRadius || 100);
            if (s.innerRadius !== undefined) { p.property("ADBE Vector Star Inner Radius").setValue(s.innerRadius); }
            if (s.position) { p.property("ADBE Vector Star Position").setValue(s.position); }
        } else if (s.type === "path") {
            sh = new Shape();
            sh.vertices = s.vertices;
            if (s.inTangents) { sh.inTangents = s.inTangents; }
            if (s.outTangents) { sh.outTangents = s.outTangents; }
            sh.closed = !!s.closed;
            p = gc.addProperty("ADBE Vector Shape - Group");
            p.property("ADBE Vector Shape").setValue(sh);
        } else {
            p = gc.addProperty("ADBE Vector Shape - Rect");
            p.property("ADBE Vector Rect Size").setValue(s.size || [200, 200]);
            if (s.roundness) { p.property("ADBE Vector Rect Roundness").setValue(s.roundness); }
            if (s.position) { p.property("ADBE Vector Rect Position").setValue(s.position); }
        }
        // operators act on everything above them in the group: Trim Paths goes after the path, before the paint
        gc = root.property(root.numProperties).property("ADBE Vectors Group");
        if (s.trim) {
            tr = gc.addProperty("ADBE Vector Filter - Trim");
            if (s.trim.start !== undefined) { tr.property("ADBE Vector Trim Start").setValue(s.trim.start); }
            if (s.trim.end !== undefined) { tr.property("ADBE Vector Trim End").setValue(s.trim.end); }
            if (s.trim.offset !== undefined) { tr.property("ADBE Vector Trim Offset").setValue(s.trim.offset); }
        }
        gc = root.property(root.numProperties).property("ADBE Vectors Group");
        if (s.stroke) {
            st = gc.addProperty("ADBE Vector Graphic - Stroke");
            st.property("ADBE Vector Stroke Color").setValue([s.stroke.color[0], s.stroke.color[1], s.stroke.color[2], 1]);
            st.property("ADBE Vector Stroke Width").setValue(s.stroke.width || 4);
            if (s.stroke.cap) { st.property("ADBE Vector Stroke Line Cap").setValue({ butt: 1, round: 2, projecting: 3 }[s.stroke.cap]); }
            if (s.stroke.join) { st.property("ADBE Vector Stroke Line Join").setValue({ miter: 1, round: 2, bevel: 3 }[s.stroke.join]); }
        }
        gc = root.property(root.numProperties).property("ADBE Vectors Group");
        if (s.fill) {
            gc.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue([s.fill[0], s.fill[1], s.fill[2], 1]);
        }
        // after addProperty every earlier reference into this layer is invalid: return a fresh one
        return l.property("ADBE Root Vectors Group").property(root.numProperties);
    }
    function shape(c, name, spec, o) {
        o = o || {};
        var l = c.layers.addShape();
        l.name = name;
        if (spec instanceof Array) { for (var i = 0; i < spec.length; i++) { shapeGroup(l, spec[i]); } } else if (spec) { shapeGroup(l, spec); }
        if (o.position) { l.property("ADBE Transform Group").property("ADBE Position").setValue(o.position); }
        return l;
    }
    // effect(layer, matchName, {propMatchNameOrName: value}, name): refuses effects that are not installed
    function effect(l, matchName, props, name) {
        var fx = l.property("ADBE Effect Parade"), e, k, p, idx;
        if (!fx.canAddProperty(matchName)) { throw new Error("Effect '" + matchName + "' cannot be added to '" + l.name + "' (not installed, or wrong match name)"); }
        e = fx.addProperty(matchName);
        idx = e.propertyIndex;
        if (name) { e.name = name; }
        for (k in props) {
            if (!props.hasOwnProperty(k)) { continue; }
            p = l.property("ADBE Effect Parade").property(idx).property(k);
            if (!p) { throw new Error("Effect '" + matchName + "' has no property '" + k + "'"); }
            p.setValue(props[k]);
        }
        return l.property("ADBE Effect Parade").property(idx);
    }
    // effectProps(layer, effectIndexOrName): [{index, name, matchName, value}] to discover what an effect exposes
    function effectProps(l, which) {
        var e = l.property("ADBE Effect Parade").property(which), out = [], i, p, v;
        for (i = 1; i <= e.numProperties; i++) {
            p = e.property(i); v = null;
            try { if (p.propertyType === PropertyType.PROPERTY && p.propertyValueType !== PropertyValueType.NO_VALUE && p.propertyValueType !== PropertyValueType.CUSTOM_VALUE) { v = p.value; } } catch (er) {}
            out.push({ index: i, name: p.name, matchName: p.matchName, value: v });
        }
        return out;
    }
    // parent(child, parentLayer, jump): default keeps the child where it is on screen; jump = true moves it into the parent's space
    function parent(child, parentLayer, jump) {
        if (jump) { child.setParentWithJump(parentLayer); } else { child.parent = parentLayer; }
        return child;
    }
    // matte(layer, matteLayer, "alpha"|"alphaInverted"|"luma"|"lumaInverted"): any layer in the comp can be the matte (23.0+)
    function matte(l, m, mode) {
        var map = { alpha: TrackMatteType.ALPHA, alphaInverted: TrackMatteType.ALPHA_INVERTED, luma: TrackMatteType.LUMA, lumaInverted: TrackMatteType.LUMA_INVERTED };
        l.setTrackMatte(m, map[mode || "alpha"]);
        return { layer: l.name, matte: l.trackMatteLayer.name, matteVisible: m.enabled };
    }
    // precompose(comp, [layer indices], name, moveAllAttributes): returns the new comp. Layer references taken before are invalid.
    function precompose(c, indices, name, moveAll) {
        return c.layers.precompose(indices, name, moveAll === undefined ? true : moveAll);
    }
    // anchor(layer, ax, ay, t): move the anchor point to a fraction of the layer bounds (0.5, 0.5 = center; 0.5, 1 = bottom center)
    // without moving the layer on screen. 2D layers with no keyframes on Anchor Point or Position.
    function anchor(l, ax, ay, t) {
        var tg = l.property("ADBE Transform Group"), ap = tg.property("ADBE Anchor Point"), pp = tg.property("ADBE Position");
        if (ap.numKeys || pp.numKeys) { throw new Error("anchor(): '" + l.name + "' has keyframes on Anchor Point or Position"); }
        var r = l.sourceRectAtTime(t || 0, false), a0 = ap.value, p0 = pp.value, sc = tg.property("ADBE Scale").value;
        var rot = tg.property("ADBE Rotate Z").value * Math.PI / 180;
        var a1 = [r.left + r.width * ax, r.top + r.height * ay];
        var dx = (a1[0] - a0[0]) * sc[0] / 100, dy = (a1[1] - a0[1]) * sc[1] / 100;
        ap.setValue([a1[0], a1[1]]);
        pp.setValue([p0[0] + dx * Math.cos(rot) - dy * Math.sin(rot), p0[1] + dx * Math.sin(rot) + dy * Math.cos(rot)]);
        return { anchor: ap.value, position: pp.value, bounds: [r.left, r.top, r.width, r.height] };
    }
    // camera(comp, name, {focalLength (mm, on a 36 mm film back), position:[x,y,z], pointOfInterest:[x,y,z]})
    function camera(c, name, o) {
        o = o || {};
        var l = c.layers.addCamera(name || "Camera", [c.width / 2, c.height / 2]);
        var zoom = c.width * (o.focalLength || 50) / 36;
        l.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(zoom);
        l.property("ADBE Transform Group").property("ADBE Position").setValue(o.position || [c.width / 2, c.height / 2, -zoom]);
        if (o.pointOfInterest) { l.property("ADBE Transform Group").property("ADBE Anchor Point").setValue(o.pointOfInterest); }
        return l;
    }
    return { comp: comp, solid: solid, adjustment: adjustment, nullLayer: nullLayer, shape: shape, shapeGroup: shapeGroup, effect: effect,
        effectProps: effectProps, parent: parent, matte: matte, precompose: precompose, anchor: anchor, camera: camera };
})();
