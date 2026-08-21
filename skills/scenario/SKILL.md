---
name: scenario
description: Use when connecting an AI agent to Scenario (scenario.com) through MCP, or when a task involves generating images, video, 3D, audio, sprites, textures, or game assets. Also when picking a Scenario model, running a LoRA, refining a generation prompt, uploading reference images, waiting on generation jobs, checking credits or quota, hitting Scenario auth, scope, or Forbidden errors, or setting up mcp.scenario.com in Claude Code, Cursor, or other.
license: MIT
---

# Scenario

## Overview

Scenario (scenario.com) generates AI images, video, 3D, and audio across 500+ models plus custom training, all through the core loop below.

## Setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP). Prefer OAuth: no credentials pass through the conversation. Client config and API-key setup for headless use: [references/setup.md](references/setup.md). Never ask an agent to collect, encode, or echo a secret.

The default toolset is the core loop below; `?toolsets=full` exposes everything. Any other tool: `scenario_tools_search` with the verb as `query` returns its schema and lane; the matching `scenario_tool_execute_read` / `write` / `delete` runs it with `{name, parameters}`, scope ids inside `parameters`. The lane is the result's own `permission`, not what the verb sounds like: `asset_download` and `asset_analyze` are both write-class.

## Scope, and the two errors that name it

Resolve scope first, then pass `team_id` and `project_id` on every later call. `teams_list` returns the teams with their projects; `projects_list` requires a `team_id`, so it cannot come first. Confirm the pair with the user rather than picking.

The server will only auto-fill scope for read-only tools when there's a single possible match; otherwise, the call fails and the error will specify which part is missing or wrong.

- `context_missing`: Nothing resolved. Run `teams_list` then `projects_list`.
- `context_ambiguous`: Multiple options. Show them and let the user choose: never guess, as you could use the wrong project.

For non-interactive runs, use the `team_id` and `project_id` from the task instructions. If those aren't provided, stop and list the available choices. These scope errors appear the first time the team and project pair is missing. A Forbidden error usually means you used the wrong scope, not that you forgot it.

## Quick reference

| Step              | Tool                                     | Notes                                                   |
| ----------------- | ---------------------------------------- | ------------------------------------------------------- |
| Resolve scope     | `teams_list`, then `projects_list`       | Once per session; pass the ids on every call            |
| Find a model      | `search` or `recommend`                  | Free; `recommend` for a capability, `search` for a name |
| Get the schema    | `model_schema_get`                       | Always before `model_run`; check `runs_as` and caps     |
| Generate          | `model_run`                              | Schema-conformant `parameters`; `dry_run` for cost      |
| Wait              | `jobs_wait`                              | Server-side long-poll; never loop `job_get`             |
| View / save       | `asset_display` / `asset_download`       | Never paste raw asset URLs                              |
| Upload inputs     | `upload_asset` + `upload_asset_complete` | Local files become asset_ids                            |
| Refine a prompt   | `prompt_spark`                           | Advisory rewrite; needs `model_id`                      |
| Quota / debugging | `usage`, `diagnostics_run`               | CU consumption; `diagnose` MCP prompt                   |

## Worked example

Generating a stylized game prop image:

1. `recommend` with the user's own words as `prompt` when the need is a capability; `search` with `target="models"`, `query="flux"`, `public=true` when you have a name, and for private or unlisted models. `search` ranks by keyword and its `filters` hold no capability key, so a capability-worded query can rank the wrong output type first. Re-discover ids each time: availability differs per team.
2. `model_schema_get` on the pick: exact field names, types, required flags, defaults, and caps such as the prompt's `max_length` (an overrun is a 400, never a trim). File fields take asset ids even when named `...Url`, and `cost_impact: true` flags what moves the price.
3. If the schema carries `runs_as` (`"lora"` or `"composition"`), never send that model's own id to `model_run`. Its `run_with.required_arguments` holds the real call: `model_id` there is the base model, and its `parameters` (the `loras` or `modelId` wiring) merge into inputs from the same schema. Sending `required_arguments` alone discards your prompt.
4. Optional: `prompt_spark` rewrites a thin prompt into an on-model one; pass the discovered id (a LoRA's own, not its base) and the draft `prompt`. Skip deliberate prompts.
5. `model_run` with `model_id` and schema-conformant `parameters`. Returns asset_ids, or `status="in_progress"` with a `job_id`.
6. `jobs_wait` with `job_ids=[...]` (up to 32). A timeout is not an error: re-call with the returned `pending_job_ids` as `job_ids`. Failed jobs are reimbursed, except xAI generations stopped by moderation.
7. `asset_display` shows the asset inline. `asset_download` returns a file URL. Save it with `curl -L`, it may redirect. `format` is an image conversion (`png`, `webp`, `jpg`) and nothing else: any other value returns 400 `Invalid target format`, so omit `format` entirely for video, 3D, and audio.

Local inputs go up with `upload_asset`: always `file_name`, `content_type`, and `kind` (`image`, `audio`, `video`, `3d`). Prefer multipart: add `file_size`, follow the returned `instructions` to PUT every part URL, then `upload_asset_complete` with the `upload_id`. Inline `data` only under ~100KB. Scope rides on both; they take no other fields: no parts list, no etags.

## Limits that stop a batch

- **Concurrency.** Past a per-team ceiling, `model_run` returns a 429 whose `details` name the limit (`actionName`) and the ceiling (`actionLimit`). Launch with `wait=false` until a 429 names the ceiling, hold that many in flight, and let `jobs_wait` retire them first; an immediate retry repeats the error.
- **Cancellation.** A launched job is committed spend: `job_cancel` rejects most generation jobs (400 `Cannot cancel this type of job`), so plan batches with no abort path. `jobs_wait` takes no timeout argument either, so "wait briefly, then bail" is not expressible: it long-polls to the server budget, and a timeout is a re-call with `pending_job_ids`, never a cancel.
- **Model access.** A 403 on `model_run` names the model and the plan it needs: surface the upgrade or pick another model, retrying never clears it. `recommend` flags these ahead of time as `requires_plan_upgrade`; never run one.

## Common mistakes

- A bare value where the schema says `array: true`: silently dropped, the run ignoring your reference or LoRA. `asset_get` on the output echoes what the run consumed (`metadata.referenceImages`, `parentId`), the cheapest proof it was not.
- Taking `recommend`'s `ranked[0]` blindly: read `next_step.type` first. On `ask_user`, present the options; the user's pick wins (non-interactive: task instructions, else `proceed`). On `proceed`, prefer `specialty.model_id`, else the top `ranked` entry.
- Debugging blind: the `diagnose` MCP prompt (or `diagnostics_run`) returns trace ids; `usage` answers credit questions.
