// rig.jsx: AEX.rig, native 2D cut-out rigging helpers (parent chains, pivots, two-bone IK, cycles, delays, face switches).
// Load with: ae.py run job.jsx --lib <skill>/scripts/rig.jsx . Requires the AEK kit (core, build, expr). ES3 only.
var AEX = AEX || {};
AEX.rig = (function () {
    function tg(l) { return l.property("ADBE Transform Group"); }
    function P(l) { return tg(l).property("ADBE Position"); }
    function R(l) { return tg(l).property("ADBE Rotate Z"); }
    function q(s) { return '"' + s + '"'; }

    // limb(comp, name, length, width, color, pivotInComp): capsule drawn from the pivot along +y.
    // Both ends are half circles centered on the joints, so a bend never shows a seam. Anchor stays [0,0] = the pivot.
    function limb(c, name, len, w, color, at) {
        var l = AEK.build.shape(c, name, { name: "art", type: "rect", size: [w, len + w], roundness: w / 2, position: [0, len / 2], fill: color });
        P(l).setValue(at);
        return l;
    }
    // part(comp, name, spec | [specs], pivotInComp): any shape drawn around its own pivot (anchor [0,0])
    function part(c, name, spec, at) {
        var l = AEK.build.shape(c, name, spec);
        P(l).setValue(at);
        return l;
    }
    // pivot(layer, [x, y] in comp): moves the anchor onto a comp point without moving the art. Unparented 2D layers only:
    // set pivots before parenting.
    function pivot(l, pt) {
        if (l.parent) { throw new Error("pivot(): unparent '" + l.name + "' first, or set pivots before parenting"); }
        var ap = tg(l).property("ADBE Anchor Point"), pp = P(l), sc = tg(l).property("ADBE Scale").value;
        if (ap.numKeys || pp.numKeys) { throw new Error("pivot(): '" + l.name + "' has Anchor Point or Position keys"); }
        var a0 = ap.value, p0 = pp.value, r = R(l).value * Math.PI / 180, dx = pt[0] - p0[0], dy = pt[1] - p0[1];
        var lx = (dx * Math.cos(r) + dy * Math.sin(r)) / (sc[0] / 100), ly = (-dx * Math.sin(r) + dy * Math.cos(r)) / (sc[1] / 100);
        ap.setValue([a0[0] + lx, a0[1] + ly]);
        pp.setValue([pt[0], pt[1]]);
        return { layer: l.name, anchor: ap.value, position: pp.value };
    }
    // chain([root, ..., tip]): parents each layer to the one before it, keeping it on screen. Returns "a > b > c".
    function chain(list) {
        var i, names = [list[0].name];
        for (i = 1; i < list.length; i++) { list[i].parent = list[i - 1]; names.push(list[i].name); }
        return names.join(" > ");
    }
    // world(comp, layer, pointInLayer | null, [seconds]): comp-space position of a layer point (null = its anchor) at each time.
    // Reads through a temporary probe null with a toComp() expression, so parenting and expressions are included.
    function world(c, l, pt, times) {
        var pr = c.layers.addNull(c.duration), p, out = [], i, v, err;
        try {
            pr.name = "__probe_" + l.id;
            p = P(pr);
            p.expression = "var L = thisComp.layer(" + q(l.name) + "); L.toComp(" + (pt ? "[" + pt[0] + "," + pt[1] + "]" : "L.transform.anchorPoint") + ");";
            for (i = 0; i < times.length; i++) { v = p.valueAtTime(times[i], false); out.push([v[0], v[1]]); }
            err = p.expressionError;
        } finally { pr.remove(); }
        if (err !== "") { throw new Error("world(): " + err); }
        return out;
    }
    function hasFx(l, name) { return !!l.property("ADBE Effect Parade").property(name); }
    // ik({upper, lower, tip, ctrl}): native two-bone IK by the law of cosines, written as expressions.
    // upper: Rotation (and Scale for stretch); lower: Rotation. Lengths are read from the rig (lower and tip positions), so
    // limbs can be drawn in any direction. Controls added on ctrl: checkbox "Flip" (bend side), checkbox "Stretch".
    // Stretch scales the upper layer's Y, so draw limbs along their layer's +y axis when stretch is used.
    // The solve runs in the upper layer's PARENT space: the target comes in through parent.fromComp(), so any parent
    // transform (scale uniform or not, a squash, rotation, nesting) keeps the tip on its controller. A non-uniform parent
    // scale still shears the limb art: squash the body art itself, not a limb parent (procedures 2c).
    function ik(o) {
        var ctrl = o.ctrl, defs = [];
        if (!hasFx(ctrl, "Flip")) { defs.push({ type: "checkbox", name: "Flip", value: 0 }); }
        if (!hasFx(ctrl, "Stretch")) { defs.push({ type: "checkbox", name: "Stretch", value: 0 }); }
        if (defs.length) { AEK.expr.controls(ctrl, defs); }
        var head = [
            "var c = thisComp.layer(" + q(ctrl.name) + "), up = thisComp.layer(" + q(o.upper.name) + "), lo = thisComp.layer(" + q(o.lower.name) + "), en = thisComp.layer(" + q(o.tip.name) + ");",
            "var e = lo.transform.position, f = en.transform.position, L1 = length(e), L2 = length(f);",
            "var S = up.transform.position, Tw = c.toComp(c.transform.anchorPoint);",
            "var T = up.hasParent ? up.parent.fromComp(Tw) : Tw, D = sub(T, S), d = length(D);",
            "var bend = c.effect(\"Flip\")(1).value ? -1 : 1;",
            "var k = (c.effect(\"Stretch\")(1).value && d > L1 + L2) ? d / (L1 + L2) : 1;",
            "var l1 = L1 * k, l2 = L2 * k, dd = Math.min(Math.max(d, Math.abs(l1 - l2) + 0.001), l1 + l2);",
            "var A = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd))));",
            "var B = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + l2 * l2 - dd * dd) / (2 * l1 * l2))));",
            "var r1 = Math.atan2(e[1], e[0]), r2 = Math.atan2(f[1], f[0]);"
        ].join("\n");
        var upRot = head + "\nradiansToDegrees(Math.atan2(D[1], D[0]) - bend * A - r1) + value;";
        var loRot = head + "\nradiansToDegrees(bend * (Math.PI - B) + r1 - r2) + value;";
        var upScale = head + "\n[value[0], value[1] * k];";
        var res = [];
        res.push(AEK.expr.set(R(o.upper), upRot));
        res.push(AEK.expr.set(R(o.lower), loRot));
        res.push(AEK.expr.set(tg(o.upper).property("ADBE Scale"), upScale));
        return res;
    }
    // orientTo(layer, ctrl): the layer keeps the controller's world angle whatever its parent does (planted foot, hand on a prop).
    function orientTo(l, ctrl) {
        var code = "var c = thisComp.layer(" + q(ctrl.name) + "), w = c.toCompVec([1, 0]), a = 0;\n" +
            "if (hasParent) { var v = parent.toCompVec([1, 0]); a = Math.atan2(v[1], v[0]); }\n" +
            "radiansToDegrees(Math.atan2(w[1], w[0]) - a) + value;";
        return AEK.expr.set(R(l), code);
    }
    // keys(prop, comp, [[frame, value, inEase, outEase], ...]): ease = 0 linear, "h" hold, a number = influence % with speed 0.
    function keys(p, c, list) {
        var i, k, it, ot, e;
        for (i = 0; i < list.length; i++) { p.setValueAtTime(list[i][0] * c.frameDuration, list[i][1]); }
        for (i = 0; i < list.length; i++) {
            k = p.nearestKeyIndex(list[i][0] * c.frameDuration);
            e = list[i];
            it = (e[2] === "h") ? KeyframeInterpolationType.HOLD : (e[2] ? KeyframeInterpolationType.BEZIER : KeyframeInterpolationType.LINEAR);
            ot = (e[3] === "h") ? KeyframeInterpolationType.HOLD : (e[3] ? KeyframeInterpolationType.BEZIER : KeyframeInterpolationType.LINEAR);
            p.setInterpolationTypeAtKey(k, it, ot);
            if (it === KeyframeInterpolationType.BEZIER || ot === KeyframeInterpolationType.BEZIER) {
                // Scale and other non-spatial multi-value properties take one ease per dimension (3 for Scale on a 2D layer)
                var vt = p.propertyValueType, dim = vt === PropertyValueType.TwoD ? 2 : (vt === PropertyValueType.ThreeD ? 3 : 1), ins = [], outs = [], d;
                for (d = 0; d < dim; d++) {
                    ins.push(new KeyframeEase(0, (typeof e[2] === "number" && e[2] > 0) ? e[2] : 33.33));
                    outs.push(new KeyframeEase(0, (typeof e[3] === "number" && e[3] > 0) ? e[3] : 33.33));
                }
                p.setTemporalEaseAtKey(k, ins, outs);
            }
        }
        return p.numKeys;
    }
    // loop(prop, mode): "out" = loopOut("cycle") only; "both" also loops BEFORE the first key, needed when the first key is
    // not on frame 0 (keys only on highs and lows); "continue" = travel.
    function loop(p, mode) {
        var code = mode === "both" ? 'time < key(1).time ? loopIn("cycle") : loopOut("cycle");'
            : (mode === "continue" ? 'loopOut("continue");' : 'loopOut("cycle");');
        return AEK.expr.set(p, code);
    }
    // drag(prop, driverLayer, frames, gain): follow-through on a child Rotation, the driver's rotation change over the last
    // n frames, times gain, added to the child's own value.
    function drag(p, driver, frames, gain) {
        var code = "var r = thisComp.layer(" + q(driver.name) + ").transform.rotation, n = " + frames + " * thisComp.frameDuration;\n" +
            "value + " + gain + " * (r.valueAtTime(time - n) - r);";
        return AEK.expr.set(p, code);
    }
    // echo(prop, srcLayerName, srcPropExpr, frames, gain, rest): a delayed copy of another layer's property (head after body).
    function echo(p, srcName, srcProp, frames, gain, rest) {
        var code = "var s = thisComp.layer(" + q(srcName) + ")." + srcProp + ", n = " + frames + " * thisComp.frameDuration;\n" +
            "value + " + gain + " * (s.valueAtTime(time - n) - " + rest + ");";
        return AEK.expr.set(p, code);
    }
    // swap(layers, ctrl, controlName): one layer visible per integer value of a slider on ctrl (mouth shapes, eye states, hands).
    function swap(layers, ctrl, name) {
        var i, out = [];
        for (i = 0; i < layers.length; i++) {
            out.push(AEK.expr.set(tg(layers[i]).property("ADBE Opacity"),
                "Math.round(thisComp.layer(" + q(ctrl.name) + ").effect(" + q(name) + ")(1)) == " + i + " ? 100 : 0;"));
        }
        return out;
    }
    // holdKeys(prop, comp, [[frame, value], ...]): stepped keys (mouth index, eye state, hand swap)
    function holdKeys(p, c, list) {
        var i, k;
        for (i = 0; i < list.length; i++) {
            p.setValueAtTime(list[i][0] * c.frameDuration, list[i][1]);
            k = p.nearestKeyIndex(list[i][0] * c.frameDuration);
            p.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
        }
        return p.numKeys;
    }

    // character(comp, o): a test character, side view facing +x, about 556 px from head to sole at scale 1.
    // o: {x, ground, legIK: true, scale: 1 (through CTRL_ROOT; 1.4 fills about 72 % of a 1080 px frame)}
    // Returns layer names. Draw order back to front: far arm, legs, torso, head, face, near arm, controllers.
    function character(c, o) {
        o = o || {};
        var x = o.x || 400, g = o.ground || 642, hipY = g - 240, sh = [x, g - 400], nk = [x, g - 415];
        var skin = [0.96, 0.78, 0.62], skinD = [0.82, 0.64, 0.5], shirt = [0.2, 0.45, 0.85], pants = [0.2, 0.22, 0.3], pantsD = [0.14, 0.15, 0.2], shoe = [0.85, 0.3, 0.2];
        var n = {}, L = {};
        L.ground = part(c, "ground", { name: "art", type: "rect", size: [c.width * 4, 6], position: [0, 0], fill: [0.35, 0.35, 0.38] }, [c.width / 2, g + 21]);
        L.Lua = limb(c, "L upper arm", 120, 32, [0.15, 0.34, 0.66], sh);
        L.Lfa = limb(c, "L forearm", 110, 28, skinD, [x, sh[1] + 120]);
        L.Lha = part(c, "L hand", { name: "art", type: "ellipse", size: [36, 40], position: [0, 14], fill: skinD }, [x, sh[1] + 230]);
        L.Lth = limb(c, "L thigh", 150, 44, pantsD, [x, hipY]);
        L.Lsh = limb(c, "L shin", 112, 38, pantsD, [x, hipY + 150]);
        L.Lft = part(c, "L foot", { name: "art", type: "rect", size: [84, 24], roundness: 10, position: [20, 9], fill: [0.6, 0.22, 0.15] }, [x, hipY + 262]);
        L.Rth = limb(c, "R thigh", 150, 44, pants, [x, hipY]);
        L.Rsh = limb(c, "R shin", 112, 38, pants, [x, hipY + 150]);
        L.Rft = part(c, "R foot", { name: "art", type: "rect", size: [84, 24], roundness: 10, position: [20, 9], fill: shoe }, [x, hipY + 262]);
        L.torso = part(c, "torso", { name: "art", type: "rect", size: [96, 200], roundness: 40, position: [0, -88], fill: shirt }, [x, hipY + 10]);
        L.head = part(c, "head", [{ name: "art", type: "ellipse", size: [120, 124], position: [6, -58], fill: skin }], nk);
        L.eo = part(c, "eyes open", { name: "art", type: "ellipse", size: [14, 20], position: [0, 0], fill: [0.1, 0.1, 0.12] }, [x + 34, nk[1] - 74]);
        L.ec = part(c, "eyes closed", { name: "art", type: "rect", size: [18, 4], roundness: 2, position: [0, 2], fill: [0.1, 0.1, 0.12] }, [x + 34, nk[1] - 74]);
        L.m0 = part(c, "mouth 0 closed", { name: "art", type: "rect", size: [26, 4], roundness: 2, position: [0, 0], fill: [0.45, 0.12, 0.12] }, [x + 36, nk[1] - 34]);
        L.m1 = part(c, "mouth 1 mid", { name: "art", type: "ellipse", size: [26, 12], position: [0, 0], fill: [0.45, 0.12, 0.12] }, [x + 36, nk[1] - 34]);
        L.m2 = part(c, "mouth 2 open", { name: "art", type: "ellipse", size: [28, 26], position: [0, 2], fill: [0.45, 0.12, 0.12] }, [x + 36, nk[1] - 34]);
        L.Rua = limb(c, "R upper arm", 120, 32, [0.28, 0.55, 0.95], sh);
        L.Rfa = limb(c, "R forearm", 110, 28, skin, [x, sh[1] + 120]);
        L.Rha = part(c, "R hand", { name: "art", type: "ellipse", size: [36, 40], position: [0, 14], fill: skin }, [x, sh[1] + 230]);
        L.root = AEK.build.nullLayer(c, "CTRL_ROOT", { position: [x, g] });
        L.body = AEK.build.nullLayer(c, "CTRL_BODY", { position: [x, hipY] });
        L.fR = AEK.build.nullLayer(c, "CTRL_FOOT_R", { position: [x, g] });
        L.fL = AEK.build.nullLayer(c, "CTRL_FOOT_L", { position: [x, g] });
        L.face = AEK.build.nullLayer(c, "CTRL_FACE", { position: [x + 120, nk[1] - 60] });
        AEK.expr.controls(L.face, [{ type: "slider", name: "Mouth", value: 0 }, { type: "slider", name: "Eyes", value: 0 }]);
        n.chains = [
            chain([L.root, L.body, L.torso, L.head]), chain([L.root, L.fR]), chain([L.root, L.fL]), chain([L.face]),
            chain([L.torso, L.Rua, L.Rfa, L.Rha]), chain([L.torso, L.Lua, L.Lfa, L.Lha]),
            chain([L.body, L.Rth, L.Rsh, L.Rft]), chain([L.body, L.Lth, L.Lsh, L.Lft])
        ];
        var faceParts = [L.eo, L.ec, L.m0, L.m1, L.m2], i;
        for (i = 0; i < faceParts.length; i++) { faceParts[i].parent = L.head; }
        L.face.parent = L.head;
        swap([L.m0, L.m1, L.m2], L.face, "Mouth");
        swap([L.eo, L.ec], L.face, "Eyes");
        if (o.legIK !== false) {
            ik({ upper: L.Rth, lower: L.Rsh, tip: L.Rft, ctrl: L.fR });
            ik({ upper: L.Lth, lower: L.Lsh, tip: L.Lft, ctrl: L.fL });
            orientTo(L.Rft, L.fR);
            orientTo(L.Lft, L.fL);
        }
        // o.scale: the whole figure through CTRL_ROOT (IK is scale-safe); the ground line moves to the scaled sole
        if (o.scale && o.scale !== 1) {
            tg(L.root).property("ADBE Scale").setValue([100 * o.scale, 100 * o.scale]);
            P(L.ground).setValue([c.width / 2, g + 21 * o.scale]);
        }
        n.layers = {};
        for (i in L) { if (Object.prototype.hasOwnProperty.call(L, i)) { n.layers[i] = L[i].name; } }
        n.L = L;
        return n;
    }

    // zero(ctrl, root): puts the controller under a "ZERO_" null at its rest pose, so its Position reads [0, 0] and its
    // Rotation keeps its own value. The null goes under the controller's current parent, or under root when it has none.
    // Run it before the controller is keyed.
    function zero(l, root) {
        var c = l.containingComp, par = l.parent, p0 = P(l).value;
        var z = AEK.build.nullLayer(c, "ZERO_" + l.name, {});
        tg(z).property("ADBE Anchor Point").setValue([0, 0]);
        if (par) { z.parent = par; }
        P(z).setValue(par ? [p0[0], p0[1]] : [p0[0], p0[1]]);
        R(z).setValue(0);
        tg(z).property("ADBE Scale").setValue([100, 100]);
        if (!par && root) { z.parent = root; }
        z.moveAfter(l);
        l.parent = z;
        return { zero: z.name, parent: z.parent ? z.parent.name : null, position: P(l).value };
    }
    // cycleCode(N, stopFrame): the looped value, keys repeating every N frames before AND after the first key
    // (k + ((t - k) mod T)), then, from stopFrame on, the property's own keys (the stop). stopFrame null = loop forever.
    function cycleCode(N, S) {
        return "var fd = thisComp.frameDuration, k1 = key(1).time, T = " + N + " * fd;\n" +
            "var cyc = " + (S ? "time >= " + S + " * fd - fd / 2 ? value : " : "") + "valueAtTime(k1 + ((((time - k1) % T) + T) % T));\n";
    }
    // footRoll(ctrl, foot, N, S): controller X or Y keeps its cycle and adds the roll offset that pins the sole corner
    // (toe while the heel is up, heel while the toe is up) where the flat foot put it. Corners from the foot's own bounds.
    function rollCode(foot, axis) {
        var r = foot.sourceRectAtTime(0, false), heel = r.left, toe = r.left + r.width, sole = r.top + r.height;
        return "var a = degreesToRadians(transform.rotation), cx = a > 0 ? " + toe + " : " + heel + ", cy = " + sole + ";\n" +
            (axis === 0 ? "cyc + (cx - (cx * Math.cos(a) - cy * Math.sin(a)));" : "cyc + (cy - (cx * Math.sin(a) + cy * Math.cos(a)));");
    }
    // stopKey(prop, comp, N, S): key at S with the cycle's value and speed at that phase, so the stop leaves the cycle smoothly
    function stopKey(p, c, N, S) {
        var fd = c.frameDuration, k1 = p.keyTime(1), T = N * fd, ph = function (t) { return k1 + ((((t - k1) % T) + T) % T); };
        var t = S * fd, v = p.valueAtTime(ph(t), true), sp = (p.valueAtTime(ph(t + fd), true) - p.valueAtTime(ph(t - fd), true)) / (2 * fd);
        p.setValueAtTime(t, v);
        var k = p.nearestKeyIndex(t);
        p.setInterpolationTypeAtKey(k, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
        p.setTemporalEaseAtKey(k, [new KeyframeEase(sp, 33.333)], [new KeyframeEase(sp, 33.333)]);
        return v;
    }

    // walk(comp, ch, o): contact, down, passing, up on the controllers. Right contact on frame 0, left contact on cycle/2.
    // o: {cycle: 24 (frames per two steps), leg (px, hip to ankle when straight; defaults scale from it), stride, lift, bob,
    //     swing: 22 (deg), tilt: 2 (deg, torso, keyed 1 frame before the hips), lean: 4 (deg), travel: true,
    //     roll: true (foot roll on the controllers), stopAt: null (frame, a multiple of cycle after the last cycle key)}.
    // Defaults without o.leg are the 262 px reference leg: stride 200, lift 50, bob 14.
    function walk(c, ch, o) {
        o = o || {};
        var L = ch.L, out = {}, fd = c.frameDuration;
        var leg = o.leg || 262, k = leg / 262;
        var N = o.cycle || 24, h = N / 2, s = (o.stride || 200 * k) / 2, lift = o.lift || 50 * k, bob = o.bob || 14 * k, sw = o.swing || 22;
        var tilt = (o.tilt === undefined) ? 2 : o.tilt, lean = (o.lean === undefined) ? 4 : o.lean, S = o.stopAt || null, roll = o.roll !== false;
        if (S && (S % N !== 0 || S < N + Math.round(3 * N / 24) + 1)) { throw new Error("walk(): stopAt must be a multiple of the cycle after frame " + (N + Math.round(3 * N / 24))); }
        function f(x) { return Math.round(x * N / 24); }
        function sep(l) { var p = P(l); p.dimensionsSeparated = true; return [p.getSeparationFollower(0), p.getSeparationFollower(1)]; }
        function cyc(p, tail) { return AEK.expr.set(p, cycleCode(N, S) + (tail || "cyc;")); }
        // rest geometry before any key: hip height over the ankle and the leg length, in CTRL_ROOT units
        var legPx = length2(P(L.Rsh).value) + length2(P(L.Rft).value);
        var sc = length2(sub2(world(c, L.root, [1, 0], [0])[0], world(c, L.root, [0, 0], [0])[0]));
        var H0 = (world(c, L.fR, null, [0])[0][1] - world(c, L.body, null, [0])[0][1]) / sc;
        var rise = Math.max(0, 0.97 * legPx - H0);
        var rx = sep(L.fR), lx = sep(L.fL), by = sep(L.body);
        // feet X linear: the planted foot slides back at exactly the travel speed (stride / step frames)
        keys(rx[0], c, [[0, s, 0, 0], [h, -s, 0, 0], [N, s, 0, 0]]);
        keys(lx[0], c, [[0, -s, 0, 0], [h, s, 0, 0], [N, -s, 0, 0]]);
        // feet Y: flat while planted, ease out of the ground, hang at the top, fall without ease in
        keys(rx[1], c, [[0, 0, 0, 0], [h, 0, 0, 60], [h + f(6), -lift, 50, 50], [N, 0, 0, 0]]);
        keys(lx[1], c, [[0, 0, 0, 60], [f(6), -lift, 50, 50], [h, 0, 0, 0], [N, 0, 0, 0]]);
        // foot angle: heel strike toe up, flat, heel off before lift
        keys(R(L.fR), c, [[0, -10, 0, 0], [f(3), 0, 40, 40], [f(9), 0, 40, 0], [h, 18, 0, 0], [h + f(6), 0, 40, 40], [N, -10, 0, 0]]);
        keys(R(L.fL), c, [[0, 18, 0, 0], [f(6), 0, 40, 40], [h, -10, 0, 0], [h + f(3), 0, 40, 40], [h + f(9), 0, 40, 0], [N, 18, 0, 0]]);
        // hips: keys only on lows (down) and highs (up), so the first key is NOT on frame 0
        var y0 = by[1].value;
        keys(by[1], c, [[f(3), y0 + bob, 50, 50], [f(9), y0 - bob, 50, 50], [h + f(3), y0 + bob, 50, 50], [h + f(9), y0 - bob, 50, 50], [N + f(3), y0 + bob, 50, 50]]);
        // torso: forward lean, more on the down, keyed 1 frame before the hips (School of Motion walk)
        keys(R(L.torso), c, [[f(3) - 1, lean + tilt, 50, 50], [f(9) - 1, lean - tilt, 50, 50], [h + f(3) - 1, lean + tilt, 50, 50], [h + f(9) - 1, lean - tilt, 50, 50], [N + f(3) - 1, lean + tilt, 50, 50]]);
        // arms FK, opposite to the legs, widest on the down pose
        keys(R(L.Rua), c, [[f(3), sw, 50, 50], [h + f(3), -sw, 50, 50], [N + f(3), sw, 50, 50]]);
        keys(R(L.Lua), c, [[f(3), -sw, 50, 50], [h + f(3), sw, 50, 50], [N + f(3), -sw, 50, 50]]);
        var gx = null;
        if (o.travel !== false) { gx = sep(L.root); }
        if (S) {
            // the stop: right foot planted at S, left foot steps beside it in one step (h frames), the body decelerates
            // at a constant rate from the walk speed to 0 over the same step, then the hips, torso and arms settle
            var v0 = 2 * s / h / fd, i, bodyKeys = [by[1], R(L.torso), R(L.Rua), R(L.Lua)];
            for (i = 0; i < bodyKeys.length; i++) { stopKey(bodyKeys[i], c, N, S); }
            var e = function (p, list) { var j; for (j = 0; j < list.length; j++) { keys(p, c, [list[j]]); } };
            rx[0].setValueAtTime(S * fd, s); rx[0].setValueAtTime((S + h) * fd, 0);
            var kr = rx[0].nearestKeyIndex(S * fd);
            rx[0].setInterpolationTypeAtKey(kr, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.BEZIER);
            rx[0].setTemporalEaseAtKey(kr, [new KeyframeEase(-v0, 33.333)], [new KeyframeEase(-v0, 33.333)]);
            rx[0].setTemporalEaseAtKey(kr + 1, [new KeyframeEase(0, 33.333)], [new KeyframeEase(0, 33.333)]);
            e(rx[1], [[S, 0, 0, "h"]]);
            e(R(L.fR), [[S, -10, 0, 40], [S + f(3), 0, 40, 40]]);
            e(lx[0], [[S, -s, 0, 50], [S + h, 0, 60, 0]]);
            e(lx[1], [[S, 0, 0, 60], [S + f(6), -lift * 0.7, 50, 50], [S + h, 0, 0, "h"]]);
            e(R(L.fL), [[S, 18, 0, 0], [S + f(6), 0, 40, 40]]);
            // standing: the hips rise until the legs reach 97 % of their length, with a small overshoot
            e(by[1], [[S + f(3), y0 + bob, 50, 50], [S + h, y0 - rise - 0.3 * bob, 50, 50], [S + h + f(6), y0 - rise, 50, 50]]);
            e(R(L.torso), [[S + f(3) - 1, lean + tilt, 50, 50], [S + h, lean - 0.5 * tilt, 50, 50], [S + h + f(6), lean, 50, 50]]);
            e(R(L.Rua), [[S + f(3), 0.6 * sw, 50, 50], [S + h, -0.2 * sw, 50, 50], [S + h + f(5), 0.08 * sw, 50, 50], [S + h + f(10), 0, 50, 50]]);
            e(R(L.Lua), [[S + f(3), -0.6 * sw, 50, 50], [S + h, 0.2 * sw, 50, 50], [S + h + f(5), -0.08 * sw, 50, 50], [S + h + f(10), 0, 50, 50]]);
            if (gx) {
                var x0 = gx[0].value, xs = x0 + 4 * s * sc * S / N;
                keys(gx[0], c, [[0, x0, 0, 0], [S, xs, 0, 0]]);
                gx[0].setValueAtTime((S + h) * fd, xs + s * sc);
                var kg = gx[0].nearestKeyIndex(S * fd);
                gx[0].setInterpolationTypeAtKey(kg, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.BEZIER);
                gx[0].setTemporalEaseAtKey(kg, [new KeyframeEase(v0 * sc, 33.333)], [new KeyframeEase(v0 * sc, 33.333)]);
                gx[0].setTemporalEaseAtKey(kg + 1, [new KeyframeEase(0, 33.333)], [new KeyframeEase(0, 33.333)]);
            }
            out.stop = { start: S, planted: S + h, settled: S + h + f(10), travelAfterStop: s * sc };
        } else if (gx) {
            keys(gx[0], c, [[0, gx[0].value, 0, 0], [N, gx[0].value + 4 * s * sc, 0, 0]]);
            loop(gx[0], "continue");
        }
        // loops: every cycled property repeats its keys before the first key and after the last, until the stop
        cyc(rx[0], roll ? rollCode(L.Rft, 0) : null); cyc(rx[1], roll ? rollCode(L.Rft, 1) : null);
        cyc(lx[0], roll ? rollCode(L.Lft, 0) : null); cyc(lx[1], roll ? rollCode(L.Lft, 1) : null);
        cyc(R(L.fR)); cyc(R(L.fL)); cyc(by[1]); cyc(R(L.torso)); cyc(R(L.Rua)); cyc(R(L.Lua));
        // overlap: forearms drag 2 frames behind the upper arm, the head nods 2 frames after the hips
        R(L.Rfa).setValue(-12); R(L.Lfa).setValue(-12);
        drag(R(L.Rfa), L.Rua, 2, 0.6);
        drag(R(L.Lfa), L.Lua, 2, 0.6);
        echo(R(L.head), L.body.name, "transform.yPosition", 2, 0.25, y0);
        // reach: hip-to-ankle distance at contact over the leg length (straight leg = 1)
        out.reachContact = Math.round(Math.sqrt(H0 * H0 + s * s) / legPx * 1000) / 1000;
        out.hipOverAnkle = Math.round(H0 / legPx * 1000) / 1000;
        if (S) { out.stop.standRise = Math.round(rise * 10) / 10; }
        out.cycle = N; out.step = h; out.strideX = 2 * s; out.speedPxPerFrame = 2 * s * sc / h; out.rootScale = sc; out.lift = lift; out.bob = bob; out.leg = legPx;
        return out;
    }
    function length2(v) { return Math.sqrt(v[0] * v[0] + v[1] * v[1]); }
    function sub2(a, b) { return [a[0] - b[0], a[1] - b[1]]; }

    // hang(prop, o): a hanging prop (bag, speaker, keys) swings from its pivot's motion: a damped pendulum driven by the
    // pivot's horizontal acceleration over the last `window` frames, minus the parent's world angle so it hangs straight.
    // The prop's anchor must sit on the hanging point and the layer must have a parent. o: {length: px from the pivot to
    // the prop's center, pxPerMeter: character scale (height in px / height in m), damping: 0.3, window: 48 (frames), gain: 1,
    // rest: 0 (degrees from straight down)}. Parenting wrote the parent's angle into the prop's Rotation: hang() resets it to rest.
    function hang(l, o) {
        o = o || {};
        if (!l.parent) { throw new Error("hang(): parent '" + l.name + "' to the body or the bag strap first"); }
        R(l).setValue(o.rest || 0);
        var code = "const Lp = " + (o.length || 60) + ", ppm = " + (o.pxPerMeter || 350) + ", z = " + (o.damping || 0.3) + ", W = " + (o.window || 48) + ", gain = " + (o.gain || 1) + ";\n" +
            "const fd = thisComp.frameDuration, g = 9.81 * ppm * fd * fd, w = Math.sqrt(g / Lp), wd = w * Math.sqrt(1 - z * z);\n" +
            "const pos = transform.position, x = [];\n" +
            "for (let k = 0; k <= W + 1; k++) { const t = time - k * fd; x.push(parent.toComp(pos.valueAtTime(t), t)[0]); }\n" +
            "let th = 0;\n" +
            "for (let k = 1; k <= W; k++) { th += (x[k - 1] - 2 * x[k] + x[k + 1]) * Math.exp(-z * w * k) * Math.sin(wd * k) / wd; }\n" +
            "const v = sub(parent.toComp([1, 0]), parent.toComp([0, 0]));\n" +
            "value + radiansToDegrees(gain * th / Lp - Math.atan2(v[1], v[0]));";
        return AEK.expr.set(R(l), code);
    }

    // bounds(comp, t, skip): comp-space box around every visible shape or footage layer at time t (corners of
    // sourceRectAtTime through toComp), skipping guide layers, nulls, unparented layers that cover the whole frame, and
    // names that start with an entry of skip (default CTRL_, ZERO_, ground, BG, shadow). Returns {left, top, right, bottom, height, heightPct of the comp}.
    function bounds(c, t, skip) {
        skip = skip || ["CTRL_", "ZERO_", "ground", "BG", "shadow"];
        var b = { left: 1e9, top: 1e9, right: -1e9, bottom: -1e9 }, i, j, l, r, pts, ok;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i); ok = l.enabled && !l.guideLayer && !l.nullLayer && (l instanceof ShapeLayer || l instanceof AVLayer);
            for (j = 0; ok && j < skip.length; j++) { if (l.name.indexOf(skip[j]) === 0) { ok = false; } }
            if (!ok || (l.property("ADBE Transform Group").property("ADBE Opacity").valueAtTime(t, false) === 0)) { continue; }
            r = l.sourceRectAtTime(t, false);
            // a layer that covers the whole frame (background solid or plate) is not the figure
            if (!l.parent && r.width * Math.abs(tg(l).property("ADBE Scale").valueAtTime(t, false)[0]) / 100 >= c.width &&
                r.height * Math.abs(tg(l).property("ADBE Scale").valueAtTime(t, false)[1]) / 100 >= c.height) { continue; }
            pts = [[r.left, r.top], [r.left + r.width, r.top], [r.left, r.top + r.height], [r.left + r.width, r.top + r.height]];
            for (j = 0; j < pts.length; j++) {
                var w = world(c, l, pts[j], [t])[0];
                b.left = Math.min(b.left, w[0]); b.right = Math.max(b.right, w[0]); b.top = Math.min(b.top, w[1]); b.bottom = Math.max(b.bottom, w[1]);
            }
        }
        b.height = Math.round(b.bottom - b.top); b.heightPct = Math.round(1000 * b.height / c.height) / 10;
        return b;
    }

    // limit(prop, ctrl, min, max): a joint limit as named controls. Adds "<layer> Min" and "<layer> Max" sliders on ctrl
    // (degrees for Rotation) and clamps the property's keyed or static value into that range (no expression on it yet).
    function limit(p, ctrl, min, max) {
        var l = p.propertyGroup(p.propertyDepth), n = l.name, defs = [];
        if (!hasFx(ctrl, n + " Min")) { defs.push({ type: "slider", name: n + " Min", value: min }); }
        if (!hasFx(ctrl, n + " Max")) { defs.push({ type: "slider", name: n + " Max", value: max }); }
        if (defs.length) { AEK.expr.controls(ctrl, defs); }
        if (p.expression !== "") { throw new Error("limit(): '" + n + "' already has an expression: end it with clamp(result, min, max) instead"); }
        return AEK.expr.set(p, "var v0 = value;\nvar c = thisComp.layer(" + q(ctrl.name) + ");\nclamp(v0, c.effect(" + q(n + " Min") + ")(1), c.effect(" + q(n + " Max") + ")(1));");
    }
    // attach(layer, target, pointInTarget): the layer's Position follows a point of the target layer (its art space),
    // through toComp and the layer's own parent fromComp. A shoulder attached to a squashing body rides the squash and
    // rotation without inheriting the non-uniform scale, so the arm keeps its shape.
    function attach(l, target, pt) {
        return AEK.expr.set(P(l), "var p = thisComp.layer(" + q(target.name) + ").toComp([" + pt[0] + ", " + pt[1] + "]);\nhasParent ? parent.fromComp(p) : p;");
    }
    // squash(art, driver, o): squash and stretch of a body's ART layer (a layer with no children) from the driver's vertical
    // motion, volume kept (X = 10000 / Y). Stretch grows with speed, squash with the upward push at a landing (acceleration).
    // The art's anchor must sit on its base (feet or bottom). o: {stretch: 0.6 (% per px/frame), squash: 1.2 (% per
    // px/frame^2), max: 12 (% either way), axis: 1}. Never squash a limb parent: its children shear (check() reports it).
    function squash(art, driver, o) {
        o = o || {};
        var code = "var d = thisComp.layer(" + q(driver.name) + "), fd = thisComp.frameDuration;\n" +
            "function y(t) { return d.toComp(d.transform.anchorPoint, t)[1]; }\n" +
            "var v = (y(time + fd) - y(time - fd)) / 2, a = y(time + fd) - 2 * y(time) + y(time - fd);\n" +
            "var s = " + (o.stretch || 0.6) + " * Math.abs(v) - " + (o.squash || 1.2) + " * Math.max(0, -a);\n" +
            "s = clamp(s, -" + (o.max || 12) + ", " + (o.max || 12) + ");\n" +
            "var sy = 100 + s, sx = 10000 / sy;\n[value[0] * sx / 100, value[1] * sy / 100];";
        return AEK.expr.set(tg(art).property("ADBE Scale"), code);
    }
    // blink(prop, comp, frames, o): blinks on an eye layer's Scale (2D) as hold keys, one frame each: close over 2 frames,
    // closed for o.hold (2) frames, open over 2 frames. o: {closed: 8 (% Y when shut), x: 100}. A blink then lasts 6 frames
    // and reads on a contact sheet; a 1-frame blink is lost at 24 fps. frames: start frames, 1.25 s or more apart.
    function blink(p, c, frames, o) {
        o = o || {};
        var h = o.hold || 2, cl = o.closed === undefined ? 8 : o.closed, x = o.x || 100, list = [], i, k, seq;
        for (i = 0; i < frames.length; i++) {
            seq = [100, 45, cl];
            for (k = 1; k < h; k++) { seq.push(cl); }
            seq.push(50); seq.push(100);
            for (k = 0; k < seq.length; k++) { list.push([frames[i] + k, [x, seq[k]]]); }
        }
        return holdKeys(p, c, list);
    }

    // check(comp, {ik: [[tip, ctrl], ...], limbs: [names], times: [seconds]}): the rig rubric in numbers.
    // ikError: largest distance, comp px, between each tip's pivot and its controller over the times (the controller must sit
    // inside the reach; out of reach the tip stops short by design). shear: every limb ancestor whose Scale X and Y differ by
    // more than 0.5 % at a sampled time: the IK still lands, but the limb art is sheared, so squash the body art instead.
    // restOff: CTRL_ layers under a ZERO_ null whose Position is not [0, 0] at time 0. dupNames: names used twice.
    // ok = no duplicate, ikError under 0.01 px, no shear, every controller at rest.
    function check(c, o) {
        o = o || {};
        var t = o.times || [0, c.duration / 2, c.duration - c.frameDuration], out = { dupNames: [], ikError: [], shear: [], restOff: [] }, seen = {}, i, j, k, l;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (seen[l.name]) { out.dupNames.push(l.name); } seen[l.name] = true;
            if (l.name.indexOf("CTRL_") === 0 && l.parent && l.parent.name.indexOf("ZERO_") === 0) {
                var p0 = P(l).valueAtTime(0, false);
                if (Math.abs(p0[0]) + Math.abs(p0[1]) > 1e-6) { out.restOff.push(l.name); }
            }
        }
        var pairs = o.ik || [], maxErr = 0;
        for (i = 0; i < pairs.length; i++) {
            var a = world(c, c.layer(pairs[i][0]), null, t), b = world(c, c.layer(pairs[i][1]), null, t), e = 0;
            for (j = 0; j < t.length; j++) { e = Math.max(e, length2(sub2(a[j], b[j]))); }
            out.ikError.push({ tip: pairs[i][0], px: Math.round(e * 1000) / 1000 }); maxErr = Math.max(maxErr, e);
        }
        var limbs = o.limbs || [], flagged = {};
        for (i = 0; i < limbs.length; i++) {
            for (l = c.layer(limbs[i]).parent; l; l = l.parent) {
                if (flagged[l.name]) { continue; }
                for (k = 0; k < t.length; k++) {
                    var sc = tg(l).property("ADBE Scale").valueAtTime(t[k], false);
                    if (Math.abs(sc[0] - sc[1]) > 0.005 * Math.max(Math.abs(sc[0]), Math.abs(sc[1]), 1)) {
                        out.shear.push({ layer: l.name, under: limbs[i], scale: [Math.round(sc[0] * 100) / 100, Math.round(sc[1] * 100) / 100], at: t[k] });
                        flagged[l.name] = true; break;
                    }
                }
            }
        }
        out.maxIkError = Math.round(maxErr * 1000) / 1000;
        out.ok = !out.dupNames.length && maxErr < 0.01 && !out.shear.length && !out.restOff.length;
        return out;
    }

    return { check: check, attach: attach, limit: limit, squash: squash, blink: blink, bounds: bounds, limb: limb, part: part, pivot: pivot, chain: chain, world: world, ik: ik, orientTo: orientTo, keys: keys, loop: loop,
        drag: drag, echo: echo, swap: swap, holdKeys: holdKeys, character: character, walk: walk, zero: zero, hang: hang, cycleCode: cycleCode };
})();
