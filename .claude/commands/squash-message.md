Generate a single squash commit message for the current PR.

1. Run `git fetch origin main --quiet && git log --oneline $(git merge-base HEAD origin/main)..HEAD` to see all commits in this branch
2. Analyze all the changes: what was added, fixed, refactored
3. Write ONE conventional commit message that summarizes the entire PR and passes `commitlint.config.js`:
   - Title: max 120 chars, conventional commit format (feat/fix/docs/chore), scope from the skill directory names or the cross-cutting scopes (skills, agents, ci, deps, docs, tooling)
   - Body: bullet points of key changes, grouped by category
   - Footer: Co-Authored-By line
4. Preserve distinct meaningful changes instead of flattening everything into one vague line; it is fine for the body to list multiple feat and fix items
5. Verify the title passes: `echo "TITLE" | pnpm exec commitlint`
6. Copy the message to clipboard with `echo "MESSAGE" | pbcopy`
7. Tell me the message you copied
