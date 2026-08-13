---
name: scenario-workflow-authoring
description: "Use when a task involves creating or editing a Scenario workflow graph through MCP: building a new workflow or app from a brief, adding or rewiring nodes (models, prompts, approval gates, loops), authoring editor_info, publishing a draft, unpublishing or renaming, importing an exported workflow JSON, copying a workflow to customize it, or turning a prompt chain into a reusable app. Running or pricing an existing workflow is scenario-workflows. Keywords: node graph, editor_info, publish, CEL."
license: MIT
---

# Scenario Workflow Authoring

## Overview

A workflow has two representations: `editor_info` (the editable node graph: `nodes`, `edges`, `inputKeys`) and `flow` (the compiled runnable form). Authoring through MCP means writing the whole `editor_info` document: there are no per-node editing tools; every change is a read, modify, write of the full graph through `workflow_create` or `workflow_update`. Never hand-write `flow`: `workflow_publish` compiles `editor_info` into it and flips status to `ready`. Editing a ready workflow's `editor_info` leaves the stale `flow` running until you publish again.

Read [references/editor-info.md](references/editor-info.md) before writing any graph: it holds the node type vocabulary, the node choice doctrine (when an `llm` node is legitimate), the edge direction rule, per-node data contracts, and a validated minimal example. Create, update, publish, copy and delete live in the tool catalog (`scenario_tools_search` plus the matching executor, see the `scenario` skill). Running and pricing: the `scenario-workflows` skill.

## Quick reference

| Step              | Call                                 | Notes                                    |
| ----------------- | ------------------------------------ | ---------------------------------------- |
| 1. Study a graph  | `workflow_get` on a working workflow | Copy the shape, never ids                |
| 2. Model contract | `model_schema_get`                   | Handle names and required inputs         |
| 3. Author         | `editor_info` + `inputs_definition`  | Per the reference file                   |
| 4. Create         | `workflow_create`                    | Non-atomic, see below                    |
| 5. Publish        | `workflow_publish`                   | Compiles `flow`, needs input+output pins |
| 6. Validate       | `workflow_run` with `dry_run=true`   | Prices and runs the real validator       |

`workflow_create` is two calls under the hood: a failed create may still have created a draft whose id is in the error. Recover with `workflow_update` on that id; re-creating duplicates. Seed step 1 with `workflow_get`: it returns the full graph of any workflow whose id you have, public ones included (an id or app URL the user supplies, or your own team's from `workflows_list`). Do not hunt ids with `search`: its `workflows` target returned 403 at authoring time, with or without `public=true` (the `scenario-workflows` skill records the same). [scripts/fetch_workflow_examples.py](scripts/fetch_workflow_examples.py) bulk-exports trimmed featured-workflow graphs for maintainers (setup in its header).

## Worked example: a text-to-image app

1. `search` for the model, then `model_schema_get`: its input names become the model node's handle names, and `required.always === true` marks what must be wired.
2. Author `editor_info`: `text1` with `data.isInput: true`, `model1` with `type: "model"`, `data.modelId` and `data.isOutput: true`, one edge from `model1`'s input to `text1`'s output (edges name the downstream node as `source`, see the reference), `inputKeys: ["text1"]`.
3. `workflow_create` with `name`, `editor_info`, and `inputs_definition` naming `text1` as a string input. The published input key is the node id, which is why run inputs have names like `text1`.
4. `workflow_publish`, then `workflow_run` with `dry_run=true` to validate and price. Fix the graph and re-publish if validation fails.

## Common mistakes

- Writing UI palette names as node types: persisted types are the camelCase vocabulary in the reference, and every generator is `type: "model"`.
- Wiring edges producer to consumer: persisted edges point the other way.
- Expecting an `editor_info` update to change a live app without re-publishing.
- Retrying a failed `workflow_create` with a second create instead of `workflow_update` on the id from the error.
- Publishing with no pins: at least one `data.isInput` node listed in `inputKeys` and one `data.isOutput` node.
- Double-quoted CEL literals: they evaluate but corrupt the canvas editor, single quotes only.
- Sending `workflow_id` to `workflow_copy`: its parameter is `source_workflow_id`; the copy inherits everything verbatim and needs its own publish.
