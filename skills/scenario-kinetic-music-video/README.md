# scenario-kinetic-music-video (maintainer notes, not packaged)

## Origin

Sara Nemati own `kinetic-music-video` skill, built from the production of the Every Scenario
music video (and the kinetic music video it grew out of) and rewritten to be generic: any
subject or none, any looks, no project examples. Brought into this repository from the ZIP she
exported on 2026-10-02.

## Edits for this repository

- Frontmatter reduced to `name`, `description` ("Use when", under 500 characters) and
  `license`; the name carries the `scenario-` prefix.
- Generative model names and ids removed (availability differs per team): lanes are named by
  capability and found with `recommend`. Parameter names are the ones that held at authoring
  time, with the schema as the authority.
- Credit amounts stated as relative costs, with `dry_run` before paid steps.
- En and em dashes replaced, scripts print usage when called without arguments, and the
  output-writing scripts refuse to replace an existing file without `--force`.
- Sibling references and the install invitation added; connection setup points to `scenario`.

## What the record does not cover

- The skill is the creator's own document, not distilled here, so it does not follow the
  house layout for recipe skills: its `references/lessons.md` plays the Common mistakes role.
- Costs are the production's observed relative prices, not live quotes.
- The engine and scripts need Node with Playwright, ffmpeg and a Python environment
  (`scripts/scaffold.sh` builds it); the matte tool needs macOS (Apple Vision).
- Tests cover only the dependency-light scripts; the rest need the full environment and
  generated footage.
