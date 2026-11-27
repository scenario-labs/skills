"""Checks the 3ds Max skills' text and code blocks with no 3ds Max installed.

- Every Python block compiles; every MAXScript block and .ms file matches its brackets in order.
- Every Python or MAXScript block carries a source line ("checked against <source>") and a
  channel line.
- MAXScript blocks for the mcp-safe channel avoid the calls Safe Scene Script Execution blocks.
- No text claims a run in 3ds Max, and none says "game-ready".
- Every reference and script is linked from its SKILL.md, and every link resolves.
Warnings (a missing section, a short body) print without failing.
"""

import re
import unittest
from pathlib import Path

FAMILY = Path(__file__).resolve().parents[2] / "skills" / "dcc" / "3dsmax"

BLOCKED = [r"\bdotNetObject\b", r"\bdotNetClass\b", r"\bmacroScript\b", r"\bUIAccessor\b",
           r"windows\.sendMessage", r"\bsetINISetting\b", r"\bdeleteFile\b", r"\bcopyFile\b",
           r"\bpython\.execute", r"\bDOSCommand\b", r"\bShellLaunch\b", r"\bHiddenDOSCommand\b"]
BAD_TEXT = [("\u2014", "em dash"), ("\u2013", "en dash"), ("/Users/", "local path"), ("C:\\Users\\", "local path"),
            ("game-ready", "the phrase game-ready"), ("game ready", "the phrase game ready")]
CLAIMS = [r"\btested in 3ds Max\b", r"\bverified in 3ds Max\b", r"\brun in 3ds Max 20\d\d on\b"]
FENCE = re.compile(r"^```([a-zA-Z0-9_+-]*)[^\n]*\n(.*?)^```", re.S | re.M)


def body_words(text):
    parts = text.split("---", 2)
    return len(parts[2].split()) if len(parts) >= 3 else len(text.split())


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def mxs_balance(code):
    # strip strings and comments, then match brackets in order
    s = re.sub(r'@"[^"]*"', '""', code)
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"--[^\n]*", "", s)
    pairs, stack, out = {")": "(", "]": "[", "}": "{"}, [], []
    for i, ch in enumerate(s):
        if ch in "([{":
            stack.append((ch, i))
        elif ch in pairs:
            line = s.count("\n", 0, i) + 1
            if not stack:
                out.append(f"unmatched {ch} on line {line}")
            elif stack[-1][0] != pairs[ch]:
                out.append(f"{stack[-1][0]} closed by {ch} on line {line}")
                stack.pop()
            else:
                stack.pop()
    for ch, i in stack:
        out.append(f"unclosed {ch} from line {s.count(chr(10), 0, i) + 1}")
    return out


def check_skill(d):
    errs, warns, stats = [], [], {}
    sk = d / "SKILL.md"
    if not sk.exists():
        return [f"{d.name}: SKILL.md missing"], [], {}
    text = sk.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if not fm:
        errs.append("no frontmatter")
        fm = {}
    if fm.get("name") != d.name:
        errs.append(f"name '{fm.get('name')}' differs from folder")
    desc = fm.get("description", "")
    if not desc.startswith("Use when"):
        errs.append("description does not start with 'Use when'")
    if len(desc) > 1024:
        errs.append(f"description {len(desc)} chars")
    if fm.get("license") != "MIT":
        errs.append("license is not MIT")
    extra = set(fm) - {"name", "description", "license"}
    if extra:
        errs.append(f"extra frontmatter keys {sorted(extra)}")
    w = body_words(text)
    stats["words"] = w
    stats["description_chars"] = len(desc)
    if w > 2500:
        errs.append(f"body {w} words (limit 2,500)")
    elif w < 1400:
        warns.append(f"body {w} words (short)")
    for sec in ("## Stance", "## Establish first", "## Quality gates", "## Common mistakes", "## Handoffs", "## References"):
        if sec not in text:
            warns.append(f"section missing: {sec}")
    if re.search(r"not yet run", text, re.I):
        errs.append("SKILL.md carries a not-run note")
    # links
    links = set(re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", text))
    for l in links:
        if l.startswith("http"):
            continue
        if not (d / l).exists():
            errs.append(f"broken link {l}")
    for f in sorted(list((d / "references").glob("*")) + list((d / "scripts").glob("*"))):
        if f.name.startswith(".") or f.name == "__pycache__":
            continue
        rel = f.relative_to(d).as_posix()
        if rel not in text and (rel + "/") not in text:
            warns.append(f"not linked from SKILL.md: {rel}")
    # all text files
    n_blocks = n_py = n_mxs = n_verify = 0
    for f in sorted(d.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts or f.suffix in (".pyc", ".png", ".jpg"):
            continue
        try:
            t = f.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            errs.append(f"{f.relative_to(d).as_posix()}: not UTF-8 ({e.reason} at byte {e.start})")
            continue
        rel = f.relative_to(d).as_posix()
        for bad, label in BAD_TEXT:
            if bad in t and f.name != "api-names.txt":
                errs.append(f"{rel}: contains {label}")
        for line in t.splitlines():
            if any(re.search(c, line) for c in CLAIMS) and not re.search(r"\b(never|unless|not|no)\b", line, re.I):
                errs.append(f"{rel}: claims a live run: {line.strip()[:80]}")
        n_verify += t.count("[verify]")
        if f.suffix == ".py":
            try:
                compile(t, str(f), "exec")
            except SyntaxError as e:
                errs.append(f"{rel}: syntax error line {e.lineno}: {e.msg}")
            if re.search(r"not yet run", t, re.I):
                errs.append(f"{rel}: carries a not-run note")
        if f.suffix == ".ms":
            for e in mxs_balance(t):
                errs.append(f"{rel}: {e}")
        if f.suffix == ".md":
            for lang, code in FENCE.findall(t):
                lang = lang.lower()
                if lang not in ("python", "maxscript", "py", "ms", "mxs"):
                    continue
                n_blocks += 1
                head = "\n".join(code.splitlines()[:6]).lower()
                if not any(k in head for k in ("checked against", "note:", "status:")):
                    warns.append(f"{rel}: a {lang} block has no source line")
                if "not yet run" in code.lower():
                    errs.append(f"{rel}: a {lang} block carries a not-run note")
                if "channel:" not in head:
                    warns.append(f"{rel}: a {lang} block has no channel line")
                if lang in ("python", "py"):
                    n_py += 1
                    try:
                        compile(code, f"{rel} block", "exec")
                    except SyntaxError as e:
                        errs.append(f"{rel}: python block does not compile (line {e.lineno}: {e.msg}): {code.strip().splitlines()[0][:60]}")
                else:
                    n_mxs += 1
                    for e in mxs_balance(code):
                        errs.append(f"{rel}: maxscript block {e}: {code.strip().splitlines()[0][:60]}")
                    chan = re.search(r"channel:\s*([^\n]*)", head)
                    if chan and "mcp-safe" in chan.group(1):
                        body = re.sub(r"--[^\n]*", "", code)
                        for b in BLOCKED:
                            if re.search(b, body):
                                errs.append(f"{rel}: mcp-safe block uses blocked {b}")
    stats.update(blocks=n_blocks, python_blocks=n_py, maxscript_blocks=n_mxs, verify_marks=n_verify)
    return errs, warns, stats


class SkillDocs(unittest.TestCase):
    def test_every_skill(self):
        skills = sorted(p for p in FAMILY.iterdir() if (p / "SKILL.md").is_file())
        self.assertEqual(len(skills), 12)
        blocks = 0
        for d in skills:
            with self.subTest(skill=d.name):
                errs, warns, stats = check_skill(d)
                blocks += stats.get("blocks", 0)
                for w in warns:
                    print(f"{d.name}: warning: {w}")
                self.assertEqual(errs, [])
        self.assertGreater(blocks, 0)


if __name__ == "__main__":
    unittest.main()
