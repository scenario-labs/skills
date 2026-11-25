// aekit/capture.jsx: frames and renders to look at. Requires core.jsx. All paths absolute.
var AEK = AEK || {};
AEK.capture = (function () {
    // frame(): comp.saveFrameToPng is asynchronous. The file appears after the call returns, so poll for it.
    function frame(c, seconds, path, timeoutMs) {
        var f = AEK.core.abs(path), waited = 0, limit = timeoutMs || 60000;
        if (f.exists) { f.remove(); }
        AEK.core.ensureFolder(f.parent.fsName);
        c.saveFrameToPng(seconds, f);
        while (!f.exists && waited < limit) { $.sleep(100); waited += 100; }
        if (!f.exists) { throw new Error("Frame not written after " + limit + " ms: " + path); }
        $.sleep(150);
        // At 32 bpc saveFrameToPng writes every value divided by 10 (white is 0.1): pngScale tells the reader. ae.py sheet --gain 10 shows it right.
        var bpc = app.project.bitsPerChannel;
        return { path: f.fsName, time: seconds, frame: Math.round(seconds * c.frameRate), waitedMs: waited, bpc: bpc, pngScale: bpc === 32 ? 0.1 : 1 };
    }
    function statusName(s) {
        var names = ["WILL_CONTINUE", "NEEDS_OUTPUT", "UNQUEUED", "QUEUED", "RENDERING", "USER_STOPPED", "ERR_STOPPED", "DONE"], i;
        for (i = 0; i < names.length; i++) { if (s === RQItemStatus[names[i]]) { return names[i]; } }
        return String(s);
    }
    // frames(comp, [seconds...], dir, prefix): one PNG per time, named <prefix>_f<frame>.png
    function frames(c, times, dir, prefix) {
        var out = [], i, fr, name;
        for (i = 0; i < times.length; i++) {
            fr = Math.round(times[i] * c.frameRate);
            name = (prefix || c.name.replace(/[^\w\-]+/g, "_")) + "_f" + ("00000" + fr).slice(-5) + ".png";
            out.push(frame(c, times[i], dir + "/" + name));
        }
        return out;
    }
    // spread(comp, n, dir): n frames evenly spread over the work area, never the very last frame
    function spread(c, n, dir, prefix) {
        var times = [], i, start = c.workAreaStart, dur = c.workAreaDuration - c.frameDuration;
        for (i = 0; i < n; i++) { times.push(start + (n === 1 ? 0 : dur * i / (n - 1))); }
        return frames(c, times, dir, prefix);
    }
    // queue(): render through the render queue. Blocks until done. opts: {template, renderSettings, start, duration}
    function queue(c, path, opts) {
        opts = opts || {};
        var f = AEK.core.abs(path), rq = app.project.renderQueue, rqi, om, t0 = (new Date()).getTime(), i, status;
        AEK.core.ensureFolder(f.parent.fsName);
        var held = [];   // the person's own queued items: switched off for this render, switched back on after it
        for (i = 1; i <= rq.numItems; i++) { if (rq.item(i).status === RQItemStatus.QUEUED) { rq.item(i).render = false; held.push(i); } }
        rqi = rq.items.add(c);
        if (opts.renderSettings) { rqi.applyTemplate(opts.renderSettings); }
        if (opts.start !== undefined) { rqi.timeSpanStart = opts.start; }
        if (opts.duration !== undefined) { rqi.timeSpanDuration = opts.duration; }
        om = rqi.outputModule(1);
        if (opts.template) { om.applyTemplate(opts.template); }
        om.file = f;
        rq.render();
        status = rqi.status;
        var res = { path: om.file ? om.file.fsName : f.fsName, done: status === RQItemStatus.DONE, status: statusName(status),
            ms: (new Date()).getTime() - t0, template: opts.template || "", frames: Math.round(rqi.timeSpanDuration * c.frameRate) };
        rqi.remove();
        for (i = 0; i < held.length; i++) { try { rq.item(held[i]).render = true; } catch (e) {} }
        if (!res.done) { throw new Error("Render did not finish (status " + res.status + ") for " + path); }
        return res;
    }
    function templates(c) {
        var rq = app.project.renderQueue, rqi = rq.items.add(c), om = rqi.outputModule(1), a = [], b = [], i;
        for (i = 0; i < om.templates.length; i++) { if (om.templates[i].indexOf("_HIDDEN") !== 0) { a.push(om.templates[i]); } }
        for (i = 0; i < rqi.templates.length; i++) { if (rqi.templates[i].indexOf("_HIDDEN") !== 0) { b.push(rqi.templates[i]); } }
        rqi.remove();
        return { outputModule: a, renderSettings: b };
    }
    return { frame: frame, frames: frames, spread: spread, queue: queue, templates: templates };
})();
