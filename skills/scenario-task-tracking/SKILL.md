---
name: scenario-task-tracking
description: "Use when a Scenario billed call is refused with task-id-required, when a project attributes Creative Units to tasks of the team's task tracker, when the user asks which task their generations are billed to, or when the user moves on to other work on such a project. Keywords: task_id, task tracker, task attribution, project tasks, cost attribution, time tracking, production tracking, enterprise."
license: MIT
---

# Scenario Task Tracking

## Overview

Some Enterprise projects attribute every Creative Units charge to a task of the team's own task
tracker. On those projects, a billed call without `task_id` is refused with `task-id-required`, and
nothing is charged. The server stores no task: the agent carries the chosen `task_id` from call to
call. The job is to bill each piece of work to the task the user means, while asking as rarely as
that allows. Core loop and scope rules: see the `scenario` skill. If a sibling skill named here is
missing from your available skills, load it with `skill_get` (Scenario MCP) or ask the user to
install it (https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas
and flag the gap.

## Quick reference

| Situation                         | Action                                                              |
| --------------------------------- | ------------------------------------------------------------------- |
| Billed call refused, tasks listed | Show the tasks, ask the user which one, retry the same call with it |
| Refused, no list in the refusal   | Ask the user to type the id from their task tracker                 |
| Task not among the inline 20      | `project_tasks_list` with `query` (id or name), read lane           |
| Next billed call, same work       | Pass the same `task_id`, ask nothing                                |
| User moves on to other work       | Ask whether it still belongs to the current task                    |
| Project or team switch            | Drop the `task_id`, wait for the next refusal or ask                |
| `dry_run` estimate                | No `task_id` needed                                                 |
| Unattended, no user to ask        | Stop the billed steps and report which project needs a task         |

The tools that take `task_id` are the ones that offer `dry_run`: `model_run`, `workflow_run`,
`train`, `prompt_spark`, `asset_analyze`, `asset_caption`, `asset_describe`, `asset_detect`, and
`asset_quality_gate_run`. `project_tasks_list` is catalog-only: run it through
`scenario_tool_execute_read`.

## The id comes from the user, never from you

The API checks only the id's format (1 to 256 printable ASCII characters), never that the task
exists or belongs to the project. Any string passes and bills that work to it.

- Use only an id the user picked from the project's task list or typed themselves.
- Never invent one, never guess from the task names, never reuse an example or placeholder id.
- Never pick for the user, even when one task looks like the obvious match: suggest it, then ask.
- A task the user named in an earlier conversation is a suggestion only. Tasks open and close, so
  confirm it before the first billed call.

## When to ask again

Ask once per piece of work, not once per call and not once per conversation.

- **Same work**: more variations, a retry, an upscale or an edit of the same asset, the next step of
  the same pipeline. Keep the `task_id`, ask nothing.
- **Other work**: a new subject, a new deliverable, a different stage of production, or the user
  saying they are moving on ("now the environment", "next, the trailer"). Ask one short question
  before the first billed call of it: keep the current task or pick another.
- **Another project or team**: a task belongs to one project. Drop the `task_id` there; the first
  billed call either goes through (the project enforces nothing) or is refused with the list.
- In doubt, ask. A question costs the user a second; a charge on the wrong task costs a correction
  in their tracker.

Word the switch question so a one-word answer works: name the current task and offer the list.

## Worked example

The user asks for three concept sheets of a dragon on a project that enforces task ids.

1. `model_run` without `task_id` comes back refused: `Task id required`, with the project's tasks
   inline (`ART-12 "Dragon concept"`, `ART-14 "Castle key art"`, ...).
2. Ask: "This project bills generations to a task. Which one is this for? ART-12 Dragon concept
   looks like the match." The user answers ART-12.
3. Retry the same `model_run` with `task_id="ART-12"`. Pass `ART-12` on the two remaining sheets and
   on the upscale of the chosen one, without asking.
4. The user says "now let's do the castle". Before the first billed call: "Still on ART-12 Dragon
   concept, or switch to ART-14 Castle key art?" The user picks ART-14; carry it from there.

## Common mistakes

- Filling `task_id` with something plausible to get past the refusal: it passes and bills the wrong
  task.
- Asking before every billed call: once per piece of work is the contract.
- Carrying a `task_id` into another project or team, where the same id means nothing.
- Retrying the refused call unchanged: only a `task_id` clears the refusal.
- Asking for a task on a project that refused nothing: no `task_id` is needed until a billed call is
  refused.
- Saving a task id to memory as a standing default: tasks change, so confirm it each session.
