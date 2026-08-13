---
name: scenario-consistency
description: "Use when one look must hold across many Scenario generations: the same character across scenes or a turnaround, the same product across angles and colorways, the same style across an icon set or tileset, or a variant that matches an approved baseline except for one change. Triggers include make this match, same character, keep it consistent, character sheet, reference sheet, style bible, on-model, locked pose, and asking whether to train a LoRA. Keywords: consistency, identity, reference image, control map, ControlNet, seed."
license: MIT
---

# Scenario Consistency

## Overview

"Make variant two look exactly like variant one except for X" is the most repeated creative ask, and agents reach for seeds, which do not solve it. Consistency comes from what you feed the model, in this order of durability: an exhaustive prompt baseline, then reference images, then a structural control map, then a trained model. Connection and the core loop: see the `scenario` skill in this repo; training: see `scenario-model-training`.

## Quick reference

| Technique                  | Holds                       | Effort | Reach for it when                      |
| -------------------------- | --------------------------- | ------ | -------------------------------------- |
| Baseline-plus-delta prompt | identity, framing, palette  | low    | always, it is the floor                |
| Reference image input      | identity and world          | low    | a set of scenes or angles              |
| `asset_detect` control map | pose, geometry, composition | medium | the layout must not move               |
| Seed reuse                 | one image's exact roll      | low    | re-rolling a single generation         |
| Trained LoRA               | a house style at scale      | high   | repeated brand work, not one character |

Scenario's own pipeline guidance is explicit that LoRA training "is for repeated brand-style work at scale, not single character runs", and that you should "generate one strong reference image, then pass it as an image input to every scene generation", preferring models with the most reference-image slots when the request mentions consistency.

## The baseline-plus-delta prompt

The technique that actually works, and the one agents skip: write out everything that must **not** change, exhaustively, then put the single change in a final clause. Keep the whole prompt byte-identical between runs and edit only that last clause.

Enumerate specifics rather than gesturing at them: subject geometry, camera height and angle, subject size and position in frame, lighting direction, each named sub-element and where it sits, palette by name or hex, and any embedded text. Vague anchors drift, so name the exact shade rather than writing "auburn".

Attach the approved baseline as a reference image alongside it. Reference parameters are array-typed, so one asset still goes in as `["asset_..."]` and a bare string is dropped silently. Take the exact name and cap from `model_schema_get`, and state each reference's role in the prompt rather than relying on positional tags.

## Locking structure with a control map

When the layout must survive, generate the control map and pass it as a conditioning input.

`asset_detect` takes an `asset_id` and a `modality` from `canny`, `depth`, `grayscale`, `lineart_anime`, `mlsd`, `normal`, `pose`, `scribble`, `segmentation` and `sketch`, with `remove_background` defaulting to true. It is catalog-only, so reach it through `scenario_tools_search` plus `scenario_tool_execute_write`.

Models that accept control input expose `controlImage`, `controlModality`, `controlStrength`, `controlStart` and `controlEnd`. The two vocabularies are not the same list: `controlModality` allows `canny`, `tile`, `depth`, `blur`, `pose`, `gray` and `low-quality`, so only canny, depth and pose map straight across, and `grayscale` becomes `gray`. `controlStrength` defaults to 0.7, with a recommended range of 0.3 to 0.8: near 0.7 for canny, depth and tile, 0.8 to 0.9 for pose, gray and blur, and rigid above 0.9. Strength is how much the map applies; `controlStart` and `controlEnd` are when. Lowering `controlEnd` to around 0.65 locks composition early, then releases so the prompt can refine detail.

## Common mistakes

- Reaching for a seed to make two different prompts match. A seed reproduces one generation, it does not transfer identity.
- Writing "same as before". The model has no memory between calls; the baseline has to be restated in full every time.
- Passing one reference asset as a bare string instead of an array: it is dropped silently, and the output simply ignores it.
- Piling on references: attribution gets less reliable as the count grows.
- Chaining a set by feeding each output into the next generation: drift compounds. Anchor every item to the same approved baseline.
- Training a LoRA for one character: train for a house style used across many assets. A trained LoRA also cannot be run by its own id (see the `scenario` skill).
- Assuming `asset_detect` modality names are valid `controlModality` values.
