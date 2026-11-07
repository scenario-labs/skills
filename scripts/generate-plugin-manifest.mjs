#!/usr/bin/env node
// Generates .claude-plugin/marketplace.json from skills.sh.json, keeping the
// repo-page groupings the single source of truth for skill grouping:
// - the skills CLI (npx skills add) groups its installer picker by the plugin
//   entries in .claude-plugin/marketplace.json and never reads skills.sh.json,
//   which only drives the repo page on skills.sh
// - each grouping becomes one plugin entry (title lowercased and hyphenated as
//   the plugin name, same description, one path per skill, nested for the
//   expert tools under skills/<category>/<family>/),
//   which also makes the repo installable as a Claude Code plugin marketplace,
//   one plugin per grouping
// - plugin names come from scripts/plugin-names.json, keyed by grouping
//   title, never from position: a name is its Claude Code install key, so a
//   renumbered name breaks every install of it. Each name starts with a fixed
//   three-digit number assigned once, with gaps (010-getting-started), because
//   the picker sorts groups by name and shows them title-cased ("010 Getting
//   Started"). A new grouping takes a free number between its neighbors.
//   --check fails on a missing, unused, out-of-order or retired name.
// - entries carry no version: Claude Code then versions a plugin by commit, so
//   its catalog entry and its files always come from the same commit. Releases
//   reach plugin users through the stable branch the release workflow moves.
// Never edit the manifest by hand; edit skills.sh.json and run `pnpm manifest`.
// By default regenerates the file in place and, for the pre-commit hook, its
// staged copy from the staged skills.sh.json and skill folders. --check
// verifies without rewriting, for `pnpm validate` and CI. Grouping contents are
// validated by check-groupings.mjs.
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { listSkills, listSkillsFromPaths } from "./lib/skills.mjs";

process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));

const MANIFEST_PATH = ".claude-plugin/marketplace.json";

const bail = (message) => {
  console.error(message);
  process.exit(1);
};

const NAMES_PATH = "scripts/plugin-names.json";
const NAME_PATTERN = /^\d{3}-[a-z0-9]+(-[a-z0-9]+)*$/;

// `source` names the skills.sh.json being read in error messages.
function render(source, read, skills, names) {
  let config;
  try {
    config = JSON.parse(read());
  } catch (error) {
    bail(`${source}: not valid JSON (${error.message})`);
  }
  if (!Array.isArray(config.groupings) || config.groupings.length === 0) {
    bail(`${source}: groupings must be a non-empty array (see pnpm groupings)`);
  }

  const skillDirOf = new Map(skills.map((skill) => [skill.name, skill.dir]));
  const seen = new Map();
  const plugins = config.groupings.map((group, index) => {
    if (group === null || typeof group !== "object" || Array.isArray(group)) {
      bail(
        `${source}: grouping ${index} must be an object (see pnpm groupings)`,
      );
    }
    const title = String(group.title ?? "");
    const name = names[title];
    if (typeof name !== "string") {
      bail(
        `${NAMES_PATH}: grouping "${title}" has no plugin name; add one whose number sits between its neighbors' (a new grouping between 030 and 040 takes 035)`,
      );
    }
    if (seen.has(name)) {
      bail(
        `${NAMES_PATH}: groupings "${seen.get(name)}" and "${title}" share plugin name "${name}"`,
      );
    }
    seen.set(name, title);
    if (!Array.isArray(group.skills)) {
      bail(
        `${source}: grouping "${title}" needs a skills array (see pnpm groupings)`,
      );
    }
    const plugin = { name };
    if (group.description) plugin.description = group.description;
    plugin.source = "./";
    plugin.strict = false;
    plugin.skills = group.skills.map((skill) => {
      if (!skillDirOf.has(skill)) {
        bail(
          `${source}: "${skill}" in grouping "${title}" has no skill directory (see pnpm groupings)`,
        );
      }
      return `./${skillDirOf.get(skill)}`;
    });
    return plugin;
  });

  const manifest = {
    name: "scenario-skills",
    owner: { name: "Scenario", url: "https://scenario.com" },
    metadata: {
      description:
        "Agent Skills for creating production-ready images, video, audio, 3D, and custom models with Scenario, plus expert tools for DCC software and game engines",
    },
    plugins,
  };
  return {
    rendered: `${JSON.stringify(manifest, null, 2)}\n`,
    groups: plugins.length,
    names: plugins.map((plugin) => plugin.name),
  };
}

const registry = JSON.parse(readFileSync(NAMES_PATH, "utf8"));
const { rendered, groups, names } = render(
  "skills.sh.json",
  () => readFileSync("skills.sh.json", "utf8"),
  listSkills(),
  registry.plugins ?? {},
);

const existing = existsSync(MANIFEST_PATH)
  ? readFileSync(MANIFEST_PATH, "utf8")
  : null;

if (process.argv.includes("--check")) {
  const listed = Object.values(registry.plugins ?? {});
  const retired = registry.retired ?? [];
  const problems = [
    ...listed
      .filter((name) => !NAME_PATTERN.test(name))
      .map(
        (name) => `"${name}" is not a three-digit number, a hyphen, and a slug`,
      ),
    ...listed
      .filter((name) => !names.includes(name))
      .map(
        (name) =>
          `"${name}" names no grouping: existing installs of it break; move it to "retired" only if that is intended`,
      ),
    ...names
      .filter((name) => retired.includes(name))
      .map((name) => `"${name}" is retired: pick another name`),
    ...names
      .slice(1)
      .filter((name, i) => name.localeCompare(names[i]) <= 0)
      .map(
        (name) =>
          `"${name}" sorts before the grouping above it, so the picker would leave skills.sh.json order`,
      ),
  ];
  if (problems.length > 0) {
    bail(
      [
        `${NAMES_PATH}: plugin names are install keys, so every change is deliberate.`,
        ...problems.map((problem) => `  ${problem}`),
      ].join("\n"),
    );
  }
  if (existing !== rendered) {
    bail(
      `${MANIFEST_PATH} is out of sync with skills.sh.json; run pnpm manifest`,
    );
  }
  console.log(
    `${MANIFEST_PATH} is in sync with skills.sh.json (${groups} plugin groups)`,
  );
  process.exit(0);
}

if (existing !== rendered) {
  mkdirSync(path.dirname(MANIFEST_PATH), { recursive: true });
  writeFileSync(MANIFEST_PATH, rendered);
}

// The commit ships the index, not the working tree the check reads, so the
// staged copy is rendered from the staged skills.sh.json and skill folders: a
// staged skill move or grouping edit reaches the commit, an unstaged one never
// does.
const git = (args, input) =>
  execFileSync("git", args, {
    input,
    encoding: "utf8",
    stdio: ["pipe", "pipe", "ignore"],
  });
let index;
try {
  index = {
    config: git(["show", ":skills.sh.json"]),
    names: JSON.parse(git(["show", `:${NAMES_PATH}`])).plugins ?? {},
    paths: git(["ls-files", "-z", "--", "skills"]).split("\0"),
  };
} catch {
  // Not in a git repository, or skills.sh.json is not tracked yet.
}
if (index) {
  const staged = render(
    "staged skills.sh.json",
    () => index.config,
    listSkillsFromPaths(index.paths),
    index.names,
  ).rendered;
  let indexed = null;
  try {
    indexed = git(["show", `:${MANIFEST_PATH}`]);
  } catch {
    // The manifest is not tracked yet.
  }
  if (staged !== indexed) {
    const blob = git(["hash-object", "-w", "--stdin"], staged).trim();
    git([
      "update-index",
      "--add",
      "--cacheinfo",
      `100644,${blob},${MANIFEST_PATH}`,
    ]);
  }
}

console.log(
  existing !== rendered
    ? `${MANIFEST_PATH} regenerated from skills.sh.json (${groups} plugin groups)`
    : `${MANIFEST_PATH} already in sync with skills.sh.json (${groups} plugin groups)`,
);
