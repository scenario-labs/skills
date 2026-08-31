---
name: scenario-brand-kit
description: "Use when building a visual identity or brand kit with Scenario: a logo, wordmark, or icon as editable SVG, a color palette and typography spec, logo variants (mono, reversed, favicon), brand applications like social templates, avatars, banners, or merchandise mockups, and the assembled kit filed with usage rules. Also for a rebrand or refreshing an existing mark. Keywords: brand kit, visual identity, logo, wordmark, SVG, vectorize, color palette, typography, brand guidelines, brand board, identity deck, launch kit."
license: MIT
---

# Scenario Brand Kit

## Overview

An identity is decided, then rendered. Palette and typography are choices written into a spec before any run; the logo is generated once as a real vector and reused everywhere; every application references the approved mark instead of re-imagining it. Skipping the spec yields ten assets that each look fine and do not look related. Connection and the core loop: see the `scenario` skill. Finding the direction when nothing is decided: `scenario-inspiration`. Image runs and reference wiring: `scenario-image`. Exact taglines and CTAs on applications: `scenario-text-overlay`. Per-placement sizes: `scenario-formats`. Gating contract: `scenario-asset-analysis`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Need         | Route                                                                                                                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The spec     | Written first, by you with the user: palette as hex values with roles, two type families with weights, voice line, clear-space and don't rules                                                      |
| Logo, native | `search` `"svg"`: prompt-to-SVG generators (logos, icons, badges) were the authoring-time hits; the output is a real editable vector                                                                |
| Logo, traced | An existing raster mark goes through `search` `"vectorize"` (raster-to-SVG tracers) rather than being regenerated                                                                                   |
| Gate         | `asset_analyze` the mark, the spec passed via `text_inputs`: spelling letter by letter, geometry, palette; a drifted wordmark is re-run, never patched                                              |
| Variants     | `asset_get` the mark and save its `url` (`curl -L`): it serves the stored SVG verbatim, where `asset_download` converts to `png` by default; recolor locally, `upload_asset` each variant back      |
| Applications | `recommend` with `capability="img2img"` (skip a specialty whose `caveats` disclaim the task), approved mark as reference, spec hex values in the prompt, one placement per run                      |
| Fix a mark   | `search` `"logo"`: an authoring-time hit repairs a drifted logo in a scene from the reference as ground truth                                                                                       |
| The board    | `model_scenario-compose-image` (first-party compositor, id fixed): mark, swatches, specimen and applications as positioned layers, labels via `scenario-text-overlay`                               |
| File the kit | `collection_create` before the first run, then `collection_add_assets` each keeper as it lands (tool catalog: `scenario` skill); `asset_update` gives each a description carrying its role and rule |

## The spec sheet

One short document anchors every run and every gate: four to six hex values, each with a role (primary, ink, paper, accent); two type families with weights and their jobs (display, body); the logo's clear space and minimum size; three "never" rules (never stretch, never recolor outside the palette, never set the wordmark in another face). Prompts name hex values from it verbatim, every gate hands its full text to `asset_analyze` through `text_inputs` (a paraphrase drops exact spelling and hex roles), and it ships with the kit as its usage page. Type comes from families the destination can load (widely available or licensed): a generated "font" is a picture of one, so real text is set by `scenario-text-overlay` in the spec's family.

## Worked example: an identity for a new game studio

1. Spec first. The brief names a mood; `scenario-inspiration` turns it into a chosen direction when it names nothing. Write palette, type, and rules down before any generation and confirm with the user (unattended: take the brief's constraints, decide the rest, mark it provisional). Create this run's collection before the first generation (`collection_create`, catalog write lane, `name` only), then `collection_add_assets` each keeper as it lands; its returned `itemCount` is the receipt.
2. Mark: `search` with `target="models"`, `query="svg"`, `public=true` (no capability expresses vector output, so the keyword is the route); `model_schema_get` the generator pick. Prompt one idea about what the studio makes, reduced until it still reads in one color at favicon size: flat closed geometry, few colors, the spec's hex values, the studio name for the wordmark. Say what to avoid or the model reaches for its defaults (gradient mesh, sparkles, an unmotivated bolt, a globe). One run per candidate, `jobs_wait`, `asset_display`, and let the user pick (unattended: gate all, keep the best pass).
3. Gate the pick with `asset_analyze` (write lane, contract in `scenario-asset-analysis`), the spec via `text_inputs`: name read letter by letter, geometry closed and centered, colors on palette. Fail means re-run with the prompt tightened (`jobs_wait` the new job before re-gating), never an edit of the drifted output.
4. Variants: `asset_get` the winning mark and save its `url` with `curl -L`, which serves the stored SVG verbatim (`asset_download` converts to raster, `format` defaulting to `png`). Recolor fills to make mono, reversed, and paper-background variants; `upload_asset` each (`kind` `image`). One mark, colorways as data.
5. Applications: `recommend` with `capability="img2img"`, skipping a specialty whose `caveats` or `when_general_better` name the placement at hand; wire the approved mark as reference exactly as the schema says (an array only under `array: true`; a pick whose schema has no image field cannot hold the mark, so take the next option). One run per placement (avatar, banner, wallpaper), each prompt subordinating the scene to the mark: "the exact logo from the reference, unaltered, centered on...". `jobs_wait` the runs, then gate each against the spec; text the gate cannot resolve at output size is unverified, not passed (upscale and re-gate, or flag it), and a scene that mangled the mark can go through the logo-repair route in the table.
6. Exact text (tagline, handle, URL) is composited by `scenario-text-overlay` in the spec's type, never prompted into the plate. Placement sizes derive per `scenario-formats`.
7. Board: the kit is judged as one picture. `model_scenario-compose-image` (a first-party compositor, so the id is fixed) takes the mark, palette swatches, a type specimen and two applications as layers placed by `x`, `y`, `anchor` and `zIndex` on a `canvasMode: "custom"` canvas, panel labels rendered by `scenario-text-overlay` (layer fields and traps: `scenario-video-assembly`). Give every layer an explicit `width` and `height`; empty is documented as native size and is not reliable. `asset_download` the mark here: its raster conversion, the step 4 hazard, is what a board layer wants.
8. The collection, filled as the run went, is the kit: the SVG master, every variant, every application, the board. Write each asset's role and rule into its `asset_update` description, and deliver the spec sheet as the kit's usage page.

## Common mistakes

- Generating applications before a spec exists: without written hex values and rules there is nothing to gate against, and the kit drifts apart asset by asset.
- Prompting the brand name into every application: generated type drifts; the name rides the approved mark or a `scenario-text-overlay` card.
- Re-imagining the logo per application instead of referencing it: ten cousins, no identity. The mark is generated once, then reused.
- Upscaling a raster of the logo: the vector already scales; the SVG stays the master.
- Recoloring by regenerating: fills and strokes in an SVG are text edits; a regeneration changes the geometry too.
- Passing a wordmark that looks right at thumbnail size: letterform drift hides there; the gate reads it back letter by letter.
- Treating palette hex values as a vibe: unnamed colors drift warm or cool per run; every prompt names them from the spec.
- Deriving a variant from a mockup instead of the master: derivative-of-derivative compounds artifacts (`scenario-formats` has the order of operations).
