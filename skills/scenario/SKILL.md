---
name: scenario
description: Use when connecting a coding agent to Scenario (scenario.com) through MCP, or when a task involves generating images, video, 3D, audio, sprites, textures, or game assets with Scenario. Also when picking a Scenario model, running a LoRA, refining a generation prompt, uploading reference images, waiting on generation jobs, checking credits or quota, hitting Scenario auth, scope, or Forbidden errors, or setting up mcp.scenario.com in Claude Code, Cursor, or VSCode.
license: MIT
---

# Scenario

## Overview

Scenario (scenario.com) generates AI images, video, 3D, and audio across 500+ models plus custom model training; its MCP server exposes the full pipeline; the Quick reference below is the core loop.

## Setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP). Prefer OAuth: no credentials pass through the conversation. Client config and API-key setup for headless use: [references/setup.md](references/setup.md). Never ask an agent to collect, encode, or echo a key or secret.

The default toolset is the core loop below; `?toolsets=full` exposes everything. Any other tool: `scenario_tools_search` with the verb as `query` returns its schema and lane; the matching `scenario_tool_execute_read` / `write` / `delete` runs it with `{name, parameters}` (`team_id` and `project_id` go inside `parameters`).

On OAuth connections every data-changing tool (and most others) takes `team_id` and `project_id`; a Forbidden error usually means missing or wrong scope. Read-only tools fill them in when exactly one candidate remains; writes never do: the refusal names the candidate or lists the choices (`teams_list` / `projects_list` enumerate them). Ask the user rather than picking for them.

## Quick reference

| Step              | Tool                                     | Notes                                              |
| ----------------- | ---------------------------------------- | -------------------------------------------------- |
| Find a model      | `search` or `recommend`                  | Free; never hardcode model ids                     |
| Get the schema    | `model_schema_get`                       | Always before `model_run`; check `runs_as`         |
| Generate          | `model_run`                              | Schema-conformant `parameters`; `dry_run` for cost |
| Wait              | `jobs_wait`                              | Server-side long-poll; never loop `job_get`        |
| View / save       | `asset_display` / `asset_download`       | Never paste raw asset URLs                         |
| Upload inputs     | `upload_asset` + `upload_asset_complete` | Local files become asset_ids                       |
| Refine a prompt   | `prompt_spark`                           | Advisory rewrite; needs `model_id`                 |
| Quota / debugging | `usage`, `diagnostics_run`               | CU consumption; `diagnose` MCP prompt              |

## Worked example

Generating a stylized game prop image:

1. `search` with `target="models"`, `query="flux"`, `public=true`, or `recommend` with the user's own words as `prompt`. Re-discover ids each time: availability differs per team.
2. `model_schema_get` on the pick: exact field names, types, required flags, defaults. Names differ per model, file fields take asset ids even when named `...Url`, and `cost_impact: true` flags what moves the price.
3. If the schema carries `runs_as` (`"lora"` or `"composition"`), never send that model's own id to `model_run`. The schema's `run_with.required_arguments` holds the real call: `model_id` there is the base model, and its `parameters` (the `loras` or `modelId` wiring) merge into inputs from the same schema; one `model_schema_get` is enough. Sending `required_arguments` alone discards your prompt.
4. Optional: `prompt_spark` rewrites a thin prompt into an on-model one; pass the discovered id (for a LoRA, its own id, not the base) and your draft as `prompt`. Skip when the prompt is deliberate.
5. `model_run` with `model_id` and schema-conformant `parameters`. Returns asset_ids, or `status="in_progress"` with a `job_id`.
6. `jobs_wait` with `job_ids=[...]` (up to 32). A timeout is not an error: re-call with the returned `pending_job_ids` as `job_ids`.
7. `asset_display` shows the asset inline. `asset_download` returns a file URL; `format` converts image outputs (`png` default, `webp`, `jpg`), omit it for video, 3D, or audio. Save with `curl -L`, it may redirect.

Local inputs go up with `upload_asset`: multipart preferred (pass `file_size`, PUT the presigned URLs, then `upload_asset_complete`); inline base64 only under ~100KB.

## Common mistakes

- A bare value where the schema says `array: true`: pass the array anyway; a scalar can be silently dropped, ignoring your reference image or LoRA.
- Taking `recommend`'s `ranked[0]` blindly: read `next_step.type` first. `ask_user` means present the options; the user's pick wins. On `proceed`, prefer `specialty.model_id` when present, else the top `ranked` entry. Never run a `requires_plan_upgrade` entry; show it with its upgrade option.
- Debugging blind: the `diagnose` MCP prompt (or `diagnostics_run`) returns a report with trace ids; `usage` answers credit questions.
