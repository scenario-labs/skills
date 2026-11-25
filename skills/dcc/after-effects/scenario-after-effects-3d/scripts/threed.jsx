// threed.jsx: AEX.threeD helpers for 3D scenes in After Effects 27.0. Requires the AEK kit (core, build, motion, expr).
// Load with: ae.py run job.jsx --lib skills/scenario-after-effects-3d/scripts/threed.jsx
var AEX = AEX || {};
AEX.threeD = (function () {
    // internal renderer names on 27.0: the name "ADBE Advanced 3d" is CLASSIC 3D; the Advanced 3D renderer is "ADBE Calder"
    var RENDERER = { classic: "ADBE Advanced 3d", advanced: "ADBE Calder", cinema4d: "ADBE Ernst" };
    function rendererName(c) { var k; for (k in RENDERER) { if (RENDERER.hasOwnProperty(k) && RENDERER[k] === c.renderer) { return k; } } return c.renderer; }
    // use(comp, "advanced"|"classic"|"cinema4d"): a new comp made by script is Classic 3D; set it before adding models
    function use(c, which) { c.renderer = RENDERER[which || "advanced"]; return rendererName(c); }
    // settable(group): every property of a group with its value and whether this renderer exposes it (hidden ones throw on setValue)
    function settable(g) {
        var out = [], i, p, v, ok;
        for (i = 1; i <= g.numProperties; i++) {
            p = g.property(i);
            if (p.propertyType !== PropertyType.PROPERTY) { out.push({ matchName: p.matchName, group: true }); continue; }
            try { v = p.value; } catch (e0) { v = null; }
            try { p.setValue(p.value); ok = true; } catch (e1) { ok = false; }
            out.push({ matchName: p.matchName, name: p.name, value: v, exposed: ok });
        }
        return out;
    }
    // fitModel(layer, comp, {height, x, floorY, z, rotateY}): anchor at the bottom center of the footprint, scale to a height in pixels,
    // stand it on floorY. sourceRectAtTime on a model is the front footprint at scale 100; it ignores rotation and scale.
    function fitModel(l, c, o) {
        o = o || {};
        var tg = l.property("ADBE Transform Group"), r = l.sourceRectAtTime(0, false);
        var h = o.height || c.height * 0.5, s = h / r.height * 100;
        tg.property("ADBE Anchor Point").setValue([r.left + r.width / 2, r.top + r.height, 0]);
        tg.property("ADBE Scale").setValue([s, s, s]);
        tg.property("ADBE Position").setValue([o.x === undefined ? c.width / 2 : o.x, o.floorY === undefined ? c.height * 0.75 : o.floorY, o.z || 0]);
        if (o.rotateY) { tg.property("ADBE Rotate Y").setValue(o.rotateY); }
        return { rect: [r.left, r.top, r.width, r.height], scale: s, widthPx: r.width * s / 100, heightPx: h };
    }
    // shadowCatcher(comp, floorY, {x, z, size, shadowColor}): a 3D white solid lying flat that shows only the shadows it receives
    function shadowCatcher(c, floorY, o) {
        o = o || {};
        var f = AEK.build.solid(c, o.name || "shadow catcher", [1, 1, 1], { width: o.size || 4000, height: o.size || 4000 });
        f.threeDLayer = true;
        var tg = f.property("ADBE Transform Group"), mo = f.property("ADBE Material Options Group");
        tg.property("ADBE Orientation").setValue([270, 0, 0]);
        tg.property("ADBE Position").setValue([o.x === undefined ? c.width / 2 : o.x, floorY, o.z || 0]);
        mo.property("ADBE Accepts Shadows").setValue(2);
        mo.property("ADBE Casts Shadows").setValue(0);
        if (o.shadowColor) { try { mo.property("ADBE Shadow Color").setValue(o.shadowColor); } catch (e) {} }
        return f;
    }
    // keyLight(comp, position, target, {type, intensity, cone, darkness, diffusion, color}): a shadow-casting spot (or parallel/point)
    function keyLight(c, pos, target, o) {
        o = o || {};
        var l = c.layers.addLight(o.name || "key", [c.width / 2, c.height / 2]);
        l.lightType = LightType[o.type || "SPOT"];
        l.property("ADBE Transform Group").property("ADBE Position").setValue(pos);
        if (target && l.lightType !== LightType.POINT) { l.property("ADBE Transform Group").property("ADBE Anchor Point").setValue(target); }
        var lo = l.property("ADBE Light Options Group");
        lo.property("ADBE Light Intensity").setValue(o.intensity || 100);
        if (o.color) { lo.property("ADBE Light Color").setValue(o.color); }
        if (l.lightType === LightType.SPOT) { lo.property("ADBE Light Cone Angle").setValue(o.cone || 70); }
        lo.property("ADBE Casts Shadows").setValue(1);
        lo.property("ADBE Light Shadow Darkness").setValue(o.darkness === undefined ? 60 : o.darkness);
        if (l.lightType !== LightType.PARALLEL) { lo.property("ADBE Light Shadow Diffusion").setValue(o.diffusion === undefined ? 15 : o.diffusion); }
        return l;
    }
    // envLight(comp, {intensity, source: footage item or null}): environment light; with a source, the source layer is added and hidden
    function envLight(c, o) {
        o = o || {};
        // a layer source in a Classic 3D comp crashed 27.0 twice at render (stack overflow): refuse it here
        if (o.source && c.renderer !== RENDERER.advanced) { throw new Error("envLight: set the comp to Advanced 3D (AEX.threeD.use) before giving the light a layer source"); }
        var l = c.layers.addLight(o.name || "environment", [c.width / 2, c.height / 2]);
        l.lightType = LightType.ENVIRONMENT;
        l.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(o.intensity || 100);
        if (o.source) {
            var s = c.layers.add(o.source); s.name = (o.name || "environment") + " source"; s.enabled = false;
            l.lightSource = s;
        }
        return l;
    }
    // orbitRig(comp, center, {focalLength, distance, height, tilt, from, to, push, start, end, influence}):
    // a 3D null at the subject carries the orbit (Y rotation); a one-node camera parented to it carries the push (its own Z)
    function orbitRig(c, center, o) {
        o = o || {};
        var rig = AEK.build.nullLayer(c, o.name || "cam rig"); rig.threeDLayer = true;
        rig.property("ADBE Transform Group").property("ADBE Position").setValue(center);
        var cam = c.layers.addCamera((o.name || "cam rig") + " camera", [c.width / 2, c.height / 2]);
        cam.autoOrient = AutoOrientType.NO_AUTO_ORIENT;
        var zoom = c.width * (o.focalLength || 50) / 36, d = o.distance || zoom, t0 = o.start || 0, t1 = o.end || c.duration, inf = o.influence || 50;
        cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(zoom);
        cam.parent = rig;
        var ct = cam.property("ADBE Transform Group"), rt = rig.property("ADBE Transform Group");
        ct.property("ADBE Rotate X").setValue(o.tilt === undefined ? -8 : o.tilt);
        AEK.motion.key(ct.property("ADBE Position"), t0, [0, -(o.height || 0), -d]);
        AEK.motion.key(ct.property("ADBE Position"), t1, [0, -(o.height || 0), -d + (o.push || 0)]);
        AEK.motion.key(rt.property("ADBE Rotate Y"), t0, o.from || 0);
        AEK.motion.key(rt.property("ADBE Rotate Y"), t1, o.to || 0);
        AEK.motion.ease(ct.property("ADBE Position"), 1, inf, inf); AEK.motion.ease(ct.property("ADBE Position"), 2, inf, inf);
        AEK.motion.ease(rt.property("ADBE Rotate Y"), 1, inf, inf); AEK.motion.ease(rt.property("ADBE Rotate Y"), 2, inf, inf);
        return { rig: rig, camera: cam, zoom: zoom };
    }
    // focusOn(camera, layerName, {aperture, areaWidth, base}): Depth of Field on, Focus Distance follows the middle of the layer's
    // footprint by expression (base: true aims at the anchor point). Advanced 3D: Focus Area Width 0 keeps one plane sharp only.
    function focusOn(cam, layerName, o) {
        o = o || {};
        var co = cam.property("ADBE Camera Options Group"), aim;
        co.property("ADBE Camera Depth of Field").setValue(1);
        if (o.aperture) { co.property("ADBE Camera Aperture").setValue(o.aperture); }
        if (o.areaWidth) { try { co.property("ADBE Camera Focus Area Width").setValue(o.areaWidth); } catch (e) {} }
        aim = o.base ? "t.anchorPoint" : "[t.anchorPoint[0], r.top + r.height / 2, 0]";
        return AEK.expr.set(co.property("ADBE Camera Focus Distance"),
            "var t = thisComp.layer(\"" + layerName + "\");\nvar r = t.sourceRectAtTime(time, false);\nlength(toWorld([0, 0, 0]), t.toWorld(" + aim + "));", [0]);
    }
    // screenRect(comp, layer, t): where a 3D layer lands in the frame (camera projection included), through a temporary probe null
    function screenRect(c, l, t) {
        var probe = AEK.build.nullLayer(c, "__probe"), fx = probe.property("ADBE Effect Parade");
        fx.addProperty("ADBE Point Control"); fx.addProperty("ADBE Point Control");
        var a = probe.property("ADBE Effect Parade").property(1).property(1), b = probe.property("ADBE Effect Parade").property(2).property(1);
        var ref = "thisComp.layer(\"" + l.name.replace(/"/g, "\\\"") + "\")";
        a.expression = "var L = " + ref + "; L.toComp([0, 0, 0]);";
        b.expression = "var L = " + ref + "; L.toComp([L.width, L.height, 0]);";
        var p = a.valueAtTime(t || 0, false), q = b.valueAtTime(t || 0, false), err = a.expressionError;
        probe.remove();
        if (err) { throw new Error(err); }
        return { left: p[0], top: p[1], right: q[0], bottom: q[1], width: q[0] - p[0], height: q[1] - p[1] };
    }
    // parallaxScale(baseScale, z, zoom, overscan): scale that keeps a layer's framed size after moving it to depth z,
    // for a camera at z = -zoom looking down +z. overscan 1.1 leaves 10 % margin for the camera move.
    function parallaxScale(baseScale, z, zoom, overscan) { return baseScale * (zoom + z) / zoom * (overscan || 1); }
    // warmUp(comp, path): the first frame after a model is added can come back without the model; render one and discard it
    function warmUp(c, path) { var t0 = new Date().getTime(); AEK.capture.frame(c, 0, path); return new Date().getTime() - t0; }
    return { RENDERER: RENDERER, rendererName: rendererName, use: use, settable: settable, fitModel: fitModel, shadowCatcher: shadowCatcher,
        keyLight: keyLight, envLight: envLight, orbitRig: orbitRig, focusOn: focusOn, screenRect: screenRect, parallaxScale: parallaxScale, warmUp: warmUp };
})();
