#!/usr/bin/env node
// Keeps the hand-maintained Skills tables in README.md in sync with both the
// skills/ directory and skills.sh.json (the single source of truth for
// grouping, which also generates the plugin marketplace manifest):
// - the "## Skills" section holds one "###" subsection per grouping, in the
//   same order, with the same title and description, and a table whose rows
//   are exactly the grouping's skills in the same order, so a grouping edit
//   in skills.sh.json cannot leave the README telling a different story
// - every skill directory has exactly one row linking skills/<name>/SKILL.md,
//   so a new skill cannot ship without its human-facing index entry
// - every row points at an existing skill directory with a matching label,
//   so renames and removals cannot leave stale rows behind
// - every row carries a non-empty "Use it for" description
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));

const errors = [];
const bail = (message) => {
  for (const error of [...errors, message]) console.error(error);
  process.exit(1);
};

let readme;
try {
  readme = readFileSync("README.md", "utf8");
} catch (error) {
  bail(`README.md: cannot read (${error.message})`);
}

let skillDirs;
try {
  skillDirs = readdirSync("skills", { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
    .map((entry) => entry.name);
} catch (error) {
  bail(`skills/: cannot list skill directories (${error.message})`);
}

// Grouping contents (titles, descriptions, membership) are validated by
// check-groupings.mjs; here the file is only the reference the README must
// mirror.
let groupings;
try {
  groupings = JSON.parse(readFileSync("skills.sh.json", "utf8")).groupings;
} catch (error) {
  bail(`skills.sh.json: cannot read (${error.message})`);
}
if (!Array.isArray(groupings)) {
  bail("skills.sh.json: groupings must be an array (see pnpm groupings)");
}

// Isolate the "## Skills" section so table rows elsewhere in the README
// (if any ever appear) are not mistaken for skill rows.
const lines = readme.split("\n");
const start = lines.findIndex((line) => line.trim() === "## Skills");
if (start === -1) {
  bail('README.md: no "## Skills" section found');
}
let end = lines.length;
for (let i = start + 1; i < lines.length; i++) {
  if (lines[i].startsWith("## ")) {
    end = i;
    break;
  }
}

// Walk the section into "###" subsections, collecting each one's description
// paragraph and table rows. Skip each table's first two pipe rows (header and
// |---| separator) by position so a header copy-edit cannot make this check
// fail.
const rowPattern = /^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|(.*)\|$/;
const sections = [];
const rows = [];
let current = null;
let pipeRun = 0;
for (const raw of lines.slice(start + 1, end)) {
  const line = raw.trim();
  if (line.startsWith("### ")) {
    current = { title: line.slice(4).trim(), prose: [], labels: [] };
    sections.push(current);
    pipeRun = 0;
    continue;
  }
  if (!line.startsWith("|")) {
    pipeRun = 0;
    if (current !== null && line !== "" && current.labels.length === 0) {
      current.prose.push(line);
    }
    continue;
  }
  pipeRun += 1;
  if (pipeRun <= 2) continue;
  rows.push(line);
  if (current === null) {
    errors.push(
      `README.md: Skills table row before the first "###" heading: ${line.slice(0, 80)}`,
    );
    continue;
  }
  const match = line.match(rowPattern);
  if (match) current.labels.push(match[1]);
}

// The subsections mirror skills.sh.json: same groups, same order, same
// description, same rows. skills.sh.json is the source of truth, so on a
// mismatch edit README.md (or edit skills.sh.json first, then the README).
if (sections.length !== groupings.length) {
  errors.push(
    `README.md: the Skills section has ${sections.length} "###" subsections, skills.sh.json has ${groupings.length} groupings`,
  );
}
const pairs = Math.min(sections.length, groupings.length);
for (let i = 0; i < pairs; i++) {
  const section = sections[i];
  const group = groupings[i];
  const label = `Skills subsection ${i + 1} ("${section.title}")`;
  if (section.title !== group.title) {
    errors.push(
      `README.md: ${label} should be "${group.title}" (skills.sh.json grouping ${i + 1})`,
    );
    continue;
  }
  const prose = section.prose.join(" ").trim();
  if (typeof group.description === "string" && prose !== group.description) {
    errors.push(
      `README.md: ${label} description differs from the skills.sh.json grouping description`,
    );
  }
  const expected = Array.isArray(group.skills) ? group.skills : [];
  if (section.labels.join("\n") !== expected.join("\n")) {
    const missing = expected.filter((s) => !section.labels.includes(s));
    const extra = section.labels.filter((s) => !expected.includes(s));
    const detail =
      missing.length === 0 && extra.length === 0
        ? `rows out of order, expected: ${expected.join(", ")}`
        : [
            missing.length > 0 ? `missing: ${missing.join(", ")}` : "",
            extra.length > 0 ? `unexpected: ${extra.join(", ")}` : "",
          ]
            .filter(Boolean)
            .join("; ");
    errors.push(
      `README.md: ${label} rows do not match the skills.sh.json grouping (${detail})`,
    );
  }
}

const rowFor = new Map();
for (const row of rows) {
  const match = row.match(rowPattern);
  if (!match) {
    errors.push(
      `README.md: Skills table row is not "| [name](skills/name/SKILL.md) | description |": ${row.slice(0, 80)}`,
    );
    continue;
  }
  const [, label, link, description] = match;
  if (link !== `skills/${label}/SKILL.md`) {
    errors.push(
      `README.md: row "${label}" links ${link}, expected skills/${label}/SKILL.md`,
    );
  }
  if (rowFor.has(label)) {
    errors.push(`README.md: "${label}" has more than one Skills table row`);
  } else {
    rowFor.set(label, description.trim());
  }
  if (!skillDirs.includes(label)) {
    errors.push(
      `README.md: row "${label}" has no matching skills/${label}/ directory (stale row?)`,
    );
  }
  if (description.trim() === "") {
    errors.push(`README.md: row "${label}" has an empty description cell`);
  }
}

for (const dir of skillDirs) {
  if (!rowFor.has(dir)) {
    errors.push(
      `skills/${dir}: missing from the README.md Skills table (add a "| [${dir}](skills/${dir}/SKILL.md) | ... |" row)`,
    );
  }
}

if (errors.length > 0) {
  for (const error of errors) console.error(error);
  process.exit(1);
}
console.log(
  `README.md Skills section mirrors skills.sh.json (${groupings.length} groups) and covers all ${skillDirs.length} skills with no stale or duplicate rows`,
);
