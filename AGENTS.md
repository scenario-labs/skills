# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

## What this repo is

Public Agent Skills for [Scenario](https://scenario.com): procedural knowledge that teaches AI coding agents how to create production-ready content (images, video, audio, textures, skyboxes, 3D, custom models) through the [Scenario MCP server](https://mcp.scenario.com). The workflows serve games, entertainment, and any creative vertical. Skills follow the [Agent Skills](https://agentskills.io) format, install with `npx skills add scenario-labs/skills`, and are listed on [skills.sh](https://www.skills.sh/scenario-labs/skills).

## Layout

```
skills/<name>/SKILL.md   # name must equal the directory name
```

Supporting files (heavy references, scripts) may sit next to a SKILL.md only when the content is too large to inline.

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
- Ground every tool and parameter claim in the [tool reference](https://mcp.scenario.com/docs/tools). Never present a model ID as a constant: model availability differs per team, so teach discovery via `search`.
- Cross-reference the `scenario` skill for connection setup instead of repeating it.
- Style: no em dashes, ever (use a comma, a colon, parentheses, or two sentences). No marketing language. Agent-agnostic wording: do not assume a specific agent outside clearly labeled setup snippets.

## Authoring aids

Anthropic's [skill-creator](https://www.skills.sh/anthropics/skills/skill-creator) (Apache-2.0) is vendored as a dev skill in `.claude/skills/` and `.agents/skills/`, so agents working in a clone of this repo pick it up automatically. `skills-lock.json` records its source and hash; refresh with `npx skills update`. Vendored dev skills live only in agent directories and are never part of the published set: the skills CLI and skills.sh surface only `skills/` (verified against this repo). Where skill-creator's generic guidance and this file disagree, this file wins.

## Validation and testing

- `skills-ref validate` must pass for every skill before any commit (command above; CI runs it too).
- Before merging a new or changed skill, run an application test: give a fresh agent only the SKILL.md and a realistic task. It must produce a correct tool-call plan without guessing tool names, schemas, or the job-wait flow. Fix the skill until it does.

## Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- PRs target `main`.
- `CLAUDE.md` is a symlink to this file.
