// aekit/audit.jsx: read-only project checks. Each finding: {severity, rule, where, message}. Requires core.jsx.
var AEK = AEK || {};
AEK.audit = (function () {
    function F(list, severity, rule, where, message) { list.push({ severity: severity, rule: rule, where: where, message: message }); }
    function project(out) {
        var p = app.project;
        if (!p.file) { F(out, "warn", "project.unsaved", "project", "Project has never been saved"); }
        if (p.bitsPerChannel === 8) { F(out, "info", "project.bpc", "project", "8 bpc: gradients, glows and grades band; use 16 bpc for finishing, 32 bpc for linear or HDR work"); }
        if (String(p.workingSpace) === "None" || p.workingSpace === "") { F(out, "info", "project.workingSpace", "project", "No working color space: color management is off"); }
        if (p.expressionEngine !== "javascript-1.0") { F(out, "warn", "project.expressionEngine", "project", "Expression engine is '" + p.expressionEngine + "' (Legacy ExtendScript): slower, old syntax"); }
    }
    function footage(out) {
        var i, it, used, path;
        for (i = 1; i <= app.project.numItems; i++) {
            it = app.project.item(i);
            if (!(it instanceof FootageItem)) { continue; }
            if (it.footageMissing) { F(out, "error", "footage.missing", it.name, "Missing footage" + (it.file ? ": " + it.file.fsName : "")); }
            used = 0; try { used = it.usedIn.length; } catch (e) {}
            if (used === 0 && !(it.mainSource instanceof SolidSource)) { F(out, "info", "footage.unused", it.name, "Not used in any comp"); }
            if (it.file) {
                path = it.file.fsName;
                if (/\/(Dropbox|Google Drive|GoogleDrive|OneDrive|iCloud Drive|CloudStorage|Mobile Documents)\//i.test(path)) {
                    F(out, "info", "footage.cloud", it.name, "Source sits in a cloud-synced folder: slow reads, possible offline placeholders (" + path + ")");
                }
            }
        }
    }
    function compsAudit(out) {
        var all = AEK.core.comps(), rates = {}, i, c, k, n = 0, list = [];
        for (i = 0; i < all.length; i++) {
            c = all[i];
            rates[String(Math.round(c.frameRate * 1000) / 1000)] = (rates[String(Math.round(c.frameRate * 1000) / 1000)] || 0) + 1;
            if (/^(Comp|Pre-comp|Composition) \d+$/i.test(c.name)) { F(out, "warn", "comp.defaultName", c.name, "Default comp name"); }
            if (c.usedIn.length === 0 && c.numLayers === 0) { F(out, "info", "comp.empty", c.name, "Empty comp, used nowhere"); }
            if (c.width % 2 || c.height % 2) { F(out, "warn", "comp.oddSize", c.name, c.width + "x" + c.height + ": H.264 and HEVC need even dimensions"); }
            layers(out, c);
        }
        for (k in rates) { if (rates.hasOwnProperty(k)) { n++; list.push(k + " fps x" + rates[k]); } }
        if (n > 1) { F(out, "warn", "comp.mixedFrameRates", "project", "Comps use " + n + " frame rates: " + list.join(", ")); }
    }
    function layers(out, c) {
        var i, l, where, src, fx, j, e;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            where = c.name + " > " + i + " " + l.name;
            src = null; try { src = l.source; } catch (e0) {}
            if (src instanceof FootageItem && src.hasVideo && !src.mainSource.isStill && src.frameRate &&
                Math.abs(src.frameRate - c.frameRate) > 0.01 && !(src.mainSource instanceof SolidSource)) {
                F(out, "warn", "layer.frameRateMismatch", where, "Footage " + (Math.round(src.frameRate * 1000) / 1000) + " fps in a " + c.frameRate + " fps comp");
            }
            if (src instanceof CompItem && Math.abs(src.frameRate - c.frameRate) > 0.01) {
                F(out, "warn", "layer.nestedFrameRate", where, "Nested comp at " + (Math.round(src.frameRate * 1000) / 1000) + " fps in a " + c.frameRate + " fps comp");
            }
            if (src instanceof FootageItem && src.hasVideo && src.width && l.matchName === "ADBE AV Layer" && !(src.mainSource instanceof SolidSource)) {
                try {
                    var sc = l.property("ADBE Transform Group").property("ADBE Scale").value;
                    if (l.enabled && !l.threeDLayer && (sc[0] > 105 || sc[1] > 105)) { F(out, "warn", "layer.upscaled", where, "Scaled to " + Math.round(sc[0]) + "%: footage is enlarged past its pixels"); }
                } catch (e1) {}
            }
            fx = null; try { fx = l.property("ADBE Effect Parade"); } catch (e2) {}
            if (fx) {
                for (j = 1; j <= fx.numProperties; j++) {
                    e = fx.property(j);
                    if (!e.isEffect || /^Missing:/i.test(e.name) || e.matchName === "") { F(out, "error", "effect.missing", where, "Effect not installed: " + e.name + " [" + e.matchName + "]"); }
                }
            }
            AEK.core.walk(l, function (p) {
                if (p.propertyType !== PropertyType.PROPERTY) { return; }
                var ex = ""; try { if (p.canSetExpression) { ex = p.expression; } } catch (e3) { return; }
                if (ex === "") { return; }
                if (p.expressionError !== "") { F(out, "error", "expression.error", where + " > " + p.name, p.expressionError.replace(/\s+/g, " ").substring(0, 220)); }
                else if (!p.expressionEnabled) { F(out, "warn", "expression.disabled", where + " > " + p.name, "Expression is switched off"); }
            });
        }
    }
    function fonts(out) {
        // 1) what each text layer asks for now; 2) what the application flagged when the project was opened or edited.
        // The application list is not cleared when a font is replaced in the same session, so it only adds a warning.
        var all = AEK.core.comps(), i, j, l, f, used = {}, missing = null, a = [], name;
        for (i = 0; i < all.length; i++) {
            for (j = 1; j <= all[i].numLayers; j++) {
                l = all[i].layer(j);
                if (l.matchName !== "ADBE Text Layer") { continue; }
                try { f = l.property("ADBE Text Properties").property("ADBE Text Document").value.font; } catch (e0) { continue; }
                used[f] = true;
                try {
                    // After a project is reopened the lookup returns a stand-in font object: isSubstitute tells it apart.
                    var hits = app.fonts.getFontsByPostScriptName(f), sub = false;
                    try { sub = hits.length > 0 && hits[0].isSubstitute === true; } catch (e3) {}
                    if (!hits.length || sub) { F(out, "error", "fonts.missing", all[i].name + " > " + j + " " + l.name, "Font not installed: " + f); }
                } catch (e1) {}
            }
        }
        try { missing = app.fonts.missingOrSubstitutedFonts; } catch (e) { return; }
        if (!missing) { return; }
        for (i = 0; i < missing.length; i++) {
            name = ""; try { name = missing[i].postScriptName || String(missing[i]); } catch (e2) {}
            if (name && !used[name]) { a.push(name); }
        }
        if (a.length) { F(out, "warn", "fonts.flagged", "project", "Flagged as missing or substituted by the application, not found on the first style of any text layer (later style runs, or already replaced): " + a.join(", ")); }
    }
    function all() {
        var out = [];
        project(out); footage(out); compsAudit(out); fonts(out);
        return out;
    }
    function summary(findings) {
        var s = { error: 0, warn: 0, info: 0 }, i;
        for (i = 0; i < findings.length; i++) { s[findings[i].severity]++; }
        return s;
    }
    return { all: all, summary: summary, project: function () { var o = []; project(o); return o; },
        footage: function () { var o = []; footage(o); return o; }, comps: function () { var o = []; compsAudit(o); return o; },
        comp: function (c) { var o = []; layers(o, c); return o; }, fonts: function () { var o = []; fonts(o); return o; } };
})();
