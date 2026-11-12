import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import {
  copyFileSync,
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
import * as prettier from "prettier";
import { BLOCK, HEADING, blockProblem, withBlock } from "./freshness-block.mjs";

const scripts = dirname(fileURLToPath(import.meta.url));
const FRONTMATTER =
  "---\nname: scenario-demo\ndescription: Use when testing.\nlicense: MIT\n---\n";
const skill = (...sections) =>
  `${FRONTMATTER}\n# Demo\n\n${sections.join("\n")}`;
const OVERVIEW = "## Overview\n\nWhat it does.\n";
const STEPS = "## Steps\n\n1. Run it.\n";

test("puts the block last, moving one found elsewhere", () => {
  assert.equal(
    withBlock(skill(OVERVIEW, STEPS)),
    skill(OVERVIEW, STEPS, BLOCK),
  );
  const misplaced = skill(OVERVIEW, BLOCK, STEPS);
  assert.equal(
    blockProblem(misplaced),
    "freshness block is not the last section",
  );
  assert.equal(withBlock(misplaced), skill(OVERVIEW, STEPS, BLOCK));
});

// A merge where both sides appended the block leaves two.
test("keeps one block when a skill holds two", () => {
  const twice = skill(OVERVIEW, STEPS, BLOCK, BLOCK);
  assert.equal(blockProblem(twice), "has more than one freshness block");
  assert.equal(withBlock(twice), skill(OVERVIEW, STEPS, BLOCK));
});

test("does not take the heading inside fenced code for the block", () => {
  const template = `## Overview\n\n\`\`\`markdown\n${HEADING}\n\`\`\`\n`;
  assert.equal(blockProblem(skill(template, STEPS)), "has no freshness block");
  assert.equal(
    withBlock(skill(template, STEPS)),
    skill(template, STEPS, BLOCK),
  );
});

// `pnpm format` runs prettier after this script: a block prettier rewraps
// would fail `pnpm freshness:check` on every skill.
test("prettier leaves the block as written", async () => {
  const text = skill(OVERVIEW, STEPS, BLOCK);
  const options = await prettier.resolveConfig(
    join(scripts, "../skills/scenario/SKILL.md"),
  );
  assert.equal(
    await prettier.format(text, { ...options, filepath: "SKILL.md" }),
    text,
  );
});

// Under a git hook, GIT_DIR and friends would point every call at this repo.
const env = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_")),
);

function repo(t) {
  const root = mkdtempSync(join(tmpdir(), "skills-freshness-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const file of ["freshness-block.mjs", "lib/skills.mjs"]) {
    mkdirSync(dirname(join(root, "scripts", file)), { recursive: true });
    copyFileSync(join(scripts, file), join(root, "scripts", file));
  }
  const files = {
    core: "skills/scenario-demo/SKILL.md",
    expert: "skills/dcc/blender/scenario-blender-demo/SKILL.md",
  };
  for (const file of Object.values(files)) {
    mkdirSync(dirname(join(root, file)), { recursive: true });
    writeFileSync(join(root, file), skill(OVERVIEW, STEPS));
  }
  const read = (file) => readFileSync(join(root, file), "utf8");
  const write = (file, text) => writeFileSync(join(root, file), text);
  const run = (...args) =>
    execFileSync(
      process.execPath,
      [join(root, "scripts/freshness-block.mjs"), ...args],
      { cwd: root, env, encoding: "utf8", stdio: "pipe" },
    );
  const failure = (...args) => {
    try {
      run(...args);
    } catch (error) {
      return error.stderr;
    }
    assert.fail("expected a non-zero exit");
  };
  return { files, read, write, run, failure };
}

test("writes the block into core and expert skills, and the check passes", (t) => {
  const { files, read, run, failure } = repo(t);
  const missing = failure("--check");
  assert.ok(missing.includes(`${files.core}: has no freshness block`), missing);
  assert.ok(
    missing.includes(`${files.expert}: has no freshness block`),
    missing,
  );
  assert.ok(missing.includes("pnpm freshness"), missing);
  run();
  assert.equal(read(files.core), skill(OVERVIEW, STEPS, BLOCK));
  assert.equal(read(files.expert), skill(OVERVIEW, STEPS, BLOCK));
  run("--check");
});

test("reads a skill with Windows line endings without adding a block", (t) => {
  const { files, read, write, run } = repo(t);
  run();
  write(files.core, read(files.core).replaceAll("\n", "\r\n"));
  run("--check");
  run();
  assert.equal(read(files.core), skill(OVERVIEW, STEPS, BLOCK));
});

test("the check fails on one skill whose block was edited", (t) => {
  const { files, read, write, run, failure } = repo(t);
  run();
  write(files.expert, read(files.expert).replace("ls -l", "stat"));
  const out = failure("--check");
  assert.ok(
    out.includes(
      `${files.expert}: freshness block differs from the fixed text`,
    ),
    out,
  );
  assert.ok(!out.includes(files.core), out);
});

test("a plain write keeps lines an author wrote under the heading", (t) => {
  const { files, read, write, run, failure } = repo(t);
  const authored = skill(OVERVIEW, STEPS, `${HEADING}\n\nMy own rule.\n`);
  write(files.core, authored);
  const out = failure();
  assert.ok(out.includes(`${files.core}: the text under`), out);
  assert.equal(read(files.core), authored);
  assert.equal(read(files.expert), skill(OVERVIEW, STEPS, BLOCK));
  run("--force");
  assert.equal(read(files.core), skill(OVERVIEW, STEPS, BLOCK));
});
