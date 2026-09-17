import {
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  readlinkSync,
  symlinkSync,
  unlinkSync,
} from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const commands = [
  { name: "skills-pr-summary", path: "pr-summary.md" },
  { name: "skills-squash-message", path: "squash-message.md" },
  {
    name: "skills-pr-handle",
    path: "skills/pr-handle.md",
  },
  {
    name: "skills-validate",
    path: "skills/validate.md",
  },
];

export function syncCommands(root, check = false) {
  const errors = [];
  const commandRoot = resolve(root, ".claude/commands");
  if (lstatSync(commandRoot, { throwIfNoEntry: false })) {
    for (const path of readdirSync(commandRoot, { recursive: true })) {
      if (
        path.endsWith(".md") &&
        !commands.some((command) => command.path === path)
      ) {
        errors.push(
          `${path}: no shared command mapping; add its canonical skill and mapping`,
        );
      }
    }
  }
  for (const command of commands) {
    const source = `.agents/skills/${command.name}/SKILL.md`;
    const target = resolve(root, ".claude/commands", command.path);
    try {
      // Codex ignores SKILL.md file symlinks, so the canonical file must be real.
      if (!lstatSync(resolve(root, source)).isFile()) {
        throw new Error(`${source}: expected a regular SKILL.md`);
      }
      const content = readFileSync(resolve(root, source), "utf8");
      const parts = content.match(/^---\n([\s\S]*?)\n---\n\n([\s\S]*)$/);
      const name = parts?.[1].match(/^name: (.+)$/m)?.[1];
      const description = parts?.[1].match(/^description: (.+)$/m)?.[1];
      if (name !== command.name || !description) {
        throw new Error(`${source}: invalid command skill metadata`);
      }
      const expected = relative(dirname(target), resolve(root, source));
      const stat = lstatSync(target, { throwIfNoEntry: false });
      if (stat && !stat.isSymbolicLink()) {
        throw new Error(
          `${command.path}: refusing to overwrite a regular file or directory`,
        );
      }
      if (stat && readlinkSync(target) === expected) continue;
      if (check)
        throw new Error(
          `${command.path}: missing or incorrect symlink to ${source}`,
        );
      mkdirSync(dirname(target), { recursive: true });
      if (stat) unlinkSync(target);
      symlinkSync(expected, target);
    } catch (error) {
      errors.push(error.message);
    }
  }
  return errors;
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2);
  if (args.some((arg) => arg !== "--check")) {
    console.error("Usage: node scripts/sync-agent-commands.mjs [--check]");
    process.exitCode = 1;
  } else {
    const errors = syncCommands(
      fileURLToPath(new URL("..", import.meta.url)),
      args.includes("--check"),
    );
    if (errors.length) {
      console.error(errors.join("\n"));
      console.error(
        "Run pnpm sync:agent-commands after editing the canonical skills.",
      );
      process.exitCode = 1;
    }
  }
}
