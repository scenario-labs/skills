// motion_report.jsx: read-only motion review of one comp. Job for ae.py run, with --lib animation.jsx.
// ARGS: {comp: "Name", props: ["ADBE Position", "ADBE Scale", "ADBE Rotate Z"] (optional), open: "/abs/project.aep" (tests only)}
// Returns, per animated transform property: key frames and eases, peak speed (per frame), peak frame, overshoot %, settle frame;
// plus the motion check findings and the comp's motion blur settings.
if (ARGS.open) { AEK.core.open(ARGS.open); }   // tests only: closes the open project without saving first
var c = AEK.core.comp(ARGS.comp), out = { comp: c.name, fps: c.frameRate, layers: [] }, i, j, ps, p, s;
var want = ARGS.props || ["ADBE Position", "ADBE Scale", "ADBE Rotate Z", "ADBE Opacity"];
// separated X and Y followers carry their own match names: anything starting with "ADBE Position" counts as Position
function wanted(mn) { for (var q = 0; q < want.length; q++) { if (want[q] === mn || (want[q] === "ADBE Position" && /^ADBE Position/.test(mn))) { return true; } } return false; }
for (i = 1; i <= c.numLayers; i++) {
    ps = AEX.animation.animatedProps(c.layer(i));
    var L = { layer: c.layer(i).name, parent: c.layer(i).parent ? c.layer(i).parent.name : null, motionBlur: c.layer(i).motionBlur, props: [] };
    for (j = 0; j < ps.length; j++) {
        p = ps[j];
        if (!wanted(p.matchName) || p.numKeys < 2) { continue; }
        s = AEK.motion.sample(p, c, p.keyTime(1), p.keyTime(p.numKeys));
        var ks = AEK.motion.keys(p, c), frames = [], k;
        for (k = 0; k < ks.length; k++) { frames.push(ks[k].frame + " " + ks[k].inType.charAt(0) + "/" + ks[k].outType.charAt(0) + " in " + Math.round(ks[k].inInfluence) + " out " + Math.round(ks[k].outInfluence)); }
        L.props.push({ property: p.matchName, keys: frames, peakPerFrame: Math.round(s.peakSpeed / c.frameRate * 10) / 10, peakFrame: s.peakFrame, overshootPct: s.overshoot, settleFrame: s.settleFrame });
    }
    if (L.props.length) { out.layers.push(L); }
}
out.check = AEX.animation.motionCheck(c);
out.blur = { on: c.motionBlur, angle: c.shutterAngle, phase: c.shutterPhase, samples: c.motionBlurSamplesPerFrame, adaptiveLimit: c.motionBlurAdaptiveSampleLimit };
return out;
