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
        // f1 before f0 would put the ease on the outer sides of the two keys (measured): refuse it
        if (!(f1 > f0)) { throw new Error("move(): f1 must come after f0"); }
        // read the first key's index again once both keys exist
        AEK.motion.key(p, f0 * c.frameDuration, v0);
        var k1 = AEK.motion.key(p, f1 * c.frameDuration, v1), k0 = p.nearestKeyIndex(f0 * c.frameDuration);
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
        if (!(f0 < fPeak && fPeak < f1)) { throw new Error("overshoot(): frames must run f0 < fPeak < f1"); }
        if (v0 instanceof Array) { peak = []; for (i = 0; i < v0.length; i++) { peak.push(v1[i] + (v1[i] - v0[i]) * pct / 100); } }
        else { peak = v1 + (v1 - v0) * pct / 100; }
        // earlier indices shift when a later call adds a key before them: read them again once all three exist
        AEK.motion.key(p, f0 * c.frameDuration, v0); AEK.motion.key(p, fPeak * c.frameDuration, peak);
        var k1 = AEK.motion.key(p, f1 * c.frameDuration, v1), k0 = p.nearestKeyIndex(f0 * c.frameDuration), kp = p.nearestKeyIndex(fPeak * c.frameDuration);
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
        var out = [], f = f0, h = height, d = fallFrames, i, j, k, last, inf = apexInfluence || 33.33, dir = ground > ground - height ? 1 : -1;
        AEK.motion.key(p, f * c.frameDuration, ground - h); out.push({ frame: f, value: ground - h, kind: "apex" });
        f += d; out.push({ frame: f, value: ground, kind: "contact" }); AEK.motion.key(p, f * c.frameDuration, ground);
        for (i = 1; i <= n; i++) {
            h = h / 2; d = Math.max(1, Math.round(d / 2));
            f += d; AEK.motion.key(p, f * c.frameDuration, ground - h); out.push({ frame: f, value: ground - h, kind: "apex" });
            f += d; AEK.motion.key(p, f * c.frameDuration, ground); out.push({ frame: f, value: ground, kind: "contact" });
        }
        function segSpeed(a, b) { return 2 * Math.abs(out[b].value - out[a].value) / ((out[b].frame - out[a].frame) * c.frameDuration); }
        // only the keys made here: a key the property already had keeps its interpolation and ease
        for (j = 0; j < out.length; j++) {
            k = p.nearestKeyIndex(out[j].frame * c.frameDuration); last = j === out.length - 1;
            p.setInterpolationTypeAtKey(k, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
            if (out[j].kind === "contact") {
                p.setTemporalContinuousAtKey(k, false); p.setTemporalAutoBezierAtKey(k, false);
                var vin = segSpeed(j - 1, j) * dir, vout = last ? 0 : -segSpeed(j, j + 1) * dir;
                p.setTemporalEaseAtKey(k, [new KeyframeEase(vin, inf)], [new KeyframeEase(vout, last ? 33.33 : inf)]);
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
            // a separated Position is hidden and reports its followers' key count with linear types: read the followers only
            try { if (p.isSeparationLeader && p.dimensionsSeparated) { return; } } catch (e0) {}
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
    // speedScale(src, dst, ka, kb, i, n): factor turning a src speed into a dst speed on the segment ka to kb, ease dimension i of n.
    // One ease on a multi-value property is a path speed (lengths); otherwise dimension i (signed, so a reversed move flips it).
    function speedScale(src, dst, ka, kb, i, n) {
        function arr(x) { return x instanceof Array ? x : [x]; }
        function travel(p) {
            var a = arr(p.keyValue(ka)), b = arr(p.keyValue(kb)), s = 0, q;
            if (n === 1 && a.length > 1) { for (q = 0; q < a.length; q++) { s += (b[q] - a[q]) * (b[q] - a[q]); } return Math.sqrt(s); }
            q = Math.min(i, a.length - 1); return b[q] - a[q];
        }
        var st = travel(src), sd = src.keyTime(kb) - src.keyTime(ka), dd = dst.keyTime(kb) - dst.keyTime(ka);
        if (Math.abs(st) < 1e-9 || sd <= 0 || dd <= 0) { return 1; }
        return travel(dst) / st * (sd / dd);
    }
    // copyEase(src, dst): copies influence and speed per key, keys paired by index. Speed is rescaled by the travel and the
    // duration of the neighboring segment; a speed of 0 stays 0. At the first and last key the speed is copied as is.
    function copyEase(src, dst) {
        var n = Math.min(src.numKeys, dst.numKeys), k, ie, oe, i, done = 0, si, so;
        for (k = 1; k <= n; k++) {
            ie = src.keyInTemporalEase(k); oe = src.keyOutTemporalEase(k);
            var di = dst.keyInTemporalEase(k).length, a = [], b = [];
            for (i = 0; i < di; i++) {
                si = ie[Math.min(i, ie.length - 1)]; so = oe[Math.min(i, oe.length - 1)];
                a.push(new KeyframeEase(si.speed === 0 || k === 1 ? si.speed : si.speed * speedScale(src, dst, k - 1, k, i, di), si.influence));
                b.push(new KeyframeEase(so.speed === 0 || k === n ? so.speed : so.speed * speedScale(src, dst, k, k + 1, i, di), so.influence));
            }
            dst.setInterpolationTypeAtKey(k, src.keyInInterpolationType(k), src.keyOutInterpolationType(k));
            if (src.keyInInterpolationType(k) === KeyframeInterpolationType.BEZIER || src.keyOutInterpolationType(k) === KeyframeInterpolationType.BEZIER) { dst.setTemporalEaseAtKey(k, a, b); }
            done++;
        }
        return done;
    }
    // compPoint(layer, seconds): the layer's anchor point in comp space, parents included (temporary Point Control + toComp).
    function compPoint(l, t) {
        var fx = l.property("ADBE Effect Parade"), e = fx.addProperty("ADBE Point Control"), idx = e.propertyIndex, v;
        try {
            var pt = l.property("ADBE Effect Parade").property(idx).property(1);
            pt.expression = "thisLayer.toComp(thisLayer.anchorPoint)";
            v = pt.valueAtTime(t, false);
        } finally { l.property("ADBE Effect Parade").property(idx).remove(); }
        return [Math.round(v[0] * 10) / 10, Math.round(v[1] * 10) / 10];
    }
    function isDefaultEase(e) { return e.speed === 0 && Math.abs(e.influence - 33.33333) < 0.05; }
    // intent(layer, frame, rules, why): marks a key as intended with a layer marker "intended: <rules>: <why>" at that frame.
    // motionCheck moves a finding on that layer within 1 frame of the marker into `intended` instead of `findings`.
    function intent(l, frame, rules, why) {
        var c = l.containingComp, mv = new MarkerValue("intended: " + rules + (why ? ": " + why : ""));
        l.property("ADBE Marker").setValueAtTime(frame * c.frameDuration, mv);
        return mv.comment;
    }
    function intentsOf(l, c) {
        var m = l.property("ADBE Marker"), out = [], k, s;
        for (k = 1; k <= m.numKeys; k++) {
            s = m.keyValue(k).comment;
            if (/^intended\b/i.test(s)) { out.push({ frame: Math.round(m.keyTime(k) * c.frameRate), text: s }); }
        }
        return out;
    }
    // motionCheck(comp, {allow: ["layer|rule|frame", ...], popMin, popRatio}): findings {rule, layer, property, key, frame, message}
    // for the habits experts call unfinished motion. Findings marked as intended (intent() markers or `allow`) go to `intended`.
    function motionCheck(c, o) {
        o = o || {};
        var out = [], kept = [], starts = {}, i, l, ps, j, p, k, nKeys = 0, nDefault = 0, fd = c.frameDuration, marks = {};
        function add(rule, layer, prop, key, msg) { out.push({ rule: rule, layer: layer, property: prop, key: key, frame: (prop !== "*" && key) ? Math.round(p.keyTime(key) * c.frameRate) : null, message: msg }); }
        for (i = 1; i <= c.numLayers; i++) { marks[c.layer(i).name] = intentsOf(c.layer(i), c); }
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
        // lockstep carries its start frame, so allow "*|lockstep|<frame>" exempts it; frame-less findings take "*|<rule>"
        for (k in starts) { if (Object.prototype.hasOwnProperty.call(starts, k) && starts[k] >= 3) { out.push({ rule: "lockstep", layer: "*", property: "*", key: null, frame: Number(k), message: starts[k] + " layers start moving on frame " + k + ": offset them (2 to 3 frames for list items)" }); } }
        if (nKeys >= 4 && nDefault / nKeys > 0.6) { add("default-ease", "*", "*", null, Math.round(nDefault / nKeys * 100) + " % of keys are Easy Ease (33.33 % both sides): shape them"); }
        var allow = {}, q, x, hit;
        if (o.allow) { for (q = 0; q < o.allow.length; q++) { allow[o.allow[q]] = true; } }
        for (q = 0; q < out.length; q++) {
            hit = null;
            if (out[q].frame !== null && allow[out[q].layer + "|" + out[q].rule + "|" + out[q].frame]) { hit = "allow list"; }
            if (out[q].frame === null && allow[out[q].layer + "|" + out[q].rule]) { hit = "allow list"; }
            // hasOwnProperty: ExtendScript objects inherit a native "*" operator, so marks["*"] is a function, not undefined
            if (!hit && out[q].frame !== null && Object.prototype.hasOwnProperty.call(marks, out[q].layer)) {
                for (x = 0; x < marks[out[q].layer].length; x++) {
                    var mk = marks[out[q].layer][x];
                    if (Math.abs(mk.frame - out[q].frame) <= 1 && (mk.text.toLowerCase().indexOf(out[q].rule) >= 0 || /^intended\s*$/i.test(mk.text))) { hit = mk.text; }
                }
            }
            if (hit) { out[q].because = hit; kept.push(out[q]); out.splice(q, 1); q--; }
        }
        return { keys: nKeys, defaultEase: nDefault, findings: out, intended: kept };
    }
    // graph(prop, comp, f0, f1, {out, name, width, height, keep}): the graph editor as numbers and as a picture. Progress is the value
    // projected on the first-to-last-key travel (1 = target); speed is travel per frame. Builds a comp with a white value curve,
    // an orange speed curve, a gray target line, a dark zero line and blue key ticks; saves one PNG when `out` (absolute file path)
    // is given, then removes that comp unless keep is true. Without `out` the comp stays (it is the picture).
    function graph(p, c, f0, f1, o) {
        o = o || {};
        var W = o.width || 960, H = o.height || 540, pad = 50, n = f1 - f0, i, v, a = p.keyValue(1), b = p.keyValue(p.numKeys), d = [], len2 = 0, prog = [], spd = [0], mx = 0;
        function arr(x) { return x instanceof Array ? x : [x]; }
        a = arr(a); b = arr(b);
        for (i = 0; i < a.length; i++) { d.push(b[i] - a[i]); len2 += d[i] * d[i]; }
        // first and last keys equal (anticipation, pulse, loop): measure against the key farthest from the first instead
        if (len2 < 1e-9) {
            var far = 0, kk, kv, dd;
            for (kk = 2; kk <= p.numKeys; kk++) { kv = arr(p.keyValue(kk)); dd = 0; for (i = 0; i < a.length; i++) { dd += (kv[i] - a[i]) * (kv[i] - a[i]); } if (dd > far) { far = dd; b = kv; } }
            d = []; len2 = 0; for (i = 0; i < a.length; i++) { d.push(b[i] - a[i]); len2 += d[i] * d[i]; }
        }
        for (i = 0; i <= n; i++) {
            v = arr(p.valueAtTime((f0 + i) * c.frameDuration, false));
            var s = 0, q; for (q = 0; q < a.length; q++) { s += (v[q] - a[q]) * d[q]; }
            prog.push(len2 > 0 ? s / len2 : 0);
            if (i > 0) { spd.push(Math.abs(prog[i] - prog[i - 1])); mx = Math.max(mx, spd[i]); }
        }
        // target: the last key's value on the same scale (1 for an ordinary move, 0 when first and last keys are equal)
        var lastV = arr(p.keyValue(p.numKeys)), tg = 0, peakF = 0, maxP = -1e9, cross = 0;
        for (i = 0; i < a.length; i++) { tg += (lastV[i] - a[i]) * d[i]; }
        tg = len2 > 0 ? tg / len2 : 0;
        for (i = 0; i <= n; i++) {
            if (spd[i] === mx) { peakF = f0 + i; }
            maxP = Math.max(maxP, prog[i]);
            if (i > 0 && (prog[i - 1] - tg) * (prog[i] - tg) < 0) { cross++; }
        }
        // null when the last sampled frame is still outside the band: the settle frame lies past the window
        var settle = f0; for (i = n; i >= 0; i--) { if (Math.abs(prog[i] - tg) > 0.01) { settle = i === n ? null : f0 + i + 1; break; } }
        var R = { frames: [f0, f1], target: tg, progress: prog, speed: spd, peakSpeedFrame: peakF, overshootPct: tg === 1 ? Math.round(Math.max(0, maxP - 1) * 1000) / 10 : null, crossings: cross, settleFrame: settle };
        var g = AEK.build.comp(o.name || "graph", { width: W, height: H, fps: c.frameRate, duration: c.frameDuration * 2, bg: [0.12, 0.12, 0.13] });
        var lo = Math.min(0, Math.min.apply(null, prog)), hi = Math.max(1.15, maxP + 0.05);
        function X(k) { return pad + (W - 2 * pad) * k / n - W / 2; }
        function Y(val) { return H / 2 - pad - (H - 2 * pad) * (val - lo) / (hi - lo); }
        function line(name, pts, color, w) {
            var L = g.layers.addShape(); L.name = name;
            var C = L.property("ADBE Root Vectors Group"), gi = C.addProperty("ADBE Vector Group").propertyIndex;
            var V = function () { return L.property("ADBE Root Vectors Group").property(gi).property("ADBE Vectors Group"); };
            V().addProperty("ADBE Vector Shape - Group");
            var sh = new Shape(), z = [], k; for (k = 0; k < pts.length; k++) { z.push([0, 0]); }
            sh.vertices = pts; sh.inTangents = z; sh.outTangents = z; sh.closed = false;
            V().property(1).property("ADBE Vector Shape").setValue(sh);
            V().addProperty("ADBE Vector Graphic - Stroke");
            V().property(2).property("ADBE Vector Stroke Color").setValue(color); V().property(2).property("ADBE Vector Stroke Width").setValue(w || 3);
            L.property("ADBE Transform Group").property("ADBE Position").setValue([W / 2, H / 2]);
            return L;
        }
        var vp = [], sp = [];
        for (i = 0; i <= n; i++) { vp.push([X(i), Y(prog[i])]); sp.push([X(i), H / 2 - pad - (H - 2 * pad) * (mx > 0 ? spd[i] / mx : 0) * 0.9]); }
        line("target", [[X(0), Y(tg)], [X(n), Y(tg)]], [0.5, 0.5, 0.5], 1);
        line("zero", [[X(0), Y(0)], [X(n), Y(0)]], [0.3, 0.3, 0.3], 1);
        for (i = 1; i <= p.numKeys; i++) { var kf = Math.round(p.keyTime(i) * c.frameRate) - f0; if (kf >= 0 && kf <= n) { line("key " + i, [[X(kf), H / 2 - pad], [X(kf), -H / 2 + pad]], [0.35, 0.55, 1], 1); } }
        line("speed", sp, [1, 0.55, 0.2], 3);
        line("value", vp, [1, 1, 1], 3);
        if (o.out) { R.png = AEK.capture.frame(g, 0, o.out); }
        R.comp = g.name;
        if (o.out && !o.keep) { g.remove(); R.comp = null; R.removed = true; }
        return R;
    }
    // report(comp, props): the motion report as a function, to call at the end of the job that built the comp (shared app).
    // Per animated transform property: keys, peak speed per frame, peak frame, overshoot %, settle frame; then motionCheck and blur.
    function report(c, props) {
        var out = { comp: c.name, fps: c.frameRate, layers: [] }, i, j, ps, p, s, k;
        var want = props || ["ADBE Position", "ADBE Scale", "ADBE Rotate Z", "ADBE Opacity"];
        // separated X and Y followers carry their own match names: anything starting with "ADBE Position" counts as Position
        function wanted(mn) { for (var q = 0; q < want.length; q++) { if (want[q] === mn || (want[q] === "ADBE Position" && /^ADBE Position/.test(mn))) { return true; } } return false; }
        for (i = 1; i <= c.numLayers; i++) {
            ps = animatedProps(c.layer(i));
            var L = { layer: c.layer(i).name, parent: c.layer(i).parent ? c.layer(i).parent.name : null, motionBlur: c.layer(i).motionBlur, props: [] };
            for (j = 0; j < ps.length; j++) {
                p = ps[j];
                if (!wanted(p.matchName) || p.numKeys < 2) { continue; }
                s = AEK.motion.sample(p, c, p.keyTime(1), p.keyTime(p.numKeys));
                var ks = AEK.motion.keys(p, c), frames = [];
                for (k = 0; k < ks.length; k++) { frames.push(ks[k].frame + " " + ks[k].inType.charAt(0) + "/" + ks[k].outType.charAt(0) + " in " + Math.round(ks[k].inInfluence) + " out " + Math.round(ks[k].outInfluence)); }
                L.props.push({ property: p.matchName, keys: frames, peakPerFrame: Math.round(s.peakSpeed / c.frameRate * 10) / 10, peakFrame: s.peakFrame, overshootPct: s.overshoot, settleFrame: s.settleFrame });
            }
            if (L.props.length) { out.layers.push(L); }
        }
        out.check = motionCheck(c);
        out.blur = { on: c.motionBlur, angle: c.shutterAngle, phase: c.shutterPhase, samples: c.motionBlurSamplesPerFrame, adaptiveLimit: c.motionBlurAdaptiveSampleLimit };
        return out;
    }
    // onScreen(layer, comp, frame): share of the layer's box (sourceRectAtTime through toComp, parents included) inside the
    // frame, and the layer's own Opacity, at that frame. Masks are not counted. Uses a temporary Point Control, removed at once.
    function onScreen(l, c, f) {
        var t = f * c.frameDuration, idx = l.property("ADBE Effect Parade").addProperty("ADBE Point Control").propertyIndex, i, v, xs = [], ys = [];
        var corners = ["[r.left, r.top]", "[r.left + r.width, r.top]", "[r.left, r.top + r.height]", "[r.left + r.width, r.top + r.height]"];
        try {
            for (i = 0; i < 4; i++) {
                var pt = l.property("ADBE Effect Parade").property(idx).property(1);
                pt.expression = "var r = thisLayer.sourceRectAtTime(time, false); thisLayer.toComp(" + corners[i] + ");";
                v = pt.valueAtTime(t, false); xs.push(v[0]); ys.push(v[1]);
            }
        } finally { l.property("ADBE Effect Parade").property(idx).remove(); }
        var x0 = Math.min(xs[0], xs[1], xs[2], xs[3]), x1 = Math.max(xs[0], xs[1], xs[2], xs[3]), y0 = Math.min(ys[0], ys[1], ys[2], ys[3]), y1 = Math.max(ys[0], ys[1], ys[2], ys[3]);
        var area = Math.max(1e-6, (x1 - x0) * (y1 - y0)), iw = Math.max(0, Math.min(x1, c.width) - Math.max(x0, 0)), ih = Math.max(0, Math.min(y1, c.height) - Math.max(y0, 0));
        var active = t >= l.inPoint && t < l.outPoint;
        return { frame: f, inside: active ? Math.round(iw * ih / area * 1000) / 1000 : 0, opacity: l.property("ADBE Transform Group").property("ADBE Opacity").valueAtTime(t, false) };
    }
    // firstSeen(layer, comp, {min, opacity, last}): first frame (from 0) where at least `min` (default 0.5) of the layer's box is
    // inside the frame at `opacity` (default 50) or more. The feed rule asks for frame 3 or earlier.
    function firstSeen(l, c, o) {
        o = o || {};
        var f, r, last = o.last === undefined ? 30 : o.last;
        for (f = 0; f <= last; f++) { r = onScreen(l, c, f); if (r.inside >= (o.min || 0.5) && r.opacity >= (o.opacity === undefined ? 50 : o.opacity)) { return f; } }
        return null;
    }
    // ovalMask(layer, {center, size, feather, name}): the in-app minimum for a still without alpha: one elliptical mask in layer
    // pixels, feathered. It hides a backdrop; it cannot remove a shadow or reflection baked inside the oval. Set the comp
    // background to the plate's corner color, or the feathered rim shows (procedure 16).
    function ovalMask(l, o) {
        o = o || {};
        var w = l.width, h = l.height, ctr = o.center || [w / 2, h / 2], sz = o.size || [w * 0.8, h * 0.8];
        // the kit's mask builder: it returns the mask fetched fresh, safe after further addProperty calls on the layer
        var m = AEK.build.mask(l, { ellipse: [ctr[0] - sz[0] / 2, ctr[1] - sz[1] / 2, sz[0], sz[1]], feather: o.feather === undefined ? 60 : o.feather, name: o.name });
        return m.name;
    }
    return { EASES: EASES, move: move, overshoot: overshoot, springExpression: springExpression, bounce: bounce, shiftKeys: shiftKeys, stagger: stagger,
        animatedProps: animatedProps, copyEase: copyEase, compPoint: compPoint, intent: intent, motionCheck: motionCheck, graph: graph,
        report: report, onScreen: onScreen, firstSeen: firstSeen, ovalMask: ovalMask };
})();
