"""Runs the offline ExtendScript checker (ae_check.py) on planted jobs and expressions.

After Effects runs ExtendScript (ES3): a job written with modern JavaScript fails inside the
application, often after it has blocked the session. The checker is the gate the lead skill puts
before every send, so each rule is planted here once, a clean job must pass, and every shipped
skill folder must pass its own `--skill` check (code-block headers, frontmatter, links, the
shipped .jsx files). The .jsx files themselves only run inside After Effects.
"""

import contextlib
import gc
import io
import sys
import tempfile
import unittest
import unittest.mock
import warnings
from pathlib import Path

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
sys.path.insert(0, str(FAMILY / "scenario-after-effects-expert" / "scripts"))

import ae_check  # noqa: E402

CLEAN_JOB = """\
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), names = [], i;
for (i = 1; i <= c.numLayers; i++) { names.push(c.layer(i).name); }
var pos = c.layer(1).property("ADBE Transform Group").property("ADBE Position");
var o = { "default": 1, label: "ok", re: /,\\s*}/ };
var s = "a string with => and ` and let x inside";
return { names: names, value: pos.value, o: o, s: s };
"""

# (planted line, words the finding must contain)
PLANTED = [
    ("let n = 1;", "let/const"),
    ("const n = 1;", "let/const"),
    ("var f = (a) => a + 1;", "arrow function"),
    ("var t = `x${1}`;", "template literal"),
    ("var o = JSON.parse(s);", "no JSON object"),
    ("layers.forEach(function (l) {});", "ES5+ array method"),
    ("var k = Object.keys(o);", "Object.keys"),
    ("var t = s.trim();", "String.trim"),
    ("class Rig {}", "class syntax"),
    # a first key "default" is left alone: "{ default:" is also a switch's default case
    ("var o = { a: 1, default: 2 };", "reserved word"),
    ("var o = { new: 1 };", "reserved word"),
    ("var a = [1, 2, ];", "trailing comma"),
    ('var f = new File("~/out.json");', "path starting with ~"),
    ("var f = Folder.selectDialog();", "file dialog"),
    ('app.open(new File(ARGS.path));', "Save As panel"),
]

WARNED = [
    ('alert("done");', "alert/confirm/prompt"),
    ("app.quit();", "app.quit()"),
    ("app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);", "closes the open project"),
    ("app.executeCommand(3088);", "menu command"),
    ('var p = l.property("Position");', "display name"),
    ('var w = new Window("palette");', "ScriptUI"),
    ("l.remove();", "remove()"),
]


def findings(src, rules=ae_check.ES3):
    return ae_check.scan(src, rules, "job.jsx")


class Es3Rules(unittest.TestCase):
    def test_clean_job_has_no_finding(self):
        self.assertEqual(findings(CLEAN_JOB), [])

    def test_each_planted_trap_is_an_error(self):
        for line, words in PLANTED:
            with self.subTest(line=line):
                found = [f for f in findings(CLEAN_JOB + line + "\n") if f["severity"] == "error"]
                self.assertTrue(any(words in f["message"] for f in found), found)
                self.assertTrue(all(f["line"] == CLEAN_JOB.count("\n") + 1 for f in found if f["line"]), found)

    def test_each_risky_call_is_a_warning_only(self):
        for line, words in WARNED:
            with self.subTest(line=line):
                found = findings(CLEAN_JOB + line + "\n")
                self.assertTrue(any(words in f["message"] and f["severity"] == "warn" for f in found), found)
                self.assertFalse([f for f in found if f["severity"] == "error"], found)

    def test_traps_inside_comments_and_strings_are_ignored(self):
        src = '// let x = () => 1; JSON.parse(s)\n/* class A {} */\nvar s = "const y = `z`";\nreturn s;\n'
        self.assertEqual(findings(src), [])

    def test_unbalanced_brackets_are_an_error(self):
        found = findings("if (a) { return [1, 2;\n")
        messages = sorted(f["message"] for f in found)
        self.assertEqual(messages, ["unbalanced '[' (+1)", "unbalanced '{' (+1)"])


class ExpressionRules(unittest.TestCase):
    def check(self, src):
        return ae_check.check_expression(src, "rig.expr.js")

    def test_clean_expression_passes(self):
        src = "seedRandom(index, true);\nvar w = thisLayer.sourceRectAtTime(time, false).width;\nif (w > 10) { [w, 0] } else { [0, 0] }\n"
        self.assertEqual([f for f in self.check(src) if f["severity"] == "error"], [])

    def test_this_instead_of_thisLayer_is_an_error(self):
        found = self.check("this.position + [10, 0];\n")
        self.assertTrue(any("thisLayer" in f["message"] and f["severity"] == "error" for f in found), found)

    def test_final_if_without_else_is_an_error(self):
        found = self.check("var v = effect(\"Slider Control\")(1);\nif (v > 0) v * 2;\n")
        self.assertTrue(any("if that has no else" in f["message"] for f in found), found)

    def test_unseeded_random_and_layer_index_are_warnings(self):
        found = self.check("thisComp.layer(3).transform.position + random(5);\n")
        messages = " ".join(f["message"] for f in found)
        self.assertIn("seedRandom", messages)
        self.assertIn("layer by index", messages)


class Cli(unittest.TestCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            with unittest.mock.patch.object(sys, "argv", ["ae_check.py", *argv]), contextlib.redirect_stdout(out):
                code = ae_check.main()
            gc.collect()
        leaks = [str(w.message) for w in caught if issubclass(w.category, ResourceWarning)]
        return code, out.getvalue(), leaks

    def test_exit_code_follows_errors_not_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            good, warn, bad = Path(tmp, "good.jsx"), Path(tmp, "warn.jsx"), Path(tmp, "bad.jsx")
            good.write_text(CLEAN_JOB, encoding="utf-8")
            warn.write_text(CLEAN_JOB + 'alert("x");\n', encoding="utf-8")
            bad.write_text(CLEAN_JOB + "let x = 1;\n", encoding="utf-8")
            self.assertEqual(self.run_main(str(good)), (0, "0 error(s), 0 warning(s)\n", []))
            code, out, leaks = self.run_main(str(warn))
            self.assertEqual((code, leaks), (0, []))
            self.assertIn("1 warning(s)", out)
            code, out, leaks = self.run_main(str(bad), "--json")
            self.assertEqual((code, leaks), (1, []))
            self.assertIn('"let/const: ExtendScript is ES3, use var"', out)

    def test_skill_check_flags_a_code_block_without_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp, "scenario-after-effects-demo")
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: scenario-after-effects-demo\ndescription: Use when testing.\nlicense: MIT\n---\n"
                "# Demo\n\n```javascript\nvar a = 1;\nreturn a;\n```\n", encoding="utf-8")
            found = ae_check.check_skill(str(skill))
        messages = [f["message"] for f in found if f["severity"] == "error"]
        self.assertIn("code block without a 'channel:' header comment", messages)
        self.assertIn("code block without a 'checked:' header comment", messages)


class ShippedSkills(unittest.TestCase):
    def test_every_shipped_skill_passes_its_own_check(self):
        skills = sorted(p for p in FAMILY.iterdir() if (p / "SKILL.md").is_file())
        self.assertEqual(len(skills), 15)
        for skill in skills:
            with self.subTest(skill=skill.name):
                errors = [f for f in ae_check.check_skill(str(skill)) if f["severity"] == "error"]
                self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
