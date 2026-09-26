#!/usr/bin/env bash
# Runs the test suites for scripts shipped with skills (see AGENTS.md):
# - every core skill that ships a .py or .ts file (at any depth) must have
#   at least one test file under tests/<name>/; expert tools are exempt
#   (AGENTS.md, "Expert tools"), and check-skill-files.sh still parses every
#   Python script they ship
# - every tests/<name>/ directory must match an existing skill and hold
#   at least one test file
# - Python suites (test_*.py) run with stdlib unittest
# - TypeScript suites (*.test.ts) run with vitest
# Suites may need system tools such as ffmpeg, so this runs in CI and on
# demand, not in the pre-commit hook.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

has_tests() {
  find "$1" -type f \( -name 'test_*.py' -o -name '*.test.ts' \) 2>/dev/null |
    grep -q .
}

# Every script a core skill ships needs a suite with at least one test file.
# In a case pattern `*` crosses `/`, so nested scripts are covered too.
core_dirs=$(node scripts/lib/skills.mjs --core)
for dir in $core_dirs; do
  name=$(basename "$dir")
  while IFS= read -r -d '' file; do
    case "$file" in
      *.py | *.ts)
        if ! has_tests "tests/${name}"; then
          echo "$file: shipped script has no test files under tests/${name}/ (see AGENTS.md)"
          fail=1
        fi
        ;;
    esac
  done < <(git ls-files -z -- "$dir")
done

# Every suite needs a skill, at least one test file, and a green run.
ran=0
for dir in tests/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  if ! node scripts/lib/skills.mjs --dir "$name" >/dev/null 2>&1; then
    echo "$dir: no skill named ${name} under skills/"
    fail=1
    continue
  fi
  if ! has_tests "$dir"; then
    echo "$dir: no test files (expected test_*.py or *.test.ts)"
    fail=1
    continue
  fi
  if find "$dir" -type f -name 'test_*.py' | grep -q .; then
    ran=1
    echo "== ${name}: python unittest =="
    # No -t: hyphenated skill names are not importable as packages, so each
    # suite directory is its own top level and modules load as bare names.
    python3 -B -m unittest discover -s "$dir" || fail=1
  fi
  if find "$dir" -type f -name '*.test.ts' | grep -q .; then
    ran=1
    echo "== ${name}: vitest =="
    pnpm exec vitest run "$dir" || fail=1
  fi
done

[ "$ran" -eq 1 ] || echo "No skill-script test suites to run."

exit $fail
