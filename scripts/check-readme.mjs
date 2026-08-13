#!/usr/bin/env node
// Keeps the hand-maintained Skills table in README.md in sync with the
// skills/ directory:
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

const rows = lines
  .slice(start + 1, end)
  .map((line) => line.trim())
  .filter((line) => line.startsWith("|"))
  // a GFM table's first two pipe rows are the header and the |---|
  // separator; skip them by position so a header copy-edit cannot
  // make this check fail
  .slice(2);

const rowFor = new Map();
for (const row of rows) {
  const match = row.match(/^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|(.*)\|$/);
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
  `README.md Skills table covers all ${skillDirs.length} skills with no stale or duplicate rows`,
);
