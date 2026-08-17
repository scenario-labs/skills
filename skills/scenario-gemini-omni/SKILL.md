---
name: scenario-gemini-omni
description: "Use when generating or editing video with Gemini Omni models on Scenario via MCP: text-to-video, image-to-video from a first frame, reference-to-video keeping a character, product, or place consistent, restyling existing footage by prompt (season, wardrobe, art style) with motion preserved, native audio with dialogue and ambience in one pass, or picking between first-frame and reference conditioning. Keywords: Gemini Omni Flash, Google, T2V, I2V, V2V, video2video, subject consistency."
license: MIT
---

# Scenario Gemini Omni Video

## Overview

Gemini Omni, Google's video family on Scenario, splits its modes across three catalog members instead of folding them into one model: a text and first-frame generator (ranked first for text-to-video in public arena voting at authoring time), a reference-to-video member for subject consistency, and an edit member that restyles existing footage. Every member generates audio in the same pass. Pick the member by mode with `search`, then treat `model_schema_get` as the contract. Gemini image models are the `scenario-gemini-image` skill's domain; Gemini TTS belongs to audio.

Connection and the core loop: see the `scenario` skill; model-agnostic video work: the `scenario-video` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

Three members, one mode each (names from the live schemas):

| Member             | Mode                | Inputs                                                                            |
| ------------------ | ------------------- | --------------------------------------------------------------------------------- |
| Gemini Omni        | text or first frame | `prompt` and/or `image`, plus optional `referenceImages` (up to 7)                |
| Reference-to-Video | consistent subjects | `referenceImages` required (1 to 7), `prompt` optional                            |
| Edit               | restyle a clip      | `video` and a change `prompt`, both required; optional `referenceImages` (1 to 5) |

At authoring time both generators took `duration` 3 to 10 seconds (default 8) and `aspectRatio` `16:9` or `9:16`, at 720p. Edit exposes neither knob: length and shape follow the source clip. No seed, resolution, or negative-prompt parameter exists anywhere in the family. Cost moves with `duration`, a first-frame `image`, Reference-to-Video's references, and Edit's source clip; Edit spanned the family's widest cost range at authoring time and its jobs ran about twice as long, so `dry_run` before editing anything long.

## Sound is prompted, not switched

No member has an audio parameter: every clip arrives with generated dialogue, ambience, and effects, and the prompt is the only lever. On the generators, end the prompt with an explicit audio line naming what should be heard ("crackling campfire, distant owls") and put spoken words in quotes; leave it out and the model chooses for you. On Edit, never prompt audio: it regenerates to match the new look on its own.

## Identity from images, change from words

Reference-to-Video takes the subject's look from `referenceImages`, and re-describing it in the prompt fights the images. Call the subject "the character" or "the product" and spend the words on action, setting, camera, and sound; several angles of one subject tighten the hold, distinct subjects share one scene, and with no prompt at all the subjects still appear. There is no first-frame anchor here: when the clip must open on an exact composition, pass that still as `image` on the base member, which also accepts references alongside it.

Edit is the inverse: motion, camera path, and timing are locked from the source `video`, only the look moves. Lead the prompt with the change ("make it winter", "swap the red car for a vintage blue Beetle"), name the target concretely, and never ask for new choreography, cuts, or camera moves: those instructions will not take.

## Worked example: a mascot short with a consistent character

1. `search` with `target="models"`, `query="gemini omni"`, `public=true`. Pick the member by mode, here `model_google-omni-flash-r2v` (a live hit at authoring time: re-discover each session).
2. `model_schema_get` with that id: required fields, caps, and defaults before anything else.
3. `upload_asset` two or three angles of the mascot (see the `scenario` skill) to get asset ids.
4. `model_run` with that `model_id`, `dry_run=true`, and `parameters={"prompt": "The character skips across a rain-slick plaza, catches a falling leaf, and holds it up in triumph. Overcast soft light, low tracking shot. Audio: light rain, footsteps on wet stone, one bright chirp.", "referenceImages": ["asset_a", "asset_b"], "duration": 8, "aspectRatio": "16:9"}`; references and duration move the cost, so re-estimate after changing either.
5. Repeat `model_run` with `wait=false`, then `jobs_wait` with the returned job id, re-called with `pending_job_ids` on timeout, never a second `model_run`.
6. `asset_display` the output and review it with sound: the audio is part of the deliverable.

## Common mistakes

- Describing the reference subject's appearance in the prompt: identity comes from the images; write action and setting around "the character".
- Asking Edit for new motion, cuts, or re-timing: they are locked to the source; prompt only the look change.
- Passing `duration` or `aspectRatio` to Edit: neither is in its schema; the output follows the source clip.
- Hunting for an audio toggle: none exists; steer sound in the prompt or accept the model's choice.
- Restating a first-frame `image` as a static scene: describe the motion continuing from it.
- Packing a multi-scene story into one run: 3 to 10 seconds holds one continuous beat; sequence shots with the `scenario-video-assembly` skill.
