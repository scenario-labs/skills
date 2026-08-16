---
name: scenario-model-training
description: "Use when generated assets must keep a consistent style, character, or product look and prompts or reference images stop scaling, or when a user asks to train a custom model through the Scenario MCP, fine-tune a LoRA, clone a voice, upload, curate, or review a training dataset, choose a base model to train on, configure epochs, estimate training cost, or generate with their own trained model. Keywords: custom model, LoRA training, dataset curation, base model choice, style consistency."
license: MIT
---

# Scenario Model Training

## Overview

Train a custom model when one look must hold across many assets: an icon set, a recurring character, a product line. Prompts, references, and control maps are cheaper first steps: see `scenario-consistency`.

The judgment calls live in two references: [references/base-model-selection.md](references/base-model-selection.md) (the user interview that feeds `recommend_training`) and [references/dataset-curation.md](references/dataset-curation.md) (dataset size, image rules, captions, and review per training type).

Connection and the core generation loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

Training tools are not in the default toolset: get schemas with `scenario_tools_search`, run reads (`recommend_training`, `model_get`) via `scenario_tool_execute_read` and writes (`model_create`, `train`, `model_update`) via `scenario_tool_execute_write`, or reconnect with `?toolsets=full`.

## Quick reference

| Step                     | Tool                                                                               |
| ------------------------ | ---------------------------------------------------------------------------------- |
| Pick a base architecture | `recommend_training` (LLM-powered, cost-bearing)                                   |
| Create the model shell   | `model_create` (`data.type` from the recommendation)                               |
| Upload the dataset       | `upload_asset` + `upload_asset_complete`                                           |
| Attach training images   | `train` action `upload_images`, 10 asset ids per call                              |
| Estimate cost            | `train` action `configure` with `dry_run: true`                                    |
| Launch                   | `train` action `configure` without `dry_run` (or `start` for defaults); never both |
| Wait                     | `jobs_wait` with the returned job id                                               |
| Generate                 | `model_schema_get` on YOUR model id, then `model_run`                              |
| Manage                   | `models_list`, `model_get`, `model_update`                                         |

## Worked example: a style LoRA for game props

1. `recommend_training` with `prompt: "hand-painted prop icons for a mobile RPG"`, `modality: "image"`, `dataset_shape: "single_images"`, plus `subject`, `style`, and `priority` from the interview. Returns a recommended variant, alternatives, and `dataset_requirements` (shape and size bounds). Cost-bearing: call it once with clear intent.
2. `model_create` with `data: {"name": "rpg-prop-icons", "type": "<type from step 1>"}`. Note the returned model id.
3. Curate the set first (dataset reference), matching `dataset_requirements` from step 1, then upload each file with `upload_asset` plus `upload_asset_complete` (see the `scenario` skill) and collect the asset ids. For `image_pairs` datasets, map pairs with `train` action `set_pairs`.
4. `train` with `action: "upload_images"`, `model_id`, `images: [<asset ids>]`, at most 10 per call (see Dataset limits); it changes data, so pass `team_id` and `project_id` (scope: the `scenario` skill).
5. `train` with `action: "configure"`, `config: {"epochs": 12}`, `dry_run: true` returns the cost estimate without starting. `epochs` is the main cost lever (scales linearly); size the other levers by dataset size (dataset reference). To launch, re-run the same call without `dry_run` (`configure` and `start` hit the same trigger endpoint).
6. The launch response includes a job: `jobs_wait` with its id in `job_ids`. Training outlasts the server wait budget, so re-call with the returned `pending_job_ids` until completed; never poll `job_get`.
7. Generate: `model_schema_get` on your new model id, then `model_run`; custom models carry their own parameter contract.
8. Manage: `models_list` with `filters: {"privacy": "private", "status": "trained"}` lists ready models. `model_get` with `include_description: true` fetches the full docs; `model_update` edits name, descriptions, privacy.

## Dataset limits that stop a run

Nearly every `train` failure is dataset handling, not hyper-parameters.

- **Ten ids per call.** `upload_images` takes at most 10 asset ids; more returns 400 `Too many assetIds provided in a single request`. Call once per 10-id chunk: the model accumulates the whole set.
- **Chunks must not overlap.** Re-sending an id already attached returns 400 `The provided assetId is already a training image of this model`. After a partial failure, re-send only the chunks that did not land.
- **Two separate plan ceilings.** Dataset size is capped per team: past it, `upload_images` returns 429 naming `add-training-image` with the ceiling in `actionLimit`. Chunking cannot bypass it: trim to the strongest images or surface the upgrade. Concurrent trainings are capped separately as `parallel-training`, and some plans set it to zero.
- **Images before configuration.** `configure` or `start` on an empty dataset fails validation on the training-image count. Pair datasets need whole pairs, with a family minimum above one.
- **One launch at a time.** Once a run is live, `configure` and `start` return 400 `Model is already training`: wait with `jobs_wait` or `train` `action: "stop"`. Repeated launches also hit a cooldown whose 429 names `remainingSeconds`.

## Common mistakes

- Training for a one-off. One on-style image is a prompt plus reference job; the public catalog holds many trained LoRAs, `search` first.
- Using `recommend_training` to pick a generation model: it only picks training bases; use `recommend` or `search`.
- Passing local paths or URLs to `train`: upload with `upload_asset` first and pass asset ids; anything else surfaces as a body-shape error naming `assetId`.
- Reading 400 `Custom models only are supported for this endpoint` as a parameter problem: the route accepts your own trained models only; re-read the id from `models_list`.
- Skipping `dry_run`: `configure` and `start` both accept it and return the cost estimate without charging.
- Filtering `models_list` with `status: "ready"`: free-form values are silently ignored, returning everything including deleted models. Use `"trained"`.
- `model_update` `data.tags` replaces the whole tag set; use `model_add_tags` / `model_remove_tags` for diffs.
- Expecting an older base from `recommend_training`: the default excludes legacy families; set `legacy_ok: true` only when a project must stay on one.

## Voice cloning

Voice cloning starts from the same `recommend_training` call with `modality: "voice"` and `dataset_shape: "short_audio"` or `"long_audio"`; the returned `type` feeds `model_create` the same way.
