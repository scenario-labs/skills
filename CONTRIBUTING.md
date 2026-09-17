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

### Shared agent commands

Repository commands are available in Codex and Claude Code from the same instructions:

| Codex                     | Claude Code               | Purpose                             |
| ------------------------- | ------------------------- | ----------------------------------- |
| `$skills-pr-summary`      | `/pr-summary`             | Refresh the current PR description  |
| `$skills-squash-message`  | `/squash-message`         | Prepare the squash commit message   |
| `$skills-pr-handle <PR>`  | `/skills:pr-handle <PR>`  | Handle a PR and its review comments |
| `$skills-validate <name>` | `/skills:validate <name>` | Run a skill's application test      |

Pass flags after the command, for example `$skills-validate scenario --plan-only --no-post`. Both agents require explicit invocation for the last two commands: Claude uses `disable-model-invocation: true` in shared frontmatter, and Codex uses `allow_implicit_invocation: false` in `agents/openai.yaml`. The shared `argument-hint` field restores Claude autocomplete previews. Start a new Codex session if newly added commands do not appear in the skill picker.

Edit `.agents/skills/skills-*/SKILL.md`; Claude command symlinks read those same files immediately. `pnpm sync:agent-commands` creates or repairs the links, and `pnpm sync:agent-commands:check` validates metadata, argument hints, invocation guards, and links. These commands are repository tooling, not published Scenario skills, so their Claude frontmatter extensions are excluded from strict spec validation.

### Skill content

Read [AGENTS.md](AGENTS.md) before writing. It defines the frontmatter contract, the description format ("Use when..."), the 1000-word body target, the MCP-first rule, and the house style: no em dashes, no marketing language, and generative model ids discovered at runtime (`recommend` for a capability, `search` for a known name) rather than asserted as constants. The `skill-creator` dev skill vendored in `.claude/skills/` helps with drafting; where its generic guidance and AGENTS.md disagree, AGENTS.md wins.

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
- Merged PRs land in the next release, staged by release-please as an open release PR. Merging it tags a release, updates `CHANGELOG.md`, and posts the notes to the [Scenario changelog](https://www.scenario.com/changelog). Your commit type decides the listing: feat, fix, docs, perf, and revert entries appear under their scope, while every other type is invisible to the changelog, chore and ci as intended but also refactor, test, style, and build, so type a change to shipped skill content feat, fix, or docs. Never edit `CHANGELOG.md`, `version.txt`, or `.release-please-manifest.json` by hand.
- Keep a PR to one concern. A new skill, a fix to another skill, and a tooling change are three PRs.
- Fill in the pull request template; it mirrors the checks above.

## AI-agent contributors

Agents are first-class authors here (AGENTS.md is written for them), with one expectation: a human reviews the complete diff before the PR is submitted, and the PR says so.

## Code of conduct and license

Participation is governed by the [code of conduct](CODE_OF_CONDUCT.md). Contributions are licensed under the [MIT License](LICENSE), the same license every skill carries in its frontmatter.
