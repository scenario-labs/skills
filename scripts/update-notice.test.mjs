import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import test from "node:test";
import * as prettier from "prettier";
import { fileURLToPath } from "node:url";
import { listSkills } from "./lib/skills.mjs";
import { NOTICE_GLOB, NOTICE_HEADING, renderNotice } from "./update-notice.mjs";

const scripts = dirname(fileURLToPath(import.meta.url));
const CONFIG = {
  packages: {
    ".": {
      "extra-files": [{ type: "generic", path: NOTICE_GLOB, glob: true }],
    },
  },
};
const SKILL =
  "---\nname: x\ndescription: Use when testing.\nlicense: MIT\n---\n\n# X\n\nBody.\n";
const skill = (version, body = SKILL) => `${body}\n${renderNotice(version)}`;

// A minimal repository with one core and one expert skill, on release 1.2.3.
function repo(t, { core, expert, config = CONFIG, version = "1.2.3" }) {
  const root = mkdtempSync(join(tmpdir(), "skills-notice-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const file of ["update-notice.mjs", "lib/skills.mjs"]) {
    mkdirSync(dirname(join(root, "scripts", file)), { recursive: true });
    copyFileSync(join(scripts, file), join(root, "scripts", file));
  }
  const files = {
    core: join(root, "skills/scenario-demo/SKILL.md"),
    expert: join(root, "skills/dcc/demo/scenario-demo-expert/SKILL.md"),
  };
  mkdirSync(dirname(files.core), { recursive: true });
  mkdirSync(dirname(files.expert), { recursive: true });
  writeFileSync(files.core, core);
  writeFileSync(files.expert, expert);
  writeFileSync(join(root, "skills/dcc/demo/README.md"), "");
  writeFileSync(join(root, "version.txt"), `${version}\n`);
  writeFileSync(
    join(root, "release-please-config.json"),
    JSON.stringify(config),
  );
  const run = (...args) =>
    spawnSync("node", [join(root, "scripts/update-notice.mjs"), ...args], {
      encoding: "utf8",
    });
  const read = (which) => readFileSync(files[which], "utf8");
  return { run, read };
}

test("writing ends every skill with the notice and is idempotent", (t) => {
  const { run, read } = repo(t, { core: SKILL, expert: SKILL });
  assert.equal(run().status, 0);
  assert.equal(read("core"), skill("1.2.3"));
  assert.equal(read("expert"), skill("1.2.3"));
  assert.equal(run("--check").status, 0);
  run();
  assert.equal(read("core"), skill("1.2.3"));
});

test("writing moves an older release to the current one", (t) => {
  const { run, read } = repo(t, { core: skill("1.0.0"), expert: SKILL });
  assert.equal(run().status, 0);
  assert.equal(read("core"), skill("1.2.3"));
});

test("writing refuses to drop text it does not recognize below the heading", (t) => {
  const cases = {
    "an earlier wording": `${SKILL}\n${NOTICE_HEADING}\n\nAn earlier wording, release 1.0.0.\n`,
    "a line added below": `${skill("1.2.3")}- A mistake to avoid.\n`,
    "a section added below": `${skill("1.2.3")}\n## Common mistakes\n\nKept.\n`,
  };
  for (const [name, content] of Object.entries(cases)) {
    const { run, read } = repo(t, { core: content, expert: SKILL });
    const result = run();
    assert.equal(result.status, 1, name);
    assert.match(result.stderr, /scenario-demo\/SKILL\.md/, name);
    assert.match(result.stderr, /pnpm notice --force/, name);
    assert.equal(read("core"), content, name);
    assert.equal(read("expert"), skill("1.2.3"), name);
  }
});

test("a forced write replaces everything from the heading down", (t) => {
  const old = `${SKILL}\n${NOTICE_HEADING}\n\nAn earlier wording, release 1.0.0.\n`;
  const { run, read } = repo(t, { core: old, expert: skill("1.0.0") });
  assert.equal(run("--force").status, 0);
  assert.equal(read("core"), skill("1.2.3"));
  assert.equal(read("expert"), skill("1.2.3"));
});

test("a version.txt that is not a release number stops both modes", (t) => {
  for (const mode of [[], ["--check"]]) {
    const { run, read } = repo(t, {
      core: SKILL,
      expert: SKILL,
      version: "v1.2.3",
    });
    const result = run(...mode);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /version\.txt: "v1\.2\.3"/);
    assert.equal(read("core"), SKILL);
  }
});

test("prettier leaves the notice as written", async () => {
  const filepath = join(scripts, "../skills/scenario/SKILL.md");
  const config = await prettier.resolveConfig(filepath);
  const notice = renderNotice("1.2.3");
  assert.equal(await prettier.format(notice, { ...config, filepath }), notice);
});

test("the check accepts a release older than version.txt", (t) => {
  const { run } = repo(t, { core: skill("1.1.9"), expert: skill("1.2.3") });
  assert.equal(run("--check").status, 0);
});

test("the check fails on a missing, newer, edited, buried, appended or doubled notice", (t) => {
  const cases = {
    missing: SKILL,
    newer: skill("1.10.0"),
    edited: skill("1.2.3").replace("Never run", "Always run"),
    unmarked: skill("1.2.3").replace(" <!-- x-release-please-version -->", ""),
    malformed: skill("1.2"),
    buried: `${skill("1.2.3")}\n## Common mistakes\n\nBelow.\n`,
    appended: `${skill("1.2.3")}- A mistake to avoid.\n`,
    doubled: `${skill("1.2.3")}\n${renderNotice("1.2.3")}`,
  };
  for (const [name, content] of Object.entries(cases)) {
    const { run } = repo(t, { core: skill("1.2.3"), expert: content });
    const result = run("--check");
    assert.equal(result.status, 1, name);
    assert.match(result.stderr, /scenario-demo-expert\/SKILL\.md/, name);
    assert.match(result.stderr, /pnpm notice/, name);
  }
});

test("the check names the newer release it found", (t) => {
  const { run } = repo(t, { core: skill("2.0.0"), expert: skill("1.2.3") });
  assert.match(
    run("--check").stderr,
    /states release 2\.0\.0, newer than version\.txt 1\.2\.3/,
  );
});

test("the check fails when releases would stop rewriting the notices", (t) => {
  const { run } = repo(t, {
    core: skill("1.2.3"),
    expert: skill("1.2.3"),
    config: { packages: { ".": {} } },
  });
  const result = run("--check");
  assert.equal(result.status, 1);
  assert.match(result.stderr, /release-please-config\.json/);
});

// release-please's own pinned updater and glob matcher, so a change to the
// release line or the layout fails here rather than in a release PR.
const requireFromReleasePlease = createRequire(
  createRequire(import.meta.url).resolve("release-please"),
);
const { Generic } = requireFromReleasePlease("./updaters/generic.js");
const { Version } = requireFromReleasePlease("./version.js");
const { Minimatch } = createRequire(
  requireFromReleasePlease.resolve("@google-automations/git-file-utils"),
)("minimatch");

test("release-please rewrites the release line and nothing else", () => {
  const body = `${SKILL}\nVersion 1.2.3 in prose stays.\n`;
  const updater = new Generic({ version: Version.parse("1.3.0") });
  assert.equal(
    updater.updateContent(skill("1.2.3", body)),
    skill("1.3.0", body),
  );
});

test("the release-please glob reaches every skill, expert tools included", () => {
  const glob = new Minimatch(NOTICE_GLOB);
  const root = join(scripts, "..");
  const skills = listSkills(join(root, "skills"));
  for (const category of ["dcc", "game-engines"]) {
    assert.ok(skills.some((entry) => entry.dir.includes(`/${category}/`)));
  }
  for (const { dir } of skills) {
    const file = `${relative(root, dir)}/SKILL.md`;
    assert.ok(glob.match(file), file);
  }
});
