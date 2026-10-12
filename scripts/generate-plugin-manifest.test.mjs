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
const MANIFEST = ".claude-plugin/marketplace.json";
const SKILL = "scenario-zbrush-automation";

// Under a git hook, GIT_DIR and friends would point every call at this repo.
const env = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_")),
);

function repo(t) {
  const root = mkdtempSync(join(tmpdir(), "skills-manifest-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const file of ["generate-plugin-manifest.mjs", "lib/skills.mjs"]) {
    mkdirSync(dirname(join(root, "scripts", file)), { recursive: true });
    copyFileSync(join(scripts, file), join(root, "scripts", file));
  }
  mkdirSync(join(root, "skills/dcc/zbrush", SKILL), { recursive: true });
  writeFileSync(join(root, "skills/dcc/zbrush", SKILL, "SKILL.md"), "");
  writeFileSync(
    join(root, "skills.sh.json"),
    JSON.stringify({
      groupings: [{ title: "Expert tools: ZBrush", skills: [SKILL] }],
    }),
  );
  const run = (file, args) =>
    execFileSync(file, args, {
      cwd: root,
      env,
      encoding: "utf8",
      stdio: "pipe",
    });
  const git = (...args) =>
    run("git", [
      "-c",
      "user.name=test",
      "-c",
      "user.email=test@example.com",
      ...args,
    ]);
  const manifest = () =>
    run(process.execPath, [join(root, "scripts/generate-plugin-manifest.mjs")]);
  const staged = () =>
    git("diff", "--cached", "--name-only").trim().split("\n");
  git("-c", "init.defaultBranch=main", "init", "-q");
  manifest();
  git("add", "-A");
  git("commit", "-q", "-m", "init");
  return { root, git, manifest, staged };
}

test("moving a skill folder re-stages the manifest it changes", (t) => {
  const { root, git, manifest, staged } = repo(t);
  mkdirSync(join(root, "skills/dcc/zbrush-tools"));
  git("mv", `skills/dcc/zbrush/${SKILL}`, `skills/dcc/zbrush-tools/${SKILL}`);
  manifest();
  assert.ok(staged().includes(MANIFEST));
  assert.equal(git("diff", "--name-only", "--", MANIFEST), "");
});

test("a commit outside skills leaves an unstaged manifest change alone", (t) => {
  const { root, git, manifest, staged } = repo(t);
  writeFileSync(
    join(root, "skills.sh.json"),
    JSON.stringify({
      groupings: [{ title: "Expert tools: ZBrush 2", skills: [SKILL] }],
    }),
  );
  writeFileSync(join(root, "README.md"), "");
  git("add", "README.md");
  manifest();
  assert.deepEqual(staged(), ["README.md"]);
});
