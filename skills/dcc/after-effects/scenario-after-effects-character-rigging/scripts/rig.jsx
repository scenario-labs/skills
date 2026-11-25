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
        var pr = c.layers.addNull(c.duration), p, out = [], i, v;
        pr.name = "__probe_" + l.id;
        p = P(pr);
        p.expression = "var L = thisComp.layer(" + q(l.name) + "); L.toComp(" + (pt ? "[" + pt[0] + "," + pt[1] + "]" : "L.transform.anchorPoint") + ");";
        for (i = 0; i < times.length; i++) { v = p.valueAtTime(times[i], false); out.push([v[0], v[1]]); }
        var err = p.expressionError;
        pr.remove();
        if (err !== "") { throw new Error("world(): " + err); }
        return out;
    }
    function hasFx(l, name) { return !!l.property("ADBE Effect Parade").property(name); }
    // ik({upper, lower, tip, ctrl}): native two-bone IK by the law of cosines, written as expressions.
    // upper: Rotation (and Scale for stretch); lower: Rotation. Lengths are read from the rig (lower and tip positions), so
    // limbs can be drawn in any direction. Controls added on ctrl: checkbox "Flip" (bend side), checkbox "Stretch".
    // Stretch scales the upper layer's Y, so draw limbs along their layer's +y axis when stretch is used.
    function ik(o) {
        var ctrl = o.ctrl, defs = [];
        if (!hasFx(ctrl, "Flip")) { defs.push({ type: "checkbox", name: "Flip", value: 0 }); }
        if (!hasFx(ctrl, "Stretch")) { defs.push({ type: "checkbox", name: "Stretch", value: 0 }); }
        if (defs.length) { AEK.expr.controls(ctrl, defs); }
        var head = [
            "var c = thisComp.layer(" + q(ctrl.name) + "), up = thisComp.layer(" + q(o.upper.name) + "), lo = thisComp.layer(" + q(o.lower.name) + "), en = thisComp.layer(" + q(o.tip.name) + ");",
            "var e = lo.transform.position, f = en.transform.position, L1 = length(e), L2 = length(f);",
            "var S = up.hasParent ? up.parent.toComp(up.transform.position) : up.transform.position;",
            "var T = c.toComp(c.transform.anchorPoint), D = sub(T, S), d = length(D);",
            "var bend = c.effect(\"Flip\")(1).value ? -1 : 1;",
            "var k = (c.effect(\"Stretch\")(1).value && d > L1 + L2) ? d / (L1 + L2) : 1;",
            "var l1 = L1 * k, l2 = L2 * k, dd = Math.min(Math.max(d, Math.abs(l1 - l2) + 0.001), l1 + l2);",
            "var A = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd))));",
            "var B = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + l2 * l2 - dd * dd) / (2 * l1 * l2))));",
            "var r1 = Math.atan2(e[1], e[0]), r2 = Math.atan2(f[1], f[0]);"
        ].join("\n");
        var upRot = head + "\nvar pr = 0;\nif (up.hasParent) { var v = up.parent.toCompVec([1, 0]); pr = Math.atan2(v[1], v[0]); }\n" +
            "radiansToDegrees(Math.atan2(D[1], D[0]) - bend * A - r1 - pr) + value;";
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
        var i, k, it, ot, e, inE, outE;
        for (i = 0; i < list.length; i++) { p.setValueAtTime(list[i][0] * c.frameDuration, list[i][1]); }
        for (i = 0; i < list.length; i++) {
            k = p.nearestKeyIndex(list[i][0] * c.frameDuration);
            e = list[i];
            it = (e[2] === "h") ? KeyframeInterpolationType.HOLD : (e[2] ? KeyframeInterpolationType.BEZIER : KeyframeInterpolationType.LINEAR);
            ot = (e[3] === "h") ? KeyframeInterpolationType.HOLD : (e[3] ? KeyframeInterpolationType.BEZIER : KeyframeInterpolationType.LINEAR);
            p.setInterpolationTypeAtKey(k, it, ot);
            if (it === KeyframeInterpolationType.BEZIER || ot === KeyframeInterpolationType.BEZIER) {
                inE = new KeyframeEase(0, (typeof e[2] === "number" && e[2] > 0) ? e[2] : 33.33);
                outE = new KeyframeEase(0, (typeof e[3] === "number" && e[3] > 0) ? e[3] : 33.33);
                p.setTemporalEaseAtKey(k, [inE], [outE]);
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

    // character(comp, o): a test character, side view facing +x. o: {x, ground, legIK: true}
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
        n.layers = {};
        for (i in L) { if (L.hasOwnProperty(i)) { n.layers[i] = L[i].name; } }
        n.L = L;
        return n;
    }

    // walk(comp, ch, o): contact, down, passing, up on the controllers. o: {cycle: 24 (frames per two steps), stride: 200 (px),
    // lift: 50, bob: 14, swing: 22, travel: true, bodyLoop: "both"}. Right contact on frame 0, left contact on cycle/2.
    function walk(c, ch, o) {
        o = o || {};
        var N = o.cycle || 24, h = N / 2, s = (o.stride || 200) / 2, lift = o.lift || 50, bob = o.bob || 14, sw = o.swing || 22;
        var L = ch.L, out = {};
        function f(x) { return Math.round(x * N / 24); }
        function sep(l) { var p = P(l); p.dimensionsSeparated = true; return [p.getSeparationFollower(0), p.getSeparationFollower(1)]; }
        var rx = sep(L.fR), lx = sep(L.fL), by = sep(L.body), rot;
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
        // arms FK, opposite to the legs, widest on the down pose
        keys(R(L.Rua), c, [[f(3), sw, 50, 50], [h + f(3), -sw, 50, 50], [N + f(3), sw, 50, 50]]);
        keys(R(L.Lua), c, [[f(3), -sw, 50, 50], [h + f(3), sw, 50, 50], [N + f(3), -sw, 50, 50]]);
        R(L.torso).setValue(4);
        var lp = [rx[0], rx[1], lx[0], lx[1], R(L.fR), R(L.fL)];
        for (rot = 0; rot < lp.length; rot++) { loop(lp[rot], "out"); }
        loop(by[1], o.bodyLoop || "both");
        loop(R(L.Rua), o.bodyLoop || "both");
        loop(R(L.Lua), o.bodyLoop || "both");
        // overlap: forearms drag 2 frames behind the upper arm, the head nods 2 frames after the hips
        R(L.Rfa).setValue(-12); R(L.Lfa).setValue(-12);
        drag(R(L.Rfa), L.Rua, 2, 0.6);
        drag(R(L.Lfa), L.Lua, 2, 0.6);
        echo(R(L.head), L.body.name, "transform.yPosition", 2, 0.25, y0);
        if (o.travel !== false) {
            var gx = sep(L.root);
            keys(gx[0], c, [[0, gx[0].value, 0, 0], [N, gx[0].value + 4 * s, 0, 0]]);
            loop(gx[0], "continue");
        }
        out.cycle = N; out.step = h; out.strideX = 2 * s; out.speedPxPerFrame = 2 * s / h;
        return out;
    }

    return { limb: limb, part: part, pivot: pivot, chain: chain, world: world, ik: ik, orientTo: orientTo, keys: keys, loop: loop,
        drag: drag, echo: echo, swap: swap, holdKeys: holdKeys, character: character, walk: walk };
})();
