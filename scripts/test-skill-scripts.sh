#!/usr/bin/env bash
# Runs the test suites for scripts shipped with skills (see AGENTS.md):
# - every core skill that ships a .py or .ts file (at any depth) must have
#   at least one test file under tests/<name>/; expert tools are exempt
#   (docs/expert-tools.md), and check-skill-files.sh still parses every
#   Python script they ship
# - every tests/<name>/ directory must match an existing skill and hold
#   at least one test file
# - Python suites (test_*.py) run with stdlib unittest, under uv when the
#   suite declares a requirements.txt and uv is installed
# - TypeScript suites (*.test.ts) run with vitest
# - COVERAGE=1 also measures core skills' scripts, Python through
#   .coveragerc and TypeScript through vitest's v8 provider, and writes
#   Cobertura reports (coverage/python.xml,
#   coverage/vitest/cobertura-coverage.xml) plus the Python table in
#   coverage/report.md; no threshold fails a run
# Suites may need system tools such as ffmpeg, so this runs in CI and on
# demand, not in the pre-commit hook.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
coverage=${COVERAGE:-}
# 7.10 added patch = subprocess, which follows the scripts suites spawn.
COVERAGE_PY="coverage>=7.10"
[ -z "$coverage" ] || rm -rf coverage

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
ts_dirs=()
ts_include=()
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
    # uv installs a suite's requirements into a cached environment of its
    # own, so a local run needs no pip step. python3 is pinned by path
    # because uv otherwise prefers an active conda or virtual environment.
    # CI uses its hash-checked environment even when the runner has uv installed.
    python=(python3)
    req="${dir}requirements.txt"
    with=()
    [ ! -f "$req" ] || with+=(--with-requirements "$req")
    [ -z "$coverage" ] || with+=(--with "$COVERAGE_PY")
    if [ "${SKILLS_TEST_USE_SYSTEM_PYTHON:-}" != 1 ] &&
      [ "${#with[@]}" -gt 0 ] && command -v uv >/dev/null; then
      python=(uv run --quiet --no-project --python "$(command -v python3)"
      "${with[@]}" python)
    fi
    # No -t: hyphenated skill names are not importable as packages, so each
    # suite directory is its own top level and modules load as bare names.
    unittest=(-m unittest discover -s "$dir")
    [ -z "$coverage" ] ||
      unittest=(-m coverage run --rcfile=.coveragerc "${unittest[@]}")
    "${python[@]}" -B "${unittest[@]}" || fail=1
  fi
  if find "$dir" -type f -name '*.test.ts' | grep -q .; then
    ran=1
    skill=$(node scripts/lib/skills.mjs --dir "$name")
    # Under coverage, core suites share one vitest run below: a run per
    # suite would overwrite the one Cobertura report the upload takes.
    if [ -n "$coverage" ] && grep -qx "${skill}/" <<<"$core_dirs"; then
      ts_dirs+=("$dir")
      ts_include+=(--coverage.include="${skill}/**")
    else
      echo "== ${name}: vitest =="
      pnpm exec vitest run "$dir" || fail=1
    fi
  fi
done

[ "$ran" -eq 1 ] || echo "No skill-script test suites to run."

if [ "${#ts_dirs[@]}" -gt 0 ]; then
  echo "== vitest with coverage: ${ts_dirs[*]} =="
  pnpm exec vitest run "${ts_dirs[@]}" --coverage "${ts_include[@]}" \
    --coverage.reporter=text --coverage.reporter=cobertura \
    --coverage.reportsDirectory=coverage/vitest || fail=1
fi

if [ -n "$coverage" ] && compgen -G 'coverage/.coverage.*' >/dev/null; then
  echo "== python coverage =="
  report=(python3)
  if [ "${SKILLS_TEST_USE_SYSTEM_PYTHON:-}" != 1 ] && command -v uv >/dev/null; then
    report=(uv run --quiet --no-project --python "$(command -v python3)"
    --with "$COVERAGE_PY" python)
  fi
  report+=(-m coverage)
  "${report[@]}" combine --rcfile=.coveragerc -q &&
    "${report[@]}" report --rcfile=.coveragerc &&
    "${report[@]}" report --rcfile=.coveragerc --format=markdown \
      >coverage/report.md &&
    "${report[@]}" xml --rcfile=.coveragerc -q -o coverage/python.xml ||
    fail=1
fi

exit $fail
