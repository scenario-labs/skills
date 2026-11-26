// aekit/core.jsx: lookups and small helpers shared by every other module. Requires json.jsx.
var AEK = AEK || {};
AEK._log = AEK._log || [];
AEK.log = function (msg) { AEK._log.push(String(msg)); };
AEK.core = (function () {
    function items(test) {
        var out = [], i, it;
        for (i = 1; i <= app.project.numItems; i++) { it = app.project.item(i); if (!test || test(it)) { out.push(it); } }
        return out;
    }
    function comps() { return items(function (it) { return it instanceof CompItem; }); }
    function item(name) {
        var found = items(function (it) { return it.name === name; });
        if (found.length === 0) { throw new Error("No project item named '" + name + "'"); }
        if (found.length > 1) { throw new Error(found.length + " project items are named '" + name + "': use AEK.core.itemById"); }
        return found[0];
    }
    function comp(name) {
        var found = [], all = comps(), i, names = [];
        for (i = 0; i < all.length; i++) { names.push(all[i].name); if (all[i].name === name) { found.push(all[i]); } }
        if (found.length === 1) { return found[0]; }
        if (found.length > 1) { throw new Error(found.length + " comps are named '" + name + "'"); }
        throw new Error("No comp named '" + name + "'. Comps: " + names.slice(0, 30).join(", "));
    }
    function itemById(id) { return app.project.itemByID(id); }
    function layer(c, nameOrIndex) {
        var l = (typeof nameOrIndex === "number") ? c.layer(nameOrIndex) : c.layers.byName(nameOrIndex);
        if (!l) {
            var names = [], i;
            for (i = 1; i <= Math.min(c.numLayers, 40); i++) { names.push(c.layer(i).name); }
            throw new Error("No layer '" + nameOrIndex + "' in comp '" + c.name + "'. Layers: " + names.join(", "));
        }
        return l;
    }
    // prop(layer, ["ADBE Transform Group", "ADBE Position"]): match names first, display names second
    function prop(base, path) {
        var p = base, i, next;
        for (i = 0; i < path.length; i++) {
            next = p.property(path[i]);
            if (!next) {
                var have = [], j;
                try { for (j = 1; j <= Math.min(p.numProperties, 30); j++) { have.push(p.property(j).matchName); } } catch (e) {}
                throw new Error("Property '" + path[i] + "' not found under '" + p.name + "' (path " + path.join(" > ") + "). Children: " + have.join(", "));
            }
            p = next;
        }
        return p;
    }
    // walk(group, fn): fn(property, depth) for every leaf and group under a layer or property group
    function walk(group, fn, depth) {
        var i, p;
        depth = depth || 0;
        for (i = 1; i <= group.numProperties; i++) {
            p = group.property(i);
            fn(p, depth);
            if (p.propertyType !== PropertyType.PROPERTY) { walk(p, fn, depth + 1); }
        }
    }
    // abs(path): refuses "~" because ExtendScript resolves it to a cloud-synced folder on some Macs
    function abs(path) {
        if (!path || path.charAt(0) === "~") { throw new Error("Pass an absolute path, not '" + path + "'"); }
        return new File(path);
    }
    function ensureFolder(path) {
        var f = new Folder(path);
        if (!f.exists && !f.create()) { throw new Error("Cannot create folder " + path); }
        return f;
    }
    function bin(name, parent) {
        var found = items(function (it) { return it instanceof FolderItem && it.name === name && (!parent || it.parentFolder === parent); });
        if (found.length) { return found[0]; }
        var f = app.project.items.addFolder(name);
        if (parent) { f.parentFolder = parent; }
        return f;
    }
    // enumName(KeyframeInterpolationType, value) -> "BEZIER": enum values print as numbers otherwise
    function enumName(enumObj, value) { var k; for (k in enumObj) { if (enumObj[k] === value) { return k; } } return String(value); }
    function frame(c, seconds) { return Math.round(seconds * c.frameRate); }
    function time(c, frames) { return frames * c.frameDuration; }
    // fresh(path): test sessions only. Closes the open project WITHOUT saving, whoever left it dirty, then starts a new one.
    // A new project keeps the bit depth, working space and linear blending of the project that was open before it, so the
    // defaults are written back: 8 bpc, no working space, JavaScript engine. With an absolute path the new project is saved
    // there at once: it has a file and no unsaved changes, so a later open or close by another job raises no Save As panel.
    function fresh(path) {
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); app.newProject(); // DO_NOT_SAVE first: a dirty project would raise a Save As panel
        defaults();
        if (path) { save(path); }
        return app.project;
    }
    // save(path): save without any dialog. With an absolute path: Save As to that file (the open project moves there).
    // Without one: saves in place, and refuses an untitled project, where app.project.save() opens a Save As panel.
    function save(path) {
        var f;
        if (path) {
            f = abs(path);
            ensureFolder(f.parent.fsName);
            app.project.save(f);
        } else {
            if (!app.project.file) { throw new Error("The open project has never been saved: pass an absolute .aep path (app.project.save() would open a Save As panel)"); }
            app.project.save(app.project.file);
        }
        return { path: app.project.file.fsName, dirty: app.project.dirty };
    }
    function defaults() {
        var p = app.project;
        // Color engine first: 0 is Adobe color management, 1 is OCIO (no enum exists in 27.0). OCIO mode refuses 8 and 16 bpc.
        try { p.colorManagementSystem = 0; } catch (e0) {}
        try { p.linearizeWorkingSpace = false; } catch (e1) {}
        try { p.workingSpace = "None"; } catch (e2) {}
        try { p.bitsPerChannel = 8; } catch (e3) {}
        try { p.linearBlending = false; } catch (e5) {}
        try { p.workingGamma = 2.4; } catch (e6) {}
        try { p.expressionEngine = "javascript-1.0"; } catch (e4) {}
        return { bpc: p.bitsPerChannel, colorEngine: p.colorManagementSystem, workingSpace: p.workingSpace, linearize: p.linearizeWorkingSpace,
            linearBlending: p.linearBlending, workingGamma: p.workingGamma, expressionEngine: p.expressionEngine };
    }
    // open(path): test sessions only. Closes the open project WITHOUT saving, then opens the file.
    // A bare app.open() on a project with unsaved changes raises a Save As panel that nothing can close from outside.
    // Whoever left the open project dirty (this job, another agent), the close discards it first, so no panel can open.
    function open(path) {
        var f = abs(path);
        if (!f.exists) { throw new Error("Project not found: " + path); }
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); return app.open(f); // DO_NOT_SAVE first: no Save As panel
    }
    function info() {
        return {
            ae: app.version, os: $.os, language: app.isoLanguage,
            project: app.project.file ? app.project.file.fsName : "", dirty: app.project.dirty,
            items: app.project.numItems, comps: comps().length,
            bpc: app.project.bitsPerChannel, workingSpace: app.project.workingSpace,
            expressionEngine: app.project.expressionEngine,
            activeComp: (app.project.activeItem instanceof CompItem) ? app.project.activeItem.name : ""
        };
    }
    return { items: items, comps: comps, item: item, itemById: itemById, comp: comp, layer: layer, prop: prop, walk: walk,
        enumName: enumName, abs: abs, ensureFolder: ensureFolder, bin: bin, frame: frame, time: time, fresh: fresh, save: save, defaults: defaults, open: open, info: info };
})();
