---
name: scenario-report
description: "Use when a Scenario user wants to report a bug or request a change on the public issue tracker at github.com/scenario-labs/skills: turning a failed generation, MCP tool error, or unclear skill into a reproducible report, collecting trace ids with diagnostics_run, stripping keys, team ids, signed asset URLs, and personal data before posting, searching for duplicates, or building a prefilled issue URL when the agent cannot call GitHub. Keywords: file an issue, feature request, feedback."
license: MIT
---

# Reporting Scenario bugs and change requests

## Overview

Public tracker: `https://github.com/scenario-labs/skills/issues`, forms `bug.yml` and `change-request.yml`.

Two constraints. The issue is public and permanent, so redact first and post only after the user approves the exact text. The reader has no access to the user's account, so the report must carry everything needed to reproduce from outside.

Connection and the core generation loop: see the `scenario` skill in this repo.

Account, billing, credit, quota, sign-in, and security problems never go in a public issue: send those to in-app support at `app.scenario.com`.

## Quick reference

| Step     | Do                                              | Notes                             |
| -------- | ----------------------------------------------- | --------------------------------- |
| Classify | bug or change request                           | One problem per issue             |
| Gather   | failing call, verbatim error, `diagnostics_run` | In the session that failed        |
| Redact   | strip identity and secrets                      | Not optional                      |
| Dedupe   | search open and closed issues                   | Comment on a match, do not refile |
| Draft    | fill every form field                           | Label guesses as guesses          |
| Approve  | show the final title and body                   | Never post silently               |
| Post     | GitHub tool or prefilled URL                    | Both below                        |

## Redact before drafting

Never include API keys or tokens, signed URLs from `asset_download` (the URL is a credential), team or project ids and names, emails, local paths containing a username, or unreleased art, prompts, and model names the user has not agreed to publish.

`diagnostics_run` is the best evidence and the biggest leak: `self_test.detail` can enumerate every team and project the user belongs to, and `tenant` can encode their account. Copy only `version`, `endpoint`, `auth_type`, `self_test.layer`, `self_test.latencyMs`, `generated_at`, and the ids under `confirmed_trace_ids` and `candidate_trace_ids`. Nothing else from that report.

Job, asset, and model ids let support match the report to a server-side request: include them once the user agrees. Signed download URLs, never.

## Make it reproducible

Name the model id and whether `search` finds it with `public=true`, the exact `parameters` sent to `model_run`, the verbatim error, the UTC timestamp, and at least one trace id. Substitute a short public prompt for a confidential one, and say that you did. Say when a model is team-private: the reader will reproduce against a public equivalent.

## Worked example: a texture upscale that never finishes

1. `diagnostics_run` in the failing session: keep the fields listed above and the trace ids, discard the rest.
2. Re-run the failing call once, capturing the arguments, the verbatim response, and the UTC time.
3. `search` with `public=true`: is the upscaler public, so the reader can run the same call?
4. Search the tracker, open and closed, for `jobs_wait pending`.
5. Draft. Title: `jobs_wait keeps returning the same texture upscale job in pending_job_ids for 20 minutes`. Steps: the `model_schema_get`, `model_run`, and repeated `jobs_wait` calls with their arguments. Expected: the job completes or fails. Actual: `status` stays `in_progress`, `pending_job_ids` unchanged. Evidence: job id, trace ids, timestamp.
6. Show the user the full text, and post only on a yes.

## Posting

- With GitHub tooling: search `repo:scenario-labs/skills` for duplicates, then create the issue with the label `bug` or `enhancement`, mirroring the form headings in the body.
- Browser only: build `https://github.com/scenario-labs/skills/issues/new?template=bug.yml&summary=...&repro=...`, percent-encoding each value. Parameter names are the form field ids: `summary`, `area`, `repro`, `expected`, `actual`, `evidence`, `env`, `frequency`; change requests use `problem`, `area`, `today`, `proposal`, `impact`. The user ticks the confirmation boxes and submits. Past about 8000 characters the URL returns 414: drop `evidence` and let the user paste it in.

## Common mistakes

- Posting before the user has read the final text.
- Pasting the whole `diagnostics_run` output, which leaks the team and project list.
- A title like "generation is broken": name the surface, the symptom, and the condition.
- Three problems in one issue: each needs its own reproduction and its own close.
- Reporting the hypothesis ("the API is down") instead of the observation. Observation first, hypothesis last and marked as one.
