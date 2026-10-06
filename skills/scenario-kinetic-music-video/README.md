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

## Portrait canvas

Added after import so the skill can serve vertical feeds. One canvas per project (`CANVAS` in the
timeline), with `--canvas` for a second ratio. `assets/engine/canvas.js` holds the presets, the
9:16 safe band (derived from the band `scenario-formats` and `scenario-video-ads` compose to,
reading their 6 to 13% per side as 6% left and 13% right, where the action rail sits), the
per-canvas timeline filter and `plateFit`. The HUD, the house subtitle and the scene template lay
out inside `E.SAFE`; every portrait-only behavior is gated off landscape.

Verified headless (Playwright's Chromium, software WebGL) with synthetic audio, lyrics and a
synthetic footage clip (frames, matte, tracking): landscape stills of both template branches
(footage and 3D) and the HUD, including a 150-character lyric line, are pixel-identical to the
pre-change engine at scales 1 and 0.5. Portrait and square stills were checked by eye with the
safe band outlined, and the error paths (bad canvas, bad timeline tag, an `--only` with nothing to
render) fail fast. `canvas.js` has a unit suite. Two plan-only application tests (portrait only;
both ratios) passed with notes. No paid portrait production has run yet, so `motion_library.md`
§10 says its portrait layout rules are untested.

## What the record does not cover

- The skill is the creator's own document, not distilled here, so it does not follow the
  house layout for recipe skills: its `references/lessons.md` plays the Common mistakes role.
- Costs are the production's observed relative prices, not live quotes.
- The engine and scripts need Node with Playwright, ffmpeg and a Python environment
  (`scripts/scaffold.sh` builds it); the matte tool needs macOS (Apple Vision).
- Tests cover the dependency-light scripts and `canvas.js`; the rest need the full environment
  and generated footage.
