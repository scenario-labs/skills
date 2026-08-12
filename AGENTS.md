# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

## What this repo is

Public Agent Skills for [Scenario](https://scenario.com): procedural knowledge that teaches AI coding agents how to create production-ready content (images, video, audio, textures, skyboxes, 3D, custom models) through the [Scenario MCP server](https://mcp.scenario.com). The workflows serve games, entertainment, and any creative vertical. Skills follow the [Agent Skills](https://agentskills.io) format, install with `npx skills add scenario-labs/skills`, and are listed on [skills.sh](https://www.skills.sh/scenario-labs/skills).

## Layout

```
skills/<name>/SKILL.md   # name must equal the directory name
```

Supporting files (heavy references, scripts) may sit next to a SKILL.md only when the content is too large to inline. Link supporting files directly from SKILL.md: agents resolve file references one level deep, so a reference chained through another supporting file may never be read.

## Public content only

This repository is public. Everything in it, including commit messages, PR text, and issue text, must be limited to publicly shareable language:

- Reference only public surfaces: scenario.com, app.scenario.com, mcp.scenario.com and its `/docs`, docs.scenario.com, and the public model catalog.
- Never reference internal repositories, source file paths, internal hostnames or environments, internal project or team names, customer names, real team/project/API identifiers, credentials, pricing internals, or unreleased features.
- Facts must be verifiable from public surfaces (the tool reference at mcp.scenario.com/docs/tools, live public catalog searches). If a fact is only knowable from internal sources, leave it out.
- When in doubt, treat it as internal: ask, or drop it. Example: no internal repository naming.

## Authoring contract

CI enforces the mechanical parts of this contract on every push and PR: [`skills-ref validate`](https://github.com/agentskills/agentskills/tree/main/skills-ref) (the Agent Skills reference validator) for the spec rules, plus house-style greps. Run it locally with:

```bash
uvx --from "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref" skills-ref validate skills/<name>
```

- Frontmatter: `name` and `description` only, under 1024 characters total.
- `name`: lowercase letters, numbers, and hyphens; must equal the directory name.
- `description`: third person, starts with "Use when", describes triggering conditions only (never a summary of the skill's workflow), under 500 characters, rich in keywords an agent would search for.
- Body: 400-600 words (hard cap 900). Structure: Overview, Quick reference, one excellent worked example, Common mistakes.
- Why the budget: agents load only `name` and `description` at startup; the body enters context only when the skill triggers, and then every word competes with the user's task. Spend words on facts an agent would otherwise guess wrong, not on prose.
- Ground every tool and parameter claim in the [tool reference](https://mcp.scenario.com/docs/tools). Never present a model ID as a constant: model availability differs per team, so teach discovery via `search`.
- Cross-reference the `scenario` skill for connection setup instead of repeating it.
- Style: no em dashes, ever (use a comma, a colon, parentheses, or two sentences). No marketing language. Agent-agnostic wording: do not assume a specific agent outside clearly labeled setup snippets.

## Authoring aids

Anthropic's [skill-creator](https://www.skills.sh/anthropics/skills/skill-creator) (Apache-2.0) is vendored as a dev skill in `.claude/skills/` and `.agents/skills/`, so agents working in a clone of this repo pick it up automatically. `skills-lock.json` records its source and hash; refresh with `npx skills update`. Vendored dev skills live only in agent directories and are never part of the published set: the skills CLI and skills.sh surface only `skills/` (verified against this repo). Where skill-creator's generic guidance and this file disagree, this file wins.

## Validation and testing

- `skills-ref validate` must pass for every skill before any commit (command above; CI runs it too).
- Before merging a new or changed skill, run the application test below. Mechanical validation checks the format; the application test checks whether the skill actually teaches.

### Application test protocol

1. Spawn a fresh agent (no conversation history). Give it only: a framing line ("you are an agent connected to the Scenario MCP server; the skill document below is installed"), the SKILL.md under test (plus the `scenario` SKILL.md when testing any other skill, since real installs ship both), and one realistic task.
2. Ask for a numbered tool-call plan with exact tool names and argument shapes. Planning only: the agent must not execute tools, browse, or consult anything beyond the provided documents, and must flag uncertainty instead of guessing.
3. Pick a task that forces the skill's non-obvious facts (upload flow, job-wait re-calls, dry runs, launch semantics), not one answerable with generic MCP intuition.
4. Grade the plan against the [tool reference](https://mcp.scenario.com/docs/tools), fetched fresh rather than recalled:
   - Every tool and parameter named in the plan exists. One invented name is a fail.
   - Correct flow: discovery, `model_schema_get`, `model_run`, `jobs_wait` (re-called with `pending_job_ids`, never `job_get` polling), then `asset_display` / `asset_download`.
   - Model ids come from a `search` step, never asserted as constants.
   - The task's trap steps are handled the way the skill teaches.
   - Anything asserted that appears in neither the SKILL.md nor the tool reference counts as a guess, even when it happens to be right.
5. A failure is a defect in the skill text: fix the missing or ambiguous sentence, then re-run with a new fresh agent (a failed agent is contaminated by its own mistake).
6. Baseline probe, once per new skill (not per edit): run the same task with no skill installed to confirm the skill earns its context cost.

## Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- PRs target `main`.
- `CLAUDE.md` is a symlink to this file.
