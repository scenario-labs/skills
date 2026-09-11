---
name: scenario-moderation
description: "Use when a Scenario generation is blocked, refused, or returns a moderation or sensitive-content error, when a video is rejected after rendering or its audio track is flagged, when an output is flagged for likeness to a real person or for IP and copyright detection, when the same prompt passes on one model and fails on another, or when a team's own characters, weapons, or props get flagged. Keywords: blocked prompt, content moderation, refused generation, provider filter, false positive."
license: MIT
---

# Scenario Blocked Generations

## Overview

Three gates can stop a generation, and only one of them reads the prompt. Content filters run on the model provider's side, not on Scenario, so a provider block is a property of the model that was picked and the same prompt usually passes elsewhere in the catalog. IP Detection is the team's own gate, switched on in team settings, and no model switch clears it. Plan and blocklist restrictions remove models before any prompt is judged. Treat a block as a routing problem first and a wording problem second. This skill is about false positives on content a team is entitled to make; it is not a way to produce content a provider prohibits. Core loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step                    | Call                                                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Read the actual error   | `job_get` with `job_id`: the row carries `error` and `hint`, plus `modelId` (the model to exclude) and `cuCost` (what the failed run charged); `verbose=true` adds `metadata.input` with the exact prompt the job ran. Or read `error` and `hint` off the `jobs_wait` row                                                                                                                             |
| Read the team's gate    | `teams_list`: the team row carries `ipDetectionEnforcement`; anything but `disabled` means a block naming IP or copyright can be the team's own policy                                                                                                                                                                                                                                                |
| Find alternative models | `recommend` with the failed job's `capability` (`txt2img` for a text-to-image block, `img2img` with a reference in play, `img2video` for a clip animated from a still) plus the user's own words; set `max_cost_cu` a little above the failed row's `cuCost` per asset to stay in the cost band, and drop the failed `modelId` from the ranking yourself, since `recommend` has no exclusion argument |
| Price an alternative    | `model_run` with `dry_run=true`                                                                                                                                                                                                                                                                                                                                                                       |
| Re-test the same intent | One `model_run` per candidate, prompt unchanged, so the model stays the only variable                                                                                                                                                                                                                                                                                                                 |

Four failures look alike and only the first is about wording: a provider moderation block, an IP Detection block from the team's own settings, a 403 Forbidden error (the plan does not include that model), and a model a team has put on its own blocklist. Read the error before rewriting anything.

## Why legitimate prompts get blocked

Three triggers stack, and each alone often sits under the threshold:

- **Recognizable characters.** Automated filters react to character names and signature traits they recognize. They cannot know who owns the IP, so a team's own characters are flagged like anyone else's.
- **Intensity-coded language.** Words chosen to convey scale or drama ("oversized", "huge", "massive") read as violence in aggregate, even when the subject is a prop.
- **Real-person likeness.** Filters watch for resemblance to public figures in the output as well as names in the prompt, so a character sheet the platform itself generated can be refused as a reference on the next run, and a celebrity comparison in the prompt ("built like a heavyweight champion") is a name by another route.

With two present the prompt sits near the threshold, which is why the same intent passes one run and fails the next: a small rewording tips it over. An upstream LLM step that rewrites prompts is a frequent cause, because it leans harder on intensifiers to solve an unrelated problem and re-introduces the block on every run.

## Filters differ by provider, not by price

Scenario's public content policy guide ranks the providers: Google's models (Gemini, Veo) block the most brand and character references, ByteDance, OpenAI, Ideogram and Hunyuan sit in the middle, and FLUX and Recraft are the most permissive. `recommend` ranks by measured performance, not by filter strictness, so an alternative from the same provider inherits the same filter: take the next candidate from a different provider, and read `modelId` on the failed row to know which one that was: the provider is usually legible in the id, and when it is not, `model_get` (catalog-only, read lane) returns the record with `complianceMetadata.modelProvider`.

## Video and audio blocks

Video changes the economics of a block. Several providers moderate the finished render, so a rejected clip has already been rendered in full, and a retry of the identical payload renders it again. Read `cuCost` on the failed row before anything else: a policy block is typically refunded, and failed jobs are reimbursed except xAI generations stopped by moderation (see `scenario`), but the reservation is not always released at once, so report the figure, point the user at `usage` later, and file the `job_id` with support if a charge stands. Then switch provider as above, prompt unchanged.

The audio track is judged on its own. `OutputAudioSensitiveContentDetected` on an audio-enabled video run means the soundtrack tripped the filter, and the usual cause is a named instrument or genre, even inside an exclusion: "no music" and "a distant guitar" have both failed where "room tone, footsteps, a single voice" passed. Describe diegetic sound positively and name nothing to exclude; when the clip needs no sound, turn the audio field off where the schema exposes one (`generateAudio` on many families) rather than prompting silence.

## IP Detection is the team's own gate

Teams on plans with IP Detection can have Scenario check outputs against protected IP and enforce a policy on the result. The setting rides the `teams_list` row as `ipDetectionEnforcement`; when it is anything but `disabled`, a block or flag naming IP or copyright is the team's decision, not the provider's, so switching models re-runs the same check and rewording only helps when the output genuinely resembles someone else's property. A copyright warning attached to a completed output is informational. Recovery is a conversation, not a call: tell the user which gate fired; a team admin owns the setting, and verified IP holders who keep hitting false positives on their own licensed property have an escalation path through their Scenario account manager.

## Recovery, cheapest first

1. **Switch provider.** Usually needs no prompt edit at all. Run the unchanged prompt against two or three alternatives from other providers at comparable cost; if they pass, the filter was that provider's, not the content's.
2. **Describe scale by proportion, not intensity.** "The staff reaches shoulder height" or "the blade is about as long as the forearm" carries the same art direction as "oversized" without the violence coding.
3. **Soften recognizable names in the direct model input.** Describe the design in the prompt and carry identity with a reference image instead, which holds the look better anyway (see `scenario-consistency`). Drop real-person comparisons the same way.
4. **Constrain any upstream rewriter.** When an LLM node writes the final prompt, put steps 2 and 3 in its instructions, or the block returns on the next run.

Then stop. If every provider refuses and one honest rewrite has not cleared it, the filter is reading something real: say so and hand it back to the user. Grinding out variants until one slips through is evasion, not art direction.

## Worked example: a flagged weapon prop

The studio's own character is named Onyx, and "Onyx's oversized war hammer, huge spiked head" comes back flagged.

1. Read the error: `job_get` with `job_id` (`verbose=true` for the exact prompt the job ran), or the `error` and `hint` fields on the `jobs_wait` row. It names moderation, so this is a provider filter, not a plan restriction, a team blocklist, or IP Detection (`teams_list` shows `ipDetectionEnforcement: "disabled"`).
2. `recommend` with the failed job's `capability` (`txt2img` here) and the user's own words, take two alternatives from providers other than the failed `modelId`'s, price each with `model_run` and `dry_run=true`, then run the unchanged prompt on each. One passes: done, the filter belonged to the first provider.
3. Suppose all of them refuse. Rewrite once, by proportion and without the name: "a war hammer as tall as its wielder's shoulder, spiked head two hand-spans across", and carry Onyx's look with a reference image (see `scenario-consistency`).
4. Still refused everywhere: stop and tell the user what the filter appears to be reacting to.

## Common mistakes

- Retrying the identical prompt: near-threshold prompts pass intermittently, so a retry that happens to work has fixed nothing, and on video it renders the whole clip again first.
- Rewriting wording before trying another provider: wording changes are slow and lose art direction, switching models is one call.
- Switching within the same provider: sibling members share the filter; the next candidate comes from another provider.
- Naming a genre or instrument to exclude it in an audio-enabled prompt: the exclusion is what the audio filter reads.
- Assuming IP ownership exempts a prompt: the filter is automated and sees only the text and images sent to it.
- Reading an IP Detection block as a provider filter: the team's gate re-runs on every model; the recovery is the team admin, not a model switch.
- Reporting a block as a Scenario fault: confirm other providers refuse it too, then file it with `scenario-report`.
- Escalating to a pricier model expecting a laxer filter: cost and moderation strictness are unrelated.
- Reading an empty model list as moderation: a team blocklist or a plan restriction removes models before any prompt is judged.
