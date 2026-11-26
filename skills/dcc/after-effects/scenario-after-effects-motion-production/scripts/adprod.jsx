// adprod.jsx: AEX.ad, data-driven ad edits on top of AEK (core, build, text, motion, xio). ES3.
// Load with: ae.py run job.jsx --lib <skill>/scripts/adprod.jsx
// Layer names are the contract the checks read: SHOT_<id>, TXT_<id>, SFX_<id>, MUSIC, ENDCARD_BG, LOGO, CTA_PILL, CTA_TXT, BADGE_<n>, CHAR, GUIDE_<zone>.
var AEX = AEX || {};
AEX.ad = (function () {
    var SFX_LEAD = { whoosh: 0.35 };   // seconds before the cut: a whoosh peaks on the cut, it does not start on it

    function tg(l) { return l.property("ADBE Transform Group"); }
    function fr(c, s) { return Math.round(s * c.frameRate); }
    function levels(l, db) { l.property("ADBE Audio Group").property("ADBE Audio Levels").setValue([db, db]); }

    // importMedia({key: absPath}): {key: FootageItem}
    function importMedia(map) {
        var out = {}, k, d;
        for (k in map) { if (Object.prototype.hasOwnProperty.call(map, k)) { d = AEK.xio.importFile(map[k], { bin: "01_media" }); out[k] = AEK.core.itemById(d.id); } }
        return out;
    }

    // toEnd(layer, seconds): in point at seconds, out point at the comp end. Moving only the in point of a still or a
    // solid can slide the whole layer (measured: a logo's out point landed at 36 s in a 20 s comp).
    function toEnd(l, s) { l.inPoint = s; l.outPoint = l.containingComp.duration; }

    function fitWidth(l, item, w) { var s = w / item.width * 100; tg(l).property("ADBE Scale").setValue([s, s]); return s; }

    // pop(layer, comp, fromPercent, frames): scale from fromPercent of the layer's current scale to 100 % of it
    function pop(l, c, from, frames) {
        var p = tg(l).property("ADBE Scale"), t0 = l.inPoint, v = p.value, k1, k2;
        k1 = AEK.motion.key(p, t0, [v[0] * from / 100, v[1] * from / 100]);
        k2 = AEK.motion.key(p, t0 + frames / c.frameRate, [v[0], v[1]]);
        AEK.motion.ease(p, k1, 33, 10);
        AEK.motion.ease(p, k2, 80, 33);
    }

    function addText(c, s, o) {
        var l = AEK.text.add(c, s, { font: o.font, size: o.size, fill: o.fill || [1, 1, 1], stroke: o.stroke, strokeWidth: o.strokeWidth,
            justify: "center", position: o.position, name: o.name });
        var p = l.property("ADBE Text Properties").property("ADBE Text Document"), d = p.value, w, i, half, best, f;
        // the default paints the stroke OVER the fill: at 40 px a 5 px stroke turned white type black (measured)
        if (o.stroke) { d.strokeOverFill = false; p.setValue(d); }
        f = AEK.text.fit(l, o.width, { minSize: o.minSize || 20 });
        if (o.twoLines && f.size < o.size * 0.85) {   // shrinking past 85 %: break into two balanced lines instead
            d = p.value; w = s.split(" "); best = 1; half = s.length / 2;
            for (i = 1; i < w.length; i++) { if (Math.abs(w.slice(0, i).join(" ").length - half) < Math.abs(w.slice(0, best).join(" ").length - half)) { best = i; } }
            d.text = w.slice(0, best).join(" ") + "\r" + w.slice(best).join(" "); d.fontSize = o.size; p.setValue(d);
            f = AEK.text.fit(l, o.width, { minSize: o.minSize || 20 }); f.lines = 2;
        }
        return { layer: l, fit: f };
    }

    // lineFor(textLayer, string, maxWidth): the string as it must be written into an override: one line if it fits at the
    // master's size, else two balanced lines. Measured in the master (set, measure, restore). An override replaces the
    // whole text document, so the master's own line break and fit do not carry over to it.
    function lineFor(l, s, maxW) {
        var p = l.property("ADBE Text Properties").property("ADBE Text Document"), d0 = p.value, d = p.value, t = l.inPoint + 4 / 30, w, words, i, best = 1, half = s.length / 2, out;
        function width(str) { d = p.value; d.text = str; p.setValue(d); return AEK.text.measure(l, t).comp.width; }
        w = width(s); out = { text: s, lines: 1, width: Math.round(w) };
        if (w > maxW) {
            words = s.split(" ");
            for (i = 1; i < words.length; i++) { if (Math.abs(words.slice(0, i).join(" ").length - half) < Math.abs(words.slice(0, best).join(" ").length - half)) { best = i; } }
            out.text = words.slice(0, best).join(" ") + "\r" + words.slice(best).join(" "); out.lines = 2; out.width = Math.round(width(out.text));
        }
        p.setValue(d0);
        out.fits = out.width <= maxW;
        return out;
    }

    // Looks of the builder. GAME is the default (game ads: stroked white type, pops, a yellow CTA pill, store badges).
    // BRAND is a brand spot: type in the brand color with no stroke, no pops, the CTA as a line of text, no pill, no badges,
    // a gradient scrim under the hook line. sheet.style overrides any key: {endcardBg, textFill, textStroke (null: none),
    // strokeWidth, textPop (percent, 0: none), logoPop (percent, 0: none), cta ("pill" | "text"), ctaFill, ctaTextFill,
    // ctaSize, pulse, badges (false: endcard.badges are not built), scrim (0 to 1: opacity of a dark gradient under the
    // hook line), scrimColor}.
    var GAME = { endcardBg: [0.1, 0.06, 0.19], textFill: [1, 1, 1], textStroke: [0, 0, 0], strokeWidth: 5, textPop: 112, logoPop: 85,
        cta: "pill", ctaFill: [1, 0.8, 0], ctaTextFill: [0.1, 0.06, 0.19], ctaSize: 30, pulse: true, badges: true, scrim: 0, scrimColor: [0, 0, 0] };
    var BRAND = { endcardBg: [0.05, 0.05, 0.06], textFill: [0.96, 0.93, 0.86], textStroke: null, strokeWidth: 0, textPop: 0, logoPop: 0,
        cta: "text", ctaFill: null, ctaTextFill: [0.96, 0.93, 0.86], ctaSize: 40, pulse: false, badges: false, scrim: 0.55, scrimColor: [0, 0, 0] };
    function styleOf(sheet) {
        var base = (sheet.style && sheet.style.preset === "brand") ? BRAND : GAME, out = {}, k;
        for (k in base) { if (Object.prototype.hasOwnProperty.call(base, k)) { out[k] = base[k]; } }
        for (k in (sheet.style || {})) { if (Object.prototype.hasOwnProperty.call(sheet.style, k) && k !== "preset") { out[k] = sheet.style[k]; } }
        return out;
    }
    // scrim(comp, textLayer, opacity, color): a soft dark band from the frame edge to past the text, so light type reads on
    // a bright plate without a stroke. A comp-size solid with a mask that runs past three frame edges: only the inner edge
    // shows the feather. Same in and out points as the text, placed right under it.
    function scrim(c, tl, opacity, color) {
        var b = AEK.text.measure(tl, tl.inPoint + 4 * c.frameDuration).comp, top = (b.top + b.bottom) / 2 < c.height / 2;
        var edge = top ? b.bottom + b.height * 1.5 : b.top - b.height * 1.5, f = Math.round(b.height * 2);
        var sl = AEK.build.solid(c, "SCRIM_" + tl.name, color || [0, 0, 0]);
        var r = top ? [-f, -f, c.width + 2 * f, edge + f] : [-f, edge - f, c.width + 2 * f, c.height - edge + 2 * f];
        AEK.build.mask(sl, { rect: r, feather: f });
        tg(sl).property("ADBE Opacity").setValue(opacity * 100);
        sl.inPoint = tl.inPoint; sl.outPoint = tl.outPoint;
        sl.moveAfter(tl);
        return { layer: sl.name, edge: Math.round(edge), feather: f };
    }

    // build(sheet, items, fmt, opts): one comp from a beat sheet. fmt = layout key ("9x16", "1x1", "16x9").
    // opts {name, size:[w,h], protect: true (hook and end card become protected regions), bin}
    // Shots tagged product: true in the sheet carry the comment "product" on their layer: report() reads it for the hook gate.
    function build(sheet, items, fmt, opts) {
        opts = opts || {};
        var L = sheet.layout[fmt], fps = sheet.fps, size = opts.size || sheet.size, i, s, l, mv, rep = { shots: [], texts: [], fits: [] }, ST = styleOf(sheet);
        rep.style = (sheet.style && sheet.style.preset) || "game";
        var c = AEK.build.comp(opts.name || sheet.name, { width: size[0], height: size[1], fps: fps, duration: sheet.frames / fps, bg: [0, 0, 0], bin: opts.bin || "02_comps" });
        var mus = c.layers.add(items[sheet.music.key]); mus.name = "MUSIC"; levels(mus, sheet.music.db);
        for (i = 0; i < sheet.shots.length; i++) {
            s = sheet.shots[i];
            l = c.layers.add(items[s.clip]); l.name = "SHOT_" + s.id;
            l.startTime = (s.f0 - (s.src || 0)) / fps; l.inPoint = s.f0 / fps; l.outPoint = s.f1 / fps;
            var sc = Math.max(c.width / items[s.clip].width, c.height / items[s.clip].height) * 100;
            tg(l).property("ADBE Scale").setValue([sc, sc]);
            if (l.hasAudio) { l.audioEnabled = false; }   // captured game audio is muted and re-laid as designed sound
            l.comment = s.product ? "product" : "";
            mv = new MarkerValue(s.id); mv.duration = (s.f1 - s.f0) / fps;
            if (opts.protect && i === 0) { mv.protectedRegion = true; }
            c.markerProperty.setValueAtTime(s.f0 / fps, mv);
            rep.shots.push({ id: s.id, f0: fr(c, l.inPoint), f1: fr(c, l.outPoint), cover: Math.round(sc * 10) / 10 });
        }
        var e = sheet.endcard, ef = e.f0 / fps;
        var bg = AEK.build.solid(c, "ENDCARD_BG", ST.endcardBg); toEnd(bg, ef);
        mv = new MarkerValue("endcard"); mv.duration = (sheet.frames - e.f0) / fps; if (opts.protect) { mv.protectedRegion = true; }
        c.markerProperty.setValueAtTime(ef, mv);
        var logo = c.layers.add(items[e.logo]); logo.name = "LOGO"; toEnd(logo, ef);
        // a logo precomp plays its own animation from its start time: start it at the end card, not at 0
        if (items[e.logo] instanceof CompItem) { logo.startTime = ef; logo.outPoint = c.duration; }
        fitWidth(logo, items[e.logo], L.logoW); tg(logo).property("ADBE Position").setValue(L.logo); if (ST.logoPop) { pop(logo, c, ST.logoPop, 6); }
        var ct, pill = null;
        if (ST.cta === "pill") {
            pill = AEK.build.shape(c, "CTA_PILL", { name: "pill", type: "rect", size: [L.ctaW, 64], roundness: 32, fill: ST.ctaFill }, { position: L.cta });
            toEnd(pill, ef + 8 / fps);
            ct = addText(c, e.cta, { font: sheet.font, size: ST.ctaSize, fill: ST.ctaTextFill, position: [L.cta[0], L.cta[1] + 11], width: L.ctaW - 40, name: "CTA_TXT" });
            toEnd(ct.layer, pill.inPoint);
            if (ST.pulse) {
                // breathing pulse 100 to 104 % every 1.5 s, measured from the layer's own in point
                AEK.expr.set(tg(pill).property("ADBE Scale"), "var t = time - inPoint; var s = 100 + 2 * (1 - Math.cos(t * 2 * Math.PI / 1.5)); [s, s];");
            }
            ct.layer.parent = pill;   // the text pulses around the pill center
        } else {
            ct = addText(c, e.cta, { font: e.ctaFont || sheet.font, size: ST.ctaSize, fill: ST.ctaTextFill, position: L.cta, width: L.ctaW, name: "CTA_TXT" });
            toEnd(ct.layer, ef + (e.ctaDelay === undefined ? 8 : e.ctaDelay) / fps);
        }
        for (i = 0; i < (ST.badges ? (e.badges || []).length : 0); i++) {
            var b = AEK.build.shape(c, "BADGE_" + (i + 1), { name: "badge", type: "rect", size: [L.badgeW, 48], roundness: 10, fill: [0, 0, 0], stroke: { color: [1, 1, 1], width: 2 } }, { position: L.badges[i] });
            toEnd(b, ef + 12 / fps);
            var bt = addText(c, e.badges[i], { font: sheet.font, size: 18, position: [L.badges[i][0], L.badges[i][1] + 6], width: L.badgeW - 20, name: "BADGE_" + (i + 1) + "_TXT" });
            toEnd(bt.layer, b.inPoint);
        }
        for (i = 0; i < sheet.shots.length; i++) {
            s = sheet.shots[i];
            if (s.character && items.character) {
                var ch = c.layers.add(items.character); ch.name = "CHAR"; ch.inPoint = s.f0 / fps + 6 / fps; ch.outPoint = s.f1 / fps;
                var cs = L.charH / items.character.height * 100; tg(ch).property("ADBE Scale").setValue([cs, cs]);
                tg(ch).property("ADBE Position").setValue(L.char);
                var cp = tg(ch).property("ADBE Scale"), k1 = AEK.motion.key(cp, ch.inPoint, [0, 0]), k2 = AEK.motion.key(cp, ch.inPoint + 5 / fps, [cs * 1.1, cs * 1.1]), k3 = AEK.motion.key(cp, ch.inPoint + 9 / fps, [cs, cs]);
                AEK.motion.ease(cp, k1, 33, 60); AEK.motion.ease(cp, k2, 50, 50); AEK.motion.ease(cp, k3, 80, 33);
            }
            if (s.text) {
                var tx = addText(c, s.text, { font: sheet.font, size: L.size, fill: ST.textFill, stroke: ST.textStroke || undefined, strokeWidth: ST.textStroke ? ST.strokeWidth : undefined,
                    position: L.text, width: L.textW, name: "TXT_" + s.id, twoLines: true });
                tx.layer.inPoint = s.f0 / fps; tx.layer.outPoint = (s.textF1 || s.f1) / fps;   // a line may hold across the next cut (textF1)
                if (ST.textPop) { pop(tx.layer, c, ST.textPop, 4); }
                if (ST.scrim && (s.scrim !== false)) { scrim(c, tx.layer, s.scrim || ST.scrim, ST.scrimColor); }
                rep.fits.push({ layer: tx.layer.name, size: tx.fit.size, lines: tx.fit.lines || 1, overflow: tx.fit.overflow });
            }
        }
        var sfxList = [];
        for (i = 0; i < sheet.shots.length; i++) { if (sheet.shots[i].sfx) { sfxList.push(sheet.shots[i]); } }
        if (e.sfx) { sfxList.push({ id: "endcard", f0: e.f0, sfx: e.sfx, db: e.db }); }
        for (i = 0; i < sfxList.length; i++) {
            s = sfxList[i];
            var a = c.layers.add(items[s.sfx]); a.name = "SFX_" + s.id + "_" + s.sfx;
            a.startTime = s.f0 / fps - (SFX_LEAD[s.sfx] || 0); levels(a, s.db || 0);
        }
        return { comp: c, report: rep };
    }

    // zoneRects(comp, zones): zones {name: {top, bottom, left, right (fractions of the frame), source}} -> [{name, rect:[l, t, r, b]}]
    function zoneRects(c, zones) {
        var out = [], k, z;
        for (k in zones) { if (Object.prototype.hasOwnProperty.call(zones, k)) { z = zones[k]; out.push({ name: k, rect: [c.width * z.left, c.height * z.top, c.width * (1 - z.right), c.height * (1 - z.bottom)] }); } }
        return out;
    }

    function checked(l) { return /^(TXT_|LOGO|CTA_|BADGE_)/.test(l.name) && l.enabled && !l.guideLayer; }

    // zoneCheck(comp, zones): every text, logo, CTA and badge layer, 4 frames after its in point and on its last frame,
    // against each zone's safe rectangle. Returns [{layer, zone, frame, bounds, rect}].
    function zoneCheck(c, zones) {
        var rects = zoneRects(c, zones), bad = [], i, j, k, l, ts, m, r;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!checked(l)) { continue; }
            ts = [Math.min(l.inPoint + 4 * c.frameDuration, l.outPoint - c.frameDuration), l.outPoint - c.frameDuration];
            for (k = 0; k < ts.length; k++) {
                m = AEK.text.measure(l, ts[k]).comp;   // comp space through the whole parent chain (kit text.jsx)
                for (j = 0; j < rects.length; j++) {
                    r = rects[j].rect;
                    if (m.left < r[0] || m.top < r[1] || m.right > r[2] || m.bottom > r[3]) {
                        bad.push({ layer: l.name, zone: rects[j].name, frame: fr(c, ts[k]), bounds: [Math.round(m.left), Math.round(m.top), Math.round(m.right), Math.round(m.bottom)], rect: [Math.round(r[0]), Math.round(r[1]), Math.round(r[2]), Math.round(r[3])] });
                    }
                }
            }
        }
        return bad;
    }

    // guides(comp, zones, {render}): one shape layer per zone painting the unsafe bands; guide layer (not rendered) unless render is true
    function guides(c, zones, o) {
        o = o || {};
        var rects = zoneRects(c, zones), out = [], i, r, W = c.width, H = c.height, g, specs;
        var colors = [[1, 0, 0], [0, 0.6, 1], [0, 1, 0.4], [1, 0, 1]];
        for (i = 0; i < rects.length; i++) {
            r = rects[i].rect;
            specs = [
                { name: "top", type: "rect", size: [W, r[1]], position: [W / 2, r[1] / 2], fill: colors[i % 4] },
                { name: "bottom", type: "rect", size: [W, H - r[3]], position: [W / 2, (H + r[3]) / 2], fill: colors[i % 4] },
                { name: "left", type: "rect", size: [r[0], r[3] - r[1]], position: [r[0] / 2, (r[1] + r[3]) / 2], fill: colors[i % 4] },
                { name: "right", type: "rect", size: [W - r[2], r[3] - r[1]], position: [(W + r[2]) / 2, (r[1] + r[3]) / 2], fill: colors[i % 4] }
            ];
            g = AEK.build.shape(c, "GUIDE_" + rects[i].name, specs, { position: [0, 0] });
            g.property("ADBE Transform Group").property("ADBE Opacity").setValue(30);
            g.guideLayer = !o.render;
            out.push(g.name);
        }
        return out;
    }

    // beatMarkers(layer, beatsF): one layer marker per beat; the comment keeps the exact float frame
    function beatMarkers(l, beatsF) {
        var c = l.containingComp, i, mv;
        for (i = 0; i < beatsF.length; i++) { mv = new MarkerValue(String(beatsF[i])); l.property("ADBE Marker").setValueAtTime(beatsF[i] / c.frameRate, mv); }
        return l.property("ADBE Marker").numKeys;
    }

    function cutsOf(c) {
        var cuts = [], i, l, f;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (/^SHOT_/.test(l.name) || l.name === "ENDCARD_BG") { f = fr(c, l.inPoint); if (f > 0) { cuts.push({ layer: l.name, f: f }); } }
        }
        cuts.sort(function (a, b) { return a.f - b.f; });
        return cuts;
    }

    // beatOffsets(comp): each cut against the nearest beat marker on MUSIC (comment = float frame). offset > 0: cut is late.
    function beatOffsets(c) {
        var mus = c.layers.byName("MUSIC"), m, beats = [], i, j, cuts = cutsOf(c), out = [], best;
        if (!mus) { return null; }
        m = mus.property("ADBE Marker");
        for (i = 1; i <= m.numKeys; i++) { beats.push(parseFloat(m.keyValue(i).comment)); }
        if (!beats.length) { return null; }
        for (i = 0; i < cuts.length; i++) {
            best = beats[0];
            for (j = 1; j < beats.length; j++) { if (Math.abs(beats[j] - cuts[i].f) < Math.abs(best - cuts[i].f)) { best = beats[j]; } }
            out.push({ cut: cuts[i].layer, f: cuts[i].f, beat: best, offset: Math.round((cuts[i].f - best) * 100) / 100 });
        }
        return out;
    }

    // report(comp, zones): the numbers a creative lead asks for, read from the built comp (never from the sheet)
    function report(c, zones) {
        var i, l, d, words, texts = [], hook = null, cuts = cutsOf(c), win = [], w, n, j, fps = c.frameRate, end = fr(c, c.duration);
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (/^TXT_/.test(l.name)) {
                d = l.property("ADBE Text Properties").property("ADBE Text Document").value.text;
                words = d.replace(/^\s+|\s+$/g, "").split(/\s+/).length;
                texts.push({ layer: l.name, text: d, words: words, f0: fr(c, l.inPoint), frames: fr(c, l.outPoint) - fr(c, l.inPoint) });
                if (hook === null || fr(c, l.inPoint) < hook) { hook = fr(c, l.inPoint); }
            }
        }
        texts.sort(function (a, b) { return a.f0 - b.f0; });
        for (w = 0; w < end; w += Math.round(10 * fps)) {
            n = 0; for (j = 0; j < cuts.length; j++) { if (cuts[j].f >= w && cuts[j].f < w + 10 * fps) { n++; } }
            win.push({ window: w + "-" + Math.min(end, w + Math.round(10 * fps)), cuts: n });
        }
        var logo = c.layers.byName("LOGO"), cta = c.layers.byName("CTA_TXT"), ec = c.layers.byName("ENDCARD_BG"), hookShot = null;
        // the shot on screen under the hook line: its layer comment says whether the sheet tagged it as showing the product
        for (i = 1; i <= c.numLayers; i++) { l = c.layer(i); if (/^SHOT_/.test(l.name) && hook !== null && fr(c, l.inPoint) <= hook && fr(c, l.outPoint) > hook) { hookShot = { layer: l.name, product: l.comment === "product" }; } }
        return { comp: c.name, fps: fps, frames: end, size: [c.width, c.height], hook_text_frame: hook, hook_shot: hookShot, first_cut_f: cuts.length ? cuts[0].f : end,
            cuts: cuts, cuts_per_10s: win, texts: texts,
            logo_first_f: logo ? fr(c, logo.inPoint) : null,
            cta_frames: cta ? fr(c, cta.outPoint) - fr(c, cta.inPoint) : 0,
            endcard_frames: ec ? end - fr(c, ec.inPoint) : 0,
            beat_offsets: beatOffsets(c),
            zone_violations: zones ? zoneCheck(c, zones) : [] };
    }

    // reformat(master, layouts, opts): one master comp (a product precomp, an end card, a brand spot) delivered in several
    // formats. Each layout row {fmt, size:[w,h], scale (percent), position:[x,y], texts:[{name, text, font, size, fill,
    // position, width}], zones, name} gives one comp (name, else "<prefix>_<fmt>") holding the master nested as MASTER under its own texts
    // (names start with TXT_ so zoneCheck reads them). Real re-layout per format, never a crop of one frame.
    // opts {prefix, bin, bg:[r,g,b]}. Returns {fmt: {comp (name), id, zoneViolations, fits}}.
    function reformat(master, layouts, o) {
        o = o || {};
        var out = {}, i, j, L, c, m, t, r, fits;
        for (i = 0; i < layouts.length; i++) {
            L = layouts[i];
            c = AEK.build.comp(L.name || ((o.prefix || master.name) + "_" + L.fmt), { width: L.size[0], height: L.size[1], fps: master.frameRate, duration: master.duration, bin: o.bin });
            if (o.bg) { AEK.build.solid(c, "BG", o.bg); }
            m = c.layers.add(master); m.name = "MASTER";
            tg(m).property("ADBE Position").setValue(L.position || [L.size[0] / 2, L.size[1] / 2]);
            if (L.scale) { tg(m).property("ADBE Scale").setValue([L.scale, L.scale]); }
            fits = [];
            for (j = 0; j < (L.texts || []).length; j++) {
                t = L.texts[j];
                r = addText(c, t.text, { font: t.font, size: t.size, fill: t.fill, position: t.position, name: t.name, width: t.width || L.size[0] * 0.9, twoLines: t.twoLines });
                if (t.inPoint !== undefined) { toEnd(r.layer, t.inPoint); }
                fits.push({ layer: t.name, size: r.fit.size, from: r.fit.from, overflow: r.fit.overflow });
            }
            out[L.fmt] = { comp: c.name, id: c.id, fits: fits, zoneViolations: L.zones ? zoneCheck(c, L.zones) : [] };
        }
        return out;
    }

    return { reformat: reformat, importMedia: importMedia, build: build, scrim: scrim, GAME: GAME, BRAND: BRAND, zoneRects: zoneRects, zoneCheck: zoneCheck, guides: guides,
        beatMarkers: beatMarkers, lineFor: lineFor, beatOffsets: beatOffsets, cuts: cutsOf, report: report, levels: levels };
})();
