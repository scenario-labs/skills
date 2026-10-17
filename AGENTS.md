# AGENTS.md

Guidance for AI agents (and humans) working in this repository. The history and evidence behind its
rules live in [docs/decisions.md](docs/decisions.md).

## What this repo is

Public Agent Skills for [Scenario](https://scenario.com): procedural knowledge that teaches AI
coding agents to create production-ready content through the
[Scenario MCP server](https://mcp.scenario.com). The content spans images, video, audio, textures,
skyboxes, 3D, and custom models, for games, entertainment, and any creative vertical.

- Format: [Agent Skills](https://agentskills.io).
- Install: `npx skills add scenario-labs/skills`.
- Listing: [skills.sh](https://www.skills.sh/scenario-labs/skills).
- The one exception to the MCP focus: the expert tools, teams of skills that drive DCC software and
  game engines installed on the user's machine (see Expert tools).

## Quick start

- `pnpm install`: once after cloning. It installs the git hooks.
- `pnpm format && pnpm validate`: before committing. `format` rewrites files locally; `validate`
  runs the checks CI runs, `format:check` included.
- `pnpm test`: after touching a script. It runs Python suites with the `python3` on your PATH, so a
  suite with a `tests/<name>/requirements.txt` fails on imports unless those packages are installed.
  Run that suite with its packages:

  ```bash
  uv run --no-project --with-requirements tests/<name>/requirements.txt python -m unittest discover -s tests/<name>
  ```

- `/skills:validate <name>` (`$skills-validate` in Codex): the application test, before merging a
  skill change.

## Layout

```
skills/<name>/SKILL.md                         # name must equal the directory name
skills/<category>/<family>/README.md           # expert tools: the family's build notes
skills/<category>/<family>/<name>/SKILL.md     # expert tools: dcc/ or game-engines/
tests/<name>/                                  # test suite for any script shipped with skill <name>
```

- `scripts/lib/skills.mjs` defines this layout, and every check finds skills through it.
- Skill names are unique repo-wide (`pnpm skill-files` checks). The skills CLI installs every skill
  flat under its name, whatever its folder, and silently keeps only the first of two that share one.
- A supporting file (heavy reference, script) sits next to a SKILL.md only when its content is too
  large to inline.
- Link every supporting file directly from SKILL.md. Agents resolve file references one level deep,
  so a file reached only through another may never be read.
- A skill may carry a `README.md` recording how it was built and why it makes its choices. It is for
  the agents and humans working on the skill, not the agent running it.
  - It is the one supporting file exempt from the link rule (`pnpm skill-files` skips it).
  - Leave it unlinked: linking it spends body words and invites a runtime agent to read maintainer
    notes as instructions, which once made an agent discount a fact it needed.
- Every script shipped with a skill has a test suite in `tests/<name>/` at the repo root, never in
  the skill directory: a published skill directory carries only what an agent needs at runtime. See
  Validation and testing.

## Public content only

This repository is public. Everything in it, commit messages, PR text, and issue text included, uses
publicly shareable language only.

- Reference only public surfaces: scenario.com, app.scenario.com, help.scenario.com (the Scenario
  Knowledge Base), mcp.scenario.com and its `/docs`, docs.scenario.com, the public model catalog,
  and the Scenario for Blender extension's public repository and releases
  (github.com/scenario-labs/blender-plugin) with its `docs/MCP.md` tool reference and handbook at
  blender.scenario.com.
- Never reference internal repositories, source file paths, internal hostnames or environments,
  internal project or team names, customer names, real team/project/API identifiers, credentials,
  pricing internals, or unreleased features.
- Every fact must be verifiable from public surfaces: the tool reference at
  mcp.scenario.com/docs/tools, the Blender extension's `docs/MCP.md` for its local tools, live
  public catalog searches. A fact knowable only from internal sources stays out.
- In doubt, treat it as internal: ask, or drop it. Example: no internal repository naming.

## Authoring contract

CI enforces the mechanical parts on every push and PR: the spec rules through
[`skills-ref validate`](https://github.com/agentskills/agentskills/tree/main/skills-ref) (the Agent
Skills reference validator), plus house-style greps, prettier, cspell, and supporting-file checks.
Run the content checks locally with `pnpm run validate`; commitlint checks commit messages and PR
titles separately. Spec-validate one skill with:

```bash
uvx --from "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref" skills-ref validate skills/<name>
```

### Frontmatter and budget

- Published skill frontmatter: `name`, `description`, and `license: MIT`, nothing else. The spec
  caps `name` at 64 characters and `description` at 1024. The other spec-optional fields
  (`compatibility`, `metadata`, `allowed-tools`) are unused here.
- `name`: lowercase letters, numbers, and hyphens, equal to the directory name.
- `description`: third person, starting "Use when". It names triggering conditions only, never a
  summary of the skill's steps. Under 500 characters, rich in keywords an agent would search for.
- Body: 1000 words is the target; the build fails past 2500 (`pnpm style`). Structure: Overview,
  Quick reference, one excellent worked example, Common mistakes.
- Measure before trimming: `awk '/^---$/{c++; next} c>=2' skills/<name>/SKILL.md | wc -w` is the
  exact number `pnpm style` checks.
- Why a budget: agents load only `name` and `description` at startup. The body enters context only
  when the skill triggers, and then every word competes with the user's task. Spend words on facts
  an agent would otherwise guess wrong, not on prose.
- Why these numbers: after compaction, Claude Code re-attaches the first 5000 tokens of each invoked
  skill from a 25,000-token pool they share. 2500 words is about 4400 tokens, inside that share. The
  cap is the guardrail; the mean protects the pool. The full derivation, and why no line cap, is in
  [docs/decisions.md](docs/decisions.md#word-budget).
- Over budget? Trim first, split last.
  - The body loads on every trigger. A linked file loads only when the agent follows the link.
  - Facts every run needs stay in the body. A linked file holds only situational content: deep
    tables, per-mode detail, scripts.
  - A linked file the agent always reads is a longer body plus a hop.
- Context fan-out: a skill plus the siblings it names is the closest stand-in for one session's
  load, and after compaction they share the re-attach pool. `pnpm style` prints a notice once a
  fan-out approaches it, never a failure, since the total moves when a skill nobody touched grows.
  Answer it by trimming the body or dropping a sibling reference the skill does not need.

### Models and discovery

- Ground every tool and parameter claim in the
  [tool reference](https://mcp.scenario.com/docs/tools).
- Never name a generative model, whoever built it: availability differs per team, and the generation
  named today is superseded within months.
- Name a model id in two cases only:
  - **Platform utility**: Scenario ships exactly one deterministic tool for the operation, and
    nothing third-party does the same job, so discovery would only re-derive the id. These are the
    compositors (`model_scenario-compose-video`, `model_scenario-compose-image`), the timeline tools
    (`model_scenario-video-cut`, `model_scenario-video-split`, `model_scenario-video-concat`,
    `model_scenario-video-to-image-seq`, `model_scenario-image-seq-to-video`), the exact-dimension
    resize tools (`model_scenario-resize-video`, `model_scenario-resize-image`), the audio
    structural tools (`model_scenario-audio-cut`, `model_scenario-audio-split`,
    `model_scenario-audio-extract`), the small image utilities (`model_scenario-grid-maker`,
    `model_scenario-image-slicer`, `model_scenario-padding-remover`), and the
    `model_scenario-postprocessing-*` effects. Say in the body why the id is fixed, so the next
    author does not read it as an oversight.
  - **Dedicated member**: a skill built around one first-party tool model names its id outright
    (scenario-caption-studio runs `model_scenario-caption-studio`). Running that member is the
    skill's whole purpose, so a discovery step would only re-derive the subject. The contested-lane
    test below governs skills reaching the capability, never the skill dedicated to the member.
- Being Scenario's own is necessary, not sufficient:
  - Check the provider first. `modelProvider: "Scenario"` on a `tool`-tagged model is the marker,
    and an upstream vendor there means the operation is a market: the FLUX upscale variants report
    BFL, and upscaling has competitors.
  - Then confirm nothing third-party does the job. These lanes are Scenario-built and still
    contested:
    - reframing and expanding: `model_scenario-smart-reframe` and `model_scenario-gemini-reframe`,
      against Photoroom Expand and Uncrop;
    - splitting an image into layers: `model_scenario-image-layers-extractor`, against Ideogram and
      Seedream;
    - transcription: `model_scenario-audio-to-text`, against Gemini Transcribe;
    - subtitles: `model_scenario-caption-studio` and `model_scenario-video-subtitles`, two Scenario
      tools for one job, so the lane fails the test internally;
    - segmentation: `model_scenario-detection` is unique for ControlNet preprocessor maps, but SAM
      covers object masks.
  - Ids split across `model_scenario-` and `model_sc-`: confirm one against the catalog, never
    reconstruct it.
- Discovery:
  - `recommend` when the skill needs a capability. It takes the capability plus the user's own
    words, ranks members on measured cost and latency, names the purpose-built pick, and warns when
    a generative model is the wrong instrument.
  - `search` when the member is already known by name or is private. It ranks by keyword, and its
    `filters` hold no capability key, so a capability-worded query fails: `query="image edit"`
    returned 318 hits with nothing to choose between them.
  - Lane tables carry capabilities (`img2video`), not query strings.
  - `dry_run` still prices the exact payload: `recommend`'s figures are modeled, and one quoted 48.2
    CU where 55 was billed.
  - Leave the `next_step` discipline to the `scenario` skill and reference it.

### Scope and surface

- Model-family skills group one provider family each and carry no version number
  (`scenario-seedance`, never `scenario-seedance-2-5`). A skill name is permanent (installs, README
  rows, `skills.sh.json` groupings, sibling cross-references), while generations churn every few
  months: versions are data, not identity.
  - Version and generation keywords go in the `description` (the seedance one carries "Seedance 2.5
    and 2.0"), so a search for a specific version still triggers the skill.
  - The body teaches per-member differences by reading caps off `model_schema_get`, with
    authoring-time numbers hedged as such.
  - Split a family only when coexisting members target different output types, never by version.
- One skill, one output type: image, video, 3d, or audio.
  - A brand spanning types splits by surface (`scenario-grok-imagine-image` and
    `scenario-grok-imagine-video`, `scenario-luma-image` and `scenario-luma-video`), leaving the
    other type's members to the sibling skill.
  - An intermediate asset of another type inside one pipeline (a skybox still on the way to a splat)
    does not change the skill's type.
- MCP is the surface a skill teaches.
  - Every step the agent performs itself goes through an MCP tool, even one reachable another way.
    Never route it through the Scenario REST API, the official SDK, or a CLI where an MCP tool
    exists.
  - A capability the MCP server does not expose is a gap to report, not one to bridge with an API
    call.
  - Fetching a URL an MCP tool already returned (`asset_download` then `curl -L`) is not an API
    call.
- Scripts are the exception.
  - A script under `skills/<name>/scripts/` may use the official public SDK where it is the better
    tool, whether a maintainer runs it or a skill has an agent run it.
  - The SDK must not become the route the body teaches. Keep the agent's own steps on MCP, and have
    the script's link in SKILL.md say what it does and who runs it, so no agent reads it as the
    steps to follow.
  - `pnpm style` prints a notice, never a failure, when skill markdown mentions the SDK, to prompt
    that judgment.
- Cross-reference the `scenario` skill for connection setup; never repeat it.
- A skill that names a sibling skill carries the sibling-install invitation, byte-identical across
  skills (copy it from any SKILL.md: "If a sibling skill named here is missing from your available
  skills, ask the user to install it..."). Neither the Agent Skills spec nor the skills CLI resolves
  dependencies (issue #49 tracks the upstream work), so this sentence is the mechanism.
- No disclosure marks: a skill never tells an agent to burn AI-disclosure marks, badges, or
  compliance overlays into generated content, by default or as an option. The skills serve
  professionals who own their distribution compliance; the pipeline does not decide it for them.

## Writing

These rules cover skill bodies and references, scripts, commit messages, PR text, and replies.

- Lead with the instruction or the fact. No preamble, no restating the question, no closing summary.
- One fact per sentence, about 20 words. Past 40, split it or make a list.
- Three or more parallel items make a list. Prefer short bullets to a long sentence.
- Keep the words that carry a condition: only, unless, never, before, after. Terse is not
  telegraphic: drop "only when" and an agent applies the rule everywhere.
- Give a reason only when it prevents a mistake, in one clause. The debate behind a rule goes in the
  skill's `README.md`, in [docs/decisions.md](docs/decisions.md) for this file, or in the PR, not in
  the body.
- Hedge only a fact that changes, like an authoring-time number. State the rest flatly.
- Use one name per thing, from the glossary below.
- Say it once, then stop: noise is paid on every future read. Never spend a paragraph where a clause
  serves, and link to a rule in this file rather than restate it.
- Before cutting a passage as a duplicate, compare the two item by item. Topic overlap is not
  content overlap, and nothing tests whether a fact that used to be present still is.
- A comment records only what the code cannot say: a constraint, a trap that already bit someone, a
  why not visible in the lines below. Never narrate the next line. A stale comment costs more than a
  missing one.
- No em dashes, ever: use a comma, a colon, parentheses, or two sentences.
- No marketing language.
- Agent-agnostic wording: assume no specific agent outside clearly labeled setup snippets.
- American spelling (color, behavior, center, modeling, optimize). cspell's en-US dictionary accepts
  some British forms, so those are forbidden words, prefixed with `!`, at the top of
  `project-words.txt`. Add a form there when one slips through.
- Tables hold short lookups: a capability against its lane, a parameter against its range. A row
  never wraps (a line break ends it), and prettier pads every row to the widest cell. So one
  sentence in a cell makes every line long, and widening it rewrites every row in the diff. A cell
  that needs a sentence becomes a list item: `- **term**: sentence`.

`pnpm style` prints notices, never failures, for staged skill markdown:

- a table cell past 200 characters, anywhere in a staged file, so old tables convert when next
  edited;
- a sentence past 40 words, on added lines only;
- "workflow" on added lines outside the workflow skills.

Before, one 84-word sentence:

> A reference-audio field is guidance the prompt has to claim: what it conditions (timing and energy
> on one family, a voice on another) and whether it rides alone or needs an image or video reference
> beside it are the family skill's contract, but on every member a track passed silently beside a
> character reference is easily ignored, so the prompt says what the track is for ("the reference
> audio is her own voice, lip-synced" for speech; the beat the cuts land on for music).

After, the same facts:

- Reference audio is guidance the prompt has to claim.
- The family skill says what it conditions (timing and energy, or a voice) and whether it needs an
  image or video reference beside it.
- On every member, a track passed silently beside a character reference is easily ignored.
- So the prompt names the track's job: "the reference audio is her own voice, lip-synced" for
  speech, the beat the cuts land on for music.

### Glossary

| Term          | Means                                                              | Not                              |
| ------------- | ------------------------------------------------------------------ | -------------------------------- |
| skill         | A folder holding a `SKILL.md`, installed by the skills CLI         | workflow, recipe, guide, plugin  |
| sibling skill | Another skill a skill names                                        | dependency (nothing resolves it) |
| workflow      | A Scenario workflow: a node graph run with `workflow_run`          | a skill, or the steps it teaches |
| tool          | An MCP tool: `model_run`, `jobs_wait`                              | a tool model                     |
| tool model    | A `tool`-tagged catalog model, run with `model_run`                | a tool                           |
| member        | One catalog model within a family or capability                    |                                  |
| job           | One run of `model_run` or `workflow_run`, awaited with `jobs_wait` | task, request                    |
| asset         | A file stored in Scenario: an upload or a generated output         | image (when the type varies)     |
| plugin        | One grouping in `.claude-plugin/marketplace.json`                  | a skill                          |

GitHub Actions files under `.github/workflows/` keep their name. For what a skill teaches, say
steps, procedure, or pipeline.

## Expert tools

`skills/dcc/` (ZBrush, Blender, Maya) and `skills/game-engines/` (Unreal Engine, Unity, Godot) hold
teams of skills, ported from Emmanuel de Maistre's expert-skill repositories. They drive
applications installed on the user's machine through their Python, bridges, and command lines.

- Each family is a lead `scenario-<app>-expert` plus specialists named `scenario-<app>-<topic>`. The
  specialists import the lead's `scripts/`, so a family installs as one set.
- The family folder's `README.md` records how the family was built and how far it was verified. It
  sits outside every skill folder, so no install ships it. It carries no version; this repository's
  releases do.

The authoring contract applies with these differences, because the tier drives an application rather
than the MCP server:

- The MCP rules (MCP as the surface, `recommend` discovery, model ids) do not apply. The rest does,
  including the frontmatter, the 2500-word cap, house style, public content only, and the
  sibling-install sentence.
- Descriptions follow the spec's 1024-character cap, not the 500-character target. Bodies run near
  the cap, not the 1000-word target. Both are the author's choice, kept until a live run shows what
  to trim.
- Shipped scripts need no suite of their own under `tests/<name>/`: the behavior suites live in the
  author's build project and run against the application.
  - One suite per family, `tests/scenario-<app>-expert/` (the same file in each), imports every
    script with system Python and checks that each skill name a script uses to find the lead's
    `scripts/` exists. `pnpm skill-files` still parses every Python script.
  - Godot is the exception that runs the application: its toolkit branches per OS (locks, the
    process table, copies). `tests/scenario-godot-expert/test_toolkit_live.py` runs against a real
    Godot on Linux, macOS, and Windows in `.github/workflows/godot.yml` whenever a Godot script
    changes. Without Godot installed its live tests skip; its lock and GUI-check tests still run in
    `pnpm test`.
  - Unity's `tests/scenario-unity-expert/test_toolkit_offline.py` needs no application: it runs the
    toolkit's lock probe, process-table parsing, and signal handling in `pnpm test`.
    `.github/workflows/unity.yml` runs it on macOS, the OS the toolkit targets, whenever a Unity
    script changes.
- A link to a subfolder (`scripts/AgentKit/`, never `scripts/` itself) covers the files under it:
  these skills ship code trees an agent copies into a project whole.
- cspell skips code, fenced and inline, and YouTube video ids. Prose is checked as everywhere else
  (`cspell.json` overrides).
- Each family is one `skills.sh.json` grouping titled "Expert tools: <app>". Every expert grouping
  comes after every core grouping, so the expert tools stay at the bottom of skills.sh and the
  installer picker (`pnpm groupings` enforces both). A new core grouping goes above them, which
  renumbers their plugin ids.
- The application test protocol grades MCP plans. For an expert tool, grade the plan against the
  lead skill's execution channels and the application's own documentation instead.

## Authoring aids

- Two of Anthropic's skills are vendored as dev skills in `.agents/skills/`, symlinked from
  `.claude/skills/`, so agents working in a clone pick them up automatically:
  - [skill-creator](https://www.skills.sh/anthropics/skills/skill-creator) (Apache-2.0, from
    anthropics/skills);
  - [skill-development](https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev/skills/skill-development)
    (MIT per the plugin-dev README, from anthropics/claude-code).
- `skills-lock.json` records each source and hash; refresh with `npx skills update`. Their entries
  there exclude them from CLI discovery. Agent directories alone do not, since the CLI also scans
  `.agents/skills/` and `.claude/skills/`.
- Where their generic guidance and this file disagree, this file wins.

Repository commands:

- They live in regular `.agents/skills/skills-*/SKILL.md` files. Codex exposes `$skills-pr-handle`
  and `$skills-validate`; the [contributor guide](CONTRIBUTING.md#shared-agent-commands) maps their
  Claude names.
- Claude command paths under `.claude/commands/` are relative symlinks to those files. Edit the
  canonical files, then run `pnpm sync:agent-commands` to create or repair links (`pnpm format` runs
  it too).
- Explicit-only commands carry `disable-model-invocation: true` and `argument-hint` in shared
  frontmatter for Claude, plus `allow_implicit_invocation: false` in `agents/openai.yaml` for Codex.
  Codex CLI 0.154.0 was verified to load both commands with those Claude fields present.
- These maintainer skills keep their command structure and stay outside the published `skills/`
  catalog.
- Set `metadata.internal: true` (a YAML boolean) in each command's frontmatter to exclude it from
  normal CLI discovery and bulk installs. Explicit skill requests or `INSTALL_INTERNAL_SKILLS=1` can
  still include it. The flag does not remove existing skills.sh listings: request removal from the
  maintainers (see [vercel-labs/skills#1578](https://github.com/vercel-labs/skills/issues/1578)).
- Add new command mappings in `scripts/sync-agent-commands.mjs`.
- `pnpm validate` checks command metadata, argument hints, invocation guards, and symlinks. Strict
  spec validation covers only published `skills/*/`, because the spec rejects Claude frontmatter
  extensions.
- `pnpm test` runs the command, plugin-manifest, style, and readme regression suites as well as the
  shipped-script suites.

## Repo tooling

### Setup

- After cloning, run `pnpm install`. It installs commitlint, cspell, prettier, and the husky git
  hooks.
- In Claude Code, a SessionStart hook (`.claude/hooks/ensure-husky.sh`) runs it when the hooks are
  missing.
- In Codex, run `pnpm install --frozen-lockfile` if `node_modules` is missing or
  `git config --local core.hooksPath` is not `.husky/_`. The Claude Code hook does not run there.

### Commits and checks

- Commit messages and PR titles follow Conventional Commits. commitlint (`commitlint.config.js`)
  enforces them in three places: the husky `commit-msg` hook, a commitlint job on PR commits, and
  the `pr-name-linter` workflow on the PR title.
- Valid scopes: the skill directory names (derived automatically from `skills/`) plus `skills`,
  `agents`, `ci`, `deps`, `docs`, and `tooling`.
- The husky `pre-commit` hook runs, in order:
  1. `pnpm words:sort`: sorts `project-words.txt` in place, re-staging it only when it is part of
     the commit.
  2. `pnpm manifest`: regenerates `.claude-plugin/marketplace.json` from `skills.sh.json` and the
     skill folders, and stages the copy rendered from their staged versions, so unstaged moves and
     edits never reach the commit.
  3. `pnpm validate`: the checks below, which CI runs as separate steps.
- What `pnpm validate` runs:
  - **`pnpm style`**: house style, the body budget, and the fan-out, table-cell, sentence-length,
    and wording notices.
  - **`pnpm format:check`**: prettier.
  - **`pnpm sync:agent-commands:check`**: the command links and metadata (see Authoring aids).
  - **`pnpm skill-files`**: supporting files next to a SKILL.md are linked and runnable, a skill's
    own `README.md` excepted.
  - **`pnpm lint:py`**: ruff's pyflakes rules over every Python script, configured in `ruff.toml`,
    the vendored dev skills excluded.
  - **`pnpm groupings`**: every skill sits in a `skills.sh.json` grouping, every listed skill
    exists, and the file satisfies the published skills.sh schema.
  - **`pnpm manifest:check`**: the plugin marketplace manifest matches `skills.sh.json`.
  - **`pnpm readme`**: the README Skills section mirrors `skills.sh.json`, one subsection per
    grouping in the same order with the same title, description, and rows, and every skill has
    exactly one non-stale row. It also checks the install commands (see below).
  - **`pnpm words:check`**: `project-words.txt` is sorted and deduplicated.
  - **`pnpm spell`**: cspell.
  - **`pnpm spec`**: spec validation.
- Each command is defined once in `package.json`. Most run a script in `scripts/`; `format` and
  `format:check` invoke prettier directly.
- A commit hook runs with git's location variables (`GIT_DIR`, `GIT_INDEX_FILE`, and the rest)
  pointing at this repository, and hook steps read the index through them. Never unset them for the
  whole hook. A tool a step runs that issues its own git commands must run without them, as
  `scripts/validate-skills.sh` does for uvx: from a linked worktree, uv's inherited git commands
  reset the worktree's branch and set `core.bare` on this repository.

### Formatting and spelling

- prettier enforces formatting with the config committed in `.prettierrc.json`, so the CLI and the
  VS Code extension agree. `pnpm format` rewrites the repo; `pnpm format:check` only verifies.
- Coverage: everything prettier can parse (markdown, JSON, YAML, JS/TS), plus shell scripts via
  `prettier-plugin-sh`, which formats with mvdan-sh, the engine behind shfmt. `.prettierignore`
  excludes generated files and the vendored dev skills.
- Markdown prose wraps at 100 columns (`proseWrap: "always"`), so a GitHub diff shows the changed
  lines rather than one paragraph-long line. Tables and code never wrap.
- SKILL.md files and `.claude/` agents and commands also set `embeddedLanguageFormatting: "off"`. It
  is the one setting that stops prettier folding a frontmatter `description` across lines, so the
  description stays on the one line `pnpm style` reads and every skill has shipped with. Their
  fenced code is therefore left as written.
- A merged commit that only reformats, like the one that introduced the wrap, goes in
  `.git-blame-ignore-revs` so blame skips it.
- After authoring markdown, run `pnpm format` before `pnpm validate`: prettier reflows prose and
  rewrites tables, so `format:check` rejects correct hand-written markdown.
- Add legitimate project terms to `project-words.txt`; never disable cspell inline. The file stays
  sorted (byte order, deduplicated): the pre-commit hook sorts it, and `pnpm words:sort` does it by
  hand.

### skills.sh and install commands

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
  - Plugin names carry a two-digit position prefix (`01.-getting-started`, shown as "01. Getting
    Started"), because the picker sorts group names alphabetically. The prefix makes it follow the
    `skills.sh.json` order, so inserting or merging a grouping renumbers the plugin ids on
    regeneration.
  - The manifest also makes the repo a Claude Code plugin marketplace, one plugin per grouping.
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
  - After adding a core skill, add it to the role it serves (as an outcome bullet when it leads one)
    and to any goal it leads or serves, each with any sibling it names that the command lacks. Then
    update the counts.
  - A skills.sh pack URL (`npx skills add https://skills.sh/p/<id>`) is the only install that
    preselects a set. Packs are created manually on skills.sh behind a Vercel sign-in (no CLI or
    API); pack links belong in README.md's Install section.

### Pull requests and releases

- PRs are squash-merged, so the PR title becomes the commit header on `main`. Shared Scenario PR
  skills, vendored like the Anthropic dev skills (pinned in `skills-lock.json`, never edited here,
  refreshed with `npx skills update`), handle the routine:
  - `/pr-squash-message` drafts the squash message;
  - `/pr-summary` refreshes the PR body;
  - `/pr-handle-comments` answers review threads.
- `/skills:validate <name>` (`.claude/commands/skills/`) runs the application test for one skill and
  reports it to the PR; see Validation and testing.
- release-please cuts releases (`.github/workflows/release-please.yml`, configured in
  `release-please-config.json`).
  - feat, fix, docs, perf, and revert commits squash-merged to `main` land in the next release,
    which release-please stages as an open release PR.
  - Every other Conventional Commits type is invisible to the changelog: chore and ci by design, but
    also refactor, test, style, and build. A release window holding only those cuts no release at
    all, so a change to shipped skill content must be typed feat, fix, or docs.
  - release-please never lets you pick the version. To force an exact one, dispatch the workflow by
    hand: `gh workflow run release-please.yml --ref main -f release_as=X.Y.Z`, which must be higher
    than `.release-please-manifest.json`. Never push an empty `Release-As` commit to `main`.
  - The dispatch runs the release-please CLI (pinned in `package.json` to the version the action
    bundles), not the action: release-please-action v5 silently drops `release-as` in manifest mode,
    which this repo's `release-please-config.json` selects.
  - The override is one-shot: the next push to `main` re-derives the version and rewrites the
    release PR, so merge it promptly. A pin that survives pushes is `"release-as"` in
    `release-please-config.json`, through a PR, removed once released.
  - Merging the release PR tags `skills-vX.Y.Z`, titles the GitHub release `skills: vX.Y.Z`,
    rewrites `CHANGELOG.md`, `version.txt`, and `.release-please-manifest.json`, and publishes the
    GitHub release.
  - `.github/workflows/publish-changelog.yml` then posts the notes to the public changelog at
    [scenario.com/changelog](https://www.scenario.com/changelog). It hangs off the
    `release: published` event, not the release-please run, because release-please reports a created
    release exactly once. Re-run a failed post from the Actions tab, or dispatch it by tag.
  - Those three files are release-please's alone, never hand-edited, like the marketplace manifest.
    That is why `CHANGELOG.md` sits in `.prettierignore`, where it also keeps prettier from
    rewriting release-please's `*` bullets. It also sits in cspell's ignorePaths, as a guard should
    the spell-check globs widen; `scripts/check-spelling.sh` does not reach it today.
  - In `.release-please-manifest.json`, exactly `0.0.0` is the sentinel for "no release yet": it
    makes `initial-version` and the root `bootstrap-sha` apply. Editing it to match
    `initial-version` looks like a sync fix and silently changes the first release number.
  - The release PR title (`chore: release skills X.Y.Z`) passes commitlint because an omitted scope
    only warns.
  - The `skills-` tag prefix matches the sibling repositories' convention. It is set by hand as
    `component` plus `include-component-in-tag` in `release-please-config.json`, because
    `release-type: simple` derives none, unlike `release-type: node`, which takes one from the
    `package.json` name.
  - Changing the tag format orphans release-please from its own history unless the existing tag and
    its GitHub release move with it. The next changelog then replays every commit since
    `bootstrap-sha`.

### CI and review agents

- Every `uses:` in `.github/workflows/` names a full commit SHA with the release in a trailing
  comment (`actions/checkout@<sha> # v7.0.1`), never a tag: a tag is a pointer its publisher can
  move.
- Dependabot (`.github/dependabot.yml`) proposes one grouped `ci(deps)` PR a week, for releases at
  least seven days old. It skips release-please-action, which moves by hand together with the
  `release-please` pin in `package.json`.
- The `skill-files-reviewer` agent (`.claude/agents/`) reviews supporting files added or changed
  next to a SKILL.md: justified, linked from SKILL.md, runnable, MCP for the agent's own steps,
  public content only, house style.
- The `skill-tester` agent in the same directory is the clean-room runner `/skills:validate` spawns
  when a separate process cannot reach the MCP server. It is not for ordinary work.

## Validation and testing

- `skills-ref validate` must pass for every published skill before any commit: the pre-commit hook
  and CI both run it via `pnpm spec`.
- Every script shipped with a skill has a test suite in `tests/<name>/` (see Layout). Python scripts
  use stdlib `unittest` (files named `test_*.py`), TypeScript scripts vitest (files named
  `*.test.ts`).
- `pnpm test` runs every suite and fails when a shipped script has no suite; CI runs it on every
  push and PR. It is not in the pre-commit hook, since suites may need system tools such as ffmpeg,
  so run it by hand when touching a script. A `tests/<name>/requirements.txt` declares extra Python
  dependencies for CI.
- Before merging a new or changed skill, run the application test below. Mechanical validation
  checks the format; the application test checks whether the skill actually teaches.
- `/skills:validate <name>` (`.claude/commands/skills/`) drives that test:
  - it writes a use case for the skill;
  - installs the working-tree copy into a clean-room agent with no repository context;
  - runs it end to end against the real MCP server, in a team and project you choose;
  - grades the transcript;
  - posts the report to the current branch's PR, or asks what to do with it when there is none.
  - `--plan-only` runs the zero-cost planning variant below instead of live generation.

Rules learned from past runs:

- Catalog-only MCP tools (`collection_*`, `asset_quality_gate_run`) take their arguments under
  `parameters`, not `arguments`, in `scenario_tool_execute_read/write`. The wrong key fails with a
  misleading "team_id and project_id are required".
- `usage` accepts inclusive date bounds and defaults to the last 31 days when both dates are
  omitted. Set explicit dates and scope for attribution.
  - Overall consumed CU is `totals.totalCU` (the sum of `consumption.value`). Model CU is generation
    activity and can differ. Both are already after discounts.
  - Never substitute job billing snapshots, or a sum of your own calls, for consumed CU.
- Verify a delivered video by sweeping it into contact sheets (`ffmpeg -vf "fps=2"`), not one frame
  per shot: a defect that fades in mid-shot passes a spot check.
- Before a paid run, pre-register what each outcome would mean, so conclusions are not fitted to
  results afterwards.
- Stop hunting a mechanism after roughly two inconclusive controlled runs: ship the rule that holds
  regardless and record the open question.

### Application test protocol

1. Spawn a fresh agent with no conversation history. Give it only:
   - a framing line ("you are an agent connected to the Scenario MCP server; the skill document
     below is installed");
   - the SKILL.md under test, plus the `scenario` SKILL.md when testing any other skill, since real
     installs ship both;
   - one realistic task.
2. Ask for a numbered tool-call plan with exact tool names and argument shapes. Planning only: the
   agent must not execute tools, browse, or consult anything beyond the provided documents, and must
   flag uncertainty instead of guessing.
3. Pick a task that forces the skill's non-obvious facts (upload flow, job-wait re-calls, dry runs,
   launch semantics), not one answerable with generic MCP intuition.
4. Grade the plan against the [tool reference](https://mcp.scenario.com/docs/tools), fetched fresh
   rather than recalled:
   - Every tool and parameter named in the plan exists. One invented name is a fail.
   - Correct flow: the loop the skill under test teaches. For a generation task: discovery,
     `model_schema_get`, `model_run`, then `jobs_wait` re-called with `pending_job_ids` for any job
     still running (fast models return complete inline; `job_get` polling is never correct), then
     `asset_display` / `asset_download`.
   - Generative model ids come from a `recommend` or `search` step, never asserted as constants. A
     named first-party tool model is not a violation when it is a sanctioned singleton or the member
     the skill under test is dedicated to; a named generative model always is.
   - The agent's own steps stay on MCP. A plan that reaches for the REST API, the SDK, or a CLI
     where an MCP tool exists fails, and so does one that invents an API call to cover a capability
     MCP lacks. Running a script the skill ships does not fail, whatever that script uses
     internally, and neither does saving a URL an MCP tool returned.
   - The task's trap steps are handled the way the skill teaches.
   - Anything asserted that appears in neither the SKILL.md nor the tool reference counts as a
     guess, even when it happens to be right.
5. A failure is a defect in the skill text. Fix the missing or ambiguous sentence, then re-run with
   a new fresh agent: a failed agent is contaminated by its own mistake.
6. Baseline probe, once per new skill (not per edit): run the same task with no skill installed, to
   confirm the skill earns its context cost.

## Codex commit attribution

- For Codex-assisted commits and prepared squash messages, add a co-author trailer naming the model
  and, when verified, the reasoning effort and speed tier:
  `Co-authored-by: Codex <model> <effort> <tier> <noreply@openai.com>`. Example:
  `Co-authored-by: Codex gpt-6-astra low fast <noreply@openai.com>`.
- Use the contributing session's actual settings, not repository defaults or the example.
- Omit unknown fields rather than guess. If the model is unavailable, use
  `Co-authored-by: Codex <noreply@openai.com>`.
- Preserve the human author and existing contributor trailers, and carry these trailers into the
  final squash message so attribution survives squash merges.

## Conventions

- PRs target `main`. Commit types and squash merges: see Repo tooling.
- `CLAUDE.md` is a symlink to this file, so Claude Code and Codex read the same conventions.
- Shared Codex defaults live in `.codex/config.toml`; model selection stays in user configuration.
