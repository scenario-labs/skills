"""Review round 2, expression references: AEX.expressions.renameLayer and AEX.project.rewriteRefs under Node.

- A layer reference inside a string literal, a template literal, a regex literal, a line comment or a block
  comment stays byte for byte; real calls are rewritten in both quote styles, with spaces inside the parentheses.
- An escaped quote inside a string does not end it; a disabled expression stays disabled.
- A comp named hasOwnProperty or __proto__ does not break the comp name lookup of rewriteRefs.

The module files are loaded as shipped in a Node vm with After Effects stand-ins. No After Effects, no network.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
EXPRESSIONS = FAMILY / "scenario-after-effects-expressions" / "scripts" / "expressions.jsx"
PROJECT = FAMILY / "scenario-after-effects-project" / "scripts" / "project.jsx"

HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const [file, mode, spec] = process.argv.slice(1);
const S = JSON.parse(spec);
function prop(name, ex, on) {
  const p = { name, propertyType: 1, canSetExpression: true, expressionEnabled: on !== false, _ex: ex };
  // After Effects turns an expression back on when its text is assigned (measured in 27.0)
  Object.defineProperty(p, "expression", { get() { return this._ex; }, set(v) { this._ex = v; this.expressionEnabled = true; } });
  return p;
}
const comps = S.comps.map((c) => {
  const layers = c.layers.map((l) => ({ name: l.name, props: l.exprs.map((e, i) => prop("P" + i, e.text, e.on)) }));
  return { name: c.name, id: c.id, numLayers: layers.length, layer: (j) => layers[j - 1], _layers: layers };
});
const ctx = {
  PropertyType: { PROPERTY: 1 }, CompItem: function () {}, FootageItem: function () {}, SolidSource: function () {},
  AEK: {
    core: {
      comps: () => comps,
      layer: (c, n) => c._layers.find((l) => l.name === n),
      walk: (l, fn) => l.props.forEach(fn),
    },
    expr: { check: () => ({ errors: [] }) },
  },
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(file, "utf8"), ctx);
const out = {};
try {
  if (mode === "rename") { out.result = ctx.AEX.expressions.renameLayer(comps[0], S.from, S.to); }
  else { out.result = ctx.AEX.project.rewriteRefs(S.pairs); }
} catch (e) { out.error = String(e); }
out.exprs = comps.map((c) => c._layers.map((l) => l.props.map((p) => ({ text: p._ex, on: p.expressionEnabled }))));
out.parses = [].concat(...out.exprs.map((c) => [].concat(...c))).map((e) => {
  try { new vm.Script(e.text); return true; } catch (err) { return false; }
});
process.stdout.write(JSON.stringify(out));
"""

# (expression before, expression after) for renameLayer(comp, "CTRL", "Controls")
RENAME_CASES = [
    ('var label = "layer(\'CTRL\')"; thisComp.layer("CTRL").transform.opacity',
     'var label = "layer(\'CTRL\')"; thisComp.layer("Controls").transform.opacity'),
    ("var label = 'layer(\"CTRL\")'; thisComp.layer('CTRL').transform.opacity",
     "var label = 'layer(\"CTRL\")'; thisComp.layer('Controls').transform.opacity"),
    ('// was layer("CTRL")\nthisComp.layer( \'CTRL\' ).effect("Size")(1)',
     '// was layer("CTRL")\nthisComp.layer( \'Controls\' ).effect("Size")(1)'),
    ('/* layer("CTRL") and\n layer(\'CTRL\') */ thisComp.layer ("CTRL").index',
     '/* layer("CTRL") and\n layer(\'CTRL\') */ thisComp.layer ("Controls").index'),
    ('var s = "say \\"layer(\'CTRL\')\\" twice"; thisComp.layer("CTRL").index',
     'var s = "say \\"layer(\'CTRL\')\\" twice"; thisComp.layer("Controls").index'),
    ('`${thisComp.layer("CTRL").name} is layer("CTRL")`',
     '`${thisComp.layer("Controls").name} is layer("CTRL")`'),
    ('var r = /layer\\("CTRL"\\)/; thisComp.layer("CTRL").index / 2',
     'var r = /layer\\("CTRL"\\)/; thisComp.layer("Controls").index / 2'),
    ('thisComp.layer("CTRL2").index + mylayer("CTRL") + thisComp.layer("CTRL").index',
     'thisComp.layer("CTRL2").index + mylayer("CTRL") + thisComp.layer("Controls").index'),
]


def node(file, mode, spec):
    r = subprocess.run(["node", "-e", HARNESS, str(file), mode, json.dumps(spec)], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class RenameLayer(unittest.TestCase):
    def test_only_real_calls_are_rewritten(self):
        exprs = [{"text": a, "on": True} for a, _ in RENAME_CASES] + [{"text": 'thisComp.layer("CTRL").index', "on": False}]
        spec = {"from": "CTRL", "to": "Controls",
                "comps": [{"name": "Main", "id": 1, "layers": [{"name": "CTRL", "exprs": []}, {"name": "A", "exprs": exprs}]}]}
        out = node(EXPRESSIONS, "rename", spec)
        self.assertNotIn("error", out)
        got = out["exprs"][0][1]
        for (before, want), g in zip(RENAME_CASES, got):
            self.assertEqual(g["text"], want, before)
        self.assertEqual(got[-1], {"text": 'thisComp.layer("Controls").index', "on": False})
        self.assertTrue(all(out["parses"]), out["exprs"])
        # every case but the disabled one still quotes the old name somewhere: a person checks those
        self.assertEqual(len(out["result"]["review"]), len(RENAME_CASES))

    def test_name_with_a_quote_in_both_quote_styles(self):
        exprs = [{"text": "thisComp.layer('Joe\\'s').index + thisComp.layer(\"Joe's\").index", "on": True}]
        spec = {"from": "Joe's", "to": 'Big "J"',
                "comps": [{"name": "Main", "id": 1, "layers": [{"name": "Joe's", "exprs": []}, {"name": "A", "exprs": exprs}]}]}
        out = node(EXPRESSIONS, "rename", spec)
        self.assertEqual(out["exprs"][0][1][0]["text"], "thisComp.layer('Big \"J\"').index + thisComp.layer(\"Big \\\"J\\\"\").index")
        self.assertTrue(all(out["parses"]))


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class RewriteRefs(unittest.TestCase):
    def spec(self, exprs):
        return {"pairs": [{"kind": "comp", "from": "Pre-comp 1", "to": "PC_Logo"},
                          {"kind": "layer", "from": "Pre-comp 1", "to": "PC_Logo", "scope": 10}],
                "comps": [{"name": "hasOwnProperty", "id": 7, "layers": []},
                          {"name": "__proto__", "id": 8, "layers": []},
                          {"name": "MAIN", "id": 10, "layers": [{"name": "A", "exprs": [{"text": t, "on": True} for t in exprs]}]},
                          {"name": "PC_Logo", "id": 11, "layers": []}]}

    def test_comp_named_hasOwnProperty_and_strings_and_comments(self):
        exprs = [
            'comp("Pre-comp 1").layer(1).index + thisComp.layer("Pre-comp 1").index',
            'var s = "comp(\'Pre-comp 1\')"; // layer("Pre-comp 1")\ncomp(\'MAIN\').layer(\'Pre-comp 1\').index',
            'comp("hasOwnProperty").layer("Pre-comp 1").index',
        ]
        out = node(PROJECT, "refs", self.spec(exprs))
        self.assertNotIn("error", out)
        got = [e["text"] for e in out["exprs"][2][0]]
        self.assertEqual(got[0], 'comp("PC_Logo").layer(1).index + thisComp.layer("PC_Logo").index')
        self.assertEqual(got[1], 'var s = "comp(\'Pre-comp 1\')"; // layer("Pre-comp 1")\ncomp(\'MAIN\').layer(\'PC_Logo\').index')
        # comp "hasOwnProperty" is not the comp that holds the renamed layer: its reference stays
        self.assertEqual(got[2], exprs[2])
        self.assertEqual(out["result"]["rewritten"], 2)
        self.assertTrue(all(out["parses"]))


if __name__ == "__main__":
    unittest.main()
