import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const scripts = dirname(fileURLToPath(import.meta.url));
const REFERENCE = "skills/scenario-demo/references/notes.md";
const NOTICE = "Notice (not a failure): a table cell";

// Under a git hook, GIT_DIR and friends would point every call at this repo.
const env = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_")),
);

function repo(t) {
  const root = mkdtempSync(join(tmpdir(), "skills-style-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const file of ["check-style.sh", "lib/skills.mjs"]) {
    mkdirSync(dirname(join(root, "scripts", file)), { recursive: true });
    copyFileSync(join(scripts, file), join(root, "scripts", file));
  }
  // The em-dash rule greps these paths and fails when one is missing.
  for (const dir of [
    "docs",
    "tests",
    ".github",
    ".claude/commands",
    ".claude/agents",
  ]) {
    mkdirSync(join(root, dir), { recursive: true });
  }
  for (const file of [
    "README.md",
    "INSTALL.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
  ]) {
    writeFileSync(join(root, file), "");
  }
  const write = (file, text) => {
    mkdirSync(dirname(join(root, file)), { recursive: true });
    writeFileSync(join(root, file), text);
  };
  write(
    "skills/scenario-demo/SKILL.md",
    "---\nname: scenario-demo\ndescription: Use when testing.\nlicense: MIT\n---\n\nBody.\n",
  );
  const git = (...args) =>
    execFileSync(
      "git",
      ["-c", "user.name=test", "-c", "user.email=test@example.com", ...args],
      {
        cwd: root,
        env,
        stdio: "pipe",
      },
    );
  git("init", "-q");
  git("add", "-A");
  git("commit", "-q", "-m", "base");
  // Throws on a non-zero exit, so every passing test also proves the notice
  // never fails the check.
  const style = () =>
    execFileSync(join(root, "scripts/check-style.sh"), {
      cwd: root,
      env,
      encoding: "utf8",
      stdio: "pipe",
    });
  return { write, git, style };
}

const table = (...rows) =>
  ["| A | B |", "| --- | --- |", ...rows, ""].join("\n");
const cell = (length) => "x".repeat(length);

test("names a staged cell past 200 characters with its line", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `# Notes\n\n${table(`| ${cell(250)} | short |`)}`);
  git("add", REFERENCE);
  const out = style();
  assert.ok(out.includes(NOTICE), out);
  assert.ok(out.includes(`${REFERENCE}:5: a 250-character cell`), out);
});

test("stays quiet for a cell of exactly 200 characters", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, table(`| ${cell(200)} | short |`));
  git("add", REFERENCE);
  assert.ok(!style().includes(NOTICE));
});

test("stays quiet when the file is committed, not staged", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, table(`| ${cell(250)} | short |`));
  git("add", REFERENCE);
  git("commit", "-q", "-m", "table");
  assert.ok(!style().includes(NOTICE));
});

test("measures cells, not a row padded wide by many short cells", (t) => {
  const { write, git, style } = repo(t);
  const wide = `| ${Array(12).fill(cell(30)).join(" | ")} |`;
  write(REFERENCE, ["| h |", "| --- |", wide, ""].join("\n"));
  git("add", REFERENCE);
  assert.ok(wide.length > 200);
  assert.ok(!style().includes(NOTICE));
});

test("keeps an escaped pipe inside its cell", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, table(`| ${cell(120)} \\| ${cell(120)} | short |`));
  git("add", REFERENCE);
  assert.match(style(), /a 2\d\d-character cell/);
});

test("skips table rows inside fenced code", (t) => {
  const { write, git, style } = repo(t);
  write(
    REFERENCE,
    ["```text", `| ${cell(250)} | short |`, "```", ""].join("\n"),
  );
  git("add", REFERENCE);
  assert.ok(!style().includes(NOTICE));
});

test("only reads skill markdown", (t) => {
  const { write, git, style } = repo(t);
  write("docs/notes.md", table(`| ${cell(250)} | short |`));
  git("add", "docs/notes.md");
  assert.ok(!style().includes(NOTICE));
});

const SENTENCE =
  "Notice (not a failure): staged skill markdown adds a sentence";
const TERM = 'Notice (not a failure): staged skill markdown adds "workflow"';
const words = (count) =>
  Array.from({ length: count }, (_, i) => `w${i}`).join(" ");
// Prettier wraps prose, so a sentence usually spans lines.
const wrapped = (count) => {
  const all = words(count).split(" ");
  return `${all.slice(0, 20).join(" ")}\n${all.slice(20).join(" ")}.`;
};

test("names an added sentence past 40 words by its first line", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `# Notes\n\n${wrapped(41)}\n`);
  git("add", REFERENCE);
  const out = style();
  assert.ok(out.includes(SENTENCE), out);
  assert.ok(out.includes(`${REFERENCE}:3: a 41-word sentence`), out);
});

test("stays quiet for a sentence of exactly 40 words", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `${wrapped(40)}\n`);
  git("add", REFERENCE);
  assert.ok(!style().includes(SENTENCE));
});

test("ignores a long sentence on lines the change does not add", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `${wrapped(60)}\n`);
  git("add", REFERENCE);
  git("commit", "-q", "-m", "notes");
  write(REFERENCE, `${wrapped(60)}\n\nA short new line.\n`);
  git("add", REFERENCE);
  assert.ok(!style().includes(SENTENCE));
});

test("names a long sentence when one of its lines is added", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `${wrapped(60)}\n`);
  git("add", REFERENCE);
  git("commit", "-q", "-m", "notes");
  write(REFERENCE, `${wrapped(60).replace("w59", "changed")}\n`);
  git("add", REFERENCE);
  assert.ok(style().includes(`${REFERENCE}:1: a 60-word sentence`));
});

test("ends a sentence at each list item", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `- ${words(25)}\n- ${words(25)}\n1. ${words(25)}\n`);
  git("add", REFERENCE);
  assert.ok(!style().includes(SENTENCE));
});

test("reads e.g. as part of a sentence", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `${words(20)} e.g. ${words(20)}.\n`);
  git("add", REFERENCE);
  assert.ok(style().includes(`${REFERENCE}:1: a 41-word sentence`));
});

test("reads etc. before a lowercase word as part of a sentence", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `${words(20)} etc.)\n${words(20)}.\n`);
  git("add", REFERENCE);
  assert.ok(style().includes(`${REFERENCE}:1: a 41-word sentence`));
});

test("ends a sentence at etc. before a capital", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, `${words(30)} etc. Next ${words(30)}.\n`);
  git("add", REFERENCE);
  assert.ok(!style().includes(SENTENCE));
});

test("skips frontmatter, fenced code, and tables for sentences", (t) => {
  const { write, git, style } = repo(t);
  write(
    "skills/scenario-demo/SKILL.md",
    [
      "---",
      "name: scenario-demo",
      `description: Use when ${words(50)}.`,
      "license: MIT",
      "---",
      "",
      "```text",
      words(50),
      "```",
      "",
      `| ${words(50)} |`,
      "",
    ].join("\n"),
  );
  git("add", "-A");
  assert.ok(!style().includes(SENTENCE));
});

test("names an added workflow outside the workflow skills", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, "# Notes\n\nFollow this Workflow.\n\n## WORKFLOW\n");
  git("add", REFERENCE);
  const out = style();
  assert.ok(out.includes(TERM), out);
  assert.ok(out.includes(`  ${REFERENCE}:3\n  ${REFERENCE}:5\n`), out);
});

test("leaves workflow alone in the workflow skills", (t) => {
  const { write, git, style } = repo(t);
  const skill = "skills/scenario-workflows/SKILL.md";
  write(
    skill,
    "---\nname: scenario-workflows\ndescription: Use when testing.\nlicense: MIT\n---\n\nRun a workflow.\n",
  );
  git("add", skill);
  assert.ok(!style().includes(TERM));
});

test("ignores workflow in code, link targets, and skill names", (t) => {
  const { write, git, style } = repo(t);
  write(
    REFERENCE,
    [
      'Call `workflow_run`, or `search` with `target="workflows"`.',
      "Read [the docs](https://example.com/workflows).",
      "See scenario-workflows.",
      "```text",
      "workflow",
      "```",
      "",
    ].join("\n"),
  );
  git("add", REFERENCE);
  assert.ok(!style().includes(TERM));
});

test("ignores workflow on lines the change does not add", (t) => {
  const { write, git, style } = repo(t);
  write(REFERENCE, "Follow this workflow.\n");
  git("add", REFERENCE);
  git("commit", "-q", "-m", "notes");
  write(REFERENCE, "Follow this workflow.\n\nA new line.\n");
  git("add", REFERENCE);
  assert.ok(!style().includes(TERM));
});

const AGENTS_CAP = "Codex reads by default";

test("fails when AGENTS.md passes 32 KiB", (t) => {
  const { write, style } = repo(t);
  write("AGENTS.md", "x".repeat(32769));
  assert.throws(style, (error) => {
    assert.ok(error.stdout.includes(`AGENTS.md is 32769 bytes`), error.stdout);
    assert.ok(error.stdout.includes(AGENTS_CAP), error.stdout);
    return true;
  });
});

test("accepts AGENTS.md of exactly 32 KiB", (t) => {
  const { write, style } = repo(t);
  write("AGENTS.md", "x".repeat(32768));
  assert.ok(!style().includes(AGENTS_CAP));
});

test("fails on an em dash in SUPPORT.md", (t) => {
  const { write, style } = repo(t);
  write("SUPPORT.md", `Ask here ${String.fromCodePoint(0x2014)} or there.\n`);
  assert.throws(style, (error) => {
    assert.ok(error.stdout.includes("SUPPORT.md:1:10:"), error.stdout);
    return true;
  });
});
