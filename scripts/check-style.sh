#!/usr/bin/env bash
# House style checks, shared by CI and the pre-commit hook.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

if grep -rn --include='*.md' -e '—' skills README.md AGENTS.md .claude/commands .claude/agents 2>/dev/null; then
  echo 'Em dashes are forbidden (house style)'
  fail=1
fi

for f in skills/*/SKILL.md; do
  grep -Eq '^description: "?Use when' "$f" || {
    echo "$f: description must start with \"Use when\""
    fail=1
  }
done

exit $fail
