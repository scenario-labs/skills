#!/usr/bin/env bash
# Spell check for authored markdown, shared by CI and the pre-commit hook.
# Legitimate project terms go in project-words.txt, never inline disables.
set -euo pipefail
cd "$(dirname "$0")/.."

pnpm exec cspell --no-progress --relative --no-must-find-files \
  'skills/**/*.md' \
  'README.md' \
  'AGENTS.md' \
  '.claude/commands/*.md' \
  '.claude/agents/*.md'
