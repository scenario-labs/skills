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
  for (const dir of [".github", ".claude/commands", ".claude/agents"]) {
    mkdirSync(join(root, dir), { recursive: true });
  }
  for (const file of [
    "README.md",
    "INSTALL.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
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
