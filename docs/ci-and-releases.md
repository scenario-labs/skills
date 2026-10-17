# CI and releases

Release mechanics and CI pinning. [AGENTS.md](../AGENTS.md) "Pull requests and releases" states
which commit types release and which files release-please owns.

## Releases

- release-please never lets you pick the version. To force an exact one, dispatch the workflow by
  hand: `gh workflow run release-please.yml --ref main -f release_as=X.Y.Z`, which must be higher
  than `.release-please-manifest.json`. Never push an empty `Release-As` commit to `main`.
- The dispatch runs the release-please CLI (pinned in `package.json` to the version the action
  bundles), not the action: release-please-action v5 silently drops `release-as` in manifest mode,
  which this repo's `release-please-config.json` selects.
- The override is one-shot: the next push to `main` re-derives the version and rewrites the release
  PR, so merge it promptly. A pin that survives pushes is `"release-as"` in
  `release-please-config.json`, through a PR, removed once released.
- Merging the release PR tags `skills-vX.Y.Z`, titles the GitHub release `skills: vX.Y.Z`, rewrites
  `CHANGELOG.md`, `version.txt`, and `.release-please-manifest.json`, and publishes the GitHub
  release.
- `.github/workflows/publish-changelog.yml` then posts the notes to the public changelog at
  [scenario.com/changelog](https://www.scenario.com/changelog). It hangs off the
  `release: published` event, not the release-please run, because release-please reports a created
  release exactly once. Re-run a failed post from the Actions tab, or dispatch it by tag.
- Because release-please owns `CHANGELOG.md`, it sits in `.prettierignore`, where it also keeps
  prettier from rewriting release-please's `*` bullets. It also sits in cspell's ignorePaths, as a
  guard should the spell-check globs widen; `scripts/check-spelling.sh` does not reach it today.
- In `.release-please-manifest.json`, exactly `0.0.0` is the sentinel for "no release yet": it makes
  `initial-version` and the root `bootstrap-sha` apply. Editing it to match `initial-version` looks
  like a sync fix and silently changes the first release number.
- The release PR title (`chore: release skills X.Y.Z`) passes commitlint because an omitted scope
  only warns.
- The `skills-` tag prefix matches the sibling repositories' convention. It is set by hand as
  `component` plus `include-component-in-tag` in `release-please-config.json`, because
  `release-type: simple` derives none, unlike `release-type: node`, which takes one from the
  `package.json` name.
- Changing the tag format orphans release-please from its own history unless the existing tag and
  its GitHub release move with it. The next changelog then replays every commit since
  `bootstrap-sha`.

## CI

- Dependabot (`.github/dependabot.yml`) proposes one grouped `ci(deps)` PR a week, for releases at
  least seven days old. It skips release-please-action, which moves by hand together with the
  `release-please` pin in `package.json`.
