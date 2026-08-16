---
name: scenario-image
description: "Use when generating or editing images with Scenario through MCP: text-to-image, image-to-image, instruction editing, inpainting or outpainting with a mask, background control, aspect ratio or resolution sizing, several outputs per run, or choosing between Scenario image models. Also when a run fails on prompt length, a plan-restricted model, or a reference image that was silently ignored. Keywords: txt2img, img2img, image edit, inpaint, mask, reference image, aspect ratio."
license: MIT
---

# Scenario Image Generation and Editing

## Overview

Scenario runs hundreds of image models, split across `txt2img` (generate from a prompt) and `img2img` (edit, restyle, inpaint, upscale). The loop is the one the `scenario` skill teaches. What breaks image runs is the per-model contract: sizing fields, prompt limits, and reference caps differ between two models that do the same job, so read `model_schema_get` every time. Grading, effects, expand, resize and the other deterministic tool models: see `scenario-image-editing`. Holding one look across a set: see `scenario-consistency`. Sprites, icons, and tilesets: see `scenario-game-assets`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

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

- **Size.** Sizing has no common shape: numeric `width` and `height` with `min`, `max`, and a `step` to land on; an enum (`aspectRatio`, a `resolution` in megapixels or K tiers, a `size` mixing tiers with pixel pairs); or an aspect ratio alone, which puts an exact pixel target out of reach entirely. Pixels sent to an enum field, or an off-step value, are rejected. When the schema cannot express the size asked for, report what it can reach rather than rounding silently.
- **Prompt length.** The prompt field's `max_length` ranges from roughly 2000 characters to 32000. A prompt that fits one model is a 400 on the next.
- **References.** Name (`referenceImages`, `image`), cap, and cardinality all come from the schema, and the name settles none of them: a field called `referenceImages` is a single scalar file on some models. Pass an array only where the schema says `array: true`, and there pass one even for a lone asset, since a bare string is dropped silently and the run then succeeds while ignoring the reference. With several references, say in the prompt which is which.

A batch-count field (`numOutputs`, `numImages`) repeats one prompt, so it yields variations, not a set. Anything with a per-item difference needs one `model_run` per item.

## Worked example: replacing a label on a product shot

1. `recommend` with `capability="img2img"` and the user's own words as `prompt`. On `next_step.type="ask_user"`, present the options instead of picking; skip any `requires_plan_upgrade` entry.
2. `upload_asset` the product photo, then `upload_asset_complete`, which returns the `asset_id`. Only the inline path under ~100KB skips the second call.
3. `model_schema_get` on the pick: the reference field's name and cap, which sizing family it uses, the prompt `max_length`, and whether a `mask` field exists.
4. For a masked edit, read the `mask` field's own description before building anything. Masks are not interchangeable: one model wants an alpha channel at the source's exact dimensions, another wants a black and white image it resizes itself, and which pixels get painted differs too.
5. `model_run` with the schema's own field names: the prompt, the reference (wrapped in an array only where the schema says `array: true`), plus the mask and sizing fields it named. Use `dry_run=true` first when cost matters.
6. `jobs_wait`, then `asset_display` to review and `asset_download` to save.

## Common mistakes

- Passing a bare string where the schema marks the reference field `array: true`: it is dropped without an error, and the output quietly ignores it.
- Reusing one model's parameter block on another: `aspectRatio` and `width`/`height` rarely coexist, and unknown fields are rejected.
- Retrying a 403 `ModelAccessRestrictedError`: it names `modelId` and `requiredPlan`, so surface the upgrade or pick another model.
- Prompting "transparent background": diffusion outputs are opaque. Use a `background` field when the schema has one, otherwise run a background-removal model afterwards.
- Assuming a model can hit a requested pixel size: some expose an aspect ratio and nothing else.
