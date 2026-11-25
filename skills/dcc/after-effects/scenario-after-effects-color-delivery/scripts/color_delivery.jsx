// AEX.delivery: color settings, multi-output renders and safe-area checks for After Effects 27.0 (ExtendScript ES3).
// Load with: ae.py run job.jsx --lib <this file>. Needs the AEK kit.
var AEX = AEX || {};
AEX.delivery = (function () {
    var CMS = { adobe: 0, ocio: 1 };   // the ColorManagementSystem enum is undefined on 27.0: use the numbers
    // state(): every project color field in one object
    function state() {
        var p = app.project;
        return { bpc: p.bitsPerChannel, workingSpace: p.workingSpace, workingGamma: p.workingGamma, linearize: p.linearizeWorkingSpace,
            linearBlending: p.linearBlending, compensateSceneReferred: p.compensateForSceneReferredProfiles,
            engine: p.colorManagementSystem === 1 ? "ocio" : "adobe", ocioConfig: p.ocioConfigurationFile };
    }
    function hasProfile(name) {
        var l = app.project.listColorProfiles(), i;
        for (i = 0; i < l.length; i++) { if (l[i] === name) { return true; } }
        return false;
    }
    // setColor({bpc, workingSpace, linearize, linearBlending, gamma, engine: "adobe"|"ocio", ocioConfig}): sets, reads back, throws on any mismatch.
    // An unknown workingSpace name silently becomes "None" (color management off): the name is checked against listColorProfiles() first.
    function setColor(s) {
        var p = app.project, got, bad = [];
        if (s.engine) { p.colorManagementSystem = CMS[s.engine]; }
        if (s.ocioConfig) { p.ocioConfigurationFile = s.ocioConfig; }   // throws "Invalid ocio configuration used." on a wrong name
        // OCIO mode refuses 16 bpc ("Not supported for OCIO color managed mode") and accepts 8 and 32; a new project can inherit OCIO
        if (s.bpc === 16 && p.colorManagementSystem === 1) { throw new Error("Project is OCIO color managed (16 bpc refused): pass engine: \"adobe\" for 16 bpc, or 32 bpc"); }
        if (s.bpc) { p.bitsPerChannel = s.bpc; }
        if (s.workingSpace !== undefined) {
            if (s.workingSpace !== "" && s.workingSpace !== "None" && !hasProfile(s.workingSpace)) { throw new Error("Unknown working space '" + s.workingSpace + "': pick a name from listColorProfiles()"); }
            p.workingSpace = s.workingSpace === "None" ? "" : s.workingSpace;
        }
        if (s.linearize !== undefined) { p.linearizeWorkingSpace = s.linearize; }
        if (s.linearBlending !== undefined) { p.linearBlending = s.linearBlending; }
        if (s.gamma) { p.workingGamma = s.gamma; }
        got = state();
        if (s.bpc && got.bpc !== s.bpc) { bad.push("bpc " + got.bpc); }
        if (s.workingSpace && s.workingSpace !== "None" && got.workingSpace !== s.workingSpace) { bad.push("workingSpace " + got.workingSpace); }
        if (s.linearize !== undefined && got.linearize !== s.linearize) { bad.push("linearize " + got.linearize); }
        if (s.engine && got.engine !== s.engine) { bad.push("engine " + got.engine); }
        if (bad.length) { throw new Error("setColor did not hold: " + bad.join(", ")); }
        return got;
    }
    function templateExists(om, name) {
        for (var i = 0; i < om.templates.length; i++) { if (om.templates[i] === name) { return true; } }
        return false;
    }
    // omSummary(om): the fields that decide a deliverable (Format, Channels, Depth, Color are read-only for setSettings on 27.0)
    function omSummary(om) {
        var s = om.getSettings(GetSettingsFormat.STRING);
        return { file: om.file ? om.file.fsName : "", format: s.Format, channels: s.Channels, depth: s.Depth, color: s.Color,
            audio: s["Output Audio"], audioRate: s["Audio Sample Rate"], resize: s.Resize, crop: s.Crop, startNumber: s["Starting #"], useCompFrame: s["Use Comp Frame Number"] };
    }
    // render(comp, [{template, file, audio: "On"|"Off"|"Auto"}], {rs, start, duration, mfr, keep, allowProxies}): one render item, one output module per entry.
    // The comp renders once and every file is written from that pass. Other queued items are switched off for the run and back on after.
    function render(c, outputs, o) {
        o = o || {};
        var rq = app.project.renderQueue, held = [], i, rqi, om, f, rs, res = { modules: [] }, t0;
        for (i = 1; i <= rq.numItems; i++) { if (rq.item(i).status === RQItemStatus.QUEUED) { rq.item(i).render = false; held.push(i); } }
        rqi = rq.items.add(c);
        try {
            rqi.applyTemplate(o.rs || "Best Settings");
            rqi.timeSpanStart = o.start !== undefined ? o.start : 0;
            rqi.timeSpanDuration = o.duration !== undefined ? o.duration : c.duration;
            rs = rqi.getSettings(GetSettingsFormat.STRING);
            res.renderSettings = { quality: rs.Quality, resolution: rs.Resolution, proxyUse: rs["Proxy Use"], colorDepth: rs["Color Depth"] };
            // finals never render proxies: Best Settings reads "Use No Proxies"; pass allowProxies only for a draft
            if (!o.allowProxies && res.renderSettings.proxyUse !== "Use No Proxies") { throw new Error("Render settings use proxies (" + res.renderSettings.proxyUse + "): use Best Settings for finals"); }
            for (i = 0; i < outputs.length; i++) {
                om = (i === 0) ? rqi.outputModule(1) : rqi.outputModules.add();
                if (!templateExists(om, outputs[i].template)) { throw new Error("Output module template not found: '" + outputs[i].template + "'"); }
                om.applyTemplate(outputs[i].template);
                if (outputs[i].audio) { om.setSettings({ "Output Audio": outputs[i].audio }); }
                f = new File(outputs[i].file);
                AEK.core.ensureFolder(f.parent.fsName);   // render() throws "Directory does not exist" otherwise
                om.file = f;
                res.modules.push(omSummary(om));
            }
            if (o.mfr !== undefined) { app.setMultiFrameRenderingConfig(o.mfr > 0, o.mfr > 0 ? o.mfr : 100); }
            t0 = (new Date()).getTime();
            rq.render();
            res.ms = (new Date()).getTime() - t0;
            res.status = AEK.core.enumName(RQItemStatus, rqi.status);
            for (i = 1; i <= rqi.numOutputModules; i++) { res.modules[i - 1].written = rqi.outputModule(i).file ? rqi.outputModule(i).file.fsName : ""; }
        } finally {
            if (!o.keep) { try { rqi.remove(); } catch (e) {} }
            for (i = 0; i < held.length; i++) { try { rq.item(held[i]).render = true; } catch (e2) {} }
        }
        if (res.status !== "DONE") { throw new Error("Render ended " + res.status); }
        return res;
    }
    // saveTemplate(comp, baseTemplate, name, {audio}): stores the current output module as a template name for aerender -OMtemplate.
    // Only fields setSettings can change (audio, resize, crop, file naming, post-render action) differ from the base template.
    function saveTemplate(c, base, name, s) {
        var rqi = app.project.renderQueue.items.add(c), om = rqi.outputModule(1), out;
        try {
            om.applyTemplate(base);
            if (s) { om.setSettings(s); }
            om.saveAsTemplate(name);
            out = { name: name, listed: templateExists(om, name), summary: omSummary(om) };
        } finally { rqi.remove(); }
        return out;
    }
    // margins(comp, pct): one inset per side as a fraction of width and height (pct 0.05 = 5 % each side, a 90 % box)
    function box(c, m) {
        var l = m.left !== undefined ? m.left : m.all, r = m.right !== undefined ? m.right : m.all;
        var t = m.top !== undefined ? m.top : m.all, b = m.bottom !== undefined ? m.bottom : m.all;
        return [c.width * l, c.height * t, c.width * (1 - r), c.height * (1 - b)];
    }
    // bounds(layer, t): comp-space box of an unrotated 2D layer from sourceRectAtTime, scale, anchor and position (parents ignored)
    function bounds(l, t) {
        var r = l.sourceRectAtTime(t, false), tr = l.property("ADBE Transform Group");
        var a = tr.property("ADBE Anchor Point").valueAtTime(t, false), s = tr.property("ADBE Scale").valueAtTime(t, false), p = tr.property("ADBE Position").valueAtTime(t, false);
        var x1 = p[0] + (r.left - a[0]) * s[0] / 100, y1 = p[1] + (r.top - a[1]) * s[1] / 100;
        var x2 = p[0] + (r.left + r.width - a[0]) * s[0] / 100, y2 = p[1] + (r.top + r.height - a[1]) * s[1] / 100;
        return [Math.min(x1, x2), Math.min(y1, y2), Math.max(x1, x2), Math.max(y1, y2)];
    }
    // safeCheck(comp, margins, times, test): every enabled text layer (or layers where test(layer) is true) inside the box at each time
    function safeCheck(c, m, times, test) {
        var bx = box(c, m), out = [], i, j, l, b, ok;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!l.enabled || l.guideLayer) { continue; }
            if (test ? !test(l) : !(l instanceof TextLayer)) { continue; }
            for (j = 0; j < times.length; j++) {
                if (times[j] < l.inPoint || times[j] >= l.outPoint) { continue; }
                b = bounds(l, times[j]);
                ok = b[0] >= bx[0] - 0.5 && b[1] >= bx[1] - 0.5 && b[2] <= bx[2] + 0.5 && b[3] <= bx[3] + 0.5;
                out.push({ layer: l.name, t: times[j], ok: ok, bounds: [Math.round(b[0]), Math.round(b[1]), Math.round(b[2]), Math.round(b[3])], box: [Math.round(bx[0]), Math.round(bx[1]), Math.round(bx[2]), Math.round(bx[3])] });
            }
        }
        return out;
    }
    // guides(comp, [{name, margins, color}]): one guide shape layer with a rectangle per safe box; guide layers do not render
    function guides(c, list) {
        var l = c.layers.addShape(), i, g, bx, w, h;
        l.name = "SAFE_GUIDES";
        for (i = 0; i < list.length; i++) {
            bx = box(c, list[i].margins); w = bx[2] - bx[0]; h = bx[3] - bx[1];
            AEK.build.shapeGroup(l, { type: "rect", name: list[i].name, size: [w, h], position: [bx[0] + w / 2 - c.width / 2, bx[1] + h / 2 - c.height / 2], fill: null, stroke: { color: list[i].color || [1, 0, 0], width: 2 } });
        }
        l.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
        l.guideLayer = true;
        return l;
    }
    return { CMS: CMS, state: state, hasProfile: hasProfile, setColor: setColor, templateExists: templateExists, omSummary: omSummary,
        render: render, saveTemplate: saveTemplate, box: box, bounds: bounds, safeCheck: safeCheck, guides: guides };
})();
