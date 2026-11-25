// ae_bridge.jsx: resident mailbox bridge for After Effects (ExtendScript, ES3).
// Start it once per session: File > Scripts > Run Script File, or copy it to the user
// Scripts/Startup folder so it starts with the application (ae_env.py install-bridge).
// It polls <userData>/AEAgentBridge/inbox for <id>.jsx jobs, runs each one with dialogs
// suppressed, and writes <id>.json to outbox. status.json is the heartbeat.
// Needs: Settings > Scripting & Expressions > Allow Scripts to Write Files and Access Network.
(function (g) {
    var VERSION = "1.5.0";
    // aerender and render-engine instances also run Startup scripts: they must never take jobs meant for the interactive session
    try { if (app.isRenderEngine || app.isWatchFolder) { return; } } catch (e00) {}
    // Measured on 27.0 (macOS): the aerendercore instance that aerender starts runs the Startup scripts with isRenderEngine
    // false. Its own process name tells it apart: only the interactive application ("MacOS/After Effects") may host the bridge.
    var SELF = { pid: "", comm: "" };
    try {
        if ($.os.indexOf("Mac") >= 0) {
            var psOut = String(system.callSystem("/bin/ps -o pid=,comm= -p $PPID")).replace(/^\s+|\s+$/g, "");
            SELF.pid = psOut.split(/\s+/)[0]; SELF.comm = psOut.substring(SELF.pid.length).replace(/^\s+/, "");
            if (SELF.comm && !/\/MacOS\/After Effects$/.test(SELF.comm)) { return; }
        }
    } catch (e01) {}
    if (g.__aeBridge && g.__aeBridge.version === VERSION && g.__aeBridge.taskId !== null) { return; }
    if (g.__aeBridge && g.__aeBridge.stop) { try { g.__aeBridge.stop(); } catch (e0) {} }
    var B = { version: VERSION, root: null, busy: false, lastBeat: 0, taskId: null, jobs: 0, last: "" };
    g.__aeBridge = B;

    function q(s) {
        s = String(s);
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
    function writeAtomic(path, text) {
        var tmp = new File(path + ".tmp");
        tmp.encoding = "UTF-8";
        if (!tmp.open("w")) { return false; }
        tmp.write(text);
        tmp.close();
        var dst = new File(path);
        if (dst.exists) { dst.remove(); }
        return tmp.rename(dst.name);
    }
    function now() { return (new Date()).getTime(); }
    function beat(state) {
        var proj = "", dirty = false;
        try { proj = app.project.file ? app.project.file.fsName : ""; dirty = app.project.dirty; } catch (e) {}
        writeAtomic(B.root.fsName + "/status.json",
            '{"bridge":' + q(B.version) + ',"ae":' + q(app.version) + ',"state":' + q(state) +
            ',"time":' + now() + ',"jobs":' + B.jobs + ',"last":' + q(B.last) +
            ',"project":' + q(proj) + ',"dirty":' + (dirty ? "true" : "false") + ',"pid":' + q(SELF.pid) + "}");
        B.lastBeat = now();
    }
    // beginSuppressDialogs() hides the application's own error dialogs, NOT the script functions alert(), confirm() and
    // prompt(): those open a modal window that nothing can close from outside when the application is in the background.
    // The job text is evaluated in a scope where the three names are harmless local functions.
    function runJob(file) {
        var alert = function (m) { B.said.push("alert: " + m); };
        var confirm = function (m) { B.said.push("confirm (answered true): " + m); return true; };
        var prompt = function (m, d) { B.said.push("prompt (answered default): " + m); return d === undefined ? "" : d; };
        var __src;
        B.said = [];
        file.encoding = "UTF-8";
        if (!file.open("r")) { throw new Error("Cannot read job " + file.fsName); }
        __src = file.read();
        file.close();
        return eval(__src);
    }
    B.poll = function () {
        if (B.busy) { return; }
        var inbox = new Folder(B.root.fsName + "/inbox");
        var files = inbox.getFiles("*.jsx");
        if (!files.length) {
            if (now() - B.lastBeat > 2000) { beat("idle"); }
            return;
        }
        files.sort(function (a, b) { return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0); });
        var job = files[0];
        var id = decodeURI(job.name).replace(/\.jsx$/, "");
        var outPath = B.root.fsName + "/outbox/" + id + ".json";
        var t0 = now(), res = "", err = null;
        B.busy = true;
        B.last = id;
        // The job leaves the inbox BEFORE it runs: a job that blocks or crashes the application is never run twice.
        var running = new File(B.root.fsName + "/running/" + job.name);
        if (running.exists) { running.remove(); }
        if (!job.copy(running.fsName) || !job.remove()) { B.busy = false; return; }
        beat("running");
        try { app.beginSuppressDialogs(); } catch (e1) {}
        try { res = runJob(running); } catch (e2) { err = e2; }
        try { app.endSuppressDialogs(false); } catch (e3) {}
        try {
            if (!(new File(outPath)).exists) {
                if (err) {
                    writeAtomic(outPath, '{"ok":false,"error":' + q(err.toString()) + ',"line":' + (err.line || 0) +
                        ',"ms":' + (now() - t0) + ',"ae":' + q(app.version) + ',"from":"bridge"}');
                } else {
                    writeAtomic(outPath, '{"ok":true,"result":' + q(res === undefined || res === null ? "" : res) +
                        ',"ms":' + (now() - t0) + ',"ae":' + q(app.version) + ',"from":"bridge"}');
                }
            }
            running.copy(B.root.fsName + "/done/" + running.name);
            running.remove();
        } catch (e4) {}
        B.jobs++;
        B.busy = false;
        beat("idle");
    };
    // Jobs found in running/ at start were interrupted by a quit, a crash or a kill: report them, do not run them again.
    // A job is left alone when the heartbeat says another live process is running it (an instance this guard did not catch).
    function ownerAlive() {
        var st = new File(B.root.fsName + "/status.json"), txt = "", m;
        try { if (!st.exists || !st.open("r")) { return false; } txt = st.read(); st.close(); } catch (e) { return false; }
        m = /"state":"running"[\s\S]*"pid":"(\d+)"/.exec(txt);
        if (!m || m[1] === SELF.pid || $.os.indexOf("Mac") < 0) { return false; }
        try { return String(system.callSystem("/bin/ps -o comm= -p " + m[1])).indexOf("/MacOS/After Effects") >= 0; } catch (e2) { return false; }
    }
    function sweep() {
        var left = (new Folder(B.root.fsName + "/running")).getFiles("*.jsx"), i, id;
        if (left.length && ownerAlive()) { return; }
        for (i = 0; i < left.length; i++) {
            id = decodeURI(left[i].name).replace(/\.jsx$/, "");
            if (!(new File(B.root.fsName + "/outbox/" + id + ".json")).exists) {
                writeAtomic(B.root.fsName + "/outbox/" + id + ".json", '{"ok":false,"error":"The application stopped while this job was running. It was not run again.","interrupted":true,"from":"bridge"}');
            }
            left[i].copy(B.root.fsName + "/failed/" + left[i].name);
            left[i].remove();
        }
    }
    B.start = function () {
        B.root = new Folder(Folder.userData.fsName + "/AEAgentBridge");
        var subs = ["", "/inbox", "/outbox", "/running", "/done", "/failed"], i, f;
        for (i = 0; i < subs.length; i++) { f = new Folder(B.root.fsName + subs[i]); if (!f.exists) { f.create(); } }
        sweep();
        beat("started");
        B.taskId = app.scheduleTask("$.global.__aeBridge.poll()", 300, true);
    };
    B.stop = function () {
        if (B.taskId !== null) { app.cancelTask(B.taskId); B.taskId = null; beat("stopped"); }
    };
    try { B.start(); } catch (e5) {}
})($.global);
"ae_bridge started";
