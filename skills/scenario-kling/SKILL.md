---
name: scenario-kling
description: "Use when generating or editing video with Kling models on Scenario via MCP: text-to-video, image-to-video with start and end frames, multi-shot scenes, reference-to-video with elements, images, and clips, prompt-based video editing, motion control, lipsync, talking avatars, native audio and dialogue, 4K tiers, or replacing a deprecated Kling member. Keywords: Kling V4, 4.0, Flash, V3, O1, 2.6, 2.5, Omni, Kuaishou, T2V, I2V, R2V, V2V."
license: MIT
---

# Scenario Kling Video

## Overview

Kling, Kuaishou's video family on Scenario, ships as specialists. At authoring time V4 (T2V, I2V,
R2V, Video Edit, Flash) is current, beside V3 Omni, the V3 4K lines, V3 motion control, O1 Reference
Video, Lipsync, and AI Avatar; the other V3, O1, and 2.x members are deprecated. Treat
`model_schema_get` as the contract: the same parameter changes shape, default, and legality between
members. Kling Video to Audio is audio output (`scenario-audio`); Kling image members belong to
`scenario-image`.

Connection and the core loop: see the `scenario` skill in this repo; model-agnostic video work: the
`scenario-video` skill. If a sibling skill named here is missing from your available skills, load it
with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

## Skip deprecated members

- A deprecated member carries the tag `Deprecated` plus `deprecated:<successor id>`, naming the
  member to run instead. `search` hits list their `tags`.
- `search` ranks by score, and at authoring time deprecated V3 members outrank every V4 one. Never
  take the first hit unread.
- Exclude them with the raw `filter` string, `filter='NOT tags = "Deprecated"'`; structured
  `filters` only include.
- A request or saved payload names a deprecated id: propose the successor with the payload rebuilt
  from its schema, and run it only once the user agrees. Unattended, stop and report the proposal.
- The successor covers the lane, not every field: a V3 I2V payload with `elements` belongs on V4
  R2V, since V4 I2V takes none. R2V takes no `endImage`, so the proposal names any field it drops.

## Quick reference

Pick by job; discover ids with `search` (`target="models"`, `query="kling"`, `public=true`, the
filter above):

| Job                                       | Members                                                   |
| ----------------------------------------- | --------------------------------------------------------- |
| Text or a still to video, up to 30 s      | V4 T2V, V4 I2V (optional `endImage`)                      |
| Fast 720p drafts, 3 to 20 s, any input    | V4 Flash                                                  |
| Consistent characters, products, or style | V4 R2V (`images`, `elements`, `referenceVideos`)          |
| Edit or restyle footage by prompt         | V4 Video Edit, Omni (`videoReferenceType: "base"`)        |
| New scene guided by a source clip         | V4 R2V, O1 Reference Video, Omni (`"feature"`)            |
| Native 4K (V4 stops at 1080p: upscale)    | V3 T2V 4K / I2V 4K, Omni (`mode: "4k"`)                   |
| Motion from a video onto a character      | Motion Control (V3 Pro / Std)                             |
| Talking head                              | AI Avatar (image plus audio), Lipsync (video plus speech) |

V4 contract (live schemas, caps at authoring time):

- T2V, I2V, and R2V take `prompt` or `multiPrompt`; a set `multiPrompt` replaces the prompt. It is
  an array of `{prompt, duration}` shots (512 characters each), and the clip lasts their sum.
- `duration` is a number, 3 to 30 (1 to 30 per shot; Flash 3 to 20). Video Edit alone takes a
  string, `""` by default to match the source.
- `resolution` is `720p` or `1080p` (default); Flash has none and outputs 720p. I2V follows the
  start image's aspect ratio and takes no `aspectRatio`.
- R2V caps: `images` 10 (a `startImage` counts, with no stated tag number), `elements` 7,
  `referenceVideos` 5 of 3 to 30 s. `aspectRatio: "auto"` follows the references.
- Video Edit requires `prompt` and `video` (3 to 30 s, 700 to 4553 px per side). `images` and
  `elements` keep the R2V caps.
- A V4 element is a `frontalImage` plus 1 to 3 `referenceImages`, both required. With one photo of
  the subject, pass it in `images` and tag it `@Image1` instead.
- Tags bind by order. R2V and Video Edit write `@Image1`, `@Video1` (the edited clip), `@Element1`.
  Flash writes `@image_1` and `@video_1`, counting the start image and the edited video first.
- Flash requires `prompt`. Images total 10 with `startImage`; videos total 5 and 20 s with the
  edited `video`, whose length and aspect the output keeps.

Current V3 and O1 traps:

- The V3 4K lines take `prompt` or `multiPrompt`, never both, with `shotType` (`customize` or
  `intelligent`) beside `multiPrompt`. Omni keeps `prompt` required; its `multiPrompt` is a JSON
  string of up to 6 shots whose durations sum to `duration`.
- `duration` is a string enum on the V3 4K lines (to 15) and O1 Reference Video (to 10): `"5"`, not
  `5`. Omni takes a number, 3 to 15.
- V3 I2V 4K takes up to 3 `elements`: a `frontalImage` plus up to 4 `referenceImages`, each
  optional, or a `video` defining the element.
- Budgets shrink beside a video: O1 Reference Video takes 4 total (elements plus images), and Omni's
  `referenceImages` drops from 7 to 4 next to `referenceVideo`. Omni prompts use `<<<image_1>>>`.
- A reference clip runs 3 to 10 seconds on Omni and O1 Reference Video, 2 to 10 on Lipsync (trim
  first, per `scenario-video`). Omni's `referenceVideo` defaults to `"feature"`, lending style and
  camera to a new clip; `"base"` edits the clip and ignores `duration`; `4k` mode refuses it.
- `cfgScale` (V3 4K, 0 to 1, default 0.5): raise toward 0.8 for storyboard fidelity, drop toward 0.3
  to let the model invent.

Prompt in director order: scene, subject, action, one camera move, then audio and style. Natural
sentences beat tag lists, and complex scenes hold together near 5 seconds, not 30.

## Audio differs per generation

- V4 has no audio switch. The T2V, I2V, R2V, and Flash descriptions promise native audio.
- Only T2V's description names multilingual dialogue at authoring time. Before counting on
  non-English speech elsewhere, read the hit's description; the fallback is Lipsync with a recorded
  track.
- `generateAudio` defaults true on the V3 4K lines, billed per second either way, and false on Omni,
  where a reference video refuses it.
- V3 voice output is Chinese and English; other languages auto-translate to English.
- Put dialogue in quotes in the prompt; on V3, lowercase English speech and uppercase acronyms.
- O1 Reference Video carries source audio via `keepAudio`.
- For new speech on existing footage use Lipsync: an audio file, or `text` with a `voiceId`, never
  both.

## Motion control reads two inputs

V3 Pro and Std Motion Control require a character `image` and a driving `video`.
`characterOrientation` names which input holds the character; defaults differ (Std `video`, Pro
`image`), so set it explicitly. `keepOriginalSound` decides whether the source audio survives.

## Worked example: two-shot character clip from a still

1. `search` with `target="models"`, `query="kling reference"`, `public=true`, and
   `filter='NOT tags = "Deprecated"'`. Pick `model_kling-v4-r2v` (a live hit at authoring time:
   re-discover each session).
2. `model_schema_get` with that id: multiPrompt shape, numeric durations, element and image caps.
3. `upload_asset` the start frame, the character's frontal photo, and one side view (see the
   `scenario` skill).
4. `model_run` with that `model_id`, `dry_run=true`, and
   `parameters={"startImage": "asset_s", "multiPrompt": [{"prompt": "Wide shot, @Element1 crosses the plaza, slow dolly-in", "duration": 5}, {"prompt": "Close-up, @Element1 smiles and says: 'we made it'", "duration": 4}], "elements": [{"frontalImage": "asset_f", "referenceImages": ["asset_p"]}], "resolution": "720p"}`
   for the cost estimate; re-estimate after changing durations or resolution.
5. Proceed only within the task's stated budget; otherwise report the estimate and stop. Repeat
   `model_run` with `wait=false`, then `jobs_wait` with the returned job id, re-called with
   `pending_job_ids` on timeout, never a second `model_run`.
6. `asset_display` the output and review both shots with sound.

## Common mistakes

- Porting a V3 or 2.x payload to V4: `generateAudio`, `cfgScale`, `negativePrompt`, and `shotType`
  do not exist there, and durations are numbers outside Video Edit. Rebuild from its schema.
- Carrying one member's caps to another: 30 seconds, 4K, `elements`, and tag syntax each change
  between members.
- Compound camera moves ("dolly in while orbiting"): one dominant move per shot; split the rest
  across `multiPrompt` shots.
- Overloaded negative prompts on V3 4K: a short artifact list steers; a long one stiffens motion.
- Prompting Omni `base` to extend a clip: it edits in place. Continue from the clip's `lastFrame` id
  (`asset_get`) as the start frame of a new I2V run, then concatenate, per `scenario-video`.
- Skipping `dry_run` on 4K or avatar runs: at authoring time 4K ran several times Standard and
  avatar cost spanned a 100x range. Iterate at 720p or on Flash; no current Kling schema carries a
  seed, so a 4K re-run of the keeper is a new take, while upscaling it (`scenario-video`) keeps the
  take.
