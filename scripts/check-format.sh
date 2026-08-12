#!/usr/bin/env bash
# Formatting check (prettier), shared by CI and the pre-commit hook.
# Fix violations with: pnpm format
set -euo pipefail
cd "$(dirname "$0")/.."

pnpm exec prettier --check .
