#!/usr/bin/env bash
# Checks supporting files shipped next to a SKILL.md:
# - every supporting file is linked from its SKILL.md with a markdown link
#   (agents resolve file references one level deep, so unlinked files are dead weight)
# - shell scripts have a shebang and pass a bash syntax check
# - python scripts parse
# Only files git knows about (tracked or staged) are checked, so untracked
# junk like .DS_Store or editor swap files never blocks a commit.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

for skill in skills/*/; do
  while IFS= read -r -d '' file; do
    [ "$file" = "${skill}SKILL.md" ] && continue
    rel=${file#"$skill"}

    # Require a markdown link target, "](rel" or "](./rel", so an unrelated
    # path that merely contains rel as a substring does not count as a link.
    if ! grep -qF "](${rel}" "${skill}SKILL.md" &&
      ! grep -qF "](./${rel}" "${skill}SKILL.md"; then
      echo "$file: not linked from ${skill}SKILL.md (expected a markdown link like [...](${rel}))"
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
  done < <(git ls-files -z -- "$skill")
done

exit $fail
