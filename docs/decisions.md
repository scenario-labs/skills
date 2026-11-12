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

## No install commands in skills

The sibling-install sentence once carried `npx skills add scenario-labs/skills --skill <name>`. That
resolves the latest `skills` package and the repository's moving `main`. A marketplace scan flagged
skills carrying it as possibly loading code from an untrusted or mutable source (October 2026), and
the scan names no line, so that sentence is a suspect, not a proven cause.

- A pin cannot live in the skill: a skill cannot name the commit it ships in.
- `skill_get` serves the core skills from the connected Scenario MCP, with no local install. It
  returns markdown only and does not serve the expert tools, so the sentence also links the README's
  Install section. A link is not an instruction to run, and that section carries the pinned form.
- The pinned form `npx skills@<version> add scenario-labs/skills#<commit>` works: skills 1.7.4
  clones that commit and records it in `skills-lock.json` (checked in a container, October 2026). It
  lives in the README, where a person runs it.

## Freshness block

An installed copy never refreshes itself, and nothing told the user. Every skill now ends with one
fixed block. Before its final reply the agent dates the skill file with `ls -l`. Past two months it
tells the user once, with a link to the README, and carries on.

- The file's date, not a version number. A release number in every skill made each release rewrite
  every SKILL.md, and needed the Scenario MCP server to name the latest release. Nothing in this
  block changes at a release, and the release tooling never touches a skill for it.
- In every skill: a session that loads one task skill does not load the root `scenario` skill. With
  the block in the root skill alone, 2 of 35 trial sessions loaded that skill and none gave the
  reminder (0 of 20).
- A titled block. Written as a plain paragraph, the rule was skipped by Sonnet in 6 of 6 trial
  sessions.
- Last in the file, under a heading that names the moment to act. The trials below ran in a folder
  with no agent instructions, on a file 100 days old.
  - The first version sat right after the first section, under "Freshness check", and said "once per
    session". Sonnet ran the date check in 5 of 21 sessions. Opus reminded in 5 of 6.
  - The same text moved last: Sonnet 6 of 6, Haiku 1 of 4. Moved to the top: Sonnet 0 of 3.
  - Under "Before your final reply", last: Sonnet 18 of 18 over two skills, Haiku 8 of 12, Opus 8 of
    9, the reminder given once each time. Only the Sonnet gain is larger than chance.
  - A first-step heading at the top also reached 6 of 6 with Sonnet, but gave the reminder twice in
    3 of those sessions.
- Two months: by 60 days an installed copy was behind in every case measured, and in 68% of them
  leaving out three repo-wide edits (60 skills, history from August 2026).
- The 2500-word cap counts the block like any other text. An earlier design left its block out of
  the count; seven bodies were trimmed instead, and `scripts/check-style.test.mjs` holds the rule.
- `ls -l` is the block's only command, and the README it links carries the update steps
  ([No install commands in skills](#no-install-commands-in-skills)). Asked to update, agents ran
  `npx skills add` in 6 of 6 sessions when the server instructions named it, and in none when they
  gave only the link.
- The link is `#install`, the one the sibling-install sentence already carries. Fetch tools ignore
  the anchor and return the whole README: 9 trial sessions showed no difference between `#install`,
  `#staying-up-to-date`, and no anchor. What an agent runs is the text under "Staying up to date",
  so that section names one command and no second way to update.
- Trials ran headless Claude Code against a stand-in MCP server (November 2026). The task went on in
  every session, and no session with a recent file gave the reminder. On a recent file Sonnet often
  adds a line saying the file is current (5 of 7 sessions), and Opus did once in 5. That is left as
  it is: a block that tells an agent to run a command silently reads as something to hide.
- Dropped after trials: the rule in the server instructions alone (1 of 12), a release file compared
  with GitHub (1 of 7), a revision line compared through `skill_get` (Sonnet 0 of 7), and the newest
  date among all Scenario skills (2 of 6).
- Also dropped: a 7-word pointer to a `freshness.md` beside each skill. It worked (Sonnet 9 of 10,
  Opus 5 of 5, Haiku 2 of 5), but it trades about 20 body words for a file read in every session and
  one more file in every skill folder, since skills share no folder once installed.
- Limits: the reminder depends on the model and on what else the session was told. A host without a
  shell stays silent. So does a clone or a team repository, where file dates are checkout dates. A
  skill unchanged upstream keeps its old date after an update and can remind again.

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
