#!/usr/bin/env node
// Post-commit step: re-syncs the real index with HEAD for the files the
// pre-commit hook generates or rewrites.
//
// A path-limited commit (`git commit REVIEW.md`) runs pre-commit on a
// temporary index. The hook stages the regenerated file there, so the commit
// is right, but git then restores the real index with the old entry: status
// shows a staged rollback plus an unstaged reapplication (MM). post-commit
// runs on the real index with no lock held, so it can set the entry back.
//
// An entry changes only when the worktree file equals HEAD's blob, so a later
// edit to the file, staged or not, is never touched.
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

process.chdir(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));

// Keep in step with the pre-commit steps that stage a file.
const GENERATED = [
  ".cursor/BUGBOT.md",
  ".claude-plugin/marketplace.json",
  "project-words.txt",
];

const git = (...args) =>
  execFileSync("git", args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  }).trim();

const synced = [];
for (const file of GENERATED) {
  let head, indexed, worktree;
  try {
    // "<mode> blob <sha>\t<path>", empty when HEAD lacks the file.
    head = git("ls-tree", "HEAD", "--", file).split(/\s/);
    // "<mode> <sha> <stage>\t<path>", empty when the index lacks it.
    indexed = git("ls-files", "--stage", "--", file).split(/\s/);
    worktree = git("hash-object", "--", file);
  } catch {
    // No HEAD yet, not a git repository, or the file is missing on disk.
    continue;
  }
  const [mode, , blob] = head;
  if (!blob || indexed[1] === blob || worktree !== blob) continue;
  git("update-index", "--add", "--cacheinfo", `${mode},${blob},${file}`);
  synced.push(file);
}

if (synced.length > 0) {
  console.log(`Re-synced the index with the commit: ${synced.join(", ")}`);
}
