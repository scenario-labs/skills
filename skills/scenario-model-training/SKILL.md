---
name: scenario-model-training
description: "Use when generated assets must keep a consistent style, character, or product look and prompts or reference images stop scaling, or when a user asks to train a custom model on their images through the Scenario MCP, fine-tune a LoRA, clone a voice, upload a training dataset, configure epochs, estimate training cost, or generate with their own trained model. Keywords: custom model, fine-tune, LoRA training, dataset, training job, style consistency."
---

# Scenario Model Training

## Overview

Train a custom model when one look must hold across many assets: an icon set, a recurring character, a product line. Prompts and reference-image inputs are cheaper for one-offs; training pays off when dozens of generations must stay on-style.

Connection and the core generation loop: see the `scenario` skill in this repo.

Training tools are not in the default toolset: get schemas with `scenario_tools_search`, run reads (`recommend_training`, `model_get`) via `scenario_tool_execute_read` and writes (`model_create`, `train`, `model_update`) via `scenario_tool_execute_write`, or reconnect with `?toolsets=full`.

## Quick reference

| Step | Tool |
| --- | --- |
| Pick a base architecture | `recommend_training` (LLM-powered, cost-bearing) |
| Create the model shell | `model_create` (`data.type` from the recommendation) |
| Upload the dataset | `upload_asset` + `upload_asset_complete` |
| Attach training images | `train` action `upload_images` |
| Estimate cost | `train` action `configure` with `dry_run: true` |
| Launch | `train` action `configure` without `dry_run` (or `start` for defaults); never both |
| Wait | `jobs_wait` with the returned job id in `job_ids` |
| Generate | `model_schema_get` on YOUR model id, then `model_run` |
| Manage | `models_list`, `model_get`, `model_update` |

## Worked example: a style LoRA for game props

1. `recommend_training` with `prompt: "hand-painted prop icons for a mobile RPG"`, `modality: "image"`, `dataset_shape: "single_images"` (optional `style`, `subject`, `priority`). Returns a family, a recommended variant plus alternatives, and `dataset_requirements` (shape, min/recommended/max size). It is LLM-powered and cost-bearing: call it once with clear intent rather than iterating. The returned `type` is the exact value for `model_create` `data.type`.
2. `model_create` with `data: {"name": "rpg-prop-icons", "type": "<type from step 1>"}`. Note the returned model id.
3. Upload each dataset file with `upload_asset` (multipart path: `file_name`, `content_type`, `kind`, `file_size`; PUT the presigned parts; finish with `upload_asset_complete`) and collect the asset ids. Match `dataset_requirements` from step 1. For `image_pairs` datasets, map pairs with `train` action `set_pairs`.
4. `train` with `action: "upload_images"`, `model_id`, `images: [<asset ids>]`. OAuth connections must also pass `team_id` and `project_id` on every `train` call (get them from `teams_list` / `projects_list`).
5. `train` with `action: "configure"`, `config: {"epochs": 12}`, `dry_run: true` to get the cost estimate without starting. `epochs` is the primary duration and cost lever (cost scales linearly); `nb_repeats`, `batch_size`, and `learning_rate` carry per-family ranges in the input schema. To launch, re-run the same `configure` call without `dry_run`: `configure` and `start` hit the same trigger endpoint, so `configure` without `dry_run` starts training with your parameters. Use `action: "start"` only to launch with default settings; never call both, that starts training twice.
6. `configure`/`start` responses include a job. Call `jobs_wait` with its id in `job_ids`. Training outlasts the roughly 180s server wait budget: on `status: "in_progress"`, call `jobs_wait` again, passing the returned `pending_job_ids` as `job_ids`, until completed. Never poll `job_get` in a loop.
7. Generate: `model_schema_get` with your new model id, then `model_run`. Custom models carry their own parameter contract, so never reuse a base family's schema from memory.
8. Manage: `models_list` with `filters: {"privacy": "private", "status": "trained"}` lists ready models; `filters.type` (for example `"flux.1-lora"`) narrows server-side. `model_get` with `include_description: true` fetches the long markdown docs. `model_update` edits `name`, `shortDescription`, `description`, `privacy`.

## Common mistakes

- Training for a one-off. One on-style image is a prompt plus reference job on an existing model; `search` with `target: "models"` first, the public catalog holds many trained LoRAs.
- Using `recommend_training` to pick a generation model. It only picks a training base; use `recommend` or `search` for generation.
- Passing local file paths to `train`. Upload with `upload_asset` first and pass Scenario asset ids.
- Skipping `dry_run`. Both `configure` and `start` accept `dry_run: true` and return a cost estimate without charging credits.
- Filtering `models_list` with `status: "ready"`. Free-form values are silently ignored and return everything, including deleted models. Use `"trained"`.
- Replacing tags by accident. `model_update` `data.tags` replaces the whole set; use `model_add_tags` / `model_remove_tags` for incremental changes.
- Launching twice. `configure` (without `dry_run`) and `start` both trigger training; pick one.

## Voice cloning

Voice clone training starts from the same `recommend_training` call with `modality: "voice"` and `dataset_shape: "short_audio"` or `"long_audio"`; the returned `type` feeds `model_create` the same way.
