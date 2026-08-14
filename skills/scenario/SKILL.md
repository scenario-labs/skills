---
name: scenario
description: Use when connecting a coding agent to Scenario (scenario.com) through MCP, or when a task involves generating images, video, 3D, audio, sprites, textures, or game assets with Scenario. Also when picking a Scenario model, running a LoRA, refining a generation prompt, uploading reference images, waiting on generation jobs, checking credits or quota, hitting Scenario auth, scope, or Forbidden errors, or setting up mcp.scenario.com in Claude Code, Cursor, or VSCode.
license: MIT
---

# Scenario

## Overview

Scenario (scenario.com) generates AI images, video, 3D, and audio across 500+ models plus custom model training; its MCP server exposes the full pipeline; the Quick reference below is the core loop.

## Setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP). Prefer OAuth: no credentials pass through the conversation. Client config and API-key setup for headless use: [references/setup.md](references/setup.md). Never ask an agent to collect, encode, or echo a secret.

The default toolset is the core loop below; `?toolsets=full` exposes everything. Any other tool: `scenario_tools_search` with the verb as `query` returns its schema and lane; the matching `scenario_tool_execute_read` / `write` / `delete` runs it with `{name, parameters}` (`team_id` and `project_id` go inside `parameters`). The lane is the result's own `permission`, not what the verb sounds like: `asset_download` and `asset_analyze` are both write-class.

## Scope, and the two errors that name it

Resolve scope first, then pass `team_id` and `project_id` on every later call. `teams_list` returns the teams with their projects; `projects_list` requires a `team_id`, so it cannot come first. Confirm the pair with the user rather than picking.

The server fills scope in only for read-only tools, and only while one candidate remains, so an unresolved scope fails the call rather than guessing, and the error names which half is wrong. `context_missing` means nothing resolved: run `teams_list`, then `projects_list`. `context_ambiguous` means several fit: present them and let the user choose, because a guess here writes assets into someone else's project. A non-interactive run takes the pair from its task instructions; when they name none, stop and list the choices. Together these are the most common failure across every tool below, and they surface mid-session on the first call that drops the pair once a second team or project is in play. A Forbidden error usually means wrong scope rather than missing scope.

## Quick reference

| Step              | Tool                                     | Notes                                              |
| ----------------- | ---------------------------------------- | -------------------------------------------------- |
| Resolve scope     | `teams_list`, then `projects_list`       | Once per session; pass the ids on every call       |
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
3. If the schema carries `runs_as` (`"lora"` or `"composition"`), never send that model's own id to `model_run`. Its `run_with.required_arguments` holds the real call: `model_id` there is the base model, and its `parameters` (the `loras` or `modelId` wiring) merge into inputs from the same schema. Sending `required_arguments` alone discards your prompt.
4. Optional: `prompt_spark` rewrites a thin prompt into an on-model one; pass the discovered id (for a LoRA, its own, not the base) and your draft as `prompt`. Skip a deliberate prompt.
5. `model_run` with `model_id` and schema-conformant `parameters`. Returns asset_ids, or `status="in_progress"` with a `job_id`.
6. `jobs_wait` with `job_ids=[...]` (up to 32). A timeout is not an error: re-call with the returned `pending_job_ids` as `job_ids`.
7. `asset_display` shows the asset inline. `asset_download` returns a file URL. Save it with `curl -L`, it may redirect. `format` is an image conversion (`png`, `webp`, `jpg`) and nothing else: any other value returns 400 `Invalid target format`, so omit `format` entirely for video, 3D, and audio.

Local inputs go up with `upload_asset`, which always needs `file_name`, `content_type`, and `kind` (`image`, `audio`, `video`, `3d`). Prefer multipart: add `file_size`, follow the returned `instructions` to PUT every part URL, then `upload_asset_complete` with the `upload_id`. Inline `data` only under ~100KB. Scope rides on both; beyond the fields named here they take nothing: no parts list, no etags.

## Limits that stop a batch

- **Concurrency.** A team may only run so many jobs at once. Past that, `model_run` returns a 429 whose `details` name the limit (`actionName`) and the ceiling (`actionLimit`). Launch with `wait=false` until a 429 names the ceiling, hold that many in flight, and let `jobs_wait` retire them before launching more. Retrying immediately just repeats the error.
- **Model access.** A 403 on `model_run` names the model and the plan it needs: surface the upgrade or pick another model, retrying never clears it. `recommend` flags these ahead of time as `requires_plan_upgrade`; never run one.

## Common mistakes

- A bare value where the schema says `array: true`: a scalar can be silently dropped, ignoring your reference image or LoRA.
- Taking `recommend`'s `ranked[0]` blindly: read `next_step.type` first. `ask_user` means present the options; the user's pick wins (non-interactive: task instructions name the pick, else `proceed`). On `proceed`, prefer `specialty.model_id`, else the top `ranked` entry.
- Debugging blind: the `diagnose` MCP prompt (or `diagnostics_run`) returns trace ids; `usage` answers credit questions.
