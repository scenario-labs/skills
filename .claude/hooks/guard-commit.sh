#!/usr/bin/env bash
# PreToolUse hook on Bash: refuse a git commit that skips the husky hooks, so
# commitlint and pnpm validate run on every commit an agent makes. Commits made
# without them reached PRs (#253, #315, #353), and ensure-husky.sh lets a
# session continue when pnpm install fails. guard-commit.mjs holds the logic.
# Exit 2 blocks the command and shows stderr to the agent. Any other failure
# blocks it too, so a check that cannot run never lets a commit through.
set -uo pipefail

input=$(cat) || exit 2
# A command that never says "commit" cannot run git commit; skip node for it.
case "$input" in
  *commit*) ;;
  *) exit 0 ;;
esac

status=0
printf '%s' "$input" | node "$(dirname "$0")/guard-commit.mjs" || status=$?
if [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; then
  echo "guard-commit: the check could not run (exit $status), so the command is refused. Run 'pnpm install', and check that node runs." >&2
fi
[ "$status" -eq 0 ] || exit 2
