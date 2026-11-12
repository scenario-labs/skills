#!/usr/bin/env node
// The freshness block every SKILL.md carries (AGENTS.md, "Layout"): fixed text
// that has an agent date the installed file and tell the user once when it is
// over two months old. An installed copy never refreshes itself, and a session
// that loads one skill does not load the root skill, so each skill carries its
// own (docs/decisions.md, "Freshness block").
//
//   node scripts/freshness-block.mjs            write the block into every skill
//   node scripts/freshness-block.mjs --force    the same, replacing an edited block
//                                               (after a change to BLOCK below)
//   node scripts/freshness-block.mjs --check    problems, exit 1 if any
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { listSkills } from "./lib/skills.mjs";

// The heading names the moment to act, and the block is the last section:
// both decide whether an agent follows it (docs/decisions.md, "Freshness block").
export const HEADING = "## Before your final reply";

// Wrapped as prettier wraps it, so `pnpm format` and this script agree.
export const BLOCK = `${HEADING}

Run \`ls -l\` on this file. Over two months old: tell the user once it may be outdated
(https://github.com/scenario-labs/skills#install). Otherwise say nothing.
`;

// Indexes of the "## " heading lines, frontmatter and fenced code skipped.
function sectionStarts(lines) {
  const starts = [];
  let frontmatter = lines[0] === "---";
  let fence = null;
  lines.forEach((line, index) => {
    if (frontmatter) {
      if (index > 0 && line === "---") frontmatter = false;
      return;
    }
    const marker = line.trimStart().match(/^(```|~~~)/)?.[1];
    if (marker && (fence === null || fence === marker)) {
      fence = fence === null ? marker : null;
      return;
    }
    if (fence === null && line.startsWith("## ")) starts.push(index);
  });
  return starts;
}

// { rest, blocks }: the text without its freshness sections, and each of those
// sections from its heading to the next one. A merge can leave two.
function separateBlocks(text) {
  const lines = text.split("\n");
  const starts = sectionStarts(lines);
  const blocks = [];
  const rest = [];
  let from = 0;
  for (const at of starts.filter((index) => lines[index] === HEADING)) {
    const end = starts.find((index) => index > at) ?? lines.length;
    blocks.push(`${lines.slice(at, end).join("\n").trimEnd()}\n`);
    rest.push(...lines.slice(from, at));
    from = end;
  }
  rest.push(...lines.slice(from));
  return { rest: rest.join("\n"), blocks };
}

const isEdited = (blocks) => blocks.some((block) => block !== BLOCK);

export const withBlock = (text) =>
  `${separateBlocks(text).rest.trimEnd()}\n\n${BLOCK}`;

export function blockProblem(text) {
  const { blocks } = separateBlocks(text);
  if (blocks.length === 0) return "has no freshness block";
  if (isEdited(blocks)) return "freshness block differs from the fixed text";
  if (blocks.length > 1) return "has more than one freshness block";
  if (text !== withBlock(text)) {
    return "freshness block is not the last section";
  }
  return null;
}

// Resolved, because a temporary directory is often reached through a symlink.
if (
  process.argv[1] &&
  realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));
  const mode = process.argv[2];
  const files = listSkills().map((skill) => path.join(skill.dir, "SKILL.md"));
  // A Windows checkout can hold CRLF: its heading line would not match, and a
  // write would append a second block.
  const read = (file) => readFileSync(file, "utf8").replaceAll("\r\n", "\n");
  if (mode === "--check") {
    const problems = files
      .map((file) => [file, blockProblem(read(file))])
      .filter(([, problem]) => problem);
    for (const [file, problem] of problems)
      console.error(`${file}: ${problem}`);
    if (problems.length > 0) {
      console.error("Run `pnpm freshness` to write the block.");
    }
    process.exit(problems.length > 0 ? 1 : 0);
  }
  // A plain write only replaces the block it recognizes, so it never drops
  // lines an author wrote under the heading.
  const refused = [];
  for (const file of files) {
    const text = read(file);
    if (isEdited(separateBlocks(text).blocks) && mode !== "--force") {
      refused.push(file);
      continue;
    }
    const next = withBlock(text);
    if (next !== readFileSync(file, "utf8")) writeFileSync(file, next);
  }
  if (refused.length > 0) {
    for (const file of refused) {
      console.error(
        `${file}: the text under "${HEADING}" is not the fixed block, so it was left alone`,
      );
    }
    console.error(
      "Move what you wrote to another section. After a wording change, run `pnpm freshness --force`, which replaces everything under the heading.",
    );
    process.exit(1);
  }
}
