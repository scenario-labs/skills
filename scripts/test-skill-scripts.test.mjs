import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import {
  chmodSync,
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const scripts = dirname(fileURLToPath(import.meta.url));
const NAME = "scenario-demo";
const SUITE = `tests/${NAME}/`;
const REQUIREMENTS = `${SUITE}requirements.txt`;
// Every tool the runner calls: a PATH holding only these hides the real uv.
const TOOLS = ["basename", "dirname", "find", "git", "grep", "node", "python3"];

// Under a git hook, GIT_DIR and friends would point every call at this repo.
const env = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_")),
);
const which = (tool) =>
  execFileSync("sh", ["-c", `command -v ${tool}`], {
    env,
    encoding: "utf8",
  }).trim();

const executable = (file, body) => {
  writeFileSync(file, `#!/bin/sh\n${body}\n`);
  chmodSync(file, 0o755);
};

// A repository with one skill and one passing Python suite, run on a PATH of
// the runner's tools. A numeric `uv` adds a uv stub that records its
// arguments and exits with that code.
function run(t, { requirements, uv }) {
  const root = mkdtempSync(join(tmpdir(), "skills-script-tests-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const file of ["test-skill-scripts.sh", "lib/skills.mjs"]) {
    mkdirSync(dirname(join(root, "scripts", file)), { recursive: true });
    copyFileSync(join(scripts, file), join(root, "scripts", file));
  }
  mkdirSync(join(root, "skills", NAME), { recursive: true });
  writeFileSync(join(root, "skills", NAME, "SKILL.md"), "");
  mkdirSync(join(root, SUITE), { recursive: true });
  writeFileSync(
    join(root, SUITE, "test_demo.py"),
    "import unittest\n\n\nclass Demo(unittest.TestCase):\n    def test_demo(self):\n        pass\n",
  );
  if (requirements) writeFileSync(join(root, REQUIREMENTS), requirements);
  execFileSync("git", ["init", "-q"], { cwd: root, env });
  const bin = join(root, "bin");
  mkdirSync(bin);
  for (const tool of TOOLS) {
    executable(join(bin, tool), `exec "${which(tool)}" "$@"`);
  }
  const log = join(root, "uv.log");
  if (uv !== undefined) {
    executable(join(bin, "uv"), `printf '%s\\n' "$@" > "${log}"\nexit ${uv}`);
  }
  const result = spawnSync(which("bash"), ["scripts/test-skill-scripts.sh"], {
    cwd: root,
    env: { ...env, PATH: bin },
    encoding: "utf8",
  });
  const uvArgs = existsSync(log)
    ? readFileSync(log, "utf8").trimEnd().split("\n")
    : null;
  return { bin, result, uvArgs, output: result.stdout + result.stderr };
}

test("a suite with a requirements.txt runs under uv on the PATH's python3", (t) => {
  const { bin, result, uvArgs, output } = run(t, {
    requirements: "numpy\n",
    uv: 0,
  });
  assert.equal(result.status, 0, output);
  assert.deepEqual(uvArgs, [
    "run",
    "--quiet",
    "--no-project",
    "--python",
    join(bin, "python3"),
    "--with-requirements",
    REQUIREMENTS,
    "python",
    "-B",
    "-m",
    "unittest",
    "discover",
    "-s",
    SUITE,
  ]);
});

test("a failing uv run fails the runner", (t) => {
  const { result } = run(t, { requirements: "numpy\n", uv: 1 });
  assert.equal(result.status, 1);
});

test("a suite without a requirements.txt runs on python3, not uv", (t) => {
  const { result, uvArgs, output } = run(t, { uv: 0 });
  assert.equal(result.status, 0, output);
  assert.equal(uvArgs, null);
  assert.match(result.stderr, /Ran 1 test/);
});

test("without uv, a suite with a requirements.txt runs on python3", (t) => {
  const { result, output } = run(t, { requirements: "numpy\n" });
  assert.equal(result.status, 0, output);
  assert.match(result.stderr, /Ran 1 test/);
});
