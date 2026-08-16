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

# MCP is the surface a skill teaches (AGENTS.md, "Authoring contract"), so skill
# documentation should not hand an agent the official SDK in place of a tool it
# could call itself. Scripts are free to use the SDK, so a hit here is a notice
# for review to weigh and never a failure: it asks whether the mention describes
# a script or teaches the agent's own route. The pattern is case insensitive, so
# it already covers the SCENARIO_SDK_API_KEY and _SECRET environment variables.
grep_status=0
sdk_hits=$(grep -rniE --include='*.md' -e 'scenario[-_]sdk' skills) || grep_status=$?
if [ "$grep_status" -eq 0 ]; then
  echo "$sdk_hits"
  echo 'Notice (not a failure): skill documentation mentions the Scenario SDK. Confirm it describes a script rather than the route an agent takes at runtime, per AGENTS.md "Authoring contract".'
elif [ "$grep_status" -ge 2 ]; then
  echo "check-style: grep failed (exit $grep_status); a checked path is probably missing"
  fail=1
fi

for f in skills/*/SKILL.md; do
  grep -Eq '^description: "?Use when' "$f" || {
    echo "$f: description must start with \"Use when\""
    fail=1
  }

  # Body word budget (AGENTS.md "Authoring contract"): 400-600 words with a
  # hard cap of 900. Only the hard cap fails the build; the 400-600 target
  # stays editorial. The body is everything after the closing frontmatter ---.
  words=$(awk 'BEGIN { fm = 0 } /^---$/ { fm++; next } fm >= 2 { print }' "$f" | wc -w | tr -d ' ')
  if [ "$words" -gt 900 ]; then
    echo "$f: body is $words words, over the 900-word hard cap"
    fail=1
  fi
done

exit $fail
