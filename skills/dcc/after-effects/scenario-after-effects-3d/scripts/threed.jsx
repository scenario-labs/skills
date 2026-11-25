// threed.jsx: AEX.threeD helpers for 3D scenes in After Effects 27.0. Requires the AEK kit (core, build, motion, expr).
// Load with: ae.py run job.jsx --lib skills/scenario-after-effects-3d/scripts/threed.jsx
var AEX = AEX || {};
AEX.threeD = (function () {
    // internal renderer names on 27.0: the name "ADBE Advanced 3d" is CLASSIC 3D; the Advanced 3D renderer is "ADBE Calder"
    var RENDERER = { classic: "ADBE Advanced 3d", advanced: "ADBE Calder", cinema4d: "ADBE Ernst" };
    // A layer name inside a double-quoted expression string: backslashes first, then quotes.
    function esc(s) { return String(s).replace(/\\/g, "\\\\").replace(/"/g, "\\\""); }
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
        // an explicit 0 must stay 0 (o.intensity || 100 turned it into 100 and lit a pass that was meant dark)
        lo.property("ADBE Light Intensity").setValue(o.intensity === undefined ? 100 : o.intensity);
        if (o.color) { lo.property("ADBE Light Color").setValue(o.color); }
        if (l.lightType === LightType.SPOT) { lo.property("ADBE Light Cone Angle").setValue(o.cone || 70); }
        lo.property("ADBE Casts Shadows").setValue(1);
        lo.property("ADBE Light Shadow Darkness").setValue(o.darkness === undefined ? 60 : o.darkness);
        if (l.lightType !== LightType.PARALLEL) { lo.property("ADBE Light Shadow Diffusion").setValue(o.diffusion === undefined ? 15 : o.diffusion); }
        return l;
    }
    // sunLight(comp, target, az, el, {intensity, color, shadows, name}): a parallel light from a plate's sun. az: degrees from
    // straight away from the camera (negative = left), el: degrees above the floor. Read az from where the plate's own shadow
    // lines meet near the horizon, el from the sun's height. The light sits 20000 px from target along that direction.
    function sunLight(c, target, az, el, o) {
        o = o || {};
        var r = Math.PI / 180, k = 20000;
        var pos = [target[0] + k * Math.sin(az * r) * Math.cos(el * r), target[1] - k * Math.sin(el * r), target[2] + k * Math.cos(az * r) * Math.cos(el * r)];
        var l = keyLight(c, pos, target, { name: o.name || "sun", type: "PARALLEL", intensity: o.intensity, darkness: 100, color: o.color });
        l.property("ADBE Light Options Group").property("ADBE Casts Shadows").setValue(o.shadows === false ? 0 : 1);
        return l;
    }
    // envLight(comp, {intensity, source: footage item or null, shadows}): environment light; with a source, the source layer is added
    // and hidden. shadows is set explicitly (default false): a spot carries the contact shadow, a second soft shadow muddies it.
    function envLight(c, o) {
        o = o || {};
        // a layer source in a Classic 3D comp crashed 27.0 twice at render (stack overflow): refuse it here
        if (o.source && c.renderer !== RENDERER.advanced) { throw new Error("envLight: set the comp to Advanced 3D (AEX.threeD.use) before giving the light a layer source"); }
        var l = c.layers.addLight(o.name || "environment", [c.width / 2, c.height / 2]);
        l.lightType = LightType.ENVIRONMENT;
        l.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(o.intensity === undefined ? 100 : o.intensity);
        try { l.property("ADBE Light Options Group").property("ADBE Casts Shadows").setValue(o.shadows ? 1 : 0); } catch (e0) {}
        if (o.source) {
            var s = c.layers.add(o.source); s.name = (o.name || "environment") + " source"; s.enabled = false;
            l.lightSource = s;
        }
        return l;
    }
    // orbitRig(comp, center, {focalLength, distance, height, tilt, from, to, push, start, end, influence, bezier}):
    // a 3D null at the subject carries the orbit (Y rotation); a one-node camera parented to it carries the push.
    // height left out: the camera sits at distance x tan(-tilt) and pushes along its view line, so the null stays at frame
    // center (measured: height 0 with tilt -9 at 1100 px put the subject 211 px high; a Z-only push then drifted it 77 px).
    // bezier [x1, y1, x2, y2]: CSS curve on both moves instead of influence eases (a long soft settle: [0.3, 0, 0.12, 1]).
    function orbitRig(c, center, o) {
        o = o || {};
        var rig = AEK.build.nullLayer(c, o.name || "cam rig"); rig.threeDLayer = true;
        rig.property("ADBE Transform Group").property("ADBE Position").setValue(center);
        var cam = c.layers.addCamera((o.name || "cam rig") + " camera", [c.width / 2, c.height / 2]);
        cam.autoOrient = AutoOrientType.NO_AUTO_ORIENT;
        var zoom = c.width * (o.focalLength || 50) / 36, d = o.distance || zoom, t0 = o.start || 0, t1 = o.end || c.duration, inf = o.influence || 50;
        var tilt = o.tilt === undefined ? -8 : o.tilt, p = o.push || 0, h0, h1;
        if (o.height === undefined) { h0 = d * Math.tan(-tilt * Math.PI / 180); h1 = h0 * (d - p) / d; } else { h0 = o.height; h1 = o.height; }
        cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(zoom);
        cam.parent = rig;
        var ct = cam.property("ADBE Transform Group"), rt = rig.property("ADBE Transform Group"), cp = ct.property("ADBE Position"), ry = rt.property("ADBE Rotate Y");
        ct.property("ADBE Rotate X").setValue(tilt);
        AEK.motion.key(cp, t0, [0, -h0, -d]);
        AEK.motion.key(cp, t1, [0, -h1, -d + p]);
        AEK.motion.key(ry, t0, o.from || 0);
        AEK.motion.key(ry, t1, o.to || 0);
        if (o.bezier) { AEK.motion.bezier(cp, 1, 2, o.bezier); AEK.motion.bezier(ry, 1, 2, o.bezier); }
        else {
            AEK.motion.ease(cp, 1, inf, inf); AEK.motion.ease(cp, 2, inf, inf);
            AEK.motion.ease(ry, 1, inf, inf); AEK.motion.ease(ry, 2, inf, inf);
        }
        return { rig: rig, camera: cam, zoom: zoom, height: [h0, h1] };
    }
    // floor(comp, floorY, {color, size, opacity, x, z}): a lit 3D floor in one flat color that receives shadows.
    // Keep it flat: the light pool comes from the key spot, never from a gradient on the floor.
    function floor(c, floorY, o) {
        o = o || {};
        var f = AEK.build.solid(c, o.name || "floor", o.color || [0.08, 0.1, 0.15], { width: o.size || 4000, height: o.size || 4000 });
        f.threeDLayer = true;
        var tg = f.property("ADBE Transform Group"), mo = f.property("ADBE Material Options Group");
        tg.property("ADBE Orientation").setValue([270, 0, 0]);
        tg.property("ADBE Position").setValue([o.x === undefined ? c.width / 2 : o.x, floorY, o.z || 0]);
        if (o.scale) { tg.property("ADBE Scale").setValue([o.scale, o.scale, 100]); }
        mo.property("ADBE Accepts Shadows").setValue(1);
        mo.property("ADBE Casts Shadows").setValue(0);
        if (o.opacity !== undefined) { tg.property("ADBE Opacity").setValue(o.opacity); }
        return f;
    }
    // contactShadow(comp, floorY, width, {depth, feather, opacity, x, z, lift}): a feathered dark ellipse lying 1 px above the floor.
    // Advanced 3D draws no ambient occlusion: this decal is what seats a product. width and depth in comp pixels at scale 100.
    function contactShadow(c, floorY, width, o) {
        o = o || {};
        var dep = o.depth || width * 0.35, f = AEK.build.solid(c, o.name || "contact shadow", [0, 0, 0], { width: Math.round(width * 1.6), height: Math.round(dep * 1.6) });
        f.threeDLayer = true;
        var tg = f.property("ADBE Transform Group"), mo = f.property("ADBE Material Options Group");
        tg.property("ADBE Orientation").setValue([270, 0, 0]);
        tg.property("ADBE Position").setValue([o.x === undefined ? c.width / 2 : o.x, floorY - (o.lift || 1), o.z || 0]);
        tg.property("ADBE Opacity").setValue(o.opacity === undefined ? 75 : o.opacity);
        mo.property("ADBE Casts Shadows").setValue(0);
        try { mo.property("ADBE Accepts Lights").setValue(0); } catch (e0) {}
        var W = f.source.width, H = f.source.height, m = f.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), s = new Shape(), k = 0.5523;
        var cx = W / 2, cy = H / 2, rx = width / 2, ry = dep / 2;
        s.vertices = [[cx, cy - ry], [cx + rx, cy], [cx, cy + ry], [cx - rx, cy]];
        s.inTangents = [[-rx * k, 0], [0, -ry * k], [rx * k, 0], [0, ry * k]];
        s.outTangents = [[rx * k, 0], [0, ry * k], [-rx * k, 0], [0, -ry * k]];
        s.closed = true;
        m.property("ADBE Mask Shape").setValue(s);
        m.property("ADBE Mask Feather").setValue([o.feather === undefined ? dep * 0.4 : o.feather, o.feather === undefined ? dep * 0.4 : o.feather]);
        return f;
    }
    // reflection(comp3d, modelName, {opacity, blur, fadeTo, backdrop, name}): a floor reflection that blurs and fades with distance.
    // Builds "<comp> refl" (a duplicate holding only a mirrored copy of the model, plus camera and lights) and an outer comp:
    // backdrop, reflection with Compound Blur and a luminance fade from a ramp precomp, then the 3D comp on top.
    // The floor in the 3D comp must be partly transparent (opacity 70 to 90): the reflection shows through it.
    function reflection(c3, modelName, o) {
        o = o || {};
        var r = c3.duplicate(), i, l, keep, mirror;
        r.name = c3.name + " refl";
        for (i = r.numLayers; i >= 1; i--) {
            l = r.layer(i);
            keep = (l instanceof CameraLayer) || (l instanceof LightLayer) || (l.name === modelName) || (l.nullLayer === true) || (l.enabled === false);
            if (!keep) { l.enabled = false; }
        }
        mirror = r.layer(modelName);
        var sc = mirror.property("ADBE Transform Group").property("ADBE Scale").value;
        // the anchor sits at the base (fitModel), so a negative Y scale mirrors the model about the floor line
        mirror.property("ADBE Transform Group").property("ADBE Scale").setValue([sc[0], -sc[1], sc[2]]);
        var W = c3.width, H = c3.height, fps = c3.frameRate, D = c3.duration;
        var ramp = AEK.build.comp(c3.name + " refl ramp", { width: W, height: H, fps: fps, duration: D });
        var rs = AEK.build.solid(ramp, "ramp", [1, 1, 1], {});
        var re = AEK.build.effect(rs, "ADBE Ramp", {});
        var y0 = o.contactY === undefined ? H * 0.7 : o.contactY;
        re.property("ADBE Ramp-0001").setValue([W / 2, y0]); re.property("ADBE Ramp-0002").setValue([0, 0, 0]);
        re.property("ADBE Ramp-0003").setValue([W / 2, y0 + (o.fadeTo || H * 0.3)]); re.property("ADBE Ramp-0004").setValue([1, 1, 1]);
        var fin = AEK.build.comp(o.name || (c3.name + " final"), { width: W, height: H, fps: fps, duration: D });
        var bd = AEK.build.solid(fin, "backdrop", o.backdrop || [0.05, 0.06, 0.08], {});
        var blurMap = fin.layers.add(ramp); blurMap.name = "blur map"; blurMap.enabled = false;
        var rl = fin.layers.add(r); rl.name = "reflection";
        var cb = AEK.build.effect(rl, "ADBE Compound Blur", { "ADBE Compound Blur-0002": o.blur === undefined ? 12 : o.blur });
        cb.property("ADBE Compound Blur-0001").setValue(blurMap.index);
        var fade = fin.layers.add(ramp); fade.name = "fade matte";
        rl.moveBefore(bd); fade.moveBefore(rl);
        rl.setTrackMatte(fade, TrackMatteType.LUMA_INVERTED);
        rl.property("ADBE Transform Group").property("ADBE Opacity").setValue(o.opacity === undefined ? 100 : o.opacity);
        var top = fin.layers.add(c3); top.name = "scene";
        return { comp: fin, reflComp: r, rampComp: ramp };
    }
    // screenPoint(comp, layer, [x, y, z] in layer space, t): where a point of a 3D layer lands in the frame
    function screenPoint(c, l, pt, t) {
        var probe = AEK.build.nullLayer(c, "__probe"), fx = probe.property("ADBE Effect Parade");
        fx.addProperty("ADBE Point Control");
        var a = probe.property("ADBE Effect Parade").property(1).property(1);
        a.expression = "thisComp.layer(\"" + esc(l.name) + "\").toComp([" + pt[0] + "," + pt[1] + "," + (pt[2] || 0) + "]);";
        var v = a.valueAtTime(t || 0, false), err = a.expressionError;
        probe.remove();
        if (err) { throw new Error(err); }
        return v;
    }
    // maxPush(zoom, z, edgeOffset, halfFrame, keep): the largest camera push (px) that keeps a foreground edge inside the frame.
    // edgeOffset: distance in px from frame center to the foreground's inner edge at the start; keep: px of it to keep visible.
    // A layer at depth z grows by (zoom + z) / (zoom + z - push), so its edge leaves when edgeOffset x growth passes halfFrame - keep.
    function maxPush(zoom, z, edgeOffset, halfFrame, keep) { return (zoom + z) * (1 - edgeOffset / (halfFrame - (keep || 0))); }
    // focusOn(camera, layerName, {aperture, areaWidth, base}): Depth of Field on, Focus Distance follows the middle of the layer's
    // footprint by expression (base: true aims at the anchor point). Advanced 3D: Focus Area Width 0 keeps one plane sharp only.
    function focusOn(cam, layerName, o) {
        o = o || {};
        var co = cam.property("ADBE Camera Options Group"), aim;
        co.property("ADBE Camera Depth of Field").setValue(1);
        if (o.aperture) { co.property("ADBE Camera Aperture").setValue(o.aperture); }
        if (o.areaWidth) { try { co.property("ADBE Camera Focus Area Width").setValue(o.areaWidth); } catch (e) {} }
        aim = o.base ? "t.anchorPoint" : "[t.anchorPoint[0], r.top + r.height / 2, 0]";
        var ex = "var t = thisComp.layer(\"" + layerName + "\");\nvar r = t.sourceRectAtTime(time, false);\nvar d = length(toWorld([0, 0, 0]), t.toWorld(" + aim + "));";
        // rack: {layer, from, to, amount}: between from and to (s), Focus Distance eases toward the anchor of a second layer by amount (0 to 1)
        if (o.rack) {
            ex += "\nvar u = thisComp.layer(\"" + o.rack.layer + "\");\nvar d2 = length(toWorld([0, 0, 0]), u.toWorld(u.anchorPoint));" +
                "\nd + (d2 - d) * ease(time, " + o.rack.from + ", " + o.rack.to + ", 0, " + (o.rack.amount === undefined ? 1 : o.rack.amount) + ");";
        } else { ex += "\nd;"; }
        return AEK.expr.set(co.property("ADBE Camera Focus Distance"), ex, [0]);
    }
    // screenRect(comp, layer, t): where a 3D layer lands in the frame (camera projection included), through a temporary probe null
    function screenRect(c, l, t) {
        var probe = AEK.build.nullLayer(c, "__probe"), fx = probe.property("ADBE Effect Parade");
        fx.addProperty("ADBE Point Control"); fx.addProperty("ADBE Point Control");
        var a = probe.property("ADBE Effect Parade").property(1).property(1), b = probe.property("ADBE Effect Parade").property(2).property(1);
        var ref = "thisComp.layer(\"" + esc(l.name) + "\")";
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
    // warmUp(comp, path, timeoutMs): the first frame after a model is added can come back without the model; render one and
    // discard it. It loads the meshes and the environment map: allow minutes (default 180 s) when another render shares the machine.
    function warmUp(c, path, ms) { var t0 = new Date().getTime(); AEK.capture.frame(c, 0, path, ms || 180000); return new Date().getTime() - t0; }
    // dofBlur(comp, camera, layer, point, t): predicted defocus at a layer point from the camera's own values,
    // aperture x zoom x |d - focus| / (d x focus) in px (d = camera to point distance). Compare it with focus_check.py on frames.
    function dofBlur(c, cam, l, pt, t) {
        var probe = AEK.build.nullLayer(c, "__dof"), fx = probe.property("ADBE Effect Parade");
        fx.addProperty("ADBE Slider Control");
        var a = fx.property(1).property(1), cn = esc(cam.name), ln = esc(l.name);
        a.expression = "var C = thisComp.layer(\"" + cn + "\"); var L = thisComp.layer(\"" + ln + "\");\n" +
            "length(C.toWorld([0, 0, 0]), L.toWorld([" + pt[0] + "," + pt[1] + "," + (pt[2] || 0) + "]));";
        var d = a.valueAtTime(t || 0, false), err = a.expressionError;
        probe.remove();
        if (err) { throw new Error(err); }
        var co = cam.property("ADBE Camera Options Group"), s = co.property("ADBE Camera Focus Distance").valueAtTime(t || 0, false);
        var A = co.property("ADBE Camera Aperture").valueAtTime(t || 0, false), Z = co.property("ADBE Camera Zoom").valueAtTime(t || 0, false);
        return { distance: d, focus: s, aperture: A, zoom: Z, blurPx: A * Z * Math.abs(d - s) / (d * s) };
    }
    // mattes(comp, names, times, dir, prefix): one PNG per named layer and time with only that layer drawn (cameras and lights stay on),
    // written as <prefix>_<name>_<frame>.png. Their alpha is the layer's on-screen matte: compare two of them to measure what hides what.
    // Every layer's enabled flag is restored afterwards. Names with spaces are written with underscores.
    function mattes(c, names, times, dir, prefix) {
        var keep = [], i, j, k, l, on, out = [], f, base;
        for (i = 1; i <= c.numLayers; i++) { keep.push(c.layer(i).enabled); }
        try {
            for (k = 0; k < names.length; k++) {
                for (i = 1; i <= c.numLayers; i++) {
                    l = c.layer(i);
                    on = (l instanceof CameraLayer) || (l instanceof LightLayer) || l.name === names[k];
                    if (l instanceof LightLayer && l.lightType === LightType.ENVIRONMENT) { on = keep[i - 1]; }
                    if (l.enabled !== on) { l.enabled = on; }
                }
                for (j = 0; j < times.length; j++) {
                    f = Math.round(times[j] * c.frameRate);
                    base = (prefix || "matte") + "_" + names[k].replace(/[^A-Za-z0-9]+/g, "_") + "_" + f;
                    out.push({ name: names[k], t: times[j], path: AEK.capture.frame(c, times[j], dir + "/" + base + ".png").path });
                }
            }
        } finally {
            for (i = 1; i <= c.numLayers; i++) { if (c.layer(i).enabled !== keep[i - 1]) { c.layer(i).enabled = keep[i - 1]; } }
        }
        return out;
    }
    // parallax(comp, near, far, t0, t1): near and far are {layer, point} (point in layer space). Returns how far each point
    // travels on screen between t0 and t1 and the change of their separation (relPx, relPct of comp width): the parallax the move shows.
    function parallax(c, near, far, t0, t1) {
        var a0 = screenPoint(c, near.layer, near.point, t0), a1 = screenPoint(c, near.layer, near.point, t1);
        var b0 = screenPoint(c, far.layer, far.point, t0), b1 = screenPoint(c, far.layer, far.point, t1);
        var dx = (a1[0] - b1[0]) - (a0[0] - b0[0]), dy = (a1[1] - b1[1]) - (a0[1] - b0[1]), rel = Math.sqrt(dx * dx + dy * dy);
        return { near: [a0, a1], far: [b0, b1], relPx: rel, relPct: rel / c.width * 100 };
    }
    return { RENDERER: RENDERER, rendererName: rendererName, use: use, settable: settable, fitModel: fitModel, shadowCatcher: shadowCatcher,
        keyLight: keyLight, sunLight: sunLight, envLight: envLight, orbitRig: orbitRig, floor: floor, contactShadow: contactShadow, reflection: reflection,
        focusOn: focusOn, screenRect: screenRect, screenPoint: screenPoint, maxPush: maxPush, parallaxScale: parallaxScale, warmUp: warmUp,
        mattes: mattes, parallax: parallax, dofBlur: dofBlur };
})();
