---
name: scenario-workflows
description: "Use when a task involves running a Scenario workflow through MCP, including anything the user calls a Scenario app, a saved pipeline, or a multi-step generation graph. Triggers include listing workflows, building the inputs object for workflow_run, pricing a run with a dry run, approving or rejecting the approval node a run is stuck on, or a workflows_list reply that flooded the context. Creating or editing graphs is scenario-workflow-authoring. Keywords: workflow, app, pipeline, approval gate."
license: MIT
---

# Scenario Workflows

## Overview

A Scenario workflow is a saved node graph chaining several models into one call; users say "app" and mean one whose status is `ready`. `workflow_run` returns a job tracked like any other generation.

Only `workflows_list`, `workflow_get` and `workflow_run` are listed by default; approve and reject run through `scenario_tools_search` plus their executor lane. Connection and the core loop: the `scenario` skill. Creating, editing and publishing graphs: the `scenario-workflow-authoring` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step                  | Call                               | Notes                          |
| --------------------- | ---------------------------------- | ------------------------------ |
| 1. List               | `workflows_list` `status="ready"`  | Always cap `limit`             |
| 2. Read the contract  | the record's `inputs[]`            | `name` is the run key          |
| 3. Price and validate | `workflow_run` with `dry_run=true` | Returns cost, creates no job   |
| 4. Run                | `workflow_run` with `inputs`       | Returns a job                  |
| 5. Wait               | `jobs_wait`                        | Re-call with `pending_job_ids` |

Ids are prefixed `wflow_`, not `workflow_` as tool-doc examples show; copy them from `workflows_list`. `search` with `target="workflows"` returned 403 at authoring time, with or without `public=true`.

## Cap every list call

Each record carries the compiled `flow` and the whole `editorInfo` node graph with no compact flag; live records ran 5,500 to 22,000 characters. Cap `limit` at 3 or fewer, read only `id`, `name`, `hasFlow` and `inputs`, and page with `page_token` set to the previous reply's `nextPaginationToken`.

Only `draft` and `ready` filter server-side; other statuses filter each page client-side (flagged `_workflowListStatusFilter`); there an empty page beside a `nextPaginationToken` means keep paging.

## The input contract

`workflow_run`'s `inputs` object is keyed by `inputs[].name`, taken verbatim from the record. Each name is the id of the node behind it, so names can be positional (`text2`, `text3`), neither contiguous nor ordered.

- `label` and `description` carry the human intent, not the key.
- Never harvest keys from `editorInfo.nodes[].data.name`; node names go stale.
- `required` is an object: test `required.always === true`, a truthiness check reads `{"always": false}` as required too.
- Inputs are typed: `string`, `file`, `file_array`, `string_array`, more. `file` takes an asset id (upload first). Match the type: the API drops scalar-for-array mismatches silently and still charges; `workflow_run` wraps simple scalars into arrays, but only simple ones.
- `workflow_get` wraps `inputs_definition`/`editor_info` in `workflow`; `workflows_list` wraps `inputs`/`editorInfo` in `workflows`.

## Worked example: run a saved app

1. `workflows_list` with `status="ready"`, `limit=3`, plus `team_id` and `project_id`. Read `id`, `name` and `inputs` off each record; ignore `flow` and `editorInfo`.
2. An `inputs[]` entry `{"name": "text1", "required": {"always": false}}` runs with `{"text1": "..."}`.
3. `workflow_run` with `workflow_id`, `dry_run=true`, and the full `inputs` object. The reply is `creativeUnitsCost`, `creativeUnitsDiscount` and an empty `job`; quote the cost first. It also runs the real validator.
4. Repeat without `dry_run`, then `jobs_wait` on the returned job, re-calling with `pending_job_ids` while it runs.
5. `asset_display` each output asset, one per id.

## Common mistakes

- Guessing input keys from labels or the node graph instead of reading `inputs[]`.
- Skipping the dry run: two of three ready workflows failed its validation with correctly named inputs; report that error, not the payload.
- Running a draft: `flow: []` and `hasFlow: false` while `inputs` looks complete. Publishing: see `scenario-workflow-authoring`.
- Calling `workflow_approve` or `workflow_reject` without all three of `workflow_id`, `workflow_job_id` and `node_id`: the gate is per node; a parked run never finishes on its own. Find the run with `jobs_list`, read it with `job_get` `verbose=true` (compact replies omit `metadata`): `metadata.flow` lists per-node statuses, the pending approval node's id is `node_id`, the job's id is `workflow_job_id`, its `workflowId` the `workflow_id`. Reject cancels the run.
