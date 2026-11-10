#!/usr/bin/env node
// The update notice every SKILL.md ends with (AGENTS.md, "Layout"): the release
// the copy comes from, and the rule that has an agent tell the user when the
// Scenario MCP server names a newer one. An installed copy never refreshes
// itself, and a session that loads one skill does not load the root skill, so
// each skill carries its own (docs/decisions.md, "Update notice").
//
//   node scripts/update-notice.mjs            write the notice into every skill
//   node scripts/update-notice.mjs --force    the same, replacing whatever sits
//                                             below the heading (a new wording)
//   node scripts/update-notice.mjs --check    problems, exit 1 if any
//   node scripts/update-notice.mjs --heading  the heading, for check-style.sh
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { listSkills } from "./lib/skills.mjs";

export const NOTICE_HEADING = "## Update notice";
export const NOTICE_GLOB = "skills/**/SKILL.md";

// release-please's generic updater rewrites the version on a line that holds
// this marker, and nothing else in the file.
const MARKER = "<!-- x-release-please-version -->";
const RELEASE_LINE =
  /^This copy is skills release (\S+)\. <!-- x-release-please-version -->$/m;
const VERSION = /^(\d+)\.(\d+)\.(\d+)$/;

export const renderNotice = (version) => `${NOTICE_HEADING}

This copy is skills release ${version}. ${MARKER}

- Once per session, before your first step, compare it with the latest skills release named in the
  Scenario MCP server instructions.
- When the latest is newer, tell the user once, in one line, that their installed Scenario skills
  are behind. Give both releases and https://github.com/scenario-labs/skills#staying-up-to-date,
  then continue the task without waiting for an answer. Do not repeat it later in the session.
- Otherwise, or when the server names no release, say nothing.
- Skip the notice once the user has said to stop.
- Never run an installer or an update unasked.
`;

// The notice runs from its heading to the end of the file.
function splitNotice(text) {
  const lines = text.split("\n");
  const at = lines.indexOf(NOTICE_HEADING);
  if (at === -1) return { body: text, tail: null };
  return {
    body: lines.slice(0, at).join("\n"),
    tail: lines.slice(at).join("\n"),
  };
}

// The release a tail states, or null when the tail is anything but the notice
// in its current wording.
const releaseOf = (tail) => {
  const version = tail.match(RELEASE_LINE)?.[1];
  return version && VERSION.test(version) && tail === renderNotice(version)
    ? version
    : null;
};

// Replaces everything from the heading down, whatever it holds.
export const applyNotice = (text, version) =>
  `${splitNotice(text).body.trimEnd()}\n\n${renderNotice(version)}`;

const compare = (a, b) => {
  const [x, y] = [a, b].map((version) =>
    version.match(VERSION).slice(1).map(Number),
  );
  return x[0] - y[0] || x[1] - y[1] || x[2] - y[2];
};

// An older release passes: a skill added from a branch cut before the last
// release keeps its number until the next release rewrites it, and failing
// there would break main, which does not require up-to-date branches.
export function noticeProblem(text, current) {
  const { tail } = splitNotice(text);
  if (tail === null) return "has no update notice";
  const version = releaseOf(tail);
  if (!version || text !== applyNotice(text, version)) {
    return "must end with the update notice, unedited";
  }
  if (compare(version, current) > 0) {
    return `states release ${version}, newer than version.txt ${current}`;
  }
  return null;
}

const stampedByReleases = (config) =>
  Object.values(config.packages ?? {}).some((pkg) =>
    (pkg["extra-files"] ?? []).some(
      (entry) =>
        entry.type === "generic" &&
        entry.path === NOTICE_GLOB &&
        entry.glob === true,
    ),
  );

// Resolved, because a temporary directory is often reached through a symlink.
if (
  process.argv[1] &&
  realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));
  const mode = process.argv[2];
  if (mode === "--heading") {
    console.log(NOTICE_HEADING);
    process.exit(0);
  }
  const current = readFileSync("version.txt", "utf8").trim();
  if (!VERSION.test(current)) {
    console.error(`version.txt: "${current}" is not a release number (X.Y.Z)`);
    process.exit(1);
  }
  const files = listSkills().map((skill) => path.join(skill.dir, "SKILL.md"));
  if (mode === "--check") {
    const problems = [];
    for (const file of files) {
      const problem = noticeProblem(readFileSync(file, "utf8"), current);
      if (problem) problems.push(`${file}: ${problem}`);
    }
    if (problems.length > 0)
      problems.push("Run `pnpm notice` to rewrite the notices.");
    if (
      !stampedByReleases(
        JSON.parse(readFileSync("release-please-config.json", "utf8")),
      )
    ) {
      problems.push(
        `release-please-config.json: no generic extra-files entry for ${NOTICE_GLOB} with glob: true, so a release would leave the notices on the old number`,
      );
    }
    for (const problem of problems) console.error(problem);
    process.exit(problems.length > 0 ? 1 : 0);
  }
  // A plain write only replaces a notice it recognizes, so it never drops
  // lines an author wrote below the heading.
  const refused = [];
  for (const file of files) {
    const text = readFileSync(file, "utf8");
    const { tail } = splitNotice(text);
    if (tail !== null && !releaseOf(tail) && mode !== "--force") {
      refused.push(file);
      continue;
    }
    const next = applyNotice(text, current);
    if (next !== text) writeFileSync(file, next);
  }
  if (refused.length > 0) {
    for (const file of refused) {
      console.error(
        `${file}: the text from "${NOTICE_HEADING}" to the end is not the current notice, so it was left alone`,
      );
    }
    console.error(
      "Move what you wrote above the heading. After a wording change, run `pnpm notice --force`, which replaces everything from the heading down.",
    );
    process.exit(1);
  }
}
