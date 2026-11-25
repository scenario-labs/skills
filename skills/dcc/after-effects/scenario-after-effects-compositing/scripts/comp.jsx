// AEX.comp: compositing helpers (keying chain, matte views, masks, light wrap, pre-render).
// Load with: ae.py run job.jsx --lib <skill>/scripts/comp.jsx . Requires the AEK kit (core, build, capture).
// ES3 only. Every function was run on After Effects 27.0.
var AEX = AEX || {};
AEX.comp = (function () {
    // Keylight 906 "View" values (index in the dropdown)
    var VIEW = { source: 1, sourceAlpha: 2, correctedSource: 3, colourCorrectionEdges: 4, screenMatte: 5, insideMask: 6,
        outsideMask: 7, combinedMatte: 8, status: 9, intermediate: 10, "final": 11 };
    var REPLACE = { none: 1, source: 2, hardColour: 3, softColour: 4 };

    function fxByIndex(l, idx) { return l.property("ADBE Effect Parade").property(idx); }

    // sampleColor(comp, layer, [x, y], [halfW, halfH], seconds): average RGBA of a box, read through sampleImage().
    // center is in the LAYER's own space. Uses a temporary null with a Color Control; the null is removed before returning.
    // Trap (measured on 27.0): read from a script, sampleImage() through valueAtTime(t) returns [0,0,0,0] unless t is the
    // comp's current time (or that frame was rendered twice). So the comp time is moved to t, .value is read, time restored.
    // rimLight(comp, fg, {angle, widthPx, blurPx, color, opacity, mode, name}): a rim on the edge of the foreground
    // that faces the light. angle = direction from the subject toward the plate's light source in comp pixels
    // (0 = right, 90 = down, -90 = up, 180 = left). The crescent is the foreground minus a copy of itself shifted
    // widthPx away from the light, blurred, clipped to the foreground, filled with the source color.
    function rimLight(c, fg, o) {
        o = o || {};
        if (fg.parent) { throw new Error("rimLight: precompose a parented foreground first"); }
        var name = o.name || "rim_light_v001", a = (o.angle || 0) * Math.PI / 180, wpx = o.widthPx || 8;
        var dx = -Math.cos(a) * wpx, dy = -Math.sin(a) * wpx, inner, outer, k, l1, l2, cr, clip, m, s;
        inner = AEK.build.comp(name + "_crescent", { width: c.width, height: c.height, fps: c.frameRate, duration: c.duration });
        fg.copyToComp(inner); fg.copyToComp(inner);
        l1 = inner.layer(1); l2 = inner.layer(2);
        for (k = 1; k <= 2; k++) { if (inner.layer(k).hasTrackMatte) { inner.layer(k).removeTrackMatte(); } inner.layer(k).enabled = true; }
        // the upper copy, shifted away from the light, cuts the lower one: what is left faces the light
        l1.property("ADBE Transform Group").property("ADBE Position").expression = "value + [" + dx + ", " + dy + "]";
        l2.setTrackMatte(l1, TrackMatteType.ALPHA_INVERTED);
        outer = AEK.build.comp(name + "_matte", { width: c.width, height: c.height, fps: c.frameRate, duration: c.duration });
        fg.copyToComp(outer);
        clip = outer.layer(1); if (clip.hasTrackMatte) { clip.removeTrackMatte(); }
        cr = outer.layers.add(inner); cr.name = "crescent";
        AEK.build.effect(cr, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.blurPx === undefined ? wpx : o.blurPx, "ADBE Gaussian Blur 2-0003": 0 }, "rim soften");
        cr.setTrackMatte(clip, TrackMatteType.ALPHA);   // the blurred rim stays inside the subject
        m = c.layers.add(outer); m.name = name + " matte";
        s = AEK.build.solid(c, name, o.color || [1, 0.8, 0.55]);
        s.moveBefore(fg); m.moveBefore(s);
        s.setTrackMatte(m, TrackMatteType.ALPHA);
        s.blendingMode = (o.mode === "add") ? BlendingMode.ADD : BlendingMode.SCREEN;
        s.property("ADBE Transform Group").property("ADBE Opacity").setValue(o.opacity === undefined ? 60 : o.opacity);
        fg.enabled = true;
        return { layer: s.name, matte: m.name, offset: [dx, dy], mode: AEK.core.enumName(BlendingMode, s.blendingMode) };
    }
    // shadeLight(comp, fg, {angle, center, radius, color, opacity, name}): a linear falloff across the foreground,
    // white on the side facing the light and `color` on the far side, in Multiply, clipped to the foreground's alpha.
    // center and radius (comp px) come from `matte_metrics.py light` (subject_center, subject_radius).
    function shadeLight(c, fg, o) {
        o = o || {};
        if (fg.parent) { throw new Error("shadeLight: precompose a parented foreground first"); }
        var name = o.name || "shade_light_v001", a = (o.angle || 0) * Math.PI / 180, r = o.radius || c.height / 4, ctr = o.center || [c.width / 2, c.height / 2];
        var mc = AEK.build.comp(name + "_matte", { width: c.width, height: c.height, fps: c.frameRate, duration: c.duration }), cp, m, s;
        fg.copyToComp(mc); cp = mc.layer(1); if (cp.hasTrackMatte) { cp.removeTrackMatte(); } cp.enabled = true;
        m = c.layers.add(mc); m.name = name + " matte";
        s = AEK.build.solid(c, name, [1, 1, 1]);
        AEK.build.effect(s, "ADBE Ramp", { "ADBE Ramp-0001": [ctr[0] + Math.cos(a) * r, ctr[1] + Math.sin(a) * r], "ADBE Ramp-0002": [1, 1, 1, 1],
            "ADBE Ramp-0003": [ctr[0] - Math.cos(a) * r, ctr[1] - Math.sin(a) * r], "ADBE Ramp-0004": (o.color || [0.6, 0.58, 0.66]).concat([1]), "ADBE Ramp-0005": 1 }, "falloff");
        s.moveBefore(fg); m.moveBefore(s);
        s.setTrackMatte(m, TrackMatteType.ALPHA);
        s.blendingMode = BlendingMode.MULTIPLY;
        s.property("ADBE Transform Group").property("ADBE Opacity").setValue(o.opacity === undefined ? 100 : o.opacity);
        fg.enabled = true;
        return { layer: s.name, from: [ctr[0] + Math.cos(a) * r, ctr[1] + Math.sin(a) * r], to: [ctr[0] - Math.cos(a) * r, ctr[1] - Math.sin(a) * r] };
    }
    function sampleColor(c, l, center, half, t) {
        var n = c.layers.addNull(c.duration), cc, v, keep = c.time, zero;
        n.name = "AEX_sample_tmp";
        cc = n.property("ADBE Effect Parade").addProperty("ADBE Color Control");
        cc = n.property("ADBE Effect Parade").property(1).property(1);
        cc.expression = "thisComp.layer(" + l.index + ").sampleImage([" + center[0] + "," + center[1] + "],[" + half[0] + "," + half[1] + "],true,time)";
        c.time = t;
        v = cc.value;
        zero = (v[0] === 0 && v[1] === 0 && v[2] === 0 && v[3] === 0);
        if (zero) { AEK.capture.frame(c, t, Folder.temp.fsName + "/aex_sample_" + c.id + ".png"); v = cc.value; }
        c.time = keep;
        if (cc.expressionError) { var msg = cc.expressionError; n.remove(); throw new Error(msg); }
        n.remove();
        return [v[0], v[1], v[2], v[3]];
    }

    // keyChain(layer, o): Keylight, then Key Cleaner, then Advanced Spill Suppressor, in that order.
    // o: {screen:[r,g,b], view:"intermediate"|"final"|..., clipBlack, clipWhite, gain, balance, preBlur, shrink, softness,
    //     despotBlack, despotWhite, rollback, replace:"softColour"|..., cleaner:{radius, chatter, contrast, strength} | false,
    //     spill:{method:"standard"|"ultra", suppression, color:[r,g,b], tolerance, desaturate, range, correction, luma} | false}
    // With spill on, View must be "intermediate": with "final" Keylight despills first and the suppressor has nothing left to do.
    function keyChain(l, o) {
        o = o || {};
        var out = {}, k, s, i;
        k = AEK.build.effect(l, "Keylight 906", {}, o.name || "Keylight");
        i = k.propertyIndex;
        function kp(n, v) { if (v !== undefined && v !== null) { fxByIndex(l, i).property("Keylight 906-" + n).setValue(v); } }
        if (o.screen) { kp("0004", [o.screen[0], o.screen[1], o.screen[2], 1]); }
        kp("0002", VIEW[o.view || (o.spill ? "intermediate" : "final")]);
        kp("0005", o.gain); kp("0006", o.balance); kp("0010", o.preBlur);
        kp("0012", o.clipBlack); kp("0013", o.clipWhite); kp("0014", o.rollback); kp("0015", o.shrink); kp("0016", o.softness);
        kp("0017", o.despotBlack); kp("0018", o.despotWhite);
        if (o.replace) { kp("0019", REPLACE[o.replace]); }
        out.keylight = i;
        if (o.cleaner) {
            s = AEK.build.effect(l, "ADBE KeyCleaner", {}, "Key Cleaner");
            out.cleaner = s.propertyIndex;
            if (o.cleaner.radius !== undefined) { fxByIndex(l, out.cleaner).property("ADBE KeyCleaner-0006").setValue(o.cleaner.radius); }
            if (o.cleaner.chatter !== undefined) { fxByIndex(l, out.cleaner).property("ADBE KeyCleaner-0002").setValue(o.cleaner.chatter ? 1 : 0); }
            if (o.cleaner.contrast !== undefined) { fxByIndex(l, out.cleaner).property("ADBE KeyCleaner-0016").setValue(o.cleaner.contrast); }
            if (o.cleaner.strength !== undefined) { fxByIndex(l, out.cleaner).property("ADBE KeyCleaner-0001").setValue(o.cleaner.strength); }
        }
        if (o.spill) {
            s = AEK.build.effect(l, "ADBE Spill2", {}, "Advanced Spill Suppressor");
            out.spill = s.propertyIndex;
            var sp = function (n, v) { if (v !== undefined && v !== null) { fxByIndex(l, out.spill).property("ADBE Spill2-" + n).setValue(v); } };
            sp("0001", o.spill.method === "ultra" ? 2 : 1);
            sp("1001", o.spill.suppression);
            if (o.spill.color) { sp("0003", [o.spill.color[0], o.spill.color[1], o.spill.color[2], 1]); }
            sp("0004", o.spill.tolerance); sp("0005", o.spill.desaturate); sp("0006", o.spill.range);
            sp("0007", o.spill.correction); sp("0008", o.spill.luma);
        }
        return out;
    }

    // setView(layer, keylightEffectIndex, viewName): switch Keylight's View ("screenMatte", "status", "intermediate", "final", ...)
    function setView(l, idx, name) { fxByIndex(l, idx).property("Keylight 906-0002").setValue(VIEW[name]); return VIEW[name]; }

    // alphaView(srcComp, name): a comp that shows srcComp's alpha as gray (white = opaque) over black, for measuring.
    function alphaView(src, name) {
        var c = AEK.build.comp(name, { width: src.width, height: src.height, fps: src.frameRate, duration: src.duration, bg: [0, 0, 0] });
        AEK.build.solid(c, "black", [0, 0, 0]);
        var l = c.layers.add(src);
        AEK.build.effect(l, "ADBE Fill", { "ADBE Fill-0002": [1, 1, 1, 1] }, "alpha as white");
        return c;
    }

    // overView(srcComp, name, [r,g,b]): srcComp over a solid color, to judge spill and edges on a known background.
    function overView(src, name, bg) {
        var c = AEK.build.comp(name, { width: src.width, height: src.height, fps: src.frameRate, duration: src.duration });
        AEK.build.solid(c, "bg", bg || [0.5, 0.5, 0.5]);
        c.layers.add(src);
        return c;
    }

    // mask(layer, points [[x,y]...] in layer space, o): closed polygon mask. o {mode:"add"|"subtract"|"intersect"|"none",
    //   feather (px), expansion (px, negative shrinks), inverted, name, keys:[{t, points}] for an animated garbage matte}
    function mask(l, pts, o) {
        o = o || {};
        var modes = { add: MaskMode.ADD, subtract: MaskMode.SUBTRACT, intersect: MaskMode.INTERSECT, none: MaskMode.NONE,
            lighten: MaskMode.LIGHTEN, darken: MaskMode.DARKEN, difference: MaskMode.DIFFERENCE };
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), idx = m.propertyIndex, j;
        function shp(p) { var s = new Shape(); s.vertices = p; s.closed = true; return s; }
        m = l.property("ADBE Mask Parade").property(idx);
        if (o.name) { m.name = o.name; }
        m.maskMode = modes[o.mode || "add"];
        if (o.inverted) { m.inverted = true; }
        if (o.keys && o.keys.length) {
            for (j = 0; j < o.keys.length; j++) { m.property("ADBE Mask Shape").setValueAtTime(o.keys[j].t, shp(o.keys[j].points)); }
        } else {
            m.property("ADBE Mask Shape").setValue(shp(pts));
        }
        if (o.feather !== undefined) { m.property("ADBE Mask Feather").setValue([o.feather, o.feather]); }
        if (o.expansion !== undefined) { m.property("ADBE Mask Offset").setValue(o.expansion); }
        return { index: idx, mode: AEK.core.enumName(MaskMode, m.maskMode), keys: m.property("ADBE Mask Shape").numKeys };
    }

    // lightWrap(comp, fgLayer, bgLayer, o): native light wrap from track mattes (no plugin).
    // Builds precomp "<name>_src" = background matted by the INVERTED foreground alpha, then in the main comp a layer of it,
    // blurred (Fast Box Blur, radius = o.radiusPct of comp height), matted by the foreground alpha, blend Add or Screen.
    // fgLayer must carry the key in its own alpha (a precomp layer of the keyed plate), bgLayer the background.
    // Both layers are copied with copyToComp, so their transforms, masks, effects and start times carry into the wrap
    // (adding .source dropped them: a scaled or moved background wrapped the wrong pixels). Parenting does not carry:
    // a parented layer is precomposed first.
    // o {radiusPct (default 1.0), opacity (default 35), mode "add"|"screen", name}
    function lightWrap(c, fg, bg, o) {
        o = o || {};
        var name = o.name || ("light_wrap_" + c.name), r = Math.round(c.height * (o.radiusPct === undefined ? 1.0 : o.radiusPct) / 100);
        if (bg.parent || fg.parent) { throw new Error("lightWrap: precompose a parented foreground or background first"); }
        var src = AEK.build.comp(name + "_src", { width: c.width, height: c.height, fps: c.frameRate, duration: c.duration });
        bg.copyToComp(src);
        fg.copyToComp(src);
        var f = src.layer(1), b = src.layer(2);
        f.enabled = true; b.enabled = true;
        if (f.hasTrackMatte) { f.removeTrackMatte(); }
        if (b.hasTrackMatte) { b.removeTrackMatte(); }
        b.setTrackMatte(f, TrackMatteType.ALPHA_INVERTED);
        var w = c.layers.add(src);
        w.name = name;
        w.moveBefore(fg);
        AEK.build.effect(w, "ADBE Box Blur2", { "ADBE Box Blur2-0001": r, "ADBE Box Blur2-0002": 3, "ADBE Box Blur2-0004": 0 }, "wrap blur");
        w.setTrackMatte(fg, TrackMatteType.ALPHA);
        w.blendingMode = (o.mode === "screen") ? BlendingMode.SCREEN : BlendingMode.ADD;
        w.property("ADBE Transform Group").property("ADBE Opacity").setValue(o.opacity === undefined ? 35 : o.opacity);
        // setTrackMatte switched the foreground's video off: it must stay visible, it is the subject
        fg.enabled = true;
        return { layer: w.name, radiusPx: r, mode: AEK.core.enumName(BlendingMode, w.blendingMode), fgVisible: fg.enabled };
    }

    // preRender(comp, absPath, template): render a heavy matte comp once (template with alpha, e.g. "High Quality with Alpha"),
    // import the file and point every layer that used the comp to it. The comp itself stays in the project.
    function preRender(c, path, template) {
        var r = AEK.capture.queue(c, path, { template: template || "High Quality with Alpha" });
        var it = app.project.importFile(new ImportOptions(new File(r.path))), i, j, cc, l, n = 0;
        for (i = 1; i <= app.project.numItems; i++) {
            cc = app.project.item(i);
            if (!(cc instanceof CompItem)) { continue; }
            for (j = 1; j <= cc.numLayers; j++) {
                l = cc.layer(j);
                if (l.source === c) { var nm = l.name; l.replaceSource(it, false); l.name = nm; n++; }
            }
        }
        return { file: r.path, renderMs: r.ms, frames: r.frames, replacedLayers: n, item: it.name, hasAlpha: it.mainSource.hasAlpha, alphaMode: AEK.core.enumName(AlphaMode, it.mainSource.alphaMode) };
    }

    return { VIEW: VIEW, sampleColor: sampleColor, keyChain: keyChain, setView: setView, alphaView: alphaView,
        overView: overView, mask: mask, lightWrap: lightWrap, rimLight: rimLight, shadeLight: shadeLight, preRender: preRender };
}());
