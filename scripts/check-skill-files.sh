#!/usr/bin/env bash
# Checks supporting files shipped next to a SKILL.md:
# - every supporting file is linked directly from its SKILL.md
#   (agents resolve file references one level deep, so unlinked files are dead weight)
# - shell scripts have a shebang and pass a bash syntax check
# - python scripts parse
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

for skill in skills/*/; do
  while IFS= read -r file; do
    rel=${file#"$skill"}

    if ! grep -qF "$rel" "${skill}SKILL.md"; then
      echo "$file: not referenced from ${skill}SKILL.md"
      fail=1
    fi

    case "$file" in
      *.sh)
        head -1 "$file" | grep -q '^#!' || {
          echo "$file: missing shebang"
          fail=1
        }
        bash -n "$file" || {
          echo "$file: bash syntax check failed"
          fail=1
        }
        ;;
      *.py)
        python3 -c 'import ast, sys; ast.parse(open(sys.argv[1]).read())' "$file" || {
          echo "$file: python syntax check failed"
          fail=1
        }
        ;;
    esac
  done < <(find "$skill" -type f ! -name 'SKILL.md')
done

exit $fail
