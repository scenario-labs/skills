---
name: scenario-gpt-image
description: "Use when generating or editing images with OpenAI's GPT Image models on Scenario via MCP: text-to-image, instruction-driven editing from reference images, inpainting with an alpha-channel mask, in-image text rendering for logos and infographics, transparent background cutouts, exact pixel sizing, preserving product or face detail with input fidelity, or choosing between family members. Keywords: GPT Image 2, GPT Image 1.5, OpenAI, gpt-image, txt2img, img2img, mask, quality, background."
license: MIT
---

# Scenario GPT Image

## Overview

Every member of GPT Image, OpenAI's image family on Scenario, both generates and edits. At authoring time GPT Image 2 led public arenas in both text-to-image and image editing; 1.5 keeps two contract features 2 lacks. Discover members with `search` and treat `model_schema_get` as the contract: the family agrees on prompt and references, splitting on sizing, masks, and backgrounds.

Connection and the core loop: see the `scenario` skill in this repo; model-agnostic image work: the `scenario-image` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

Shared shape at authoring time: `prompt` (required, cap 32000 characters), `referenceImages` (array, up to 10; the image to edit rides here), `numOutputs` (1 to 10), `quality`, `background`. The splits:

| Contract        | GPT Image 2                         | GPT Image 1.5                            |
| --------------- | ----------------------------------- | ---------------------------------------- |
| Sizing          | `width` and `height`, 16 to 3840 px | `aspectRatio`: auto, 1:1, 3:2, 2:3       |
| Inpainting      | `mask` file                         | no mask field                            |
| `background`    | auto, opaque                        | transparent, opaque, auto                |
| Source fidelity | prompt wording only                 | `inputFidelity`: high locks, low reworks |
| `quality`       | auto, high, medium, low (auto)      | high, medium, low (high)                 |

Routing: exact pixel targets (each axis a multiple of 16) and masked edits go to 2; transparent cutouts and the fidelity dial go to 1.5. The mask on 2 must match the edited image's format and dimensions and keep its alpha channel through export. `referenceImages`, `numOutputs`, `quality`, sizing on 2, and `inputFidelity` on 1.5 all carry `cost_impact`: `dry_run` again after touching any.

## Prompting behavior

Position is weight: style, medium, subject, and mood open the prompt, then scene, details, lighting, and text, in natural sentences rather than tag lists. The 32000-character cap is headroom: past roughly seven distinct requirements some quietly drop, so build a clean base, then one targeted change per edit. When editing, list what must not change; anything unmentioned is open to change.

Text inside the image: quote the exact copy, spell out typography (weight, case, placement), and append "no extra words, no duplicate text". Prompts naming public figures are declined; describe an archetype instead.

## Worked example: a product hero with headline text

1. `search` with `target="models"`, `query="gpt image"`, `public=true`. Prefer the newest non-deprecated hit, e.g. `model_openai-gpt-image-2` (a live hit at authoring time: re-discover each session).
2. `model_schema_get` with that id: sizing bounds, mask presence, and defaults first.
3. `upload_asset` the product photo (see the `scenario` skill) for its asset id.
4. `model_run` with that `model_id`, `dry_run=true`, and `parameters={"prompt": "Editorial product photography, soft daylight. The exact bottle from the reference image on brushed concrete, label, shape, and color preserved. Headline \"DRINK GREEN\" in bold sans-serif, centered, no extra words, no duplicate text.", "referenceImages": ["asset_x"], "width": 1536, "height": 1024, "quality": "high"}` for the cost estimate.
5. Repeat `model_run` with `wait=false`, then `jobs_wait` with the returned job id, re-called with `pending_job_ids` on timeout. A timeout is not a failure and never justifies a second `model_run`.
6. `asset_display` the result and proofread the rendered text before batching; `asset_download` to save.

## Common mistakes

- Asking 2 for `background: "transparent"`: its schema at authoring time takes only auto and opaque; cutouts are 1.5's contract.
- Carrying sizing across members: `width`/`height` on 2, `aspectRatio` on 1.5, never both; off-step pixel values are rejected.
- Leaving `inputFidelity` at its high default when you wanted reinterpretation: drop it to low and re-`dry_run`.
