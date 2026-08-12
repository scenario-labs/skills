---
name: scenario
description: Use when connecting a coding agent to Scenario (scenario.com) through MCP, or when a task involves generating images, video, 3D, audio, sprites, textures, or game assets with Scenario. Also when picking a Scenario model, refining a generation prompt, uploading reference images, waiting on generation jobs, checking credits or quota, hitting Scenario auth or Forbidden errors, or setting up mcp.scenario.com in Claude Code, Cursor, or VSCode.
license: MIT
---

# Scenario

## Overview

Scenario (scenario.com) generates AI images, video, 3D, and audio across 500+ models plus custom model training. Its MCP server exposes the full pipeline to any MCP client. Core principle: discover a model, inspect its schema, run it, wait for the job, display the asset.

## Setup

Endpoint: `https://mcp.scenario.com/mcp` (Streamable HTTP). Two auth methods, same endpoint:

- OAuth (recommended): add the URL and sign in with a Scenario account.
- API key: from app.scenario.com/settings/api, sent as `Authorization: Basic base64(key:secret)`.

Claude Code:

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
# API key variant:
claude mcp add --transport http scenario https://mcp.scenario.com/mcp \
  --header "Authorization: Basic $(echo -n 'KEY:SECRET' | base64)"
```

Cursor / VSCode (`mcp.json`):

```json
{ "mcpServers": { "scenario": { "url": "https://mcp.scenario.com/mcp" } } }
```

For API key auth, add `"headers": {"Authorization": "Basic <base64 key:secret>"}`.

The default toolset is the core loop below. Reconnect with `https://mcp.scenario.com/mcp?toolsets=full` to expose everything, or reach any tool at runtime via `scenario_tools_search` plus the `scenario_tool_execute_read` / `write` / `delete` executors.

OAuth callers must pass `team_id` and `project_id` on most tools: call `teams_list` once, and ask the user which to use when several exist.

## Quick reference

| Step               | Tool                                     | Notes                                                  |
| ------------------ | ---------------------------------------- | ------------------------------------------------------ |
| 1. Find a model    | `search` with `target="models"`          | Free; never hardcode model ids                         |
| 2. Get the schema  | `model_schema_get`                       | Always before `model_run`                              |
| 3. Generate        | `model_run`                              | Schema-conformant `parameters`; `dry_run` for cost     |
| 4. Wait            | `jobs_wait`                              | Server-side long-poll; never loop `job_get`            |
| 5. View / save     | `asset_display` / `asset_download`       | Never paste raw asset URLs                             |
| Upload inputs      | `upload_asset` + `upload_asset_complete` | Local files become asset_ids                           |
| Refine a prompt    | `prompt_spark`                           | Rewrites thin prompts per model                        |
| Long-tail tools    | `scenario_tools_search`                  | Full catalog, then permission-scoped executors         |
| Quota / debugging  | `usage`, `diagnostics_run`               | CU consumption; support report (`diagnose` MCP prompt) |

## The core generation loop

Worked example, generating a stylized game prop image:

1. `search` with `target="models"`, `query="flux"`, `public=true`. Returns ranked models with ids such as `model_bfl-flux-2-dev` (an example: re-discover ids each time, availability differs per team).
2. `model_schema_get` with `model_id="model_bfl-flux-2-dev"`: exact field names, types, required flags, defaults.
3. Optional: `prompt_spark` with that `model_id` and `prompt="rusty sci-fi supply crate"` returns on-model prompt variants plus a ready-to-run `recommended_call`. Skip it when the user wants their exact prompt verbatim: it rewrites, it does not lightly edit.
4. `model_run` with `model_id` and schema-conformant `parameters` (for file inputs like `image`, pass asset_ids). Returns asset_ids on completion, or `status="in_progress"` with a `job_id`.
5. `jobs_wait` with `job_ids=[...]`. Timeout is not an error: call it again, passing the returned `pending_job_ids` as `job_ids`.
6. `asset_display` with the asset_id to show it inline; `asset_download` for a file URL (follow redirects when saving: `curl -L`).

Reference images and other local inputs go up with `upload_asset`: prefer the multipart path (pass `file_size`, PUT the presigned URLs, then `upload_asset_complete`); inline base64 only for files under ~100KB.

## Common mistakes

- Guessing `model_run` parameters instead of calling `model_schema_get` first: most models reject the empty default payload.
- Polling `job_get` in a loop: `jobs_wait` blocks server-side and streams progress.
- Hardcoding model ids from memory: catalogs evolve and differ per team, re-run `search`.
- Rendering asset CDN URLs directly: use `asset_display`.
- OAuth calls returning Forbidden: `team_id` and `project_id` are missing, call `teams_list` first.
- Debugging blind: run the `diagnose` MCP prompt (or `diagnostics_run` where MCP prompts are unsupported) for a diagnostics report with trace ids, and `usage` for credit questions.
