// project.jsx: AEX.project, intake and hygiene helpers for a whole After Effects project.
// Load with: ae.py run job.jsx --lib <this file>. Needs the AEK kit (core, audit). ES3 only.
var AEX = AEX || {};
AEX.project = (function () {
    var DEFAULT_NAME = /^(Comp|Pre-comp|Precomp|Composition|Comp Copy)\s*\d*$/i;

    function isComp(it) { return it instanceof CompItem; }
    function isFootage(it) { return it instanceof FootageItem && !(it.mainSource instanceof SolidSource); }
    function srcOf(l) { var s = null; try { s = l.source; } catch (e) {} return s; }
    function has(a, v) { var i; for (i = 0; i < a.length; i++) { if (a[i] === v) { return true; } } return false; }

    // roots(main): the comps that ship. main may be one comp or a list; comps in the render queue and comps named MAIN_ or
    // DLV_ (deliverables) are added, so a deliverable that nests nothing of the master is never filed as unused.
    function roots(main) {
        var list = [], ids = {}, all = AEK.core.comps(), rq = app.project.renderQueue, i, c;
        function push(x) { if (x && !ids[x.id]) { ids[x.id] = true; list.push(x); } }
        if (main instanceof Array) { for (i = 0; i < main.length; i++) { push(main[i]); } } else { push(main); }
        for (i = 1; i <= rq.numItems; i++) { try { push(rq.item(i).comp); } catch (e) {} }
        for (i = 0; i < all.length; i++) { c = all[i]; if (/^(MAIN|DLV)_/.test(c.name)) { push(c); } }
        return list;
    }

    // tree(main): every item reachable from the roots (main, the render queue, MAIN_ and DLV_ comps), with nesting depth.
    // Unreached comps and footage are dead weight.
    function tree(main) {
        var seen = {}, order = [], maxDepth = 0;
        function visit(c, depth, parentName) {
            var i, s;
            if (seen[c.id]) { return; }
            seen[c.id] = { depth: depth, parent: parentName };
            order.push(c);
            if (depth > maxDepth) { maxDepth = depth; }
            for (i = 1; i <= c.numLayers; i++) {
                s = srcOf(c.layer(i));
                if (!s) { continue; }
                if (isComp(s)) { visit(s, depth + 1, c.name); }
                else if (!seen[s.id]) { seen[s.id] = { depth: depth + 1, parent: c.name }; order.push(s); }
                // track matte and effect layer inputs are layers of this comp: already covered by the loop
            }
        }
        var R = roots(main), r0;
        for (r0 = 0; r0 < R.length; r0++) { visit(R[r0], 0, ""); }
        var unusedComps = [], unusedFootage = [], it, j;
        for (j = 1; j <= app.project.numItems; j++) {
            it = app.project.item(j);
            if (seen[it.id]) { continue; }
            if (isComp(it)) { unusedComps.push(it.name); }
            else if (it instanceof FootageItem) { unusedFootage.push(it.name); }
        }
        var rootNames = []; for (r0 = 0; r0 < R.length; r0++) { rootNames.push(R[r0].name); }
        return { reached: order.length, maxDepth: maxDepth, unusedComps: unusedComps, unusedFootage: unusedFootage, seen: seen, roots: rootNames, rootIds: R };
    }

    // collapseRisks(): collapsed precomps that will flatten (effect, closed mask, layer style) and adjustment layers inside collapsed comps
    function collapseRisks() {
        var out = [], comps = AEK.core.comps(), i, j, l, s, fx, masks, k, closed, inner;
        for (i = 0; i < comps.length; i++) {
            for (j = 1; j <= comps[i].numLayers; j++) {
                l = comps[i].layer(j); s = srcOf(l);
                if (!isComp(s) || !l.collapseTransformation) { continue; }
                fx = l.property("ADBE Effect Parade"); masks = l.property("ADBE Mask Parade"); closed = 0;
                if (masks) { for (k = 1; k <= masks.numProperties; k++) { if (masks.property(k).maskMode !== MaskMode.NONE) { closed++; } } }
                if (fx && fx.numProperties) { out.push({ where: comps[i].name + " > " + l.name, rule: "collapse.effect", message: fx.numProperties + " effect(s) on a collapsed precomp: it flattens, inner 3D stops interacting with the parent" }); }
                if (closed) { out.push({ where: comps[i].name + " > " + l.name, rule: "collapse.mask", message: closed + " closed mask(s) on a collapsed precomp: it flattens" }); }
                try { if (l.property("ADBE Layer Styles") && l.property("ADBE Layer Styles").canSetEnabled && l.property("ADBE Layer Styles").enabled && l.property("ADBE Layer Styles").numProperties > 1) { out.push({ where: comps[i].name + " > " + l.name, rule: "collapse.style", message: "Layer style on a collapsed precomp: it flattens" }); } } catch (e0) {}
                for (k = 1; k <= s.numLayers; k++) {
                    inner = s.layer(k);
                    if (inner.adjustmentLayer) { out.push({ where: s.name + " > " + inner.name, rule: "collapse.adjustment", message: "Adjustment layer inside a collapsed precomp: forces flattening and cropping" }); }
                }
            }
        }
        return out;
    }

    // inventory(main): one read-only intake report: counts, frame rates, missing items, dead weight, risks, audit summary
    function inventory(main) {
        var t = tree(main), comps = AEK.core.comps(), rates = {}, frates = {}, i, it, missing = [], proxies = [], defaults = [], k;
        for (i = 0; i < comps.length; i++) {
            k = String(Math.round(comps[i].frameRate * 1000) / 1000); rates[k] = (rates[k] || 0) + 1;
            if (DEFAULT_NAME.test(comps[i].name)) { defaults.push(comps[i].name); }
        }
        for (i = 1; i <= app.project.numItems; i++) {
            it = app.project.item(i);
            if (!isFootage(it)) { continue; }
            if (it.footageMissing) { missing.push({ name: it.name, path: (it.mainSource.missingFootagePath || "") }); }
            if (it.proxySource) { proxies.push({ name: it.name, useProxy: it.useProxy }); }
            if (it.hasVideo && !it.mainSource.isStill) { k = String(Math.round(it.frameRate * 1000) / 1000); frates[k] = (frates[k] || 0) + 1; }
        }
        var findings = AEK.audit.all();
        return {
            items: app.project.numItems, comps: comps.length, reached: t.reached, maxDepth: t.maxDepth,
            unusedComps: t.unusedComps, unusedFootage: t.unusedFootage, defaultNames: defaults,
            compRates: rates, footageRates: frates, missing: missing, proxies: proxies,
            nestedRateMismatch: nestedRates(), missingFonts: missingFonts(),
            collapseRisks: collapseRisks(), audit: AEK.audit.summary(findings), findings: findings,
            bpc: app.project.bitsPerChannel, workingSpace: app.project.workingSpace, engine: app.project.expressionEngine
        };
    }

    // nestedRates(): precomp layers whose comp frame rate differs from the comp they sit in (the kit audit reports the same as layer.nestedFrameRate)
    function nestedRates() {
        var out = [], comps = AEK.core.comps(), i, j, s;
        for (i = 0; i < comps.length; i++) {
            for (j = 1; j <= comps[i].numLayers; j++) {
                s = srcOf(comps[i].layer(j));
                if (isComp(s) && Math.abs(s.frameRate - comps[i].frameRate) > 0.001) {
                    out.push({ where: comps[i].name + " > " + comps[i].layer(j).name, inner: Math.round(s.frameRate * 1000) / 1000, outer: comps[i].frameRate, preserve: s.preserveNestedFrameRate });
                }
            }
        }
        return out;
    }

    // findFile(name, roots, maxDepth): first file with this exact name under any root (breadth first, never follows aliases)
    function findFile(name, roots, maxDepth) {
        var queue = [], i, f, kids, j;
        for (i = 0; i < roots.length; i++) { queue.push({ f: new Folder(roots[i]), d: 0 }); }
        while (queue.length) {
            f = queue.shift();
            if (!f.f.exists) { continue; }
            kids = f.f.getFiles();
            for (j = 0; j < kids.length; j++) {
                if (kids[j] instanceof File && decodeURI(kids[j].name) === name) { return kids[j]; }
            }
            if (f.d < (maxDepth || 6)) { for (j = 0; j < kids.length; j++) { if (kids[j] instanceof Folder && !kids[j].alias) { queue.push({ f: kids[j], d: f.d + 1 }); } } }
        }
        return null;
    }

    // relink(roots): relink every missing footage item by file name under the search roots; never guesses between two candidates
    function relink(roots) {
        var res = { relinked: [], notFound: [] }, i, it, oldPath, name, hit;
        for (i = 1; i <= app.project.numItems; i++) {
            it = app.project.item(i);
            if (!isFootage(it) || !it.footageMissing) { continue; }
            oldPath = it.mainSource.missingFootagePath || "";
            name = oldPath.split("/").pop();
            hit = name ? findFile(name, roots) : null;
            if (!hit) { res.notFound.push({ name: it.name, path: oldPath }); continue; }
            // an image file with a frame number in a moving item is a sequence; a movie with digits in its name is not
            if (!it.mainSource.isStill && /\d{3,}\.(png|jpe?g|exr|tiff?|dpx|psd|tga)$/i.test(name)) { it.replaceWithSequence(hit, true); } else { it.replace(hit); }
            res.relinked.push({ name: it.name, from: oldPath, to: hit.fsName, missingNow: it.footageMissing });
        }
        return res;
    }

    // missingFonts(): fonts the project uses that are substitutes. getFontsByPostScriptName() is NOT a test: once a
    // project references a missing font, it returns a substitute Font object for it (length 1). Use isSubstitute.
    function missingFonts() {
        var uf = app.project.usedFonts, out = [], i;
        for (i = 0; i < uf.length; i++) { if (uf[i].font.isSubstitute) { out.push({ postScriptName: uf[i].font.postScriptName, family: uf[i].font.familyName, layers: uf[i].usedAt.length }); } }
        return out;
    }
    // fixFonts(fallback): every substitute font becomes the installed fallback, project wide, through Project.replaceFont (24.5+)
    function fixFonts(fallback) {
        var to = app.fonts.getFontsByPostScriptName(fallback), uf = app.project.usedFonts, res = { replaced: [] }, i;
        if (!to.length || to[0].isSubstitute) { throw new Error("Fallback font not installed: " + fallback); }
        for (i = 0; i < uf.length; i++) {
            if (!uf[i].font.isSubstitute) { continue; }
            res.replaced.push({ from: uf[i].font.postScriptName, layers: uf[i].usedAt.length, changed: app.project.replaceFont(uf[i].font, to[0]) });
        }
        res.stillMissing = missingFonts().length;
        return res;
    }

    // rewriteRefs(pairs): a rename by script leaves expressions on the old name ("layer named 'X' is missing").
    // pairs [{kind: "comp"|"layer", from, to, scope: comp id for layers}]: rewrites comp("from") and layer("from") in place.
    // Indirect references (a name built from a string variable) are not seen: read exprErrors afterwards.
    function rewriteRefs(pairs) {
        var comps = AEK.core.comps(), res = { rewritten: 0, exprErrors: [] }, i, j;
        function swap(code, c) {
            var k, q, p, qs = ['"', "'"];
            for (k = 0; k < pairs.length; k++) {
                p = pairs[k];
                if (p.kind === "layer" && p.scope !== c.id) { continue; }
                for (q = 0; q < 2; q++) { code = code.split(p.kind + "(" + qs[q] + p.from + qs[q] + ")").join(p.kind + "(" + qs[q] + p.to + qs[q] + ")"); }
            }
            return code;
        }
        for (i = 0; i < comps.length; i++) {
            for (j = 1; j <= comps[i].numLayers; j++) {
                AEK.core.walk(comps[i].layer(j), function (p) {
                    if (p.propertyType !== PropertyType.PROPERTY) { return; }
                    var ex = ""; try { if (p.canSetExpression) { ex = p.expression; } } catch (e) { return; }
                    if (ex === "") { return; }
                    var nx = swap(ex, comps[i]);
                    if (nx !== ex) { p.expression = nx; res.rewritten++; }
                });
            }
        }
        for (i = 0; i < comps.length; i++) {
            var bad = AEK.expr.check(comps[i], 3).errors;
            for (j = 0; j < bad.length; j++) { bad[j].comp = comps[i].name; res.exprErrors.push(bad[j]); }
        }
        return res;
    }

    // rename(main, mainName): default-named comps get a placeholder from their place in the tree, parents first:
    // PC_<parent without prefix>_<user layer name, else first named layer inside>. Read frames, then give final names by hand.
    // Returns {renamed, rewritten, exprErrors}: expressions that named a renamed comp or layer are rewritten.
    function rename(main, mainName) {
        var t = tree(main), comps = AEK.core.comps(), i, j, c, users, l, base, name, n, taken = {}, out = [], order = [], inner, pairs = [];
        if (main instanceof Array) { main = main[0]; }   // the first comp of a list is the one mainName applies to
        for (i = 0; i < comps.length; i++) { taken[comps[i].name] = true; }
        if (mainName && main.name !== mainName) { out.push({ from: main.name, to: mainName }); pairs.push({ kind: "comp", from: main.name, to: mainName }); delete taken[main.name]; main.name = mainName; taken[mainName] = true; }
        for (i = 0; i < comps.length; i++) { if (t.seen[comps[i].id]) { order.push(comps[i]); } }
        order.sort(function (x, y) { return t.seen[x.id].depth - t.seen[y.id].depth; });
        for (i = 0; i < comps.length; i++) { if (!t.seen[comps[i].id]) { order.push(comps[i]); } }
        for (i = 0; i < order.length; i++) {
            c = order[i];
            if (c.id === main.id || !DEFAULT_NAME.test(c.name)) { continue; }
            users = c.usedIn; l = null;
            if (users.length) {
                for (j = 1; j <= users[0].numLayers; j++) { if (srcOf(users[0].layer(j)) === c) { l = users[0].layer(j); break; } }
                inner = "";
                if (l && !DEFAULT_NAME.test(l.name)) { inner = l.name; }
                for (j = 1; !inner && j <= c.numLayers; j++) { if (!DEFAULT_NAME.test(c.layer(j).name)) { inner = c.layer(j).name.replace(/\.[^.]+$/, ""); } }
                base = "PC_" + users[0].name.replace(/^(MAIN|PC)_/, "") + "_" + (inner || "Nest");
            } else { base = "UNUSED_" + c.name; }
            base = base.replace(/[^\w\- ]+/g, "").replace(/\s+/g, "");
            name = base; n = 2;
            while (taken[name]) { name = base + "_" + n; n++; }
            out.push({ from: c.name, to: name, usedIn: users.length });
            pairs.push({ kind: "comp", from: c.name, to: name });
            // a precomp layer without its own name follows the comp name: record its old name before the comp changes
            for (j = 0; j < users.length; j++) { layerPairs(users[j], c, name, pairs); }
            delete taken[c.name]; c.name = name; taken[name] = true;
            for (j = 0; j < users.length; j++) { renameLayersOf(users[j], c); }
        }
        var refs = rewriteRefs(pairs);
        return { renamed: out, rewritten: refs.rewritten, exprErrors: refs.exprErrors };
    }
    function layerPairs(parentComp, src, newName, pairs) {
        var j, l;
        for (j = 1; j <= parentComp.numLayers; j++) {
            l = parentComp.layer(j);
            if (srcOf(l) === src && (l.name === src.name || DEFAULT_NAME.test(l.name))) { pairs.push({ kind: "layer", from: l.name, to: newName, scope: parentComp.id }); }
        }
    }
    function renameLayersOf(parentComp, src) {
        var j, l;
        for (j = 1; j <= parentComp.numLayers; j++) { l = parentComp.layer(j); if (srcOf(l) === src && DEFAULT_NAME.test(l.name)) { l.name = src.name; } }
    }

    // fileItems(main | [comps], scheme): numbered bins; roots (main, deliverables, render queue comps) in 01_Main, reached
    // comps in 02_Precomps, footage by kind, unreached items to the archive bin
    function fileItems(main, scheme) {
        scheme = scheme || {};
        var b = {
            main: AEK.core.bin(scheme.main || "01_Main"), pre: AEK.core.bin(scheme.precomps || "02_Precomps"),
            foot: AEK.core.bin(scheme.footage || "03_Footage"), solids: AEK.core.bin(scheme.solids || "04_Solids"),
            unused: AEK.core.bin(scheme.unused || "99_Unused")
        };
        b.video = AEK.core.bin("Video", b.foot); b.stills = AEK.core.bin("Stills", b.foot); b.audio = AEK.core.bin("Audio", b.foot);
        var t = tree(main), i, it, moved = { main: 0, precomps: 0, video: 0, stills: 0, audio: 0, solids: 0, unused: 0, roots: t.roots }, items = [], rootId = {};
        for (i = 0; i < t.rootIds.length; i++) { rootId[t.rootIds[i].id] = true; }
        for (i = 1; i <= app.project.numItems; i++) { items.push(app.project.item(i)); }
        for (i = 0; i < items.length; i++) {
            it = items[i];
            if (it instanceof FolderItem) { continue; }
            if (rootId[it.id]) { it.parentFolder = b.main; moved.main++; }
            else if (it instanceof FootageItem && it.mainSource instanceof SolidSource) { it.parentFolder = b.solids; moved.solids++; }
            else if (!t.seen[it.id]) { it.parentFolder = b.unused; moved.unused++; }
            else if (isComp(it)) { it.parentFolder = b.pre; moved.precomps++; }
            else if (it.hasVideo && !it.mainSource.isStill) { it.parentFolder = b.video; moved.video++; }
            else if (it.hasVideo) { it.parentFolder = b.stills; moved.stills++; }
            else { it.parentFolder = b.audio; moved.audio++; }
        }
        return moved;
    }

    // layout(comp, {t, safe: {top, bottom, left, right} (fractions), minGap (px), minSpanY, maxCenterOffset, skip: /regex/}):
    // the per-format layout gate, measured from layer bounds at time t. A precomp layer is measured by its content (the
    // union of its own visible layers), not by its frame (a precomp holding only a full-frame layer counts by its frame). Layers covering 90 % of the frame or more are backgrounds and
    // are left out. Returns the blocks, then fails: a block outside the safe area, two blocks closer than minGap
    // (default 3 % of the shorter side), content spanning less than minSpanY of the safe height (default 0.5 for a
    // vertical frame, 0.35 otherwise), content center further than maxCenterOffset (default 0.12) of the safe height
    // from the safe-area center.
    function layout(c, o) {
        o = o || {};
        var t = o.t === undefined ? c.duration / 2 : o.t, W = c.width, H = c.height, z = o.safe || { top: 0.1, bottom: 0.1, left: 0.1, right: 0.1 };
        var S = { left: W * z.left, top: H * z.top, right: W * (1 - z.right), bottom: H * (1 - z.bottom) };
        var minGap = o.minGap === undefined ? Math.round(Math.min(W, H) * 0.03) : o.minGap, vertical = H > W * 1.2;
        var minSpan = o.minSpanY === undefined ? (vertical ? 0.5 : 0.35) : o.minSpanY, maxOff = o.maxCenterOffset === undefined ? 0.12 : o.maxCenterOffset;
        var blocks = [], i, l, b, fails = [];
        function visible(L, tt) {
            if (!L.enabled || L.guideLayer || L.adjustmentLayer || !(L instanceof AVLayer || L instanceof TextLayer || L instanceof ShapeLayer)) { return false; }
            if (L instanceof AVLayer && !L.hasVideo) { return false; }
            if (tt < L.inPoint || tt >= L.outPoint) { return false; }
            if (o.skip && o.skip.test(L.name)) { return false; }
            return L.property("ADBE Transform Group").property("ADBE Opacity").valueAtTime(tt, false) > 1;
        }
        function box(L, tt) {
            var s = null; try { s = L.source; } catch (e) {}
            if (s instanceof CompItem) {
                var it = (tt - L.startTime) * (L.stretch ? 100 / L.stretch : 1), u = null, k, m, cs, q, j, pts;
                for (k = 1; k <= s.numLayers; k++) {
                    if (!visible(s.layer(k), it) || s.layer(k).isTrackMatte) { continue; }
                    m = AEK.text.measure(s.layer(k), it).comp;
                    if (m.width * m.height >= s.width * s.height * 0.9) { continue; }
                    pts = [[m.left, m.top], [m.right, m.top], [m.left, m.bottom], [m.right, m.bottom]];
                    for (j = 0; j < 4; j++) {
                        q = AEK.text.toComp2D(L, pts[j], tt);
                        if (!u) { u = { left: q.x, top: q.y, right: q.x, bottom: q.y }; }
                        u.left = Math.min(u.left, q.x); u.top = Math.min(u.top, q.y); u.right = Math.max(u.right, q.x); u.bottom = Math.max(u.bottom, q.y);
                    }
                }
                if (u) { return u; }   // a precomp whose only layer fills it (a cropped still) is measured by its own frame
            }
            m = AEK.text.measure(L, tt).comp;
            return { left: m.left, top: m.top, right: m.right, bottom: m.bottom };
        }
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!visible(l, t) || l.isTrackMatte) { continue; }
            b = box(l, t);
            if (!b || (b.right - b.left) * (b.bottom - b.top) >= W * H * 0.9) { continue; }
            blocks.push({ layer: l.name, box: [Math.round(b.left), Math.round(b.top), Math.round(b.right), Math.round(b.bottom)] });
        }
        var U = null, a, d, dx, dy, j2;
        for (i = 0; i < blocks.length; i++) {
            b = blocks[i].box;
            if (b[0] < S.left - 0.5 || b[1] < S.top - 0.5 || b[2] > S.right + 0.5 || b[3] > S.bottom + 0.5) { fails.push({ rule: "outside safe area", layer: blocks[i].layer, box: b }); }
            U = U ? [Math.min(U[0], b[0]), Math.min(U[1], b[1]), Math.max(U[2], b[2]), Math.max(U[3], b[3])] : b.slice(0);
            for (j2 = i + 1; j2 < blocks.length; j2++) {
                a = blocks[j2].box;
                dx = Math.max(a[0] - b[2], b[0] - a[2]); dy = Math.max(a[1] - b[3], b[1] - a[3]);
                d = Math.max(dx, dy);   // negative: the boxes overlap
                if (d < minGap) { fails.push({ rule: d < 0 ? "blocks overlap" : "gap under " + minGap + " px", layers: [blocks[i].layer, blocks[j2].layer], gap: Math.round(d) }); }
            }
        }
        var SH = S.bottom - S.top, res = { comp: c.name, t: t, size: [W, H], safe: [Math.round(S.left), Math.round(S.top), Math.round(S.right), Math.round(S.bottom)], minGap: minGap, blocks: blocks };
        if (U) {
            res.content = U;
            res.spanY = Math.round((U[3] - U[1]) / SH * 100) / 100;
            res.centerOffsetY = Math.round(((U[1] + U[3]) / 2 - (S.top + S.bottom) / 2) / SH * 100) / 100;
            res.emptyBelow = Math.round((S.bottom - U[3]) / SH * 100) / 100;
            res.emptyAbove = Math.round((U[1] - S.top) / SH * 100) / 100;
            if (res.spanY < minSpan) { fails.push({ rule: "content spans " + res.spanY + " of the safe height (minimum " + minSpan + ")" }); }
            if (Math.abs(res.centerOffsetY) > maxOff) { fails.push({ rule: "content centre off by " + res.centerOffsetY + " of the safe height (maximum " + maxOff + ")" }); }
        } else {
            fails.push({ rule: "no visible content" });
        }
        res.fails = fails; res.ok = fails.length === 0;
        return res;
    }

    // color({bpc, workingSpace, linearize, engine, linearBlending, gamma}): set, then read back what After Effects kept.
    // A new project inherits the color engine, bit depth, linear blending and gamma of the project open before it, and
    // OCIO mode (engine 1) refuses 8 and 16 bpc: the engine is set first, and an inherited OCIO engine is switched back
    // to Adobe color management (0) when the brief asks for 8 or 16 bpc and names no engine (engineReset in the result).
    function color(o) {
        var p = app.project, reset = false;
        if (o.engine !== undefined) { p.colorManagementSystem = o.engine; }
        else if (o.bpc && o.bpc !== 32 && p.colorManagementSystem === 1) { p.colorManagementSystem = 0; reset = true; }
        if (o.bpc) { p.bitsPerChannel = o.bpc; }
        if (o.workingSpace) {
            // an unknown name is accepted silently and turns color management OFF (workingSpace reads "None")
            var names = p.listColorProfiles(), ok = false, i;
            for (i = 0; i < names.length; i++) { if (names[i] === o.workingSpace) { ok = true; } }
            if (!ok && o.workingSpace !== "None") { throw new Error("Unknown working space '" + o.workingSpace + "': use a name from app.project.listColorProfiles()"); }
            p.workingSpace = o.workingSpace;
        }
        if (o.linearize !== undefined) { p.linearizeWorkingSpace = o.linearize; }
        if (o.linearBlending !== undefined) { p.linearBlending = o.linearBlending; }
        if (o.gamma !== undefined) { p.workingGamma = o.gamma; }
        return { bpc: p.bitsPerChannel, workingSpace: p.workingSpace, linearize: p.linearizeWorkingSpace, gamma: p.workingGamma,
            engine: p.colorManagementSystem, linearBlending: p.linearBlending, engineReset: reset };
    }

    // conformComps(fps, comps): change comp frame rates; reports keys that land between frames afterwards (they keep their seconds)
    function conformComps(fps, list) {
        var out = [], i, c, off;
        for (i = 0; i < list.length; i++) {
            c = list[i];
            if (Math.abs(c.frameRate - fps) < 0.001) { continue; }
            var was = c.frameRate; c.frameRate = fps; off = offFrameKeys(c);
            out.push({ comp: c.name, from: was, to: c.frameRate, durationFrames: Math.round(c.duration * fps), keysBetweenFrames: off });
        }
        return out;
    }
    function offFrameKeys(c) {
        var n = 0, j;
        for (j = 1; j <= c.numLayers; j++) {
            AEK.core.walk(c.layer(j), function (p) {
                var k, f;
                if (p.propertyType !== PropertyType.PROPERTY || !p.numKeys) { return; }
                for (k = 1; k <= p.numKeys; k++) { f = p.keyTime(k) * c.frameRate; if (Math.abs(f - Math.round(f)) > 0.001) { n++; } }
            });
        }
        return n;
    }

    // makeProxy(item, dir, scale, template): render a reduced copy through the render queue, attach it as proxy, leave useProxy on.
    // template: an output module template name from AEK.capture.templates(comp); default H.264 (small, long-GOP decode).
    function makeProxy(it, dir, scale, template) {
        scale = scale || 0.5;
        template = template || "H.264 - Match Render Settings - 15 Mbps";
        var w = Math.round(it.width * scale / 2) * 2, h = Math.round(it.height * scale / 2) * 2;
        var c = app.project.items.addComp("tmp_proxy_" + it.id, w, h, 1, it.duration, it.frameRate), l = c.layers.add(it);
        l.property("ADBE Transform Group").property("ADBE Scale").setValue([scale * 100, scale * 100]);
        // templates rewrite the extension (.mp4, .mov): read the real path back from the queue result
        var path = dir + "/" + it.name.replace(/\.[^.]+$/, "") + "_proxy.mp4";
        var r = AEK.capture.queue(c, path, { template: template });
        c.remove();
        it.setProxy(new File(r.path));
        return { proxy: r.path, ms: r.ms, size: [w, h], useProxy: it.useProxy, proxyFile: (it.proxySource && it.proxySource.file) ? it.proxySource.file.fsName : "" };
    }

    // profile(comp, seconds, dir, frames): scripted stand-in for the Composition Profiler. Renders the same span
    // through the render queue with all layers on, then with each video layer off in turn: cost = full - without.
    // A single saveFrameToPng is too coarse to time (the kit polls every 100 ms), so time 10 or more frames.
    function profile(c, t, dir, nFrames) {
        nFrames = nFrames || 10;
        var span = nFrames * c.frameDuration, k = 0;
        function measure() {
            app.purge(PurgeTarget.ALL_CACHES);
            k++;
            return AEK.capture.queue(c, dir + "/profile_" + k + ".mp4", { template: "H.264 - Match Render Settings - 15 Mbps", start: t, duration: span }).ms;
        }
        var empty, full, rows = [], i, l, without, states = [];
        for (i = 1; i <= c.numLayers; i++) { states.push(c.layer(i).enabled); }
        for (i = 1; i <= c.numLayers; i++) { c.layer(i).enabled = false; }
        empty = measure();
        for (i = 1; i <= c.numLayers; i++) { c.layer(i).enabled = states[i - 1]; }
        full = measure();
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            if (!l.enabled || !l.hasVideo) { continue; }
            l.enabled = false; without = measure(); l.enabled = true;
            rows.push({ index: i, layer: l.name, costMsPerFrame: Math.round((full - without) / nFrames), costShare: Math.round(100 * (full - without) / Math.max(1, full - empty)) });
        }
        rows.sort(function (a, b) { return b.costMsPerFrame - a.costMsPerFrame; });
        return { comp: c.name, startFrame: Math.round(t * c.frameRate), frames: nFrames, fullMs: full, emptyMs: empty,
            msPerFrame: Math.round((full - empty) / nFrames), budgetMsPerFrame: Math.round(1000 / c.frameRate), rows: rows };
    }

    // sequenceFiles(item): every frame file of an image-sequence item, sorted, or null for a movie or a still.
    // item.file is the first frame only: copying it alone turns the sequence into a still in the collected project.
    var SEQ = /^(.*?)(\d{2,})\.(png|jpe?g|exr|tiff?|dpx|psd|tga|bmp)$/i;
    function sequenceFiles(it) {
        if (!it.file || it.mainSource.isStill) { return null; }
        var m = SEQ.exec(decodeURI(it.file.name)), all, i, out = [], mm;
        if (!m) { return null; }
        all = it.file.parent.getFiles();
        for (i = 0; i < all.length; i++) {
            mm = (all[i] instanceof File) ? SEQ.exec(decodeURI(all[i].name)) : null;
            if (mm && mm[1] === m[1] && mm[2].length === m[2].length && mm[3].toLowerCase() === m[3].toLowerCase()) { out.push(all[i]); }
        }
        out.sort(function (a, b) { return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0); });
        return out;
    }
    // collect(destDir, main): Collect Files stand-in. Copies the file of every footage item reached from main to
    // <dest>/Footage/ (an image sequence: all its frames, into Footage/<name>/), relinks to the copy, saves the
    // project as <dest>/<name>.aep. Originals are never touched. sidecars lists what After Effects wrote beside the
    // .aep (a "<name>.aep Logs" folder, an "Auto-Save" folder): leave them out of a handoff archive.
    function collect(dest, main, projectName) {
        var t = tree(main), fdir = AEK.core.ensureFolder(dest + "/Footage"), i, j, it, src, target, res = { copied: [], skipped: [], bytes: 0, sequences: [] };
        var frames, sdir, fps, firstOk;
        for (i = 1; i <= app.project.numItems; i++) {
            it = app.project.item(i);
            if (!isFootage(it) || !t.seen[it.id]) { continue; }
            if (it.footageMissing) { res.skipped.push({ name: it.name, why: "missing" }); continue; }
            frames = sequenceFiles(it);
            if (frames && frames.length > 1) {
                sdir = AEK.core.ensureFolder(fdir.fsName + "/" + it.id + "_" + decodeURI(it.file.name).replace(SEQ, "$1").replace(/[^\w\-]+/g, "_"));
                firstOk = true;
                for (j = 0; j < frames.length; j++) {
                    target = new File(sdir.fsName + "/" + decodeURI(frames[j].name));
                    if (!target.exists && !frames[j].copy(target.fsName)) { firstOk = false; res.skipped.push({ name: it.name, why: "copy failed: " + decodeURI(frames[j].name) }); break; }
                    res.bytes += target.length;
                }
                if (!firstOk) { continue; }
                fps = it.mainSource.conformFrameRate;
                it.replaceWithSequence(new File(sdir.fsName + "/" + decodeURI(frames[0].name)), true);
                if (fps) { it.mainSource.conformFrameRate = fps; }
                res.sequences.push({ name: it.name, frames: frames.length, to: sdir.fsName, framesNow: Math.round(it.duration * it.frameRate) });
                res.copied.push({ name: it.name, to: sdir.fsName });
                continue;
            }
            src = it.file; target = new File(fdir.fsName + "/" + decodeURI(src.name));
            if (target.exists && target.length !== src.length) { target = new File(fdir.fsName + "/" + it.id + "_" + decodeURI(src.name)); }
            if (!target.exists && !src.copy(target.fsName)) { res.skipped.push({ name: it.name, why: "copy failed: " + src.error }); continue; }
            it.replace(target); res.bytes += target.length;
            res.copied.push({ name: it.name, to: target.fsName });
        }
        var aep = new File(dest + "/" + (projectName || "collected") + ".aep");
        app.project.save(aep);
        res.project = aep.fsName; res.dirty = app.project.dirty;
        var side = new Folder(dest).getFiles(), sc = [];
        for (i = 0; i < side.length; i++) { if (side[i] instanceof Folder && /( Logs|^Auto-Save)$/.test(decodeURI(side[i].name))) { sc.push(decodeURI(side[i].name)); } }
        res.sidecars = sc;
        return res;
    }

    // saveVersion(dir, base): save as <base>_v###.aep with the next free number in dir; never overwrites
    function saveVersion(dir, base) {
        var files = new Folder(dir).getFiles(function (f) { return f instanceof File; }), n = 0, i, m, re = new RegExp("^" + base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "_v(\\d{3})\\.aep$");
        for (i = 0; i < files.length; i++) { m = re.exec(decodeURI(files[i].name)); if (m && parseInt(m[1], 10) > n) { n = parseInt(m[1], 10); } }
        var name = base + "_v" + ("00" + (n + 1)).slice(-3) + ".aep", f = new File(dir + "/" + name);
        AEK.core.ensureFolder(dir);
        app.project.save(f);
        return { saved: f.fsName, version: n + 1, dirty: app.project.dirty };
    }

    // expose(comp, prop, name): add one property of a layer of comp to its Essential Properties under a unique name
    function expose(c, prop, name) {
        if (!prop.canAddToMotionGraphicsTemplate(c)) { throw new Error("Cannot expose '" + prop.name + "' of comp " + c.name); }
        prop.addToMotionGraphicsTemplateAs(c, name);
        return { comp: c.name, name: name, count: c.motionGraphicsTemplateControllerCount };
    }
    function plain(p) { if (p.propertyType !== PropertyType.PROPERTY) { return null; } var v = p.value; return (v instanceof TextDocument) ? v.text : v; }
    // overrides(layer): the Essential Properties of a precomp layer, value and the source property each one drives
    function overrides(l) {
        var g = l.essentialProperty, out = [], i, p, src;
        for (i = 1; i <= g.numProperties; i++) {
            p = g.property(i); src = null;
            try { src = p.essentialPropertySource; } catch (e) {}
            out.push({ name: p.name, value: plain(p), source: src ? src.name : "", sourceValue: src ? plain(src) : null });
        }
        return out;
    }

    return { roots: roots, layout: layout, tree: tree, collapseRisks: collapseRisks, inventory: inventory, findFile: findFile, relink: relink, fixFonts: fixFonts, missingFonts: missingFonts, nestedRates: nestedRates,
        rename: rename, fileItems: fileItems, color: color, conformComps: conformComps, offFrameKeys: offFrameKeys,
        makeProxy: makeProxy, rewriteRefs: rewriteRefs, profile: profile, collect: collect, saveVersion: saveVersion, expose: expose, overrides: overrides,
        DEFAULT_NAME: DEFAULT_NAME };
})();
