---
name: scenario-ace-step
description: "Use when creating or editing music with ACE-Step models on Scenario via MCP: text-to-music songs with sung vocals from a lyric sheet, instrumental tracks, covering or restyling an existing song, repainting one section in place, changing sung lyrics, adding an instrument layer, completing a partial recording into a full arrangement, extracting stems, or choosing between Turbo and Quality lanes. Keywords: ACE-Step 1.5, cover strength, repaint, Vocal2BGM, stem separation, karaoke, BPM."
license: MIT
---

# Scenario ACE-Step Music

## Overview

ACE-Step 1.5, a music production family on Scenario, splits every mode into its own model: Text to Music, Cover, and Repaint each in a Turbo and a Quality lane, plus a full-quality edit trio (Add Layer, Complete Track, Stem Extract), nine members at authoring time. Discover them with `search`, pick the member by mode name, and treat `model_schema_get` as the contract.

Connection and the core loop: see the `scenario` skill in this repo; model-agnostic audio work: the `scenario-audio` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Mode           | Key inputs                                     | Behavior                                                                         |
| -------------- | ---------------------------------------------- | -------------------------------------------------------------------------------- |
| Text to Music  | `prompt` or `lyrics` (either suffices)         | full song; `duration` 10 to 600 s (empty lets the model pick), `bpm`, `keyscale` |
| Cover          | `srcAudio` (+ `referenceAudio`)                | restyles a song; `audioCoverStrength` sets how much of the original survives     |
| Repaint        | `srcAudio` + window                            | regenerates `repaintingStart` to `repaintingEnd` in place, length preserved      |
| Add Layer      | `srcAudio` + `trackName` + `prompt`            | adds one stem matched to key, tempo, and groove, optionally windowed             |
| Complete Track | `srcAudio` + `completeTrackClasses` + `prompt` | arranges stems around a partial recording (Vocal2BGM)                            |
| Stem Extract   | `srcAudio` + `trackName`                       | isolates one stem from a mix                                                     |

Numbers are at authoring time: read caps off `model_schema_get`. Stem fields take one of twelve fixed values (vocals, backing_vocals, drums, bass, guitar, keyboard, percussion, strings, synth, fx, brass, woodwinds), never free text. `srcAudio` is a single audio asset: `upload_asset` first, or reuse a generated asset id. Across members: `numOutputs` (1 to 4) multiplies cost, `thinking` (default true, absent on Stem Extract) runs a planning pass, `vocalLanguage`, where present, defaults to auto-detect. `guidanceScale` exists on the edit trio alone, `audioCoverStrength` on Cover alone, and `repaintingEnd: -1` runs to the end of the track.

## Lane choice

Turbo and Quality siblings take the same parameters, except `audioFormat` (mp3, wav, flac), at authoring time on Repaint Turbo alone. Quality is the full-size checkpoint tuned for fidelity and prompt adherence; Turbo is distilled for speed and at authoring time costs half as much. Iterate on Turbo (lyrics, structure, windows), then re-run the keeper's parameters on the Quality sibling. The edit trio has no Turbo lane. `duration` and `numOutputs` both move the price, so `dry_run=true` before a long track or a batch.

## Writing the song

Keep `prompt` to a one-line style caption (genre, mood, instruments, production) and put the words in `lyrics`, shaped with section tags: `[Verse]`, `[Chorus]`, direction inside the tag like `[Bridge - whispered]`, backing vocals in (parentheses), UPPERCASE for belted lines. Vocal-free music is `instrumental: true`, not "no vocals" in the caption. Tempo and key have dedicated fields (`bpm`, `keyscale`, e.g. "C Major"), not caption text.

## Editing without regenerating

- Cover keeps the structure recognizable; `audioCoverStrength`: near 1 stays faithful to the arrangement, 0.5 to 0.6 transforms the genre while the hook survives, around 0.2 borrows only the mood. `referenceAudio` optionally donates genre and feel; rewritten words go in `lyrics`.
- To change sung lyrics in a Repaint window: start `prompt` with "Repaint the selected section with new sung lyrics:", pass the full lyric sheet in `lyrics` with the new section in place, and set `thinking: false`.
- Complete Track works best on a source with clear melody and rhythm.

## Worked example: fix a chorus in a generated song

1. `search` with `target="models"`, `query="ace-step"`, `public=true`. Pick members by mode name, e.g. `model_ace-step-1-5-turbo-text-to-music` and `model_ace-step-1-5-turbo-repaint` (live hits at authoring time: re-discover each session).
2. `model_schema_get` on each id before running it.
3. `model_run` the Text to Music member with `dry_run=true` and `parameters={"prompt": "indie folk, warm, fingerpicked guitar, soft female vocals", "lyrics": "[Verse]\n...\n[Chorus]\n...", "duration": 90, "vocalLanguage": "en"}`; re-estimate after changing `duration` or `numOutputs`.
4. Repeat with `wait=false`, then `jobs_wait` with the job id, re-called with `pending_job_ids` on timeout. A timeout is not a failure and never justifies a second `model_run`.
5. `asset_display` to listen; note the chorus window, say 24 to 52 seconds.
6. `model_run` the Repaint member with `parameters={"srcAudio": "<asset id>", "repaintingStart": 24, "repaintingEnd": 52, "thinking": false, "prompt": "Repaint the selected section with new sung lyrics:", "lyrics": "<full sheet with the new chorus in place>"}`.
7. Listen again, then `asset_download` the keeper (omit `format` for audio).

## Common mistakes

- Expecting one model to infer the mode: every mode is a separate member; pick it by name from `search`.
- The lyric sheet in `prompt`: it caps at 512 characters and carries style; words go in `lyrics`.
- Free-text stems ("kick drum") in `trackName` or `completeTrackClasses`: only the twelve fixed values are valid.
- Repainting new sung lyrics without the recipe: the sentinel prompt, the full sheet with the new section in place, and `thinking: false` go together.
- Expecting Repaint to change track length: the window regenerates in place; a different length means a new Text to Music run.
