---
name: scenario-consistency
description: "Use when one look must hold across Scenario generations: one character across scenes, a turnaround, or a video animated from its references, one product across angles, one style across icon sets, a character from an uploaded drawing, a variant off an approved baseline, or deciding when references stop scaling and a trained model is due. Triggers: make this match, same character, on-model, reference to video, style reference. Keywords: consistency, identity, control map, seed, LoRA."
license: MIT
---

# Scenario Consistency

## Overview

"Make variant two look exactly like variant one except for X" is the most repeated creative ask, and agents reach for seeds, which do not solve it. Consistency comes from what you feed the model, in rising order of durability: a prompt baseline, reference images, a style reference, a control map, a trained model. The same references carry a character into video. Connection and the core loop: see the `scenario` skill; training: see `scenario-model-training`; creating and filing a named character or prop library, with its sheets: see `scenario-identity-library`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Technique                  | Holds                             | Effort | Reach for it when                     |
| -------------------------- | --------------------------------- | ------ | ------------------------------------- |
| Baseline-plus-delta prompt | identity, framing, palette        | low    | always, it is the floor               |
| Reference image input      | identity and world                | low    | a set of scenes or angles             |
| Style reference input      | rendering style, not a subject    | low    | icon sets, UI, an illustration series |
| `asset_detect` control map | pose, geometry, composition       | medium | the layout must not move              |
| Reference-to-video         | identity through motion           | medium | the character or product has to move  |
| Seed reuse                 | one image's exact roll            | low    | re-rolling a single generation        |
| Trained model              | a house style, or a cast at scale | high   | references stop scaling (see below)   |

Scenario's published pipeline guidance: generate one strong reference image, pass it as an image input to every scene generation, and prefer models with the most reference-image slots.

## The baseline-plus-delta prompt

Write out everything that must **not** change, then put the single change in a final clause. Keep the prompt byte-identical between runs and edit only that clause.

Enumerate specifics: subject geometry, camera height and angle, subject size and position in frame, lighting direction, each named sub-element and where it sits, palette by name or hex, and embedded text. Look at the baseline first (`asset_display`): you cannot enumerate a shade you have not seen, and vague anchors drift.

Attach the approved baseline as a reference image alongside it. Image models converge on `referenceImages`, but cap, requiredness, and cardinality all come from `model_schema_get`, and on some models the field is a single scalar file. A scalar `image` plus `strength` is img2img, not a reference slot: it anchors composition along with identity, and at the default strength a plain-background anchor overrides a whole-scene delta, so a scene set needs a schema with a true reference field. Wrap an array only where the schema says `array: true`, even a lone asset as `["asset_..."]`: a bare string is silently dropped and the run succeeds while ignoring it. State each reference's role in the prompt. A pool of approved on-model shots fills the remaining slots: curate it as a collection (catalog tools, write lane) and retrieve it with `search` `filters={"collection_ids": [...]}`.

The anchor can be an upload: the user's character art, sketch, or product photo goes up with `upload_asset` plus `upload_asset_complete` (see `scenario`) and rides the reference field like any approved hero. `asset_describe` (see `scenario-asset-analysis`) turns it into a promptable synthesis to seed the baseline enumeration.

A set takes one `model_run` per item: a batch-count field repeats one prompt and cannot carry a per-item delta clause.

## Locking a style without a subject

A style reference is a different slot from a subject reference, and a few image models expose it: at authoring time one family took one to ten images as `styleReferenceImages`, built a private style from them for a small extra charge, and returned a reusable style id in the job output that later runs pass as `styleId` instead of the images (the two fields were mutually exclusive), with `styleMatch` choosing `precise` or `flexible` adherence. It holds rendering, palette, and line, not a character: pair it with a subject reference or the baseline enumeration for identity. Find such members with `recommend` and the style need in the user's own words, then confirm the field on `model_schema_get`. Palette fields that take RGB triples (`colors`) are preferences, not constraints, so keep the hex values in the prompt as well.

## Locking structure with a control map

Generate the map and pass it as a conditioning input. Never extract it for the attribute that is the delta: a pose map from the approved image locks the pose you were asked to change; a pose set needs its map from a target-pose image, or none.

`asset_detect` takes an `asset_id` and a `modality` from `canny`, `depth`, `grayscale`, `lineart_anime`, `mlsd`, `normal`, `pose`, `scribble`, `segmentation`, `sketch` (`remove_background` defaults true). Catalog-only and write lane, despite the docs page grouping it under Analysis: run it via `scenario_tool_execute_write`.

The control block (`controlImage`, `controlModality`, `controlStrength`, `controlStart`, `controlEnd`) exists only on models listing `controlnet` in `capabilities`: check before planning around it; models without it take reference images. `controlModality` allows `canny`, `tile`, `depth`, `blur`, `pose`, `gray` and `low-quality`: only canny, depth and pose map across, `grayscale` becoming `gray`. `controlStrength` defaults to 0.7 with a recommended 0.3 to 0.8 band: near 0.7 for canny, depth and tile, 0.8 to 0.9 for pose, gray and blur, rigid above 0.9. Strength is how much, `controlStart` and `controlEnd` are when: `controlEnd` near 0.65 locks composition early, then releases so the prompt refines detail.

## Carrying identity into video

Reference-to-video members animate the subject the references show, with no first frame locking composition. The catalog has no reference-to-video capability value: these members are tagged `img2video`, so `recommend` with `capability="img2video"` and the consistency need in the user's own words ("the same character as in these images"), then confirm on `model_schema_get` that the pick carries a multi-slot `referenceImages` array (7 to 9 slots on the leading members at authoring time, one of them billing slots past the first four) and, when a motion should be copied, a `referenceVideo` or `referenceVideos` slot (capped between 3 and 15 seconds, billed per second of upload on some). `image`, the first-frame anchor, and the reference arrays are mutually exclusive on several families: a reference run opens free, and pinning the opening frame is a different member. Fill the slots from the library: the hero and two or three approved on-model shots per `scenario-identity-library`, as individual shots, never the turnaround sheet. Prompt the action, not the look: some schemas address uploads by order ("Image 1 turns toward the camera, moving as in Video 1"), others state that the subjects appear whether or not a prompt is given, and on all of them re-describing the character fights the images. Per-family contracts and prompt syntax: the video model-family skills that `scenario-video` lists. Judge identity across the whole clip: `asset_get` returns `firstFrame` and `lastFrame` as free asset ids, and a drift that fades in mid-shot passes both, so sweep the frames (the extractor tool, per `scenario-video`) before the clip ships.

## When references stop scaling

Reference-first is the published order and the cheaper one, so exhaust it before training. Training pays back when one character recurs across hundreds of images, when four or more identities must share scenes, or when every run needs the same rendering style whatever the subject. Train one model per recurring character and a separate one for the style: a single model carrying both drifts on whichever it saw less of. Multi-character scenes composite rather than co-generate: reference slots split attention, so generate each identity alone against its baseline, then place them together with the edit workflows in `scenario-image-editing`. Dataset size, base choice, and the quote-before-launch rule: `scenario-model-training`. A trained model never runs by its own id (`runs_as` and `run_with`, see `scenario`), and it still takes the baseline-plus-delta prompt: training lightens the enumeration, not the delta discipline.

Sprite sheets and animation frames are the hard case: adjacent frames from a general image model drift in proportion, scale, and silhouette, which an engine exposes at once. Frames of one character come from the video lanes in `scenario-sprite-animation`, where one render holds the identity instead of a generation per frame.

## Worked example: five poses of one mascot

1. `asset_display` the approved hero (`asset_hero`) and write its baseline: the full must-not-change enumeration above.
2. `recommend` with the task's own words as `prompt` (`search` only for a named family), preferring models with reference-image slots, then `model_schema_get`: the reference field's name, cap, cardinality, requiredness. No reference field in the schema disqualifies the candidate: go back to the ranked list, and when that holds nothing reference-capable either (`recommend` ranks community fine-tunes and can miss first-party models), take a family name from a sibling model-family skill (`scenario-gemini-image`, `scenario-seedream`) and `search` for it.
3. One `model_run` per pose, five in all: the byte-identical baseline, the pose alone in the final clause, the hero in the reference field shaped as the schema says: `["asset_hero"]` only under `array: true`. No seed. No control map: a pose map from the hero locks the pose being changed.
4. `jobs_wait` on the five jobs, re-calling with `pending_job_ids` until done. `asset_display` each against the hero; fix drift by tightening the enumeration, not by chaining outputs.

## Common mistakes

- Reaching for a seed to make two prompts match: it reproduces one generation and transfers nothing. Leave it unset across a set; set one only to re-roll a single unchanged prompt.
- Writing "same as before": there is no memory between calls; restate the baseline in full each time.
- Chaining a set output to output: drift compounds. Anchor every item to the same approved baseline.
- Training for a one-off: one character in one scene is a reference job, and a recurring cast at scale is the training case above, one model per character plus one for the style.
- Assuming `asset_detect` modality names are valid `controlModality` values.
- Passing the turnaround sheet as a reference-to-video input: the clip animates a grid. Reference slots take individual approved shots.
- Re-describing the character in a reference-to-video prompt: the images carry the look; the prompt carries action, camera, and timing.
