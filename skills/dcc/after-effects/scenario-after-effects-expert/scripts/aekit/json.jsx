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
    // parse(text): strict JSON grammar, read by hand and never evaluated (a data file may come from anyone)
    function parse(text) {
        var s = String(text), i = 0, n = s.length;
        var ESC = { "\"": "\"", "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t" };
        function fail(what) { throw new Error("AEK.json.parse: " + what + " at character " + i); }
        function ws() { var c; while (i < n) { c = s.charAt(i); if (c === " " || c === "\t" || c === "\n" || c === "\r") { i++; } else { break; } } }
        function word(w, v) { if (s.substr(i, w.length) !== w) { fail("unexpected token"); } i += w.length; return v; }
        function string() {
            var out = "", c, h;
            i++;
            while (i < n) {
                c = s.charAt(i);
                if (c === "\"") { i++; return out; }
                if (c === "\\") {
                    c = s.charAt(i + 1);
                    if (c === "u") {
                        h = s.substr(i + 2, 4);
                        if (!/^[0-9a-fA-F]{4}$/.test(h)) { fail("bad \\u escape"); }
                        out += String.fromCharCode(parseInt(h, 16)); i += 6;
                    } else if (ESC.hasOwnProperty(c)) { out += ESC[c]; i += 2; } else { fail("bad escape"); }
                } else if (c.charCodeAt(0) < 32) { fail("control character in a string"); } else { out += c; i++; }
            }
            fail("unterminated string");
        }
        function digits() { var j = i; while (i < n && s.charAt(i) >= "0" && s.charAt(i) <= "9") { i++; } return i - j; }
        function number() {
            var j = i;
            if (s.charAt(i) === "-") { i++; }
            if (s.charAt(i) === "0") { i++; } else if (!digits()) { fail("bad number"); }
            if (s.charAt(i) === ".") { i++; if (!digits()) { fail("bad number"); } }
            if (s.charAt(i) === "e" || s.charAt(i) === "E") {
                i++;
                if (s.charAt(i) === "+" || s.charAt(i) === "-") { i++; }
                if (!digits()) { fail("bad number"); }
            }
            return Number(s.substring(j, i));
        }
        function value() {
            var c, a, o, k;
            ws();
            c = s.charAt(i);
            if (c === "{") {
                o = {}; i++; ws();
                if (s.charAt(i) === "}") { i++; return o; }
                while (true) {
                    ws(); if (s.charAt(i) !== "\"") { fail("expected a string key"); }
                    k = string(); ws();
                    if (s.charAt(i) !== ":") { fail("expected ':'"); }
                    i++; o[k] = value(); ws();
                    c = s.charAt(i); i++;
                    if (c === "}") { return o; }
                    if (c !== ",") { i--; fail("expected ',' or '}'"); }
                }
            }
            if (c === "[") {
                a = []; i++; ws();
                if (s.charAt(i) === "]") { i++; return a; }
                while (true) {
                    a.push(value()); ws();
                    c = s.charAt(i); i++;
                    if (c === "]") { return a; }
                    if (c !== ",") { i--; fail("expected ',' or ']'"); }
                }
            }
            if (c === "\"") { return string(); }
            if (c === "t") { return word("true", true); }
            if (c === "f") { return word("false", false); }
            if (c === "n") { return word("null", null); }
            if (c === "-" || (c >= "0" && c <= "9")) { return number(); }
            fail(i >= n ? "unexpected end of input" : "unexpected token");
        }
        var v = value();
        ws();
        if (i < n) { fail("unexpected text after the value"); }
        return v;
    }
    return {
        stringify: function (v) { return str(v, 0); },
        parse: parse
    };
})();
