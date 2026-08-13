---
name: scenario-workflows
description: "Use when a task involves a Scenario workflow through MCP, including anything the user calls a Scenario app, a saved pipeline, or a multi-step generation graph. Triggers include listing or running workflows, building the inputs object for workflow_run, pricing a run with a dry run, publishing a draft so it becomes runnable, approving or rejecting a paused approval node, copying a workflow, or a workflows_list reply that flooded the context. Keywords: workflow, app, pipeline, node graph, approval gate."
license: MIT
---

# Scenario Workflows

## Overview

A Scenario workflow is a saved node graph that chains several models into one call. Users say "app" and mean a workflow whose status is `ready`. Running one is `workflow_run`, which returns a job tracked like any other generation.

Only `workflows_list`, `workflow_get` and `workflow_run` are listed by default; the create, update, publish, copy, approve, reject and delete verbs run through `scenario_tools_search` plus the executor matching their lane. Connection and the core loop: see the `scenario` skill in this repo.

## Quick reference

| Step                  | Call                               | Notes                          |
| --------------------- | ---------------------------------- | ------------------------------ |
| 1. List               | `workflows_list` `status="ready"`  | Always cap `limit`             |
| 2. Read the contract  | the record's `inputs[]`            | `name` is the run key          |
| 3. Price and validate | `workflow_run` with `dry_run=true` | Returns cost, creates no job   |
| 4. Run                | `workflow_run` with `inputs`       | Returns a job                  |
| 5. Wait               | `jobs_wait`                        | Re-call with `pending_job_ids` |

Ids are prefixed `wflow_`, not `workflow_` as the tool-doc examples show, so copy them from `workflows_list`. `search` with `target="workflows"` returned 403 at authoring time.

## Cap every list call

Each record carries the compiled `flow` and the whole `editorInfo` node graph, and no compact flag exists. Live records ran 5,500 to 22,000 characters each, so the default `limit=20` returns a few hundred thousand. Cap `limit` at 3 or fewer, then read only `id`, `name`, `hasFlow` and `inputs`, paging with `page_token` set to the previous reply's `nextPaginationToken`.

Only `draft` and `ready` filter server-side. Any other status filters the returned page client-side and the reply flags `_workflowListStatusFilter`, so an empty array beside a `nextPaginationToken` means none on this page.

## The input contract

`workflow_run`'s `inputs` object is keyed by `inputs[].name`, taken verbatim from the record. Names are authored per workflow: some semantic (`characterDescription`, `line1`), some positional (`text2`, `text3`), and positional names are neither contiguous nor ordered. One live workflow exposes only `text2` and `text3` while its graph still contains a `text1` node.

- `label` and `description` carry the human intent, not the key. A field labelled "Source Image" is still keyed `image1`.
- Never harvest keys from `editorInfo.nodes[].data.name`: on one live workflow seven input nodes all carried the stale value `text1`.
- `required` is an object. Test `required.always === true`, because a truthiness check reads `{"always": false}` as required too.
- `workflow_get` returns the definition as `inputs_definition` and `editor_info` wrapped in `workflow`; `workflows_list` returns the same data as `inputs` and `editorInfo` wrapped in `workflows`. Use the names belonging to the tool you called.

## Worked example: run a saved app

1. `workflows_list` with `status="ready"`, `limit=3`, plus `team_id` and `project_id`. Read `id`, `name` and `inputs` off each record; ignore `flow` and `editorInfo`.
2. Take the target's `inputs[]` and key off each entry's `name`. One exposing `{"name": "text1", "label": "Text 1", "required": {"always": false}}` runs with `{"text1": "..."}`.
3. `workflow_run` with `workflow_id`, `dry_run=true`, and the full `inputs` object. The reply is `creativeUnitsCost`, `creativeUnitsDiscount` and an empty `job`, so no job is created; quote that cost before running. It also runs the real validator, so it doubles as a pre-flight check.
4. Repeat without `dry_run`, then `jobs_wait` on the returned job, re-called with `pending_job_ids` while it is in progress.
5. `asset_display` each output asset, one call per id.

## Common mistakes

- Calling `workflows_list` with no `limit`: the node graphs alone can fill a context window.
- Guessing input keys from labels, or rebuilding them from the node graph instead of reading `inputs[]`.
- Treating `required` as a boolean, so every input reads as mandatory.
- Skipping the dry run because `ready` looks like proof: at authoring time two of three ready workflows failed validation there with correctly named inputs. Report that error rather than blaming the payload.
- Running a draft: it carries `flow: []` and `hasFlow: false` while `editorInfo` and `inputs` look complete. `workflow_create` and `workflow_update` only persist a draft; `workflow_publish` compiles it.
- Calling `workflow_approve` or `workflow_reject` with fewer than all three of `workflow_id`, `workflow_job_id` and `node_id`: the gate is per node. A run parked on an approval node never finishes on its own, however long `jobs_wait` runs.
- Sending `workflow_id` to `workflow_copy`: its parameter is `source_workflow_id`.
