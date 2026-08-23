<!--
The PR title becomes the squash commit header on main, so write it as a
Conventional Commit: type(scope): summary. Valid scopes are the skill
directory names plus skills, agents, ci, deps, docs, and tooling.
Example: feat(scenario-luma-video): teach the keyframe reframe workflow

One concern per PR. A new skill, a fix to another skill, and a tooling
change are three PRs. See CONTRIBUTING.md and AGENTS.md.
-->

## What and why

<!-- One or two sentences: what changes, and the problem it solves. -->

## Validation

- [ ] `pnpm format` ran, then `pnpm validate` passes locally
- [ ] `pnpm test` passes (required only when a shipped script changed)
- [ ] For a new or changed skill: the application test from AGENTS.md ran (`/skills:validate <name>`), and the result is summarized below

<!-- Application test result: the task used, pass or fail, what was fixed.
     For docs or tooling changes, write "not applicable" instead. -->

## Public content

- [ ] No internal repositories, hostnames, team or project identifiers, customer names, or unreleased features
- [ ] No credentials: no API keys, tokens, or signed asset URLs
- [ ] Every tool and parameter claim is verifiable from public surfaces (the [tool reference](https://mcp.scenario.com/docs/tools), the public model catalog)

## Authorship

- [ ] A human reviewed the complete diff before this PR was submitted

<!-- If an agent authored this PR, name the harness (Claude Code, Cursor,
     Codex, ...) so reviewers know how the change was produced. -->
