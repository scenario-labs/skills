---
name: scenario
description: Use when connecting a coding agent to Scenario (scenario.com) through MCP, or when a task involves generating images, video, 3D, audio, sprites, textures, or game assets with Scenario. Also when picking a Scenario model, running a LoRA, refining a generation prompt, uploading reference images, waiting on generation jobs, checking credits or quota, hitting Scenario auth, scope, or Forbidden errors, or setting up mcp.scenario.com in Claude Code, Cursor, or VSCode.
license: MIT
---

# Scenario

## Overview

Scenario (scenario.com) generates AI images, video, 3D, and audio across 500+ models plus custom model training. Its MCP server exposes the full pipeline to any MCP client. Core principle: discover a model, inspect its schema, run it, wait for the job, display the asset.

## Setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP). Prefer OAuth: add the URL, sign in with a Scenario account, and no credentials pass through the conversation.

Claude Code:

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
```

Cursor / VSCode (`mcp.json`):

```json
{ "mcpServers": { "scenario": { "url": "https://mcp.scenario.com/mcp" } } }
```

For headless or CI use, the same endpoint accepts API keys (`Authorization: Basic base64(key:secret)`, keys from app.scenario.com/settings/api). Build the header per the [connection guide](https://mcp.scenario.com/docs), reference it from an environment variable, and never ask an agent to collect, encode, or echo a secret.

The default toolset is the core loop below. Reconnect with `?toolsets=full` for everything, or reach any tool at runtime via `scenario_tools_list` and `scenario_tools_search` plus the `scenario_tool_execute_read` / `write` / `delete` executors.

Scope fills itself in only when exactly one team and project remain possible; otherwise the reply says so and lists them. Ask the user which to use rather than picking one.

## Quick reference

| Step              | Tool                                     | Notes                                              |
| ----------------- | ---------------------------------------- | -------------------------------------------------- |
| 1. Find a model   | `search` or `recommend`                  | Free; never hardcode model ids                     |
| 2. Get the schema | `model_schema_get`                       | Always before `model_run`; check `runs_as`         |
| 3. Generate       | `model_run`                              | Schema-conformant `parameters`; `dry_run` for cost |
| 4. Wait           | `jobs_wait`                              | Server-side long-poll; never loop `job_get`        |
| 5. View / save    | `asset_display` / `asset_download`       | Never paste raw asset URLs                         |
| Upload inputs     | `upload_asset` + `upload_asset_complete` | Local files become asset_ids                       |
| Refine a prompt   | `prompt_spark`                           | Advisory, never a required step                    |
| Quota / debugging | `usage`, `diagnostics_run`               | CU consumption; `diagnose` MCP prompt              |

## The core generation loop

Worked example, generating a stylized game prop image:

1. `search` with `target="models"`, `query="flux"`, `public=true`. Re-discover ids each time: availability differs per team.
2. `model_schema_get` on the pick: exact field names, types, required flags, defaults. Names are per-model (`numOutputs`, not `numImages`), file-typed fields take asset ids even when named `...Url`, and `cost_impact: true` marks the fields that move the price.
3. If that schema carries `runs_as: "lora"`, the model cannot be invoked by its own id. Read `run_with.required_arguments`: `model_run` takes its `model_id` (the base model), and its `parameters` (the `loras` wiring) merge into inputs drawn from the LoRA's own schema. Sending `required_arguments` as the whole request discards your prompt. This is routine, not an edge case: much of the catalog is LoRAs and `recommend` returns them as top picks.
4. Optional: `prompt_spark` rewrites a thin prompt into an on-model one; skip it when the prompt is already deliberate.
5. `model_run` with `model_id` and schema-conformant `parameters` (file inputs take asset_ids). Returns asset_ids, or `status="in_progress"` with a `job_id`.
6. `jobs_wait` with `job_ids=[...]`, up to 32 per call. A timeout is not an error: read `pending_job_ids` off the response and call `jobs_wait` again with those as `job_ids`.
7. `asset_display` to show the asset inline; `asset_download` for a file URL (`curl -L`, it may redirect).

Local inputs go up with `upload_asset`: prefer the multipart path (pass `file_size`, PUT the presigned URLs, then `upload_asset_complete`); inline base64 only for files under ~100KB.

## Common mistakes

- Guessing `model_run` parameters instead of calling `model_schema_get` first: most models reject the empty default payload.
- Passing a LoRA id as `model_run`'s `model_id`: pass the base model from `run_with` instead.
- A bare value where the schema says `array: true`: it is dropped silently, so the job succeeds and quietly ignores your reference image or LoRA.
- Taking `recommend`'s `ranked[0]`: check `next_step.type` first (`ask_user` means present the options and wait), then prefer `specialty.model_id`, which sits outside `ranked`. Never run an entry flagged `requires_plan_upgrade`.
- Polling `job_get` in a loop: `jobs_wait` blocks server-side and streams progress.
- Hardcoding model ids from memory, or rendering asset CDN URLs instead of calling `asset_display`.
- Debugging blind: run the `diagnose` MCP prompt (or `diagnostics_run`) for a report with trace ids, and `usage` for credit questions.
