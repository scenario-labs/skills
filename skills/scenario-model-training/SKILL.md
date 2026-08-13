---
name: scenario-model-training
description: "Use when generated assets must keep a consistent style, character, or product look and prompts or reference images stop scaling, or when a user asks to train a custom model on their images through the Scenario MCP, fine-tune a LoRA, clone a voice, upload a training dataset, configure epochs, estimate training cost, or generate with their own trained model. Keywords: custom model, fine-tune, LoRA training, dataset, training job, style consistency."
license: MIT
---

# Scenario Model Training

## Overview

Train a custom model when one look must hold across many assets: an icon set, a recurring character, a product line. Prompts and reference-image inputs are cheaper for one-offs; training pays off when dozens of generations must stay on-style.

Connection and the core generation loop: see the `scenario` skill in this repo.

Training tools are not in the default toolset: get schemas with `scenario_tools_search`, run reads (`recommend_training`, `model_get`) via `scenario_tool_execute_read` and writes (`model_create`, `train`, `model_update`) via `scenario_tool_execute_write`, or reconnect with `?toolsets=full`.

## Quick reference

| Step                     | Tool                                                                               |
| ------------------------ | ---------------------------------------------------------------------------------- |
| Pick a base architecture | `recommend_training` (LLM-powered, cost-bearing)                                   |
| Create the model shell   | `model_create` (`data.type` from the recommendation)                               |
| Upload the dataset       | `upload_asset` + `upload_asset_complete`                                           |
| Attach training images   | `train` action `upload_images`                                                     |
| Estimate cost            | `train` action `configure` with `dry_run: true`                                    |
| Launch                   | `train` action `configure` without `dry_run` (or `start` for defaults); never both |
| Wait                     | `jobs_wait` with the returned job id                                               |
| Generate                 | `model_schema_get` on YOUR model id, then `model_run`                              |
| Manage                   | `models_list`, `model_get`, `model_update`                                         |

## Worked example: a style LoRA for game props

1. `recommend_training` with `prompt: "hand-painted prop icons for a mobile RPG"`, `modality: "image"`, `dataset_shape: "single_images"`. Returns a recommended variant, alternatives, and `dataset_requirements` (shape and size bounds). Cost-bearing: call it once with clear intent rather than iterating. The returned `type` feeds `model_create` `data.type`.
2. `model_create` with `data: {"name": "rpg-prop-icons", "type": "<type from step 1>"}`. Note the returned model id.
3. Upload each dataset file with `upload_asset` plus `upload_asset_complete` (see the `scenario` skill) and collect the asset ids. Match `dataset_requirements` from step 1. For `image_pairs` datasets, map pairs with `train` action `set_pairs`.
4. `train` with `action: "upload_images"`, `model_id`, `images: [<asset ids>]`. `train` changes data, so pass `team_id` and `project_id` (scope: see the `scenario` skill).
5. `train` with `action: "configure"`, `config: {"epochs": 12}`, `dry_run: true` returns the cost estimate without starting. `epochs` is the main cost lever (scales linearly); `nb_repeats`, `batch_size`, and `learning_rate` carry per-family ranges in the input schema. To launch, re-run the same `configure` call without `dry_run` (`configure` and `start` hit the same trigger endpoint; `start` launches with defaults instead).
6. The launch response includes a job: `jobs_wait` with its id in `job_ids`. Training outlasts the server wait budget, so re-call with the returned `pending_job_ids` until completed; never poll `job_get`.
7. Generate: `model_schema_get` on your new model id, then `model_run`; custom models carry their own parameter contract.
8. Manage: `models_list` with `filters: {"privacy": "private", "status": "trained"}` lists ready models (`filters.type` narrows server-side). `model_get` with `include_description: true` fetches the full docs. `model_update` edits `name`, `shortDescription`, `description`, `privacy`.

## Common mistakes

- Training for a one-off. One on-style image is a prompt plus reference job; the public catalog holds many trained LoRAs, `search` first.
- Using `recommend_training` to pick a generation model: it only picks training bases; use `recommend` or `search`.
- Passing local file paths to `train`. Upload with `upload_asset` first and pass Scenario asset ids.
- Skipping `dry_run`. Both `configure` and `start` accept it, returning a cost estimate without charging credits.
- Filtering `models_list` with `status: "ready"`: free-form values are silently ignored, returning everything including deleted models. Use `"trained"`.
- Replacing tags by accident. `model_update` `data.tags` replaces the whole set; use `model_add_tags` / `model_remove_tags` instead.
- Launching twice. `configure` (without `dry_run`) and `start` both trigger training; pick one.

## Voice cloning

Voice clone training starts from the same `recommend_training` call with `modality: "voice"` and `dataset_shape: "short_audio"` or `"long_audio"`; the returned `type` feeds `model_create` the same way.
