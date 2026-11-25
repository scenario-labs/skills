// aekit/text.jsx: text layers, measurement, fitting, animators. Requires core.jsx.
var AEK = AEK || {};
AEK.text = (function () {
    var JUST = { left: ParagraphJustification.LEFT_JUSTIFY, center: ParagraphJustification.CENTER_JUSTIFY, right: ParagraphJustification.RIGHT_JUSTIFY };
    function src(l) { return l.property("ADBE Text Properties").property("ADBE Text Document"); }
    // fontExists(postScriptName): fonts are addressed by PostScript name ("Inter-Bold"), never by display name
    function fontExists(ps) {
        // After a project that names a missing font is reopened, the lookup returns a stand-in object: isSubstitute tells it apart.
        try { var f = app.fonts.getFontsByPostScriptName(ps); if (!(f && f.length)) { return false; } return f[0].isSubstitute !== true; } catch (e) { return null; }
    }
    // style(layer, {font, size, fill:[r,g,b], stroke:[r,g,b], strokeWidth, tracking, leading, justify, allCaps, text})
    function style(l, o) {
        var p = src(l), d = p.value;
        // a missing font is accepted silently and substituted at render time: check before writing
        if (o.font && fontExists(o.font) === false) { throw new Error("Font '" + o.font + "' is not installed (use the PostScript name, for example 'Helvetica-Bold')"); }
        if (o.text !== undefined) { d.text = o.text; }
        if (o.font) { d.font = o.font; }
        if (o.size) { d.fontSize = o.size; }
        if (o.fill) { d.applyFill = true; d.fillColor = o.fill; }
        if (o.stroke) { d.applyStroke = true; d.strokeColor = o.stroke; d.strokeWidth = o.strokeWidth || 2; }
        if (o.tracking !== undefined) { d.tracking = o.tracking; }
        if (o.leading !== undefined) { d.leading = o.leading; }
        if (o.justify) { d.justification = JUST[o.justify]; }
        if (o.allCaps !== undefined) { d.allCaps = o.allCaps; }
        p.setValue(d);
        d = p.value;
        return { text: d.text, font: d.font, size: d.fontSize, tracking: d.tracking, leading: d.leading };
    }
    // add(comp, "text", {..style.., box:[w,h], position:[x,y], name})
    function add(c, string, o) {
        o = o || {};
        var l = o.box ? c.layers.addBoxText(o.box, string) : c.layers.addText(string);
        if (o.name) { l.name = o.name; }
        style(l, o);
        if (o.position) { l.property("ADBE Transform Group").property("ADBE Position").setValue(o.position); }
        return l;
    }
    // measure(layer, t): bounds in layer space and in comp space (2D, parents and rotation included through toComp-free math: scale and position only)
    function measure(l, t) {
        var r = l.sourceRectAtTime(t || 0, false), tg = l.property("ADBE Transform Group");
        var a = tg.property("ADBE Anchor Point").valueAtTime(t || 0, false), p = tg.property("ADBE Position").valueAtTime(t || 0, false), s = tg.property("ADBE Scale").valueAtTime(t || 0, false);
        var left = p[0] + (r.left - a[0]) * s[0] / 100, top = p[1] + (r.top - a[1]) * s[1] / 100;
        return { left: r.left, top: r.top, width: r.width, height: r.height,
            comp: { left: left, top: top, right: left + r.width * s[0] / 100, bottom: top + r.height * s[1] / 100, width: r.width * s[0] / 100, height: r.height * s[1] / 100 } };
    }
    // fit(layer, maxWidth, {minSize, step}): shrinks the font size until the line fits. Returns the size used and whether it still overflows.
    function fit(l, maxWidth, o) {
        o = o || {};
        var p = src(l), d = p.value, size = d.fontSize, min = o.minSize || 12, step = o.step || 1, w = measure(l, 0).comp.width, start = size;
        while (w > maxWidth && size - step >= min) { size -= step; d = p.value; d.fontSize = size; p.setValue(d); w = measure(l, 0).comp.width; }
        return { from: start, size: size, width: w, maxWidth: maxWidth, overflow: w > maxWidth };
    }
    // inFrame(layer, comp, margin, t): is the text inside the comp minus a margin (fraction of the frame, 0.05 = 5 %)
    function inFrame(l, c, margin, t) {
        var m = measure(l, t).comp, mx = c.width * (margin || 0), my = c.height * (margin || 0);
        return { ok: m.left >= mx && m.top >= my && m.right <= c.width - mx && m.bottom <= c.height - my, bounds: m, safe: [mx, my, c.width - mx, c.height - my] };
    }
    var PROPS = { opacity: "ADBE Text Opacity", position: "ADBE Text Position 3D", scale: "ADBE Text Scale 3D", rotation: "ADBE Text Rotation",
        anchor: "ADBE Text Anchor Point 3D", skew: "ADBE Text Skew", tracking: "ADBE Text Tracking Amount", fillColor: "ADBE Text Fill Color",
        strokeColor: "ADBE Text Stroke Color", strokeWidth: "ADBE Text Stroke Width", blur: "ADBE Text Blur", lineSpacing: "ADBE Text Line Spacing" };
    var BASED = { characters: 1, charactersExcludingSpaces: 2, words: 3, lines: 4 };
    var SHAPE = { square: 1, rampUp: 2, rampDown: 3, triangle: 4, round: 5, smooth: 6 };
    // animator(layer, {name, properties:{opacity:0, position:[0,40], ...}, basedOn, shape, easeHigh, easeLow, start, end, offset, units:"percent"|"index", randomize})
    // Animator values are OFFSETS from the base style; the selector decides which characters get them.
    function animator(l, o) {
        var anims = l.property("ADBE Text Properties").property("ADBE Text Animators"), a = anims.addProperty("ADBE Text Animator"), idx = a.propertyIndex, k, p, sel, adv, pre;
        function A() { return l.property("ADBE Text Properties").property("ADBE Text Animators").property(idx); }
        if (o.name) { A().name = o.name; }
        for (k in o.properties) {
            if (!o.properties.hasOwnProperty(k)) { continue; }
            if (!PROPS[k]) { throw new Error("animator(): unknown property '" + k + "'"); }
            p = A().property("ADBE Text Animator Properties").addProperty(PROPS[k]);
            A().property("ADBE Text Animator Properties").property(PROPS[k]).setValue(o.properties[k]);
        }
        A().property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel = function () { return A().property("ADBE Text Selectors").property(1); };
        adv = function () { return sel().property("ADBE Text Range Advanced"); };
        if (o.units === "index") { adv().property("ADBE Text Range Units").setValue(2); }
        if (o.basedOn) { adv().property("ADBE Text Range Type2").setValue(BASED[o.basedOn]); }
        if (o.shape) { adv().property("ADBE Text Range Shape").setValue(SHAPE[o.shape]); }
        if (o.easeHigh !== undefined) { adv().property("ADBE Text Levels Max Ease").setValue(o.easeHigh); }
        if (o.easeLow !== undefined) { adv().property("ADBE Text Levels Min Ease").setValue(o.easeLow); }
        if (o.randomize) { adv().property("ADBE Text Randomize Order").setValue(1); }
        pre = (o.units === "index") ? "ADBE Text Index " : "ADBE Text Percent ";
        if (o.start !== undefined) { sel().property(pre + "Start").setValue(o.start); }
        if (o.end !== undefined) { sel().property(pre + "End").setValue(o.end); }
        if (o.offset !== undefined) { sel().property(pre + "Offset").setValue(o.offset); }
        return { animatorIndex: idx, offset: sel().property(pre + "Offset"), start: sel().property(pre + "Start"), end: sel().property(pre + "End") };
    }
    return { add: add, style: style, measure: measure, fit: fit, inFrame: inFrame, animator: animator, fontExists: fontExists };
})();
