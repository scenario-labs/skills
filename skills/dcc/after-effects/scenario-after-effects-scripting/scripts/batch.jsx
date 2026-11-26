// batch.jsx: data-driven versioning helpers (AEX.batch). ES3. Load with: ae.py run job.jsx --lib <this file>. Requires the AEK kit (core, json).
var AEX = AEX || {};
AEX.batch = (function () {
    // readText(path): UTF-8 text; a leading BOM is removed (Excel writes one in "CSV UTF-8")
    function readText(path) {
        var f = AEK.core.abs(path);
        if (!f.exists) { throw new Error("File not found: " + path); }
        f.encoding = "UTF-8";
        if (!f.open("r")) { throw new Error("Cannot open " + path + ": " + f.error); }
        var t = f.read();
        f.close();
        if (t.charCodeAt(0) === 0xFEFF) { t = t.substring(1); }
        return t;
    }
    // writeText(path, text): needs the Allow Scripts to Write Files preference; always close or the file stays locked
    function writeText(path, text) {
        var f = AEK.core.abs(path);
        AEK.core.ensureFolder(f.parent.fsName);
        f.encoding = "UTF-8";
        f.lineFeed = "Unix";
        if (!f.open("w")) { throw new Error("Cannot write " + path + ": " + f.error); }
        f.write(text);
        f.close();
        return f.fsName;
    }
    // parseCsv(text, sep): RFC 4180 rows of strings. Quoted fields may hold the separator, "" and line breaks. CRLF, LF or CR.
    function parseCsv(text, sep) {
        sep = sep || ",";
        var rows = [], row = [], cur = "", q = false, i, ch, n = text.length;
        for (i = 0; i < n; i++) {
            ch = text.charAt(i);
            if (q) {
                if (ch === "\"") {
                    if (text.charAt(i + 1) === "\"") { cur += "\""; i++; } else { q = false; }
                } else { cur += ch; }
            } else if (ch === "\"") { q = true; }
            else if (ch === sep) { row.push(cur); cur = ""; }
            else if (ch === "\r" || ch === "\n") {
                if (ch === "\r" && text.charAt(i + 1) === "\n") { i++; }
                row.push(cur); cur = "";
                if (!(row.length === 1 && row[0] === "")) { rows.push(row); }
                row = [];
            } else { cur += ch; }
        }
        if (q) { throw new Error("CSV: unclosed quote"); }
        if (cur !== "" || row.length) { row.push(cur); rows.push(row); }
        return rows;
    }
    // readCsv(path): {header: [...], rows: [{col: value, _line: n}]}. Header cells are trimmed; values are kept as typed.
    function readCsv(path, sep) {
        var a = parseCsv(readText(path), sep), head = [], out = [], r, c, o;
        if (!a.length) { throw new Error("CSV is empty: " + path); }
        for (c = 0; c < a[0].length; c++) { head.push(a[0][c].replace(/^\s+|\s+$/g, "")); }
        for (r = 1; r < a.length; r++) {
            o = { _line: r + 1 };
            if (a[r].length !== head.length) { o._error = "row has " + a[r].length + " cells, header has " + head.length; }
            for (c = 0; c < head.length; c++) { o[head[c]] = (a[r][c] === undefined) ? "" : a[r][c]; }
            out.push(o);
        }
        return { header: head, rows: out };
    }
    // fromJson(list): a JSON list of objects in the readCsv shape {header, rows: [{col: value, _line: n}]}, so validate,
    // eachRow and fill work on it. Values become strings like CSV cells; header = keys of the first object, then new keys.
    // _line is the item number + 1 (line 1 is the header in a CSV). A non-object item gets _error.
    function isList(x) { return x !== null && typeof x === "object" && typeof x.length === "number"; }
    function fromJson(list) {
        if (!isList(list)) { throw new Error("fromJson(): expected a list of objects"); }
        var head = [], seen = {}, out = [], i, k, o;
        for (i = 0; i < list.length; i++) {
            if (list[i] === null || typeof list[i] !== "object" || isList(list[i])) { continue; }
            for (k in list[i]) { if (Object.prototype.hasOwnProperty.call(list[i], k) && !seen[k]) { seen[k] = true; head.push(k); } }
        }
        for (i = 0; i < list.length; i++) {
            o = { _line: i + 2 };
            if (list[i] === null || typeof list[i] !== "object" || isList(list[i])) { o._error = "item " + (i + 1) + " is not an object"; }
            for (k = 0; k < head.length; k++) {
                var v = o._error ? undefined : list[i][head[k]];
                o[head[k]] = (v === undefined || v === null) ? "" : String(v);
            }
            out.push(o);
        }
        return { header: head, rows: out };
    }
    // readJson(path, key): a JSON file holding a list (or an object whose `key` holds the list) in the readCsv shape.
    function readJson(path, key) {
        var d = AEK.json.parse(readText(path));
        return fromJson(key ? d[key] : d);
    }
    // fill("{id}_{lang}_{ratio}", row): output names from a pattern; unsafe file-name characters become "_"
    function fill(pattern, row) {
        return pattern.replace(/\{(\w+)\}/g, function (m, k) {
            if (row[k] === undefined) { throw new Error("Pattern field {" + k + "} is not a column"); }
            return String(row[k]).replace(/[\/\\:*?"<>|\r\n]+/g, "_");
        });
    }
    // deepDuplicate(comp, suffix, bin): comp.duplicate() SHARES nested precomps; this copies every nested comp once and relinks the layers.
    // suffix defaults to "_copy"; bin is optional.
    function deepDuplicate(c, suffix, bin, seen) {
        seen = seen || {};
        if (suffix === undefined) { suffix = "_copy"; }
        var d = c.duplicate(), i, l, src, copy, copied = [];
        d.name = c.name + suffix;
        if (bin) { d.parentFolder = bin; }
        for (i = 1; i <= d.numLayers; i++) {
            l = d.layer(i);
            src = l.source;
            if (src && src instanceof CompItem) {
                if (!seen[src.id]) { seen[src.id] = deepDuplicate(src, suffix, bin, seen).comp; copied.push(src.name); }
                copy = seen[src.id];
                l.replaceSource(copy, true);
            }
        }
        return { comp: d, copied: copied };
    }
    // setText(layer, string): keeps the layer's style; returns the text read back
    function setText(l, s) {
        var p = l.property("ADBE Text Properties").property("ADBE Text Document"), d = p.value;
        d.text = s;
        p.setValue(d);
        return p.value.text;
    }
    // importOnce(path, cache): one footage item per file for the whole batch; throws on a missing file.
    // Without a cache object it uses one shared by every call of this module.
    var importCache = {};
    function importOnce(path, cache, bin) {
        cache = cache || importCache;
        if (cache[path]) { return cache[path]; }
        var f = AEK.core.abs(path), it;
        if (!f.exists) { throw new Error("Image not found: " + path); }
        it = app.project.importFile(new ImportOptions(f));
        if (bin) { it.parentFolder = bin; }
        cache[path] = it;
        return it;
    }
    // swapImage(layer, footage, box): replaceSource keeps transforms, so rescale to fit a box [w, h] in comp pixels
    function swapImage(l, it, box) {
        l.replaceSource(it, false);
        if (box) {
            var s = Math.min(box[0] / it.width, box[1] / it.height) * 100;
            l.property("ADBE Transform Group").property("ADBE Scale").setValue([s, s]);
        }
        return { name: it.name, width: it.width, height: it.height };
    }
    // resize(comp, w, h, cover, rule): comp.width/height alone do not move layers.
    // rule "short" (default): scale by the short-side ratio and keep offsets from the center, so a title block stays compact in 9:16.
    // rule "fit": scale by min(sx, sy) and keep each layer at the same fraction of the frame (shrinks a 16:9 layout into a 9:16 strip).
    // Layers named in cover[] are scaled to cover the new frame (backgrounds). Layers with keyframed Position or Scale are reported and left alone.
    function resize(c, w, h, cover, rule) {
        var sx = w / c.width, sy = h / c.height, s = (rule === "fit") ? Math.min(sx, sy) : Math.min(w, h) / Math.min(c.width, c.height);
        var cx = c.width / 2, cy = c.height / 2, i, l, tg, p, sc, skipped = [], isCover, k;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            tg = l.property("ADBE Transform Group");
            if (!tg) { continue; }
            p = tg.property("ADBE Position"); sc = tg.property("ADBE Scale");
            if (p.numKeys || sc.numKeys || p.dimensionsSeparated) { skipped.push(l.name); continue; }
            isCover = false;
            for (k = 0; cover && k < cover.length; k++) { if (cover[k] === l.name) { isCover = true; } }
            var v = p.value, z = sc.value, f = isCover ? Math.max(sx, sy) : s, nx, ny;
            if (rule === "fit" || isCover) { nx = v[0] * sx; ny = v[1] * sy; } else { nx = w / 2 + (v[0] - cx) * s; ny = h / 2 + (v[1] - cy) * s; }
            p.setValue(v.length > 2 ? [nx, ny, v[2]] : [nx, ny]);
            sc.setValue(z.length > 2 ? [z[0] * f, z[1] * f, z[2]] : [z[0] * f, z[1] * f]);
        }
        c.width = Math.round(w); c.height = Math.round(h);
        return { width: c.width, height: c.height, scale: s, rule: rule || "short", skipped: skipped };
    }
    function statusName(s) { return AEK.core.enumName(RQItemStatus, s); }
    // hasTemplate(rqItem, name, "om"|"rs"): templates differ per machine, so check before applyTemplate
    function hasTemplate(rqi, name, kind) {
        var list = kind === "rs" ? rqi.templates : rqi.outputModule(1).templates, i;
        for (i = 0; i < list.length; i++) { if (list[i] === name) { return true; } }
        return false;
    }
    // queue(comp, outPath, {om, rs, start, duration}): adds one item, leaves it QUEUED, does not render
    function queue(c, outPath, o) {
        o = o || {};
        var rq = app.project.renderQueue, rqi = rq.items.add(c), om;
        if (o.rs) {
            if (!hasTemplate(rqi, o.rs, "rs")) { rqi.remove(); throw new Error("Render settings template not found: " + o.rs); }
            rqi.applyTemplate(o.rs);
        }
        if (o.om) {
            if (!hasTemplate(rqi, o.om, "om")) { rqi.remove(); throw new Error("Output module template not found: " + o.om); }
            rqi.outputModule(1).applyTemplate(o.om);
        }
        if (o.start !== undefined) { rqi.timeSpanStart = o.start; }
        if (o.duration !== undefined) { rqi.timeSpanDuration = o.duration; }
        AEK.core.ensureFolder(AEK.core.abs(outPath).parent.fsName);
        om = rqi.outputModule(1);
        om.file = AEK.core.abs(outPath);
        return rqi;
    }
    // renderOnly(items): unqueues every other QUEUED item, renders (blocks), restores the others; returns one line per item
    function renderOnly(items) {
        var rq = app.project.renderQueue, held = [], i, j, mine, out = [], t0 = (new Date()).getTime();
        for (i = 1; i <= rq.numItems; i++) {
            mine = false;
            for (j = 0; j < items.length; j++) { if (rq.item(i) === items[j]) { mine = true; } }
            if (!mine && rq.item(i).status === RQItemStatus.QUEUED) { rq.item(i).render = false; held.push(rq.item(i)); }
        }
        for (j = 0; j < items.length; j++) { items[j].render = true; }
        rq.render();
        for (j = 0; j < items.length; j++) {
            out.push({ comp: items[j].comp.name, status: statusName(items[j].status), file: items[j].outputModule(1).file.fsName, seconds: items[j].elapsedSeconds });
        }
        for (i = 0; i < held.length; i++) { held[i].render = true; }
        return { items: out, ms: (new Date()).getTime() - t0 };
    }
    // eachRow(rows, fn): try/catch per row; one failure never stops the batch. fn(row, index) returns a result object.
    function eachRow(rows, fn) {
        var rep = { ok: [], failed: [] }, i, r;
        for (i = 0; i < rows.length; i++) {
            if (rows[i]._error) { rep.failed.push({ id: rows[i].id, line: rows[i]._line, error: rows[i]._error }); continue; }
            try { r = fn(rows[i], i) || {}; r.id = rows[i].id; rep.ok.push(r); }
            catch (e) { rep.failed.push({ id: rows[i].id, line: rows[i]._line, error: e.toString(), at: e.line }); }
        }
        return rep;
    }
    function inList(a, v) { for (var k = 0; k < a.length; k++) { if (a[k] === v) { return true; } } return false; }
    // validate(csv, {required: [col], allowed: {col: [values]}, range: {col: [min, max]}, maxLength: {col: n}, unique: [col]}): run before any build.
    // A missing required column stops at once: a header that differs from the layer name silently does nothing.
    // Every rule is optional: a missing one is an empty list or object (ExtendScript throws on for-in over undefined).
    function validate(csv, rules) {
        rules = rules || {};
        var out = [], req = rules.required || [], uni = rules.unique || [], seen = {}, i, j, r, col, v, key;
        var allowed = rules.allowed || {}, range = rules.range || {}, maxLength = rules.maxLength || {};
        for (j = 0; j < req.length; j++) { if (!inList(csv.header, req[j])) { out.push({ id: null, line: 1, error: "Missing column: " + req[j] }); } }
        if (out.length) { return out; }
        for (i = 0; i < csv.rows.length; i++) {
            r = csv.rows[i];
            if (r._error) { out.push({ id: r.id, line: r._line, error: r._error }); continue; }
            for (j = 0; j < req.length; j++) { if (r[req[j]] === "") { out.push({ id: r.id, line: r._line, error: "Empty " + req[j] }); } }
            for (col in allowed) {
                if (Object.prototype.hasOwnProperty.call(allowed, col) && !inList(allowed[col], r[col])) {
                    out.push({ id: r.id, line: r._line, error: col + " '" + r[col] + "' is not one of " + allowed[col].join(", ") });
                }
            }
            for (col in range) {
                if (Object.prototype.hasOwnProperty.call(range, col)) {
                    v = parseFloat(r[col]);
                    if (isNaN(v) || String(r[col]).replace(/^\s+|\s+$/g, "") === "" || v < range[col][0] || v > range[col][1]) {
                        out.push({ id: r.id, line: r._line, error: col + " '" + r[col] + "' is not a number from " + range[col][0] + " to " + range[col][1] });
                    }
                }
            }
            for (col in maxLength) {
                if (Object.prototype.hasOwnProperty.call(maxLength, col)) {
                    v = String(r[col] === undefined ? "" : r[col]);
                    if (v.length > maxLength[col]) { out.push({ id: r.id, line: r._line, error: col + " has " + v.length + " characters, limit " + maxLength[col] }); }
                }
            }
            for (j = 0; j < uni.length; j++) {
                key = uni[j] + "\u0001" + r[uni[j]];
                if (seen[key]) { out.push({ id: r.id, line: r._line, error: "Duplicate " + uni[j] + " '" + r[uni[j]] + "' (also line " + seen[key] + ")" }); } else { seen[key] = r._line; }
            }
        }
        return out;
    }
    // writeCsv(path, header, rows): quotes a field holding the separator, a quote or a line break; readCsv reads it back intact
    function writeCsv(path, header, rows) {
        function cell(v) {
            var s = (v === undefined || v === null) ? "" : String(v);
            var q = s.indexOf("\"") >= 0 || s.indexOf(",") >= 0 || s.indexOf("\n") >= 0 || s.indexOf("\r") >= 0;
            return q ? "\"" + s.split("\"").join("\"\"") + "\"" : s;
        }
        var lines = [], i, j, a = [];
        for (j = 0; j < header.length; j++) { a.push(cell(header[j])); }
        lines.push(a.join(","));
        for (i = 0; i < rows.length; i++) {
            a = [];
            for (j = 0; j < header.length; j++) { a.push(cell(rows[i][header[j]])); }
            lines.push(a.join(","));
        }
        return writeText(path, lines.join("\n") + "\n");
    }
    // resumeQueue(verified): a saved project keeps QUEUED after aerender (-close defaults to DO_NOT_SAVE_CHANGES).
    // verified = output file names (no folder) that passed the probe. Those items are unqueued; any other existing
    // output is renamed "<name>.incomplete" (kept, never deleted) so the rerender writes a fresh file.
    function resumeQueue(verified) {
        var rq = app.project.renderQueue, i, it, f, name, n, out = { skipped: [], requeued: [], renamed: [] };
        for (i = 1; i <= rq.numItems; i++) {
            it = rq.item(i);
            if (it.status !== RQItemStatus.QUEUED && it.status !== RQItemStatus.UNQUEUED) { continue; }
            f = it.outputModule(1).file;
            if (!f) { continue; }
            name = decodeURI(f.name);
            if (f.exists && inList(verified, name)) { it.render = false; out.skipped.push(name); continue; }
            if (f.exists) {
                n = name + ".incomplete";
                for (var k = 2; new File(f.parent.fsName + "/" + n).exists; k++) { n = name + ".incomplete" + k; }
                if (!f.rename(n)) { throw new Error("Cannot rename " + name + ": " + f.error); }
                out.renamed.push(n);
            }
            it.render = true;
            out.requeued.push(name);
        }
        return out;
    }
    // freeSpace(folder): {freeMB, folder} on the volume that holds the folder (its nearest existing parent), read with df -k.
    // macOS and Linux only (system.callSystem needs Allow Scripts to Write Files). Returns freeMB null when df gives nothing.
    function freeSpace(path) {
        var f = new Folder(path);
        while (f && !f.exists) { f = f.parent; }
        var out = system.callSystem('/bin/df -k "' + (f ? f.fsName : "/") + '"'), lines = out.split(/\r?\n/), cols;
        cols = lines.length > 1 ? lines[1].replace(/^\s+|\s+$/g, "").split(/\s+/) : [];
        return { folder: f ? f.fsName : "/", freeMB: cols.length > 3 ? Math.round(parseInt(cols[3], 10) / 1024) : null };
    }
    // diskCheck(folder, bytesNeeded, margin): refuses a render that would fill the volume (margin default 2, twice the estimate)
    // or that cannot write its file: the folder is created and a probe file written and removed (a folder aerender cannot
    // write gives exit 0 and no file). `aerenders` counts aerender processes already running: two that write into one
    // folder at the same time lose a render with exit 0, so give each its own output folder (`ok` stays true).
    function diskCheck(path, bytes, margin) {
        var d = new Folder(path), probe, writable = false;
        if (!d.exists) { d.create(); }
        probe = new File(d.fsName + "/.aex_write_probe");
        if (probe.open("w")) { writable = probe.write("x") && probe.close(); probe.remove(); }
        var fs = freeSpace(path), needMB = Math.ceil(bytes * (margin || 2) / 1048576);
        var ps = system.callSystem("/bin/ps -A -o comm"), n = 0, lines = ps.split(/\r?\n/), i;
        for (i = 0; i < lines.length; i++) { if (/(^|\/)aerender$/.test(lines[i].replace(/\s+$/, ""))) { n++; } }
        var why = "";   // if/else: a chained ?: returned its second branch here on 27.0
        if (!writable) { why = "cannot write in " + d.fsName; } else if (fs.freeMB === null || fs.freeMB < needMB) { why = fs.freeMB + " MB free, " + needMB + " MB needed"; }
        return { ok: why === "", why: why, freeMB: fs.freeMB, needMB: needMB, folder: fs.folder, writable: writable, aerenders: n };
    }
    // renderManifest(file): writes "path<TAB>frames" for every output of every QUEUED item, for render_guarded.sh, which then
    // also fails an item that never started. Returns the rows.
    function renderManifest(path) {
        var rq = app.project.renderQueue, rows = [], txt = "", i, j, it;
        for (i = 1; i <= rq.numItems; i++) {
            it = rq.item(i);
            if (it.status !== RQItemStatus.QUEUED) { continue; }
            var fr = Math.round(it.timeSpanDuration / it.comp.frameDuration);
            for (j = 1; j <= it.numOutputModules; j++) {
                if (it.outputModule(j).file) { rows.push({ path: it.outputModule(j).file.fsName, frames: fr }); txt += it.outputModule(j).file.fsName + "\t" + fr + "\n"; }
            }
        }
        writeText(path, txt);
        return rows;
    }
    return { freeSpace: freeSpace, diskCheck: diskCheck, renderManifest: renderManifest, readText: readText, writeText: writeText, parseCsv: parseCsv, readCsv: readCsv, readJson: readJson, fromJson: fromJson, fill: fill, deepDuplicate: deepDuplicate,
        setText: setText, importOnce: importOnce, swapImage: swapImage, resize: resize, statusName: statusName, hasTemplate: hasTemplate,
        queue: queue, renderOnly: renderOnly, eachRow: eachRow, validate: validate, writeCsv: writeCsv, resumeQueue: resumeQueue };
})();
