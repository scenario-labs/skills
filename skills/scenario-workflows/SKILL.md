---
name: scenario-workflows
description: "Use when a task involves a Scenario workflow through MCP, including anything the user calls a Scenario app, a saved pipeline, or a multi-step generation graph. Triggers include listing or running workflows, building the inputs object for workflow_run, pricing a run with a dry run, publishing a draft so it becomes runnable, approving or rejecting a paused approval node, copying a workflow, or a workflows_list reply that flooded the context. Keywords: workflow, app, pipeline, approval gate."
license: MIT
---

# Scenario Workflows

## Overview

A Scenario workflow is a saved node graph chaining several models into one call; users say "app" and mean one whose status is `ready`. `workflow_run` runs it and returns a job tracked like any other generation.

Only `workflows_list`, `workflow_get` and `workflow_run` are listed by default; create, update, publish, copy, approve, reject and delete run through `scenario_tools_search` plus the executor matching their lane. Connection and the core loop: see the `scenario` skill.

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

Each record carries the compiled `flow` and the whole `editorInfo` node graph with no compact flag, and live records ran 5,500 to 22,000 characters each. Cap `limit` at 3 or fewer, read only `id`, `name`, `hasFlow` and `inputs`, and page with `page_token` set to the previous reply's `nextPaginationToken`.

Only `draft` and `ready` filter server-side; other statuses filter each page client-side (the reply flags `_workflowListStatusFilter`), so an empty page beside a `nextPaginationToken` means keep paging.

## The input contract

`workflow_run`'s `inputs` object is keyed by `inputs[].name`, taken verbatim from the record. Names are authored per workflow, some semantic (`characterDescription`), some positional (`text2`), and positional names are neither contiguous nor ordered: one live workflow exposes only `text2` and `text3`.

- `label` and `description` carry the human intent, not the key. A field labelled "Source Image" is still keyed `image1`.
- Never harvest keys from `editorInfo.nodes[].data.name`; node names go stale.
- `required` is an object. Test `required.always === true`, because a truthiness check reads `{"always": false}` as required too.
- `workflow_get` wraps the definition in `workflow` as `inputs_definition` and `editor_info`; `workflows_list` wraps it in `workflows` as `inputs` and `editorInfo`.

## Worked example: run a saved app

1. `workflows_list` with `status="ready"`, `limit=3`, plus `team_id` and `project_id`. Read `id`, `name` and `inputs` off each record; ignore `flow` and `editorInfo`.
2. An `inputs[]` entry `{"name": "text1", "label": "Text 1", "required": {"always": false}}` runs with `{"text1": "..."}`.
3. `workflow_run` with `workflow_id`, `dry_run=true`, and the full `inputs` object. The reply is `creativeUnitsCost`, `creativeUnitsDiscount` and an empty `job`; quote the cost first. It also runs the real validator, doubling as a pre-flight check.
4. Repeat without `dry_run`, then `jobs_wait` on the returned job, re-calling with `pending_job_ids` while it runs.
5. `asset_display` each output asset, one call per id.

## Common mistakes

- Guessing input keys from labels or the node graph instead of reading `inputs[]`.
- Treating `required` as a boolean, so every input reads as mandatory.
- Skipping the dry run because `ready` looks like proof: two of three ready workflows failed its validation with correctly named inputs. Report that error rather than blaming the payload.
- Running a draft: it carries `flow: []` and `hasFlow: false` while `inputs` looks complete. `workflow_create` and `workflow_update` only persist a draft; `workflow_publish` compiles it.
- Calling `workflow_approve` or `workflow_reject` with fewer than all three of `workflow_id`, `workflow_job_id` and `node_id`: the gate is per node, and a run parked on one never finishes on its own.
- Sending `workflow_id` to `workflow_copy`: its parameter is `source_workflow_id`.
