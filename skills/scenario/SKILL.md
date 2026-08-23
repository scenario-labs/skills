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

The default toolset is the core loop below; `?toolsets=full` exposes everything. Any other tool: `scenario_tools_search` with the verb as `query` returns its schema and lane; the matching `scenario_tool_execute_read` / `write` / `delete` runs it with `{name, parameters}`, scope ids inside `parameters` (unlike the core tools' top-level `team_id`/`project_id`). The lane is the result's own `permission`, not what the verb sounds like: `asset_download` and `asset_analyze` are both write-class.

## Scope first

Resolve scope first, then pass `team_id` and `project_id` on every later call. `teams_list` returns the teams with their projects; `projects_list` requires a `team_id`, so it cannot come first. Confirm the pair with the user: a guess writes into someone else's project. A non-interactive run takes the pair from its task instructions; when they name none, stop and list the choices.

The server fills scope in only for read-only tools with one candidate remaining; anything else fails rather than guesses, and the error names which half is wrong (see Errors and recovery). Scope errors are the most common failure here, surfacing mid-session on the first call that drops the pair once a second team or project is in play.

## Quick reference

| Step              | Tool                                     | Notes                                                           |
| ----------------- | ---------------------------------------- | --------------------------------------------------------------- |
| Resolve scope     | `teams_list`, then `projects_list`       | Once per session; pass the ids on every call                    |
| Find a model      | `search` or `recommend`                  | Free; `recommend` for a capability, `search` for a name         |
| Get the schema    | `model_schema_get`                       | Always before `model_run`; check `runs_as` and caps             |
| Generate          | `model_run`                              | Schema-conformant `parameters`; `dry_run` for cost              |
| Wait              | `jobs_wait`                              | Only if `model_run` returns `in_progress`; never loop `job_get` |
| View / save       | `asset_display` / `asset_download`       | Never paste raw asset URLs                                      |
| Upload inputs     | `upload_asset` + `upload_asset_complete` | Local files become asset_ids                                    |
| Refine a prompt   | `prompt_spark`                           | Advisory rewrite; needs `model_id`                              |
| Quota / debugging | `usage`, `diagnostics_run`               | CU consumption; `diagnose` MCP prompt                           |

A multi-step request ("product video with voiceover", "concept to 3D") goes to `plan_generation` (catalog-only, read lane): plain words in `description`, ordered steps out, each naming a tool and optional model hint; it runs nothing. Single-step: `recommend`.

## Worked example

Generating a stylized game prop image:

1. `recommend` with the user's own words as `prompt` when the need is a capability; `search` with `target="models"`, `query="flux"`, `public=true` when you have a name. `search` ranks by keyword and its `filters` hold no capability key, so a capability-worded query can rank the wrong output type first. For the user's own trained models, omit `public` on `search` (`search` has no private flag); on `recommend` the flag is `include_private_models: true`. Re-discover ids each time: availability differs per team.
2. `model_schema_get` on the pick: exact field names, types, required flags, defaults, and caps such as the prompt's `max_length` (an overrun is a 400, never a trim). File fields take asset ids even when named `...Url`, and `cost_impact: true` flags what moves the price.
3. If the schema carries `runs_as` (`"lora"` or `"composition"`), never send that model's own id to `model_run`. Its `run_with.required_arguments` holds the real call: `model_id` there is the base model, and its `parameters` (the `loras` or `modelId` wiring) merge into inputs from the same schema. Sending `required_arguments` alone discards your prompt.
4. Optional: `prompt_spark` rewrites a thin prompt into an on-model one; pass the discovered id (a LoRA's own, not its base) and the draft `prompt`. Skip deliberate prompts.
5. `model_run` with `model_id` and schema-conformant `parameters`. Returns asset_ids, or `status="in_progress"` with a `job_id`.
6. `jobs_wait` with `job_ids=[...]` (up to 32); on timeout re-call with the returned `pending_job_ids` as `job_ids`. Failed jobs are reimbursed, except xAI generations stopped by moderation.
7. `asset_display` shows the asset inline; `asset_download` returns a file URL (save with `curl -L`, it may redirect). `format` is an image conversion (`png`, `webp`, `jpg`) and nothing else; omit it for video, 3D, and audio.

Local inputs go up with `upload_asset`: always `file_name`, `content_type`, and `kind` (`image`, `audio`, `video`, `3d`). Prefer multipart: add `file_size`, follow the returned `instructions` to PUT every part URL, then `upload_asset_complete` with the `upload_id`. Inline `data` only under ~100KB. Scope rides on both; they take no other fields: no parts list, no etags.

## Errors and recovery

| Error                                            | Recovery                                                                                                                                                                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `context_missing`                                | Nothing resolved: `teams_list`, then `projects_list`                                                                                                                                                                      |
| `context_ambiguous`                              | Several fit: present the options; the user picks (non-interactive: task instructions name the pair, else stop and list)                                                                                                   |
| 403 Forbidden                                    | Usually wrong scope, not missing: re-check the id pair                                                                                                                                                                    |
| 403 naming a plan                                | Surface the upgrade or switch models; retrying never clears it. `recommend` pre-flags these as `requires_plan_upgrade` (never run one) unless its response says plan gating is `_degraded`; then this row is the backstop |
| 429 with `actionName`/`actionLimit` in `details` | Per-team concurrency ceiling: launch `wait=false`, hold `actionLimit` jobs in flight, let `jobs_wait` retire them; an immediate retry repeats it                                                                          |
| `jobs_wait` timeout (`in_progress`)              | Not an error: re-call with the returned `pending_job_ids`, never a second `model_run` or a cancel; it takes no timeout argument                                                                                           |
| 400 `Cannot cancel this type of job`             | A launched job is committed spend: `job_cancel` rejects most generation jobs, so plan batches with no abort path                                                                                                          |
| 400 `Invalid target format`                      | `format` converts images only: omit it for video, 3D, audio                                                                                                                                                               |

## Common mistakes

- A bare value where the schema says `array: true`: silently dropped, the run ignoring your reference or LoRA. `asset_get` on the output echoes what the run consumed (`metadata.referenceImages`, `parentId`), the cheapest proof it was not.
- Taking `recommend`'s `ranked[0]` blindly: read `next_step.type` first. On `ask_user`, present the options; the user's pick wins (non-interactive: task instructions, else `proceed`). On `proceed`, prefer `specialty.model_id`, else the top `ranked` entry.
- Debugging blind: the `diagnose` MCP prompt (or `diagnostics_run`) returns trace ids; `usage` answers credit questions.
