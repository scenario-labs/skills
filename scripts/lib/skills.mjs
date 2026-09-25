#!/usr/bin/env node
// Skill discovery shared by every check, so the layout is defined once
// (AGENTS.md, "Layout"): core skills sit at skills/<name>/, expert tools at
// skills/<category>/<family>/<name>/ beside one README.md per family.
// The skills CLI installs every skill flat by name and silently keeps only
// the first of two skills sharing one, so names must be unique repo-wide.
//
// Run directly for the shell checks:
//   node scripts/lib/skills.mjs            every skill folder, one per line
//   node scripts/lib/skills.mjs --core     core skill folders only
//   node scripts/lib/skills.mjs --expert   expert-tool skill folders only
//   node scripts/lib/skills.mjs --dir <n>  the folder of skill <n>, unslashed
//   node scripts/lib/skills.mjs --check    layout problems, exit 1 if any
// Listed folders print with a trailing slash, the form `skills/*/` globs
// produced; --dir prints none, because BSD `cp -R dir/` copies the contents.
import { readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const EXPERT_CATEGORIES = ["dcc", "game-engines"];

const entries = (dir) =>
  readdirSync(dir, { withFileTypes: true })
    .filter((entry) => !entry.name.startsWith("."))
    .sort((a, b) => a.name.localeCompare(b.name));
const subdirs = (dir) =>
  entries(dir)
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

// [{ name, dir, expert, family }] with dir repo-relative and unslashed.
export function listSkills(root = "skills") {
  const skills = [];
  for (const top of subdirs(root)) {
    if (!EXPERT_CATEGORIES.includes(top)) {
      skills.push({ name: top, dir: path.join(root, top), expert: false });
      continue;
    }
    for (const family of subdirs(path.join(root, top))) {
      for (const name of subdirs(path.join(root, top, family))) {
        skills.push({
          name,
          dir: path.join(root, top, family, name),
          expert: true,
          family,
        });
      }
    }
  }
  return skills;
}

export function layoutProblems(root = "skills") {
  const problems = [];
  const seen = new Map();
  for (const skill of listSkills(root)) {
    if (seen.has(skill.name)) {
      problems.push(
        `${skill.dir}: skill name also used by ${seen.get(skill.name)} (the skills CLI keeps only one)`,
      );
    } else {
      seen.set(skill.name, skill.dir);
    }
    try {
      statSync(path.join(skill.dir, "SKILL.md"));
    } catch {
      problems.push(`${skill.dir}: no SKILL.md`);
    }
  }
  for (const category of EXPERT_CATEGORIES) {
    const categoryDir = path.join(root, category);
    for (const entry of entries(categoryDir)) {
      if (!entry.isDirectory()) {
        problems.push(
          `${path.join(categoryDir, entry.name)}: only family folders belong in ${categoryDir}/`,
        );
      }
    }
    for (const family of subdirs(categoryDir)) {
      const familyDir = path.join(categoryDir, family);
      const files = entries(familyDir).filter((entry) => !entry.isDirectory());
      if (!files.some((entry) => entry.name === "README.md")) {
        problems.push(`${familyDir}: missing the family README.md`);
      }
      for (const entry of files) {
        if (entry.name !== "README.md") {
          problems.push(
            `${path.join(familyDir, entry.name)}: a family folder holds skill folders and one README.md only`,
          );
        }
      }
    }
  }
  return problems;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  process.chdir(
    path.join(path.dirname(fileURLToPath(import.meta.url)), "../.."),
  );
  const args = process.argv.slice(2);
  if (args[0] === "--check") {
    const problems = layoutProblems();
    for (const problem of problems) console.error(problem);
    process.exit(problems.length > 0 ? 1 : 0);
  }
  if (args[0] === "--dir") {
    const skill = listSkills().find((entry) => entry.name === args[1]);
    if (!skill) {
      console.error(`no skill named "${args[1]}" under skills/`);
      process.exit(1);
    }
    console.log(skill.dir);
    process.exit(0);
  }
  for (const skill of listSkills()) {
    if (args[0] === "--core" && skill.expert) continue;
    if (args[0] === "--expert" && !skill.expert) continue;
    console.log(`${skill.dir}/`);
  }
}
