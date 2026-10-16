---
name: scenario-reel-recast
description: "Use when recreating a trending reel, TikTok or Short with a different performer: the same dance, moves, timing and camera, performed by the user's own character from a reference sheet, optionally in another outfit or a redecorated room, keeping the original song in sync. Keywords: reel recast, trend remake, TikTok dance, replace the dancer, character swap, choreography transfer, video to video, keep the music, Seedance edit mode."
license: MIT
---

# Scenario Reel Recast

## Overview

A recast performs an existing reel again with a new performer. Seedance's edit mode takes the reel as `@video1` and keeps its choreography, timing, camera and framing, while the prompt changes who dances, what they wear and how the room is dressed. The performer is rendered at the reel's scale, so anything that brings its own camera breaks the result: a background plate shot from another angle produces a performer with wrong proportions. The song never goes through generation: lift it off the reel first, lay it back on the finals.

Recast only characters the user owns or has rights to, never a real person's likeness without their consent; clearing the song for where it ships is the user's call.

Edit mode, references and moderation: `scenario-seedance`. Variations, review, ranking and the 1080p finish: `scenario-seedance-drafts`. Plate edits: `scenario-image`. Timeline and sync: `scenario-video-assembly`. Connection and the core loop: `scenario`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step               | Call                                                     | Detail                                                                                                                     |
| ------------------ | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Upload             | `upload_asset`, `upload_asset_complete`                  | Then `asset_get`: `duration`, `frameRate`, and the `firstFrame` asset id the plate starts from                             |
| Keep the song      | `model_scenario-audio-extract`, `outputFormat: "wav"`    | Returns inline                                                                                                             |
| Mute the reference | `model_scenario-video-cut`, `preserveAudio: false`       | Returns inline; probe the download to confirm no audio stream remains                                                      |
| Room plate         | Image edit of the reel's `firstFrame` (`scenario-image`) | Optional; see Changing the room, and check it before any video spend                                                       |
| Recast drafts      | Seedance edit mode, `"draft": true`                      | `referenceVideos: [muted reel]`, `referenceImages` in tag order, `duration: -1`, `generateAudio: false`; see Prompt recipe |
| Pick and finish    | `scenario-seedance-drafts`                               | Review every take, complete only the picks                                                                                 |
| Song back          | `model_scenario-compose-video`                           | A video layer and an audio layer, both at `startTime: 0`                                                                   |

The three tool ids are fixed: each is Scenario's single deterministic tool for its job, so discovery would only re-derive them. Discover the Seedance member each session per `scenario-seedance`.

Plan from the output, not the source: at authoring time a 14.87 s, 30 fps, 720x1280 reel came back as 14.71 s at 24 fps (480x854 drafts, 1080x1920 completions), and a 15 s edit-mode draft priced 366 CU.

## Prompt recipe

This structure held identity, outfit and timing across three outfits and nine takes:

1. **The swap**: "Edit @video1: replace the dancing woman with the woman from @image1", plus "wearing the dress from @image2" or "and redecorate the room as shown in @image3" when those apply.
2. **The keep list**: "Keep from @video1 exactly: the room itself, the camera position, height, lens and framing, her size, proportions and position in the frame, the light, and the choreography with every movement, gesture and head turn at the same timing."
3. **The sheet binding**: "@image1 is a character reference sheet of her: use it for her face, hair and outfit. Take nothing else from @image1: no panels, labels or text." The whole sheet works as one reference: no cropping into panels. When another image supplies the outfit, bind the sheet to face and hair only, and the outfit image to "only the dress: nothing of the mannequin, the background, the logos or any text".
4. **Keeping the reel's outfit**: "replace only the dancing woman's face and hair", with the outfit listed under the keep list.
5. **Named fragile details**: hair ("tied high at the crown, hangs down her back, keeps the same length, sections and color from the first frame to the last, never falls forward over her shoulder or blends into the curtains"), accessories ("the gloves stay black with natural fingers"), and props. Unnamed, they drifted: lace gloves vanished from one take, and a long ponytail draped forward.

## Changing the room

Outcomes at authoring time, best first:

- **Redecorate the reel's own room: works.** Edit the `firstFrame` with that frame as the only reference: remove the dancer, keep walls, floor, window, camera and light, add the decoration in words, keep the center floor clear. Then overlay the plate on the frame locally (`ffmpeg -filter_complex "[0][1]blend=all_mode=average"`): walls, floor line and window must coincide, and the original dancer must fit the empty floor at her own size. Pass the plate as the last `referenceImages` entry: "this same room seen from this same camera, with only the decoration changed; the decorations are fixed props that stay in place behind her and never move, morph, multiply or overlap her."
- **A new location rebuilt from the frame**, the same single-reference edit with the place described in words: the camera held in the overlay, but the user rejected the result. Prefer redecorating.
- **A location plate from text-to-image**, or a plate edit given a second scene image as a reference: fails. The plate keeps its own camera (the second reference made the editor copy that scene's angle), Seedance renders the performer at the reel's scale on top of it, and the proportions break.

## Worked example: one reel, three outfits, a Halloween room

1. `upload_asset` the reel, `upload_asset_complete`, then `asset_get` it.
2. `model_run` the audio extractor and the muted cut. Download the cut and confirm it has a video stream only.
3. `recommend` with `capability="img2img"` and the decor in the user's words; edit the `firstFrame` as above, run the overlay check, and show the user the plate before any video spend.
4. Discover Seedance and `model_schema_get` it. `dry_run` one draft payload and quote N takes per outfit times that price.
5. Three payloads (the sheet outfit, an outfit image, the reel's own outfit), each sent N times with `"draft": true` and `wait=false`; `jobs_wait` all of them (7 to 8 minutes).
6. Give each draft a music review copy (step 8 recipe at the draft's length), then review per `scenario-seedance-drafts`, adding a timing check: the reel and the draft side by side at four matched timestamps.
7. Complete the picks with the draft job's own asset ids, never the music copies.
8. Compose each completion: the video and the extracted song as layers at `startTime: 0`, `durationMode: "custom"` at the completion's `duration`, `canvasMode: "custom"` at its size, `fps` at its frame rate. Measure sync on the download (see Common mistakes), then `asset_download`.

## Common mistakes

- Muting, extracting or muxing the song with local ffmpeg: each step has a tool model above. Local ffmpeg is for inspecting downloads.
- Writing the new performer into the plate: it then sits in the background as a second figure. The plate is the empty room.
- Spending on video before the plate passes the overlay check.
- Expecting the source's frame rate and exact length, or composing to the source's duration: take both from `asset_get` on the output.
- Shifting the song to line up with the reel's audio: line it up with the dance instead. At authoring time the extracted track ran 110 ms early and the recast dance 83 ms early, a net offset under one frame, so the track at 0 was right. Measure by cross-correlating the final's audio envelope against the reel's, and its frame-difference motion envelope against the reel's. The compositor moves layers in 0.1 s steps, coarser than such offsets.
- Re-generating the performer when only the room changes on an approved recast: confirm first which one the user wants kept.
