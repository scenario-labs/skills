---
name: scenario-model-training
description: "Use when generated assets must keep a consistent style, character, or product look and prompts or reference images stop scaling, or when a user asks to train a custom model on their images through the Scenario MCP, fine-tune a LoRA, clone a voice, upload a training dataset, configure epochs, estimate training cost, or generate with their own trained model. Keywords: custom model, fine-tune, LoRA training, dataset, training job, style consistency."
license: MIT
---

# Scenario Model Training

## Overview

Train a custom model when one look must hold across many assets: an icon set, a recurring character, a product line. Prompts and references are cheaper for one-offs; training pays off when dozens of generations must stay on-style.

Connection and the core generation loop: see the `scenario` skill in this repo.

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

1. `recommend_training` with `prompt: "hand-painted prop icons for a mobile RPG"`, `modality: "image"`, `dataset_shape: "single_images"`. Returns a recommended variant, alternatives, and `dataset_requirements` (shape and size bounds). Cost-bearing: call it once with clear intent rather than iterating. The returned `type` feeds `model_create` `data.type`.
2. `model_create` with `data: {"name": "rpg-prop-icons", "type": "<type from step 1>"}`. Note the returned model id.
3. Upload each dataset file with `upload_asset` plus `upload_asset_complete` (see the `scenario` skill) and collect the asset ids. Match `dataset_requirements` from step 1. For `image_pairs` datasets, map pairs with `train` action `set_pairs`.
4. `train` with `action: "upload_images"`, `model_id`, `images: [<asset ids>]`, at most 10 per call (see Dataset limits). `train` changes data, so pass `team_id` and `project_id` (scope: see the `scenario` skill).
5. `train` with `action: "configure"`, `config: {"epochs": 12}`, `dry_run: true` returns the cost estimate without starting. `epochs` is the main cost lever (scales linearly); `nb_repeats`, `batch_size`, and `learning_rate` carry per-family ranges in the schema. To launch, re-run the same call without `dry_run` (`configure` and `start` hit the same trigger endpoint; `start` uses defaults).
6. The launch response includes a job: `jobs_wait` with its id in `job_ids`. Training outlasts the server wait budget, so re-call with the returned `pending_job_ids` until completed; never poll `job_get`.
7. Generate: `model_schema_get` on your new model id, then `model_run`; custom models carry their own parameter contract.
8. Manage: `models_list` with `filters: {"privacy": "private", "status": "trained"}` lists ready models (`filters.type` narrows server-side). `model_get` with `include_description: true` fetches the full docs. `model_update` edits `name`, `shortDescription`, `description`, `privacy`.

## Dataset limits that stop a run

Nearly every `train` failure is dataset handling, not hyper-parameters.

- **Ten ids per call.** `upload_images` takes at most 10 asset ids; more returns 400 `Too many assetIds provided in a single request`. Chunk the dataset and call once per chunk, which is additive: the model accumulates the whole set.
- **Chunks must not overlap.** Re-sending an id already attached returns 400 `The provided assetId is already a training image of this model`. After a partial failure, re-send only the chunks that did not land, not the whole list.
- **Two separate plan ceilings.** Dataset size is capped per team: past it, `upload_images` returns 429 naming `add-training-image` with the ceiling in `actionLimit`. Chunking cannot get around that one, so trim to the strongest images or surface the upgrade. Concurrent trainings are capped separately as `parallel-training`, and some plans set it to zero.
- **Images before configuration.** `configure` or `start` on an empty dataset fails validation on the training-image count. Pair datasets need whole pairs, with a family minimum above one.
- **One launch at a time.** Once a run is live, `configure` and `start` both return 400 `Model is already training`. Wait it out with `jobs_wait`, or `train` with `action: "stop"`. Repeated launches also hit a cooldown whose 429 names `remainingSeconds`.

## Common mistakes

- Training for a one-off. One on-style image is a prompt plus reference job; the public catalog holds many trained LoRAs, `search` first.
- Using `recommend_training` to pick a generation model: it only picks training bases; use `recommend` or `search`.
- Passing local file paths or URLs to `train`. Upload with `upload_asset` first and pass Scenario asset ids; anything else surfaces as a body-shape error naming `assetId`, not as a field error on `images`.
- Reading 400 `Custom models only are supported for this endpoint` as a parameter problem: it means the id reached a route that accepts your own trained models only. Re-read the id from `models_list`.
- Skipping `dry_run`. Both `configure` and `start` accept it, returning a cost estimate without charging credits.
- Filtering `models_list` with `status: "ready"`: free-form values are silently ignored, returning everything including deleted models. Use `"trained"`.
- Replacing tags by accident. `model_update` `data.tags` replaces the whole set; use `model_add_tags` / `model_remove_tags` instead.
- Leaving `recommend_training`'s `legacy_ok` at its default and expecting an older base: the default excludes legacy families, so set it true only when a project must stay on one.

## Voice cloning

Voice clone training starts from the same `recommend_training` call with `modality: "voice"` and `dataset_shape: "short_audio"` or `"long_audio"`; the returned `type` feeds `model_create` the same way.
