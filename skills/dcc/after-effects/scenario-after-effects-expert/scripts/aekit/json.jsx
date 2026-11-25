// aekit/json.jsx: JSON for ExtendScript (the engine has no native JSON object).
var AEK = AEK || {};
AEK.json = (function () {
    function q(s) {
        var out = '"', i, c, code;
        for (i = 0; i < s.length; i++) {
            c = s.charAt(i); code = s.charCodeAt(i);
            if (c === '"') { out += '\\"'; }
            else if (c === "\\") { out += "\\\\"; }
            else if (c === "\n") { out += "\\n"; }
            else if (c === "\r") { out += "\\r"; }
            else if (c === "\t") { out += "\\t"; }
            else if (code < 32 || code > 126) { out += "\\u" + ("0000" + code.toString(16)).slice(-4); }
            else { out += c; }
        }
        return out + '"';
    }
    function str(v, depth) {
        var t = typeof v, a = [], i, k;
        if (v === null || v === undefined) { return "null"; }
        if (t === "number") { return isFinite(v) ? String(v) : "null"; }
        if (t === "boolean") { return v ? "true" : "false"; }
        if (t === "string") { return q(v); }
        if (depth > 12) { return q("[depth]"); }
        if (v instanceof Array) {
            for (i = 0; i < v.length; i++) { a.push(str(v[i], depth + 1)); }
            return "[" + a.join(",") + "]";
        }
        if (v instanceof File || v instanceof Folder) { return q(v.fsName); }
        if (t === "object") {
            // host objects (layers, properties, items) are reduced to a readable tag, never walked
            if (v.constructor !== Object) {
                try { return q("<" + (v.matchName || v.typeName || v.constructor.name || "object") + (v.name ? " " + v.name : "") + ">"); }
                catch (e) { return q("<object>"); }
            }
            for (k in v) { if (v.hasOwnProperty(k) && typeof v[k] !== "function") { a.push(q(String(k)) + ":" + str(v[k], depth + 1)); } }
            return "{" + a.join(",") + "}";
        }
        return q(String(v));
    }
    return {
        stringify: function (v) { return str(v, 0); },
        // parse is for files written by the runner or by AEK.json.stringify (trusted input)
        parse: function (text) { return eval("(" + text + ")"); }
    };
})();
