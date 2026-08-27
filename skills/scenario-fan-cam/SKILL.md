---
name: scenario-fan-cam
description: "Use when putting a person from a photo into live-broadcast crowd footage with Scenario: a stadium or arena fan-cam reaction, a jumbotron or kiss-cam moment, a spectator cutaway at a match or concert, a courtside or front-row sighting, or a personalized sports-TV still that then animates into video. Keywords: fan cam, crowd reaction, jumbotron, stadium screen, kiss cam, broadcast cutaway, spectator, crowd shot, sports TV, courtside, arena."
license: MIT
---

# Scenario Fan Cam

## Overview

A fan cam is a two-stage build: an identity-preserving image edit places the person into a 16:9 broadcast still, and image-to-video animates the approved still into a reaction. The uploaded photo is an identity reference, never a start frame: feeding it straight to a video model animates a portrait, not a broadcast. Stage one is cheap and stage two is not, so the still carries every decision worth approving.

Use only photos of the user or of people who gave them permission; refuse celebrity or stranger insertions. Real faces also trip provider filters more than most subjects: on a block, see `scenario-moderation`. Connection and the core loop: see the `scenario` skill in this repo. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

Discover ids with `search` (`target="models"`, `public=true`); never assert one as a constant.

| Stage             | What happens                                                                           | Detail                                             |
| ----------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 1. Identity still | Image-edit member (query `"image edit"`) composites the person into a 16:9 crowd frame | `scenario-image-editing`, `scenario-consistency`   |
| 2. Still gate     | Likeness checked against the photo before any video money is spent                     | `scenario-asset-analysis`                          |
| 3. Animate        | Image-to-video from the approved still, reaction beats, one camera move                | `scenario-kling`, `scenario-video`                 |
| 4. Identity gate  | Frames extracted from the clip, compared to the approved still                         | `scenario-asset-analysis`                          |
| 5. Overlays       | Score strip, channel bug, lower third composited as post layers, never generated       | `scenario-text-overlay`, `scenario-video-assembly` |
| 6. Derivatives    | 9:16 and 1:1 social cuts off the 16:9 master                                           | `scenario-formats`                                 |

Broadcast grammar is what sells the shot, so prompt it explicitly at both stages: long-lens compression with the crowd defocused in front and behind, harsh stadium floodlight or arena strobe, slight motion blur, the camera hunting and reframing as it finds the subject. Keep the person mid-ground among other fans, off-center, at broadcast camera height. A centered, well-lit, eye-level subject reads as a photoshoot in a stadium, not a cutaway.

Give the reaction an arc rather than a state: oblivious, then noticing the camera or the screen, then the reaction the user asked for (cheering, laughing, disbelief, heartbreak). Multi-beat prompting per the video family's contract keeps the turn inside one clip.

## Worked example: caught on the stadium screen, 8 seconds

1. Collect the photo, the sport or event, venue mood, wardrobe, and the wanted reaction. `upload_asset` the photo once and reuse the returned asset id.
2. `search` `target="models"`, `query="image edit"`, `public=true`; pick a current identity-capable editor and read `model_schema_get` for its reference-image inputs (`scenario-image-editing` for the lane, `scenario-consistency` for reference discipline).
3. Edit prompt: "the person from the reference image seated mid-crowd at a floodlit football stadium, 16:9 television cutaway, long-lens crowd compression, no text, logos, or graphics in frame". Keep the plate text-free: overlays come later.
4. Gate the still: `asset_display` it for approval, and inventory the likeness (face geometry, hair, wardrobe) with the analysis lane from `scenario-asset-analysis`; unattended, that inventory stands in for the user's sign-off.
5. `search` `query="image to video"`, pick per `scenario-kling` or `scenario-video`, `model_schema_get`, then `model_run` with `dry_run=true` for the quote.
6. Run with the approved still as the start image and two beats: "she chats, unaware" then "she spots herself on the stadium screen, stands, and cheers", one slow reframing move, `wait=false`, then `jobs_wait` re-called with `pending_job_ids` on timeout, never a second `model_run`.
7. Extract frames from the clip and compare against the approved still; likeness drift fails the clip, and the retry starts from the same still, never from the drifted output.
8. Assemble per `scenario-video-assembly`: score strip and channel bug rendered by `scenario-text-overlay` as image layers in the safe corners. `asset_display` the master, then cut 9:16 per `scenario-formats`.

## Common mistakes

- Animating the uploaded photo directly: the mandatory stage is the broadcast still; skip it only when the user hands over an already approved 16:9 frame.
- Letting the image or video model render the scoreboard, channel bug, or jersey sponsor text: generated type drifts frame to frame; composite graphics in post on a text-free plate.
- Portrait staging: centered subject, flattering light, and empty seats around them break the documentary read; bury them in a reacting crowd.
- Judging likeness from one glance at the moving clip: drift hides between glances; run the frame-extract gate.
- Retrying from a drifted clip instead of the approved still: errors compound.
- Composing the master at 9:16: broadcast is 16:9; verticals are derivatives.
- A flat emotional state for the whole clip: without the notice-then-react turn, the result is a looping portrait, not a fan cam.
- Compound camera moves: one reframing drift; the crowd and the reaction supply the motion.
