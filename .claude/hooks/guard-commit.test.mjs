import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { inspect } from "./guard-commit.mjs";

const hook = join(dirname(fileURLToPath(import.meta.url)), "guard-commit.sh");

// Under a git hook, GIT_DIR and friends would point every call at this repo.
const env = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_")),
);

function project(t, hooksPath) {
  const root = mkdtempSync(join(tmpdir(), "guard-commit-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  execFileSync("git", ["init", "-q"], { cwd: root, env });
  if (hooksPath) {
    execFileSync("git", ["config", "core.hooksPath", hooksPath], {
      cwd: root,
      env,
    });
  }
  return (command, extra = {}) =>
    spawnSync(hook, {
      input: JSON.stringify({ tool_name: "Bash", tool_input: { command } }),
      env: { ...env, CLAUDE_PROJECT_DIR: root, ...extra },
      encoding: "utf8",
    });
}

test("allows a commit when the husky hooks are installed", (t) => {
  const run = project(t, ".husky/_");
  const result = run('git add -A && git commit -m "fix(ci): pin it"');
  assert.equal(result.status, 0, result.stderr);
});

test("refuses a commit when the hooks are not installed", (t) => {
  const run = project(t, null);
  const result = run('git commit -m "fix(ci): pin it"');
  assert.equal(result.status, 2);
  assert.match(result.stderr, /core\.hooksPath is unset or unreadable/);
  assert.match(result.stderr, /Run `pnpm install`/);
});

test("refuses a commit when core.hooksPath points elsewhere", (t) => {
  const run = project(t, ".git/hooks");
  const result = run("git commit -m x");
  assert.equal(result.status, 2);
  assert.match(result.stderr, /core\.hooksPath is "\.git\/hooks"/);
});

test("refuses a commit when the project is not a repository", (t) => {
  const result = spawnSync(hook, {
    input: JSON.stringify({ tool_input: { command: "git commit -m x" } }),
    env: { ...env, CLAUDE_PROJECT_DIR: tmpdir() },
    encoding: "utf8",
  });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /unset or unreadable/);
});

test("refuses --no-verify even with the hooks installed", (t) => {
  const run = project(t, ".husky/_");
  const result = run('git commit --no-verify -m "fix(ci): pin it"');
  assert.equal(result.status, 2);
  assert.match(result.stderr, /--no-verify skips the husky hooks/);
  assert.match(result.stderr, /`pnpm install`/);
});

test("allows commands that are not commits, hooks or not", (t) => {
  const run = project(t, null);
  for (const command of ["git status", "git log --oneline -3", "ls"]) {
    assert.equal(run(command).status, 0, command);
  }
});

test("refuses when the check cannot run", (t) => {
  const run = project(t, ".husky/_");
  // A PATH with the shell tools the hook needs, but no node.
  const bin = mkdtempSync(join(tmpdir(), "guard-commit-bin-"));
  t.after(() => rmSync(bin, { recursive: true, force: true }));
  for (const tool of ["bash", "cat", "dirname"]) {
    const found = execFileSync("/bin/sh", ["-c", `command -v ${tool}`], {
      encoding: "utf8",
    }).trim();
    symlinkSync(found, join(bin, tool));
  }
  const result = run("git commit -m x", { PATH: bin });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /the check could not run/);
});

test("refuses malformed hook input that mentions a commit", (t) => {
  const result = spawnSync(hook, {
    input: "git commit -m x",
    env,
    encoding: "utf8",
  });
  assert.equal(result.status, 2);
});

const bypasses = (command) => inspect(command).bypasses;

test("finds a commit wherever it sits in the command", () => {
  for (const command of [
    "git commit -m x",
    "cd repo && git commit -am x",
    "git -C repo -c user.name=me commit -m x",
    "/usr/bin/git commit",
    "FOO=1 git commit",
    'echo "$(git commit -m x)"',
    "(git commit -m x)",
  ]) {
    assert.ok(inspect(command).commit, command);
  }
  for (const command of [
    "git log --grep commit",
    "echo git commit",
    "git commit-tree HEAD^{tree}",
  ]) {
    assert.ok(!inspect(command).commit, command);
  }
});

test("finds every way to skip the hooks", () => {
  assert.deepEqual(bypasses("git commit --no-verify -m x"), ["--no-verify"]);
  assert.deepEqual(bypasses("git commit --no-verif -m x"), ["--no-verif"]);
  assert.deepEqual(bypasses("git commit -n -m x"), ["-n"]);
  assert.deepEqual(bypasses("git commit -anm x"), ["-n"]);
  assert.deepEqual(bypasses("HUSKY=0 git commit -m x"), ["HUSKY=0"]);
  assert.deepEqual(bypasses("git -c core.hooksPath=/dev/null commit"), [
    "-c core.hooksPath=/dev/null",
  ]);
  assert.deepEqual(bypasses("git -c core.hookspath= commit"), [
    "-c core.hookspath=",
  ]);
});

test("reads a flag-like word inside a message as text", () => {
  for (const command of [
    'git commit -m "refuse --no-verify"',
    'git commit -m "-n is a flag"',
    "git commit -m-n",
    'git commit --message "-n is a flag"',
    "git commit -m 'it skips -n' && echo --no-verify",
    "git commit -m x # --no-verify",
    "git commit --no-verify --verify -m x",
    "git commit -m x -- --no-verify",
  ]) {
    assert.deepEqual(bypasses(command), [], command);
  }
});

test("skips a heredoc message, even inside a substitution", () => {
  const command = [
    `git commit -m "$(cat <<'EOF'`,
    "chore(ci): refuse --no-verify",
    "",
    'It reads "git commit -n" (and an unbalanced paren) as text.',
    "EOF",
    ')"',
  ].join("\n");
  assert.deepEqual(inspect(command), { commit: true, bypasses: [] });
  assert.deepEqual(inspect(`${command} --no-verify`).bypasses, ["--no-verify"]);
});

test("ignores the target of a redirection", () => {
  assert.deepEqual(bypasses("git commit -m x 2>&1 > -n"), []);
});
