// aekit/expr.jsx: write expressions and prove they evaluate. Requires core.jsx.
var AEK = AEK || {};
AEK.expr = (function () {
    // set(prop, code, times): assigns the expression, evaluates it at each time, and throws with the engine's message if it fails.
    // An expression never throws at assignment: the error only shows in property.expressionError after an evaluation.
    function set(p, code, times) {
        var i, v = null, t = times || [0];
        if (!p.canSetExpression) { throw new Error("'" + p.name + "' cannot take an expression"); }
        p.expression = code;
        for (i = 0; i < t.length; i++) { try { v = p.valueAtTime(t[i], false); } catch (e) {} }
        if (p.expressionError !== "") { throw new Error("Expression on '" + p.name + "' failed: " + p.expressionError.replace(/\s+/g, " ")); }
        return { property: p.name, enabled: p.expressionEnabled, value: v };
    }
    // list(comp): every expression in a comp, with its error if any
    function list(c) {
        var out = [], i, l;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            AEK.core.walk(l, function (p) {
                if (p.propertyType !== PropertyType.PROPERTY) { return; }
                var ex = ""; try { if (p.canSetExpression) { ex = p.expression; } } catch (e) { return; }
                if (ex === "") { return; }
                out.push({ layer: l.name, index: l.index, property: p.name, matchName: p.matchName, enabled: p.expressionEnabled,
                    error: p.expressionError.replace(/\s+/g, " "), lines: ex.split(/\r\n|\r|\n/).length, code: ex.substring(0, 400) });
            });
        }
        return out;
    }
    // check(comp, n): evaluates every expression at n times across the comp, because some fail only on some frames
    function check(c, n) {
        var all = [], bad = [], i, l, j, t;
        n = n || 5;
        for (i = 1; i <= c.numLayers; i++) {
            l = c.layer(i);
            AEK.core.walk(l, function (p) {
                if (p.propertyType !== PropertyType.PROPERTY) { return; }
                var ex = ""; try { if (p.canSetExpression) { ex = p.expression; } } catch (e) { return; }
                if (ex === "") { return; }
                all.push(p);
                for (j = 0; j < n; j++) {
                    t = (n === 1) ? 0 : (c.duration - c.frameDuration) * j / (n - 1);
                    try { p.valueAtTime(t, false); } catch (e1) {}
                    if (p.expressionError !== "") { bad.push({ layer: l.name, property: p.name, time: t, error: p.expressionError.replace(/\s+/g, " ").substring(0, 300) }); break; }
                }
            });
        }
        return { expressions: all.length, failed: bad.length, errors: bad };
    }
    // bake(prop, comp, t0, t1): one keyframe per frame from the expression result, then the expression is switched off (kept as text)
    function bake(p, c, t0, t1) {
        var times = [], values = [], t, fd = c.frameDuration;
        t0 = (t0 === undefined) ? 0 : t0; t1 = (t1 === undefined) ? c.duration - fd : t1;
        for (t = t0; t <= t1 + fd / 2; t += fd) { times.push(t); values.push(p.valueAtTime(t, false)); }
        p.expressionEnabled = false;
        p.setValuesAtTimes(times, values);
        return { property: p.name, keys: p.numKeys };
    }
    var CONTROLS = { slider: "ADBE Slider Control", checkbox: "ADBE Checkbox Control", color: "ADBE Color Control", point: "ADBE Point Control",
        angle: "ADBE Angle Control", layer: "ADBE Layer Control", dropdown: "ADBE Dropdown Control", point3d: "ADBE Point3D Control" };
    // controls(layer, [{type, name, value, items:[...] for dropdown}]): expression controls on a controller layer
    function controls(l, defs) {
        var out = [], i, d, e, idx;
        for (i = 0; i < defs.length; i++) {
            d = defs[i];
            if (!CONTROLS[d.type]) { throw new Error("controls(): unknown type '" + d.type + "'"); }
            e = l.property("ADBE Effect Parade").addProperty(CONTROLS[d.type]);
            idx = e.propertyIndex;
            if (d.type === "dropdown" && d.items) {
                // setPropertyParameters returns the property again; the effect must be renamed after it, never before
                e = l.property("ADBE Effect Parade").property(idx).property(1).setPropertyParameters(d.items).propertyGroup(1);
                idx = e.propertyIndex;
            }
            l.property("ADBE Effect Parade").property(idx).name = d.name;
            if (d.value !== undefined) { l.property("ADBE Effect Parade").property(idx).property(1).setValue(d.value); }
            out.push({ name: d.name, type: d.type, index: idx, ref: 'effect("' + d.name + '")(1)' });
        }
        return out;
    }
    return { set: set, list: list, check: check, bake: bake, controls: controls };
})();
