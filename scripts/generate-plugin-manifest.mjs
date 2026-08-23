#!/usr/bin/env node
// Generates .claude-plugin/marketplace.json from skills.sh.json, keeping the
// repo-page groupings the single source of truth for skill grouping:
// - the skills CLI (npx skills add) groups its installer picker by the plugin
//   entries in .claude-plugin/marketplace.json and never reads skills.sh.json,
//   which only drives the repo page on skills.sh
// - each grouping becomes one plugin entry (title lowercased and hyphenated as
//   the plugin name, same description, one ./skills/<name> path per skill),
//   which also makes the repo installable as a Claude Code plugin marketplace,
//   one plugin per grouping
// - plugin names carry a two-digit position prefix (01.-getting-started,
//   displayed by the picker as "01. Getting Started") because the picker sorts
//   group names alphabetically, so the prefix is what makes it follow
//   skills.sh.json order; inserting or merging a grouping renumbers the plugin
//   identifiers on the next regeneration
// Never edit the manifest by hand; edit skills.sh.json and run `pnpm manifest`.
// By default regenerates in place for the pre-commit hook, re-staging the file
// only when it is part of the commit. --check verifies without rewriting, for
// `pnpm validate` and CI. Grouping contents are validated by check-groupings.mjs.
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));

const MANIFEST_PATH = ".claude-plugin/marketplace.json";

const bail = (message) => {
  console.error(message);
  process.exit(1);
};

let config;
try {
  config = JSON.parse(readFileSync("skills.sh.json", "utf8"));
} catch (error) {
  bail(`skills.sh.json: not valid JSON (${error.message})`);
}
if (!Array.isArray(config.groupings) || config.groupings.length === 0) {
  bail(
    "skills.sh.json: groupings must be a non-empty array (see pnpm groupings)",
  );
}

const pluginNameOf = (title) =>
  title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

const seen = new Map();
const plugins = config.groupings.map((group, index) => {
  if (group === null || typeof group !== "object" || Array.isArray(group)) {
    bail(
      `skills.sh.json: grouping ${index} must be an object (see pnpm groupings)`,
    );
  }
  const title = String(group.title ?? "");
  const slug = pluginNameOf(title);
  if (slug === "") {
    bail(`skills.sh.json: grouping "${title}" produces an empty plugin name`);
  }
  if (seen.has(slug)) {
    bail(
      `skills.sh.json: groupings "${seen.get(slug)}" and "${title}" both map to plugin name "${slug}"`,
    );
  }
  seen.set(slug, title);
  if (!Array.isArray(group.skills)) {
    bail(
      `skills.sh.json: grouping "${title}" needs a skills array (see pnpm groupings)`,
    );
  }
  const name = `${String(index + 1).padStart(2, "0")}.-${slug}`;
  const plugin = { name };
  if (group.description) plugin.description = group.description;
  plugin.source = "./";
  plugin.strict = false;
  plugin.skills = group.skills.map((skill) => `./skills/${skill}`);
  return plugin;
});

const manifest = {
  name: "scenario-skills",
  owner: { name: "Scenario", url: "https://scenario.com" },
  metadata: {
    description:
      "Agent Skills for creating production-ready images, video, audio, 3D, and custom models with Scenario",
  },
  plugins,
};
const rendered = `${JSON.stringify(manifest, null, 2)}\n`;

const existing = existsSync(MANIFEST_PATH)
  ? readFileSync(MANIFEST_PATH, "utf8")
  : null;

if (process.argv.includes("--check")) {
  if (existing !== rendered) {
    bail(
      `${MANIFEST_PATH} is out of sync with skills.sh.json; run pnpm manifest`,
    );
  }
  console.log(
    `${MANIFEST_PATH} is in sync with skills.sh.json (${plugins.length} plugin groups)`,
  );
  process.exit(0);
}

if (existing !== rendered) {
  mkdirSync(path.dirname(MANIFEST_PATH), { recursive: true });
  writeFileSync(MANIFEST_PATH, rendered);
}
// Re-stage even when the working tree was already in sync: an earlier manual
// `pnpm manifest` run leaves the regenerated file unstaged, and the commit
// ships the index, not the working tree the check reads.
try {
  execSync(`git diff --cached --quiet -- skills.sh.json ${MANIFEST_PATH}`, {
    stdio: "ignore",
  });
} catch {
  try {
    execSync(`git add ${MANIFEST_PATH}`, { stdio: "ignore" });
  } catch {
    // Not in a git repository; the regenerated file is still on disk.
  }
}
console.log(
  existing !== rendered
    ? `${MANIFEST_PATH} regenerated from skills.sh.json (${plugins.length} plugin groups)`
    : `${MANIFEST_PATH} already in sync with skills.sh.json (${plugins.length} plugin groups)`,
);
