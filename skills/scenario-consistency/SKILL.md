---
name: scenario-consistency
description: "Use when one look must hold across many Scenario generations: the same character across scenes or a turnaround, the same product across angles and colorways, the same style across an icon set or tileset, or a variant that matches an approved baseline except for one change. Triggers include make this match, same character, keep it consistent, character sheet, reference sheet, on-model, and whether to train a LoRA. Keywords: consistency, identity, reference image, control map, ControlNet, seed."
license: MIT
---

# Scenario Consistency

## Overview

"Make variant two look exactly like variant one except for X" is the most repeated creative ask, and agents reach for seeds, which do not solve it. Consistency comes from what you feed the model, in rising order of durability: a prompt baseline, reference images, a control map, a trained model. Connection and the core loop: see the `scenario` skill; training: see `scenario-model-training`.

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

The technique that works, and the one agents skip: write out everything that must **not** change, then put the single change in a final clause. Keep the prompt byte-identical between runs and edit only that clause.

Enumerate specifics rather than gesturing at them: subject geometry, camera height and angle, subject size and position in frame, lighting direction, each named sub-element and where it sits, palette by name or hex, and embedded text. Look at the baseline first (`asset_display`): you cannot enumerate a shade you have not seen, and vague anchors drift.

Attach the approved baseline as a reference image alongside it. Current image models converge on `referenceImages`, but the name settles nothing: cap, requiredness, and cardinality all come from `model_schema_get`, and on some models the field is a single scalar file. Pass an array only where the schema says `array: true`, and there wrap even a lone asset as `["asset_..."]`: a bare string is dropped silently and the run succeeds while ignoring it. State each reference's role in the prompt. A pool of approved on-model shots fills the remaining slots: curate it as a collection (`collection_create`, `collection_add_assets`, catalog tools on the write lane) and retrieve it with `search` `filters={"collection_ids": [...]}`.

A set takes one `model_run` per item: a batch-count field repeats one prompt, so it cannot carry a per-item delta clause.

## Locking structure with a control map

Generate the control map and pass it as a conditioning input. Never extract the map for the attribute that is the delta: a pose map from the approved image locks the very pose you were asked to change, so a pose set needs its map from a target-pose image, or none at all.

`asset_detect` takes an `asset_id` and a `modality` from `canny`, `depth`, `grayscale`, `lineart_anime`, `mlsd`, `normal`, `pose`, `scribble`, `segmentation`, `sketch` (`remove_background` defaults true). Catalog-only and write lane, despite the docs page grouping it under Analysis: run it via `scenario_tool_execute_write`.

The control block (`controlImage`, `controlModality`, `controlStrength`, `controlStart`, `controlEnd`) exists only on models listing `controlnet` in `capabilities`, so check that before planning around it; models without it take reference images instead. The two vocabularies differ: `controlModality` allows `canny`, `tile`, `depth`, `blur`, `pose`, `gray` and `low-quality`, so only canny, depth and pose map across, and `grayscale` becomes `gray`. `controlStrength` defaults to 0.7 with a recommended 0.3 to 0.8 band: near 0.7 for canny, depth and tile, 0.8 to 0.9 for pose, gray and blur, rigid above 0.9. Strength is how much, `controlStart` and `controlEnd` are when: `controlEnd` near 0.65 locks composition early, then releases so the prompt refines detail.

## Worked example: five poses of one mascot

1. `asset_display` the approved hero (`asset_hero`) and write its baseline: the full must-not-change enumeration above.
2. `search` (`target="models"`, `public=true`) for an image model, preferring reference-image slots, then `model_schema_get`: the reference field's exact name, cap, cardinality, and whether it is required.
3. One `model_run` per pose, five in all: the byte-identical baseline, the pose alone in the final clause, the hero in the reference field shaped as the schema says: `["asset_hero"]` only under `array: true`. No seed. No control map: a pose map from the hero locks the very pose being changed.
4. `jobs_wait` on the five job ids, re-calling with `pending_job_ids` until done. `asset_display` each against the hero; fix drift by tightening the enumeration, not by chaining outputs.

## Common mistakes

- Reaching for a seed to make two different prompts match: it reproduces one generation and transfers nothing. Across a set leave it unset; set one only to re-roll a single unchanged prompt.
- Writing "same as before": there is no memory between calls, so restate the baseline in full every time.
- Chaining a set output to output: drift compounds. Anchor every item to the same approved baseline.
- Training a LoRA for one character: train for a house style spanning many assets. A trained LoRA also never runs by its own id: its schema's `runs_as` and `run_with` carry the base-model call (see `scenario`).
- Assuming `asset_detect` modality names are valid `controlModality` values.
