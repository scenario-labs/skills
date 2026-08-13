---
name: scenario-image
description: "Use when generating or editing images with Scenario through MCP: text-to-image, image-to-image, instruction editing, inpainting or outpainting with a mask, background control, aspect ratio or resolution sizing, several outputs per run, or choosing between Scenario image models. Also when a run fails on prompt length, a plan-restricted model, or a reference image that was silently ignored. Keywords: txt2img, img2img, image edit, inpaint, mask, reference image, aspect ratio."
license: MIT
---

# Scenario Image Generation and Editing

## Overview

Images are Scenario's largest catalog, split across `txt2img` (generate from a prompt) and `img2img` (edit, restyle, inpaint, upscale). The loop is the one the `scenario` skill teaches. What breaks image runs is the per-model contract: sizing fields, prompt limits, and reference caps differ between two models that do the same job, so read `model_schema_get` every time. Holding one look across a set: see `scenario-consistency`. Sprites, icons, and tilesets: see `scenario-game-assets`.

## Quick reference

| Need              | Call                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| Pick a model      | `recommend` with `capability="txt2img"` or `"img2img"`, or `search` (`target="models"`, `public=true`) |
| Read the contract | `model_schema_get`, before every `model_run`                                                           |
| Estimate cost     | `model_run` with `dry_run=true`; `cost_impact: true` marks the fields that move price                  |
| Generate or edit  | `model_run`, then `jobs_wait`                                                                          |
| Review and save   | `asset_display`, then `asset_download` (`png` default, `webp`, `jpg`)                                  |

Inpainting and outpainting are `img2img`, not capabilities of their own.

## The three fields that fail runs

All three are per-model, so take them from the schema rather than from a previous run:

- **Size.** Models use one of two families: either an enum `aspectRatio` (`1:1`, `16:9`, `9:16`, often `match_input_image`) paired with a `resolution` in megapixels, or numeric `width` and `height` in pixels carrying `min`, `max`, and a `step` the value must land on. Pixels sent to an enum field, or an off-step size, are rejected.
- **Prompt length.** The prompt field's `max_length` ranges from roughly 2000 characters to 32000. A prompt that fits one model is a 400 on the next.
- **References.** `referenceImages` is array-typed with a per-model cap (commonly 8 to 10). Pass an array even for one asset: a bare string is dropped silently, so the run succeeds while ignoring the reference. State each reference's role in the prompt.

`numOutputs` repeats one prompt, so it yields variations, not a set. Anything with a per-item difference needs one `model_run` per item.

## Worked example: replacing a label on a product shot

1. `recommend` with `capability="img2img"` and the user's own words as `prompt`. On `next_step.type="ask_user"`, present the options instead of picking; skip any `requires_plan_upgrade` entry.
2. `upload_asset` the product photo, which returns an `asset_id`.
3. `model_schema_get` on the pick: the reference field's name and cap, which sizing family it uses, the prompt `max_length`, and whether a `mask` field exists.
4. For a masked edit, build the mask from the source image. It must match the source's format and dimensions and carry an alpha channel, so export with alpha preserved.
5. `model_run` with `parameters={"prompt": "...", "referenceImages": ["asset_abc"]}` plus the mask and sizing fields the schema named. Use `dry_run=true` first when cost matters.
6. `jobs_wait`, then `asset_display` to review and `asset_download` to save.

## Common mistakes

- Passing a single reference as a bare string: it is dropped without an error, and the output quietly ignores it.
- Reusing one model's parameter block on another: `aspectRatio` and `width`/`height` rarely coexist, and unknown fields are rejected.
- Retrying a 403 `ModelAccessRestrictedError`: it names `modelId` and `requiredPlan`, so surface the upgrade or pick another model.
- Prompting "transparent background": diffusion outputs are opaque. Use a `background` field when the schema has one, otherwise run a background-removal model afterwards.
- Sizing a mask for convenience: a mask differing from the source in format or dimensions fails the run.
