# Listing and install commands

How skills.sh, the installer picker, and the install commands work. [AGENTS.md](../AGENTS.md)
"Adding a skill" holds the checklist; this file holds the mechanics.

- `pnpm groupings` proves `skills.sh.json` valid, not that skills.sh has applied it.
  - Per the [customize docs](https://www.skills.sh/docs/customize), the directory reads the file
    only after its telemetry has seen the repository: in practice, after a fresh
    `npx skills add scenario-labs/skills` run with telemetry enabled.
  - Repo pages are cached, so the skill content on
    [the repo page](https://www.skills.sh/scenario-labs/skills) trails `main` by hours.
  - Ungrouped listings appear under "Other skills". `notGrouped` controls their position, not their
    visibility.
- `pnpm manifest` (`scripts/generate-plugin-manifest.mjs`) generates
  `.claude-plugin/marketplace.json` from `skills.sh.json`, the single source of truth. Never edit
  the manifest by hand. `pnpm manifest:check` fails validation and CI when the two drift; the
  pre-commit hook regenerates the manifest.
  - The manifest gives the `npx skills add` picker its group headers. The skills CLI groups the
    picker by the manifest's plugin entries and never reads `skills.sh.json`, which only drives the
    skills.sh repo page.
  - The manifest also makes the repo a Claude Code plugin marketplace, `scenario-skills`, one plugin
    per grouping. A plugin's name is its install key (`<plugin>@scenario-skills`) and the namespace
    of its skills (`/030-images:scenario-image`).
  - Plugin names come from `scripts/plugin-names.json`, keyed by grouping title: a fixed three-digit
    number assigned once, with gaps, then the slug (`030-images`). The picker sorts groups by name
    and shows them title-cased ("030 Images"), so the numbers keep it in `skills.sh.json` order. The
    old position-derived prefix renumbered install keys whenever a grouping was inserted.
  - A new grouping takes a free number between its neighbors' (`035-...` between `030` and `040`).
    `pnpm manifest:check` fails on a grouping without a name, an unused name, a name out of
    `skills.sh.json` order, or a retired name. Renaming or removing a grouping breaks every install
    of its plugin, so its old name moves to `retired` in the same reviewed change.
  - Plugin entries carry no `version`, so Claude Code versions each plugin by commit and its catalog
    entry and files always come from the same commit. Users add the marketplace from the `stable`
    branch, which the release workflow fast-forwards to each release, so plugins change only at
    releases ([docs/ci-and-releases.md](ci-and-releases.md#releases)).
  - Every installed skill costs always-on context, so the README recommends the getting-started
    plugin plus the per-role sets in `INSTALL.md`, each with its cost measured by
    `claude plugin details`. `pnpm readme` checks that every plugin those commands name exists, and
    that the README's install-everything loop lists exactly the plugins holding core skills.
- Install commands:
  - `npx skills add scenario-labs/skills` opens a picker with nothing preselected, so a reader who
    runs the bare command and hits enter installs nothing. The README says so on the command.
  - The README does not offer `--skill "*"`: it takes every skill, the expert tools included, and an
    agent loads every installed skill's description at startup.
  - The README Install section leads with a default command that writes out every core skill, then
    points to `INSTALL.md`.
  - `INSTALL.md` holds one command per role and one per goal. A role command is a base of `scenario`
    plus the troubleshooting skills, the role's lead skills, and the siblings they name in
    backticks, one level deep (transitively would pull in nearly everything). A goal command is
    `scenario`, the goal's lead skills, and their siblings.
  - Roles are the complete taxonomy; goals are shortcuts for readers who think in outcomes. Both
    stay in `INSTALL.md`, not the README, so every curated command sits in one checked file.
  - `pnpm readme` checks that every install command passes all its names after one `--skill` (the
    CLI collects names up to the next flag) and names only real skills. It checks that the default
    lists exactly the core skills, and that each family README's command lists exactly its family.
  - Until the skills CLI can install a group from the command line
    ([#192](https://github.com/scenario-labs/skills/issues/192)), `pnpm readme` also fails when a
    core skill sits in no `INSTALL.md` role command, or when a role's or goal's "N skills." count
    disagrees with its command.
  - A skills.sh pack URL (`npx skills add https://skills.sh/p/<id>`) is the only install that
    preselects a set. Packs are created manually on skills.sh behind a Vercel sign-in (no CLI or
    API); pack links belong in README.md's Install section.
