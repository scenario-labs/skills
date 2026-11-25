// vfx.jsx: helpers for effects built with After Effects' own tools, measured on After Effects 27.0. Requires the AEK kit
// (core, build, expr, capture, xio, motion). Load with: ae.py run job.jsx --lib <skills>/scenario-after-effects-vfx/scripts/vfx.jsx
// Namespaces:
//   AEX.vfxu      shared helpers (options merge, effects, linear gain, masks, colors)
//   AEX.vfx       CC Particle World keys and follow, Glow-effect stack, tint, grain, noise loops, bit depth, plate, frame cost
//   AEX.light     the light rig: gray light summed in Add, Gaussian bloom, one 5-tone luminance map (CC Toner)
//   AEX.glow      Gaussian Blur copies at doubling radii with linear gains (the bloom used by AEX.light)
//   AEX.pn        CC Particle World set from on-screen numbers (count, px, px/s)
//   AEX.burst     energy hit: radial streaks through Polar Coordinates, core cones, a few sparks with Echo trails; particle-only planes
//   AEX.atmo      embers and dust in three planes, beam, title hole, seamless loop
//   AEX.smoke     smoke plume and looping flame entry points (build, flame), embers, heat haze, crossfade loop
//   AEX.fire      flame grown from a fixed source: one-sided displacement map, three noise scales, one tone map, sharpen
//   AEX.plume     smoke plume: stringy wisps through a widening leaning mask, swayed with height, gray, Screen
//   AEX.motes     dust in a light beam: few motes by depth, slow rise, soft discs, faint beam
//   AEX.element   land a generated element on black (fire, smoke): foot, black level, palette, Screen, glow, thrown light
//   AEX.shock     shockwave ring: polar band, stroke ring, ring of light, refraction, motion-blur split
//   AEX.rays      light rays from a light-only layer, plate fallback, rays inside a light rig
//   AEX.bolt      lightning strike: white core in a light rig, envelope, spill
//   AEX.distort   heat haze and bipolar refraction rings by Displacement Map, envelope, mirrored pad, chromatic split
//   AEX.lens      lens finish: distortion, chromatic aberration, halation, streak, vignette, grain
//   AEX.integrate an effect sitting in a plate: interactive light, pool, reflection, dim, envelope, grain
//   AEX.pulse     a hit leaving a subject on a plate: two light rigs by depth, choked holdout, rim and wrap, floor ellipse ring, one envelope null
var AEX = AEX || {};

AEX.vfxu = (function () {
    // merge(defaults, o): a copy of defaults with o's own keys on top. Returns the new object.
    function merge(d, o) {
        var r = {}, k;
        for (k in d) { if (d.hasOwnProperty(k)) { r[k] = d[k]; } }
        if (o) { for (k in o) { if (o.hasOwnProperty(k)) { r[k] = o[k]; } } }
        return r;
    }
    // fx(layer, matchName, props, name): AEK.build.effect with props optional. Returns the effect.
    function fx(l, mn, props, name) { return AEK.build.effect(l, mn, props || {}, name); }
    // stops(gain): Exposure stops for a linear gain. Returns a number.
    function stops(g) { return Math.log(g) / Math.LN2; }
    // gain(layer, g, name): Exposure with Bypass Linear Light Conversion on (-0022), a plain multiply by g at 8, 16 and 32 bpc. Returns the effect.
    function gain(l, g, name) { return fx(l, "ADBE Exposure2", { "ADBE Exposure2-0003": stops(g), "ADBE Exposure2-0022": 1 }, name); }
    // opacity(layer): the layer's Opacity property.
    function opacity(l) { return l.property("ADBE Transform Group").property("ADBE Opacity"); }
    // ellipse(layer, cx, cy, rx, ry, feather, o): a feathered ellipse mask in layer pixels; o = {mode: MaskMode.*, inverted, opacity}. Returns the mask.
    // Mask mode is set with mask.maskMode; property("ADBE Mask Mode") returns null.
    function ellipse(l, cx, cy, rx, ry, feather, o) {
        o = o || {};
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape(), kx = 0.5523 * rx, ky = 0.5523 * ry;
        sh.vertices = [[cx, cy - ry], [cx + rx, cy], [cx, cy + ry], [cx - rx, cy]];
        sh.inTangents = [[-kx, 0], [0, -ky], [kx, 0], [0, ky]];
        sh.outTangents = [[kx, 0], [0, ky], [-kx, 0], [0, -ky]];
        sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh);
        m.property("ADBE Mask Feather").setValue(feather instanceof Array ? feather : [feather, feather]);
        if (o.mode) { m.maskMode = o.mode; }
        if (o.inverted) { m.inverted = true; }
        if (o.opacity !== undefined) { m.property("ADBE Mask Opacity").setValue(o.opacity); }
        return m;
    }
    // rect(layer, x0, y0, x1, y1, feather): a feathered rectangle mask; feather in px or [x, y]. Returns the mask.
    function rect(l, x0, y0, x1, y1, feather) {
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape();
        sh.vertices = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
        sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh);
        m.property("ADBE Mask Feather").setValue(feather instanceof Array ? feather : [feather, feather]);
        return m;
    }
    // hex("#RRGGBB"): [r, g, b] in 0 to 1.
    function hex(h) { return [parseInt(h.substr(1, 2), 16) / 255, parseInt(h.substr(3, 2), 16) / 255, parseInt(h.substr(5, 2), 16) / 255]; }
    // mix(a, b, t) and scale(c, k): color arithmetic on [r, g, b].
    function mix(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
    function scale(c, k) { return [c[0] * k, c[1] * k, c[2] * k]; }
    // The palette the builders default to (ink ground, navy haze, coral energy, cream cores, warm gray). Pass your own colors in o.
    var PALETTE = { ink: hex("#0D0F14"), navy: hex("#1B2740"), coral: hex("#E0452C"), cream: hex("#F1E9D8"), grey: hex("#8C8577") };
    return { merge: merge, fx: fx, stops: stops, gain: gain, opacity: opacity, ellipse: ellipse, rect: rect, hex: hex, mix: mix, scale: scale, PALETTE: PALETTE };
})();

AEX.vfx = (function () {
    // CC Particle World property match names (live 27.0). Group headers (Producer, Physics...) are flat entries, not groups.
    // animation: 1 Explosive, 3 Cone Axis (points along axisX/axisY in screen axes; 2 Direction Axis does not point the burst).
    // transfer: 1 Composite (keeps color where particles overlap), 2 Screen, 3 Add, 4 Black Alpha. colorMap 2 Birth to Death, 1 custom (custom1 to custom5).
    var PW = { birthRate: "-0004", longevity: "-0005", x: "-0007", y: "-0008", z: "-0009", rx: "-0010", ry: "-0011", rz: "-0012",
        animation: "-0015", velocity: "-0016", inherit: "-0017", gravity: "-0018", resistance: "-0041", extra: "-0019", extraAngle: "-0020",
        floorPosition: "-0003", floorAction: "-0066", axisX: "-0095", axisY: "-0096", axisZ: "-0097", gravityX: "-0100", gravityY: "-0101", gravityZ: "-0102",
        type: "-0023", textureLayer: "-0045", birthSize: "-0024", deathSize: "-0025", sizeVar: "-0026", maxOpacity: "-0027",
        colorMap: "-0028", birthColor: "-0029", deathColor: "-0030", volumeShade: "-0040", transfer: "-0039",
        custom1: "-0074", custom2: "-0075", custom3: "-0076", custom4: "-0077", custom5: "-0078",
        camDistance: "-0033", camRotX: "-0034", camRotY: "-0035", camRotZ: "-0036", fov: "-0037", holdRelease: "-0091", seed: "-0104" };
    // the on-screen guides: Position, Radius, Motion Path, Grid, Horizon, Axis Box. They render in the comp view only, but switch them off for clean frames.
    var GUIDES = ["-0051", "-0052", "-0053", "-0055", "-0060", "-0061"];
    // pw(layer, {friendly keys above}, name): CC Particle World with the guides off. Returns the effect.
    function pw(l, o, name) {
        var p = {}, k, i;
        for (i = 0; i < GUIDES.length; i++) { p["CC Particle World" + GUIDES[i]] = 0; }
        for (k in o) { if (o.hasOwnProperty(k)) { if (!PW[k]) { throw new Error("pw: unknown key " + k); } p["CC Particle World" + PW[k]] = o[k]; } }
        return AEK.build.effect(l, "CC Particle World", p, name);
    }
    // pwProp(fx, key): one CC Particle World property by friendly key.
    function pwProp(fx, key) { return fx.property("CC Particle World" + PW[key]); }
    // followExpr(nullName, axis): Producer Position X or Y expression that puts the producer on a layer's anchor.
    // Measured: one unit = the particle layer's WIDTH on both axes (0.25 = 240 px in X and in Y on a 960x540 layer), 0 = layer center.
    function followExpr(nullName, axis) {
        return "var L = thisComp.layer(\"" + nullName + "\");\nvar p = fromComp(L.toComp(L.anchorPoint));\n" +
            (axis === "x" ? "(p[0] - width / 2) / width;" : "(p[1] - height / 2) / width;");
    }
    // follow(fx, nullName): wire Producer Position X and Y of a CC Particle World effect to a layer. Returns the effect.
    function follow(fx, nullName) {
        AEK.expr.set(pwProp(fx, "x"), followExpr(nullName, "x"));
        AEK.expr.set(fx.property("CC Particle World" + PW.y), followExpr(nullName, "y"));
        return fx;
    }
    // glowStack(layer, [{radius, intensity}], threshold0to255): several Glow effects (ADBE Glo2). Threshold on the 0-255 scale (153 = 60 %).
    // One Glow brings a 1.0 disc to 1.1 to 1.4 x its light at 16 bpc and up to 15 x at 32 bpc (threshold 0, intensity 1): for colored light use AEX.light.rig.
    function glowStack(l, passes, threshold) {
        var out = [], i, g;
        for (i = 0; i < passes.length; i++) {
            g = AEK.build.effect(l, "ADBE Glo2", { "ADBE Glo2-0002": threshold === undefined ? 0 : threshold, "ADBE Glo2-0003": passes[i].radius, "ADBE Glo2-0004": passes[i].intensity }, "Glow " + passes[i].radius);
            out.push(g.name);
        }
        return out;
    }
    // tint(layer, colorWhite, colorBlack): Tint maps luminance to two colors. Returns the effect.
    function tint(l, white, black) {
        return AEK.build.effect(l, "ADBE Tint", { "ADBE Tint-0001": black || [0, 0, 0], "ADBE Tint-0002": white });
    }
    // grain(layer, intensity, size): Add Grain (VISINF Grain Implant). Viewing Mode 1 shows a preview box only: set 3 (Final Output).
    // Intensity is linear: frame-to-frame luma std 4.2 levels per unit on flat patches near 10/255 and 2.2 at mid gray.
    // Over a plate: intensity = the plate's std / that slope (0.17 for a dark plate at 0.73 levels). 1.5 to 2 is a film look on clean CG.
    function grain(l, intensity, size) {
        return AEK.build.effect(l, "VISINF Grain Implant", { "VISINF Grain Implant-0021": 3, "VISINF Grain Implant-0008": intensity, "VISINF Grain Implant-0007": size || 1 });
    }
    // loopNoise(fx, comp, seconds, revolutions): Cycle Evolution on and Evolution keyed 0 to revolutions * 360 over the loop, linear.
    // Works for ADBE Fractal Noise (-0023 Evolution, -0025 Cycle, -0026 Cycle revs) and ADBE Turbulent Displace (-0006, -0008, -0009).
    function loopNoise(fx, c, seconds, revs) {
        var mn = fx.matchName, ids = mn === "ADBE Fractal Noise" ? ["-0023", "-0025", "-0026"] : ["-0006", "-0008", "-0009"];
        fx.property(mn + ids[1]).setValue(1);
        fx.property(mn + ids[2]).setValue(revs);
        var ev = fx.property(mn + ids[0]);
        ev.setValueAtTime(0, 0);
        ev.setValueAtTime(seconds, revs * 360);
        ev.setInterpolationTypeAtKey(1, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
        ev.setInterpolationTypeAtKey(2, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
        return { evolutionEnd: revs * 360, loopFrames: Math.round(seconds * c.frameRate) };
    }
    // cost(comp, [seconds], dir, prefix): frames with the time each took. saveFrameToPng is async: the kit polls, then waits 150 ms; that is subtracted.
    function cost(c, times, dir, prefix) {
        var out = [], i, t0, ms, f;
        for (i = 0; i < times.length; i++) {
            t0 = new Date().getTime();
            f = AEK.capture.frame(c, times[i], dir + "/" + prefix + "_f" + ("000" + Math.round(times[i] * c.frameRate)).slice(-3) + ".png");
            ms = new Date().getTime() - t0 - 150;
            out.push({ frame: f.frame, ms: ms, path: f.path });
        }
        return out;
    }
    // plate(comp, path, name): import a plate and fit it to the comp (cover), bottom of the stack. Frames from saveFrameToPng have
    // a transparent comp background: an opaque plate keeps contact sheets honest. Returns the layer.
    function plate(c, path, name) {
        var it = AEK.xio.importItem(path, {});
        var l = c.layer(AEK.xio.addToComp(c, it, { fit: "cover", name: name || "PLATE" }).index);
        l.moveToEnd();
        return l;
    }
    // depth(bpc): project bit depth. OCIO color management accepts 32 bpc only ("Not supported for OCIO color managed mode"): for 8 or 16
    // it switches to Adobe color management (0). In a person's OCIO project call depth(32) to keep their engine. Returns {bpc, cms}.
    function depth(bpc) {
        if (app.project.colorManagementSystem !== 0 && bpc !== 32) { app.project.colorManagementSystem = 0; }
        app.project.bitsPerChannel = bpc;
        return { bpc: app.project.bitsPerChannel, cms: app.project.colorManagementSystem };
    }
    return { PW: PW, depth: depth, pw: pw, pwProp: pwProp, followExpr: followExpr, follow: follow, glowStack: glowStack, tint: tint, grain: grain,
        loopNoise: loopNoise, cost: cost, plate: plate };
})();

AEX.glow = (function () {
    var U = AEX.vfxu;
    // DEFAULTS (glow_stack sweep): r0 12 px for strokes 5 to 30 px wide, 5 copies (12 to 192 px), total gain 2.0, each copy 0.75 x the previous.
    // Total 0.6 reads as no glow; 3.0 pushes thin strokes to the top of the light map.
    var DEFAULTS = { r0: 12, n: 5, total: 2.0, k: 0.75, colors: null, prefix: null };
    // plan(o): {radii, weights}: radii doubling from r0, weights summing to total, each k x the previous.
    function plan(o) {
        o = U.merge(DEFAULTS, o);
        var radii = [], w = [], s = 0, i;
        for (i = 0; i < o.n; i++) { radii.push(o.r0 * Math.pow(2, i)); w.push(Math.pow(o.k, i)); s += w[i]; }
        for (i = 0; i < o.n; i++) { w[i] = w[i] * o.total / s; }
        return { radii: radii, weights: w, colors: o.colors, prefix: o.prefix };
    }
    // copies(src, radii, weights, o): duplicates of src above it, each Solid Composite black, optional Tint o.colors[i], Gaussian Blur
    // (Repeat Edge Pixels off), Exposure linear gain, Add. Gaussian Blur keeps energy: the light added is sum(weights) x the source.
    // The source's own effects are cleared on each copy unless o.keepEffects: content drawn by an effect (CC Particle World, Fractal Noise)
    // then blooms too, at the cost of rendering the effect once per copy. Names: "<o.prefix or src name> <o.label> <radius>".
    // Returns the copy names; the array's .cleared lists the effects removed (empty when none or kept).
    function copies(src, radii, weights, o) {
        o = o || {};
        var i, d, parade, out = [], cleared = [], sp = src.property("ADBE Effect Parade");
        if (!o.keepEffects && sp) { for (i = 1; i <= sp.numProperties; i++) { cleared.push(sp.property(i).matchName); } }
        for (i = 0; i < radii.length; i++) {
            d = src.duplicate();
            parade = d.property("ADBE Effect Parade");
            while (!o.keepEffects && parade.numProperties) { parade.property(1).remove(); }
            d.name = (o.prefix || src.name) + " " + (o.label || "glow") + " " + radii[i];
            U.fx(d, "ADBE Solid Composite", { "ADBE Solid Composite-0002": [0, 0, 0] });
            if (o.colors && o.colors[i]) { U.fx(d, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": o.colors[i] }); }
            U.fx(d, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": radii[i], "ADBE Gaussian Blur 2-0003": 0 });
            U.gain(d, weights[i]);
            d.blendingMode = BlendingMode.ADD;
            out.push(d.name);
        }
        out.cleared = cleared;
        return out;
    }
    // stack(layer, o): n copies above the layer from plan(o). o.colors: optional [r,g,b] per copy for a falloff that changes color on a white
    // source. Gaussian Blur, not Fast Box Blur: box copies lost the light outside the shape layer's bounds. o.keepEffects as in copies().
    // Returns {copies, radii, weights, warnings}: a warning names the effects cleared from the copies.
    function stack(src, o) {
        var p = plan(o), cp = copies(src, p.radii, p.weights, { colors: p.colors, prefix: p.prefix, label: "glow", keepEffects: o && o.keepEffects });
        return { copies: cp, radii: p.radii, weights: p.weights, warnings: cp.cleared.length ? ["effects cleared on the copies (" + cp.cleared.join(", ") + "): content they draw does not bloom; pass keepEffects or precompose"] : [] };
    }
    // gain(comp, srcName, total, o): rewrite each copy's Exposure for a new total. Returns the weights.
    function gain(c, srcName, total, o) {
        var q = U.merge(o || {}, { total: total }), p = plan(q), i, l;
        for (i = 0; i < p.radii.length; i++) {
            l = c.layer(srcName + " glow " + p.radii[i]);
            l.property("ADBE Effect Parade").property("ADBE Exposure2").property("ADBE Exposure2-0003").setValue(U.stops(p.weights[i]));
        }
        return p.weights;
    }
    return { DEFAULTS: DEFAULTS, plan: plan, copies: copies, stack: stack, gain: gain };
})();

AEX.light = (function () {
    var U = AEX.vfxu, BLACK = [0, 0, 0];
    // TONES at luminance 0, 0.25, 0.5, 0.75, 1: black, ember (mid x 0.3), coral, hot coral, cream. Keep the dark tone in the hue of the mid
    // tone: a navy dark tone with a coral mid turned dim sparks lavender. Every channel of every tone at 0.95 or less: a bright tone with red
    // at 1.0 (#FF8A5C) added 1,068 to 11,209 px of red at 255 to a pulse on a dark plate (frames 0 to 12 after the hit); [0.94, 0.51,
    // 0.34] adds 3 to 220 px, on top of the plate's own speculars.
    var TONES = { shadow: BLACK, dark: U.hex("#43150D"), mid: U.hex("#E0452C"), bright: [0.94, 0.51, 0.34], high: U.hex("#F1E9D8") };
    var MAXCH = 0.95;
    // check(tones): warnings for a tone with a channel above MAXCH (that channel clips in the core). Returns an array of strings.
    function check(t) {
        var w = [], k, i;
        for (k in t) { if (t.hasOwnProperty(k) && t[k] && t[k].length === 3) { for (i = 0; i < 3; i++) { if (t[k][i] > MAXCH) { w.push("tone " + k + " has channel " + i + " at " + t[k][i] + " (above " + MAXCH + "): it clips in the core"); break; } } } }
        return w;
    }
    // tones(o): TONES with o's own keys on top (a partial override keeps the other tones).
    function tones(o) { return U.merge(TONES, o); }
    // radii(r0, n): doubling radii (12, 24, 48, 96, 192). weights(total, n, k): n weights summing to total, each k x the previous.
    function radii(r0, n) { var a = [], i; for (i = 0; i < n; i++) { a.push(r0 * Math.pow(2, i)); } return a; }
    function weights(total, n, k) { var a = [], s = 0, i; for (i = 0; i < n; i++) { a.push(Math.pow(k, i)); s += a[i]; } for (i = 0; i < n; i++) { a[i] = a[i] * total / s; } return a; }
    // bloom(layer, {radii, weights}): Gaussian copies named "<layer> bloom <radius>" (AEX.glow.copies). Returns the copy names.
    function bloom(src, o) { return AEX.glow.copies(src, o.radii, o.weights, { label: "bloom" }); }
    // map(layer, tones), also toneMap (the name to call from other modules: ae_check reads ".map(" as the ES5 array method): CC Toner in Pentone mode (Tones -0005 = 3): shadow, dark, mid, bright, high at luminance 0, 0.25, 0.5, 0.75, 1. Returns the effect.
    function map(l, t) {
        t = t ? tones(t) : TONES;
        return U.fx(l, "CC Toner", { "CC Toner-0005": 3, "CC Toner-0003": t.shadow || BLACK, "CC Toner-0007": t.dark, "CC Toner-0002": t.mid, "CC Toner-0006": t.bright, "CC Toner-0001": t.high }, "Light map");
    }
    // rig(comp, name, o): comps <name>_light (put gray light layers here with add()) and <name>_sum (black, light in Add, bloom copies),
    // and a layer <name> in comp with o.gain, the map (o.tones, partial override of TONES) and Add. o.bloom default AEX.glow.plan({r0 12, n 5,
    // total 2.0, k 0.75}). o.headroom (h, 1 = off; 2 for a hit whose core and bloom sum above 1, which reads as a flat pale disc at the attack).
    // Comp names must be new: a second rig with the same name throws. Returns {light, sum, layer, bloom, warnings}.
    function rig(c, name, o) {
        o = o || {};
        var lc = AEK.build.comp(name + "_light", { width: c.width, height: c.height, fps: c.frameRate, duration: c.duration });
        var hc = AEK.build.comp(name + "_sum", { width: c.width, height: c.height, fps: c.frameRate, duration: c.duration });
        AEK.build.solid(hc, "BLACK", BLACK);
        var ll = hc.layers.add(lc);
        ll.name = "LIGHT";
        ll.blendingMode = BlendingMode.ADD;
        var b = o.bloom || AEX.glow.plan({ r0: 12, n: 5, total: 2.0, k: 0.75 }), hr = o.headroom || 1, i;
        if (hr > 1) { b = { radii: b.radii, weights: [] }; for (i = 0; i < b.radii.length; i++) { b.weights.push((o.bloom || AEX.glow.plan({ r0: 12, n: 5, total: 2.0, k: 0.75 })).weights[i] / hr); } }
        if (b.radii.length) { bloom(ll, b); }
        if (hr > 1) { U.gain(ll, 1 / hr, "Headroom"); }
        var l = c.layers.add(hc);
        l.name = name;
        if (o.gain) { U.gain(l, o.gain, "Gain"); }
        // headroom: the sum is scaled by 1 / h before it clamps at 1, then a gamma of h brings the mid tones back; only a sum at h or more
        // reaches the top tone, so a hot core rolls off instead of a flat disc of the top tone. The gamma also lifts the faint bloom tails into
        // visible boxes (the copies' bounds): Input Black o.headroomBlack (0.02) cuts them
        if (hr > 1) { U.fx(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.headroomBlack === undefined ? 0.02 : o.headroomBlack, "ADBE Easy Levels2-0005": hr }, "Headroom shoulder"); }
        map(l, o.tones);
        l.blendingMode = BlendingMode.ADD;
        return { light: lc, sum: hc, layer: l, bloom: b, warnings: check(tones(o.tones)) };
    }
    // add(layer, lum): a light layer in the rig: Add, and a linear gain so its brightest pixel sits at luminance lum on the map.
    // Levels that worked: rings and strokes 0.35 to 0.5 (the bloom lifts them), sparks 0.5 to 1, flame body 0.85. Returns the layer.
    function add(l, lum) {
        l.blendingMode = BlendingMode.ADD;
        if (lum !== undefined && lum !== 1) { U.gain(l, lum, "Light level"); }
        return l;
    }
    return { TONES: TONES, MAXCH: MAXCH, check: check, tones: tones, hex: U.hex, radii: radii, weights: weights, bloom: bloom, map: map, toneMap: map, rig: rig, add: add };
})();

AEX.pn = (function () {
    // Constants measured on a 1920x1080 layer, default Effect Camera, Explosive animation.
    var K = {
        perSecPerRate: 110,     // particles alive = 110 x Birth Rate x Longevity (s), at 24, 30, 60 fps and any layer size
        burstPerRateSec: 132,   // held-rate burst: about 4.4 x Birth Rate particles per frame at 30 fps (count = rate x frames x 132 / fps)
        sizePerWidth: 0.1,      // Birth Size 1 = layer width / 10 px diameter
        diamPerWidth: 0.075,    // measured on screen (06b, type 4, 10 % of peak): Birth Size 1 = 0.075 x width px; sparks() sizes with it
        speedPerWidth: 0.58,    // Velocity 1 = 0.58 x width px/s at the outer edge (p95) of an Explosive burst; median 0.62 of that
        gravPerWidth: 3.2,      // Gravity 1 = 3.2 x width px/s^2 with Resistance 0
        resPerUnit: 0.7,        // Resistance R slows speed as exp(-0.7 R t): stop distance = speed / (0.7 R)
        minRate: 0.05           // a Birth Rate below this can emit nothing for seconds (embers_dust, 02_diag): sparks() warns
    };
    // smallest Birth Size that stays visible (peak >= 0.15 on >= 90 % of particles) on a 1920 layer, per Particle Type
    var MIN_SIZE = { 2: 0.004, 4: 0.015, 5: 0.015, 6: 0.015, 7: 0.03, 11: 0.002, 12: 0.002, 16: 0.002 };
    // sparks(layer, o): CC Particle World from on-screen targets. o = {count, life, diameter (px), speed (outer px/s), stop (px), fall (px/s^2),
    //   burstFrames (count is then the total of a burst starting at o.at s), type (default 5), deathDiameter, color, deathColor,
    //   transfer (default 1 Composite), opacity, radius, sizeVar, seed, name}. Returns the settings written and warnings about invisible sizes.
    function sparks(l, o) {
        var c = l.containingComp, w = l.width, fps = c.frameRate, warn = [], type = o.type || 5;
        var size = o.diameter / (w * K.diamPerWidth), dsize = (o.deathDiameter === undefined ? o.diameter : o.deathDiameter) / (w * K.diamPerWidth);
        var minS = MIN_SIZE[type] * (1920 / w);
        if (size < minS) { warn.push("birth diameter " + o.diameter + " px is below the visible minimum for type " + type + " (" + (minS * w * K.diamPerWidth).toFixed(1) + " px)"); }
        if (size >= minS && dsize < minS && type !== 1) { warn.push("death diameter fades below visible: the spark vanishes at " + Math.round(100 * (size - minS) / Math.max(size - dsize, 1e-6)) + " % of its life"); }
        var vel = o.speed / (K.speedPerWidth * w);
        var res = o.stop ? o.speed / (K.resPerUnit * o.stop) : 0;
        var grav = o.fall ? o.fall / (K.gravPerWidth * w) : 0;
        var rate = o.burstFrames ? o.count * fps / (K.burstPerRateSec * o.burstFrames) : o.count / (K.perSecPerRate * o.life);
        if (rate < K.minRate) { warn.push("Birth Rate " + rate.toFixed(4) + " is below " + K.minRate + ": it can emit nothing for seconds; raise count, shorten life or hold the burst fewer frames"); }
        var r = o.radius === undefined ? 0.005 : o.radius;
        var fx = AEX.vfx.pw(l, { birthRate: o.burstFrames ? 0 : rate, longevity: o.life, velocity: vel, extra: 0, gravity: grav, resistance: res,
            rx: r, ry: r, rz: r, type: type, birthSize: size, deathSize: dsize, sizeVar: o.sizeVar || 0, maxOpacity: o.opacity || 100,
            birthColor: o.color || [1, 1, 1], deathColor: o.deathColor || o.color || [1, 1, 1], transfer: o.transfer || 1, seed: o.seed || 0 }, o.name);
        if (o.burstFrames) {
            var br = AEX.vfx.pwProp(fx, "birthRate"), t0 = o.at || 0, k;
            if (t0 > 0) { br.setValueAtTime(0, 0); }
            br.setValueAtTime(t0, rate); br.setValueAtTime(t0 + o.burstFrames / fps, 0);
            for (k = 1; k <= br.numKeys; k++) { br.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD); }
        }
        return { effect: fx.name, birthRate: rate, velocity: vel, resistance: res, gravity: grav, birthSize: size, deathSize: dsize, warnings: warn };
    }
    return { K: K, MIN_SIZE: MIN_SIZE, sparks: sparks };
})();

AEX.burst = (function () {
    var U = AEX.vfxu, CREAM = U.PALETTE.cream, CORAL = U.PALETTE.coral, WHITE = [1, 1, 1], BLACK = [0, 0, 0];
    function tr(l, mn) { return l.property("ADBE Transform Group").property(mn); }
    // keys(prop, [[t, v], ...], cb): keys eased by a cubic bezier between each pair. Returns the property.
    function keys(p, kv, cb) {
        var i;
        for (i = 0; i < kv.length; i++) { p.setValueAtTime(kv[i][0], kv[i][1]); }
        for (i = 1; i < p.numKeys; i++) { AEK.motion.bezier(p, i, i + 1, cb || [0.2, 0.7, 0.3, 1]); }
        return p;
    }
    // env(o, life): the hit's time curve as [[t, multiplier]]: attack 2 frames, short hold, long decay over about 1.6 x life s.
    function env(o, life) {
        var f = 1 / 30, a = o.at;
        life = life || 1;
        return [[0, 0], [a, 0], [a + 2 * f, 1], [a + 5 * f, 0.85], [a + 0.35 * life, 0.32], [a + 0.9 * life, 0.08], [a + 1.6 * life, 0]];
    }
    function opacityEnv(l, o, gain, life) {
        var e = env(o, life), kv = [], i;
        for (i = 0; i < e.length; i++) { kv.push([e[i][0], Math.min(100, 100 * e[i][1] * gain)]); }
        return keys(tr(l, "ADBE Opacity"), kv, [0.25, 0.6, 0.35, 1]);
    }
    // hold(fx, rate, at, frames, fps): Birth Rate 0, rate held for frames from at, then 0 (hold keys).
    function hold(fx, rate, at, frames, fps) {
        var br = fx.property("CC Particle World-0004"), k;
        br.setValue(0);
        if (at > 0) { br.setValueAtTime(0, 0); }
        br.setValueAtTime(at, rate); br.setValueAtTime(at + frames / fps, 0);
        for (k = 1; k <= br.numKeys; k++) { br.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD); }
    }
    // plane(comp, name, o, p): one CC Particle World layer from pixel targets (AEX.pn constants), producer at o.center, Direction Axis at o.dir
    // degrees (Y is screen-down positive). Cone Axis (anim 3) emits on a cone SHELL at p.angle from the axis: above 90 the burst goes backwards.
    // Colors p.c0 to p.c1, or white to gray p.fade when no c0 (gray light for a rig). p = {count, frames, life, d, dd, speed, stop, fall, type,
    // anim, angle, extra, sizeVar, op, c0, c1, fade, radius, seedOff, delay, mb}. Returns the solid.
    function plane(c, name, o, p) {
        var K = AEX.pn.K, w = c.width, s = AEK.build.solid(c, name, BLACK), fd = p.fade === undefined ? 0.35 : p.fade;
        var th = (o.dir === undefined ? -90 : o.dir) * Math.PI / 180;
        var fx = AEX.vfx.pw(s, { birthRate: 0, longevity: p.life,
            x: (o.center[0] - c.width / 2) / w, y: (o.center[1] - c.height / 2) / w, z: 0,
            rx: p.radius || 0.004, ry: p.radius || 0.004, rz: p.radius || 0.004,
            animation: p.anim || 1, axisX: Math.cos(th), axisY: Math.sin(th), axisZ: 0, extraAngle: p.angle || 360,
            velocity: p.speed / (K.speedPerWidth * w), extra: p.extra === undefined ? 0.6 : p.extra,
            resistance: p.stop ? p.speed / (K.resPerUnit * p.stop) : 0, gravity: (p.fall || 0) / (K.gravPerWidth * w),
            type: p.type || 5, birthSize: p.d / (w * K.sizePerWidth), deathSize: (p.dd === undefined ? p.d : p.dd) / (w * K.sizePerWidth),
            sizeVar: p.sizeVar || 0, maxOpacity: p.op || 100, colorMap: 2, birthColor: p.c0 || WHITE, deathColor: p.c1 || (p.c0 ? p.c0 : [fd, fd, fd]),
            transfer: 1, seed: (o.seed || 0) + (p.seedOff || 0) });
        hold(fx, p.count * c.frameRate / (K.burstPerRateSec * p.frames), o.at + (p.delay || 0), p.frames, c.frameRate);
        if (p.mb === true || (p.mb !== false && !p.c0)) { s.motionBlur = true; }
        return s;
    }
    // cone(comp, name, center, R, lum): a square solid with a radial Gradient Ramp, white at the center to black at R, at light level lum. Returns the solid.
    function cone(c, name, center, R, lum) {
        var sz = Math.ceil(2 * R + 4), h = sz / 2, s = AEK.build.solid(c, name, BLACK, { width: sz, height: sz });
        U.fx(s, "ADBE Ramp", { "ADBE Ramp-0001": [h, h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [h + R, h], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 2 });
        tr(s, "ADBE Position").setValue(center);
        AEX.light.add(s, lum);
        return s;
    }
    // core(lightComp, o): three cones (34 / 110 / 320 px x scale at light 1.05 / 0.30 / 0.07 x energy), scale 35 to 125 to 70 %, opacity on the
    // hit envelope. A real falloff once the hit decays; at the attack the center is the sum of everything, so budget it there. Returns the names.
    function core(lc, o) {
        var s = o.scale || 1, e = o.energy || 1, i, l, out = [];
        var spec = [["CORE_TIGHT", 34 * s, 1.05 * e], ["CORE_MID", 110 * s, 0.3 * e], ["CORE_WIDE", 320 * s, 0.07 * e]];
        for (i = 0; i < spec.length; i++) {
            l = cone(lc, spec[i][0], o.center, spec[i][1], spec[i][2]);
            opacityEnv(l, o, 1, i === 0 ? 0.8 : 1.6);
            keys(tr(l, "ADBE Scale"), [[o.at, [35, 35]], [o.at + 3 / 30, [125, 125]], [o.at + 0.5, [85, 85]], [o.at + 1.4, [70, 70]]], [0.2, 0.8, 0.3, 1]);
            out.push(l.name);
        }
        return out;
    }
    // streaks(lightComp, o): the body of the hit as procedural radial streaks. In a square comp of side D = 2 x 700 x scale x reach: two Fractal
    // Noise column layers (Uniform Scaling off; thin 2.2 x 260, contrast 420, brightness -95; wide 9 x 900, contrast 330, brightness -75 at 75 %)
    // scrolled outward with an eased deceleration, times an angle comp (omni floor o.omni 0.08 plus a feathered column o.cone 0.32 D wide at
    // x = D / 2) and a front comp (tail-to-head ramp, a cut ahead of the head, a fixed rim fade 0.6 D to 0.92 D). Then Displacement Map, vertical
    // only, o.ragged 0.2 x D from a column-noise precomp (ragged lengths), Polar Coordinates Rect to Polar (top row to the center), CC Radial
    // Fast Blur 30. The layer sits at o.center, rotated o.dir - 90. Returns the layer.
    function streaks(lc, o) {
        var s = o.scale || 1, R = Math.round(700 * s * (o.reach || 1)), D = 2 * R, a = o.at, nm = o.name || "E", fps = lc.frameRate, dur = lc.duration;
        var rc = AEK.build.comp(nm + "_streak_rect", { width: D, height: D, fps: fps, duration: dur });
        var n1 = AEK.build.solid(rc, "COLS_THIN", BLACK), n2 = AEK.build.solid(rc, "COLS_WIDE", BLACK), f1, f2;
        f1 = U.fx(n1, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 420, "ADBE Fractal Noise-0005": -95, "ADBE Fractal Noise-0009": 0,
            "ADBE Fractal Noise-0011": 2.2, "ADBE Fractal Noise-0012": 260, "ADBE Fractal Noise-0015": 2, "ADBE Fractal Noise-0027": (o.seed || 0) + 11 });
        f2 = U.fx(n2, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 330, "ADBE Fractal Noise-0005": -75, "ADBE Fractal Noise-0009": 0,
            "ADBE Fractal Noise-0011": 9, "ADBE Fractal Noise-0012": 900, "ADBE Fractal Noise-0015": 2, "ADBE Fractal Noise-0027": (o.seed || 0) + 17 });
        n2.blendingMode = BlendingMode.ADD;
        tr(n2, "ADBE Opacity").setValue(75);
        keys(f1.property("ADBE Fractal Noise-0013"), [[a, [D / 2, 0]], [a + 1.2, [D / 2, 0.55 * D]]], [0.1, 0.75, 0.3, 1]);
        keys(f2.property("ADBE Fractal Noise-0013"), [[a, [D / 2, 0]], [a + 1.2, [D / 2, 0.3 * D]]], [0.1, 0.75, 0.3, 1]);
        f1.property("ADBE Fractal Noise-0023").expression = "time * 160";
        f2.property("ADBE Fractal Noise-0023").expression = "time * 90";
        var ac = AEK.build.comp(nm + "_streak_angle", { width: D, height: D, fps: fps, duration: dur });
        var fl = o.omni === undefined ? 0.08 : o.omni, cw = D * (o.cone || 0.32);
        AEK.build.solid(ac, "FLOOR", [fl, fl, fl]);
        var band = AEK.build.solid(ac, "CONE", WHITE);
        U.rect(band, D / 2 - cw / 2, -10, D / 2 + cw / 2, D + 10, [cw * 0.9, 0]);
        var al = rc.layers.add(ac); al.blendingMode = BlendingMode.MULTIPLY;
        var fc = AEK.build.comp(nm + "_streak_front", { width: D, height: D, fps: fps, duration: dur });
        var body = AEK.build.solid(fc, "BODY", BLACK), cut = AEK.build.solid(fc, "CUT", BLACK);
        U.fx(body, "ADBE Ramp", { "ADBE Ramp-0002": BLACK, "ADBE Ramp-0004": WHITE, "ADBE Ramp-0005": 1 });
        U.fx(cut, "ADBE Ramp", { "ADBE Ramp-0002": WHITE, "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        cut.blendingMode = BlendingMode.MULTIPLY;
        var cb = [0.08, 0.8, 0.25, 1], hd = [[a, 0.03], [a + 0.12, 0.4], [a + 0.45, 0.72], [a + 1.6, 0.88]], tl = [[a, 0], [a + 0.18, 0], [a + 0.7, 0.45], [a + 1.4, 0.85]];
        var pb0 = body.property("ADBE Effect Parade").property(1), pc0 = cut.property("ADBE Effect Parade").property(1), kv0 = [], kv1 = [], kv2 = [], kv3 = [], i;
        for (i = 0; i < hd.length; i++) { kv1.push([hd[i][0], [D / 2, hd[i][1] * D]]); kv2.push([hd[i][0], [D / 2, hd[i][1] * D - 4]]); kv3.push([hd[i][0], [D / 2, hd[i][1] * D + 0.05 * D]]); }
        for (i = 0; i < tl.length; i++) { kv0.push([tl[i][0], [D / 2, tl[i][1] * D]]); }
        keys(pb0.property("ADBE Ramp-0001"), kv0, cb);
        keys(pb0.property("ADBE Ramp-0003"), kv1, cb);
        keys(pc0.property("ADBE Ramp-0001"), kv2, cb);
        keys(pc0.property("ADBE Ramp-0003"), kv3, cb);
        var rim = AEK.build.solid(fc, "RIM", BLACK);
        U.fx(rim, "ADBE Ramp", { "ADBE Ramp-0001": [D / 2, 0.6 * D], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [D / 2, 0.92 * D], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        rim.blendingMode = BlendingMode.MULTIPLY;
        var frl = rc.layers.add(fc); frl.blendingMode = BlendingMode.MULTIPLY;
        var pc = AEK.build.comp(nm + "_streaks", { width: D, height: D, fps: fps, duration: dur });
        pc.layers.add(rc);
        // ragged lengths: each column shifted along the radius by a column noise; the map is a precomp (Displacement Map reads its source)
        var mc = AEK.build.comp(nm + "_streak_len", { width: D, height: D, fps: fps, duration: dur });
        var mn = AEK.build.solid(mc, "LEN", BLACK);
        U.fx(mn, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 160, "ADBE Fractal Noise-0009": 0, "ADBE Fractal Noise-0011": 14, "ADBE Fractal Noise-0012": 10000,
            "ADBE Fractal Noise-0015": 3, "ADBE Fractal Noise-0027": (o.seed || 0) + 23 });
        var ml = pc.layers.add(mc); ml.enabled = false; ml.moveToEnd();
        var rl = pc.layer(rc.name);
        U.fx(rl, "ADBE Displacement Map", { "ADBE Displacement Map-0001": ml.index, "ADBE Displacement Map-0002": 1, "ADBE Displacement Map-0003": 0,
            "ADBE Displacement Map-0004": 2, "ADBE Displacement Map-0005": (o.ragged === undefined ? 0.2 : o.ragged) * D, "ADBE Displacement Map-0006": 1 });
        U.fx(rl, "ADBE Polar Coordinates", { "ADBE Polar Coordinates-0001": 1, "ADBE Polar Coordinates-0002": 1 });
        if (o.radialSoft !== 0) { U.fx(rl, "CC Radial Fast Blur", { "CC Radial Fast Blur-0001": [D / 2, D / 2], "CC Radial Fast Blur-0002": o.radialSoft || 30, "CC Radial Fast Blur-0003": 1 }); }
        var l = lc.layers.add(pc);
        l.name = "STREAKS";
        tr(l, "ADBE Position").setValue(o.center);
        tr(l, "ADBE Rotate Z").setValue((o.dir === undefined ? -90 : o.dir) - 90);   // a 2D layer's rotation is ADBE Rotate Z (ADBE Rotation returns null)
        AEX.light.add(l, (o.streakLum || 0.9) * (o.energy || 1));
        opacityEnv(l, o, 1, o.streakLife || 2.2);
        return l;
    }
    // trails(layer, mode, o): "echo": Echo, Maximum operator (-0005 2: a bright head and a fading tail without stacking light), step o.step
    // (1/120 s) x o.n (16), decay o.decay (0.89); "widetime": CC Wide Time o.n backward steps (a faint smear). Put it first in the stack. Returns the effect.
    function trails(l, mode, o) {
        o = o || {};
        if (mode === "echo") {
            return U.fx(l, "ADBE Echo", { "ADBE Echo-0001": -(o.step || 1 / 120), "ADBE Echo-0002": o.n || 16, "ADBE Echo-0003": 1, "ADBE Echo-0004": o.decay || 0.89, "ADBE Echo-0005": 2 }, "Trails");
        }
        if (mode === "widetime") { return U.fx(l, "CC Wide Time", { "CC Wide Time-0001": 0, "CC Wide Time-0002": o.n || 6 }, "Trails"); }
        return null;
    }
    // sparks(lightComp, o): the accent, about 125 sparks at the peak (x o.count): leaders (14, 2,600 px/s, stop 900, cone 18), body (55, 1,100 px/s,
    // 6 px, size variation 85, cone 40), arcs (12, gravity 520 px/s^2, cone 55), far (24 tiny hard spheres, explosive, 55 %), linger (16 slow, rising,
    // flickering), near (3 discs 70 to 110 px, Camera Lens Blur 26, 10 %). White to gray (light), Composite inside, shutter 270 in the sparks comp,
    // Echo trails first (o.trail "echo"). Returns the precomp layer in the light comp.
    function sparks(lc, o) {
        var s = o.scale || 1, n = o.count || 1, nm = o.name || "E";
        var c = AEK.build.comp(nm + "_sparks", { width: lc.width, height: lc.height, fps: lc.frameRate, duration: lc.duration });
        c.motionBlur = true; c.shutterAngle = 270;
        plane(c, "FAR", o, { count: 24 * n, frames: 2, life: 1.3, d: 2.4, dd: 2.4, type: 4, speed: 380 * s, stop: 230 * s, fall: 30, anim: 1, angle: 360, extra: 0.6, sizeVar: 30, op: 55, fade: 0.4, seedOff: 3 });
        plane(c, "BODY", o, { count: 55 * n, frames: 2, life: 1.2, d: 6 * s, dd: 3, type: 5, speed: 1100 * s, stop: 420 * s, fall: 60, anim: 3, angle: 40, extra: 0.9, sizeVar: 85, op: 100, fade: 0.3, seedOff: 7 });
        plane(c, "LEADERS", o, { count: 14 * n, frames: 1, life: 0.75, d: 4.5 * s, dd: 3, type: 5, speed: 2600 * s, stop: 900 * s, fall: 0, anim: 3, angle: 18, extra: 0.5, sizeVar: 50, op: 100, fade: 0.45, seedOff: 13 });
        plane(c, "ARCS", o, { count: 12 * n, frames: 2, life: 1.6, d: 4 * s, dd: 3, type: 5, speed: 900 * s, stop: 1400 * s, fall: 520 * s, anim: 3, angle: 55, extra: 0.6, sizeVar: 60, op: 100, fade: 0.35, seedOff: 19, delay: 1 / 30 });
        var lg = plane(c, "LINGER", o, { count: 16 * n, frames: 3, life: 2.2, d: 3.6 * s, dd: 2.6, type: 5, speed: 300 * s, stop: 220 * s, fall: -25, anim: 3, angle: 70, extra: 0.8, sizeVar: 60, op: 100, fade: 0.5, seedOff: 37 });
        tr(lg, "ADBE Opacity").expression = "85 + 15 * noise([time * 6, 1])";
        var nr = plane(c, "NEAR", o, { count: 3 * n, frames: 2, life: 1.0, d: 70 * s, dd: 110 * s, type: 4, speed: 1500 * s, stop: 2200 * s, fall: 0, anim: 1, extra: 0.6, sizeVar: 50, op: 10, fade: 0.6, seedOff: 29, mb: false });
        U.fx(nr, "ADBE Camera Lens Blur", { "ADBE Camera Lens Blur-0001": 26 * s });
        var l = lc.layers.add(c);
        l.name = "SPARKS"; l.motionBlur = true;
        if (o.trail && o.trail !== "none") { trails(l, o.trail, o.trailOpts); }
        AEX.light.add(l, (o.sparkLum || 1.0) * (o.energy || 1));
        return l;
    }
    // airGlow(lightComp, o): Fractal Noise haze in the light comp seen through a radial luma matte (460 px x scale), light o.airLum 0.14, on the envelope. Returns the layer.
    function airGlow(lc, o) {
        var s = o.scale || 1, hz = AEK.build.solid(lc, "AIR", BLACK);
        U.fx(hz, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 90, "ADBE Fractal Noise-0005": -8, "ADBE Fractal Noise-0010": 420 * s, "ADBE Fractal Noise-0015": 5,
            "ADBE Fractal Noise-0027": (o.seed || 0) + 41 });
        hz.property("ADBE Effect Parade").property(1).property("ADBE Fractal Noise-0023").expression = "time * 40";
        var m = AEK.build.solid(lc, "AIR_MATTE", BLACK);
        U.fx(m, "ADBE Ramp", { "ADBE Ramp-0001": o.center, "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [o.center[0] + 460 * s, o.center[1]], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 2 });
        hz.setTrackMatte(m, TrackMatteType.LUMA);
        AEX.light.add(hz, (o.airLum || 0.14) * (o.energy || 1));
        opacityEnv(hz, o, 1, 1.4);
        return hz;
    }
    // build(host, o): an energy hit leaving a point, all gray light in one AEX.light rig (bloom radii 10 to 320, total 1.0), colored once.
    // Body = streaks(), accent = sparks() with Echo trails, core = three cones, air glow. Motion blur switched on in every comp of the chain and on
    // every precomp layer (particles two comps deep get none otherwise). o = {name, center [x, y], dir (deg: 0 right, 90 down, -90 up), scale, energy,
    // seed, at (s), count, streaks (false = none), particles (false), trail ("echo" default, "widetime", "none"), trailOpts, core, air, bloom, tones}.
    // The rig layer is in Add as built: over a lit plate set it to Screen. Returns {name, light, layer, air, streaks, sparks, core} (names; parts
    // switched off are absent).
    function build(host, o) {
        var R = { name: o.name || "E" }, li;
        host.motionBlur = true;
        var rig = AEX.light.rig(host, R.name, { tones: o.tones, bloom: o.bloom || { radii: AEX.light.radii(10, 6), weights: AEX.light.weights(1.0, 6, 0.75) } });
        rig.light.motionBlur = true; rig.sum.motionBlur = true;
        for (li = 1; li <= rig.sum.numLayers; li++) { if (rig.sum.layer(li).source instanceof CompItem) { rig.sum.layer(li).motionBlur = true; } }
        rig.layer.motionBlur = true;
        if (o.air !== false) { R.air = airGlow(rig.light, o).name; }
        if (o.streaks !== false) { R.streaks = streaks(rig.light, o).name; }
        if (o.particles !== false) {
            if (o.trail === undefined) { o.trail = "echo"; }
            R.sparks = sparks(rig.light, o).name;
        }
        if (o.core !== false) { R.core = core(rig.light, o); }
        R.light = rig.light.name; R.layer = rig.layer.name;
        return R;
    }
    // planes(host, o): the particle-only burst: a precomp (far sharp, three follower speed tiers, line leaders, embers, near bokeh, 4-frame flash), added to host
    // in Add with a blurred copy as the glow. o = {name, center [x, y] px, at (s), dir (deg, 0 right, -90 up), scale (speed and size), count
    // (multiplier), seed, flash (peak %), glow (copy opacity %, 0 inside a light rig), followOpacity, lineScale (0.1), duration}. Used as the burst inside AEX.integrate; for a hero hit use build(). Returns {comp, layer, glow} (names).
    function planes(host, o) {
        var sc = o.scale || 1, n = o.count || 1, fps = host.frameRate, R = {};
        var c = AEK.build.comp(o.name || "BURST", { width: host.width, height: host.height, fps: fps, duration: o.duration || host.duration, bg: [0, 0, 0] });
        // far plane: small, sharp, slower, dimmer, cooler
        plane(c, "FAR", o, { count: 260 * n, frames: 2, life: 1.1, d: 3 * sc, dd: 3 * sc, type: 4, speed: 420 * sc, stop: 170 * sc, fall: 40, anim: 1, extra: 0.8,
            sizeVar: 30, op: 60, c0: U.mix(CREAM, CORAL, 0.25), c1: U.mix(CORAL, [0.2, 0.25, 0.35], 0.4), seedOff: 11 });
        // followers: three speed tiers fill the inside (one speed alone is a hollow shell); Cone Axis on the fast tiers at 40 and 70 degrees
        // (Cone Axis emits on a shell at that angle from the axis: above 90 the particles go backwards); layer motion blur on
        var tiers = [[1, 0.3, 3, 40], [0.6, 0.35, 3, 70], [0.35, 0.35, 1, 360]], t, fl0;
        for (t = 0; t < tiers.length; t++) {
            fl0 = plane(c, "MID_FOLLOW_" + (t + 1), o, { count: 900 * n * tiers[t][1], frames: 3, life: 2.0, d: 7 * sc, dd: 3.5 * sc, type: 5, speed: 1100 * sc * tiers[t][0],
                stop: 420 * sc * tiers[t][0], fall: 80, anim: tiers[t][2], angle: tiers[t][3], extra: 0.3, sizeVar: 60, op: o.followOpacity || 100, c0: CREAM, c1: CORAL, seedOff: 23 + t });
            fl0.motionBlur = true;
        }
        // leaders: Line type streaks; Line renders far more light per Birth Rate unit, so its rate is scaled by lineScale (0.1)
        plane(c, "MID_LEAD", o, { count: 36 * n * (o.lineScale || 0.1), frames: 2, life: 0.55, d: 4, type: 1, speed: 2300 * sc, stop: 900 * sc, fall: 0, anim: 3, angle: 70, extra: 0.5,
            op: 100, c0: CREAM, c1: U.mix(CREAM, CORAL, 0.6), seedOff: 37 });
        // embers: a few long-lived, slow, rising, flickering
        var em = plane(c, "EMBERS", o, { count: 30 * n, frames: 3, life: 3.4, d: 7 * sc, dd: 5 * sc, type: 5, speed: 380 * sc, stop: 300 * sc, fall: -45, anim: 1, extra: 0.7,
            sizeVar: 40, op: 100, c0: U.mix(CREAM, CORAL, 0.3), c1: U.mix(CREAM, CORAL, 0.75), seedOff: 53 });
        em.property("ADBE Transform Group").property("ADBE Opacity").expression = "seedRandom(index, true); 72 + 28 * noise([time * 7, 3]);";
        // near plane: a few large defocused discs crossing the lens fast
        var nr = plane(c, "NEAR_BOKEH", o, { count: 6 * n, frames: 2, life: 0.9, d: 90 * sc, dd: 130 * sc, type: 4, speed: 1900 * sc, stop: 2400 * sc, fall: 0, anim: 1, extra: 0.6,
            sizeVar: 40, op: 18, c0: U.mix(CREAM, CORAL, 0.4), c1: CORAL, seedOff: 71 });
        U.fx(nr, "ADBE Camera Lens Blur", { "ADBE Camera Lens Blur-0001": 22 * sc });
        // flash: 4 frames, a feathered disc on a solid larger than its feather (a small solid showed a square edge), eased, peak under 30 %
        var fl = AEK.build.solid(c, "FLASH", CREAM, { width: 1400, height: 1400 });
        fl.property("ADBE Transform Group").property("ADBE Position").setValue([o.center[0], o.center[1]]);
        U.ellipse(fl, 700, 700, 220, 220, 280);
        var op = U.opacity(fl);
        op.setValueAtTime(o.at - 1 / fps, 0); op.setValueAtTime(o.at + 1 / fps, o.flash === undefined ? 26 : o.flash); op.setValueAtTime(o.at + 6 / fps, 0);
        AEK.motion.ease(op, 1, 33, 33); AEK.motion.ease(op, 2, 20, 33); AEK.motion.ease(op, 3, 60, 33);
        fl.blendingMode = BlendingMode.ADD;
        c.motionBlur = true;
        var L = host.layers.add(c); L.name = o.name || "BURST"; L.blendingMode = BlendingMode.ADD;
        var G = host.layers.add(c); G.name = (o.name || "BURST") + "_GLOW"; G.blendingMode = BlendingMode.ADD;
        U.fx(G, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 22 * sc, "ADBE Box Blur2-0002": 3 });
        U.opacity(G).setValue(o.glow === undefined ? 32 : o.glow);
        R.comp = c.name; R.layer = L.name; R.glow = G.name;
        return R;
    }
    return { build: build, streaks: streaks, core: core, cone: cone, sparks: sparks, trails: trails, airGlow: airGlow, env: env, plane: plane, planes: planes,
        CREAM: CREAM, CORAL: CORAL };
})();

AEX.atmo = (function () {
    var U = AEX.vfxu, CREAM = U.PALETTE.cream, CORAL = U.PALETTE.coral;
    // plane(comp, name, p): particles over a wide band, rising or drifting, each faded in and out by a custom color map
    // (black, color, hot, color, black) with Transfer Mode 3 Add: safe while sparse (under about 50 particles per 100x100 px).
    // p = {count (on screen), life, cy, ry, d (px), rise (px/s), drift (px/s), col, hot, turb, turbSize, turbSpeed, blur, flicker, seed}. Returns the solid.
    function plane(c, name, p) {
        var K = AEX.pn.K, w = c.width, s = AEK.build.solid(c, name, [0, 0, 0]);
        var fx = AEX.vfx.pw(s, { birthRate: p.count / (K.perSecPerRate * p.life), longevity: p.life,
            x: 0, y: (p.cy - c.height / 2) / w, z: 0, rx: 0.55, ry: p.ry, rz: 0.05,
            animation: 1, velocity: p.drift / (K.speedPerWidth * w), extra: 0, resistance: 10, gravity: -p.rise / (0.23 * w),
            type: 5, birthSize: p.d / (w * K.sizePerWidth), deathSize: p.d * 0.7 / (w * K.sizePerWidth), sizeVar: 50, maxOpacity: 100,
            colorMap: 1, transfer: 3, seed: p.seed || 0 });
        var cm = ["custom1", "custom2", "custom3", "custom4", "custom5"], cols = [[0, 0, 0], U.scale(p.col, 0.8), p.hot, U.scale(p.col, 0.7), [0, 0, 0]], i;
        for (i = 0; i < 5; i++) { AEX.vfx.pwProp(fx, cm[i]).setValue(cols[i]); }
        if (p.turb) {
            var td = U.fx(s, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": p.turb, "ADBE Turbulent Displace-0003": p.turbSize || 220 });
            td.property("ADBE Turbulent Displace-0006").expression = "time * " + (p.turbSpeed || 40) + ";";
        }
        if (p.blur) { U.fx(s, "ADBE Camera Lens Blur", { "ADBE Camera Lens Blur-0001": p.blur }); }
        // a + b * noise() averages a: keep a near 85 or the layer reads half as bright
        if (p.flicker) { U.opacity(s).expression = "seedRandom(" + (p.seed || 1) + ", true); " + (100 - p.flicker / 2) + " + " + (p.flicker / 2) + " * noise([time * 5, " + (p.seed || 1) + "]);"; }
        s.blendingMode = BlendingMode.ADD;
        return s;
    }
    // ellipseMask(layer, cx, cy, rx, ry, feather, mode, opacity): AEX.vfxu.ellipse with mode and opacity. Returns the mask.
    function ellipseMask(l, cx, cy, rx, ry, feather, mode, opacity) { return U.ellipse(l, cx, cy, rx, ry, feather, { mode: mode, opacity: opacity }); }
    // beam(comp, name, o, color, opacity): a feathered quad from o.beam [topX, topW, botX, botW], ramped darker down the shaft. Returns the solid.
    function beam(c, name, o, color, opacity) {
        var s = AEK.build.solid(c, name, color), m = s.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape(), a = o.beam;
        sh.vertices = [[a[0] - a[1] / 2, -80], [a[0] + a[1] / 2, -80], [a[2] + a[3] / 2, c.height + 80], [a[2] - a[3] / 2, c.height + 80]]; sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh); m.property("ADBE Mask Feather").setValue([o.beamFeather || 160, o.beamFeather || 160]);
        U.fx(s, "ADBE Ramp", { "ADBE Ramp-0001": [a[0], 0], "ADBE Ramp-0002": color, "ADBE Ramp-0003": [a[2], c.height], "ADBE Ramp-0004": U.scale(color, 0.25), "ADBE Ramp-0005": 1 });
        U.opacity(s).setValue(opacity);
        return s;
    }
    // loopPair(dst, sim, P, L, F, mode): two copies of a simulation comp (length P + L): A starts at -P, B starts at L - P and shows over the
    // last F seconds, crossfading A out and B in. Frame L of dst equals frame 0. Returns [A, B].
    function loopPair(dst, sim, P, L, F, mode) {
        var A = dst.layers.add(sim), B = dst.layers.add(sim), fps = dst.frameRate;
        A.name = sim.name + "_A"; B.name = sim.name + "_B";
        A.startTime = -P; A.outPoint = L + 1 / fps;
        B.startTime = L - P; B.inPoint = L - F; B.outPoint = L + 1 / fps;
        var oa = U.opacity(A), ob = U.opacity(B);
        oa.setValueAtTime(L - F, 100); oa.setValueAtTime(L, 0);
        ob.setValueAtTime(L - F, 0); ob.setValueAtTime(L, 100);
        A.blendingMode = mode || BlendingMode.ADD; B.blendingMode = mode || BlendingMode.ADD;
        return [A, B];
    }
    // build(host, o): embers and dust, three planes each, looped. Dust: 220 far motes at 5 px, 70 at 16 px, 24 soft discs at 110 px. o = {name, L (loop s, 4), P (pre-roll s, 4), F (crossfade s, 1), embers and dust
    // (count multipliers, 0 = none), beam [topX, topW, botX, botW] (dust only inside it), beamOpacity, warm (0 to 1), title [cx, cy, rx, ry]
    // (density hole), titleDensity (0.3), titleFeather, glow (copy opacity %), seed}. Returns {comps, layer} (names: AEK.core.layer(host, r.layer)).
    function build(host, o) {
        var L = o.L || 4, P = o.P || 4, F = o.F || 1, H = host.height, n = o.embers === undefined ? 1 : o.embers, dn = o.dust === undefined ? 1 : o.dust, sd = o.seed || 0;
        var ecol = U.mix(CREAM, CORAL, o.warm === undefined ? 0.8 : o.warm), ehot = U.mix(CREAM, ecol, 0.6), nm = o.name || "ATMO";
        var se = AEK.build.comp(nm + "_EMB", { width: host.width, height: H, fps: host.frameRate, duration: P + L + 0.1, bg: [0, 0, 0] });
        if (n > 0) {
            plane(se, "EMB_FAR", { count: 160 * n, life: 3.5, cy: H * 0.6, ry: 0.3, d: 3.4, rise: 35, drift: 8, col: U.scale(ecol, 0.65), hot: U.scale(ehot, 0.7), turb: 18, turbSize: 120, turbSpeed: 30, flicker: 30, seed: sd + 1 });
            plane(se, "EMB_MID", { count: 90 * n, life: 3.5, cy: H * 0.7, ry: 0.3, d: 6.5, rise: 70, drift: 14, col: ecol, hot: U.mix(ecol, CREAM, 0.45), turb: 30, turbSize: 200, turbSpeed: 45, flicker: 45, seed: sd + 2 });
            plane(se, "EMB_NEAR", { count: 12 * n, life: 2.5, cy: H * 0.5, ry: 0.3, d: 30, rise: 150, drift: 30, col: ecol, hot: ehot, turb: 50, turbSize: 300, turbSpeed: 60, flicker: 30, blur: 9, seed: sd + 3 });
        }
        var sdu = AEK.build.comp(nm + "_DUST", { width: host.width, height: H, fps: host.frameRate, duration: P + L + 0.1, bg: [0, 0, 0] });
        if (dn > 0) {
            // few motes, a slow rise, no swirl; a handful of large soft discs near the lens (Birth Rate of each plane stays above 0.05)
            plane(sdu, "DUST_FAR", { count: 220 * dn, life: 4, cy: H * 0.5, ry: 0.32, d: 5, rise: 5, drift: 4, col: U.scale(CREAM, 0.9), hot: U.mix(U.scale(CREAM, 0.9), [1, 1, 1], 0.13), seed: sd + 4 });
            plane(sdu, "DUST_MID", { count: 70 * dn, life: 4, cy: H * 0.5, ry: 0.32, d: 16, rise: 9, drift: 7, col: CREAM, hot: U.mix(CREAM, [1, 1, 1], 0.15), seed: sd + 5 });
            plane(sdu, "DUST_NEAR", { count: 24 * dn, life: 3.5, cy: H * 0.5, ry: 0.32, d: 110, rise: 16, drift: 12, col: U.scale(CREAM, 0.22), hot: U.scale(CREAM, 0.24), seed: sd + 6 });
        }
        var atmo = AEK.build.comp(nm, { width: host.width, height: H, fps: host.frameRate, duration: L + 2 / host.frameRate, bg: [0, 0, 0] });
        var R = { comps: [se.name, sdu.name, atmo.name] }, dp, bm;
        if (o.beam) {
            bm = beam(atmo, "BEAM_MATTE", o, [1, 1, 1], 100);
            dp = loopPair(atmo, sdu, P, L, F);
            dp[0].setTrackMatte(bm, TrackMatteType.LUMA); dp[1].setTrackMatte(bm, TrackMatteType.LUMA);
        } else { loopPair(atmo, sdu, P, L, F); }
        loopPair(atmo, se, P, L, F);
        // the visible beam sits in the host, outside the atmosphere comp, so the title hole does not cut it
        if (o.beam) { var bv = beam(host, nm + "_BEAM", o, U.scale(CREAM, 0.9), o.beamOpacity === undefined ? 16 : o.beamOpacity); bv.blendingMode = BlendingMode.ADD; }
        var al = host.layers.add(atmo); al.name = nm; al.blendingMode = BlendingMode.ADD;
        var gl = host.layers.add(atmo); gl.name = nm + "_GLOW"; gl.blendingMode = BlendingMode.ADD;
        U.fx(gl, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 10, "ADBE Box Blur2-0002": 3 });
        U.fx(gl, "ADBE Exposure2", { "ADBE Exposure2-0003": 1.5 });
        U.opacity(gl).setValue(o.glow === undefined ? 70 : o.glow);
        if (o.title) {
            var dm = AEK.build.solid(host, nm + "_DENSITY", [1, 1, 1]);
            U.ellipse(dm, o.title[0], o.title[1], o.title[2], o.title[3], o.titleFeather || 180, { mode: MaskMode.SUBTRACT, opacity: 100 * (1 - (o.titleDensity === undefined ? 0.3 : o.titleDensity)) });
            al.setTrackMatte(dm, TrackMatteType.ALPHA); gl.setTrackMatte(dm, TrackMatteType.ALPHA);
        }
        R.layer = al.name;
        return R;
    }
    return { build: build, plane: plane, loopPair: loopPair, ellipseMask: ellipseMask, CREAM: CREAM, CORAL: CORAL };
})();

AEX.smoke = (function () {
    var U = AEX.vfxu, P = U.PALETTE;
    // ellipse(layer, cx, cy, rx, ry, feather, inverted): AEX.vfxu.ellipse with the inverted flag. Returns the mask.
    function ellipse(l, cx, cy, rx, ry, feather, inverted) { return U.ellipse(l, cx, cy, rx, ry, feather, { inverted: inverted }); }
    // noise(comp, name, p, L): a solid with Fractal Noise looped over L with p.revs whole revolutions. Returns the solid.
    function noise(c, name, p, L) {
        var s = AEK.build.solid(c, name, [0, 0, 0]);
        U.fx(s, "ADBE Fractal Noise", { "ADBE Fractal Noise-0001": p.ftype || 1, "ADBE Fractal Noise-0004": p.contrast, "ADBE Fractal Noise-0005": p.brightness,
            "ADBE Fractal Noise-0009": 0, "ADBE Fractal Noise-0011": p.sw, "ADBE Fractal Noise-0012": p.sh, "ADBE Fractal Noise-0015": p.complexity || 6,
            "ADBE Fractal Noise-0017": p.subInf || 70, "ADBE Fractal Noise-0018": p.subScale || 56, "ADBE Fractal Noise-0027": p.seed || 0 });
        AEX.vfx.loopNoise(s.property("ADBE Effect Parade").property(1), c, L, p.revs);
        return s;
    }
    // density(host, o, name): precomp <name>_DENS, white smoke density on black, looping over o.L (two noise scales, Turbulent Displace,
    // CC Vector Blur o.wisp (6; above about 12 it combs smoke into hair), Fast Box Blur 7, feathered radial matte). Returns the comp.
    function density(host, o, nm) {
        var L = o.L, W = host.width, H = host.height, sd = o.seed || 0, k = o.scale || 1;
        var c = AEK.build.comp(nm + "_DENS", { width: W, height: H, fps: host.frameRate, duration: L + 2 / host.frameRate, bg: [0, 0, 0] });
        noise(c, "BIG", { contrast: 150, brightness: -18, sw: 900 * k, sh: 650 * k, complexity: 6, subInf: 65, revs: 1, seed: sd + 1 }, L);
        var sm = noise(c, "SMALL", { contrast: 120, brightness: 0, sw: 260 * k, sh: 200 * k, complexity: 5, subInf: 55, revs: 2, seed: sd + 2 }, L);
        sm.blendingMode = BlendingMode.MULTIPLY; U.opacity(sm).setValue(40);
        var adj = AEK.build.adjustment(c, "SHAPE");
        U.fx(adj, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 80, "ADBE Turbulent Displace-0003": 240, "ADBE Turbulent Displace-0005": 2, "ADBE Turbulent Displace-0010": sd + 3 });
        AEX.vfx.loopNoise(adj.property("ADBE Effect Parade").property(1), c, L, 1);
        U.fx(adj, "CC Vector Blur", { "CC Vector Blur-0002": o.wisp === undefined ? 6 : o.wisp });
        U.fx(adj, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 7, "ADBE Box Blur2-0002": 3 });
        var mt = AEK.build.solid(c, "RADIAL_MATTE", [0, 0, 0]);
        ellipse(mt, o.center[0], o.center[1], o.size[0], o.size[1], o.size[0] * 0.45, true);
        return c;
    }
    // build(host, o): a smoke plume from a source (AEX.plume): wisps of stringy noise rising through a widening, leaning plume mask, swayed more
    // with height, gray, shaded toward the far side, tinted, Screen at low opacity. o = {name, L, F, center [x, y] (the plume's middle), size
    // [rx, ry], light [dx, dy] (dx >= 0: lit from the left), shade, body (opacity %, 70), color, lean, scale (texture and sway scale; default
    // 2.2 x ry / 860 between 0.2 and 1, so a small wisp gets fine wisps instead of two blobs of the 860 px plume's texture), seed}. The gray plume comp is
    // <name>_DENS. Older keys (edge, edgeGain, lightPass, lightColor, wisp) are accepted and ignored. Returns {comps, layers, layer, grey} (names, so a job can return
    // them as JSON: the layer itself is AEK.core.layer(host, r.layer)).
    function build(host, o) {
        var nm = o.name || "SMOKE", c = o.center || [host.width / 2, host.height / 2], sz = o.size || [400, 300], lv = o.light || [1, -0.3], k = o.scale || Math.min(1, Math.max(0.2, 2.2 * sz[1] / 860));
        var r = AEX.plume.build(host, { name: nm, greyName: nm + "_DENS", base: [c[0], c[1] + sz[1]], height: 2.2 * sz[1] / k, width: 1.5 * sz[0] / k,
            lean: o.lean, scale: k, seed: o.seed, L: o.L, F: o.F, light: lv[0] >= 0 ? 1 : -1, shade: o.shade, opacity: o.body, color: o.color });
        return { comps: [r.grey], layers: [r.layer], layer: r.layer, grey: r.grey };
    }
    // FIRE: flame tones on the luminance map: tips ember red, body coral, hot coral, cream only where the density reaches 1 (the foot).
    var FIRE = { shadow: [0, 0, 0], dark: U.hex("#5A160C"), mid: U.hex("#E0452C"), bright: U.hex("#FF8A5C"), high: U.hex("#F1E9D8") };
    function tr(l, mn) { return l.property("ADBE Transform Group").property(mn); }
    // loop(container, src, L, P, F, name, over): the crossfade loop; A starts at -P, B at L - P and shows over the last F s. Light over black: both
    // in Add, A fades out as B fades in. Opaque maps (over true): A stays, B (Normal) fades in on top. Opacity keys are a mix: linear. Returns [A, B].
    function loop(c, src, L, P, F, name, over) {
        var a = c.layers.add(src), b = c.layers.add(src), oa, ob;
        a.name = name + "_A"; b.name = name + "_B";
        a.startTime = -P; b.startTime = L - P;
        oa = tr(a, "ADBE Opacity"); ob = tr(b, "ADBE Opacity");
        if (!over) { oa.setValueAtTime(L - F, 100); oa.setValueAtTime(L, 0); a.blendingMode = BlendingMode.ADD; b.blendingMode = BlendingMode.ADD; }
        ob.setValueAtTime(L - F, 0); ob.setValueAtTime(L, 100);
        b.inPoint = L - F;
        return [a, b];
    }
    // flameNoise(o, W, H, dur, fps): two stretched Fractal Noise layers (Basic, Invert on, contrast 140, brightness -15, Uniform Scaling off,
    // 70 x 150 and 28 x 70 px) scrolled upward at o.rise (240) and 1.7x that px/s, evolution time * 140 / 260, the fine one Add at 55 %. Returns the comp.
    function flameNoise(o, W, H, dur, fps) {
        var nm = o.name || "F", s = o.scale || 1, c = AEK.build.comp(nm + "_noise", { width: W, height: H, fps: fps, duration: dur }), i, l, spec;
        spec = [["N_BIG", 70 * s, 150 * s, o.rise || 240, 140, 100], ["N_FINE", 28 * s, 70 * s, (o.rise || 240) * 1.7, 260, 55]];
        for (i = 0; i < spec.length; i++) {
            l = AEK.build.solid(c, spec[i][0], [0, 0, 0]);
            U.fx(l, "ADBE Fractal Noise", { "ADBE Fractal Noise-0001": o.fractalType || 1, "ADBE Fractal Noise-0003": o.invert === false ? 0 : 1,
                "ADBE Fractal Noise-0004": 140, "ADBE Fractal Noise-0005": o.noiseBright === undefined ? -15 : o.noiseBright, "ADBE Fractal Noise-0009": 0,
                "ADBE Fractal Noise-0011": spec[i][1], "ADBE Fractal Noise-0012": spec[i][2], "ADBE Fractal Noise-0015": 5, "ADBE Fractal Noise-0027": (o.seed || 0) + 7 + i * 13 });
            l.property("ADBE Effect Parade").property(1).property("ADBE Fractal Noise-0013").expression = "[" + W / 2 + ", " + H / 2 + " + time * " + spec[i][3] + "]";
            l.property("ADBE Effect Parade").property(1).property("ADBE Fractal Noise-0023").expression = "time * " + spec[i][4];
            if (i) { l.blendingMode = BlendingMode.ADD; tr(l, "ADBE Opacity").setValue(spec[i][5]); }
        }
        return c;
    }
    // flameSrc(o, fps): the flame comp (520 x 760 x scale). Density = looped noise, Screen a vertical ramp at o.baseFill 45 % (noise x (1 - ramp)
    // + ramp: solid foot, noise-eaten top), Multiply a shape comp (opaque black ground, body ellipse, plume in Screen at 75 %, taper ramp to 1.2 x
    // height). Then Turbulent Displace Licks (22, size 55, 3 revolutions per loop) and Sway (16, 260, 1), Levels soft threshold o.thrLo 0.28 to
    // o.thrHi 0.72, CC Radial Fast Blur o.upBlur 22 centered 2,200 px below the foot (a one-direction smear upward), Fast Box Blur 1, and a heat
    // ramp in Multiply (1.0 at the foot to o.tipLevel 0.42 at the top) so the map gives cream at the foot only. Returns {comp, W, H, bx, by, h, w}.
    function flameSrc(o, fps) {
        var s = o.scale || 1, nm = o.name || "F", W = Math.round(520 * s), H = Math.round(760 * s), L = o.L, P = o.F, F = o.F, WHITE = [1, 1, 1], BLACK = [0, 0, 0];
        var bx = W / 2, by = H - 90 * s, h = (o.height || 360) * s, w = (o.width || 150) * s;
        var nsrc = flameNoise(o, W, H, L + P + 0.1, fps);
        var nl = AEK.build.comp(nm + "_noise_loop", { width: W, height: H, fps: fps, duration: L + 0.1 });
        loop(nl, nsrc, L, P, F, "NOISE", true);
        var d = AEK.build.comp(nm + "_density", { width: W, height: H, fps: fps, duration: L + 0.1 });
        d.layers.add(nl);
        var bf = AEK.build.solid(d, "BASE_FILL", BLACK);
        U.fx(bf, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.06 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx, by - (o.solid || 0.3) * h], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        bf.blendingMode = BlendingMode.SCREEN;
        tr(bf, "ADBE Opacity").setValue(o.baseFill === undefined ? 45 : o.baseFill);
        var sc = AEK.build.comp(nm + "_shape", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEK.build.solid(sc, "BLACK", BLACK);   // a Multiply layer over transparency composites as itself: the shape comp needs an opaque ground
        var body = AEK.build.solid(sc, "BODY", WHITE);
        U.ellipse(body, bx, by - 0.3 * h, w * 0.5, 0.33 * h, [w * 0.3, 0.2 * h]);
        var plume = AEK.build.solid(sc, "PLUME", WHITE);
        U.ellipse(plume, bx, by - 0.7 * h, w * 0.3, 0.5 * h, [w * 0.22, 0.38 * h]);
        tr(plume, "ADBE Opacity").setValue(75); plume.blendingMode = BlendingMode.SCREEN;
        var taper = AEK.build.solid(sc, "TAPER", BLACK);
        U.fx(taper, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.15 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx, by - 1.2 * h], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        taper.blendingMode = BlendingMode.MULTIPLY;
        var sl = d.layers.add(sc); sl.blendingMode = BlendingMode.MULTIPLY;
        var fc = AEK.build.comp(nm + "_flame", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEK.build.solid(fc, "GROUND", BLACK);
        var dl = fc.layers.add(d);
        U.fx(dl, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0001": 1, "ADBE Turbulent Displace-0002": (o.lick || 22) * s, "ADBE Turbulent Displace-0003": 55 * s,
            "ADBE Turbulent Displace-0005": 2, "ADBE Turbulent Displace-0010": (o.seed || 0) + 5, "ADBE Turbulent Displace-0012": 1 }, "Licks");
        AEX.vfx.loopNoise(dl.property("ADBE Effect Parade").property("Licks"), fc, L, 3);
        U.fx(dl, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0001": 1, "ADBE Turbulent Displace-0002": (o.sway || 16) * s, "ADBE Turbulent Displace-0003": 260 * s,
            "ADBE Turbulent Displace-0005": 1, "ADBE Turbulent Displace-0010": (o.seed || 0) + 9, "ADBE Turbulent Displace-0012": 1 }, "Sway");
        AEX.vfx.loopNoise(dl.property("ADBE Effect Parade").property("Sway"), fc, L, 1);
        U.fx(dl, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.thrLo === undefined ? 0.28 : o.thrLo, "ADBE Easy Levels2-0004": o.thrHi === undefined ? 0.72 : o.thrHi }, "Soft threshold");
        if (o.upBlur !== 0) {
            U.fx(dl, "CC Radial Fast Blur", { "CC Radial Fast Blur-0001": [bx, by + 2200 * s], "CC Radial Fast Blur-0002": o.upBlur || 22, "CC Radial Fast Blur-0003": 1 }, "Up blur");
        }
        U.fx(dl, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 1 * s, "ADBE Box Blur2-0002": 2, "ADBE Box Blur2-0004": 0 });
        var hr = AEK.build.solid(fc, "HEAT_RAMP", BLACK), tg = o.tipLevel === undefined ? 0.42 : o.tipLevel;
        U.fx(hr, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.12 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx, by - 0.95 * h], "ADBE Ramp-0004": [tg, tg, tg], "ADBE Ramp-0005": 1 });
        hr.blendingMode = BlendingMode.MULTIPLY;
        return { comp: fc, W: W, H: H, bx: bx, by: by, h: h, w: w };
    }
    // embers(o, fps): CC Particle World in a 1920 x 1080 comp P (2.6 s) + L long, three planes (far 14 at 4.5 px, mid 10 at 8 px shrinking to 4.5,
    // near 3 at 16 px with Camera Lens Blur 6) rising by negative gravity 230 to 380 px/s^2 against Resistance 1.6 to 2.2 (terminal speed about
    // 150 to 340 px/s), Turbulent Displace drift 34 / 170, opacity flicker 80 + 20 x noise, motion blur on. Returns {comp, P}.
    function embers(o, fps) {
        var s = o.scale || 1, nm = o.name || "F", L = o.L, P = 2.6, W = 1920, H = 1080, K = AEX.pn.K, n = o.emberCount || 1, i, sp, l;
        var src = AEK.build.comp(nm + "_embers_src", { width: W, height: H, fps: fps, duration: P + L + 0.1 });
        src.motionBlur = true;
        var spec = [   // name, on screen, life, d, dd, rise px/s^2, R, opacity, flicker rate, seed, lens blur
            ["EMB_FAR", 14, 2.4, 4.5, 3, 230, 2.2, 70, 9, 3, 0], ["EMB_MID", 10, 2.2, 8, 4.5, 300, 2.0, 100, 7, 7, 0], ["EMB_NEAR", 3, 1.8, 16, 10, 380, 1.6, 45, 5, 11, 6]];
        for (i = 0; i < spec.length; i++) {
            sp = spec[i];
            l = AEK.build.solid(src, sp[0], [0, 0, 0]);
            AEX.vfx.pw(l, { birthRate: sp[1] * n / (K.perSecPerRate * sp[2]), longevity: sp[2], x: (o.base[0] - W / 2) / W, y: (o.base[1] - 0.35 * (o.height || 360) * s - H / 2) / W, z: 0,
                rx: 0.03 * s, ry: 0.02 * s, rz: 0.01, animation: 1, velocity: 0.06, extra: 0.8, resistance: sp[6], gravity: -sp[5] * s / (K.gravPerWidth * W),
                type: 5, birthSize: sp[3] * s / (W * K.sizePerWidth), deathSize: sp[4] * s / (W * K.sizePerWidth), sizeVar: 50, maxOpacity: sp[7],
                colorMap: 2, birthColor: [1, 1, 1], deathColor: [0.45, 0.45, 0.45], transfer: 1, seed: (o.seed || 0) + sp[9] });
            U.fx(l, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 34 * s, "ADBE Turbulent Displace-0003": 170 * s, "ADBE Turbulent Displace-0005": 1,
                "ADBE Turbulent Displace-0010": sp[9], "ADBE Turbulent Displace-0012": 1 }, "Drift");
            l.property("ADBE Effect Parade").property("Drift").property("ADBE Turbulent Displace-0006").expression = "time * 70";
            if (sp[10]) { U.fx(l, "ADBE Camera Lens Blur", { "ADBE Camera Lens Blur-0001": sp[10] * s }); }
            tr(l, "ADBE Opacity").expression = "80 + 20 * noise([time * " + sp[8] + ", " + i + "])";
            l.motionBlur = true;
        }
        return { comp: src, P: P };
    }
    // heat(host, o, top): heat haze above the flame: AEX.distort.hazeMap (noise scale 90 x scale, rising 160 px/s) in a feathered band from 260 px
    // above the flame top down to its lower quarter, looped by crossfade, read by a Displacement Map adjustment layer at the TOP of the host
    // (it bends the tips, the embers and the plate together), amount o.heat 0.08 x the noise scale. Returns the adjustment layer.
    function heat(c, o, top) {
        var s = o.scale || 1, sc = 90 * s, x0 = o.base[0] - 170 * s, x1 = o.base[0] + 170 * s, y0 = top - 260 * s, y1 = o.base[1] - 0.25 * (o.height || 360) * s, F = o.F, L = o.L;
        var m = AEX.distort.hazeMap({ width: c.width, height: c.height, frameRate: c.frameRate, duration: L + F + 0.2 },
            { name: (o.name || "F") + "_HEAT", scale: sc, region: [x0, y0, x1, y1], feather: 90 * s, rise: 160 * s, speed: 300, seed: o.seed });
        var hl = AEK.build.comp((o.name || "F") + "_HEAT_LOOP", { width: c.width, height: c.height, fps: c.frameRate, duration: L + 0.1 });
        loop(hl, m, L, F, F, "MAP", true);
        var ml = c.layers.add(hl); ml.enabled = false;
        var adj = AEK.build.adjustment(c, "HEAT");
        U.fx(adj, "ADBE Displacement Map", { "ADBE Displacement Map-0001": ml.index, "ADBE Displacement Map-0002": 1, "ADBE Displacement Map-0003": (o.heat || 0.08) * sc,
            "ADBE Displacement Map-0004": 2, "ADBE Displacement Map-0005": (o.heat || 0.08) * sc, "ADBE Displacement Map-0006": 1, "ADBE Displacement Map-0008": 0 });
        adj.moveToBeginning();
        return adj;
    }
    // flame(host, o): a looping flame grown from a fixed source (AEX.fire), with embers and heat haze. o = {name, base [x, y] (the foot), height
    // (px, 600), width (px, 280), scale, seed, L, F (0.8), embers (false = none), emberCount, emberGain, heat (0 = none), tones, glow, sharpen,
    // hot, push, sway}. Older keys (baseFill, thrLo, thrHi, tipLevel, upBlur, gain, poolLum, rise) are accepted and ignored. The flame layer is
    // in Screen. Returns {name, flame (grey comp), embers, heat, light (the glow layer), layer} (names).
    function flame(c, o) {
        o.L = o.L || c.duration; o.F = o.F || 0.8;
        var r = AEX.fire.build(c, { name: o.name || "F", base: o.base, height: o.height, width: o.width, scale: o.scale, seed: o.seed, L: o.L, F: o.F,
            embers: o.embers, emberCount: o.emberCount, emberGain: o.emberGain, heat: o.heat, tones: o.tones, glow: o.glow, sharpen: o.sharpen, hot: o.hot, push: o.push, sway: o.sway });
        return { name: r.name, flame: r.grey, embers: r.embers, heat: r.heat, light: r.glow, layer: r.layer };
    }
    return { build: build, density: density, ellipse: ellipse, FIRE: FIRE, flame: flame, flameSrc: flameSrc, flameNoise: flameNoise, embers: embers, heat: heat, loop: loop };
})();

// AEX.fire: a flame grown from a fixed source by a one-sided displacement map, three noise
// scales rising at their own speeds, gray until the end, coloured once by a CC Toner map that keeps most of the flame red and coral.
// Uses AEX.smoke.loop, embers and heat. AEX.smoke.flame calls it.
AEX.fire = (function () {
    var U = AEX.vfxu, BLACK = [0, 0, 0], WHITE = [1, 1, 1], GREY = [0.5, 0.5, 0.5];
    // tones: luminance 0, 0.25, 0.5, 0.75, 1. Most of a flame sits between 0.25 and 0.75: deep red to coral. Cream only in the hottest licks.
    var TONES = { shadow: BLACK, dark: U.hex("#3A0C06"), mid: U.hex("#B0361F"), bright: [0.92, 0.42, 0.25], high: U.hex("#F1E9D8") };
    function tr(l, mn) { return l.property("ADBE Transform Group").property(mn); }
    function fxp(l, name) { return l.property("ADBE Effect Parade").property(name); }
    // noiseLayer(comp, name, p): Fractal Noise rising at p.rise px/s, evolution p.evo degrees/s. Returns the solid.
    function noiseLayer(c, name, p) {
        var s = AEK.build.solid(c, name, BLACK), e;
        e = U.fx(s, "ADBE Fractal Noise", { "ADBE Fractal Noise-0001": p.type || 1, "ADBE Fractal Noise-0003": p.invert ? 1 : 0, "ADBE Fractal Noise-0004": p.contrast,
            "ADBE Fractal Noise-0005": p.bright || 0, "ADBE Fractal Noise-0006": 1, "ADBE Fractal Noise-0009": 0, "ADBE Fractal Noise-0011": p.sw, "ADBE Fractal Noise-0012": p.sh,
            "ADBE Fractal Noise-0015": p.complexity || 6, "ADBE Fractal Noise-0017": p.subInf || 70, "ADBE Fractal Noise-0018": p.subScale || 56,
            "ADBE Fractal Noise-0019": p.subRot || 0, "ADBE Fractal Noise-0027": p.seed || 0 }, "Noise");
        e.property("ADBE Fractal Noise-0013").expression = "[" + c.width / 2 + ", " + c.height / 2 + " + time * " + p.rise + "]";
        e.property("ADBE Fractal Noise-0023").expression = "time * " + p.evo;
        if (p.mode) { s.blendingMode = p.mode; }
        if (p.opacity !== undefined) { tr(s, "ADBE Opacity").setValue(p.opacity); }
        return s;
    }
    // teardrop(layer, bx, by, w, h, feather): a mask from a round foot of width w at the base to a point h above it.
    function teardrop(l, bx, by, w, h, f) {
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape(), r = w / 2;
        sh.vertices = [[bx, by + 0.03 * h], [bx - 0.5 * r, by - 0.04 * h], [bx - r, by - 0.22 * h], [bx - 0.3 * w, by - 0.55 * h], [bx, by - h], [bx + 0.3 * w, by - 0.55 * h], [bx + r, by - 0.22 * h], [bx + 0.5 * r, by - 0.04 * h]];
        sh.inTangents = [[0.3 * r, 0], [0.2 * r, 0.03 * h], [0, 0.1 * h], [0.08 * w, 0.15 * h], [0, 0], [0.06 * w, -0.2 * h], [0, -0.1 * h], [0.2 * r, -0.03 * h]];
        sh.outTangents = [[-0.3 * r, 0], [-0.2 * r, -0.03 * h], [0, -0.1 * h], [-0.06 * w, -0.2 * h], [0, 0], [-0.08 * w, 0.15 * h], [0, 0.1 * h], [-0.2 * r, 0.03 * h]];
        sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh);
        m.property("ADBE Mask Feather").setValue(f instanceof Array ? f : [f, f]);
        return m;
    }
    // build(host, o): o = {name, base [x, y], height (px, 520), width (px, 220), scale, seed, L (s), F (crossfade s, 0.8), push (px, 140),
    //   sway (px, 26), texMix (Overlay opacity %, 100), black (Levels input black, 0.06), gamma (0.85), tones, sharpen (80), glow (0.35),
    //   embers (false = none), heat (0 = none), pool (0.18)}. Returns names.
    function build(host, o) {
        var s = o.scale || 1, nm = o.name || "FIRE", fps = host.frameRate, L = o.L || host.duration, F = o.F || 0.8, P = F, sd = o.seed || 0;
        var h = (o.height || 600) * s, w = (o.width || 280) * s, W = Math.round(Math.max(3.2 * w, 1.6 * h)), H = Math.round(1.6 * h + 160 * s), bx = W / 2, by = H - 140 * s, R = { name: nm };
        // 1. envelope: white teardrop over black, fading upward (static)
        var env = AEK.build.comp(nm + "_env", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEK.build.solid(env, "BLACK", BLACK);
        var td = AEK.build.solid(env, "SHAPE", [o.core || 0.8, o.core || 0.8, o.core || 0.8]);
        teardrop(td, bx, by, w, h, [0.12 * w, 0.12 * w]);
        var rp = AEK.build.solid(env, "FADE_UP", BLACK);
        U.fx(rp, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.12 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx, by - 1.3 * h], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        rp.blendingMode = BlendingMode.MULTIPLY;
        // 2. displacement map: noise limited to 0 to 0.5 (one direction), mid gray over the foot so the base never moves
        var msrc = AEK.build.comp(nm + "_map_src", { width: W, height: H, fps: fps, duration: L + P + 0.1 });
        AEK.build.solid(msrc, "GREY", GREY);
        var mn = noiseLayer(msrc, "MAP_NOISE", { type: 1, contrast: 130, sw: 80 * s, sh: 190 * s, complexity: 4, rise: 260 * s, evo: 160, seed: sd + 3 });
        U.fx(mn, "ADBE Easy Levels2", { "ADBE Easy Levels2-0007": 0.5 }, "One side");
        var pin = AEK.build.solid(msrc, "PIN_BASE", GREY);
        U.rect(pin, -50, by - 0.08 * h, W + 50, H + 50, [1, 0.2 * h]);
        var mloop = AEK.build.comp(nm + "_map", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEX.smoke.loop(mloop, msrc, L, P, F, "MAP", true);
        // 3. texture: stringy flames, big shadows (Multiply), fine hot specks (Add), each rising at its own speed (parallax)
        var tsrc = AEK.build.comp(nm + "_tex_src", { width: W, height: H, fps: fps, duration: L + P + 0.1 });
        noiseLayer(tsrc, "STRINGS", { type: o.stringType || 7, invert: true, contrast: 120, bright: 0, sw: 70 * s, sh: 200 * s, complexity: 6, subRot: 30, rise: 170 * s, evo: 150, seed: sd + 5 });
        noiseLayer(tsrc, "SHADOWS", { type: 1, contrast: 120, bright: 20, sw: 240 * s, sh: 420 * s, complexity: 3, rise: 80 * s, evo: 60, seed: sd + 7, mode: BlendingMode.MULTIPLY, opacity: 40 });
        noiseLayer(tsrc, "SPECKS", { type: 1, contrast: 80, bright: -45, sw: 12 * s, sh: 28 * s, complexity: 3, rise: 330 * s, evo: 300, seed: sd + 9, mode: BlendingMode.ADD, opacity: 35 });
        var tloop = AEK.build.comp(nm + "_tex", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEX.smoke.loop(tloop, tsrc, L, P, F, "TEX", true);
        // 4. gray flame: envelope pushed up by the map, twisted a little, texture in Overlay, then Levels
        var g = AEK.build.comp(nm + "_grey", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEK.build.solid(g, "GROUND", BLACK);
        var ml = g.layers.add(mloop); ml.enabled = false; ml.name = "MAP";
        var tl = g.layers.add(tloop); tl.enabled = false; tl.name = "TEXMAP";
        var el = g.layers.add(env); el.name = "ENVELOPE"; el.moveBefore(g.layer("GROUND"));
        var push = (o.push === undefined ? 0.42 : o.push) * h;
        U.fx(el, "ADBE Displacement Map", { "ADBE Displacement Map-0001": ml.index, "ADBE Displacement Map-0002": 5, "ADBE Displacement Map-0003": 0.35 * push,
            "ADBE Displacement Map-0004": 5, "ADBE Displacement Map-0005": push, "ADBE Displacement Map-0006": 1, "ADBE Displacement Map-0008": 0 }, "Push up");
        var tw = U.fx(el, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0001": 5, "ADBE Turbulent Displace-0002": (o.sway === undefined ? 0.05 : o.sway) * h,
            "ADBE Turbulent Displace-0003": 0.22 * h, "ADBE Turbulent Displace-0005": 2, "ADBE Turbulent Displace-0010": sd + 11, "ADBE Turbulent Displace-0012": 1 }, "Sway");
        AEX.vfx.loopNoise(tw, g, L, 2);
        var tex = g.layers.add(tloop); tex.name = "TEXTURE"; tex.moveBefore(el);
        U.fx(tex, "ADBE Displacement Map", { "ADBE Displacement Map-0001": ml.index, "ADBE Displacement Map-0002": 5, "ADBE Displacement Map-0003": 0.35 * push,
            "ADBE Displacement Map-0004": 5, "ADBE Displacement Map-0005": push, "ADBE Displacement Map-0006": 1, "ADBE Displacement Map-0008": 0 }, "Push up");
        tex.blendingMode = BlendingMode.OVERLAY; tr(tex, "ADBE Opacity").setValue(o.texMix === undefined ? 100 : o.texMix);
        // hot core: the texture again, pushed the same way, seen only through a soft ellipse in the lower body, in Add: heat inside the
        // flame that keeps the texture, so the hottest part is filaments, never a flat egg
        var hot = g.layers.add(tloop); hot.name = "HOT_CORE"; hot.moveBefore(tex);
        U.fx(hot, "ADBE Displacement Map", { "ADBE Displacement Map-0001": ml.index, "ADBE Displacement Map-0002": 5, "ADBE Displacement Map-0003": 0.35 * push,
            "ADBE Displacement Map-0004": 5, "ADBE Displacement Map-0005": push, "ADBE Displacement Map-0006": 1, "ADBE Displacement Map-0008": 0 }, "Push up");
        U.ellipse(hot, bx, by - 0.2 * h, 0.3 * w, 0.2 * h, [0.25 * w, 0.18 * h]);
        hot.blendingMode = BlendingMode.ADD; tr(hot, "ADBE Opacity").setValue(o.hot === undefined ? 45 : o.hot);
        var adj = AEK.build.adjustment(g, "GRADE"); adj.moveToBeginning();
        U.fx(adj, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.black === undefined ? 0.22 : o.black, "ADBE Easy Levels2-0004": o.white === undefined ? 0.95 : o.white, "ADBE Easy Levels2-0005": o.gamma === undefined ? 0.9 : o.gamma }, "Levels");
        // 5. colour once, sharpen; glow from a blurred copy; the flame in Screen over the plate
        var fl = host.layers.add(g); fl.name = nm;
        tr(fl, "ADBE Position").setValue([o.base[0], o.base[1] - by + H / 2]);
        AEX.light.toneMap(fl, o.tones || TONES);
        U.fx(fl, "ADBE Unsharp Mask2", { "ADBE Unsharp Mask2-0001": o.sharpen === undefined ? 80 : o.sharpen, "ADBE Unsharp Mask2-0002": 1.5 }, "Sharpen");
        fl.blendingMode = BlendingMode.SCREEN;
        var gl = host.layers.add(g); gl.name = nm + "_GLOW";
        tr(gl, "ADBE Position").setValue([o.base[0], o.base[1] - by + H / 2]);
        AEX.light.toneMap(gl, o.tones || TONES);
        U.fx(gl, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 40 * s, "ADBE Gaussian Blur 2-0003": 0 });
        U.gain(gl, o.glow === undefined ? 0.25 : o.glow);
        gl.blendingMode = BlendingMode.SCREEN; gl.moveAfter(fl);
        if (o.embers !== false) {
            var em = AEX.smoke.embers({ name: nm, base: o.base, height: 0.75 * h / s, scale: s, L: L, seed: sd, emberCount: o.emberCount || 1.5 }, fps), ec = AEK.build.comp(nm + "_embers", { width: host.width, height: host.height, fps: fps, duration: L + 0.1 });
            ec.motionBlur = true; AEX.smoke.loop(ec, em.comp, L, em.P, F, "EMB");
            var eb = host.layers.add(ec); eb.name = nm + "_EMBERS"; eb.motionBlur = true;
            AEX.light.toneMap(eb, o.tones || TONES); U.gain(eb, o.emberGain || 2.0); eb.blendingMode = BlendingMode.SCREEN; R.embers = eb.name;
        }
        if (o.heat !== 0) { R.heat = AEX.smoke.heat(host, { name: nm, base: o.base, height: 0.75 * h / s, scale: s, L: L, F: F, heat: o.heat || 0.08, seed: sd }, o.base[1] - h).name; }
        R.layer = fl.name; R.glow = gl.name; R.grey = g.name; R.W = W; R.H = H; R.by = by; R.h = h;
        return R;
    }
    return { TONES: TONES, build: build, noiseLayer: noiseLayer, teardrop: teardrop };
})();

// AEX.plume: a smoke plume from a fixed source. Wisps are stringy Fractal Noise (type 7, Invert)
// rising through a widening, leaning plume mask; a displacement map pinned at the source sways and curls it more with height; gray, low
// opacity, lit from one side, Screen. AEX.smoke.build calls it.
AEX.plume = (function () {
    var U = AEX.vfxu, BLACK = [0, 0, 0], WHITE = [1, 1, 1], GREY = [0.5, 0.5, 0.5];
    function tr(l, mn) { return l.property("ADBE Transform Group").property(mn); }
    // cone(layer, bx, by, w0, w1, h, lean, feather): a plume mask: w0 wide at the source, w1 wide at height h, top shifted by lean px.
    function cone(l, bx, by, w0, w1, h, lean, f) {
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape(), tx = bx + lean;
        sh.vertices = [[bx - w0 / 2, by], [bx - 0.3 * w1 + 0.5 * lean, by - 0.5 * h], [tx - w1 / 2, by - h], [tx + w1 / 2, by - h], [bx + 0.3 * w1 + 0.5 * lean, by - 0.5 * h], [bx + w0 / 2, by]];
        sh.inTangents = [[0, 0], [0.05 * w1, 0.2 * h], [0, 0.1 * h], [0, 0], [0, -0.2 * h], [0, 0]];
        sh.outTangents = [[0, 0], [-0.05 * w1, -0.2 * h], [0, 0], [0, 0.1 * h], [0, 0.2 * h], [0, 0]];
        sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh);
        m.property("ADBE Mask Feather").setValue(f instanceof Array ? f : [f, f]);
        return m;
    }
    // build(host, o): o = {name, base [x, y] (the source), height (px, 900), width (px at the top, 640), lean (px, -180), scale, seed, L, F,
    //   rise (px/s, 90), sway (px, 0.12 x height), opacity (%, 55), color (warm gray to cream), light (+1 lit from the left, -1 from the right), shade (0.45),
    //   greyName (the gray comp's name, <name>_grey)}. Returns {name, layer, grey} (names).
    function build(host, o) {
        var s = o.scale || 1, nm = o.name || "PLUME", fps = host.frameRate, L = o.L || host.duration, F = o.F || 0.8, P = F, sd = o.seed || 0;
        var W = host.width, H = host.height, bx = o.base[0], by = o.base[1], h = (o.height || 860) * s, w1 = (o.width || 760) * s, lean = (o.lean === undefined ? -240 : o.lean) * s, R = { name: nm };
        // texture: wisps (type 7 Invert, stretched up), soft density (Multiply), each rising at its own speed
        var tsrc = AEK.build.comp(nm + "_tex_src", { width: W, height: H, fps: fps, duration: L + P + 0.1 });
        AEX.fire.noiseLayer(tsrc, "WISPS", { type: 7, invert: true, contrast: 115, bright: -10, sw: 110 * s, sh: 190 * s, complexity: 8, subInf: 80, subRot: 100, rise: (o.rise || 90) * s, evo: 50, seed: sd + 2 });
        AEX.fire.noiseLayer(tsrc, "DENSITY", { type: 1, contrast: 140, bright: 15, sw: 700 * s, sh: 800 * s, complexity: 2, rise: 0.6 * (o.rise || 90) * s, evo: 25, seed: sd + 4, mode: BlendingMode.MULTIPLY, opacity: 35 });
        var tl = AEK.build.comp(nm + "_tex", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEX.smoke.loop(tl, tsrc, L, P, F, "TEX", true);
        // mask: the widening, leaning plume, fading out toward its top and fading in just above the source
        var mk = AEK.build.comp(nm + "_mask", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEK.build.solid(mk, "BLACK", BLACK);
        // a narrow column at the source (tight feather) and a wide crown above it (wide feather): the plume is thin where it is born
        var cs = AEK.build.solid(mk, "CROWN", WHITE);
        cone(cs, bx, by, 70 * s, w1, h, lean, [0.3 * w1, 0.22 * h]);
        U.fx(cs, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.12 * h], "ADBE Ramp-0002": BLACK, "ADBE Ramp-0003": [bx, by - 0.5 * h], "ADBE Ramp-0004": WHITE, "ADBE Ramp-0005": 1 });
        var col = AEK.build.solid(mk, "COLUMN", WHITE);
        cone(col, bx, by, 30 * s, 0.3 * w1, 0.62 * h, 0.3 * lean, [0.08 * w1, 0.04 * h]);
        U.fx(col, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.2 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx, by - 0.6 * h], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        col.blendingMode = BlendingMode.SCREEN;
        var fade = AEK.build.solid(mk, "FADE", BLACK);
        U.fx(fade, "ADBE Ramp", { "ADBE Ramp-0001": [bx, by - 0.2 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx + lean, by - 1.0 * h], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 1 });
        fade.blendingMode = BlendingMode.MULTIPLY;
        // sway map: noise around mid gray, mid gray over the source so it never moves
        var msrc = AEK.build.comp(nm + "_map_src", { width: W, height: H, fps: fps, duration: L + P + 0.1 });
        AEK.build.solid(msrc, "GREY", GREY);
        var mn = AEX.fire.noiseLayer(msrc, "MAP_NOISE", { type: 1, contrast: 100, sw: 380 * s, sh: 520 * s, complexity: 3, rise: 0.8 * (o.rise || 90) * s, evo: 40, seed: sd + 6 });
        var pin = AEK.build.solid(msrc, "PIN_BASE", GREY);
        pin.property("ADBE Mask Parade"); U.rect(pin, -50, by - 0.1 * h, W + 50, H + 50, [1, 0.6 * h]);
        var ml = AEK.build.comp(nm + "_map", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEX.smoke.loop(ml, msrc, L, P, F, "MAP", true);
        // gray plume: texture through the mask, swayed by the map, a little Turbulent Displace for curls, shaded toward the far side
        var g = AEK.build.comp(o.greyName || nm + "_grey", { width: W, height: H, fps: fps, duration: L + 0.1 });
        AEK.build.solid(g, "GROUND", BLACK);
        var mapL = g.layers.add(ml); mapL.enabled = false; mapL.name = "MAP";
        var tx = g.layers.add(tl); tx.name = "TEXTURE";
        var mm = g.layers.add(mk); mm.name = "MASK";
        tx.moveBefore(g.layer("GROUND")); mm.moveBefore(tx);
        tx.setTrackMatte(mm, TrackMatteType.LUMA);
        var adj = AEK.build.adjustment(g, "SWAY"); adj.moveToBeginning();
        var sway = (o.sway === undefined ? 0.12 : o.sway) * h;
        U.fx(adj, "ADBE Displacement Map", { "ADBE Displacement Map-0001": mapL.index, "ADBE Displacement Map-0002": 5, "ADBE Displacement Map-0003": sway,
            "ADBE Displacement Map-0004": 5, "ADBE Displacement Map-0005": 0.15 * sway, "ADBE Displacement Map-0006": 1, "ADBE Displacement Map-0008": 0 }, "Sway");
        var td = U.fx(adj, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0001": 5, "ADBE Turbulent Displace-0002": 28 * s, "ADBE Turbulent Displace-0003": 146 * s,
            "ADBE Turbulent Displace-0005": 1.5, "ADBE Turbulent Displace-0010": sd + 9 }, "Curls");
        AEX.vfx.loopNoise(td, g, L, 1);
        var sh = AEK.build.solid(g, "SHADE", WHITE), lx = o.light === undefined ? 1 : o.light, sk = o.shade === undefined ? 0.45 : o.shade;
        U.fx(sh, "ADBE Ramp", { "ADBE Ramp-0001": [bx - lx * 0.5 * w1, by - 0.5 * h], "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [bx + lx * 0.5 * w1, by - 0.5 * h], "ADBE Ramp-0004": [sk, sk, sk], "ADBE Ramp-0005": 1 });
        sh.blendingMode = BlendingMode.MULTIPLY; sh.moveBefore(mm);
        var gr = AEK.build.adjustment(g, "GRADE"); gr.moveToBeginning();
        U.fx(gr, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.floor === undefined ? 0.06 : o.floor, "ADBE Easy Levels2-0004": o.ceil === undefined ? 0.55 : o.ceil, "ADBE Easy Levels2-0005": 1.1 });
        // into the host: tinted, Screen, low opacity
        var pl = host.layers.add(g); pl.name = nm;
        U.fx(pl, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": o.color || U.mix(U.PALETTE.grey, U.PALETTE.cream, 0.6) });
        U.fx(pl, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 1.5 * s, "ADBE Gaussian Blur 2-0003": 0 });
        pl.blendingMode = BlendingMode.SCREEN; tr(pl, "ADBE Opacity").setValue(o.opacity === undefined ? 70 : o.opacity);
        R.layer = pl.name; R.grey = g.name;
        return R;
    }
    return { build: build, cone: cone };
})();

// AEX.motes: dust in a light beam. Few motes in a deep, thin band, a slow rise with a light drift,
// no swirl; size, softness and brightness by depth (far small and dim, a handful of large soft discs near); seen only inside the beam,
// a faint share outside it; the beam itself soft and faint. Loops by the crossfade pair of AEX.atmo.
AEX.motes = (function () {
    var U = AEX.vfxu, CREAM = U.PALETTE.cream;
    // layers: [name, count on screen, diameter px, rise px/s, drift px/s, brightness 0 to 1, blur px, life s]
    var LAYERS = [["FAR", 220, 5, 5, 4, 0.9, 0, 4], ["MID", 70, 16, 9, 7, 1.0, 0, 4], ["NEAR", 24, 110, 16, 12, 0.22, 0, 3.5]];   // NEAR: 24 on screen keeps Birth Rate above 0.05
    // build(host, o): o = {name, L (4), P (4), F (1), beam [topX, topW, botX, botW], beamFeather (220), beamOpacity (9), density (count
    //   multiplier, 1), outside (share of motes visible outside the beam, 0.15), color (cream), seed}. Returns {comps, layer, beam} (names).
    function build(host, o) {
        var L = o.L || 4, P = o.P || 4, F = o.F || 1, H = host.height, nm = o.name || "MOTES", k = o.density === undefined ? 1 : o.density, sd = o.seed || 0, i;
        var col = o.color || CREAM, sim = AEK.build.comp(nm + "_SIM", { width: host.width, height: H, fps: host.frameRate, duration: P + L + 0.1, bg: [0, 0, 0] });
        for (i = 0; i < LAYERS.length; i++) {
            var a = LAYERS[i], c = U.scale(col, a[5]), hot = U.mix(c, [1, 1, 1], 0.15 * a[5]);
            AEX.atmo.plane(sim, nm + "_" + a[0], { count: a[1] * k, life: a[7], cy: H * 0.5, ry: 0.32, d: a[2], rise: a[3], drift: a[4], col: c, hot: hot, blur: a[6], seed: sd + i + 1 });
        }
        var mo = AEK.build.comp(nm, { width: host.width, height: H, fps: host.frameRate, duration: L + 2 / host.frameRate, bg: [0, 0, 0] });
        var bo = o.beamFeather || 220, R = { comps: [sim.name, mo.name] };
        // inside the beam: full; outside: a faint share
        var mat = AEK.build.solid(mo, "BEAM_MATTE", [1, 1, 1]), m = mat.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape(), b = o.beam;
        sh.vertices = [[b[0] - b[1] / 2, -80], [b[0] + b[1] / 2, -80], [b[2] + b[3] / 2, H + 80], [b[2] - b[3] / 2, H + 80]]; sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh); m.property("ADBE Mask Feather").setValue([bo, bo]);
        var out = AEK.build.solid(mo, "OUTSIDE", [1, 1, 1]); U.opacity(out).setValue(100 * (o.outside === undefined ? 0.2 : o.outside)); out.moveAfter(mat);
        var pre = AEK.build.comp(nm + "_MATTE", { width: host.width, height: H, fps: host.frameRate, duration: L + 0.1, bg: [0, 0, 0] });
        mat.copyToComp(pre); out.copyToComp(pre); mat.remove(); out.remove();   // both made just above in this call
        var matL = mo.layers.add(pre); matL.name = "MATTE";
        var pr = AEX.atmo.loopPair(mo, sim, P, L, F, BlendingMode.ADD);
        pr[0].moveAfter(matL);
        pr[0].setTrackMatte(matL, TrackMatteType.LUMA); pr[1].setTrackMatte(matL, TrackMatteType.LUMA);
        // the beam: soft, faint, brighter at its top
        var bv = AEK.build.solid(host, nm + "_BEAM", U.scale(col, 0.9)), bmk = bv.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
        bmk.property("ADBE Mask Shape").setValue(sh); bmk.property("ADBE Mask Feather").setValue([1.3 * bo, 1.3 * bo]);
        U.fx(bv, "ADBE Ramp", { "ADBE Ramp-0001": [b[0], 0], "ADBE Ramp-0002": U.scale(col, 0.9), "ADBE Ramp-0003": [b[2], H], "ADBE Ramp-0004": U.scale(col, 0.2), "ADBE Ramp-0005": 1 });
        U.opacity(bv).setValue(o.beamOpacity === undefined ? 18 : o.beamOpacity); bv.blendingMode = BlendingMode.ADD;
        var ml = host.layers.add(mo); ml.name = nm; ml.blendingMode = BlendingMode.ADD;
        R.layer = ml.name; R.beam = bv.name;
        return R;
    }
    return { build: build, LAYERS: LAYERS };
})();

// AEX.element: land a generated element on black (fire, smoke) on a plate with the skill's own
// integration steps: interpret, crush the black, palette, a feathered foot, Screen, a small glow, the light it throws (pool and lift driven by
// the element's own luminance), grain.
AEX.element = (function () {
    var U = AEX.vfxu;
    function tr(l, mn) { return l.property("ADBE Transform Group").property(mn); }
    // land(host, item, o): o = {name, base [x, y] where the element's foot lands, foot (source row of the foot, default the source height),
    //   scale (%, 100), conform (true: conform the footage rate to the comp's), black (Levels Input Black 0 to 1, the clip's background p99),
    //   tones (CC Toner map, null = keep the source color), keep (Blend w. Original % of the map, 40), tint (a color: Tint black to it at
    //   tintAmount %, for smoke), footFeather (px, 60), opacity (%), glow (gain, 0.25), glowRadius (px, 50), pool (0 to 1, 0.35), lift (0 to 1, 0.2),
    //   poolColor, reach (px, 520)}. Returns {layer, glow, pool, lift, warnings} (layer names and warning texts).
    function land(host, item, o) {
        var nm = o.name || "ELEMENT", W = item.width, H = item.height, foot = o.foot === undefined ? H : o.foot, sc = o.scale || 100, k = sc / 100, w = [];
        if (o.conform !== false && item.mainSource && Math.abs(item.frameRate - host.frameRate) > 0.01) {
            var r0 = item.frameRate;
            item.mainSource.conformFrameRate = host.frameRate;
            w.push("conformed " + item.name + " from " + r0 + " to " + host.frameRate + " fps: motion plays " + (host.frameRate / r0).toFixed(2) + "x");
        }
        var l = host.layers.add(item); l.name = nm;
        tr(l, "ADBE Anchor Point").setValue([W / 2, foot]);
        tr(l, "ADBE Position").setValue(o.base);
        tr(l, "ADBE Scale").setValue([sc, sc]);
        // the source above its foot, faded over footFeather px: the foot sits on the floor line, what the clip shows below it is gone
        // a mask feather straddles its edge: end the mask half a feather above the foot so the clip is fully gone at the foot row
        var ff = o.footFeather === undefined ? 60 : o.footFeather;
        U.rect(l, -200, -200, W + 200, foot - 0.5 * ff, [1, ff]);
        U.fx(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.black || 0 }, "Black level");
        if (o.tones) {
            var tm = AEX.light.toneMap(l, o.tones);
            tm.property("CC Toner-0004").setValue((o.keep === undefined ? 40 : o.keep) / 100);   // Blend w. Original reads 0 to 1 from a script
        }
        if (o.tint) {
            var ti = U.fx(l, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": o.tint });
            ti.property("ADBE Tint-0003").setValue(o.tintAmount === undefined ? 100 : o.tintAmount);
        }
        l.blendingMode = BlendingMode.SCREEN;
        if (o.opacity !== undefined) { tr(l, "ADBE Opacity").setValue(o.opacity); }
        var R = { layer: nm, warnings: w };
        if (o.glow !== 0) {
            var g = l.duplicate(); g.name = nm + "_GLOW";
            U.fx(g, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": (o.glowRadius || 50) * k, "ADBE Gaussian Blur 2-0003": 0 });
            U.gain(g, o.glow === undefined ? 0.25 : o.glow);
            g.moveAfter(l); R.glow = g.name;
        }
        // the light it throws: the element's mean luma in a box above the foot drives a floor pool and a radial lift of the plate
        var sx = 0.25 * W, sy = 0.25 * (foot), env = "var e = thisComp.layer(\"" + nm + "\"); var c = e.sampleImage([" + W / 2 + ", " + (foot - sy) + "], [" + sx + ", " + sy + "], true, time); var y = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];";
        var col = o.poolColor || U.PALETTE.coral, reach = (o.reach || 520) * k;
        if (o.pool !== 0) {
            var p = AEK.build.solid(host, nm + "_POOL", col);
            U.ellipse(p, o.base[0], o.base[1] + 6, reach, 0.16 * reach, [0.6 * reach, 0.12 * reach]);
            tr(p, "ADBE Opacity").expression = env + " Math.min(100, 100 * " + (o.pool === undefined ? 0.35 : o.pool) + " * y / 0.5);";
            p.blendingMode = BlendingMode.SCREEN; p.moveAfter(l); R.pool = p.name;
        }
        if (o.lift !== 0) {
            var lf = AEK.build.solid(host, nm + "_LIFT", col);
            U.fx(lf, "ADBE Ramp", { "ADBE Ramp-0001": [o.base[0], o.base[1] - 0.3 * foot * k], "ADBE Ramp-0002": col, "ADBE Ramp-0003": [o.base[0] + 1.6 * reach, o.base[1] - 0.3 * foot * k], "ADBE Ramp-0004": [0, 0, 0], "ADBE Ramp-0005": 2 });
            tr(lf, "ADBE Opacity").expression = env + " Math.min(100, 100 * " + (o.lift === undefined ? 0.2 : o.lift) + " * y / 0.5);";
            lf.blendingMode = BlendingMode.SCREEN; lf.moveAfter(l); R.lift = lf.name;
        }
        return R;
    }
    return { land: land };
})();

AEX.shock = (function () {
    var U = AEX.vfxu;
    var DEFAULTS = { center: [960, 540], t0: 0, dur: 1.0, r0: 10, r1: 1150, p: 3, fadeTo: 0.25, lum: 0.6, seed: 1 };
    function merge(o) { return U.merge(DEFAULTS, o); }
    // rExpr(o): expression text defining r, the radius in px at time: ease-out of power p from r0 to r1 over dur (p 3: half the distance in 21 % of the time).
    function uExpr(o) { return "var u=Math.min(1,Math.max(0,(time-" + o.t0 + ")/" + o.dur + "));"; }
    function rExpr(o) { return uExpr(o) + "var r=" + o.r0 + "+(" + (o.r1 - o.r0) + ")*(1-Math.pow(1-u," + o.p + "));"; }
    // fadeExpr(o): opacity 100 at birth to fadeTo x 100 at the end (u squared: the ring keeps its strength while it is fast).
    function fadeExpr(o) { return uExpr(o) + "100*(1-u*u*" + (1 - o.fadeTo) + ");"; }
    function ellipseSize(grp) { return grp.property("ADBE Vectors Group").property("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size"); }
    function strokeOf(grp) { return grp.property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke"); }
    // polar(lightComp, o): (a) a Fractal Noise band in a square precomp of side S >= 2 x (r1 + thickness) (row y lands at radius y / 2),
    // a seam-fix ADJUSTMENT layer (Offset half the width, two feathered edge masks), Polar Coordinates Rect to Polar, Turbulent Displace AFTER Polar.
    // o adds {thick, thickGrow, size, noiseW, noiseH, drag, evolve, seamFeather, wisp, wispSize, name}. Returns {layer, band, size}.
    function polar(lc, o) {
        o = merge(o);
        var th = o.thick || 26, ts = o.thickGrow || 0.05, S = o.size || 2 * Math.ceil(o.r1 + th + ts * o.r1 + 60);
        var bc = AEK.build.comp((o.name || "SW") + "_band", { width: S, height: S, fps: lc.frameRate, duration: lc.duration });
        var n = AEK.build.solid(bc, "NOISE", [0.5, 0.5, 0.5]);
        var nf = U.fx(n, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 170, "ADBE Fractal Noise-0009": 0, "ADBE Fractal Noise-0011": o.noiseW || 70, "ADBE Fractal Noise-0012": o.noiseH || 500, "ADBE Fractal Noise-0015": 5, "ADBE Fractal Noise-0027": o.seed });
        nf.property("ADBE Fractal Noise-0023").expression = "time*" + (o.evolve || 300);
        nf.property("ADBE Fractal Noise-0013").expression = rExpr(o) + "[" + S / 2 + ", r*" + (o.drag || 0.8) + "];";
        var b = AEK.build.shape(bc, "BAND", { name: "b", type: "rect", size: [S + 400, 2 * th], fill: [1, 1, 1] }, { position: [S / 2, 0] });
        b.property("ADBE Transform Group").property("ADBE Position").expression = rExpr(o) + "[" + S / 2 + ", 2*r];";
        b.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size").expression = rExpr(o) + "[" + (S + 400) + ", 2*(" + th + "+" + ts + "*r)];";
        U.fx(b, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": th / 2, "ADBE Gaussian Blur 2-0002": 3, "ADBE Gaussian Blur 2-0003": 0 });
        n.setTrackMatte(b, TrackMatteType.ALPHA);
        // seam fix on an adjustment layer: a layer's own masks run before its effects, so masks on a duplicate of the band failed
        var fixL = AEK.build.adjustment(bc, "SEAM FIX");
        U.fx(fixL, "ADBE Offset", { "ADBE Offset-0001": [S, S / 2] });
        var fe = o.seamFeather || 0.1;
        U.rect(fixL, -S / 2, -10, (0.05 + fe / 2) * S, S + 10, [fe * S, 0]);
        U.rect(fixL, (0.95 - fe / 2) * S, -10, 1.5 * S, S + 10, [fe * S, 0]);
        var l = lc.layers.add(bc);
        l.property("ADBE Transform Group").property("ADBE Position").setValue(o.center);
        U.fx(l, "ADBE Polar Coordinates", { "ADBE Polar Coordinates-0001": 1, "ADBE Polar Coordinates-0002": 1 });
        if (o.wisp !== 0) {
            var td = U.fx(l, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": o.wisp || 30, "ADBE Turbulent Displace-0003": o.wispSize || 70, "ADBE Turbulent Displace-0010": o.seed });
            td.property("ADBE Turbulent Displace-0006").expression = "time*120";
        }
        U.opacity(l).expression = fadeExpr(o);
        AEX.light.add(l, o.lum);
        return { layer: l, band: bc, size: S };
    }
    // stroke(lightComp, o): (b) a hot edge stroke (edgeW px) and a wake layer of n overlapping strokes inside it, each gap x r wide, fall x
    // fainter inward, blurred by 0.6 x a step so they merge into one tapered profile (thin separate strokes read as concentric lines).
    // o adds {wake (6), gap (0.025), fall (0.7), edgeW (4), blur (1.5), wakeLum, name}. Returns {edge, wake}.
    function stroke(lc, o) {
        o = merge(o);
        var n = o.wake === undefined ? 6 : o.wake, gap = o.gap || 0.025, fall = o.fall || 0.7, w0 = o.edgeW || 4, nm = o.name || "SW", k, st, wk, edge;
        wk = lc.layers.addShape();
        wk.name = nm + " wake";
        for (k = n; k >= 1; k--) {
            AEK.build.shapeGroup(wk, { name: "s" + k, type: "ellipse", size: [100, 100], stroke: { color: [1, 1, 1], width: 10 } });
            ellipseSize(wk.property("ADBE Root Vectors Group").property("s" + k)).expression = rExpr(o) + "var d=2*r*(1-" + ((k - 0.5) * gap) + "); [d,d];";
            st = strokeOf(wk.property("ADBE Root Vectors Group").property("s" + k));
            st.property("ADBE Vector Stroke Width").expression = rExpr(o) + "Math.max(1," + (gap * 1.05) + "*r);";
            st.property("ADBE Vector Stroke Opacity").setValue(100 * Math.pow(fall, k));
        }
        wk.property("ADBE Transform Group").property("ADBE Position").setValue(o.center);
        var gb = U.fx(wk, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 4, "ADBE Gaussian Blur 2-0003": 0 });
        gb.property("ADBE Gaussian Blur 2-0001").expression = rExpr(o) + "Math.max(1," + (gap * 0.6) + "*r);";
        U.opacity(wk).expression = fadeExpr(o);
        AEX.light.add(wk, o.wakeLum || o.lum);
        edge = AEK.build.shape(lc, nm + " edge", { name: "e", type: "ellipse", size: [100, 100], stroke: { color: [1, 1, 1], width: w0 } }, { position: o.center });
        ellipseSize(edge.property("ADBE Root Vectors Group").property("e")).expression = rExpr(o) + "[2*r,2*r];";
        if (o.blur !== 0) { U.fx(edge, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.blur || 1.5, "ADBE Gaussian Blur 2-0003": 0 }); }
        U.opacity(edge).expression = fadeExpr(o);
        AEX.light.add(edge, o.lum);
        return { edge: edge, wake: wk };
    }
    function wispDisplace(c, o, name) {
        var adj = AEK.build.adjustment(c, name);
        var td = U.fx(adj, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": o.wisp || 35, "ADBE Turbulent Displace-0003": o.wispSize || 60, "ADBE Turbulent Displace-0010": o.seed });
        td.property("ADBE Turbulent Displace-0006").expression = "time*150";
        return adj;
    }
    // ring(lightComp, o): (c) a thin hot edge, Fractal Noise wisps (basic, contrast 220, brightness -45) inside a wide soft stroke (alpha
    // matte), Turbulent Displace over both. o adds {edgeW (3), wispIn, wispW (0.15), wispSoft, fractal, wispContrast, wispBright, noiseScale,
    // evolve, wispLum (0.5), wisp, wispSize, name}. Returns {edge, wisps, matte, displace}.
    function ring(lc, o) {
        o = merge(o);
        var nm = o.name || "SW";
        var edge = AEK.build.shape(lc, nm + " edge", { name: "e", type: "ellipse", size: [100, 100], stroke: { color: [1, 1, 1], width: o.edgeW || 3 } }, { position: o.center });
        ellipseSize(edge.property("ADBE Root Vectors Group").property("e")).expression = rExpr(o) + "[2*r,2*r];";
        U.opacity(edge).expression = fadeExpr(o);
        AEX.light.add(edge, o.lum);
        var wide = AEK.build.shape(lc, nm + " wisp matte", { name: "w", type: "ellipse", size: [100, 100], stroke: { color: [1, 1, 1], width: 40 } }, { position: o.center });
        ellipseSize(wide.property("ADBE Root Vectors Group").property("w")).expression = rExpr(o) + "var d=2*(r-" + (o.wispIn || 0.06) + "*r); [d,d];";
        strokeOf(wide.property("ADBE Root Vectors Group").property("w")).property("ADBE Vector Stroke Width").expression = rExpr(o) + "Math.max(8," + (o.wispW || 0.15) + "*r);";
        U.fx(wide, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.wispSoft || 18, "ADBE Gaussian Blur 2-0003": 0 });
        var nz = AEK.build.solid(lc, nm + " wisps", [0.5, 0.5, 0.5]);
        var nf = U.fx(nz, "ADBE Fractal Noise", { "ADBE Fractal Noise-0001": o.fractal || 1, "ADBE Fractal Noise-0002": 4, "ADBE Fractal Noise-0004": o.wispContrast || 220, "ADBE Fractal Noise-0005": o.wispBright === undefined ? -45 : o.wispBright, "ADBE Fractal Noise-0010": o.noiseScale || 90, "ADBE Fractal Noise-0015": 4, "ADBE Fractal Noise-0027": o.seed });
        nf.property("ADBE Fractal Noise-0023").expression = "time*" + (o.evolve || 400);
        nz.moveBefore(wide);
        nz.setTrackMatte(wide, TrackMatteType.ALPHA);
        U.opacity(nz).expression = fadeExpr(o);
        AEX.light.add(nz, o.wispLum || 0.5);
        var adj = wispDisplace(lc, o, nm + " wisp displace");
        return { edge: edge, wisps: nz, matte: wide, displace: adj };
    }
    // refraction(comp, o): two Displacement Maps on an adjustment layer above the plate. Each map comp is mid gray plus a horizontal (or
    // vertical) ramp seen through a soft band at the shock radius, with the same Turbulent Displace as the wisps; Wrap Pixels Around on.
    // o adds {amount (60 px at r1), bandIn, bandW (0.1), bandSoft, name}. Returns {layer, maps}.
    function refraction(c, o) {
        o = merge(o);
        var nm = o.name || "SW", W = c.width, H = c.height, R = o.r1, maps = [], i, mc, g, rp, bandL, m, dirs = ["H", "V"];
        for (i = 0; i < 2; i++) {
            mc = AEK.build.comp(nm + "_refr" + dirs[i], { width: W, height: H, fps: c.frameRate, duration: c.duration });
            AEK.build.solid(mc, "GREY", [0.5, 0.5, 0.5]);
            rp = AEK.build.solid(mc, "RAMP", [0.5, 0.5, 0.5]);
            U.fx(rp, "ADBE Ramp", {
                "ADBE Ramp-0001": i === 0 ? [o.center[0] - R, o.center[1]] : [o.center[0], o.center[1] - R], "ADBE Ramp-0002": [0, 0, 0],
                "ADBE Ramp-0003": i === 0 ? [o.center[0] + R, o.center[1]] : [o.center[0], o.center[1] + R], "ADBE Ramp-0004": [1, 1, 1], "ADBE Ramp-0005": 1
            });
            bandL = AEK.build.shape(mc, "BAND", { name: "b", type: "ellipse", size: [100, 100], stroke: { color: [1, 1, 1], width: 40 } }, { position: o.center });
            g = bandL.property("ADBE Root Vectors Group").property("b");
            ellipseSize(g).expression = rExpr(o) + "var d=2*(r-" + (o.bandIn || 0.04) + "*r); [d,d];";
            strokeOf(bandL.property("ADBE Root Vectors Group").property("b")).property("ADBE Vector Stroke Width").expression = rExpr(o) + "Math.max(10," + (o.bandW || 0.1) + "*r);";
            U.fx(bandL, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.bandSoft || 24, "ADBE Gaussian Blur 2-0003": 0 });
            U.opacity(bandL).expression = fadeExpr(o);
            rp.moveBefore(bandL);
            rp.setTrackMatte(bandL, TrackMatteType.ALPHA);
            if (o.wisp !== 0) { wispDisplace(mc, o, "map displace"); }
            m = c.layers.add(mc);
            m.enabled = false;
            m.name = nm + " refr map " + dirs[i];
            maps.push(m);
        }
        var adj = AEK.build.adjustment(c, nm + " refraction");
        adj.moveBefore(maps[0]);
        var amt = o.amount === undefined ? 60 : o.amount;
        // Displacement Map: -0001 map layer, -0002 / -0004 channel for H / V (5 luminance), -0003 / -0005 max px, -0007 Wrap Pixels Around
        U.fx(adj, "ADBE Displacement Map", { "ADBE Displacement Map-0001": maps[0].index, "ADBE Displacement Map-0002": 5, "ADBE Displacement Map-0003": amt, "ADBE Displacement Map-0004": 5, "ADBE Displacement Map-0005": 0, "ADBE Displacement Map-0007": 1 });
        U.fx(adj, "ADBE Displacement Map", { "ADBE Displacement Map-0001": maps[1].index, "ADBE Displacement Map-0002": 5, "ADBE Displacement Map-0003": 0, "ADBE Displacement Map-0004": 5, "ADBE Displacement Map-0005": amt, "ADBE Displacement Map-0007": 1 });
        return { layer: adj, maps: maps };
    }
    // mbSplit(layer, comp, frames): no motion blur on the first frames, a duplicate with motion blur from there (the switch cannot be keyed). Returns the duplicate.
    function mbSplit(l, c, frames) {
        var t = l.inPoint + frames * c.frameDuration, d = l.duplicate();
        l.motionBlur = false; l.outPoint = t;
        d.motionBlur = true; d.inPoint = t;
        c.motionBlur = true;
        return d;
    }
    return { DEFAULTS: DEFAULTS, rExpr: rExpr, fadeExpr: fadeExpr, polar: polar, stroke: stroke, ring: ring, refraction: refraction, mbSplit: mbSplit };
})();

AEX.rays = (function () {
    var U = AEX.vfxu;
    var DEFAULTS = { method: "lr", center: [960, 300], intensity: 100, radius: 60, amount: 95, zoom: 1, gain: 1, thr: 0.8, mode: "screen" };
    var MODES = { screen: BlendingMode.SCREEN, add: BlendingMode.ADD };
    // rays(layer, o): a light-only layer made into rays in place. method "lr": CC Light Rays (intensity, radius = the emitting circle; o.disc,
    // the source disc's radius in px, raises the radius to 1.2 x disc; o.preSoften and o.soften, Gaussian px before and after: soft beams, not wedges);
    // "zoom": CC Radial Fast Blur (amount, zoom 1 Standard / 2 Brightest), a starburst more than beams. Then o.gain, blend o.mode. Returns the layer.
    function rays(l, o) {
        o = U.merge(DEFAULTS, o);
        if (o.method === "lr") {
            // CC Light Rays emits from inside its radius only: a source disc larger than the radius covers its own rays (none visible)
            var rad = o.radius;
            if (o.disc && rad < 1.2 * o.disc) { rad = 1.2 * o.disc; }
            if (o.preSoften) { U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.preSoften, "ADBE Gaussian Blur 2-0003": 0 }, "Soften source"); }
            U.fx(l, "CC Light Rays", { "CC Light Rays-0001": o.intensity, "CC Light Rays-0002": o.center, "CC Light Rays-0003": rad });
            if (o.soften) { U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.soften, "ADBE Gaussian Blur 2-0003": 0 }, "Soften rays"); }
        } else {
            U.fx(l, "CC Radial Fast Blur", { "CC Radial Fast Blur-0001": o.center, "CC Radial Fast Blur-0002": o.amount, "CC Radial Fast Blur-0003": o.zoom });
        }
        if (o.gain !== 1) { U.gain(l, o.gain, "Ray gain"); }
        l.blendingMode = MODES[o.mode];
        return l;
    }
    // fromLight(comp, lightComp, o): the light-only comp as a layer, made into rays, Screen, moved just below o.under (the foreground). Returns the layer.
    function fromLight(c, light, o) {
        o = U.merge(DEFAULTS, o);
        var l = c.layers.add(light);
        l.name = o.name || "RAYS";
        rays(l, o);
        if (o.under) { l.moveAfter(o.under); }
        return l;
    }
    // fromPlate(comp, sceneComp, o): only a flattened plate exists. A copy keeps what is above o.thr (Levels Input Black -0003 = thr x Input
    // White -0004, which reads 1 at 16 bpc), made into rays, Screen. The rays still cross the foreground edge. Returns the layer.
    function fromPlate(c, scene, o) {
        o = U.merge(DEFAULTS, o);
        var l = c.layers.add(scene);
        l.name = o.name || "PLATE RAYS";
        var lv = U.fx(l, "ADBE Easy Levels2", {});
        lv.property("ADBE Easy Levels2-0003").setValue(o.thr * lv.property("ADBE Easy Levels2-0004").value);
        rays(l, o);
        return l;
    }
    // DAY: a neutral daylight map for AEX.light (top tone 0.96, so Screen cannot reach 255 from the rays alone).
    var DAY = { shadow: [0, 0, 0], dark: [0.2, 0.19, 0.17], mid: [0.6, 0.59, 0.56], bright: [0.86, 0.85, 0.82], high: [0.96, 0.95, 0.92] };
    // rig(comp, lightComp, o): the light (level 1) and a CC Light Rays copy (Add) inside an AEX.light rig, bloom total o.bloom (1.2), map o.tones
    // (DAY), rig layer in Screen under o.under. The sun disc maps to the top tone instead of clipping. preSoften (0.15 x disc or radius) and
    // soften (6 px) by default. Returns the rig.
    function rig(c, light, o) {
        o = U.merge(DEFAULTS, o);
        var r = AEX.light.rig(c, o.name || "RAYRIG", { bloom: { radii: AEX.light.radii(12, 5), weights: AEX.light.weights(o.bloom || 1.2, 5, 0.75) }, tones: o.tones || DAY });
        r.layer.blendingMode = BlendingMode.SCREEN;
        if (o.under) { r.layer.moveAfter(o.under); }
        var src = r.light.layers.add(light); src.name = "SOURCE"; AEX.light.add(src, 1.0);
        var d = r.light.layers.add(light); d.name = "RAYS";
        // in a rig, beams are softened by default: a sharp occluder edge cut hard-edged wedges
        rays(d, U.merge(o, { mode: "add", preSoften: o.preSoften === undefined ? 0.15 * (o.disc || o.radius) : o.preSoften, soften: o.soften === undefined ? 6 : o.soften }));
        return r;
    }
    return { DEFAULTS: DEFAULTS, DAY: DAY, rays: rays, fromLight: fromLight, fromPlate: fromPlate, rig: rig };
})();

AEX.bolt = (function () {
    var U = AEX.vfxu;
    // ELECTRIC: no channel at 1.0 (blue at 1.0 in three tones clipped the blue channel on up to 45,697 px; at 0.94 to 0.97, 7 to 522 px).
    var ELECTRIC = { shadow: [0, 0, 0], dark: [0.04, 0.07, 0.28], mid: [0.18, 0.42, 0.94], bright: [0.55, 0.8, 0.96], high: [0.88, 0.93, 0.97] };
    var DEFAULTS = { from: [700, 0], to: [1100, 760], strikes: [0, 9, 20], decay: 2.5, flicker: 0.35, hold: 2, seedJump: 37, wiggle: 0.15,
        core: 2.5, forking: 0.3, turbulence: 1.2, complexity: 6, lum: 1.2, bloom: 2.0, tones: null, spill: 8, spillBlur: 260 };
    function merge(o) { return U.merge(DEFAULTS, o); }
    // envExpr(o): expression, in stops for an Exposure (bypass linear): each strike decays as exp(-frames / decay), times a flicker
    // 1 - flicker x random held on o.hold frames; floor -12 stops.
    function envExpr(o) {
        return "var f=timeToFrames(time),S=[" + o.strikes.join(",") + "],e=0,k;for(k=0;k<S.length;k++){if(f>=S[k]){seedRandom(k*101+Math.floor((f-S[k])/" + o.hold + "),true);" +
            "e+=Math.exp(-(f-S[k])/" + o.decay + ")*(1-" + o.flicker + "*random());}}Math.max(-12,Math.log(Math.max(e,1e-4))/Math.LN2);";
    }
    // condExpr(o): Conductivity State: + seedJump at each strike (a new bolt), + wiggle every o.hold frames (even 0.15 redraws much of the bolt).
    function condExpr(o) {
        return "var f=timeToFrames(time),S=[" + o.strikes.join(",") + "],n=0,last=0,k;for(k=0;k<S.length;k++){if(f>=S[k]){n=k;last=S[k];}}" +
            "n*" + o.seedJump + "+Math.floor((f-last)/" + o.hold + ")*" + o.wiggle + ";";
    }
    // core(lightComp, o): a black solid with Advanced Lightning (Type 2 Strike, white core, Glow Opacity 0), the envelope Exposure, Add. Returns the solid.
    // Forking (-0017) takes 0 to 1 by script; Core Opacity (-0007) and Glow Opacity (-0012) take 0 to 100.
    function core(lc, o) {
        o = merge(o);
        var s = AEK.build.solid(lc, o.name || "BOLT", [0, 0, 0]);
        var lt = U.fx(s, "ADBE Lightning 2", {
            "ADBE Lightning 2-0001": 2, "ADBE Lightning 2-0002": o.from, "ADBE Lightning 2-0003": o.to,
            "ADBE Lightning 2-0006": o.core, "ADBE Lightning 2-0007": 100, "ADBE Lightning 2-0008": [1, 1, 1],
            "ADBE Lightning 2-0012": 0, "ADBE Lightning 2-0016": o.turbulence, "ADBE Lightning 2-0017": o.forking, "ADBE Lightning 2-0022": o.complexity
        });
        lt.property("ADBE Lightning 2-0004").expression = condExpr(o);
        var ex = U.fx(s, "ADBE Exposure2", { "ADBE Exposure2-0022": 1 }, "Strike envelope");
        ex.property("ADBE Exposure2-0003").expression = envExpr(o);
        AEX.light.add(s, o.lum);
        return s;
    }
    // strike(comp, o): an AEX.light rig (bloom radii 10 to 160, total o.bloom, map o.tones or ELECTRIC) in Screen, with core(). Returns the rig (+ core).
    function strike(c, o) {
        o = merge(o);
        var r = AEX.light.rig(c, o.name || "BOLT", { bloom: { radii: AEX.light.radii(10, 5), weights: AEX.light.weights(o.bloom, 5, 0.75) }, tones: o.tones || ELECTRIC });
        r.layer.blendingMode = BlendingMode.SCREEN;
        r.core = core(r.light, o);
        return r;
    }
    // spill(comp, rig, surfaceLayer, o): the light the strike throws: a soft ellipse pool on the surface at o.to (mid tone, reach 2.4 x
    // o.spillBlur, luma-matted by a duplicate of the surface) and a sky flash (a vertical ramp from the top down to o.to), both Add, both on the
    // strike envelope. Level at the strike peak: o.spill / 4 for the pool (before the matte), o.spill / 40 for the sky. A blurred copy of the bolt's own light
    // drew a box with hard vertical sides: its gain clipped the blurred line into a flat slab. Returns the pool layer.
    function spill(c, r, surf, o) {
        o = merge(o);
        var t = o.tones || ELECTRIC, nm = (o.name || "BOLT") + " spill", reach = 2.4 * o.spillBlur, x = o.to[0], y = o.to[1];
        function env(l, level) {
            var ex = U.fx(l, "ADBE Exposure2", { "ADBE Exposure2-0022": 1 }, "Strike envelope");
            ex.property("ADBE Exposure2-0003").expression = envExpr(o).replace(/;$/, "") + " + " + (Math.log(level) / Math.LN2).toFixed(4) + ";";   // the last statement is the value
            l.blendingMode = BlendingMode.ADD;
        }
        var sky = AEK.build.solid(c, nm + " sky", [0, 0, 0]);
        U.fx(sky, "ADBE Ramp", { "ADBE Ramp-0001": [x, 0], "ADBE Ramp-0002": U.scale(t.mid, 0.6), "ADBE Ramp-0003": [x, y], "ADBE Ramp-0004": [0, 0, 0], "ADBE Ramp-0005": 1 });
        env(sky, o.spill / 40);
        var l = AEK.build.solid(c, nm, t.mid);
        U.ellipse(l, x, y, reach, 0.32 * reach, [0.9 * reach, 0.3 * reach]);
        env(l, o.spill / 4);   // the luma matte of a dark surface scales it down again (a 0.15 gray keeps 15 %)
        if (r && r.layer) { sky.moveAfter(r.layer); l.moveAfter(r.layer); }
        if (surf) {
            var m = surf.duplicate();
            m.name = l.name + " matte";
            m.moveBefore(l);
            l.setTrackMatte(m, TrackMatteType.LUMA);
        }
        return l;
    }
    return { ELECTRIC: ELECTRIC, DEFAULTS: DEFAULTS, envExpr: envExpr, condExpr: condExpr, core: core, strike: strike, spill: spill };
})();

AEX.distort = (function () {
    var U = AEX.vfxu;
    // hazeMap(host, o): a displacement map comp: two blurred Fractal Noise fields tinted pure red (X) and green (Y) over neutral [0.5, 0.5, 0],
    // drifting up (heat rises). o = {name, scale (noise px), region [x0, y0, x1, y1], feather, rise (px/s, 90), speed (deg/s, 240), seed}. Returns the comp.
    // Reads as air while Max Displacement <= 0.1 x scale; melts from about 0.2 x scale.
    function hazeMap(host, o) {
        var W = host.width, H = host.height, nm = o.name || "HAZE", i, s, cols = [[1, 0, 0], [0, 1, 0]], f;
        var nc = AEK.build.comp(nm + "_NOISE", { width: W, height: H, fps: host.frameRate, duration: host.duration, bg: [0, 0, 0] });
        for (i = 0; i < 2; i++) {
            s = AEK.build.solid(nc, i ? "NY" : "NX", [0, 0, 0]);
            f = U.fx(s, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 100, "ADBE Fractal Noise-0010": o.scale, "ADBE Fractal Noise-0015": 3, "ADBE Fractal Noise-0027": (o.seed || 0) + 11 + i * 17 });
            f.property("ADBE Fractal Noise-0023").expression = "time * " + (o.speed || 240) + ";";
            f.property("ADBE Fractal Noise-0013").expression = "[" + W / 2 + ", " + H / 2 + " + time * " + (o.rise || 90) + "];";
            U.fx(s, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.scale / 20 });
            U.fx(s, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": cols[i] });
            if (i) { s.blendingMode = BlendingMode.ADD; }
        }
        var mc = AEK.build.comp(nm + "_MAP", { width: W, height: H, fps: host.frameRate, duration: host.duration, bg: [0, 0, 0] });
        AEK.build.solid(mc, "NEUTRAL", [0.5, 0.5, 0]);
        var nl = mc.layers.add(nc);
        if (o.region) { U.rect(nl, o.region[0], o.region[1], o.region[2], o.region[3], o.feather || 160); }
        return mc;
    }
    // ringMap(host, o): a refraction ring map: horizontal red and vertical green ramps (each point holds its outward direction) through a
    // ring matte, in a SQUARE comp 2 x (radius + width) wide (a host-sized comp crops a tall ring into straight edges), scaled 4 % to 100 %
    // over o.frames with an ease-out, faded in 2 frames and out over o.fade. o = {name, center, radius, width (70), at, frames (20), fade (10)}. Returns the comp.
    function ringMap(host, o) {
        var nm = o.name || "RING", r = o.radius, wd = o.width || 70, W = Math.ceil(2 * (r + wd)), H = W, cx = W / 2, cy = H / 2, fps = host.frameRate;
        var vc = AEK.build.comp(nm + "_VEC", { width: W, height: H, fps: fps, duration: host.duration, bg: [0, 0, 0] });
        var vx = AEK.build.solid(vc, "VX", [0, 0, 0]), vy = AEK.build.solid(vc, "VY", [0, 0, 0]);
        U.fx(vx, "ADBE Ramp", { "ADBE Ramp-0001": [cx - r, cy], "ADBE Ramp-0002": [0, 0, 0], "ADBE Ramp-0003": [cx + r, cy], "ADBE Ramp-0004": [1, 0, 0], "ADBE Ramp-0005": 1 });
        U.fx(vy, "ADBE Ramp", { "ADBE Ramp-0001": [cx, cy - r], "ADBE Ramp-0002": [0, 0, 0], "ADBE Ramp-0003": [cx, cy + r], "ADBE Ramp-0004": [0, 1, 0], "ADBE Ramp-0005": 1 });
        vy.blendingMode = BlendingMode.ADD;
        var sc = AEK.build.comp(nm + "_SHAPE", { width: W, height: H, fps: fps, duration: host.duration, bg: [0, 0, 0] });
        var vl = sc.layers.add(vc), ring = AEK.build.solid(sc, "RING_MATTE", [1, 1, 1]);
        U.ellipse(ring, cx, cy, r + wd / 2, r + wd / 2, wd * 0.45);
        U.ellipse(ring, cx, cy, r - wd / 2, r - wd / 2, wd * 0.45, { mode: MaskMode.SUBTRACT });
        vl.setTrackMatte(ring, TrackMatteType.ALPHA);
        var mc = AEK.build.comp(nm + "_MAP", { width: host.width, height: host.height, fps: fps, duration: host.duration, bg: [0, 0, 0] });
        AEK.build.solid(mc, "NEUTRAL", [0.5, 0.5, 0]);
        var sl = mc.layers.add(sc), tr = sl.property("ADBE Transform Group");
        tr.property("ADBE Position").setValue([o.center[0], o.center[1]]);
        var S = tr.property("ADBE Scale"), Op = tr.property("ADBE Opacity"), t0 = o.at, t1 = o.at + (o.frames || 20) / fps;
        S.setValueAtTime(t0, [4, 4]); S.setValueAtTime(t1, [100, 100]);
        AEK.motion.bezier(S, 1, 2, [0.1, 0.8, 0.3, 1]);
        Op.setValueAtTime(t0, 0); Op.setValueAtTime(t0 + 2 / fps, 100); Op.setValueAtTime(t1 - (o.fade || 10) / fps, 100); Op.setValueAtTime(t1, 0);
        return mc;
    }
    // dmap(layer, mapLayer, amount): Displacement Map, red horizontal (-0002 1), green vertical (-0004 2), max amount px both (negative
    // pushes the other way), Displacement Map Behavior Center (-0006 1), Expand Output off (-0008 0). The map layer index follows its layer
    // when layers are added above. Returns the effect.
    function dmap(l, mapLayer, amt) {
        return U.fx(l, "ADBE Displacement Map", { "ADBE Displacement Map-0001": mapLayer.index, "ADBE Displacement Map-0002": 1, "ADBE Displacement Map-0003": amt,
            "ADBE Displacement Map-0004": 2, "ADBE Displacement Map-0005": amt, "ADBE Displacement Map-0006": 1, "ADBE Displacement Map-0008": 0 });
    }
    // envelope(fx, amount, env): the strength of a Displacement Map over time; the map layer's opacity is ignored, so Max itself moves.
    // env: an expression returning 0 to 1 (for example an ENV slider), or [[seconds, 0 to 1], ...] keys (linear). Returns the effect.
    function envelope(fx, amt, env) {
        var ids = ["ADBE Displacement Map-0003", "ADBE Displacement Map-0005"], i, k, p;
        for (i = 0; i < 2; i++) {
            p = fx.property(ids[i]);
            if (typeof env === "string") { AEK.expr.set(p, amt + "*(" + env + ");"); }
            else { for (k = 0; k < env.length; k++) { p.setValueAtTime(env[k][0], amt * env[k][1]); } for (k = 1; k <= p.numKeys; k++) { p.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR); } }
        }
        return fx;
    }
    // padded(host, plateItem, pad, mode): the plate centered in a comp pad px larger on each side, so displacement samples picture beyond
    // the frame edge instead of transparent black. mode "mirror" (default): Motion Tile with mirrored edges on the plate, the border continues
    // the picture. mode "scale": the plate over a 112 % copy of itself (a displaced border pulled in a scaled sliver: 525 dark border px
    // against the plate's 76 on a daylight plate). One pad comp per plate and mode. Returns the comp.
    function padded(host, plate, pad, mode) {
        var mir = mode !== "scale", nm = "PAD_" + plate.name.replace(/\.[a-z0-9]+$/i, "") + (mir ? "" : "_S");
        var c = AEK.build.comp(nm, { width: host.width + 2 * pad, height: host.height + 2 * pad, fps: host.frameRate, duration: host.duration, bg: [0, 0, 0], reuse: true });
        if (c.numLayers) { return c; }
        var k = 100 * host.width / plate.width, over, under;
        if (mir) {
            over = c.layers.add(plate);
            over.property("ADBE Transform Group").property("ADBE Scale").setValue([k, k]);
            U.fx(over, "ADBE Tile", { "ADBE Tile-0004": 100 * (host.width + 2 * pad) / host.width + 1, "ADBE Tile-0005": 100 * (host.height + 2 * pad) / host.height + 1, "ADBE Tile-0006": 1 }, "mirror pad");
            return c;
        }
        under = c.layers.add(plate); over = c.layers.add(plate);
        under.property("ADBE Transform Group").property("ADBE Scale").setValue([k * 1.12, k * 1.12]);
        over.property("ADBE Transform Group").property("ADBE Scale").setValue([k, k]);
        return c;
    }
    // apply(host, plateItem, o): three channel copies of the (padded) plate (Channel Mixer), each displaced by the haze and the rings with
    // its own multiplier, added over black. o = {pad (48, 0 = off), padMode ("mirror" | "scale"), haze: hazeMap options + amount (+ split,
    // envelope), ring: one ringMap options object or an array of them, each + amount, inner, innerAmount, envelope; split [r, g, b] (0.88, 1, 1.14)}.
    // A ring is bipolar by default: an outer band at +amount and an inner band at radius - inner x width (inner 0.8) at innerAmount (-amount),
    // so the air between compresses like a lens edge; inner 0 gives the one-sign band, which slides the picture and barely reads in a still.
    // Keep |amount| / width at about 0.075 or under on fine texture: +/-8 px over 110 px held on grass, +/-11 over 80 tore it.
    // Returns {layers, maps, warnings} (layer names).
    function apply(host, plate, o) {
        var R = { layers: [], maps: [], warnings: [] }, ch, l, split = o.split || [0.88, 1, 1.14], i, q, rs = [], ring, fx;
        if (o.pad !== 0) { plate = padded(host, plate, o.pad || 48, o.padMode); }
        var hm = o.haze ? host.layers.add(hazeMap(host, o.haze)) : null;
        if (hm) { hm.enabled = false; R.maps.push(hm.name); }
        ring = o.ring ? (o.ring instanceof Array ? o.ring : [o.ring]) : [];
        for (i = 0; i < ring.length; i++) {
            q = ring[i];
            var rm = host.layers.add(ringMap(host, q)); rm.enabled = false; R.maps.push(rm.name);
            rs.push({ layer: rm, amount: q.amount, env: q.envelope });
            var inner = q.inner === undefined ? 0.8 : q.inner, wd = q.width || 70;
            if (Math.abs(q.amount) / wd > 0.1) { R.warnings.push("ring " + (q.name || i) + ": " + q.amount + " px over a " + wd + " px band tears fine texture (keep about 0.075 x width)"); }
            if (inner > 0) {
                var im = host.layers.add(ringMap(host, U.merge(q, { name: (q.name || "RING") + "_IN", radius: q.radius - inner * wd })));
                im.enabled = false; R.maps.push(im.name);
                rs.push({ layer: im, amount: q.innerAmount === undefined ? -q.amount : q.innerAmount, env: q.envelope });
            }
        }
        AEK.build.solid(host, "CHROMA_BLACK", [0, 0, 0]);
        var keep = [[100, 0, 0], [0, 100, 0], [0, 0, 100]];
        for (ch = 0; ch < 3; ch++) {
            l = host.layers.add(plate); l.name = "PLATE_" + ["R", "G", "B"][ch];
            U.fx(l, "ADBE CHANNEL MIXER", { "ADBE CHANNEL MIXER-0001": keep[ch][0], "ADBE CHANNEL MIXER-0006": keep[ch][1], "ADBE CHANNEL MIXER-0011": keep[ch][2] });
            if (hm) {
                fx = dmap(l, hm, o.haze.amount * (o.haze.split ? split[ch] : 1));
                if (o.haze.envelope) { envelope(fx, o.haze.amount * (o.haze.split ? split[ch] : 1), o.haze.envelope); }
            }
            for (i = 0; i < rs.length; i++) {
                fx = dmap(l, rs[i].layer, rs[i].amount * split[ch]);
                if (rs[i].env) { envelope(fx, rs[i].amount * split[ch], rs[i].env); }
            }
            if (ch > 0) { l.blendingMode = BlendingMode.ADD; }
            R.layers.push(l.name);
        }
        return R;
    }
    return { hazeMap: hazeMap, ringMap: ringMap, apply: apply, dmap: dmap, envelope: envelope, padded: padded };
})();

AEX.lens = (function () {
    var U = AEX.vfxu;
    // DEFAULTS: CA 0.15 % (0 px at the center, 2.7 px in the 1080p corners), FOV 12 with the layer at 102 % (FOV 30 needs 108 %), halation gain
    // 0.8, streak gain 0.6 (339 px half length at 160 px blur), CC Vignette 100 (-0.5 stop in the corner). Add Grain 1.5 is a film look for
    // a clean CG frame with no plate; over a plate, set grain to the plate's std over 4.2 levels per unit (dark) or 2.2 (mid gray): see AEX.vfx.grain.
    var DEFAULTS = { fov: 12, fill: 102, reverse: 0, ca: 0.0015, caMode: "scale", caShift: 2, halation: 0.8, halR: 18, halThr: 0.75, halColor: [1, 0.35, 0.15],
        streak: 0.6, streakLen: 160, streakThr: 0.8, streakColor: [0.45, 0.65, 1], vignette: 100, vigAngle: 45, grain: 1.5, grainSize: 1.1, mono: 1 };
    function merge(o) { return U.merge(DEFAULTS, o); }
    var OFF = 10; // Shift Channels popup 1 to 10: 1 Alpha, 2 Red, 3 Green, 4 Blue, 10 Full Off (11 throws "out of range 1 to 10")
    // ca(comp, src, o): three copies of src (a CompItem), one channel each, Add over black. "scale": red 1 + 2 ca, green 1 + ca, blue 1
    // (fringes grow toward the corners, none at the center; no copy below 100 % or the frame edge loses that channel); "shift": red and blue
    // moved caShift px (the same fringe everywhere). Returns the layers.
    function ca(c, src, o) {
        o = merge(o);
        var out = [], l, keep, sc, i;
        AEK.build.solid(c, "CA BLACK", [0, 0, 0]);
        for (i = 0; i < 3; i++) {
            l = c.layers.add(src);
            l.name = ["CA red", "CA green", "CA blue"][i];
            keep = [i === 0 ? 2 : OFF, i === 1 ? 3 : OFF, i === 2 ? 4 : OFF];
            U.fx(l, "ADBE Shift Channels", { "ADBE Shift Channels-0002": keep[0], "ADBE Shift Channels-0003": keep[1], "ADBE Shift Channels-0004": keep[2] });
            if (o.caMode === "scale") {
                sc = 100 * (1 + o.ca * (2 - i));
                l.property("ADBE Transform Group").property("ADBE Scale").setValue([sc, sc, 100]);
            } else if (i !== 1) {
                l.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2 + (i === 0 ? -o.caShift : o.caShift), c.height / 2]);
            }
            l.blendingMode = BlendingMode.ADD;
            out.push(l);
        }
        return out;
    }
    // highlights(comp, src, thr, name): a copy of src keeping what is above thr (Levels Input Black -0003; Input White reads 1 at 16 bpc), Screen. Returns the layer.
    function highlights(c, src, thr, name) {
        var l = c.layers.add(src);
        l.name = name;
        U.fx(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": thr }, "Keep highlights");
        l.blendingMode = BlendingMode.SCREEN;
        return l;
    }
    function tint(l, col) { U.fx(l, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": col }); }
    // halation(comp, src, o): highlights above halThr, Gaussian halR, tinted red-orange, gain o.halation, Screen. Returns the layer.
    function halation(c, src, o) {
        o = merge(o);
        var l = highlights(c, src, o.halThr, "HALATION");
        U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.halR, "ADBE Gaussian Blur 2-0003": 0 });
        tint(l, o.halColor);
        U.gain(l, o.halation);
        return l;
    }
    // streak(comp, src, o): highlights above streakThr, Gaussian Blur horizontal only (Blur Dimensions -0002 = 2) at streakLen, tinted blue, gain o.streak. Returns the layer.
    function streak(c, src, o) {
        o = merge(o);
        var l = highlights(c, src, o.streakThr, "STREAK");
        U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.streakLen, "ADBE Gaussian Blur 2-0002": 2, "ADBE Gaussian Blur 2-0003": 0 });
        tint(l, o.streakColor);
        U.gain(l, o.streak);
        return l;
    }
    // optics(layer, o): Optics Compensation ON THE SCENE LAYER, then the layer scaled to o.fill (transforms run after effects) so the black
    // corners leave the frame. On an adjustment layer the corners stay black whatever the scale below. o.reverse 1: pincushion. Returns the layer.
    function optics(l, o) {
        o = merge(o);
        U.fx(l, "ADBE Optics Compensation", { "ADBE Optics Compensation-0001": o.fov, "ADBE Optics Compensation-0002": o.reverse || 0 });
        var f = o.fill || 100;
        l.property("ADBE Transform Group").property("ADBE Scale").setValue([f, f, 100]);
        return l;
    }
    // vignette(comp, o): CC Vignette (CS Vignette) on an adjustment layer, amount o.vignette. Returns the layer.
    function vignette(c, o) {
        o = merge(o);
        var a = AEK.build.adjustment(c, "VIGNETTE");
        U.fx(a, "CS Vignette", { "CS Vignette-0001": o.vignette, "CS Vignette-0002": o.vigAngle, "CS Vignette-0003": [c.width / 2, c.height / 2] });
        return a;
    }
    // grain(comp, o): Add Grain on an adjustment layer, Final Output, monochrome (-0005), last in the stack. Returns the layer.
    function grain(c, o) {
        o = merge(o);
        var a = AEK.build.adjustment(c, "GRAIN");
        U.fx(a, "VISINF Grain Implant", { "VISINF Grain Implant-0021": 3, "VISINF Grain Implant-0008": o.grain, "VISINF Grain Implant-0007": o.grainSize, "VISINF Grain Implant-0005": o.mono });
        return a;
    }
    // apply(comp, sceneComp, o): optics in a wrapper comp first (so the copies see the distorted image), then CA, halation, streak, vignette,
    // grain last. o.skip {optics: 1, ca: 1, ...} leaves parts out. Returns the layers by part.
    function apply(c, scene, o) {
        o = merge(o);
        var sk = o.skip || {}, src = scene, w, r = {};
        if (!sk.optics) {
            w = AEK.build.comp(scene.name + "_lens", { width: scene.width, height: scene.height, fps: scene.frameRate, duration: scene.duration });
            optics(w.layers.add(scene), o);
            src = w;
        }
        if (!sk.ca) { r.ca = ca(c, src, o); } else { c.layers.add(src); }
        if (!sk.halation) { r.halation = halation(c, src, o); }
        if (!sk.streak) { r.streak = streak(c, src, o); }
        if (!sk.vignette) { r.vignette = vignette(c, o); }
        if (!sk.grain) { r.grain = grain(c, o); }
        return r;
    }
    return { DEFAULTS: DEFAULTS, ca: ca, highlights: highlights, halation: halation, streak: streak, optics: optics, vignette: vignette, grain: grain, apply: apply };
})();

AEX.integrate = (function () {
    var U = AEX.vfxu, INK = U.PALETTE.ink;
    // build(host, plateItem, o): a burst (AEX.burst geometry) as gray light in an AEX.light rig, sitting in the plate. Layers from the top:
    // grain (Noise, last), burst light (Add), reflection (flipped about the floor line, vertical box blur, alpha matte to the floor), floor pool,
    // interactive light (the plate tinted black to light color, radial falloff, Add), dim (a solid in o.black), plate. One envelope (a guide
    // null Slider reading the burst's mean luminance with sampleImage, divided by o.envRef) drives the interactive light, pool and dim.
    // o = {name, burst: AEX.burst options, floorY, lightColor, interactive (70), reach (700), poolShift, pool (30), reflection (30), dim (30),
    //   black (the plate's 1st percentile RGB, required for the dim: without it no dim layer is made and a warning is returned), soft (px),
    //   grain (Noise %, 3), envRef (0.25 placeholder; measure it from a burst-only frame: 0.19 gave +31.2 % on the nearest surface, 0.25 gave +29.6 %),
    //   envBox (260), bloomTotal (1.1), passes (false = burst only)}. Returns {layers, envelope, warnings} (layer names).
    function build(host, plate, o) {
        var nm = o.name || "FX", b = o.burst, cx = b.center[0], cy = b.center[1], R = { layers: [], warnings: [] }, W = host.width, H = host.height;
        var lightColor = o.lightColor || U.mix(U.PALETTE.cream, U.PALETTE.coral, 0.55), reach = o.reach || 700;
        var pl = host.layers.add(plate); pl.name = "PLATE";
        var rig = AEX.light.rig(host, nm + "_LIGHT", { bloom: { radii: AEX.light.radii(10, 5), weights: AEX.light.weights(o.bloomTotal || 1.1, 5, 0.75) } });
        var bo = U.merge(b, { name: nm + "_BURST", glow: 0, duration: host.duration });
        AEX.burst.planes(rig.light, bo);
        // the colored burst turned to gray light before the rig's map
        var grey = AEK.build.adjustment(rig.light, "TO_LIGHT");
        U.fx(grey, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": [1, 1, 1] });
        var bl = rig.layer;
        if (o.soft) { U.fx(bl, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.soft, "ADBE Gaussian Blur 2-0003": 0 }); }
        R.layers.push(bl.name);
        if (o.passes === false) { R.envelope = null; return R; }
        // envelope: sampleImage works at render time; read from a script it returned 0, so envRef comes from a measured frame
        var env = host.layers.addNull(); env.name = nm + "_ENVELOPE"; env.guideLayer = true; env.enabled = false;
        var sl = U.fx(env, "ADBE Slider Control", {}, "light");
        var eb = o.envBox || 260, ref = o.envRef || 0.25;
        sl.property(1).expression = "var s = thisComp.layer(\"" + bl.name + "\").sampleImage([" + cx + ", " + cy + "], [" + eb + ", " + eb + "], true, time);\n" +
            "clamp((0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]) / " + ref + ", 0, 1.5);";
        var E = "thisComp.layer(\"" + env.name + "\").effect(\"light\")(1)";
        // dim toward the plate's own black (o.black): a palette dark lighter than the plate's black raised its blacks 6.4 to 9 %
        var dm = null;
        if (o.black) {
            dm = AEK.build.solid(host, nm + "_DIM", o.black);
            U.opacity(dm).expression = "clamp(" + (o.dim === undefined ? 30 : o.dim) + " * " + E + ", 0, 100);";
        } else { R.warnings.push("no dim: pass black, the plate's 1st percentile RGB"); }
        var il = host.layers.add(plate); il.name = nm + "_INTERACTIVE";
        U.fx(il, "ADBE Tint", { "ADBE Tint-0001": [0, 0, 0], "ADBE Tint-0002": lightColor });
        U.ellipse(il, cx, cy, reach, reach * 0.85, reach * 0.9);
        il.blendingMode = BlendingMode.ADD;
        U.opacity(il).expression = "clamp(" + (o.interactive === undefined ? 70 : o.interactive) + " * " + E + ", 0, 100);";
        var fy = o.floorY || H * 0.68;
        var pool = AEK.build.solid(host, nm + "_POOL", lightColor);
        U.ellipse(pool, cx + (o.poolShift || 0), fy + 40, reach * 0.55, 60, 120);
        pool.blendingMode = BlendingMode.ADD;
        U.opacity(pool).expression = "clamp(" + (o.pool === undefined ? 30 : o.pool) + " * " + E + ", 0, 100);";
        var fm = AEK.build.solid(host, nm + "_FLOOR_MATTE", [1, 1, 1]);
        U.rect(fm, -100, fy, W + 100, H + 100, 60);
        var rf = host.layers.add(rig.sum); rf.name = nm + "_REFLECTION";
        AEX.light["map"](rf);   // bracket form: the light map, not Array.map
        var tr = rf.property("ADBE Transform Group");
        tr.property("ADBE Scale").setValue([100, -100]); tr.property("ADBE Position").setValue([W / 2, 2 * fy - H / 2]);
        U.fx(rf, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 18, "ADBE Box Blur2-0002": 3, "ADBE Box Blur2-0003": 3 });
        rf.blendingMode = BlendingMode.ADD;
        U.opacity(rf).setValue(o.reflection === undefined ? 30 : o.reflection);
        rf.setTrackMatte(fm, TrackMatteType.ALPHA);
        if (dm) { dm.moveBefore(pl); il.moveBefore(dm); } else { il.moveBefore(pl); } pool.moveBefore(il); fm.moveBefore(pool); rf.moveBefore(fm); bl.moveBefore(rf);
        // grain last; Noise clipping (-0003) at 0 wraps 16 bpc highlights into cyan specks: keep it 1
        var gr = AEK.build.adjustment(host, nm + "_GRAIN");
        U.fx(gr, "ADBE Noise", { "ADBE Noise-0001": o.grain === undefined ? 3 : o.grain, "ADBE Noise-0002": 0, "ADBE Noise-0003": 1 });
        gr.moveToBeginning();
        R.layers = dm ? [pl.name, dm.name, il.name, pool.name, rf.name, bl.name, gr.name] : [pl.name, il.name, pool.name, rf.name, bl.name, gr.name];
        R.envelope = env.name;
        return R;
    }
    return { build: build, INK: INK };
})();

AEX.pulse = (function () {
    // A hit leaving a subject that sits on a floor, built on a plate. One envelope null drives everything; the energy is gray light in TWO
    // AEX.light rigs split by depth (BACK behind and around the subject, held out by its choked matte after the bloom; FRONT on and in front
    // of it), every light layer in Screen over the plate. Then a camera comp (hold, push, shake) and a final comp (AEX.lens).
    var U = AEX.vfxu, P = U.PALETTE, BLACK = [0, 0, 0], WHITE = [1, 1, 1];
    // DEFAULTS. Geometry in comp px. center: where the pulse leaves the subject; floorY: floor line under it; floorAspect: ry / rx of a circle
    // lying on the floor (sine of the camera tilt); s: size multiplier for every radius; at: hit time (s); tau: decay of the hit (s).
    // Particle diameters are on-screen px (AEX.pn.sparks, 0.075 x width per Birth Size unit).
    // CORE, FLASH: [[radius px, peak light], ...] and the flash peak (cone radius 380). On the attack the cones are scaled 1.26x and
    // the FRONT bloom (total 0.9) adds about 0.9x the wide light again, all in Screen over the plate: the light at the center is cones +
    // flash + bloom + plate. Measured as the flat disc (luma at 0.98 x the top tone) on the scene comp, frames 0 to 3 after the hit:
    // [[28, 1.0], [100, 0.25], [320, 0.06]] with flash 0.42: 155, 61, 48, 40 px; these values: 22, 21, 13, 6 px, a hot point inside a
    // coral falloff. The flash changes the disc more than the wide cone: flash 0.2 gave 30 px, 0.28 gave 38 px.
    // Those discs were measured with flash 0.12 and FRONT bloom 0.9; 0.16 and 1.2 set the hit strength to 0.85 (vfx_measure.py flash), 0 % clipped.
    var CORE = [[18, 0.7], [90, 0.1], [320, 0.04]], FLASH = 0.16;
    // RIMTHR, EDGE: with the origin inside the subject every edge is near the source, and the lit haze behind it is bright all round:
    // the 2 px choke let the BACK rig through on every edge and the rim lit them all, a cream outline round the whole silhouette.
    // The rim now takes only BACK light above RIMTHR (rings and streaks passing behind), and the choke and the rim fade to nothing at EDGE
    // px from the origin (the far edges keep the full holdout). Far-side outline at the peak (frame 30, 0 to 3 px inside the edge minus 6 to
    // 12 px inside, more than 300 px from the origin): 41 before, 31 with RIMTHR alone, 20 with EDGE 640, 15 with EDGE 420. The cost is the
    // contour ratio on the peak frames: 1.04 before, 0.96 at 640, 0.93 at 420. 640 is the default; 0 turns the fade off.
    var RIMTHR = 0.35, EDGE = 640;
    // GRAIN: Add Grain intensity in the final comp, matched to the moving source of a held dark plate: temporal std 0.73 levels on flat
    // patches near 10/255, where Add Grain gives 4.2 levels per unit (2.2 at mid gray); 0.15 read -12 %, 0.2 +18 %.
    var GRAIN = 0.17;
    var DEFAULTS = {
        name: "PULSE", W: 1920, H: 1080, fps: 30, dur: 5, center: [960, 520], floorY: 765, floorAspect: 0.28, s: 1, at: 0.8, tau: 0.55, coreTau: 0.3, seed: 7,
        keyLo: 0.12, keyHi: 0.2, keyBottom: 772,              // subject matte on a DARK plate: luma key (black below keyLo, white above keyHi), cut at keyBottom (its reflection)
        matte: null, matteMode: "luma",                       // or a supplied matte item (footage or comp from keying, roto or a 3D pass), white = subject; "alpha" reads its alpha
        core: CORE, flash: FLASH, flashR: 380,                // see CORE: the light at the center on the attack counts cones, flash and the FRONT bloom together
        breath: 2.5,                                          // breathing glow: the soft cones (all but the first) read breath x pre; the tight cone reads core only
        tones: null,                                          // partial override of AEX.light.TONES for every map of the shot (rigs, rim, wrap, reflections)
        ring1: { r0: 30, r1: 1400, dur: 1.25, p: 3.5, lum: 0.55, wakeLum: 0.22, edgeW: 4 },
        ring2: { delay: 0.3, r0: 40, r1: 1000, dur: 1.6, p: 3, lum: 0.3, wakeLum: 0.14, edgeW: 3 },
        floorRing: { lum: 0.4, edgeW: 6, r1: 1050, dur: 2.6, p: 3.2, dash: 1 },  // wave "sphere": own slower travel so its last wisps stay in frame
        wave: "floor", shell: 0, floorPersp: 1.3,           // "floor": the hero is a ring lying on the floor (floorWave); shell > 0 adds a faint screen circle
                                                              // (ring1 at shell, no ring2); "sphere": both screen circles plus the floor ellipse, for a source in the air
        floorWave: { lum: 0.6, r0: 90, r1: 1050, dur: 2.2, p: 3.2, edge: 0.022, edgePx: 6, band: 0.16, bandLum: 0.35, echo: 0.45, echoDelay: 0.3, echoR1: 700 },
        bloomFloor: { r0: 8, n: 4, total: 0.6, k: 0.7 },
        emit: "surface",                                      // streaks born on the subject's outline (subjectBox, else emberBand x 0.9) along its normal; "point": from center
        breakFrom: 150, breakTo: -28,                         // Fractal Noise brightness of the break matte: whole ring at the hit, wisps by the end
        streaks: 36, streakLum: [0.55, 1.0], streakGain: 1.8, streakSplit: 0.45, near: 5, nearGain: 0.9, motionBlur: 1,  // 45 % behind the subject, 5 near the lens
        embers: 22, emberBack: 0.4, emberD: [3, 16], emberLife: [3.2, 5.4], emberBand: [480, 205], subjectBox: null, emberMode: "shapes",
                                                              // shape-layer embers born on an ellipse around the subject (emberBand half axes around the origin, or
                                                              // subjectBox [x0, y0, x1, y1] x 1.1), 40 % of them in the BACK rig; "particles" = the CC Particle World burst
        haze: 0.22, rays: 0.4, dustLit: 0.8, holdout: 94, holdSoft: 1.5, choke: 2,  // holdout choked 2 px, softened 1.5 px (a 6 px blur left a dark contour)
        rim: 3.2, rimW: 3, rimSrc: 6, rimThr: RIMTHR, edgeReach: EDGE, wrapFacing: 0.3, iR: 760,  // rim in a 3 px band from the BACK light above rimThr;
                                                              // choke and rim fade out at edgeReach px from the origin (0 = everywhere); wrap 1.0 to wrapFacing at iR
        ambient: 45, ambientMask: [820, 520, 420], beam: 12, dust: 100,  // percent opacities in the scene comp; ambient haze ellipse [rx, ry, feather] px around the origin
        interactive: 40, pool: 35, reflection: 25, refract: 24,      // hit strength 0.85 on hero3d.mp4 (vfx_measure.py flash; band 0.7 to 0.95)
        bloom: { r0: 10, n: 6, total: 1.2, k: 0.72 }, bloomBack: { r0: 16, n: 5, total: 0.7, k: 0.75 }, wrap: 3.5, wrapW: 26,
        halation: 0.4, halThr: 0.7, streak: 0.8, streakThr: 0.85, push: [100, 104], shake: 9, settle: 4.5,
        ca: 0.0015, vignette: 70, grain: GRAIN, grainSize: 1.0, grainMask: "auto", grainMove: 0.82, grainWhite: 0.15, hold: null  // frames frozen at the end (time remap in the camera comp): null = 15 on a
                                                              // still plate, 0 on a moving one (a hold freezes the plate's own motion too); grain: see GRAIN
    };
    function tg(l, mn) { return l.property("ADBE Transform Group").property(mn); }
    function rng(seed) { var x = seed * 9301 + 49297; return function () { x = (x * 9301 + 49297) % 233280; return x / 233280; }; }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function gcd(a, b) { while (b) { var t = b; b = a % b; a = t; } return a; }
    // poly(layer, verts, feather): a closed feathered polygon mask (beam trapezoids). Returns the mask.
    function poly(l, verts, feather) {
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"), sh = new Shape();
        sh.vertices = verts; sh.closed = true;
        m.property("ADBE Mask Shape").setValue(sh); m.property("ADBE Mask Feather").setValue([feather, feather]);
        return m;
    }
    // below(layer, o, y, feather): a feathered rectangle from y down past the frame bottom.
    function below(l, o, y, feather) { return U.rect(l, -200, y, o.W + 200, o.H + 200, feather); }
    function fitCover(l, item, o) { var k = 100 * Math.max(o.W / item.width, o.H / item.height); tg(l, "ADBE Scale").setValue([k, k]); tg(l, "ADBE Position").setValue([o.W / 2, o.H / 2]); }
    function comp(o, sfx, bg) { return AEK.build.comp(o.name + sfx, { width: o.W, height: o.H, fps: o.fps, duration: o.dur, bg: bg || BLACK }); }
    // env(scene, o): a guide null "ENV" with Slider expressions of time in frames from the hit (t): hit (0.75 on the hit frame, 1.0 one frame
    // later, then exp(-t / tau)), core (tau coreTau), flash (exp(-t / 1.1 frames)), haze (attack 4 frames, decay 0.8 e^(-t/33) + 0.2 e^(-t/90)),
    // shake (exp(-t / 3.5 frames)), pre (breathing 0.12 + 0.04 sin over 1.5 s and an inhale in the 9 frames before the hit). Returns the null.
    function env(sc, o) {
        var n = AEK.build.nullLayer(sc, "ENV"); n.guideLayer = true; n.enabled = false;
        var T = "var t=(time-" + o.at + ")*" + o.fps + ";", F = o.fps;
        var ex = {
            hit: T + "t<-0.5?0:(t<0.5?0.75:Math.min(1,Math.exp(-(t-1)/" + (o.tau * F) + ")));",
            core: T + "t<-0.5?0:(t<0.5?0.8:Math.min(1,Math.exp(-(t-1)/" + (o.coreTau * F) + ")));",
            flash: T + "t<-0.5?0:Math.exp(-Math.max(0,t)/1.1);",
            haze: T + "t<0?0:Math.min(1,1.5*(1-Math.exp(-t/4))*(0.8*Math.exp(-t/33)+0.2*Math.exp(-t/90)));",
            shake: T + "t<-0.5?0:Math.exp(-Math.max(0,t)/3.5);",
            pre: T + "var b=0.12+0.04*Math.sin(time*2*Math.PI/1.5)*(t<0?1:Math.exp(-t/15)); var a=(t>-9&&t<0.5)?0.18*Math.pow((t+9)/9,2):0; b+a;"
        }, k, sl;
        for (k in ex) { if (ex.hasOwnProperty(k)) { sl = U.fx(n, "ADBE Slider Control", {}, k); sl.property(1).expression = ex[k]; } }
        return n;
    }
    // E(o, key): the expression text reading one ENV slider of the scene comp.
    function E(o, k) { return "comp(\"" + o.name + "_SCENE\").layer(\"ENV\").effect(\"" + k + "\")(1)"; }
    // productMatte(o, plate): the subject matte comp, white = subject. With o.matte (a footage or comp item: a key from the
    // pre-composite source, a roto, a 3D matte pass; it may move) that matte fitted to the frame, read by luma or, with matteMode "alpha",
    // by its alpha. Without it, a luma key of the plate between keyLo and keyHi cut below keyBottom: it holds only on a DARK plate
    // (on a daylight plate it keys sky and ground). Returns the comp.
    function productMatte(o, plate) {
        var c = comp(o, "_PMATTE");
        AEK.build.solid(c, "BLACK", BLACK);
        if (o.matte) {
            var ml = c.layers.add(o.matte); ml.name = "MATTE"; fitCover(ml, o.matte, o);
            if (o.matteMode === "alpha") {
                var wh = AEK.build.solid(c, "WHITE", WHITE); wh.moveBefore(ml);
                wh.setTrackMatte(ml, TrackMatteType.ALPHA);
            }
            return c;
        }
        var l = c.layers.add(plate); l.name = "KEY";
        fitCover(l, plate, o);
        U.fx(l, "ADBE Tint", { "ADBE Tint-0001": BLACK, "ADBE Tint-0002": WHITE });
        U.fx(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.keyLo, "ADBE Easy Levels2-0004": o.keyHi });
        U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 2, "ADBE Gaussian Blur 2-0003": 0 });
        U.rect(l, -50, -50, o.W + 50, o.keyBottom, 6);
        return c;
    }
    // cone(comp, name, center, r, peak): a full-frame solid with a radial Gradient Ramp, white at the center to black at r, as light of peak value.
    function cone(c, name, ctr, r, peak) {
        var l = AEK.build.solid(c, name, BLACK);
        U.fx(l, "ADBE Ramp", { "ADBE Ramp-0001": ctr, "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [ctr[0] + r, ctr[1]], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 2 });
        AEX.light.add(l, peak);
        return l;
    }
    // density(o, sfx, scale, contrast): haze density, Fractal Noise with dark gaps, drifting, thicker low (vertical ramp in Multiply). Returns the comp.
    function density(o, sfx, scale, contrast) {
        var c = comp(o, "_DENSITY" + (sfx || ""));
        var n = AEK.build.solid(c, "NOISE", BLACK);
        var f = U.fx(n, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": contrast || 160, "ADBE Fractal Noise-0005": -25, "ADBE Fractal Noise-0010": scale || 400, "ADBE Fractal Noise-0015": 5,
            "ADBE Fractal Noise-0017": 55, "ADBE Fractal Noise-0027": o.seed });
        f.property("ADBE Fractal Noise-0023").expression = "time*14";
        f.property("ADBE Fractal Noise-0013").expression = "[" + o.W / 2 + "+time*18," + o.H / 2 + "-time*10];";
        var r = AEK.build.solid(c, "FALL", BLACK);
        U.fx(r, "ADBE Ramp", { "ADBE Ramp-0001": [o.W / 2, 0], "ADBE Ramp-0002": [0.35, 0.35, 0.35], "ADBE Ramp-0003": [o.W / 2, o.floorY], "ADBE Ramp-0004": WHITE, "ADBE Ramp-0005": 1 });
        r.blendingMode = BlendingMode.MULTIPLY;
        return c;
    }
    // falloff(o, src, r, name): src seen through a radial ramp around the center (Multiply), cut below the floor line. Returns the comp.
    function falloff(o, src, r, name) {
        var c = comp(o, "_" + name);
        // a black ground under src: a Multiply layer over transparent pixels shows itself, so over the transparent dust comp the ramp
        // alone drew a disc of light round the origin (the cream dome; 68 % of the peak-frame rise on a dark plate)
        AEK.build.solid(c, "GROUND", BLACK);
        c.layers.add(src);
        var m = AEK.build.solid(c, "FALLOFF", BLACK);
        U.fx(m, "ADBE Ramp", { "ADBE Ramp-0001": o.center, "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [o.center[0] + r, o.center[1]], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 2 });
        m.blendingMode = BlendingMode.MULTIPLY;
        below(AEK.build.solid(c, "BELOW FLOOR", BLACK), o, o.floorY - 20, 90);  // the air glows above the floor only
        return c;
    }
    // dust(o): slow motes over the upper frame, pre-rolled 5 s so they are there on frame 0. Returns {comp, pn}.
    function dust(o) {
        var c = comp(o, "_DUST");
        var l = AEK.build.solid(c, "MOTES", BLACK, { duration: o.dur + 5 });
        l.startTime = -5; l.outPoint = o.dur;  // a layer shifted earlier keeps its old end: reset outPoint after the shift
        var r = AEX.pn.sparks(l, { count: 170, life: 7, diameter: 3, deathDiameter: 2.4, speed: 14, fall: -5, sizeVar: 0.8, type: 5, color: [0.9, 0.87, 0.8], transfer: 1, seed: o.seed + 3, radius: 0.3, name: "Motes" });
        var e = l.property("ADBE Effect Parade").property("Motes");
        AEX.vfx.pwProp(e, "x").setValue((o.center[0] - 260 - o.W / 2) / o.W);
        AEX.vfx.pwProp(e, "y").setValue((o.center[1] - 200 - o.H / 2) / o.W);
        AEX.vfx.pwProp(e, "rx").setValue(0.32); AEX.vfx.pwProp(e, "ry").setValue(0.18); AEX.vfx.pwProp(e, "rz").setValue(0.2);
        var td = U.fx(l, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 18, "ADBE Turbulent Displace-0003": 220 });
        td.property("ADBE Turbulent Displace-0006").expression = "time*25";
        return { comp: c, pn: r };
    }
    // hideBefore(layers, R): opacity 0 before R.t0, then the ring fade (AEX.shock rings fade from 100 % before their start).
    function hideBefore(layers, R) {
        var i, ex = "var u=Math.min(1,Math.max(0,(time-" + R.t0 + ")/" + R.dur + ")); time<" + R.t0 + "?0:100*(1-u*u*" + (1 - (R.fadeTo || 0)) + ");";
        for (i = 0; i < layers.length; i++) { tg(layers[i], "ADBE Opacity").expression = ex; }
    }
    // rings(o, lightComp): ring 1 and ring 2 (AEX.shock.stroke), hidden before the hit, a Turbulent Displace that grows with age, and a
    // break matte (Fractal Noise in a square band comp, seam fix, Polar Coordinates) keyed from breakFrom to breakTo. Returns {rings, matte, band}.
    function rings(o, lc) {
        var a = o.at, s = o.s, c = comp(o, "_RINGS");
        var r1 = U.merge(o.ring1, { center: o.center, t0: a, r0: o.ring1.r0 * s, r1: o.ring1.r1 * s, fadeTo: 0, name: "R1", wake: 6, gap: 0.022, fall: 0.72 });
        var r2 = U.merge(o.ring2, { center: o.center, t0: a + o.ring2.delay, r0: o.ring2.r0 * s, r1: o.ring2.r1 * s, fadeTo: 0, name: "R2", wake: 4, gap: 0.02, fall: 0.7 });
        // wave "floor": the screen circle is only a faint shell of air around the hit; the ring on the floor carries the wave
        if (o.wave === "floor") { r1.lum = o.shell; r1.wakeLum = 0.4 * o.shell; }
        var A = AEX.shock.stroke(c, r1), B = o.wave === "floor" ? null : AEX.shock.stroke(c, r2);
        hideBefore([A.edge, A.wake], r1); if (B) { hideBefore([B.edge, B.wake], r2); }
        var td = U.fx(AEK.build.adjustment(c, "WOBBLE"), "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 10, "ADBE Turbulent Displace-0003": 70 * s, "ADBE Turbulent Displace-0010": o.seed });
        td.property("ADBE Turbulent Displace-0006").expression = "time*160";
        td.property("ADBE Turbulent Displace-0002").expression = "var u=Math.min(1,Math.max(0,(time-" + a + ")/" + o.ring1.dur + ")); 6+34*u;";
        var S = 2 * Math.ceil(o.ring1.r1 * s + 120), bc = AEK.build.comp(o.name + "_BREAKBAND", { width: S, height: S, fps: o.fps, duration: o.dur, bg: BLACK });
        var nz = AEK.build.solid(bc, "ARCS", BLACK);
        var nf = U.fx(nz, "ADBE Fractal Noise", { "ADBE Fractal Noise-0001": 1, "ADBE Fractal Noise-0002": 3, "ADBE Fractal Noise-0004": 240, "ADBE Fractal Noise-0009": 0,
            "ADBE Fractal Noise-0011": S / 7, "ADBE Fractal Noise-0012": 34, "ADBE Fractal Noise-0015": 3, "ADBE Fractal Noise-0027": o.seed + 5 });
        nf.property("ADBE Fractal Noise-0023").expression = "time*120";
        nf.property("ADBE Fractal Noise-0013").expression = "[" + S / 2 + ", " + S / 2 + "+time*260];";
        var br = nf.property("ADBE Fractal Noise-0005");
        br.setValueAtTime(a + 0.12, o.breakFrom); br.setValueAtTime(a + 1.15, o.breakTo);
        AEK.motion.bezier(br, 1, 2, [0.4, 0, 0.3, 1]);
        var fixL = AEK.build.adjustment(bc, "SEAM FIX");  // seam fix: Offset half the width, feathered masks at both edges
        U.fx(fixL, "ADBE Offset", { "ADBE Offset-0001": [S, S / 2] });
        U.rect(fixL, -S / 2, -10, 0.1 * S, S + 10, 0.1 * S);
        U.rect(fixL, 0.9 * S, -10, 1.5 * S, S + 10, 0.1 * S);
        var mc = comp(o, "_BREAK");
        AEK.build.solid(mc, "BLACK", BLACK);
        var bl = mc.layers.add(bc); tg(bl, "ADBE Position").setValue(o.center);
        U.fx(bl, "ADBE Polar Coordinates", { "ADBE Polar Coordinates-0001": 1, "ADBE Polar Coordinates-0002": 1 });
        below(AEK.build.solid(mc, "BELOW FLOOR", BLACK), o, o.floorY - 10, 110);  // the floor ring takes over below the floor line
        var rl = lc.layers.add(c); rl.name = "RINGS"; rl.blendingMode = BlendingMode.ADD;
        var ml = lc.layers.add(mc); ml.name = "BREAK MATTE"; ml.enabled = false;
        rl.setTrackMatte(ml, TrackMatteType.LUMA);
        return { rings: c, matte: mc, band: S };
    }
    // floorRing(o, lightComp, matteLayer): the wave where it meets the floor: an ellipse around the floor point under the center,
    // rx = sqrt(r^2 - h^2) with h = floorY - center y, ry = floorAspect x rx, on its own travel (floorRing.r1, dur, p); an edge plus one soft
    // band, dashes whose gap opens with age, held out by the inverted subject matte. Returns the layer.
    function floorRing(o, lc, pm) {
        var s = o.s, h = o.floorY - o.center[1], fr = o.floorRing, R = U.merge(o.ring1, { center: o.center, t0: o.at, r0: o.ring1.r0 * s, r1: fr.r1 * s, dur: fr.dur, p: fr.p, fadeTo: 0 });
        var rE = AEX.shock.rExpr(R), l = lc.layers.addShape(), k, g, st, dz;
        var fade = "var u=Math.min(1,Math.max(0,(time-" + o.at + ")/" + fr.dur + ")); time<" + o.at + "?0:100*Math.pow(1-u,1.4);";
        l.name = "FLOOR RING";
        var specs = [[0, fr.edgeW, 1], [0.05, 0.07, 0.4]];  // edge + one soft band: more wake strokes read as record grooves
        for (k = specs.length - 1; k >= 0; k--) {
            AEK.build.shapeGroup(l, { name: "f" + k, type: "ellipse", size: [10, 10], stroke: { color: WHITE, width: 4 } });
            g = l.property("ADBE Root Vectors Group").property("f" + k);
            g.property("ADBE Vectors Group").property("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").expression =
                rE + "var rx=Math.sqrt(Math.max(0,r*r-" + h * h + "))*(1-" + specs[k][0] + "); [2*rx, 2*rx*" + o.floorAspect + "];";
            st = g.property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke");
            st.property("ADBE Vector Stroke Width").expression = k === 0 ? String(fr.edgeW) : rE + "Math.max(2," + specs[k][1] + "*r*" + o.floorAspect + "*1.6);";
            st.property("ADBE Vector Stroke Opacity").setValue(100 * specs[k][2]);
            if (fr.dash) {
                try {
                    dz = st.property("ADBE Vector Stroke Dashes");
                    dz.addProperty("ADBE Vector Stroke Dash 1").expression = "var u=Math.min(1,Math.max(0,(time-" + o.at + ")/" + fr.dur + ")); 900-760*u;";
                    dz.addProperty("ADBE Vector Stroke Gap 1").expression = "var u=Math.min(1,Math.max(0,(time-" + o.at + ")/" + fr.dur + ")); 2+260*Math.pow(u,1.3);";
                    dz.addProperty("ADBE Vector Stroke Offset").expression = "time*" + (k ? -40 : 60) + ";";
                } catch (eD) { R.dashError = String(eD); }
            }
        }
        tg(l, "ADBE Position").setValue([o.center[0], o.floorY]);
        U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 5, "ADBE Gaussian Blur 2-0003": 0 });
        var td = U.fx(l, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 14, "ADBE Turbulent Displace-0003": 90, "ADBE Turbulent Displace-0010": o.seed + 2 });
        td.property("ADBE Turbulent Displace-0006").expression = "time*140";
        tg(l, "ADBE Opacity").expression = fade;
        AEX.light.add(l, fr.lum);
        l.setTrackMatte(pm, TrackMatteType.LUMA_INVERTED);
        return l;
    }
    // floorWave(o): the wave as a ring lying on the floor plane, the hero of a hit from a subject standing on a floor. Each ring is a filled
    // band between two closed paths projected through a pinhole: a floor point at depth z (px, positive away from the camera) lands at
    // x = cx + X k, y = floorY - a z k, with k = D / (D + z), a = floorAspect and D set so the ring at r1 is floorPersp x wider at the front than
    // at the back. The front half comes out lower, larger and thicker than the back half, as on a real floor. An edge band, a soft wake, a
    // fainter echo ring, a stretched noise matte that breaks the band into arcs as it ages. Returns the comp <name>_FLOORWAVE (gray on black).
    function floorWave(o) {
        var c = comp(o, "_FLOORWAVE"), F = o.floorWave, s = o.s, p = Math.max(1.01, o.floorPersp), D = F.r1 * s * (p + 1) / (p - 1), i, j, g, nm, root;
        var sh = c.layers.addShape(); sh.name = "WAVE";
        tg(sh, "ADBE Anchor Point").setValue([0, 0]); tg(sh, "ADBE Position").setValue([0, 0]);
        // [name, start (s), r1, duration, inner offset (share of r), width (share of r), width px, opacity %]
        var spec = [["edge", o.at, F.r1, F.dur, 0, F.edge, F.edgePx, 100], ["wake", o.at, F.r1, F.dur, F.edge, F.band, 0, 100 * F.bandLum],
            ["echo", o.at + F.echoDelay, F.echoR1, 1.1 * F.dur, 0, 1.2 * F.edge, 0.7 * F.edgePx, 100 * F.echo]];
        function path(q, inner) {
            var rr = inner ? "Math.max(0.5,r*(1-" + (q[4] + q[5]) + ")-" + q[6] * s + ")" : "r*(1-" + q[4] + ")";
            return "var u=Math.min(1,Math.max(0,(time-" + q[1] + ")/" + q[3] + ")), r=" + F.r0 * s + "+" + (q[2] - F.r0) * s + "*(1-Math.pow(1-u," + F.p + "));\n" +
                "var rr=" + rr + ",D=" + D + ",cx=" + o.center[0] + ",cy=" + o.floorY + ",a=" + o.floorAspect + ",N=96,pts=[],i,th,z,k;\n" +
                "for(i=0;i<N;i++){th=2*Math.PI*i/N;z=rr*Math.sin(th);k=D/(D+z);pts.push([cx+rr*Math.cos(th)*k,cy-a*z*k]);}\ncreatePath(pts,[],[],true);";
        }
        for (i = 0; i < spec.length; i++) {
            root = sh.property("ADBE Root Vectors Group"); root.addProperty("ADBE Vector Group");
            g = root.property(root.numProperties); nm = spec[i][0]; g.name = nm;
            for (j = 0; j < 2; j++) { sh.property("ADBE Root Vectors Group").property(nm).property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Group"); }
            sh.property("ADBE Root Vectors Group").property(nm).property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
            g = sh.property("ADBE Root Vectors Group").property(nm).property("ADBE Vectors Group");
            g.property(1).property("ADBE Vector Shape").expression = path(spec[i], false);
            g.property(2).property("ADBE Vector Shape").expression = path(spec[i], true);
            g.property(3).property("ADBE Vector Fill Color").setValue([1, 1, 1, 1]);
            g.property(3).property("ADBE Vector Fill Rule").setValue(2);   // even-odd: the inner path cuts the hole
            sh.property("ADBE Root Vectors Group").property(nm).property("ADBE Vector Transform Group").property("ADBE Vector Group Opacity").expression =
                "var u=Math.min(1,Math.max(0,(time-" + spec[i][1] + ")/" + spec[i][3] + ")); time<" + spec[i][1] + "?0:" + spec[i][7] + "*Math.pow(1-u,1.4);";
        }
        U.fx(sh, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 2.5 * s, "ADBE Gaussian Blur 2-0003": 0 });
        var td = U.fx(sh, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 8, "ADBE Turbulent Displace-0003": 80 * s, "ADBE Turbulent Displace-0010": o.seed + 4 });
        td.property("ADBE Turbulent Displace-0006").expression = "time*120";
        // break matte: noise stretched along the floor, whole at the hit, arcs and wisps by the end
        var nz = AEK.build.solid(c, "BREAK", BLACK);
        var nf = U.fx(nz, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 240, "ADBE Fractal Noise-0009": 0, "ADBE Fractal Noise-0011": 520 * s, "ADBE Fractal Noise-0012": 90 * s,
            "ADBE Fractal Noise-0015": 3, "ADBE Fractal Noise-0027": o.seed + 6 });
        nf.property("ADBE Fractal Noise-0023").expression = "time*90";
        var br = nf.property("ADBE Fractal Noise-0005");
        br.setValueAtTime(o.at + 0.15, 150); br.setValueAtTime(o.at + 1.4, -20);
        nz.moveBefore(sh); nz.enabled = false; sh.setTrackMatte(nz, TrackMatteType.LUMA);
        return c;
    }
    // floorMatte(o, chokeComp): the choked subject matte above the floor line only: the back half of the floor wave passes behind the
    // subject, the front half in front of it. Returns the comp.
    function floorMatte(o, ck) {
        var c = comp(o, "_FWMATTE");
        c.layers.add(ck);
        below(AEK.build.solid(c, "BELOW FLOOR", BLACK), o, o.floorY, 30);
        return c;
    }
    // subjectEllipse(o): {cx, cy, rx, ry} of the subject in comp px: subjectBox when given, else emberBand x 0.9 x s around the origin.
    function subjectEllipse(o) {
        if (o.subjectBox) { var b = o.subjectBox; return { cx: (b[0] + b[2]) / 2, cy: (b[1] + b[3]) / 2, rx: (b[2] - b[0]) / 2, ry: (b[3] - b[1]) / 2 }; }
        return { cx: o.center[0], cy: o.center[1], rx: 0.9 * o.emberBand[0] * o.s, ry: 0.9 * o.emberBand[1] * o.s };
    }
    // streaks(o, lightComp, sp): tapered strokes in one shape layer. Each streak is two groups on one decelerating, slightly falling path
    // (head at d0 + D (1 - exp(-t / tau))): a body tapered to 0 at the tail and a short head 1.7x wider and 1.25x brighter. Layer and comp
    // motion blur 180 degrees, 16 samples. sp = {name, n, seed, w [min, max] px, lum [min, max], d0 [min, max], D [min, max], blur, gain}. Returns the layer.
    function streaks(o, lc, sp) {
        var R = rng(sp.seed), l = lc.layers.addShape(), i, j, g, ang, d0, D, tau, lag, grav, del, life, w, lum, cx = o.center[0] - o.W / 2, cy = o.center[1] - o.H / 2, ex, st, tp, s = o.s, nm, parts;
        var surf = o.emit === "surface", se = subjectEllipse(o), th, nx, ny, nn;
        l.name = sp.name;
        for (i = 0; i < sp.n; i++) {
            if (surf) {
                // born on the outline, over the top and both sides down to 20 degrees below the horizontal, leaving along the outline's normal
                th = (-200 + 220 * (i + R()) / sp.n) * Math.PI / 180;
                cx = se.cx + 0.92 * se.rx * Math.cos(th) - o.W / 2; cy = Math.min(se.cy + 0.92 * se.ry * Math.sin(th), o.floorY - 6) - o.H / 2;
                nx = Math.cos(th) / se.rx; ny = Math.sin(th) / se.ry; nn = Math.sqrt(nx * nx + ny * ny); ang = Math.atan2(ny / nn, nx / nn);
            } else {
                ang = (-178 + 176 * (i + R()) / sp.n) * Math.PI / 180;             // upper half, spread evenly with jitter
            }
            d0 = lerp((surf ? sp.d0s : sp.d0)[0], (surf ? sp.d0s : sp.d0)[1], R()) * s; D = lerp(sp.D[0], sp.D[1], Math.pow(R(), 1.6)) * s;  // born past the face; most short
            tau = 0.08 + 0.4 * R(); lag = 0.03 + 0.12 * R(); grav = 60 + 260 * R(); del = Math.floor(4 * R()) / o.fps;
            life = 0.3 + 1.0 * R(); w = lerp(sp.w[0], sp.w[1], Math.pow(R(), 2.2)); lum = lerp(sp.lum[0], sp.lum[1], R());
            parts = [["b", lag, w, lum, 100], ["h", lag * 0.22, w * 1.7, Math.min(1, lum * 1.25), 70]];   // body, head
            for (j = 0; j < 2; j++) {
                nm = parts[j][0] + i;
                AEK.build.shapeGroup(l, { name: nm, type: "path", vertices: [[0, 0], [1, 0], [2, 0]], closed: false, stroke: { color: [parts[j][3], parts[j][3], parts[j][3]], width: parts[j][2], cap: "round" } });
                g = l.property("ADBE Root Vectors Group").property(nm);
                ex = "var a=" + (o.at + del) + ",cx=" + cx + ",cy=" + cy + ",c=" + Math.cos(ang) + ",s=" + Math.sin(ang) + ",d0=" + d0 + ",D=" + D + ",tau=" + tau + ",g=" + grav + ";\n" +
                    "function P(t){t=Math.max(0,t-a);var d=d0+D*(1-Math.exp(-t/tau));return [cx+c*d, cy+s*d+0.5*g*t*t];}\n" +
                    "createPath([P(time-" + parts[j][1] + "),P(time-" + parts[j][1] / 2 + "),P(time)],[],[],false);";
                g.property("ADBE Vectors Group").property("ADBE Vector Shape - Group").property("ADBE Vector Shape").expression = ex;
                g.property("ADBE Vector Transform Group").property("ADBE Vector Group Opacity").expression =
                    "var t=time-" + (o.at + del) + "; t<0?0:100*Math.pow(Math.max(0,1-t/" + (life * (j ? 0.8 : 1)) + "),1.6);";
                st = g.property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke");
                tp = st.property("ADBE Vector Stroke Taper");
                tp.property("ADBE Vector Taper Start Length").setValue(parts[j][4]);
                tp.property("ADBE Vector Taper Start Width").setValue(0);
            }
        }
        if (sp.blur) { U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": sp.blur, "ADBE Gaussian Blur 2-0003": 0 }); }
        if (o.motionBlur) { l.motionBlur = true; lc.motionBlur = true; lc.shutterAngle = 180; lc.shutterPhase = -90; lc.motionBlurSamplesPerFrame = 16; lc.motionBlurAdaptiveSampleLimit = 64; }
        AEX.light.add(l, sp.gain);
        return l;
    }
    // emberSizes(o): [min, max] diameter px from o.emberD (a number d is read as [d / 5, d]).
    function emberSizes(o) { return o.emberD instanceof Array ? o.emberD : [o.emberD / 5, o.emberD]; }
    // emberLayer(o, lightComp, name, n, seed, kSize, kLum): one shape layer of n embers. Each is born on the band ellipse in the upper half
    // (angles -172 to -8 degrees), thrown outward on a decelerating curve (70 to 300 px), then rises (14 to 48 px/s) and drifts by noise,
    // flickers, shrinks to 55 %, and fades over the last 45 % of a life drawn from emberLife (it can live into the hold). Diameters are
    // stratified over emberD with a square law (many small, few large), so the largest is emberD[1] / emberD[0] x the smallest. Returns {layer, sizes}.
    function emberLayer(o, lc, nm, n, seed, ks, kl) {
        var R = rng(seed), s = lc.layers.addShape(), k, g, ang, ex, ey, rx, ry, x0, y0, q, d, lum, a, D, tau, rise, sd, life, gn, tr, sizes = [];
        var cx = o.center[0] - o.W / 2, cy = o.center[1] - o.H / 2, band = o.emberBand, ds = emberSizes(o), lf = o.emberLife instanceof Array ? o.emberLife : [o.emberLife * 0.9, o.emberLife * 1.5];
        if (o.subjectBox) { var b = o.subjectBox; cx = (b[0] + b[2]) / 2 - o.W / 2; cy = (b[1] + b[3]) / 2 - o.H / 2; band = [0.55 * (b[2] - b[0]), 0.55 * (b[3] - b[1])]; }
        s.name = nm;
        var step = 7; while (gcd(step, n) !== 1) { step += 2; }
        for (k = 0; k < n; k++) {
            ang = (-172 + 164 * (k + R()) / n) * Math.PI / 180; ex = Math.cos(ang); ey = Math.sin(ang);
            rx = band[0] * o.s * lerp(1.0, 1.15, R()); ry = band[1] * o.s * lerp(1.0, 1.25, R());
            x0 = cx + ex * rx; y0 = cy + ey * ry;
            q = Math.pow((((k * step) % n) + R()) / n, 2);                    // stratified: every size class is drawn once in n embers
            d = lerp(ds[0], ds[1], q) * ks; lum = lerp(0.45, 1.0, Math.min(1, q * 1.3 + 0.15 * R())) * kl;
            a = o.at + lerp(0.03, 0.35, R()); D = lerp(70, 300, R()) * o.s; tau = lerp(0.25, 0.7, R()); rise = lerp(14, 48, R()); sd = Math.round(R() * 1000);
            life = lerp(lf[0], lf[1], R());
            gn = "em" + k;
            AEK.build.shapeGroup(s, { name: gn, type: "ellipse", size: [d, d], fill: [lum, lum, lum] });
            g = s.property("ADBE Root Vectors Group").property(gn);
            tr = g.property("ADBE Vector Transform Group");
            tr.property("ADBE Vector Position").expression = "var a=" + a + ",t=Math.max(0,time-a),D=" + D + ",tau=" + tau + ",d=D*(1-Math.exp(-t/tau));\n" +
                "[" + x0 + "+" + ex + "*d+22*noise([t*0.55," + sd + "]), " + y0 + "+" + (ey * (ry / rx)) + "*d-" + rise + "*t+10*noise([t*0.45," + (sd + 17) + "])];";
            tr.property("ADBE Vector Group Opacity").expression = "var t=time-" + a + ", f=Math.max(0,(t-" + (life * 0.55) + ")/" + (life * 0.45) + ");\n" +
                "t<0?0:Math.min(1,t/0.1)*(78+22*noise([time*6," + sd + "]))*Math.max(0,1-f*f);";
            tr.property("ADBE Vector Scale").expression = "var t=Math.max(0,time-" + a + "); var k=100*(1-0.45*Math.min(1,t/" + life + ")); [k,k];";
            sizes.push(Math.round(d * 10) / 10);
        }
        U.fx(s, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 1.2, "ADBE Gaussian Blur 2-0003": 0 });
        s.motionBlur = true;
        AEX.light.add(s, 1.0);
        return { layer: s, sizes: sizes };
    }
    // embers(o, frontComp, backComp): shape-layer embers around the subject, never emitted from inside it: (1 - emberBack) x o.embers in
    // the FRONT rig, the rest in the BACK rig (0.8 x size and light, held out by the matte with the rig). Returns {layer, back, count, sizes}.
    function embers(o, fc, bc) {
        var nB = bc ? Math.round(o.embers * o.emberBack) : 0, nF = o.embers - nB;
        var F = emberLayer(o, fc, "EMBERS", nF, o.seed * 17 + 11, 1, 1), B = nB ? emberLayer(o, bc, "EMBERS BACK", nB, o.seed * 19 + 5, 0.8, 0.8) : null;
        return { layer: F.layer, back: B ? B.layer : null, count: [nF, nB], sizes: B ? F.sizes.concat(B.sizes) : F.sizes, pn: null };
    }
    // embersPW(o, lightComp): the CC Particle World burst (emberMode "particles"): o.embers flying 540 px out from the origin, death color gray
    // 0.32, drift, flicker, faded before the hold. Emitted from inside the subject they stay over it and read as 2 to 4 px points at 1080p:
    // use it only when the origin is outside the subject. Returns {layer, pn}.
    function embersPW(o, lc) {
        var l = AEK.build.solid(lc, "EMBERS", BLACK), ed = emberSizes(o)[1] * 0.6;
        var r = AEX.pn.sparks(l, { count: o.embers, burstFrames: 4, at: o.at, life: o.emberLife instanceof Array ? o.emberLife[0] : o.emberLife, diameter: ed, deathDiameter: ed * 0.45, speed: 430 * o.s, stop: 540 * o.s, fall: -45, sizeVar: 0.6,
            type: 5, color: WHITE, deathColor: [0.32, 0.32, 0.32], transfer: 1, seed: o.seed + 11, radius: 0.03, name: "Embers" });
        var e = l.property("ADBE Effect Parade").property("Embers");
        AEX.vfx.pwProp(e, "x").setValue((o.center[0] - o.W / 2) / o.W);
        AEX.vfx.pwProp(e, "y").setValue((o.center[1] - o.H / 2) / o.W);
        AEX.vfx.pwProp(e, "colorMap").setValue(2);
        var td = U.fx(l, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 34, "ADBE Turbulent Displace-0003": 230 });
        td.property("ADBE Turbulent Displace-0006").expression = "time*55";
        tg(l, "ADBE Opacity").expression = "var f=Math.min(1,Math.max(0,(time-" + (o.at + 2.4) + ")/1.1)); (75+25*noise(time*11))*(1-f*f);";
        AEX.light.add(l, 1.3);
        return { layer: l, pn: r };
    }
    // oneRig(o, scene, suffix, b): an AEX.light rig with bloom {r0, n, total, k}, its layer in Screen. Returns the rig.
    function oneRig(o, sc, nm, b) {
        var R = AEX.light.rig(sc, o.name + "_" + nm, { bloom: { radii: AEX.light.radii(b.r0, b.n), weights: AEX.light.weights(b.total, b.n, b.k) }, tones: o.tones });
        R.layer.blendingMode = BlendingMode.SCREEN;
        return R;
    }
    // rigs(o, scene, matteItem, densityComp, dustComp): FRONT (core cones, flash, front and near streaks, embers) and BACK (rings, floor
    // ring, back streaks, lit haze, rays, lit dust). Returns {front, back, rings, floorRing, streaks, embers}.
    function rigs(o, sc, pmItem, dens, du) {
        var F = oneRig(o, sc, "FRONT", o.bloom), B = oneRig(o, sc, "BACK", o.bloomBack), fc = F.light, bc = B.light, i, l;
        var pm = bc.layers.add(pmItem); pm.name = "PRODUCT MATTE"; pm.enabled = false;
        for (i = 0; i < o.core.length; i++) {
            l = cone(fc, "CORE " + o.core[i][0], o.center, o.core[i][0] * o.s, o.core[i][1]);
            // breathing on the soft cones only: on the tight cone it read as an LED dot, at 1 x pre on the soft cones it was invisible
            tg(l, "ADBE Opacity").expression = i === 0 ? "100*" + E(o, "core") + ";" : "100*Math.min(1,Math.max(" + o.breath + "*" + E(o, "pre") + "," + E(o, "core") + "));";
            tg(l, "ADBE Anchor Point").setValue(o.center); tg(l, "ADBE Position").setValue(o.center);
            tg(l, "ADBE Scale").expression = "var k=85+30*" + E(o, "flash") + "+15*" + E(o, "hit") + "; [k,k];";
        }
        l = cone(fc, "FLASH", o.center, o.flashR * o.s, o.flash);
        tg(l, "ADBE Opacity").expression = "100*" + E(o, "flash") + ";";
        var nB = Math.round(o.streaks * o.streakSplit), nF = o.streaks - nB, sp = { d0: [200, 420], d0s: [0, 60], D: [240, 1140], lum: o.streakLum, gain: o.streakGain };
        var st = streaks(o, fc, U.merge(sp, { name: "STREAKS FRONT", n: nF, seed: o.seed * 7 + 1, w: [2, 9] }));
        var nr = streaks(o, fc, { name: "STREAKS NEAR", n: o.near, seed: o.seed * 13 + 5, w: [16, 30], lum: [0.3, 0.5], d0: [260, 520], d0s: [40, 160], D: [700, 1500], blur: 9, gain: o.nearGain });
        var em = o.emberMode === "particles" ? embersPW(o, fc) : embers(o, fc, bc);
        var rg = o.wave === "floor" && !(o.shell > 0) ? null : rings(o, bc);   // floor wave with no shell: no screen circle at all
        var fr = o.wave === "floor" ? null : floorRing(o, bc, pm), fw = null;
        if (o.wave === "floor") {
            fw = oneRig(o, sc, "FLOOR", o.bloomFloor);
            AEX.light.add(fw.light.layers.add(floorWave(o)), o.floorWave.lum);
        }
        var sb = streaks(o, bc, U.merge(sp, { name: "STREAKS BACK", n: nB, seed: o.seed * 11 + 3, w: [1.5, 6], lum: [0.45, 0.85] }));
        if (em.back) { em.back.moveToBeginning(); }
        var lh = bc.layers.add(falloff(o, dens, 900 * o.s, "LITHAZE")); lh.name = "LIT HAZE";
        tg(lh, "ADBE Opacity").expression = "100*Math.min(1,Math.max(" + E(o, "haze") + ",1.5*" + E(o, "pre") + "));";
        AEX.light.add(lh, o.haze);
        // rays: the lit haze blurred along the radius (CC Radial Fast Blur on the lit air only, never on the frame); finer, harder noise
        var ry = bc.layers.add(falloff(o, density(o, "_FINE", 140, 230), 700 * o.s, "RAYSRC"));
        ry.name = "RAYS";
        U.fx(ry, "CC Radial Fast Blur", { "CC Radial Fast Blur-0001": o.center, "CC Radial Fast Blur-0002": 88, "CC Radial Fast Blur-0003": 1 });
        tg(ry, "ADBE Opacity").expression = "100*" + E(o, "haze") + ";";
        AEX.light.add(ry, o.rays);
        var dl = bc.layers.add(falloff(o, du, 650 * o.s, "DUSTLIT")); dl.name = "LIT DUST";
        tg(dl, "ADBE Opacity").expression = "100*" + E(o, "haze") + ";";
        AEX.light.add(dl, o.dustLit);
        return { front: F, back: B, floor: fw, rings: rg, floorRing: fr ? fr.name : null, streaks: [st.name, nr.name, sb.name], embers: em };
    }
    // facing(o, comp, reach, end): a radial ramp in Multiply from the origin (1.0) to end at reach px (default wrapFacing at iR): edges
    // near the source take more light. With the origin inside the subject every edge is near it: rimMatte uses reach = edgeReach, end 0.
    function facing(o, c, reach, end) {
        var r = AEK.build.solid(c, "FACING", BLACK), f = end === undefined ? o.wrapFacing : end;
        U.fx(r, "ADBE Ramp", { "ADBE Ramp-0001": o.center, "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [o.center[0] + (reach || o.iR) * o.s, o.center[1]], "ADBE Ramp-0004": [f, f, f], "ADBE Ramp-0005": 2 });
        r.blendingMode = BlendingMode.MULTIPLY;
        return r;
    }
    // erode(comp, item, px): the matte shrunk by about px: Gaussian Blur 2 x px, then Levels black 0.82, white 0.98. Returns the layer.
    function erode(c, item, px) {
        var l = c.layers.add(item);
        U.fx(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 2 * px, "ADBE Gaussian Blur 2-0003": 0 });
        U.fx(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": 0.82, "ADBE Easy Levels2-0004": 0.98 });
        return l;
    }
    // reachRamp(o, comp, name): a full-frame solid, black at the origin to white at edgeReach px (radial), for "far from the source".
    function reachRamp(o, c, name) {
        var r = AEK.build.solid(c, name, BLACK);
        U.fx(r, "ADBE Ramp", { "ADBE Ramp-0001": o.center, "ADBE Ramp-0002": BLACK, "ADBE Ramp-0003": [o.center[0] + o.edgeReach * o.s, o.center[1]], "ADBE Ramp-0004": WHITE, "ADBE Ramp-0005": 2 });
        return r;
    }
    // chokeMatte(o, matteItem): the holdout matte choked by o.choke px near the origin and feathered by o.holdSoft; with edgeReach, the
    // unchoked matte takes over (Lighten) toward edgeReach px, so far edges keep the full holdout. Returns the comp.
    function chokeMatte(o, pmItem) {
        var c = comp(o, "_PMCHOKE");
        var l = erode(c, pmItem, o.choke);
        if (o.edgeReach) {
            var u = c.layers.add(pmItem); u.name = "FAR EDGES"; u.blendingMode = BlendingMode.LIGHTEN;
            var rr = reachRamp(o, c, "FAR"); rr.enabled = false; u.setTrackMatte(rr, TrackMatteType.LUMA);
        }
        var f = AEK.build.adjustment(c, "FEATHER");
        U.fx(f, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.holdSoft, "ADBE Gaussian Blur 2-0003": 0 });
        f.moveToBeginning();
        return c;
    }
    // wrapMatte(o, matteItem): the inner edge band (matte x inverted wrapW px blurred matte), weighted toward the origin. Returns the comp.
    function wrapMatte(o, pmItem) {
        var c = comp(o, "_WRAPMATTE");
        c.layers.add(pmItem);
        var b = c.layers.add(pmItem);
        U.fx(b, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.wrapW, "ADBE Gaussian Blur 2-0003": 0 });
        U.fx(b, "ADBE Invert", {});
        b.blendingMode = BlendingMode.MULTIPLY;
        facing(o, c);
        return c;
    }
    // rimMatte(o, matteItem): the matte minus its copy eroded by rimW px, feathered 1 px, weighted toward the origin. Returns the comp.
    function rimMatte(o, pmItem) {
        var c = comp(o, "_RIMMATTE");
        c.layers.add(pmItem);
        var e = erode(c, pmItem, o.rimW); e.blendingMode = BlendingMode.SUBTRACT;
        var f = AEK.build.adjustment(c, "FEATHER");
        U.fx(f, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 1, "ADBE Gaussian Blur 2-0003": 0 });
        var fc = o.edgeReach ? facing(o, c, o.edgeReach, 0) : facing(o, c); fc.moveToBeginning();
        return c;
    }
    // interactiveComp(o, plate, color): the plate tinted black to color, times a radial ramp from the origin (white to black at iR). Returns the comp.
    function interactiveComp(o, plate, col) {
        var c = comp(o, "_INTERACTIVE");
        var l = c.layers.add(plate); fitCover(l, plate, o);
        U.fx(l, "ADBE Tint", { "ADBE Tint-0001": BLACK, "ADBE Tint-0002": col });
        var r = AEK.build.solid(c, "FROM ORIGIN", BLACK);
        U.fx(r, "ADBE Ramp", { "ADBE Ramp-0001": o.center, "ADBE Ramp-0002": WHITE, "ADBE Ramp-0003": [o.center[0] + o.iR * o.s, o.center[1]], "ADBE Ramp-0004": BLACK, "ADBE Ramp-0005": 2 });
        r.blendingMode = BlendingMode.MULTIPLY;
        return c;
    }
    // scene(o, plate): the scene comp <name>_SCENE. Bottom up: plate, ambient haze, beam, dust, interactive, pool, refraction, reflections,
    // BACK rig (held out by the choked matte), light wrap, rim, FRONT rig, halation, lens streak. Returns {comp, rig, layers, dust}.
    function scene(o, plate) {
        var sc = comp(o, "_SCENE", P.ink), R = { layers: [] };
        var pl = sc.layers.add(plate); pl.name = "PLATE"; fitCover(pl, plate, o);
        var en = env(sc, o);
        var pmc = productMatte(o, plate), dens = density(o), du = dust(o);
        var T = AEX.light.tones(o.tones), am = sc.layers.add(dens); am.name = "AMBIENT HAZE";
        U.fx(am, "ADBE Tint", { "ADBE Tint-0001": BLACK, "ADBE Tint-0002": P.navy });
        am.blendingMode = BlendingMode.SCREEN; tg(am, "ADBE Opacity").setValue(o.ambient);
        // haze behind the subject, corners keep their black: 1000 x 650 feather 600 raised the plate's p1 black 6.2 % beyond 900 px
        U.ellipse(am, o.center[0], o.center[1] - 60, o.ambientMask[0] * o.s, o.ambientMask[1] * o.s, o.ambientMask[2] * o.s);
        var pmA = sc.layers.add(pmc); pmA.name = "PM_AMB"; pmA.enabled = false; am.setTrackMatte(pmA, TrackMatteType.LUMA_INVERTED);
        var bm = AEK.build.solid(sc, "BEAM", [0.75, 0.72, 0.66]);
        var c0 = o.center;
        poly(bm, [[c0[0] - 620, -150], [c0[0] - 300, -150], [c0[0] + 120, c0[1] + 230], [c0[0] - 420, c0[1] + 230]], 170);
        bm.blendingMode = BlendingMode.SCREEN; tg(bm, "ADBE Opacity").setValue(o.beam);
        var pmB = sc.layers.add(pmc); pmB.name = "PM_BEAM"; pmB.enabled = false; bm.setTrackMatte(pmB, TrackMatteType.LUMA_INVERTED);
        var dl = sc.layers.add(du.comp); dl.name = "DUST"; dl.blendingMode = BlendingMode.SCREEN; tg(dl, "ADBE Opacity").setValue(o.dust);
        var bmM = AEK.build.solid(sc, "BEAM MATTE", WHITE);
        poly(bmM, [[c0[0] - 640, -150], [c0[0] - 280, -150], [c0[0] + 160, c0[1] + 260], [c0[0] - 460, c0[1] + 260]], 120);
        bmM.enabled = false; dl.setTrackMatte(bmM, TrackMatteType.ALPHA);
        var il = sc.layers.add(interactiveComp(o, plate, U.mix(P.coral, P.cream, 0.35))); il.name = "INTERACTIVE";
        il.blendingMode = BlendingMode.SCREEN;
        tg(il, "ADBE Opacity").expression = "Math.min(100," + o.interactive + "*Math.max(" + E(o, "hit") + "+0.3*" + E(o, "flash") + ",1.2*" + E(o, "pre") + "));";
        var po = AEK.build.solid(sc, "POOL", P.coral);
        U.ellipse(po, c0[0], o.floorY + 30, 620 * o.s, 120 * o.s, 160 * o.s);
        po.blendingMode = BlendingMode.SCREEN;
        tg(po, "ADBE Opacity").expression = o.pool + "*Math.max(" + E(o, "hit") + ",0.8*" + E(o, "pre") + ");";
        // refraction reads only over texture: on a smooth dark plate pass refract 0 (no layer)
        var rf = null;
        if (o.refract) {
            rf = AEX.shock.refraction(sc, { name: o.name + "_RF", center: c0, t0: o.at, dur: o.ring1.dur, r0: o.ring1.r0 * o.s, r1: o.ring1.r1 * o.s, p: o.ring1.p, fadeTo: 0, amount: o.refract, wisp: 0, bandW: 0.08 });
            hideBefore([AEK.core.comp(o.name + "_RF_refrH").layer("BAND"), AEK.core.comp(o.name + "_RF_refrV").layer("BAND")], { t0: o.at, dur: o.ring1.dur, fadeTo: 0 });
        }
        var RG = rigs(o, sc, pmc, dens, du.comp);
        var pmR = sc.layers.add(chokeMatte(o, pmc)); pmR.name = "PM_RIG"; pmR.enabled = false;
        tg(pmR, "ADBE Opacity").setValue(o.holdout);
        RG.back.layer.setTrackMatte(pmR, TrackMatteType.LUMA_INVERTED);
        if (RG.floor) {
            var pmF = sc.layers.add(floorMatte(o, pmR.source)); pmF.name = "PM_FLOOR"; pmF.enabled = false; tg(pmF, "ADBE Opacity").setValue(o.holdout);
            RG.floor.layer.setTrackMatte(pmF, TrackMatteType.LUMA_INVERTED);
        }
        var wm = sc.layers.add(wrapMatte(o, pmc)); wm.name = "WRAP MATTE"; wm.enabled = false;
        var wr = sc.layers.add(RG.back.sum); wr.name = "LIGHT WRAP";
        AEX.light["map"](wr, T);
        U.fx(wr, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 30, "ADBE Gaussian Blur 2-0003": 0 });
        U.gain(wr, o.wrap, "Gain"); wr.blendingMode = BlendingMode.SCREEN;
        wr.setTrackMatte(wm, TrackMatteType.LUMA);
        var rm = sc.layers.add(rimMatte(o, pmc)); rm.name = "RIM MATTE"; rm.enabled = false;
        var ri = sc.layers.add(RG.back.sum); ri.name = "RIM";
        // only light above rimThr makes a rim (rings and streaks passing behind the edge); the lit haze around an origin inside the
        // subject drew a cream outline on the whole silhouette, far ends included
        if (o.rimThr > 0) { U.fx(ri, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.rimThr }, "Rim threshold"); }
        AEX.light["map"](ri, T);
        U.fx(ri, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": o.rimSrc, "ADBE Gaussian Blur 2-0003": 0 });
        U.gain(ri, o.rim, "Gain"); ri.blendingMode = BlendingMode.SCREEN;
        ri.setTrackMatte(rm, TrackMatteType.LUMA);
        var fm = AEK.build.solid(sc, "FLOOR MATTE", WHITE);
        U.rect(fm, -100, o.floorY - 5, o.W + 100, o.H + 100, 50);
        fm.enabled = false;
        var refl = [], j, rl, srcs = [RG.front.sum, RG.back.sum];
        for (j = 0; j < 2; j++) {
            rl = sc.layers.add(srcs[j]); rl.name = "REFLECTION " + (j ? "BACK" : "FRONT");
            AEX.light["map"](rl, T);
            tg(rl, "ADBE Scale").setValue([100, -100]); tg(rl, "ADBE Position").setValue([o.W / 2, 2 * o.floorY - o.H / 2]);
            U.fx(rl, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 16, "ADBE Box Blur2-0002": 3, "ADBE Box Blur2-0003": 3 });
            rl.blendingMode = BlendingMode.SCREEN; tg(rl, "ADBE Opacity").setValue(o.reflection);
            rl.setTrackMatte(fm, TrackMatteType.ALPHA);
            refl.push(rl);
        }
        var ha = sc.layers.add(RG.front.sum); ha.name = "HALATION";
        U.fx(ha, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.halThr });
        U.fx(ha, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 22, "ADBE Gaussian Blur 2-0003": 0 });
        U.fx(ha, "ADBE Tint", { "ADBE Tint-0001": BLACK, "ADBE Tint-0002": [1, 0.35, 0.15] });
        U.gain(ha, o.halation, "Gain"); ha.blendingMode = BlendingMode.SCREEN;
        var sk = sc.layers.add(RG.front.sum); sk.name = "LENS STREAK";
        U.fx(sk, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": o.streakThr });
        U.fx(sk, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 240, "ADBE Gaussian Blur 2-0002": 2, "ADBE Gaussian Blur 2-0003": 0 });
        U.fx(sk, "ADBE Tint", { "ADBE Tint-0001": BLACK, "ADBE Tint-0002": [1, 0.72, 0.58] });
        U.gain(sk, o.streak, "Gain");
        tg(sk, "ADBE Anchor Point").setValue(c0); tg(sk, "ADBE Position").setValue(c0); tg(sk, "ADBE Scale").setValue([120, 10]);
        sk.blendingMode = BlendingMode.SCREEN;
        var order = rf ? [pl, am, bm, dl, il, po, rf.layer, refl[0], refl[1], RG.back.layer, wr, ri, RG.front.layer, ha, sk] : [pl, am, bm, dl, il, po, refl[0], refl[1], RG.back.layer, wr, ri, RG.front.layer, ha, sk], k;
        if (RG.floor) { for (k = 0; k < order.length; k++) { if (order[k] === RG.back.layer) { order.splice(k, 0, RG.floor.layer); break; } } }
        for (k = 1; k < order.length; k++) { order[k].moveBefore(order[k - 1]); }
        en.moveToBeginning();
        R.comp = sc; R.rig = RG; for (k = order.length - 1; k >= 0; k--) { R.layers.push(order[k].name); }
        R.dust = du.pn;
        R.warnings = RG.front.warnings.concat(R.dust && R.dust.warnings ? R.dust.warnings : []);
        return R;
    }
    // camera(o, sceneComp): time remap frozen for the last o.hold frames, Motion Tile 112 % mirrored, push-in o.push to o.settle s, shake on
    // the ENV shake slider (o.shake px, 0.35 degrees). Returns the comp <name>_CAM.
    function camera(o, sc, sfx) {
        var c = comp(o, sfx || "_CAM", P.ink);
        var l = c.layers.add(sc); l.name = "SCENE";
        l.timeRemapEnabled = true;
        l.property("ADBE Time Remapping").expression = "Math.min(time," + ((o.dur * o.fps - o.hold) / o.fps) + ");";
        U.fx(l, "ADBE Tile", { "ADBE Tile-0004": 112, "ADBE Tile-0005": 112, "ADBE Tile-0006": 1 });
        tg(l, "ADBE Anchor Point").setValue(o.center); tg(l, "ADBE Position").setValue(o.center);
        var S = tg(l, "ADBE Scale");
        S.setValueAtTime(0, [o.push[0], o.push[0]]); S.setValueAtTime(o.settle, [o.push[1], o.push[1]]);
        AEK.motion.bezier(S, 1, 2, [0.35, 0, 0.15, 1]);
        tg(l, "ADBE Position").expression = "var e=" + E(o, "shake") + "*" + o.shake + "; value+[noise(time*15)*e, noise(time*15+40)*e*0.8];";
        tg(l, "ADBE Rotate Z").expression = "var e=" + E(o, "shake") + "; noise(time*12+80)*0.35*e;";
        return c;
    }
    // grainMatte(o, rig): where the effect covers the plate, as a luma matte through the same camera move: the rig sums in Screen,
    // Levels Input White grainWhite (light at that level or more takes full grain), blurred 12 px. Returns the comp <name>_GRAINCAM.
    function grainMatte(o, RG) {
        var c = comp(o, "_FXLUMA"), srcs = [RG.front.sum, RG.back.sum], i, l;
        if (RG.floor) { srcs.push(RG.floor.sum); }
        for (i = 0; i < srcs.length; i++) { l = c.layers.add(srcs[i]); l.blendingMode = BlendingMode.SCREEN; }
        var a = AEK.build.adjustment(c, "LEVEL");
        U.fx(a, "ADBE Easy Levels2", { "ADBE Easy Levels2-0004": o.grainWhite });
        U.fx(a, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 12, "ADBE Gaussian Blur 2-0003": 0 });
        return camera(o, c, "_GRAINCAM");
    }
    // finish(o, camComp, rig): the comp <name>_FINAL with AEX.lens.apply (CA, vignette, grain last; optics, halation and streak skipped).
    // Grain goes only where the picture lost it. grainMask "auto" (default): when nothing resamples the plate (no CA, push 100 to 100,
    // shake 0) it keeps its own grain, so grain goes only where the effect covers it (grainMatte as luma track matte). The lens CA and a
    // camera move resample the whole plate (its grain std fell 37 % with CA alone, 45 % with CA and the move, on hero3d.mp4), so grain
    // goes over the whole frame at grain x grainMove (0.82 put it at -0.5 %). "effect" or "frame" force one.
    // Returns {comp, lens}.
    function finish(o, cam, RG) {
        var c = comp(o, "_FINAL", P.ink), moving = o.ca > 0 || o.shake > 0 || o.push[0] !== 100 || o.push[1] !== 100;
        var mode = o.grainMask === "auto" ? (moving ? "frame" : "effect") : o.grainMask;
        var r = AEX.lens.apply(c, cam, { skip: { optics: 1, halation: 1, streak: 1 }, ca: o.ca, vignette: o.vignette, grain: mode === "frame" && o.grainMask === "auto" ? o.grain * o.grainMove : o.grain, grainSize: o.grainSize, mono: 0 });
        if (mode === "effect" && r.grain && RG) {
            var gm = c.layers.add(grainMatte(o, RG)); gm.name = "GRAIN MATTE"; gm.enabled = false;
            gm.moveBefore(r.grain); r.grain.setTrackMatte(gm, TrackMatteType.LUMA);
        }
        return { comp: c, lens: r };
    }
    // build(plateItem, o): the whole shot on a HELD frame: every origin, mask and ellipse sits at fixed comp pixels (a moving camera needs a
    // held frame or a rebuild per shot). o overrides DEFAULTS (nested ring1, ring2, floorRing, bloom, bloomBack merge key by key).
    // Returns {o, scene, cam, finalComp, layers, rig, dust, embers, warnings}: scene, cam and finalComp are comps (objects); layers and rig
    // are names. Compare layers and counts with the plan (a broken expression drops elements silently).
    function build(plate, opts) {
        var o = U.merge(DEFAULTS, opts), k;
        if (o.wave === "floor" && (!opts || opts.refract === undefined)) { o.refract = 0; }   // the refraction rides the screen circle
        if (o.hold === null || o.hold === undefined) { o.hold = plate.mainSource && plate.mainSource.isStill ? 15 : 0; }
        for (k in DEFAULTS) { if (DEFAULTS.hasOwnProperty(k) && DEFAULTS[k] !== null && typeof DEFAULTS[k] === "object" && !(DEFAULTS[k] instanceof Array) && opts && opts[k]) { o[k] = U.merge(DEFAULTS[k], opts[k]); } }
        var sc = scene(o, plate), cam = camera(o, sc.comp), fin = finish(o, cam, sc.rig), em = sc.rig.embers;
        var rn = [sc.rig.front.light.name, sc.rig.back.light.name]; if (sc.rig.floor) { rn.push(sc.rig.floor.light.name); }
        return { o: o, scene: sc.comp, cam: cam, finalComp: fin.comp, layers: sc.layers, rig: rn, dust: sc.dust,
            embers: em.pn || { count: em.count, sizes: em.sizes }, warnings: sc.warnings };
    }
    // gateFrames(r, dir, o): the frames the pixel gates read (scripts/vfx_measure.py gates <dir>/manifest.json), written by one job: the
    // plate alone (two consecutive frames and the calm frame), the scene comp and the subject matte at calm, peak and late times, the final
    // comp at the same times and on the last two frames. r is what build() returned. o = {calm (s, 0), peak (frames after the hit, [0, 2, 4, 6, 8, 10, 12, 15]),
    // late ([0.5, 1.5] s after the hit), prefix}. Returns the manifest (every path absolute).
    function gateFrames(r, dir, g) {
        g = g || {};
        var o = r.o, fps = o.fps, pre = g.prefix || "g", calm = g.calm === undefined ? 0 : g.calm, pk = g.peak || [0, 2, 4, 6, 8, 10, 12, 15], late = g.late || [0.5, 1.5], i, t;
        var mc = AEK.core.comp(o.name + "_PMATTE"), pc = comp(o, "_PLATEONLY"), pl = pc.layers.add(r.scene.layer("PLATE").source);
        fitCover(pl, pl.source, o);
        var M = { origin: o.center, at: o.at, fps: fps, scene: {}, matte: {}, outs: [], peaks: [], peakTimes: [] };
        var times = [calm], last = Math.floor(o.dur * fps) - 1;
        for (i = 0; i < pk.length; i++) { t = Math.round((o.at + pk[i] / fps) * 1000) / 1000; times.push(t); M.peakTimes.push(t); }
        for (i = 0; i < late.length; i++) { times.push(Math.round((o.at + late[i]) * 1000) / 1000); }
        for (i = 0; i < times.length; i++) {
            t = times[i];
            M.scene[String(t)] = AEK.capture.frame(r.scene, t, dir + "/" + pre + "_scene_" + Math.round(t * fps) + ".png").path;
            M.matte[String(t)] = AEK.capture.frame(mc, t, dir + "/" + pre + "_matte_" + Math.round(t * fps) + ".png").path;
            M.outs.push(AEK.capture.frame(r.finalComp, t, dir + "/" + pre + "_final_" + Math.round(t * fps) + ".png").path);
            if (i > 0 && i <= pk.length) { M.peaks.push(M.outs[i]); }
        }
        M.calm = M.outs[0]; M.calmScene = M.scene[String(calm)];
        M.hold = [AEK.capture.frame(r.finalComp, (last - 1) / fps, dir + "/" + pre + "_final_" + (last - 1) + ".png").path,
            AEK.capture.frame(r.finalComp, last / fps, dir + "/" + pre + "_final_" + last + ".png").path];
        M.plate = [AEK.capture.frame(pc, (last - 1) / fps, dir + "/" + pre + "_plate_" + (last - 1) + ".png").path,
            AEK.capture.frame(pc, last / fps, dir + "/" + pre + "_plate_" + last + ".png").path];
        M.plateFrame = AEK.capture.frame(pc, calm, dir + "/" + pre + "_plate_calm.png").path;
        var f = new File(dir + "/manifest.json"); f.encoding = "UTF-8"; f.open("w"); f.write(AEK.json.stringify(M)); f.close();
        M.manifest = f.fsName;
        return M;
    }
    return { DEFAULTS: DEFAULTS, build: build, env: env, productMatte: productMatte, cone: cone, density: density, falloff: falloff, dust: dust,
        rings: rings, floorRing: floorRing, floorWave: floorWave, floorMatte: floorMatte, subjectEllipse: subjectEllipse, streaks: streaks, embers: embers, embersPW: embersPW, emberLayer: emberLayer, rigs: rigs, wrapMatte: wrapMatte, rimMatte: rimMatte, chokeMatte: chokeMatte,
        interactiveComp: interactiveComp, scene: scene, camera: camera, finish: finish, gateFrames: gateFrames };
})();
