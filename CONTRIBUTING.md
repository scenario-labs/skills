# Contributing

Thanks for helping improve the Scenario Agent Skills. This guide covers the mechanics of a good contribution; [AGENTS.md](AGENTS.md) is the full authoring contract and wins wherever the two overlap.

## Before you start

- Found a bug or unclear guidance? [Open an issue](https://github.com/scenario-labs/skills/issues/new/choose) first: the templates capture exactly what a fix needs.
- This repository is public. Everything in it, including commit messages, PR text, and issue text, must be publicly shareable: no internal repositories or hostnames, no credentials or signed asset URLs, no team or project ids you would not publish, and no facts that cannot be verified from public surfaces such as the [tool reference](https://mcp.scenario.com/docs/tools). When in doubt, leave it out.
- Anything tied to your account (billing, credits, a security report) goes to support@scenario.com or in-app support at [app.scenario.com](https://app.scenario.com), never into a public issue. See the [security policy](SECURITY.md).

## Setup

```bash
git clone https://github.com/scenario-labs/skills.git
cd skills
pnpm install
```

`pnpm install` sets up commitlint, cspell, prettier, and the husky git hooks, so every commit runs the same checks CI runs.

## Authoring a skill

Read [AGENTS.md](AGENTS.md) before writing. It defines the frontmatter contract, the description format ("Use when..."), the 600-900 word body target, the MCP-first rule, and the house style: no em dashes, no marketing language, and model ids discovered via `search` rather than asserted as constants. The `skill-creator` dev skill vendored in `.claude/skills/` helps with drafting; where its generic guidance and AGENTS.md disagree, AGENTS.md wins.

## Validating

```bash
pnpm format   # prettier reflows markdown, so run it before validate
pnpm validate # house style, formatting, supporting files, groupings, README table, spelling, spec
pnpm test     # only needed when a shipped script changed; suites live in tests/<name>/
```

A new or changed skill also needs the application test from AGENTS.md ("Validation and testing"): a clean-room agent runs a realistic task with only the skill installed, and its plan is graded against the public tool reference. `/skills:validate <name>` drives it end to end. Mechanical validation checks the format; the application test checks whether the skill actually teaches.

## Commits and pull requests

- Commit messages and PR titles follow [Conventional Commits](https://www.conventionalcommits.org), enforced by commitlint. Valid scopes are the skill directory names plus `skills`, `agents`, `ci`, `deps`, `docs`, and `tooling`.
- PRs target `main` and are squash-merged: the PR title becomes the commit header, so write it as one.
- Keep a PR to one concern. A new skill, a fix to another skill, and a tooling change are three PRs.
- Fill in the pull request template; it mirrors the checks above.

## AI-agent contributors

Agents are first-class authors here (AGENTS.md is written for them), with one expectation: a human reviews the complete diff before the PR is submitted, and the PR says so.

## Code of conduct and license

Participation is governed by the [code of conduct](CODE_OF_CONDUCT.md). Contributions are licensed under the [MIT License](LICENSE), the same license every skill carries in its frontmatter.
