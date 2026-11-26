#!/usr/bin/env python3
"""ae_check.py: offline checks before anything is sent to After Effects. Standard library only.

  ae_check.py job.jsx [more.jsx ...]        ExtendScript (ES3) traps in job files and kit modules
  ae_check.py --expr rig.expr.js            expression traps (JavaScript engine)
  ae_check.py --skill path/to/skill-folder  code-block headers, wording and size of a skill

Exit code 1 when an error is found. Warnings do not fail.
"""
import argparse, glob, json, os, re, sys


def _read_text(path, **kw):
    with open(path, encoding=kw.pop("encoding", "utf-8"), **kw) as fh:
        return fh.read()


ES3 = [
    ("error", r"(^|[^\w.$])(let|const)\s+[\w${\[]", "let/const: ExtendScript is ES3, use var"),
    ("error", r"=>", "arrow function: use function () {}"),
    ("error", r"`", "template literal: build strings with +"),
    ("error", r"(^|[^\w.$])JSON\.(parse|stringify)", "no JSON object in ExtendScript: use AEK.json"),
    ("error", r"\.(forEach|map|filter|reduce|some|every|includes|find|findIndex)\s*\(", "ES5+ array method: write a for loop"),
    ("error", r"(^|[^\w.$])Object\.(keys|values|entries|assign)\s*\(", "Object.keys and friends do not exist: use for (k in o) with hasOwnProperty"),
    ("error", r"\.trim\s*\(\s*\)", "String.trim does not exist: use replace(/^\\s+|\\s+$/g, '')"),
    ("error", r"(^|[^\w.$])class\s+\w+", "class syntax: use functions"),
    # measured on 27.0 (lead test 12): ExtendScript rejects every one of these as an unquoted object key
    # a key on its own line after "{" or "," is caught too (the scan runs line by line); r"\s" here, a doubled backslash matched nothing
    ("error", r"(^|[{,])\s*(abstract|boolean|break|byte|case|catch|char|class|const|continue|debugger|delete|do|double|else|enum|export|extends|false|final|finally|float|for|function|goto|if|implements|import|in|instanceof|int|interface|long|native|new|null|package|private|protected|public|return|short|static|super|switch|synchronized|this|throw|throws|transient|true|try|typeof|var|void|volatile|while|with)\s*:(?!:)", "reserved word as an object key: the whole job fails with \'Illegal use of reserved word\', quote the key"),
    ("error", r",\s*default\s*:", "reserved word as an object key: quote \"default\""),
    ("error", r"\b(var|function)\s+(abstract|boolean|byte|char|class|const|double|enum|export|extends|final|float|goto|implements|import|int|interface|long|native|package|private|protected|public|short|static|super|synchronized|throws|transient|volatile)\b", "reserved word as a variable or function name: the whole job fails with \'Illegal use of reserved word\' (as a dotted property, M.final works)"),
    ("error", r",\s*[\]}]", "trailing comma: a syntax error in ES3 objects and arrays"),
    ("error", r"[\"']~/", "path starting with ~: resolves to a cloud-synced folder on some Macs, pass an absolute path"),
    ("error", r"(^|[^\w.$])(Folder\.selectDialog|File\.openDialog|File\.saveDialog)\s*\(|\.(openDlg|saveDlg|selectDlg)\s*\(", "file dialog: blocks an unattended session, take the path from ARGS"),
    # dialog class: the runner refuses a job that matches one of these (ae.py run, unless --no-preflight)
    ("error", r"^(?!.*DO_NOT_SAVE)(?!.*function open\b).*(^|[^\w.$])app\.open\s*\(", "dialog: app.open() over unsaved changes (left by this job or by another agent) raises a Save As panel that blocks every agent: in a test session use AEK.core.open(path); in a person's session ask them to save first"),
    ("error", r"^(?!.*DO_NOT_SAVE).*(^|[^\w.$])app\.newProject\s*\(", "dialog: app.newProject() over unsaved changes raises a Save As panel: in a test session use AEK.core.fresh(path)"),
    ("error", r"(^|[^\w$])app\.project\.save\s*\(\s*\)", "dialog: app.project.save() on a project that was never saved opens a Save As panel: use AEK.core.save(path) with an absolute path, or AEK.core.save() which refuses an untitled project"),
    ("warn", r"(^|[^\w.$])(alert|confirm|prompt)\s*\(", "alert/confirm/prompt: only logged inside a job, never shown; return the message instead"),
    ("warn", r"app\.quit\s*\(", "app.quit(): ends the session and every other job in the queue"),
    ("warn", r"app\.project\.close\s*\(|AEK\.core\.(fresh|open)\s*\(", "closes the open project without saving: test sessions only, never in a user's session"),
    ("warn", r"app\.executeCommand\s*\(", "menu command: depends on the active viewer and selection, prefer the scripting API"),
    ("warn", r"\.property\(\s*[\"'][A-Z][a-z]+( [A-Z]?[a-z]+)*[\"']\s*\)", "display name lookup: breaks on a non-English After Effects, use the match name"),
    ("warn", r"new Window\s*\(|ScriptUI", "ScriptUI window: needs a person in front of the application"),
    ("warn", r"\.remove\s*\(\s*\)", "remove(): check that the target was created by this job"),
]
DIALOG_PREFIX = "dialog:"
# Match names of layer-level properties (transform, masks, text, shapes, 3D, audio, markers): a near miss is a typo that
# returns null at run time ("null is not an object"). Effect match names are not listed: they are not checked.
KNOWN_MATCH_NAMES = set("""
ADBE Transform Group|ADBE Anchor Point|ADBE Position|ADBE Position_0|ADBE Position_1|ADBE Position_2|ADBE Scale|ADBE Orientation|ADBE Rotate X|ADBE Rotate Y|ADBE Rotate Z|ADBE Opacity
ADBE Envir Appear in Reflect|ADBE Mask Parade|ADBE Mask Atom|ADBE Mask Shape|ADBE Mask Feather|ADBE Mask Opacity|ADBE Mask Offset|ADBE Effect Parade|ADBE Marker|ADBE Time Remapping
ADBE Audio Group|ADBE Audio Levels|ADBE Layer Styles|ADBE Layer Overrides|ADBE Material Options Group|ADBE Casts Shadows|ADBE Accepts Shadows|ADBE Accepts Lights|ADBE Ambient Coefficient
ADBE Diffuse Coefficient|ADBE Specular Coefficient|ADBE Shininess Coefficient|ADBE Metal Coefficient|ADBE Light Transmission|ADBE Extrsn Options Group|ADBE Extrsn Depth|ADBE Bevel Styles|ADBE Bevel Depth|ADBE Bevel Direction
ADBE Camera Options Group|ADBE Camera Zoom|ADBE Camera Depth of Field|ADBE Camera Focus Distance|ADBE Camera Aperture|ADBE Camera Blur Level|ADBE Camera Focus Area Width
ADBE Light Options Group|ADBE Light Intensity|ADBE Light Color|ADBE Light Cone Angle|ADBE Light Cone Feather 2|ADBE Light Falloff Type|ADBE Light Shadow Darkness|ADBE Light Shadow Diffusion
ADBE Text Properties|ADBE Text Document|ADBE Text Path Options|ADBE Text Path|ADBE Text More Options|ADBE Text Anchor Point Option|ADBE Text Anchor Point Align|ADBE Text Animators|ADBE Text Animator
ADBE Text Selectors|ADBE Text Selector|ADBE Text Wiggly Selector|ADBE Text Expressible Selector|ADBE Text Animator Properties|ADBE Text Range Advanced|ADBE Text Selector Max Amount|ADBE Text Selector Mode
ADBE Text Range Units|ADBE Text Range Type2|ADBE Text Range Shape|ADBE Text Levels Max Ease|ADBE Text Levels Min Ease|ADBE Text Randomize Order|ADBE Text Random Seed|ADBE Text Percent Start|ADBE Text Percent End
ADBE Text Percent Offset|ADBE Text Index Start|ADBE Text Index End|ADBE Text Index Offset|ADBE Text Expressible Amount|ADBE Text Position 3D|ADBE Text Anchor Point 3D|ADBE Text Scale 3D|ADBE Text Skew|ADBE Text Skew Axis
ADBE Text Rotation|ADBE Text Rotation X|ADBE Text Rotation Y|ADBE Text Opacity|ADBE Text Fill Color|ADBE Text Stroke Color|ADBE Text Stroke Width|ADBE Text Tracking Amount|ADBE Text Tracking Type|ADBE Text Line Spacing
ADBE Text Blur|ADBE Text Character Offset|ADBE Text Fill Opacity|ADBE Text Stroke Opacity|ADBE Text Wiggly Max Amount|ADBE Text Wiggly Min Amount|ADBE Text Wiggly Random Seed|ADBE Text Temporal Freq
ADBE Root Vectors Group|ADBE Vector Group|ADBE Vectors Group|ADBE Vector Transform Group|ADBE Vector Anchor|ADBE Vector Position|ADBE Vector Scale|ADBE Vector Rotation|ADBE Vector Group Opacity
ADBE Vector Shape - Group|ADBE Vector Shape|ADBE Vector Shape - Rect|ADBE Vector Rect Size|ADBE Vector Rect Position|ADBE Vector Rect Roundness|ADBE Vector Shape - Ellipse|ADBE Vector Ellipse Size
ADBE Vector Ellipse Position|ADBE Vector Shape - Star|ADBE Vector Star Points|ADBE Vector Star Position|ADBE Vector Star Inner Radius|ADBE Vector Star Outer Radius|ADBE Vector Star Rotation
ADBE Vector Graphic - Fill|ADBE Vector Fill Color|ADBE Vector Fill Opacity|ADBE Vector Graphic - Stroke|ADBE Vector Stroke Color|ADBE Vector Stroke Width|ADBE Vector Stroke Opacity|ADBE Vector Stroke Line Cap
ADBE Vector Stroke Line Join|ADBE Vector Stroke Dashes|ADBE Vector Stroke Taper|ADBE Vector Stroke Wave|ADBE Vector Graphic - G-Fill|ADBE Vector Graphic - G-Stroke|ADBE Vector Filter - Trim|ADBE Vector Trim Start
ADBE Vector Trim End|ADBE Vector Trim Offset|ADBE Vector Filter - Repeater|ADBE Vector Repeater Copies|ADBE Vector Repeater Offset|ADBE Vector Repeater Transform|ADBE Vector Repeater Position
ADBE Vector Repeater Rotation|ADBE Vector Filter - Merge|ADBE Vector Merge Type|ADBE Vector Filter - Offset|ADBE Vector Offset Amount|ADBE Vector Filter - RC|ADBE Vector Filter - Roughen|ADBE Vector Filter - Twist
ADBE Vector Filter - Wiggler|ADBE Vector Filter - Zigzag|ADBE Vector Filter - PB|ADBE Vector Layer|ADBE Text Layer|ADBE AV Layer|ADBE Camera Layer|ADBE Light Layer|ADBE 3D Model Layer
ADBE Slider Control|ADBE Point Control|ADBE Point3D Control|ADBE Angle Control|ADBE Color Control|ADBE Checkbox Control|ADBE Layer Control|ADBE Dropdown Control
""".replace("\n", "|").split("|")) - {""}


def match_name_warnings(line, name, n):
    """Near misses of a known layer-level match name: 'ADBE Postion' -> 'ADBE Position'."""
    import difflib
    out = []
    for mn in re.findall(r"[\"'](ADBE [A-Za-z0-9 _&.-]+)[\"']", line):
        if mn in KNOWN_MATCH_NAMES or re.search(r"-\d{4}$", mn) or mn.endswith(" "):
            continue
        near = difflib.get_close_matches(mn, KNOWN_MATCH_NAMES, 1, 0.85)
        if near:
            out.append({"severity": "warn", "file": name, "line": n, "message": "unknown match name '%s': did you mean '%s'? A wrong name returns null at run time" % (mn, near[0]), "source": line.strip()[:140]})
    return out


CREATES = r"(\.add\w*\s*\(|\.duplicate\s*\(|AEK\.build\.|AEK\.text\.add|AEK\.xio\.|AEX\.\w+\.\w+\s*\(|new\s+(File|Folder)\s*\(|precompose\s*\(|\.importFile\s*\(|\.outputModule\s*\()"


def removes_own(clean, line):
    """True when every X.remove() on the line targets something this file created (X assigned from an add, a duplicate, a kit builder, a new File)."""
    hits = re.findall(r"([\w$]+)(?:\.[\w$]+|\([^()]*\)|\[[^\]]*\])*\.remove\s*\(\s*\)", line)
    # a chain that starts with a helper call (AEX.type.animatorByName(t, "exit")...remove()) targets its first argument
    hits = [(re.match(r"\s*([A-Za-z_$][\w$]*)", m.group(1)).group(1) if m and re.match(r"\s*([A-Za-z_$][\w$]*)", m.group(1)) else b)
            for b, m in [(b, re.search(re.escape(b) + r"(?:\.[\w$]+)+\(([^()]*)\)[^;]*\.remove\s*\(", line) if b in ("AEX", "AEK") else None) for b in hits]]
    if not hits or re.search(r"\.add\w*\s*\([^;]*\.remove\s*\(", line):
        return bool(hits)
    for base in hits:
        if not re.search(r"(^|[^\w$.])" + re.escape(base) + r"\s*=\s*[^;=][^;]*" + CREATES, clean, re.M):
            return False
    return True
EXPR = [
    ("error", r"(^|[^\w.$])this\s*\.\s*(position|scale|rotation|opacity|transform|effect|text|name|index|inPoint|outPoint)\b", "this.x: in the JavaScript engine this is not the layer, use thisLayer"),
    ("error", r"(^|[^\w.$])this\s*\(", "this(...): use thisLayer(...) or thisProperty"),
    ("warn", r"\bsnapToGrid\b|\.reflect\b", "legacy-only member"),
    ("warn", r"Math\.random\s*\(", "Math.random() changes on every evaluation: use random() with seedRandom(seed, true)"),
    ("warn", r"(^|[^\w.$])random\s*\(", "random(): add seedRandom(index, true) first if the value must hold still over time"),
    ("warn", r"\.valueAtTime\(\s*time\s*-\s*[\d.]+\s*\)", "fixed delay in seconds: express delays in frames with framesToTime() or thisComp.frameDuration"),
    ("warn", r"thisComp\.layer\(\s*\d+\s*\)", "layer by index: breaks when layers are reordered, use the layer name or a Layer Control"),
    ("warn", r"comp\(\s*\"", "reads another comp by name: breaks on rename and blocks multi-frame caching less well, expose it through Essential Properties when possible"),
]


def strip_comments_and_strings(src, keep_strings=False):
    out, i, n = [], 0, len(src)
    last = [""]  # last non-space character emitted: a join of `out` per character made the scan quadratic

    def emit(s):
        out.append(s)
        t = s.rstrip()
        if t:
            last[0] = t[-1]
    while i < n:
        c = src[i]
        prev = last[0]
        if c == "/" and i + 1 < n and src[i + 1] not in "/*" and (prev == "" or prev in "(,=:[!&|?{};"):
            j = i + 1  # regular expression literal
            while j < n and src[j] != "/" and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            emit("/re/")
            i = j + 1
        elif c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            emit("\n" * src[i:j].count("\n"))
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            if keep_strings:
                emit(src[i:j + 1])
            elif src[i + 1:i + 3] == "~/":
                emit(c + "~/" + c)
            else:
                emit(c + c)
            i = j + 1
        else:
            emit(c)
            i += 1
    return "".join(out)


def scan(src, rules, name):
    findings = []
    clean = strip_comments_and_strings(src)
    for n, line in enumerate(clean.split("\n"), 1):
        for sev, rx, msg in rules:
            if re.search(rx, line):
                if msg.startswith("remove():") and removes_own(clean, line):
                    continue
                findings.append({"severity": sev, "file": name, "line": n, "message": msg, "source": src.split("\n")[n - 1].strip()[:140]})
    if rules is ES3:
        # the line rule above cannot see a comma whose closing bracket sits on a later line
        for m in re.finditer(r",[ \t]*\n\s*[\]}]", clean):
            n = clean.count("\n", 0, m.start()) + 1
            findings.append({"severity": "error", "file": name, "line": n, "message": "trailing comma: a syntax error in ES3 objects and arrays", "source": src.split("\n")[n - 1].strip()[:140]})
    # the display-name rule needs the string content
    for n, line in enumerate(src.split("\n"), 1):
        if line.strip().startswith("//"):
            continue
        for sev, rx, msg in rules:
            if "display name" in msg and re.search(rx, line) and "ADBE" not in line:
                findings.append({"severity": sev, "file": name, "line": n, "message": msg, "source": line.strip()[:140]})
        if rules is ES3:
            findings += match_name_warnings(line, name, n)
    bal = {"(": 0, "[": 0, "{": 0}
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in clean:
        if ch in bal:
            bal[ch] += 1
        elif ch in pairs:
            bal[pairs[ch]] -= 1
    for k, v in bal.items():
        if v != 0:
            findings.append({"severity": "error", "file": name, "line": 0, "message": "unbalanced '%s' (%+d)" % (k, v), "source": ""})
    return findings


def check_expression(src, name):
    findings = scan(src, EXPR, name)
    body = strip_comments_and_strings(src).strip()
    tail = body[body.rfind("\n", 0, len(body.rstrip("; \n}"))) + 1:] if body else ""
    if re.search(r"(^|[;}\s])if\s*\(", body) and re.search(r"if\s*\([^;{]*\)\s*[^;{]+;?\s*$", body) and not re.search(r"\belse\b", tail):
        findings.append({"severity": "error", "file": name, "line": body.count("\n") + 1,
                         "message": "the expression ends with an if that has no else: the JavaScript engine needs a value on every path", "source": tail.strip()[:140]})
    return findings


def check_skill(folder):
    findings = []
    md_files = [os.path.join(folder, "SKILL.md")] + sorted(glob.glob(os.path.join(folder, "references", "*.md")))
    for path in md_files:
        if not os.path.exists(path):
            findings.append({"severity": "error", "file": path, "line": 0, "message": "missing file", "source": ""})
            continue
        text = _read_text(path)
        rel = os.path.relpath(path, folder)
        for n, line in enumerate(text.split("\n"), 1):
            if "\u2014" in line:
                findings.append({"severity": "error", "file": rel, "line": n, "message": "em dash", "source": line.strip()[:100]})
            if re.search(r"/Users/|C:\\\\Users\\\\[a-z]", line) and "<" not in line:
                findings.append({"severity": "error", "file": rel, "line": n, "message": "local path", "source": line.strip()[:100]})
        blocks = re.findall(r"```(\w+)\n(.*?)```", text, re.S)
        for lang, code in blocks:
            if lang in ("javascript", "js", "jsx", "extendscript"):
                head = "\n".join(code.split("\n")[:4])
                kind = "expression" if re.search(r"//\s*expression", head) else "job"
                if "channel:" not in head and kind == "job":
                    findings.append({"severity": "error", "file": rel, "line": 0, "message": "code block without a 'channel:' header comment", "source": code.split("\n")[0][:100]})
                if "checked:" not in head:
                    findings.append({"severity": "error", "file": rel, "line": 0, "message": "code block without a 'checked:' header comment", "source": code.split("\n")[0][:100]})
                found = check_expression(code, rel) if kind == "expression" else scan(code, ES3, rel)
                findings += [f for f in found if not (kind == "job" and "closes the open project" in f["message"])]
        if rel == "SKILL.md":
            m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
            if not m:
                findings.append({"severity": "error", "file": rel, "line": 1, "message": "no frontmatter", "source": ""})
            else:
                fm, body = m.group(1), m.group(2)
                keys = re.findall(r"^(\w[\w-]*):", fm, re.M)
                if sorted(keys) != ["description", "license", "name"]:
                    findings.append({"severity": "error", "file": rel, "line": 1, "message": "frontmatter keys must be name, description, license (found %s)" % keys, "source": ""})
                nm = re.search(r"^name:\s*(.+)$", fm, re.M)
                if nm and nm.group(1).strip() != os.path.basename(os.path.normpath(folder)):
                    findings.append({"severity": "error", "file": rel, "line": 1, "message": "name differs from the folder name", "source": nm.group(1)})
                d = re.search(r"^description:\s*(.+)$", fm, re.M)
                if d and (len(d.group(1)) > 1024 or "Use when" not in d.group(1)[:12]):
                    findings.append({"severity": "error", "file": rel, "line": 1, "message": "description must start with 'Use when' and stay under 1,024 characters (%d)" % len(d.group(1)), "source": ""})
                words = len(body.split())
                findings.append({"severity": "error" if words > 2500 else "info", "file": rel, "line": 0, "message": "body %d words (limit 2,500)" % words, "source": ""})
                for ref in sorted(glob.glob(os.path.join(folder, "references", "*.md"))):
                    if "references/" + os.path.basename(ref) not in body:
                        findings.append({"severity": "error", "file": rel, "line": 0, "message": "reference not linked from SKILL.md: " + os.path.basename(ref), "source": ""})
    for path in sorted(glob.glob(os.path.join(folder, "scripts", "**", "*.jsx"), recursive=True)):
        src = _read_text(path)
        findings += [f for f in scan(src, ES3, os.path.relpath(path, folder)) if f["severity"] == "error"]
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--expr", action="append", default=[], help="expression file")
    ap.add_argument("--skill", action="append", default=[], help="skill folder")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    findings = []
    for f in a.files:
        findings += scan(_read_text(f), ES3, f)
    for f in a.expr:
        findings += check_expression(_read_text(f), f)
    for f in a.skill:
        findings += check_skill(f)
    if a.json:
        print(json.dumps(findings, indent=1))
    else:
        for f in findings:
            print("%-5s %s:%s  %s%s" % (f["severity"].upper(), f["file"], f["line"], f["message"], ("   | " + f["source"]) if f["source"] else ""))
        e = sum(1 for f in findings if f["severity"] == "error")
        print("%d error(s), %d warning(s)" % (e, sum(1 for f in findings if f["severity"] == "warn")))
    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
