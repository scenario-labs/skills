# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

## What this repo is

Public Agent Skills for [Scenario](https://scenario.com): procedural knowledge that teaches AI coding agents how to create production-ready content (images, video, audio, textures, skyboxes, 3D, custom models) through the [Scenario MCP server](https://mcp.scenario.com). The workflows serve games, entertainment, and any creative vertical. Skills follow the [Agent Skills](https://agentskills.io) format, install with `npx skills add scenario-labs/skills`, and are listed on [skills.sh](https://www.skills.sh/scenario-labs/skills).

## Layout

```
skills/<name>/SKILL.md   # name must equal the directory name
tests/<name>/            # test suite for any script shipped with skill <name>
```

Supporting files (heavy references, scripts) may sit next to a SKILL.md only when the content is too large to inline. Link supporting files directly from SKILL.md: agents resolve file references one level deep, so a reference chained through another supporting file may never be read.

Every script shipped with a skill has a test suite in `tests/<name>/` at the repo root, never inside the skill directory: published skill directories carry only what an agent needs at runtime. Python scripts are tested with stdlib `unittest`; TypeScript scripts with vitest. See Validation and testing.

## Public content only

This repository is public. Everything in it, including commit messages, PR text, and issue text, must be limited to publicly shareable language:

- Reference only public surfaces: scenario.com, app.scenario.com, help.scenario.com (the Scenario Knowledge Base), mcp.scenario.com and its `/docs`, docs.scenario.com, and the public model catalog.
- Never reference internal repositories, source file paths, internal hostnames or environments, internal project or team names, customer names, real team/project/API identifiers, credentials, pricing internals, or unreleased features.
- Facts must be verifiable from public surfaces (the tool reference at mcp.scenario.com/docs/tools, live public catalog searches). If a fact is only knowable from internal sources, leave it out.
- When in doubt, treat it as internal: ask, or drop it. Example: no internal repository naming.

## Authoring contract

CI enforces the mechanical parts of this contract on every push and PR: [`skills-ref validate`](https://github.com/agentskills/agentskills/tree/main/skills-ref) (the Agent Skills reference validator) for the spec rules, plus house-style greps, formatting (prettier), spell checking (cspell), and supporting-file checks. Run the content checks locally with `pnpm run validate` (commit messages and PR titles are linted separately with commitlint), or spec-validate a single skill with:

```bash
uvx --from "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref" skills-ref validate skills/<name>
```

- Frontmatter: `name`, `description`, and `license: MIT`, nothing else. The spec caps `name` at 64 characters and `description` at 1024; the other spec-optional fields (`compatibility`, `metadata`, `allowed-tools`) are not used in this repo.
- `name`: lowercase letters, numbers, and hyphens; must equal the directory name.
- `description`: third person, starts with "Use when", describes triggering conditions only (never a summary of the skill's workflow), under 500 characters, rich in keywords an agent would search for.
- Body: 600-900 words is the house target; the build fails past 1400 words or 500 body lines (`pnpm style`). Structure: Overview, Quick reference, one excellent worked example, Common mistakes.
- Why the budget: agents load only `name` and `description` at startup; the body enters context only when the skill triggers, and then every word competes with the user's task. Spend words on facts an agent would otherwise guess wrong, not on prose.
- Where the numbers come from, so they are not re-litigated: nothing outside this repo caps a body. The spec says the body has "no format restrictions" and `skills-ref` validates a 200,000-word body clean; Anthropic advises "under 500 lines" and the spec "< 5000 tokens", both recommendations, and the widely repeated "5000 words" is a debugging remedy for a skill already behaving badly, not a budget. The house target is tighter than the advice for a reason specific to this repo: nearly every skill names siblings, so multi-skill sessions are the design, and Claude Code re-attaches only the first 5000 tokens of each skill after compaction from a 25,000-token pool shared across them. The caps are the guardrail, the target is the craft, and a target that describes almost no skill in the repo is a target to fix rather than a rule to golf against.
- Body over budget? Trim before you split. The body loads on every trigger; a supporting file loads only when the agent follows its link, so facts every run needs stay in the body, and a linked reference holds only content that is genuinely situational (deep reference tables, per-mode detail, scripts). Splitting to dodge the budget adds a hop to the same context cost: a reference the agent must always read is a longer body in disguise.
- Ground every tool and parameter claim in the [tool reference](https://mcp.scenario.com/docs/tools). Never present a model ID as a constant: model availability differs per team, so teach discovery via `search`.
- Model-family skills group one provider family per skill and are named without version numbers (`scenario-seedance`, never `scenario-seedance-2-5`). A skill name is a permanent identifier (installs, README rows, `skills.sh.json` groupings, cross-references from sibling skills) while model generations churn every few months: a versioned name goes stale the day the next generation ships and forces either a breaking rename or a pile of near-duplicate skills competing for the same trigger. It is the model-ID rule one level up: versions are data, not identity. Version and generation keywords belong in the `description` (the seedance description carries "Seedance 2.5 and 2.0") so an agent searching a specific version still triggers the skill, and the body teaches per-member differences by reading caps off `model_schema_get` with authoring-time numbers hedged as such. Split a family only when coexisting members target different output types, never by version.
- One skill, one output type: image, video, 3d, or audio. When a brand spans types, split by surface (`scenario-grok-imagine-image` and `scenario-grok-imagine-video`, `scenario-luma-image` and `scenario-luma-video`) and leave the other type's members to the sibling skill. An intermediate asset of another type inside one pipeline (a skybox still on the way to a splat) does not change the skill's type.
- MCP is the surface a skill teaches. Every step the body has an agent perform itself goes through an MCP tool, including the ones reachable another way: do not route the agent through the Scenario REST API, the official SDK, or a CLI where an MCP tool exists. A capability the MCP server does not expose is a gap worth reporting rather than quietly bridging with an API call. Fetching a URL an MCP tool already returned (`asset_download` then `curl -L`) is not an API call and stays fine.
- Scripts are the exception. A script under `skills/<name>/scripts/` may use the official public SDK wherever the SDK is the better tool, whether a maintainer runs it or a skill has an agent run it. What the SDK must not become is the route the body teaches: keep the agent's own steps on MCP, and have the script's link in SKILL.md say what it does and who runs it, so no agent reads it as the workflow. `pnpm style` prints a notice when skill markdown mentions the SDK; it prompts that judgement call and never fails the build.
- Cross-reference the `scenario` skill for connection setup instead of repeating it.
- Every skill that names a sibling skill also carries the sibling-install invitation, byte-identical across skills (copy it from any SKILL.md: "If a sibling skill named here is missing from your available skills, ask the user to install it..."). Neither the Agent Skills spec nor the skills CLI resolves dependencies (issue #49 tracks the upstream work), so this sentence is the mechanism.
- No disclosure marks: skills never instruct an agent to burn AI-disclosure marks, badges, or compliance overlays into generated content, by default or as an option. The skills serve professionals who own their distribution compliance; the creative pipeline does not make that decision for them.
- Style: no em dashes, ever (use a comma, a colon, parentheses, or two sentences). No marketing language. Agent-agnostic wording: do not assume a specific agent outside clearly labeled setup snippets.

## Authoring aids

Anthropic's [skill-creator](https://www.skills.sh/anthropics/skills/skill-creator) (Apache-2.0) is vendored as a dev skill in `.claude/skills/` and `.agents/skills/`, so agents working in a clone of this repo pick it up automatically. `skills-lock.json` records its source and hash; refresh with `npx skills update`. Vendored dev skills live only in agent directories and are never part of the published set: the skills CLI and skills.sh surface only `skills/` (verified against this repo). Where skill-creator's generic guidance and this file disagree, this file wins.

## Repo tooling

One-time setup after cloning: `pnpm install`. It installs commitlint, cspell, prettier, and the husky git hooks. A Claude Code SessionStart hook (`.claude/hooks/ensure-husky.sh`) runs it automatically when the hooks are missing, so agent sessions always commit with the hooks active.

- Commit messages and PR titles follow Conventional Commits, enforced by commitlint (`commitlint.config.js`) in three places: the husky `commit-msg` hook, a commitlint job on PR commits, and the `pr-name-linter` workflow on the PR title. Valid scopes are the skill directory names (derived automatically from `skills/`) plus `skills`, `agents`, `ci`, `deps`, `docs`, and `tooling`.
- The husky `pre-commit` hook runs `pnpm words:sort` (sorts `project-words.txt` in place, re-staging it only when it is part of the commit), then `pnpm validate`, the same checks CI runs as separate steps: `pnpm style` (house style), `pnpm format:check` (prettier), `pnpm skill-files` (supporting files next to a SKILL.md are linked and runnable), `pnpm groupings` (every skill sits in a `skills.sh.json` grouping, every listed skill exists, and the file satisfies the published skills.sh schema), `pnpm readme` (every skill has a row in README.md's Skills table, no stale or duplicate rows), `pnpm words:check` (`project-words.txt` is sorted and deduplicated), `pnpm spell` (cspell), and `pnpm spec` (spec validation). Each is defined once in `package.json`; most run a script in `scripts/`, while `format` and `format:check` invoke prettier directly.
- `pnpm groupings` proves `skills.sh.json` is valid, not that skills.sh has applied it. Per the [customize docs](https://www.skills.sh/docs/customize), the directory reads the file only after its telemetry has seen the repository (in practice, after a fresh `npx skills add scenario-labs/skills` run with telemetry enabled), and repo pages are cached, so both the grouping and the skill content on [the repo page](https://www.skills.sh/scenario-labs/skills) can trail `main`. If a valid file is still ignored after a fresh install and a cache refresh, report it at [vercel-labs/skills](https://github.com/vercel-labs/skills/issues) with the config, the affected slugs, and the install timestamp.
- `npx skills add scenario-labs/skills` opens a picker with nothing preselected; a skills.sh pack URL (`npx skills add https://skills.sh/p/<id>`) is the only install that preselects a set. Packs are created manually on skills.sh behind a Vercel sign-in (no CLI or API); pack links belong in README.md's Install section.
- Known bug: committing from a git worktree fails the pre-commit hook at `pnpm spec`. Git exports `GIT_DIR` to hooks, uv's git subprocesses inherit it, and spec validation resolves the agentskills repo to this repo's own HEAD, erroring with "has no subdirectory `skills-ref`" (the upstream repo is fine). Until `GIT_DIR`, `GIT_WORK_TREE`, and `GIT_INDEX_FILE` are unset at the top of `.husky/pre-commit`, run `pnpm validate` from the worktree in a shell without those variables, then commit with `--no-verify`.
- Formatting is enforced by prettier with the config committed in `.prettierrc.json`, so the CLI and the VS Code extension agree. `pnpm format` rewrites the repo; `pnpm format:check` only verifies. Coverage is everything prettier can parse (markdown, JSON, YAML, JS/TS) plus shell scripts via `prettier-plugin-sh`, which formats with mvdan-sh, the engine behind shfmt. Generated files and the vendored dev skills are excluded in `.prettierignore`.
- Spelling: add legitimate project terms to `project-words.txt`; never disable cspell inline. The file stays sorted (byte order, deduplicated): the pre-commit hook sorts it automatically, and `pnpm words:sort` does it manually.
- PRs are squash-merged, so the PR title becomes the commit header on `main`. The `/squash-message` command drafts that message and `/pr-summary` refreshes the PR body (both in `.claude/commands/`). `/skills:validate <name>` (`.claude/commands/skills/`) runs the application test for one skill and reports it to the PR; see Validation and testing.
- The `skill-files-reviewer` agent (`.claude/agents/`) reviews supporting files added or changed next to a SKILL.md: justified, linked from SKILL.md, runnable, MCP for the agent's own steps, public content only, house style. The `skill-tester` agent in the same directory is the clean-room runner `/skills:validate` spawns when a separate process cannot reach the MCP server; it is not for ordinary work.

## Validation and testing

- `skills-ref validate` must pass for every skill before any commit (the pre-commit hook and CI both run it via `pnpm spec`).
- Every script shipped with a skill has a test suite in `tests/<name>/`. Python scripts use stdlib `unittest` (files named `test_*.py`); TypeScript scripts use vitest (files named `*.test.ts`). `pnpm test` runs every suite and fails when a shipped script has no suite; CI runs it on every push and PR. It is not part of the pre-commit hook (suites may need system tools such as ffmpeg), so run it manually when touching a script. A `tests/<name>/requirements.txt` declares extra Python dependencies for CI.
- Before merging a new or changed skill, run the application test below. Mechanical validation checks the format; the application test checks whether the skill actually teaches.
- `/skills:validate <name>` (`.claude/commands/skills/`) drives that test: it writes a use case for the skill, installs the working-tree copy into a clean-room agent that has no repository context, runs it end to end against the real MCP server in a team and project you choose, grades the transcript, and posts the report to the PR for the current branch (or asks what to do with it when there is none). `--plan-only` runs the zero-cost planning variant below instead of live generation.

### Application test protocol

1. Spawn a fresh agent (no conversation history). Give it only: a framing line ("you are an agent connected to the Scenario MCP server; the skill document below is installed"), the SKILL.md under test (plus the `scenario` SKILL.md when testing any other skill, since real installs ship both), and one realistic task.
2. Ask for a numbered tool-call plan with exact tool names and argument shapes. Planning only: the agent must not execute tools, browse, or consult anything beyond the provided documents, and must flag uncertainty instead of guessing.
3. Pick a task that forces the skill's non-obvious facts (upload flow, job-wait re-calls, dry runs, launch semantics), not one answerable with generic MCP intuition.
4. Grade the plan against the [tool reference](https://mcp.scenario.com/docs/tools), fetched fresh rather than recalled:
   - Every tool and parameter named in the plan exists. One invented name is a fail.
   - Correct flow: the loop the skill under test teaches. For a generation task: discovery, `model_schema_get`, `model_run`, then `jobs_wait` re-called with `pending_job_ids` for any job still running (fast models return complete inline; `job_get` polling is never correct), then `asset_display` / `asset_download`.
   - Model ids come from a `search` or `recommend` step, never asserted as constants.
   - The agent's own steps stay on MCP. A plan that reaches for the REST API, the SDK, or a CLI where an MCP tool exists is a fail, and so is one that invents an API call to cover a capability MCP lacks. Running a script the skill ships is not, whatever that script uses internally, and neither is saving a URL an MCP tool returned.
   - The task's trap steps are handled the way the skill teaches.
   - Anything asserted that appears in neither the SKILL.md nor the tool reference counts as a guess, even when it happens to be right.
5. A failure is a defect in the skill text: fix the missing or ambiguous sentence, then re-run with a new fresh agent (a failed agent is contaminated by its own mistake).
6. Baseline probe, once per new skill (not per edit): run the same task with no skill installed to confirm the skill earns its context cost.

## Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`), enforced by commitlint (see Repo tooling).
- PRs target `main` and are squash-merged; the PR title is the future commit header.
- `CLAUDE.md` is a symlink to this file.
