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
- Two release-please `extra-files` entries carry the version into shipped files
  ([docs/decisions.md](decisions.md#skill-and-plugin-versions) records why):
  - `skills/**/SKILL.md` (`generic`, `"glob": true`) rewrites `metadata.version` in every skill. The
    updater only touches a line holding `x-release-please-version`, which rides as a YAML comment:
    `version: "X.Y.Z" # x-release-please-version`. release-please expands the glob over `main` each
    time it rebuilds the release PR, so new skills are included.
  - `.claude-plugin/marketplace.json` (`json`, `$.plugins[*].version`) rewrites every plugin's
    version. The manifest generator writes the same value from `version.txt`, so
    `pnpm manifest:check` passes on the release PR.
- `pnpm stamp` writes `metadata.version` from `version.txt`. `pnpm stamp:check` fails validation and
  CI on a missing, misplaced, or malformed version, one newer than `version.txt`, or a missing
  `extra-files` entry for the skills.
- An older `metadata.version` passes on purpose. `main` does not require branches to be up to date,
  so a new skill stamped before a release can merge after it, and the next release PR rewrites it.
- Tests run release-please's own pinned updaters on both files (`scripts/version-stamp.test.mjs`,
  `scripts/generate-plugin-manifest.test.mjs`), so a format or marker change fails before a release
  does.
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

- `script-tests` runs once on `ubuntu-24.04` and once on `ubuntu-26.04`, which install ffmpeg 6.1
  and 8.0 from apt.
  - Each runner is the coverage for one ffmpeg version, so both stay named, never `ubuntu-latest`.
  - When a newer LTS runner ships, add it as a new entry rather than renaming an existing one.
  - Never hardcode a count derived from a probed duration in a test. ffmpeg 8 reports an MP3's
    gapless duration, while 6.1 and 7.1 include the encoder padding.
  - The `ubuntu-24.04` leg runs with `COVERAGE=1` and posts the Python table to its job summary. The
    vitest table stays in the step log.
  - Coverage spans core skills only (`.coveragerc`). Expert-tool scripts mostly run inside their
    host application, which coverage.py cannot follow.
  - It reports without a threshold, so a drop never fails CI.
- `upload-coverage` sends both Cobertura reports to GitHub code coverage (part of Code Quality),
  which shows each PR's percentage against `main`.
  - It needs code coverage enabled in the repository's Code Quality settings.
  - Fork PRs skip it: their token cannot hold `code-quality: write`.
  - Separate labels (`code-coverage/python`, `code-coverage/vitest`) keep the two reports apart.
- Dependabot (`.github/dependabot.yml`) proposes one grouped PR a week per ecosystem, for releases
  at least seven days old:
  - `ci(deps)` for GitHub Actions;
  - `chore(deps)` for the npm dev tooling in `pnpm-lock.yaml`;
  - `chore(deps)` for the test suites' `tests/*/requirements.txt`. It raises the floors too, since
    advisory scanners such as OpenSSF Scorecard read a requirement's lower bound, not the version CI
    installs.
  - It skips release-please-action and the `release-please` CLI, which move by hand together: the
    `package.json` pin must stay the version the action bundles.
