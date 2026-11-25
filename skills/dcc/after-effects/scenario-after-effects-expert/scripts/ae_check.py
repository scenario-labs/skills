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
    ("error", r",\s*[\]}]", "trailing comma: a syntax error in ES3 objects and arrays"),
    ("error", r"[\"']~/", "path starting with ~: resolves to a cloud-synced folder on some Macs, pass an absolute path"),
    ("error", r"(^|[^\w.$])(Folder\.selectDialog|File\.openDialog|File\.saveDialog)\s*\(|\.(openDlg|saveDlg|selectDlg)\s*\(", "file dialog: blocks an unattended session, take the path from ARGS"),
    ("error", r"^(?!.*DO_NOT_SAVE)(?!.*function open\b).*(^|[^\w.$])app\.open\s*\(", "app.open() with unsaved changes in the open project raises a Save As panel that blocks the session: ask the person to save, or in a test session use AEK.core.open(path)"),
    ("warn", r"(^|[^\w.$])(alert|confirm|prompt)\s*\(", "alert/confirm/prompt: only logged inside a job, never shown; return the message instead"),
    ("warn", r"app\.quit\s*\(", "app.quit(): ends the session and every other job in the queue"),
    ("warn", r"app\.project\.close\s*\(|AEK\.core\.fresh\s*\(", "closes the open project: test sessions only, never in a user's session"),
    ("warn", r"app\.executeCommand\s*\(", "menu command: depends on the active viewer and selection, prefer the scripting API"),
    ("warn", r"\.property\(\s*[\"'][A-Z][a-z]+( [A-Z]?[a-z]+)*[\"']\s*\)", "display name lookup: breaks on a non-English After Effects, use the match name"),
    ("warn", r"new Window\s*\(|ScriptUI", "ScriptUI window: needs a person in front of the application"),
    ("warn", r"\.remove\s*\(\s*\)", "remove(): check that the target was created by this job"),
]
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
    while i < n:
        c = src[i]
        prev = "".join(out).rstrip()[-1:] if out else ""
        if c == "/" and i + 1 < n and src[i + 1] not in "/*" and (prev == "" or prev in "(,=:[!&|?{};"):
            j = i + 1  # regular expression literal
            while j < n and src[j] != "/" and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            out.append("/re/")
            i = j + 1
        elif c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * src[i:j].count("\n"))
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1] if keep_strings else c + "s" * 0 + c)
            if keep_strings is False and src[i + 1:i + 3] == "~/":
                out[-1] = c + "~/" + c
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def scan(src, rules, name):
    findings = []
    clean = strip_comments_and_strings(src)
    for n, line in enumerate(clean.split("\n"), 1):
        for sev, rx, msg in rules:
            if re.search(rx, line):
                findings.append({"severity": sev, "file": name, "line": n, "message": msg, "source": src.split("\n")[n - 1].strip()[:140]})
    # the display-name rule needs the string content
    for n, line in enumerate(src.split("\n"), 1):
        if line.strip().startswith("//"):
            continue
        for sev, rx, msg in rules:
            if "display name" in msg and re.search(rx, line) and "ADBE" not in line:
                findings.append({"severity": sev, "file": name, "line": n, "message": msg, "source": line.strip()[:140]})
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
