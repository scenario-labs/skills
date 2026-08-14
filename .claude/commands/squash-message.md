Generate a single squash commit message for the current PR.

1. Run `git fetch origin main --quiet && git log --oneline $(git merge-base HEAD origin/main)..HEAD` to see all commits in this branch
2. Analyze the net diff against main (`git diff $(git merge-base HEAD origin/main)..HEAD`): what the PR adds, fixes, or refactors relative to main. The commit list is context, not content: the message describes the diff, not the journey.
3. Write ONE conventional commit message that summarizes the entire PR and passes `commitlint.config.js`:
   - Title: max 120 chars, conventional commit format (feat/fix/docs/chore), scope from the skill directory names or the cross-cutting scopes (skills, agents, ci, deps, docs, tooling)
   - Body: bullet points of key changes, grouped by category
   - Footer: Co-Authored-By line
4. Preserve distinct meaningful changes instead of flattening everything into one vague line, but only changes that exist in the net diff. A branch commit that fixes or reworks something introduced earlier in the same branch is development churn: fold it into the item it amends, never list it as a fix. Label a body item `feat` or `fix` only when the PR mixes both kinds of net change relative to main; a PR that only adds one thing gets plain bullets describing what landed.
5. Verify the title passes: `echo "TITLE" | pnpm exec commitlint`
6. Copy the message to clipboard with `echo "MESSAGE" | pbcopy`
7. Tell me the message you copied
