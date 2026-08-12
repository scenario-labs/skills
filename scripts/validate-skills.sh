#!/usr/bin/env bash
# Spec validation for every published skill, using skills-ref
# (the Agent Skills reference validator). Same command CI runs.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uvx >/dev/null 2>&1; then
  echo "validate-skills: uvx not found; install uv (https://docs.astral.sh/uv/) to run spec validation" >&2
  exit 1
fi

for d in skills/*/; do
  uvx --from "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref" skills-ref validate "$d"
done
