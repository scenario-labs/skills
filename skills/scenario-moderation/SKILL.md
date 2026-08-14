---
name: scenario-moderation
description: "Use when a Scenario generation is blocked, refused, or comes back with a moderation or sensitive-content error, when the same prompt succeeds on one model and fails on another, when prompts describing a team's own characters, weapons, or props get flagged, or when a run passes one time and fails the next with no real change. Keywords: blocked prompt, content moderation, sensitive content, flagged, refused generation, provider filter, false positive."
license: MIT
---

# Scenario Blocked Generations

## Overview

Content filters run on the model provider's side, not on Scenario. A block is therefore a property of the model that was picked, not of the account or of the prompt in the abstract, and the same prompt usually passes on other models in the catalog. Treat a block as a routing problem first and a wording problem second. This skill is about false positives on content a team is entitled to make; it is not a way to produce content a provider prohibits. Core loop: see the `scenario` skill.

## Quick reference

| Step                    | Call                                                                                   |
| ----------------------- | -------------------------------------------------------------------------------------- |
| Read the actual error   | `job_get` with `verbose=true`, or the `error` and `hint` fields on the `jobs_wait` row |
| Find alternative models | `search` (`target="models"`, `public=true`), or `recommend` with the same `capability` |
| Price an alternative    | `model_run` with `dry_run=true`                                                        |
| Re-test the same intent | One `model_run` per candidate, prompt unchanged, so the model stays the only variable  |

Three failures look alike and only the first is about wording: a provider moderation block, a 403 Forbidden error (the plan does not include that model), and a model a team has put on its own blocklist. Read the error before rewriting anything.

## Why legitimate prompts get blocked

Two triggers stack, and either alone often sits under the threshold:

- **Recognizable characters.** Automated filters react to character names and signature traits they recognize. They cannot know who owns the IP, so a team's own characters are flagged like anyone else's.
- **Intensity-coded language.** Words chosen to convey scale or drama ("oversized", "huge", "massive") read as violence in aggregate, even when the subject is a prop.

With both present the prompt sits near the threshold, which is why the same intent passes one run and fails the next: a small rewording tips it over. An upstream LLM step that rewrites prompts is a frequent cause, because it leans harder on intensifiers to solve an unrelated problem and re-introduces the block on every run.

## Recovery, cheapest first

1. **Switch model.** Usually needs no prompt edit at all. Run the unchanged prompt against two or three alternatives at comparable cost; if they pass, the filter was that provider's, not the content's.
2. **Describe scale by proportion, not intensity.** "The staff reaches shoulder height" or "the blade is about as long as the forearm" carries the same art direction as "oversized" without the violence coding.
3. **Soften recognizable names in the direct model input.** Describe the design in the prompt and carry identity with a reference image instead, which holds the look better anyway (see `scenario-consistency`).
4. **Constrain any upstream rewriter.** When an LLM node writes the final prompt, put steps 2 and 3 in its instructions, or the block returns on the next run.

Then stop. If every model refuses and one honest rewrite has not cleared it, the filter is reading something real: say so and hand it back to the user. Grinding out variants until one slips through is evasion, not art direction.

## Worked example: a flagged weapon prop

The studio's own character is named Onyx, and "Onyx's oversized war hammer, huge spiked head" comes back flagged.

1. Read the error: `job_get` with `verbose=true`, or the `error` and `hint` fields on the `jobs_wait` row. It names moderation, so this is a filter, not a plan restriction or a team blocklist.
2. `search` (`target="models"`, `public=true`) for two alternatives with the same capability, price each with `model_run` and `dry_run=true`, then run the unchanged prompt on each. One passes: done, the filter belonged to the first provider.
3. Suppose all of them refuse. Rewrite once, by proportion and without the name: "a war hammer as tall as its wielder's shoulder, spiked head two hand-spans across", and carry Onyx's look with a reference image (see `scenario-consistency`).
4. Still refused everywhere: stop and tell the user what the filter appears to be reacting to.

## Common mistakes

- Retrying the identical prompt: near-threshold prompts pass intermittently, so a retry that happens to work has fixed nothing.
- Rewriting wording before trying another model: wording changes are slow and lose art direction, switching models is one call.
- Assuming IP ownership exempts a prompt: the filter is automated and sees only the text and images sent to it.
- Reporting a block as a Scenario fault: confirm other models refuse it too, then file it with `scenario-report`.
- Escalating to a pricier model expecting a laxer filter: cost and moderation strictness are unrelated.
- Reading an empty model list as moderation: a team blocklist or a plan restriction removes models before any prompt is judged.
