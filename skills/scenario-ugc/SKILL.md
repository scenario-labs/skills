---
name: scenario-ugc
description: "Use when producing UGC-style creator video with Scenario: a talking-head ad or testimonial from a portrait and a script, a founder clip, a product demo or unboxing, a reaction or before-after cut, a faceless voiceover over b-roll, or vertical social video for TikTok, Reels, or Shorts that must feel filmed on a phone rather than produced. Keywords: UGC, creator ad, talking head, testimonial, avatar, lipsync, founder video, social proof, faceless voiceover, organic, vertical video."
license: MIT
---

# Scenario UGC Creator Video

## Overview

UGC is a register, not a length: content that reads as a person talking into their own phone, not a brand talking through a camera crew. Everything in this skill serves that register, and most failures come from importing ad craft into it. This skill routes the production; mechanics live in the sibling skills named per lane. Connection and the core loop: see the `scenario` skill in this repo. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

Two rules are non-negotiable. The product is never generated: demo shots start from an uploaded photo or footage of the real product (`scenario-product-shots` for stills). And the words are never invented: no fabricated testimonials, review counts, metrics, medical or financial claims, or legal copy; speak only lines the user supplied or approved, and prefer observable statements ("the texture looks lighter") over claims ("this cures acne").

## Quick reference: route by speaker lane

Discover members with `recommend`, passing the lane's capability and the user's own words: it ranks by measured cost and latency and names the purpose-built pick, where a capability-worded `search` returns hundreds of keyword hits with nothing to choose between them. Read `next_step` before taking a pick, per the `scenario` skill. Keep `search` for a member you can already name. Never assert a generative model's id as a constant. Scenario's own single-purpose tool models are named outright below: there is exactly one of each, so discovering them would only re-derive a constant.

| Lane                                | Route                                                        | Contract                                              |
| ----------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------- |
| Portrait plus speech audio          | Talking-avatar members (`img2video`)                         | `scenario-kling`                                      |
| Existing footage, new words         | Lipsync members (`video2video`), audio or `text`, never both | `scenario-kling`                                      |
| Generated creator speaking natively | Native-audio video families, dialogue in quotes              | `scenario-veo`, `scenario-seedance`, `scenario-kling` |
| Faceless voiceover                  | B-roll clips plus TTS narration                              | `scenario-video`, `scenario-elevenlabs`               |
| Product demo inserts                | Image-to-video off the uploaded product still                | `scenario-product-shots`, `scenario-video`            |
| Captions, cut, 9:16 master          | Assembly tool models; text cards as image layers             | `scenario-video-assembly`, `scenario-text-overlay`    |

Script in six spoken beats: hook (one concrete tension or result), context (why this speaker cares), product moment, proof (visible demo or a user-supplied fact), turn (objection answered or before-after), close (soft CTA). Write for the mouth, not the page: contractions, false starts allowed, no taglines. Spoken pace runs near 2.5 words a second, so a 25-second ad is roughly 60 words, but that is a first guess and avatar members undershoot it: one delivered 63 words in 32s (1.94 a second) and another padded a 60-word script with 21s of silence. Time the returned clip before assembling, then trim the silences where there are any and cut the script where the delivery is simply slow.

Keep the register in every visual prompt: phone-height framing, available light, a real location with clutter, one handheld drift at most. Cinematic grammar (dolly moves, golden-hour rim light, shallow anamorphic looks, graded color) reads as an ad and kills belief. Compose 9:16 natively, reframing a non-vertical source still per `scenario-formats` before generating; a cropped 16:9 master frames like television.

## Worked example: 25-second founder ad from a portrait

1. Brief once: offer, platform, runtime, the facts the founder may claim, tone. Collect the portrait and the real product photo, then run without stopping.
2. Create this run's collection before the first generation (`collection_create`, catalog write lane, `name` only), then `collection_add_assets` each keeper as it lands; its returned `itemCount` is the receipt.
3. Draft the six beats at about 60 words and confirm the wording with the user; the script is a claims surface, not just copy. Unattended, keep every line to wording the brief already supplied and cut any beat that would need a new claim.
4. Voice: `upload_asset` the founder's recorded narration, or generate TTS per `scenario-elevenlabs` when they want a stand-in voice they approved.
5. `recommend` with `capability="img2video"` and the brief in the user's words; pick from its ranked list by input contract (a script-taking member when the speech exists only as text, an audio-taking one when a recording exists), then by whether the member can be told not to burn in captions: some hallucinate gibberish subtitles that no negative prompt suppresses, and the ones with a switch cost several times more, which `recommend` prices for you.
6. `upload_asset` the portrait. Prompt the speaker's hands empty and the set free of products: avatar members invent props and label type. `model_run` with `dry_run=true` first: avatar members sit far apart on price, so quote before spending.
7. Run for real with `wait=false`, then `jobs_wait` with the returned job id, re-called with `pending_job_ids` on timeout, never a second `model_run`.
8. Demo insert: animate the uploaded product photo with an image-to-video member (`scenario-video`), 3 to 5 seconds, one micro-move. `aspectRatio` is not reliably honoured once a start image is present, whatever the schema note says, so read `width` and `height` off the returned asset instead of assuming the ratio.
9. Assemble with `model_scenario-compose-video` per `scenario-video-assembly`: talking head as the spine, insert cut over beats three and four, captions burned into the platform's safe zone, product-name card from `scenario-text-overlay` as an image layer. Every overlay layer needs an explicit `width` and `height` or the compositor scales it, and `durationMode: "custom"` pins the master's length against image layers that would stretch it. A succeeded compose job is not proof the layers drew or landed where sent: pull a frame from the composite and confirm the captions and the card are present and placed before delivering.
10. `asset_display` the master. Gate every generated clip, the talking head included: extract frames on-platform with `model_scenario-video-to-image-seq` (single-digit CU, and `asset_get` returns `firstFrame` and `lastFrame` free) and verify them against the uploads (`scenario-asset-analysis`); an invented product in the speaker's hands or legible generated type fails a clip exactly like label drift on the insert. Report spend by summing this run's own job records by job id: `jobs_list` is project-scoped and over-reports, and `usage`'s headline figure is project-lifetime.

## Common mistakes

- Writing ad copy and handing it to a mouth: alliterative taglines collapse on a talking head; read the script aloud before generating.
- Fabricating social proof: an invented "10,000 five-star reviews" is a claim the user never made; keep numbers and testimonials to supplied wording.
- Prompting the creator like a commercial: tripod framing, perfect light, and a spotless studio kitchen read as an ad; imperfection is the format.
- Passing both audio and `text` to a lipsync member: exclusive inputs; pick one.
- Skipping `dry_run` on avatar and lipsync runs: per-member pricing varies too widely to guess.
- Generating the product or any on-screen text: the product comes from the uploaded photo, type is overlaid in assembly.
- One 40-second b-roll or generated-creator take: generate per-beat clips and cut on the beat turns; single long takes drift and cost more to retry. A talking-head script stays one take, trimmed in assembly.
- Cropping a landscape master to 9:16: heads and captions land outside the safe zone; compose vertical from the start.
