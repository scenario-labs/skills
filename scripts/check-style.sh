#!/usr/bin/env bash
# House style checks, shared by CI and the pre-commit hook.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

# GNU grep exits 2 on any error (e.g. a missing path) even when matches were
# found, so treat 0 as "violations found" and >=2 as a loud config failure
# instead of letting either case pass silently.
grep_status=0
grep -rn --include='*.md' -e '—' skills README.md AGENTS.md .claude/commands .claude/agents || grep_status=$?
if [ "$grep_status" -eq 0 ]; then
  echo 'Em dashes are forbidden (house style)'
  fail=1
elif [ "$grep_status" -ge 2 ]; then
  echo "check-style: grep failed (exit $grep_status); a checked path is probably missing"
  fail=1
fi

for f in skills/*/SKILL.md; do
  grep -Eq '^description: "?Use when' "$f" || {
    echo "$f: description must start with \"Use when\""
    fail=1
  }
done

exit $fail
