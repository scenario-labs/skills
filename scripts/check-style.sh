#!/usr/bin/env bash
# House style checks, shared by CI and the pre-commit hook.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

# Reporting helper for the em-dash rule. Every rule prints its diagnosis before
# its evidence, and the evidence has to name the offending character: a raw
# grep line that begins with a "- " list bullet reads like the bullet was the
# match, which is how a real em dash on a bulleted line got misdiagnosed as a
# false positive. So each hit is re-emitted as path:line:column with every em
# dash wrapped in >>> <<<.
#
# LC_ALL=C pins awk to byte semantics, so the column is the same number on BSD
# and GNU awk regardless of the caller's locale (an em dash is 3 UTF-8 bytes,
# and a UTF-8-aware awk would otherwise count it as one character). Text before
# an em dash is ASCII in practice, so the byte column is also the character
# column there.
#
# index()/substr() walk the line instead of gsub() so the em dash is matched
# literally, never as a regular expression.
annotate_em_dashes() {
  printf '%s\n' "$1" | LC_ALL=C awk -v dash='—' -v mark_open='>>>' -v mark_close='<<<' '
    {
      text = $0
      prefix = ""
      # Split off grep -n decoration ("path:line:") so the column counts from
      # the start of the file line, not from the start of grep output.
      if (match(text, /^[^:]+:[0-9]+:/)) {
        prefix = substr(text, 1, RLENGTH)
        text = substr(text, RLENGTH + 1)
      }
      out = ""
      rest = text
      column = 0
      consumed = 0
      while ((i = index(rest, dash)) > 0) {
        if (column == 0) {
          column = consumed + i
        }
        out = out substr(rest, 1, i - 1) mark_open dash mark_close
        consumed = consumed + i + length(dash) - 1
        rest = substr(rest, i + length(dash))
      }
      # A path that itself holds a colon cannot be split from grep decoration
      # reliably, so drop the column rather than print one counted from the
      # wrong place. The marker still shows which character failed.
      if (prefix == "") {
        printf "  %s\n", out rest
      } else {
        printf "  %s%d: %s\n", prefix, column, out rest
      }
    }
  '
}

# GNU grep exits 2 on any error (e.g. a missing path) even when matches were
# found, so treat 0 as "violations found" and >=2 as a loud config failure
# instead of letting either case pass silently.
grep_status=0
# CODE_OF_CONDUCT.md is excluded on purpose: it is the published Contributor
# Covenant text kept byte-identical to its source, like the vendored dev skills.
em_dash_hits=$(grep -rn --include='*.md' -e '—' skills README.md AGENTS.md CONTRIBUTING.md SECURITY.md .github .claude/commands .claude/agents) || grep_status=$?
if [ "$grep_status" -eq 0 ]; then
  echo 'Em dashes are forbidden (house style). Each hit below is path:line:column (column counts from 1) with the offending em dash (U+2014) wrapped in >>> <<<; a leading "- " list bullet is an ASCII hyphen, never the match.'
  annotate_em_dashes "$em_dash_hits"
  fail=1
elif [ "$grep_status" -ge 2 ]; then
  echo "check-style: grep failed (exit $grep_status); a checked path is probably missing"
  # grep can both error and match, so show whatever it did find, still marked up.
  if [ -n "$em_dash_hits" ]; then
    echo 'Em dashes found before that failure, as path:line:column with the em dash (U+2014) wrapped in >>> <<<:'
    annotate_em_dashes "$em_dash_hits"
  fi
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
  echo 'Notice (not a failure): skill documentation mentions the Scenario SDK. Confirm it describes a script rather than the route an agent takes at runtime, per AGENTS.md "Authoring contract". Mentions found:'
  printf '%s\n' "$sdk_hits" | sed 's/^/  /'
elif [ "$grep_status" -ge 2 ]; then
  echo "check-style: grep failed (exit $grep_status); a checked path is probably missing"
  fail=1
fi

for f in skills/*/SKILL.md; do
  grep -Eq '^description: "?Use when' "$f" || {
    echo "$f: description must start with \"Use when\""
    fail=1
  }

  # 1000-word target, 2500-word hard cap; AGENTS.md "Authoring contract" carries
  # the why. Body is everything after the closing frontmatter ---.
  body=$(awk 'BEGIN { fm = 0 } /^---$/ { fm++; next } fm >= 2 { print }' "$f")
  words=$(printf '%s\n' "$body" | wc -w | tr -d ' ')
  if [ "$words" -gt 2500 ]; then
    echo "$f: body is $words words, over the 2500-word hard cap"
    fail=1
  fi
done

# Context fan-out: a skill plus the siblings it names in backticks, weighed
# against the token pool Claude Code re-attaches skills from after compaction.
# AGENTS.md "Authoring contract" carries the why. A notice and never a failure,
# because the total moves when a skill nobody touched grows.
reattach_pool=25000
reattach_per_skill=5000
fanout_notice_at=20000

# The pre-commit hook runs on the macOS system bash, 3.2, which has no
# associative arrays.
skill_tokens_file=$(mktemp)
trap 'rm -f "$skill_tokens_file"' EXIT

for f in skills/*/SKILL.md; do
  name=$(basename "$(dirname "$f")")
  body=$(awk 'BEGIN { fm = 0 } /^---$/ { fm++; next } fm >= 2 { print }' "$f")
  chars=$(printf '%s\n' "$body" | wc -c | tr -d ' ')
  tokens=$((chars / 4))
  if [ "$tokens" -gt "$reattach_per_skill" ]; then
    tokens=$reattach_per_skill
  fi
  printf '%s\t%s\n' "$name" "$tokens" >>"$skill_tokens_file"
done

# Empty means the name is not a skill (a model id, or ordinary prose).
skill_tokens() {
  awk -F'\t' -v want="$1" '$1 == want { print $2; exit }' "$skill_tokens_file"
}

fanout_hits=""
for f in skills/*/SKILL.md; do
  name=$(basename "$(dirname "$f")")
  body=$(awk 'BEGIN { fm = 0 } /^---$/ { fm++; next } fm >= 2 { print }' "$f")
  total=$(skill_tokens "$name")
  siblings=$(printf '%s\n' "$body" | grep -oE '`scenario(-[a-z0-9]+)*`' | tr -d '`' | sort -u | grep -vx "$name" || true)
  count=0
  for sibling in $siblings; do
    sibling_tokens=$(skill_tokens "$sibling")
    [ -n "$sibling_tokens" ] || continue
    total=$((total + sibling_tokens))
    count=$((count + 1))
  done
  if [ "$total" -ge "$fanout_notice_at" ]; then
    fanout_hits="${fanout_hits}  ${name}: with its ${count} named siblings, about ${total} tokens of the ${reattach_pool}-token pool
"
  fi
done

if [ -n "$fanout_hits" ]; then
  echo "Notice (not a failure): a skill's context fan-out is approaching the ${reattach_pool}-token re-attach pool Claude Code shares across skills after compaction. Past it, the least recently invoked skills are dropped entirely. Trim the body, or drop a sibling reference the workflow does not need."
  printf '%s' "$fanout_hits"
fi

exit $fail
