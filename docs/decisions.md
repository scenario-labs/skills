# Decisions

The history and evidence behind rules in [AGENTS.md](../AGENTS.md). AGENTS.md states each rule; this
file records why, so a settled question is reopened only with new evidence.

## Word budget

The body caps (1000-word target, 2500-word hard cap) come from this repo, not from outside:

- Nothing outside this repo caps a body by word count. The spec says the body has "no format
  restrictions", and `skills-ref` validates a 200,000-word body clean.
- The widely repeated "5000 words" is a debugging remedy for a skill already behaving badly, not a
  budget.
- Anthropic states exactly one size rule, "keep SKILL.md body under 500 lines", and its own "Token
  budgets" section only restates it.
- A line count measures nothing stable here: prettier rewraps prose at 100 columns, and the largest
  body runs about 260 lines. The word cap binds well before 500 lines would, so no line cap is
  enforced.
- The one mechanism that bites is Claude Code's post-compaction re-attach. It keeps the first 5000
  tokens of each invoked skill from a 25,000-token pool shared across them. The pool fills from the
  most recently invoked, so older skills are dropped entirely once it overflows.
- At this repo's density, about 7 characters per word or roughly 1.75 tokens per word, 2500 words is
  near 4400 tokens. That sits inside the per-skill ceiling with margin for identifier-dense prose;
  past it, a body trades content for truncation.
- The cap is the guardrail and the target is the craft. The cap binds a handful of skills; what
  protects the shared pool is the mean, which the fan-out notice watches.

## Model ids and discovery

- Of the 64 tool-tagged Scenario-branded models, 61 report Scenario as provider. The three that
  report BFL are the FLUX upscale variants, upscaling being the one lane among them with
  competitors. Hence the provider check before naming an id.
- `search` with `query="image edit"` returned 318 hits with nothing to choose between them. A skill
  that shipped that query had its member picked by reading marketing blurbs. Hence `recommend` for
  capabilities.
- `recommend` quoted 48.2 CU for a run that billed 55. Hence `dry_run` for the exact price.

## Unversioned skill names

A versioned name goes stale the day the next generation ships. It then forces either a breaking
rename or a pile of near-duplicate skills competing for the same trigger. It is the model-id rule
one level up.

## skills.sh groupings

Our groups were confirmed visible on skills.sh on September 22, 2026. The earlier failure is
recorded at [vercel-labs/skills#2136](https://github.com/vercel-labs/skills/issues/2136).

## No install-everything command

The README once offered `--skill "*"`. It takes every skill, the expert tools included, and an agent
loads every installed skill's description at startup: a reader who never opens a DCC tool carried 57
expert descriptions at the time. The default command names the core skills instead.

## Skill and plugin versions

- Each SKILL.md carries `metadata.version`, the release it shipped in. The spec has no version
  field, but its own example uses `metadata.version`, as do other public skill repositories. An
  earlier draft put the version in a body HTML comment so Claude Code agents would see it (Claude
  Code strips frontmatter). It was dropped: no other project does it, and updates belong to the
  distribution layer, not to the agent.
- One release-wide version, not one per skill: `npx skills update` and plugin updates refresh
  everything at once, so a per-skill version adds bookkeeping without changing what a user does.
- Plugin entries in the marketplace carry the release version. Without one, Claude Code versions a
  relative-path plugin by commit, and every plugin here has `source: "./"`, so every merge to `main`
  (CI and chore commits included) was an update for all of them. With it, Claude Code updates
  plugins at releases, the same points the changelog announces.

## Release tags

Releases through 0.37.3 tagged bare `vX.Y.Z`. That is because a `release-type: node` package gets
its component free from the `package.json` name, while `release-type: simple` has none to derive.
Setting `component` plus `include-component-in-tag` by hand produced the `skills-` prefix.

## AGENTS.md size

- Codex reads 32 KiB of `AGENTS.md` by default (`project_doc_max_bytes`) and silently drops the
  rest. `.codex/config.toml` raised it to 64 KiB, but Codex ignores that file in untrusted projects.
- In October 2026 `AGENTS.md` reached 43 KB, so an untrusted Codex session would stop reading inside
  the release notes, before the Codex attribution rules.
- Claude Code also warns about a memory file past 40,000 characters, at the default context size.
- The fix moved situational sections into `docs/` (31.6 KB left), dropped the override, and made
  `pnpm style` fail past 32 KiB.

## Video verification

A one-frame-per-shot spot check read clean at 10.5s on a clip whose artifact appears at 11.0s. Hence
contact sheets that sweep the whole clip.
