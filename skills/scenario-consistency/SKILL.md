---
name: scenario-consistency
description: "Use when one look must hold across many Scenario generations: the same character across scenes or a turnaround, the same product across angles and colorways, the same style across an icon set or tileset, or a variant that matches an approved baseline except for one change. Triggers include make this match, same character, keep it consistent, character sheet, reference sheet, style bible, on-model, locked pose, and asking whether to train a LoRA. Keywords: consistency, identity, reference image, control map, ControlNet, seed."
license: MIT
---

# Scenario Consistency

## Overview

"Make variant two look exactly like variant one except for X" is the most repeated creative ask, and agents reach for seeds, which do not solve it. Consistency comes from what you feed the model, in rising order of durability: an exhaustive prompt baseline, reference images, a structural control map, a trained model. Connection and the core loop: see the `scenario` skill; training: see `scenario-model-training`.

## Quick reference

| Technique                  | Holds                       | Effort | Reach for it when                      |
| -------------------------- | --------------------------- | ------ | -------------------------------------- |
| Baseline-plus-delta prompt | identity, framing, palette  | low    | always, it is the floor                |
| Reference image input      | identity and world          | low    | a set of scenes or angles              |
| `asset_detect` control map | pose, geometry, composition | medium | the layout must not move               |
| Seed reuse                 | one image's exact roll      | low    | re-rolling a single generation         |
| Trained LoRA               | a house style at scale      | high   | repeated brand work, not one character |

Scenario's published pipeline guidance says to "generate one strong reference image, then pass it as an image input to every scene generation", to prefer models with the most reference-image slots, and that LoRA training "is for repeated brand-style work at scale, not single character runs".

## The baseline-plus-delta prompt

The technique that works, and the one agents skip: write out everything that must **not** change, exhaustively, then put the single change in a final clause. Keep the prompt byte-identical between runs and edit only that clause.

Enumerate specifics rather than gesturing at them: subject geometry, camera height and angle, subject size and position in frame, lighting direction, each named sub-element and where it sits, palette by name or hex, and any embedded text. Look at the baseline first (`asset_display`): you cannot enumerate a shade you have not seen, and vague anchors drift, so name the shade rather than writing "auburn".

Attach the approved baseline as a reference image alongside it. Reference parameters are array-typed, so one asset still goes in as `["asset_..."]` and a bare string is dropped silently. Take the exact name and cap from `model_schema_get`, and state each reference's role in the prompt.

A set takes one `model_run` per item. A batch-count field repeats one prompt, so it cannot carry a per-item delta clause; use it only to re-roll a single prompt.

## Locking structure with a control map

Generate the control map and pass it as a conditioning input. Never extract the map for the attribute that is the delta: a pose map from the approved image locks the very pose you were asked to change, so a pose set needs its map from a target-pose image, or none at all.

`asset_detect` takes an `asset_id` and a `modality` from `canny`, `depth`, `grayscale`, `lineart_anime`, `mlsd`, `normal`, `pose`, `scribble`, `segmentation` and `sketch` (`remove_background` defaults to true). It is catalog-only: reach it via `scenario_tools_search` plus `scenario_tool_execute_write`.

Models taking control input expose `controlImage`, `controlModality`, `controlStrength`, `controlStart` and `controlEnd`. The two vocabularies differ: `controlModality` allows `canny`, `tile`, `depth`, `blur`, `pose`, `gray` and `low-quality`, so only canny, depth and pose map across, and `grayscale` becomes `gray`. `controlStrength` defaults to 0.7 with a recommended 0.3 to 0.8 band: near 0.7 for canny, depth and tile, 0.8 to 0.9 for pose, gray and blur, rigid above 0.9. Strength is how much, `controlStart` and `controlEnd` are when: lowering `controlEnd` to about 0.65 locks composition early, then releases so the prompt can refine detail.

## Common mistakes

- Reaching for a seed to make two different prompts match: it reproduces one generation and transfers nothing. Across a set leave it unset; set one only to re-roll a single unchanged prompt.
- Writing "same as before": there is no memory between calls, so restate the baseline in full every time.
- Piling on references: attribution gets less reliable as the count grows.
- Chaining a set output to output: drift compounds. Anchor every item to the same approved baseline.
- Training a LoRA for one character: train for a house style spanning many assets. A trained LoRA also cannot be run by its own id (see `scenario`).
- Assuming `asset_detect` modality names are valid `controlModality` values.
