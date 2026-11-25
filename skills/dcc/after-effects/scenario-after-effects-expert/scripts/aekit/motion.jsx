// aekit/motion.jsx: keyframes, easing and measurement of motion. Requires core.jsx.
var AEK = AEK || {};
AEK.motion = (function () {
    function dims(p) {
        var t = p.propertyValueType;
        if (t === PropertyValueType.OneD) { return 1; }
        if (t === PropertyValueType.TwoD) { return 2; }
        if (t === PropertyValueType.ThreeD) { return 3; }
        return 1; // spatial properties (Position, Anchor Point) take ONE ease
    }
    function interp(t) { return t === KeyframeInterpolationType.LINEAR ? "linear" : (t === KeyframeInterpolationType.BEZIER ? "bezier" : "hold"); }
    // key(prop, seconds, value): adds a key and returns its index
    function key(p, seconds, value) { p.setValueAtTime(seconds, value); return p.nearestKeyIndex(seconds); }
    // ease(prop, keyIndex, inInfluence, outInfluence): speed 0 at the key, influences in percent (0.1 to 100)
    function ease(p, k, inInfluence, outInfluence) {
        var n = dims(p), i, a = [], b = [];
        for (i = 0; i < n; i++) { a.push(new KeyframeEase(0, Math.max(0.1, inInfluence))); b.push(new KeyframeEase(0, Math.max(0.1, outInfluence))); }
        p.setInterpolationTypeAtKey(k, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
        p.setTemporalEaseAtKey(k, a, b);
    }
    // bezier(prop, k1, k2, [x1, y1, x2, y2]): CSS-style cubic-bezier between two neighboring keys.
    // Exact for one-dimensional and spatial properties; for separated multi-dimension values each dimension gets the same curve.
    function bezier(p, k1, k2, cb) {
        var n = dims(p), t1 = p.keyTime(k1), t2 = p.keyTime(k2), dt = t2 - t1, v1 = p.keyValue(k1), v2 = p.keyValue(k2);
        var spatial = (p.propertyValueType === PropertyValueType.TwoD_SPATIAL || p.propertyValueType === PropertyValueType.ThreeD_SPATIAL);
        var i, outE = [], inE = [], dv, sOut, sIn, x1 = Math.max(0.001, cb[0]), x2 = Math.min(0.999, cb[2]);
        function delta(d) {
            if (spatial) { var s = 0, j; for (j = 0; j < v1.length; j++) { s += (v2[j] - v1[j]) * (v2[j] - v1[j]); } return Math.sqrt(s); }
            return (v1 instanceof Array) ? (v2[d] - v1[d]) : (v2 - v1);
        }
        for (i = 0; i < n; i++) {
            dv = delta(i);
            sOut = (cb[1] / x1) * dv / dt;
            sIn = ((1 - cb[3]) / (1 - x2)) * dv / dt;
            outE.push(new KeyframeEase(sOut, Math.max(0.1, x1 * 100)));
            inE.push(new KeyframeEase(sIn, Math.max(0.1, (1 - x2) * 100)));
        }
        p.setInterpolationTypeAtKey(k1, p.keyInInterpolationType(k1), KeyframeInterpolationType.BEZIER);
        p.setInterpolationTypeAtKey(k2, KeyframeInterpolationType.BEZIER, p.keyOutInterpolationType(k2));
        p.setTemporalEaseAtKey(k1, p.keyInTemporalEase(k1), outE);
        p.setTemporalEaseAtKey(k2, inE, p.keyOutTemporalEase(k2));
    }
    // keys(prop, comp): every key with its frame, value and eases, for a report
    function keys(p, c) {
        var out = [], k, e1, e2;
        for (k = 1; k <= p.numKeys; k++) {
            e1 = p.keyInTemporalEase(k)[0]; e2 = p.keyOutTemporalEase(k)[0];
            out.push({ k: k, time: p.keyTime(k), frame: c ? Math.round(p.keyTime(k) * c.frameRate) : null, value: p.keyValue(k),
                inType: interp(p.keyInInterpolationType(k)), outType: interp(p.keyOutInterpolationType(k)),
                inSpeed: e1.speed, inInfluence: e1.influence, outSpeed: e2.speed, outInfluence: e2.influence });
        }
        return out;
    }
    // sample(prop, comp, t0, t1): value per frame plus speed per second; finds peak speed, overshoot and settle frame
    function sample(p, c, t0, t1) {
        var fd = c.frameDuration, t, v, prev = null, d, sp, out = { frames: [], peakSpeed: 0, peakFrame: 0, overshoot: 0, settleFrame: null }, j;
        var end = p.valueAtTime(t1, false), start = p.valueAtTime(t0, false), total = 0, dist, maxPast = 0;
        function len(a, b) { if (!(a instanceof Array)) { return Math.abs(a - b); } var s = 0; for (j = 0; j < a.length; j++) { s += (a[j] - b[j]) * (a[j] - b[j]); } return Math.sqrt(s); }
        total = len(start, end);
        for (t = t0; t <= t1 + fd / 2; t += fd) {
            v = p.valueAtTime(t, false);
            sp = prev === null ? 0 : len(v, prev) / fd;
            if (sp > out.peakSpeed) { out.peakSpeed = sp; out.peakFrame = Math.round(t * c.frameRate); }
            dist = len(v, start);
            if (total > 0 && dist > total) { maxPast = Math.max(maxPast, dist - total); }
            if (out.settleFrame === null && total > 0 && len(v, end) <= total * 0.01) { out.settleFrame = Math.round(t * c.frameRate); }
            if (len(v, end) > total * 0.01) { out.settleFrame = null; }
            out.frames.push({ frame: Math.round(t * c.frameRate), value: v, speed: Math.round(sp * 100) / 100 });
            prev = v;
        }
        out.overshoot = total > 0 ? Math.round(maxPast / total * 1000) / 10 : 0; // percent of the travel
        out.travel = total;
        return out;
    }
    // linearKeys(comp): properties whose keys are still linear in time (the usual sign of unfinished motion)
    function linearKeys(c) {
        var out = [], i, l;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            AEK.core.walk(l, function (p) {
                var k, lin = 0;
                if (p.propertyType !== PropertyType.PROPERTY) { return; }
                try { if (p.numKeys < 2) { return; } } catch (e) { return; }
                for (k = 1; k <= p.numKeys; k++) { if (p.keyOutInterpolationType(k) === KeyframeInterpolationType.LINEAR && p.keyInInterpolationType(k) === KeyframeInterpolationType.LINEAR) { lin++; } }
                if (lin) { out.push({ layer: l.name, property: p.name, matchName: p.matchName, keys: p.numKeys, linear: lin }); }
            });
        }
        return out;
    }
    return { key: key, ease: ease, bezier: bezier, keys: keys, sample: sample, linearKeys: linearKeys };
})();
