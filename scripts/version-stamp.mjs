#!/usr/bin/env node
// Every SKILL.md frontmatter ends with `metadata.version`, the release it was
// published with, as the Agent Skills spec's own example does. The line
// carries a YAML comment, x-release-please-version, so the globbed generic
// extra-files entry in release-please-config.json rewrites every copy in the
// release PR.
//
// The check accepts any version up to version.txt, not only an equal one:
// main does not require branches to be up to date, so a skill stamped before
// a release can merge after it, and the next release PR rewrites it anyway.
//
//   node scripts/version-stamp.mjs           stamp every SKILL.md with version.txt
//   node scripts/version-stamp.mjs --check   exit 1 if a stamp is missing, misplaced or newer
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { listSkills } from "./lib/skills.mjs";

export const STAMP_GLOB = "skills/**/SKILL.md";
export const stampLines = (version) => [
  "metadata:",
  `  version: "${version}" # x-release-please-version`,
];
const VERSION_PATTERN =
  /^ {2}version: "(\d+)\.(\d+)\.(\d+)" # x-release-please-version$/;

const shorten = (line) => (line.length > 80 ? `${line.slice(0, 77)}...` : line);
const newer = (a, b) => {
  const i = a.findIndex((part, n) => part !== b[n]);
  return i >= 0 && a[i] > b[i];
};

// [frontmatter lines, rest of the file], or null without a frontmatter block.
function split(content) {
  const lines = content.split("\n");
  const end = lines.indexOf("---", 1);
  if (lines[0] !== "---" || end < 0) return null;
  return [lines.slice(1, end), lines.slice(end)];
}

// Drops a `metadata:` block: the key and the indented lines under it.
function withoutMetadata(frontmatter) {
  const kept = [];
  let inMetadata = false;
  for (const line of frontmatter) {
    if (line === "metadata:") {
      inMetadata = true;
      continue;
    }
    if (inMetadata && /^\s/.test(line)) continue;
    inMetadata = false;
    kept.push(line);
  }
  return kept;
}

function problem(content, version) {
  const parts = split(content);
  if (!parts) return "no frontmatter";
  const [frontmatter] = parts;
  const found = `found: "${shorten(frontmatter.slice(-2).join(" / "))}"`;
  if (frontmatter.filter((line) => line === "metadata:").length !== 1) {
    return `needs one metadata block, ${found}`;
  }
  const [key, value] = frontmatter.slice(-2);
  const match = value.match(VERSION_PATTERN);
  if (key !== "metadata:" || !match) {
    return `frontmatter must end with ${stampLines(version).join(" / ")}, ${found}`;
  }
  const stamped = match.slice(1, 4).map(Number);
  if (newer(stamped, version.split(".").map(Number))) {
    return `metadata.version ${stamped.join(".")} is newer than version.txt ${version}`;
  }
  return null;
}

function main() {
  process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));
  const version = readFileSync("version.txt", "utf8").trim();
  const check = process.argv.includes("--check");
  const errors = [];

  for (const { dir } of listSkills()) {
    const file = path.join(dir, "SKILL.md");
    const content = readFileSync(file, "utf8");
    if (check) {
      const error = problem(content, version);
      if (error) errors.push(`${file}: ${error}`);
      continue;
    }
    const parts = split(content);
    if (!parts) {
      errors.push(`${file}: no frontmatter`);
      continue;
    }
    const [frontmatter, rest] = parts;
    const stamped = [
      "---",
      ...withoutMetadata(frontmatter),
      ...stampLines(version),
      ...rest,
    ].join("\n");
    if (stamped !== content) writeFileSync(file, stamped);
  }

  if (check) {
    const config = JSON.parse(
      readFileSync("release-please-config.json", "utf8"),
    );
    const extraFiles = config.packages?.["."]?.["extra-files"] ?? [];
    if (
      !extraFiles.some(
        (entry) =>
          entry.type === "generic" && entry.glob && entry.path === STAMP_GLOB,
      )
    ) {
      errors.push(
        `release-please-config.json: extra-files needs { "type": "generic", "path": "${STAMP_GLOB}", "glob": true }, or releases stop updating metadata.version`,
      );
    }
  }
  if (errors.length > 0) {
    for (const error of errors) console.error(error);
    console.error(
      "Run `pnpm stamp` to set metadata.version in every SKILL.md from version.txt.",
    );
    process.exit(1);
  }
  if (check) {
    console.log(`Every SKILL.md carries metadata.version up to ${version}`);
  }
}

// realpath: a temporary directory on macOS is reached through a symlink, and
// import.meta.url is always the resolved path.
if (realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) main();
