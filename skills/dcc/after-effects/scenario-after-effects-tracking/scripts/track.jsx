// track.jsx: apply tracking data computed outside After Effects (ES3). Load with: ae.py run job.jsx --lib track.jsx
// Corner lists are [UL, UR, LR, LL] per frame (clockwise, as track_external.py writes them).
// Corner Pin's own order is UL, UR, LL, LR (ADBE Corner Pin-0001..0004): the helpers map it.
var AEX = AEX || {};
AEX.track = (function () {
    function times(c, n, startFrame) {
        var t = [], i;
        for (i = 0; i < n; i++) { t.push((startFrame + i) / c.frameRate); }
        return t;
    }
    function col(rows, k) { var o = [], i; for (i = 0; i < rows.length; i++) { o.push(rows[i][k]); } return o; }

    // cornerPin(layer, corners, {startFrame, motionBlur}): Corner Pin keys on every frame. The layer is set to
    // anchor [0,0], position [0,0], scale 100 so layer pixels equal comp pixels (2D layers only).
    // motionBlur: true writes the centroid motion on Position and pins relative to it, because layer motion
    // blur does not blur a Corner Pin deformation.
    function cornerPin(l, corners, o) {
        o = o || {};
        var c = l.containingComp, sf = o.startFrame || 0, t = times(c, corners.length, sf), tg = l.property("ADBE Transform Group");
        var fxp = l.property("ADBE Effect Parade"), fx = fxp.addProperty("ADBE Corner Pin"), idx = fx.propertyIndex, i, k;
        var cen = [], rel = [[], [], [], []], order = [0, 1, 3, 2], cx, cy, a0;
        for (i = 0; i < corners.length; i++) {
            cx = (corners[i][0][0] + corners[i][1][0] + corners[i][2][0] + corners[i][3][0]) / 4;
            cy = (corners[i][0][1] + corners[i][1][1] + corners[i][2][1] + corners[i][3][1]) / 4;
            cen.push([cx, cy]);
        }
        a0 = o.motionBlur ? [cen[0][0], cen[0][1]] : [0, 0];
        tg.property("ADBE Anchor Point").setValue(a0);
        tg.property("ADBE Scale").setValue([100, 100]);
        tg.property("ADBE Rotate Z").setValue(0);
        if (o.motionBlur) { tg.property("ADBE Position").setValuesAtTimes(t, cen); } else { tg.property("ADBE Position").setValue([0, 0]); }
        for (k = 0; k < 4; k++) {
            for (i = 0; i < corners.length; i++) {
                var p = corners[i][order[k]];
                rel[k].push(o.motionBlur ? [p[0] - cen[i][0] + a0[0], p[1] - cen[i][1] + a0[1]] : [p[0], p[1]]);
            }
            l.property("ADBE Effect Parade").property(idx).property(k + 1).setValuesAtTimes(t, rel[k]);
        }
        if (o.motionBlur) { l.motionBlur = true; c.motionBlur = true; }
        return l.property("ADBE Effect Parade").property(idx);
    }

    // readCorners(layer, effectIndex, n, startFrame): comp-space corners [UL, UR, LR, LL] per frame
    // (Position minus Anchor added back: valid for the unscaled, unrotated 2D layers cornerPin() sets up)
    function readCorners(l, idx, n, startFrame) {
        var c = l.containingComp, fx = l.property("ADBE Effect Parade").property(idx), tg = l.property("ADBE Transform Group"), out = [], i, k, t, p, ord = [1, 2, 4, 3], pos, an;
        for (i = 0; i < n; i++) {
            t = ((startFrame || 0) + i) / c.frameRate; p = [];
            pos = tg.property("ADBE Position").valueAtTime(t, false); an = tg.property("ADBE Anchor Point").valueAtTime(t, false);
            for (k = 0; k < 4; k++) {
                var v = fx.property(ord[k]).valueAtTime(t, false);
                p.push([v[0] + pos[0] - an[0], v[1] + pos[1] - an[1]]);
            }
            out.push(p);
        }
        return out;
    }

    // nullFromCorners(comp, corners, name, startFrame): a null carrying Position (centroid), Rotation (top edge
    // angle) and Scale (top edge length relative to the first frame) for layers parented to it.
    function nullFromCorners(c, corners, name, startFrame) {
        var n = c.layers.addNull(c.duration), tg, pos = [], rot = [], sc = [], i, dx, dy, len0, len, ang0, ang, prev = null, t;
        n.name = name || "track_null";
        for (i = 0; i < corners.length; i++) {
            var q = corners[i];
            pos.push([(q[0][0] + q[1][0] + q[2][0] + q[3][0]) / 4, (q[0][1] + q[1][1] + q[2][1] + q[3][1]) / 4]);
            dx = q[1][0] - q[0][0]; dy = q[1][1] - q[0][1]; len = Math.sqrt(dx * dx + dy * dy); ang = Math.atan2(dy, dx) * 180 / Math.PI;
            if (i === 0) { len0 = len; ang0 = ang; }
            ang = ang - ang0;
            if (prev !== null) { while (ang - prev > 180) { ang -= 360; } while (ang - prev < -180) { ang += 360; } }
            prev = ang; rot.push(ang); sc.push([100 * len / len0, 100 * len / len0]);
        }
        t = times(c, corners.length, startFrame || 0);
        tg = n.property("ADBE Transform Group");
        tg.property("ADBE Position").setValuesAtTimes(t, pos);
        tg.property("ADBE Rotate Z").setValuesAtTimes(t, rot);
        tg.property("ADBE Scale").setValuesAtTimes(t, sc);
        return n;
    }

    function rotate(v, deg) { var a = deg * Math.PI / 180; return [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)]; }

    // smoothPath(shake, window): two passes of a centered moving average (a triangle filter) over [dx, dy, rot].
    // One pass leaves visible jitter (measured 0.99 px vs 0.29 px second difference at 9 frames).
    function boxPass(s, w) {
        var out = [], i, j, h = Math.floor(w / 2), a, n, k;
        for (i = 0; i < s.length; i++) {
            a = [0, 0, 0]; n = 0;
            for (j = i - h; j <= i + h; j++) { if (j < 0 || j >= s.length) { continue; } for (k = 0; k < 3; k++) { a[k] += s[j][k]; } n++; }
            out.push([a[0] / n, a[1] / n, a[2] / n]);
        }
        return out;
    }
    function smoothPath(s, w) { return boxPass(boxPass(s, w), w); }

    // stabilize(layer, shake, {smooth, startFrame, margin}): counter-animates the footage layer.
    // shake[i] = [dx, dy, rot] of frame i (rot clockwise-positive). smooth = 0 locks the frame; smooth = N frames
    // removes only the motion that differs from an N-frame moving average (keeps the intended move).
    // Returns the uniform scale (percent) that hides every border, applied when o.autoScale is true.
    function stabilize(l, shake, o) {
        o = o || {};
        var c = l.containingComp, w = c.width, h = c.height, cc = [w / 2, h / 2], i, k, corr = [], s = 1, need;
        var base = o.smooth ? smoothPath(shake, o.smooth) : null;
        for (i = 0; i < shake.length; i++) {
            corr.push(base ? [shake[i][0] - base[i][0], shake[i][1] - base[i][1], shake[i][2] - base[i][2]] : shake[i]);
        }
        var qs = [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]];
        for (i = 0; i < corr.length; i++) {
            for (k = 0; k < 4; k++) {
                var r = rotate(qs[k], corr[i][2]);
                need = r[0] > 0 ? r[0] / (w / 2 - corr[i][0]) : -r[0] / (w / 2 + corr[i][0]); if (need > s) { s = need; }
                need = r[1] > 0 ? r[1] / (h / 2 - corr[i][1]) : -r[1] / (h / 2 + corr[i][1]); if (need > s) { s = need; }
            }
        }
        s = s * (1 + (o.margin || 0) / 100);
        var sc = o.autoScale ? s : 1, pos = [], rot = [], t = times(c, corr.length, o.startFrame || 0), tg = l.property("ADBE Transform Group");
        for (i = 0; i < corr.length; i++) {
            var d = rotate([corr[i][0], corr[i][1]], -corr[i][2]);
            pos.push([cc[0] - sc * d[0], cc[1] - sc * d[1]]);
            rot.push(-corr[i][2]);
        }
        tg.property("ADBE Anchor Point").setValue([l.source.width / 2, l.source.height / 2]);
        tg.property("ADBE Position").setValuesAtTimes(t, pos);
        tg.property("ADBE Rotate Z").setValuesAtTimes(t, rot);
        tg.property("ADBE Scale").setValue([100 * sc, 100 * sc]);
        return { scaleNeeded: Math.round(s * 10000) / 100, scaleApplied: Math.round(sc * 10000) / 100, frames: corr.length };
    }

    // reanchor(effect, frame, corrected, rampFrames, startFrame): drift fix. corrected = true corners [UL, UR, LR, LL]
    // at `frame` (from a re-track of that frame). The offset ramps in linearly over rampFrames before it and
    // holds after it. Keys keep their times; only values change.
    function reanchor(fx, frame, corrected, rampFrames, startFrame) {
        var l = fx.parentProperty.parentProperty, c = l.containingComp, ord = [1, 2, 4, 3], k, i, p, off, kt, f, wgt, v;
        // corrected corners are comp space; Corner Pin values are layer space (differ when Position carries the motion)
        var tg = l.property("ADBE Transform Group"), ft = frame / c.frameRate;
        var pos = tg.property("ADBE Position").valueAtTime(ft, false), an = tg.property("ADBE Anchor Point").valueAtTime(ft, false);
        for (k = 0; k < 4; k++) {
            p = fx.property(ord[k]);
            v = p.valueAtTime(ft, false);
            off = [corrected[k][0] - (pos[0] - an[0]) - v[0], corrected[k][1] - (pos[1] - an[1]) - v[1]];
            for (i = 1; i <= p.numKeys; i++) {
                kt = p.keyTime(i); f = Math.round(kt * c.frameRate);
                wgt = f >= frame ? 1 : (f <= frame - rampFrames ? 0 : (f - (frame - rampFrames)) / rampFrames);
                if (wgt > 0) { v = p.keyValue(i); p.setValueAtKey(i, [v[0] + off[0] * wgt, v[1] + off[1] * wgt]); }
            }
        }
        return fx;
    }

    // error(cornersA, cornersB): mean and max corner distance in px, and the worst frame
    function error(a, b) {
        var sum = 0, n = 0, mx = 0, worst = 0, wv = 0, i, k, d, fsum;
        for (i = 0; i < a.length && i < b.length; i++) {
            fsum = 0;
            for (k = 0; k < 4; k++) { d = Math.sqrt(Math.pow(a[i][k][0] - b[i][k][0], 2) + Math.pow(a[i][k][1] - b[i][k][1], 2)); fsum += d; if (d > mx) { mx = d; } }
            sum += fsum; n += 4; if (fsum / 4 > wv) { wv = fsum / 4; worst = i; }
        }
        return { meanPx: Math.round(sum / n * 1000) / 1000, maxPx: Math.round(mx * 1000) / 1000, worstFrame: worst };
    }

    // pointTracker(layer, name, points): creates a Motion Tracker with one track point per entry and writes
    // Feature Center / Attach Point keys. points: [{name, centers: [[x, y] per frame], startFrame}]
    function pointTracker(l, name, points) {
        var trs = l.property("ADBE MTrackers"), tr = trs.addProperty("ADBE MTracker"), ti = tr.propertyIndex, i, pt, pi, c = l.containingComp;
        l.property("ADBE MTrackers").property(ti).name = name || "Tracker 1";
        for (i = 0; i < points.length; i++) {
            pt = l.property("ADBE MTrackers").property(ti).addProperty("ADBE MTracker Pt"); pi = pt.propertyIndex;
            pt = l.property("ADBE MTrackers").property(ti).property(pi);
            pt.name = points[i].name || ("Track Point " + (i + 1));
            var t = times(c, points[i].centers.length, points[i].startFrame || 0);
            pt.property("ADBE MTracker Pt Feature Center").setValuesAtTimes(t, points[i].centers);
            pt.property("ADBE MTracker Pt Attach Pt").setValuesAtTimes(t, points[i].centers);
        }
        return l.property("ADBE MTrackers").property(ti);
    }

    return { cornerPin: cornerPin, readCorners: readCorners, nullFromCorners: nullFromCorners, smoothPath: smoothPath,
        stabilize: stabilize, reanchor: reanchor, error: error, pointTracker: pointTracker, col: col };
})();
