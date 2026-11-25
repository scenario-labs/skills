// animation.jsx: AEX.animation, keyframe and easing helpers for the scenario-after-effects-animation skill.
// Requires the AEK kit (core, motion). Load with: ae.py run job.jsx --lib <skill>/scripts/animation.jsx
var AEX = AEX || {};
AEX.animation = (function () {
    // Named eases as CSS cubic-bezier tuples [x1, y1, x2, y2]. Measured numbers are in references/procedures.md.
    var EASES = {
        linear: [0, 0, 1, 1],
        css_ease: [0.25, 0.1, 0.25, 1],
        out_cubic: [0.33, 1, 0.68, 1],
        out_quint: [0.22, 1, 0.36, 1],
        out_expo: [0.16, 1, 0.3, 1],
        in_cubic: [0.32, 0, 0.67, 0],
        in_out_cubic: [0.65, 0, 0.35, 1],
        in_out_quint: [0.83, 0, 0.17, 1],
        out_back: [0.34, 1.56, 0.64, 1],
        in_back: [0.36, 0, 0.66, -0.56]
    };
    function dims(p) {
        var t = p.propertyValueType;
        if (t === PropertyValueType.TwoD) { return 2; }
        if (t === PropertyValueType.ThreeD) { return 3; }
        return 1;
    }
    function rep(n, e) { var a = [], i; for (i = 0; i < n; i++) { a.push(new KeyframeEase(e.speed, e.influence)); } return a; }
    // move(prop, comp, f0, v0, f1, v1, ease): two keys at FRAMES; ease is a name in EASES, a [x1,y1,x2,y2] tuple,
    // or {out: influence, "in": influence} for zero-speed influences (Easy Ease is {out: 33.33, "in": 33.33}).
    function move(p, c, f0, v0, f1, v1, ease) {
        var k0 = AEK.motion.key(p, f0 * c.frameDuration, v0), k1 = AEK.motion.key(p, f1 * c.frameDuration, v1);
        k0 = p.nearestKeyIndex(f0 * c.frameDuration);
        if (typeof ease === "string") { ease = EASES[ease]; if (!ease) { throw new Error("Unknown ease name"); } }
        if (ease instanceof Array) {
            if (ease[0] === 0 && ease[1] === 0 && ease[2] === 1 && ease[3] === 1) {
                p.setInterpolationTypeAtKey(k0, p.keyInInterpolationType(k0), KeyframeInterpolationType.LINEAR);
                p.setInterpolationTypeAtKey(k1, KeyframeInterpolationType.LINEAR, p.keyOutInterpolationType(k1));
            } else { AEK.motion.bezier(p, k0, k1, ease); }
        } else if (ease) {
            var n = dims(p);
            p.setInterpolationTypeAtKey(k0, p.keyInInterpolationType(k0), KeyframeInterpolationType.BEZIER);
            p.setInterpolationTypeAtKey(k1, KeyframeInterpolationType.BEZIER, p.keyOutInterpolationType(k1));
            p.setTemporalEaseAtKey(k0, p.keyInTemporalEase(k0), rep(n, { speed: 0, influence: ease.out }));
            p.setTemporalEaseAtKey(k1, rep(n, { speed: 0, influence: ease["in"] }), p.keyOutTemporalEase(k1));
        }
        return [k0, k1];
    }
    // overshoot(prop, comp, f0, v0, fPeak, f1, v1, pct): three keys. The peak key sits pct percent of the travel past v1,
    // with zero speed (the turn-around); out of f0 is a fast start, into f1 a long settle.
    function overshoot(p, c, f0, v0, fPeak, f1, v1, pct, outInfluence, settleInfluence) {
        var peak, i;
        if (v0 instanceof Array) { peak = []; for (i = 0; i < v0.length; i++) { peak.push(v1[i] + (v1[i] - v0[i]) * pct / 100); } }
        else { peak = v1 + (v1 - v0) * pct / 100; }
        var k0 = AEK.motion.key(p, f0 * c.frameDuration, v0), kp = AEK.motion.key(p, fPeak * c.frameDuration, peak), k1 = AEK.motion.key(p, f1 * c.frameDuration, v1);
        k0 = p.nearestKeyIndex(f0 * c.frameDuration); kp = p.nearestKeyIndex(fPeak * c.frameDuration);
        var n = dims(p);
        p.setInterpolationTypeAtKey(k0, p.keyInInterpolationType(k0), KeyframeInterpolationType.BEZIER);
        p.setInterpolationTypeAtKey(kp, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
        p.setInterpolationTypeAtKey(k1, KeyframeInterpolationType.BEZIER, p.keyOutInterpolationType(k1));
        p.setTemporalEaseAtKey(k0, p.keyInTemporalEase(k0), rep(n, { speed: 0, influence: outInfluence || 10 }));
        p.setTemporalEaseAtKey(kp, rep(n, { speed: 0, influence: 75 }), rep(n, { speed: 0, influence: 50 }));
        p.setTemporalEaseAtKey(k1, rep(n, { speed: 0, influence: settleInfluence || 80 }), p.keyOutTemporalEase(k1));
        return [k0, kp, k1];
    }
    // springExpression(freq, decay, amp): overshoot AFTER the last key from the velocity at that key (JavaScript engine).
    function springExpression(freq, decay, amp) {
        return "var f=" + freq + ",d=" + decay + ",a=" + amp + ";\n" +
            "var n=0; if (numKeys>0){ n=nearestKey(time).index; if (key(n).time>time) n--; }\n" +
            "if (n===0 || n<numKeys) { value; } else {\n" +
            "  var t=time-key(n).time; var v=velocityAtTime(key(n).time-thisComp.frameDuration/10);\n" +
            "  value + v*a*Math.sin(f*t*2*Math.PI)/Math.exp(d*t); }";
    }
    // bounce(prop, comp, f0, ground, height, fallFrames, n, apexInfluence): a one-dimensional bounce (separated Y, or any 1D value).
    // Each rebound is half the height and half the duration of the one before. Every segment is a parabola: apex keys speed 0,
    // contact keys Bezier with broken handles at speed 2h/d (full speed into and out of the ground), influence 33.33.
    // Linear contact keys are wrong: the segment then peaks mid-fall and slows before the ground. Returns [{frame, value, kind}].
    function bounce(p, c, f0, ground, height, fallFrames, n, apexInfluence) {
        var out = [], f = f0, h = height, d = fallFrames, i, k, inf = apexInfluence || 33.33, dir = ground > ground - height ? 1 : -1;
        k = AEK.motion.key(p, f * c.frameDuration, ground - h); out.push({ frame: f, value: ground - h, kind: "apex" });
        f += d; out.push({ frame: f, value: ground, kind: "contact" }); AEK.motion.key(p, f * c.frameDuration, ground);
        for (i = 1; i <= n; i++) {
            h = h / 2; d = Math.max(1, Math.round(d / 2));
            f += d; AEK.motion.key(p, f * c.frameDuration, ground - h); out.push({ frame: f, value: ground - h, kind: "apex" });
            f += d; AEK.motion.key(p, f * c.frameDuration, ground); out.push({ frame: f, value: ground, kind: "contact" });
        }
        function segSpeed(a, b) { return 2 * Math.abs(out[b].value - out[a].value) / ((out[b].frame - out[a].frame) * c.frameDuration); }
        for (k = 1; k <= p.numKeys; k++) {
            p.setInterpolationTypeAtKey(k, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
            if (out[k - 1].kind === "contact") {
                p.setTemporalContinuousAtKey(k, false); p.setTemporalAutoBezierAtKey(k, false);
                var vin = segSpeed(k - 2, k - 1) * dir, vout = k < p.numKeys ? -segSpeed(k - 1, k) * dir : 0;
                p.setTemporalEaseAtKey(k, [new KeyframeEase(vin, inf)], [new KeyframeEase(vout, k < p.numKeys ? inf : 33.33)]);
            } else { p.setTemporalEaseAtKey(k, [new KeyframeEase(0, inf)], [new KeyframeEase(0, inf)]); }
        }
        return out;
    }
    function readKey(p, k) {
        var o = { t: p.keyTime(k), v: p.keyValue(k), inT: p.keyInInterpolationType(k), outT: p.keyOutInterpolationType(k),
            inE: p.keyInTemporalEase(k), outE: p.keyOutTemporalEase(k), spatial: false };
        if (p.propertyValueType === PropertyValueType.TwoD_SPATIAL || p.propertyValueType === PropertyValueType.ThreeD_SPATIAL) {
            o.spatial = true; o.inS = p.keyInSpatialTangent(k); o.outS = p.keyOutSpatialTangent(k);
            o.rov = p.keyRoving(k); o.sc = p.keySpatialContinuous(k); o.sab = p.keySpatialAutoBezier(k);
        }
        return o;
    }
    function writeKey(p, o, t) {
        var k = AEK.motion.key(p, t, o.v);
        p.setInterpolationTypeAtKey(k, o.inT, o.outT);
        if (o.inT === KeyframeInterpolationType.BEZIER || o.outT === KeyframeInterpolationType.BEZIER) { p.setTemporalEaseAtKey(k, o.inE, o.outE); }
        if (o.spatial) { p.setSpatialAutoBezierAtKey(k, o.sab); p.setSpatialContinuousAtKey(k, o.sc); p.setSpatialTangentsAtKey(k, o.inS, o.outS); }
        return k;
    }
    // shiftKeys(prop, comp, frames): moves every key of a property by whole frames, keeping values, interpolation, eases and tangents.
    // Keys are re-created (no move API in ExtendScript): rebuild from the last key when shifting later so keys never collide.
    function shiftKeys(p, c, frames) {
        var all = [], k, i, dt = frames * c.frameDuration;
        for (k = 1; k <= p.numKeys; k++) { all.push(readKey(p, k)); }
        for (k = p.numKeys; k >= 1; k--) { p.removeKey(k); }
        for (i = 0; i < all.length; i++) { writeKey(p, all[i], all[i].t + dt); }
        // eases are re-applied once every key exists: a neighbor added later resets the speed of the segment
        for (i = 0; i < all.length; i++) {
            k = p.nearestKeyIndex(all[i].t + dt);
            if (all[i].inT === KeyframeInterpolationType.BEZIER || all[i].outT === KeyframeInterpolationType.BEZIER) { p.setTemporalEaseAtKey(k, all[i].inE, all[i].outE); }
        }
        return p.numKeys;
    }
    // animatedProps(layer): transform properties of a layer that carry keys
    function animatedProps(l) {
        var out = [];
        AEK.core.walk(l, function (p) {
            if (p.propertyType !== PropertyType.PROPERTY) { return; }
            try { if (p.numKeys > 0) { out.push(p); } } catch (e) {}
        });
        return out;
    }
    // stagger(layers, comp, frames, mode): "layer" moves each layer's startTime by i * frames (keys travel with the layer);
    // "keys" shifts the keys of every animated property instead, leaving in-points untouched.
    function stagger(layers, c, frames, mode) {
        var i, j, ps, out = [];
        for (i = 0; i < layers.length; i++) {
            if (mode === "keys") { ps = animatedProps(layers[i]); for (j = 0; j < ps.length; j++) { shiftKeys(ps[j], c, i * frames); } }
            else { layers[i].startTime = layers[i].startTime + i * frames * c.frameDuration; }
            out.push({ layer: layers[i].name, startFrame: Math.round(layers[i].startTime * c.frameRate) });
        }
        return out;
    }
    // copyEase(src, dst): copies influence per key (and speed rescaled by the value change), keys paired by index
    function copyEase(src, dst) {
        var n = Math.min(src.numKeys, dst.numKeys), k, ie, oe, i, done = 0;
        for (k = 1; k <= n; k++) {
            ie = src.keyInTemporalEase(k); oe = src.keyOutTemporalEase(k);
            var di = dst.keyInTemporalEase(k).length, a = [], b = [];
            for (i = 0; i < di; i++) { a.push(new KeyframeEase(0, ie[Math.min(i, ie.length - 1)].influence)); b.push(new KeyframeEase(0, oe[Math.min(i, oe.length - 1)].influence)); }
            dst.setInterpolationTypeAtKey(k, src.keyInInterpolationType(k), src.keyOutInterpolationType(k));
            if (src.keyInInterpolationType(k) === KeyframeInterpolationType.BEZIER || src.keyOutInterpolationType(k) === KeyframeInterpolationType.BEZIER) { dst.setTemporalEaseAtKey(k, a, b); }
            done++;
        }
        return done;
    }
    // compPoint(layer, seconds): the layer's anchor point in comp space, parents included (temporary Point Control + toComp).
    function compPoint(l, t) {
        var fx = l.property("ADBE Effect Parade"), e = fx.addProperty("ADBE Point Control"), idx = e.propertyIndex, v;
        var pt = l.property("ADBE Effect Parade").property(idx).property(1);
        pt.expression = "thisLayer.toComp(thisLayer.anchorPoint)";
        v = pt.valueAtTime(t, false);
        l.property("ADBE Effect Parade").property(idx).remove();
        return [Math.round(v[0] * 10) / 10, Math.round(v[1] * 10) / 10];
    }
    function isDefaultEase(e) { return e.speed === 0 && Math.abs(e.influence - 33.33333) < 0.05; }
    // motionCheck(comp): findings {rule, layer, property, key, message} for the habits experts call unfinished motion.
    function motionCheck(c, o) {
        o = o || {};
        var out = [], starts = {}, i, l, ps, j, p, k, nKeys = 0, nDefault = 0, fd = c.frameDuration;
        function add(rule, layer, prop, key, msg) { out.push({ rule: rule, layer: layer, property: prop, key: key, message: msg }); }
        function same(a, b) { if (!(a instanceof Array)) { return Math.abs(a - b) < 0.001; } for (var q = 0; q < a.length; q++) { if (Math.abs(a[q] - b[q]) > 0.001) { return false; } } return true; }
        function dist(a, b) { if (!(a instanceof Array)) { return Math.abs(a - b); } var s = 0, q; for (q = 0; q < a.length; q++) { s += (a[q] - b[q]) * (a[q] - b[q]); } return Math.sqrt(s); }
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i); ps = animatedProps(l);
            var first = null;
            for (j = 0; j < ps.length; j++) {
                p = ps[j];
                if (p.numKeys < 2) { continue; }
                var f0 = Math.round(p.keyTime(1) * c.frameRate);
                if (first === null || f0 < first) { first = f0; }
                for (k = 1; k <= p.numKeys; k++) {
                    var inT = p.keyInInterpolationType(k), outT = p.keyOutInterpolationType(k);
                    nKeys++;
                    if (inT === KeyframeInterpolationType.BEZIER && outT === KeyframeInterpolationType.BEZIER && isDefaultEase(p.keyInTemporalEase(k)[0]) && isDefaultEase(p.keyOutTemporalEase(k)[0])) { nDefault++; }
                    if (k < p.numKeys && outT === KeyframeInterpolationType.LINEAR && p.keyInInterpolationType(k + 1) === KeyframeInterpolationType.LINEAR && p.matchName !== "ADBE Opacity") {
                        add("linear", l.name, p.name, k, "linear segment from frame " + Math.round(p.keyTime(k) * c.frameRate) + ": constant speed, hard start and stop");
                    }
                    if (k < p.numKeys && same(p.keyValue(k), p.keyValue(k + 1)) && outT !== KeyframeInterpolationType.HOLD) {
                        var mid = (p.keyTime(k) + p.keyTime(k + 1)) / 2, d = dist(p.valueAtTime(mid, true), p.keyValue(k));
                        if (d > 0.5) { add("drift", l.name, p.name, k, "equal keys but the value moves " + Math.round(d * 10) / 10 + " between them: use a Hold key or linear spatial tangents"); }
                    }
                    if (k > 1 && k < p.numKeys) {
                        var tk = p.keyTime(k), vb = dist(p.valueAtTime(tk, true), p.valueAtTime(tk - fd, true)), va = dist(p.valueAtTime(tk + fd, true), p.valueAtTime(tk, true));
                        var hi = Math.max(va, vb), lo = Math.min(va, vb), seg = 0, q2, t2a = p.keyTime(k - 1), t2b = p.keyTime(k + 1);
                        // peak per-frame speed of the two neighboring segments: an eased stop slows to under half of it
                        for (q2 = t2a; q2 < t2b; q2 += fd) { seg = Math.max(seg, dist(p.valueAtTime(q2 + fd, true), p.valueAtTime(q2, true))); }
                        if (hi > (o.popMin || 2) && hi > seg * (o.popRatio || 0.5) && lo < hi * 0.25 && inT !== KeyframeInterpolationType.HOLD && outT !== KeyframeInterpolationType.HOLD) {
                            add("pop", l.name, p.name, k, "speed jumps from " + Math.round(vb) + " to " + Math.round(va) + " per frame at frame " + Math.round(tk * c.frameRate));
                        }
                    }
                }
            }
            if (first !== null) { starts[first] = (starts[first] || 0) + 1; }
        }
        for (k in starts) { if (starts.hasOwnProperty(k) && starts[k] >= 3) { add("lockstep", "*", "*", null, starts[k] + " layers start moving on frame " + k + ": offset them (2 to 3 frames for list items)"); } }
        if (nKeys >= 4 && nDefault / nKeys > 0.6) { add("default-ease", "*", "*", null, Math.round(nDefault / nKeys * 100) + " % of keys are Easy Ease (33.33 % both sides): shape them"); }
        return { keys: nKeys, defaultEase: nDefault, findings: out };
    }
    return { EASES: EASES, move: move, overshoot: overshoot, springExpression: springExpression, bounce: bounce, shiftKeys: shiftKeys, stagger: stagger,
        animatedProps: animatedProps, copyEase: copyEase, compPoint: compPoint, motionCheck: motionCheck };
})();
