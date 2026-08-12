#!/usr/bin/env bash
# Runs the test suites for scripts shipped with skills (see AGENTS.md):
# - every skill that ships a .py or .ts file must have a suite in tests/<name>/
# - every tests/<name>/ directory must match an existing skill
# - Python suites (test_*.py) run with stdlib unittest
# - TypeScript suites (*.test.ts) run with vitest
# Suites may need system tools such as ffmpeg, so this runs in CI and on
# demand, not in the pre-commit hook.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

# Every shipped script needs a suite.
while IFS= read -r -d '' file; do
  case "$file" in
    skills/*/*.py | skills/*/*.ts)
      name=${file#skills/}
      name=${name%%/*}
      if [ ! -d "tests/${name}" ]; then
        echo "$file: shipped script has no test suite under tests/${name}/ (see AGENTS.md)"
        fail=1
      fi
      ;;
  esac
done < <(git ls-files -z -- 'skills/*')

# Every suite needs a skill, and passes.
ran=0
for dir in tests/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  if [ ! -d "skills/${name}" ]; then
    echo "$dir: no matching skills/${name}/ directory"
    fail=1
    continue
  fi
  if compgen -G "${dir}test_*.py" > /dev/null; then
    ran=1
    echo "== ${name}: python unittest =="
    # No -t: hyphenated skill names are not importable as packages, so each
    # suite directory is its own top level and modules load as bare names.
    python3 -B -m unittest discover -s "$dir" || fail=1
  fi
  if compgen -G "${dir}*.test.ts" > /dev/null; then
    ran=1
    echo "== ${name}: vitest =="
    pnpm exec vitest run "$dir" || fail=1
  fi
done

[ "$ran" -eq 1 ] || echo "No skill-script test suites to run."

exit $fail
