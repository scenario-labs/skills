---
name: scenario-caption-studio
description: "Use when a video needs its spoken words on screen through Scenario via MCP: burned-in styled captions for a TikTok, Reels, or Shorts cut, ad captions for sound-off feeds, YouTube subtitles, an SRT sidecar, transcription of a clip's audio, captions translated into another language, karaoke or word-by-word styles, or restyling and correcting an existing transcript. Keywords: captions, subtitles, SRT, transcribe, karaoke, word-by-word, burn in, closed captions, translate video, caption style."
license: MIT
---

# Scenario Caption Studio

## Overview

Caption Studio is one tool model: a video in, its speech transcribed (Whisper) or an existing SRT applied, styled captions out, burned into the picture or delivered as a soft track and an `.srt` sidecar. It translates into 18 languages and styles captions three ways. Find it with `search` (`target="models"`, `query="caption"`, `public=true`); the authoring-time id is `model_scenario-caption-studio`, re-discovered rather than hardcoded. Connection and the core loop: see the `scenario` skill.

Captioning is the last pass on a finished cut: assemble first (`scenario-video-assembly`), then caption the master once. Captions carry the transcript only; text that must appear letter-perfect without being spoken (CTAs, prices, legal supers) is `scenario-text-overlay` territory. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Ask once, then caption

The destination decides nearly every parameter, so collect one round of answers before touching the schema: where the video ships (a sound-off mobile feed, a paid placement, a seated long-form viewer), whether the spoken language stays or translates (`targetLanguage`, `auto` keeps it), brand colors if any, and which deliverable the platform wants. The deliverable is three switches: burned-in pixels are `outputSubtitles: "video_image"` (the default), the toggleable track is `"video_data"`, the sidecar file is `outputSrt: true`, and an SRT-only pass is that plus `outputVideo: false`. Then map the answers:

| Destination                              | Style                                                                | Segmentation                                                                          | Position                                                      | Output                                                                         |
| ---------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Social mobile short (9:16 Shorts, Reels) | `tiktok-bouncy` or `word-pop`; `karaoke-fill` when music drives      | `maxSegmentWords` 3 to 5, or 1 for karaoke                                            | `middle`: platform UI and native auto-captions own the bottom | Burn in                                                                        |
| Ad short, performance cut                | `modern-chip` or `minimal-underline`, accents set to brand color     | 3 to 7 words per cue                                                                  | `bottom`, or `top` when an end card or overlay sits below     | Burn in for sound-off feeds; add `outputSrt` for the platform's caption upload |
| YouTube long-form, tutorial, interview   | Default look or `cinematic-fade`; restraint reads as professionalism | `maxLines` 2, `maxSegmentChars` 84 (two 42-character lines, the broadcast convention) | `bottom`                                                      | `outputSrt` for the platform's closed captions; burn in only for re-embeds     |
| Cinematic piece, trailer, festival cut   | `cinematic-fade`                                                     | Sentence-length cues, `maxSegmentDuration` about 6                                    | `bottom`                                                      | Burn in                                                                        |

Rows are authoring-time starting points to confirm with the user, not platform contracts; unattended, the task's own instructions answer the interview and the matching row's defaults fill what they leave unsaid. The per-placement safe zones behind the position column live in `scenario-formats`. An uploaded track beats burn-in for long-form because viewers toggle and restyle it, assistive tech reads it, and platforms index it for search; burn-in wins wherever the style is the point or a track cannot travel with the file.

## The style ladder

Three tiers: `stylePreset` picks a ready-made look (7 presets, empty for the default); `stylePrompt` describes a look in plain words and builds a matching style (it carries `cost_impact`); `themeTsx` supplies a full custom theme that replaces the preset, with `stylePrompt` then refining that theme. `fontColor` sets the body text (contrast beats aesthetics: white body text survives every backdrop the presets put behind it), and `accentColorStart`/`accentColorEnd` drive the highlight animation (karaoke fills, pops): spend the accent on one thing, usually the brand color, with equal values for a solid and different values for a gradient. Leave `fontSizePx` empty to size automatically. `outputTsx: true` returns the theme a run used, so a look that landed can be replayed exactly on the next video.

## Getting the words right

- `transcriptionPrompt` is a spelling hint, not a style field: list the names, brands, and jargon the audio contains so they transcribe correctly.
- `modelSize` trades accuracy for speed and cost (`cost_impact`): the `medium` default is fine for clean voiceover; step up to `large-v3` for noisy audio, accents, or dense terminology; `.en` variants are English-only.
- The model transcribes whatever audio the master carries, so balance the music bed against dialogue before captioning (`scenario-video-assembly`), never after.
- Corrections and restyles ride the `subtitles` input: a run with `outputSrt: true` returns the transcript as its own asset, and passing that asset id back as `subtitles` reuses the words verbatim, so a restyle never re-transcribes. `upload_asset` has no text kind (authoring-time fact), so a locally edited `.srt` reaches the platform by the user uploading it at app.scenario.com and handing back the asset id; flag that gap rather than bridging it with an API call.

## Worked example: a vertical social short, then a Spanish variant

1. `asset_get` the assembled master: confirm duration and that it is the finished cut, since the price tracks the footage (`video` carries `cost_impact`; trim first, `scenario-video-editing`).
2. `search` with `target="models"`, `query="caption"`, `public=true`, then `model_schema_get` on the hit.
3. Price it: `model_run` with `dry_run: true` and `parameters={"video": "<asset_id>", "stylePreset": "tiktok-bouncy", "maxSegmentWords": 4, "textPosition": "middle", "transcriptionPrompt": "Scenario, LoRA, Flux", "outputSrt": true}`. Re-estimate after changing `targetLanguage`, `modelSize`, `stylePrompt`, or `outputSubtitles`: all carry `cost_impact`.
4. Run it with `wait: false`, then `jobs_wait` with the `job_id`; on timeout re-call with the returned `pending_job_ids`, never `job_get` in a loop.
5. Review before deriving: `asset_display` the video and watch it through, checking names against the audio and cue placement against the frame; download the SRT sidecar with `asset_download` (no `format`: it converts images only).
6. Spanish variant: add `targetLanguage: "es"` to the same parameters, `transcriptionPrompt` included, and `dry_run` again (it moves the price) before running. Translation happens inside the run, so one master yields a variant per market. Latin-script segmentation caps do not transfer to Chinese, Japanese, or Korean (streaming style guides run them at a third of the characters per line), so revisit `maxSegmentChars` per target language.
7. File the master, variants, and SRT assets in a collection (`scenario` skill) so the delivery set stays findable.

## Common mistakes

- Captioning each clip before assembly: caption the finished master once, or cues drift across cuts and every edit orphans its captions.
- Expecting the preset look on the soft track: `video_data` renders as plain text the viewer toggles; styling survives only when burned in.
- Styling legal lines or CTAs as captions: disclosures carry locked wording, size, and dwell time that caption logic would re-chunk and retime, and a toggleable track fails "visible without viewer action" rules outright; exact unspoken text is a `scenario-text-overlay` card composited in assembly.
- Setting `maxSegmentWords: 1` without a karaoke or pop preset: one-word cues flash as a slideshow unless the style animates them.
- Treating a `jobs_wait` timeout as failure: re-call with `pending_job_ids`; video tool jobs outlast the wait window routinely.
