---
name: scenario-audio
description: Use when generating or handling audio on Scenario via MCP. Triggers include music tracks, background scores, soundtracks, game sound effects, SFX, foley, ambience, looping audio, voiceover, narration, speech, TTS, text-to-speech, voice cloning, re-voicing a recording, scoring or adding sound to a video, transcription, or requests to create, wait on, play, or download audio files (MP3, WAV) with Scenario tools.
license: MIT
---

# Scenario Audio Generation

## Overview

Scenario generates audio through the same loop as images: discover a model, read its schema, run it, wait, download. The live catalog covers three generation lanes (music, sound effects, voice/speech) plus video-to-audio soundtrack models and audio utilities. Connection and the core generation loop: see the `scenario` skill in this repo.

## Quick reference

| Step           | Tool                                                                                     | Notes                                                                     |
| -------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Find a model   | `search` target="models", query="music" / "sound effect" / "text to speech", public=true | audio generators list `txt2audio` in capabilities                         |
| Inspect inputs | `model_schema_get`                                                                       | audio schemas vary widely: durations, lyrics, voices, looping             |
| Generate       | `model_run`                                                                              | schema-conformant parameters; wait=false for long jobs                    |
| Wait           | `jobs_wait`                                                                              | blocks server-side; re-call passing pending_job_ids as job_ids on timeout |
| Listen         | `asset_display`                                                                          | renders an inline audio player                                            |
| Save           | `asset_get`                                                                              | file URL, then `curl -L -o out.mp3 "<url>"`                               |

Find existing audio assets with `search` target="assets", filters={kind: "audio"}. OAuth callers pass team_id and project_id on every call (discover them with `teams_list`; see the `scenario` skill).

## What the audio surface covers

- Music: text-to-music models produce instrumental tracks or full songs; several accept lyrics with section tags and duration controls.
- Sound effects: text-to-SFX models generate short clips from a description; some support seamless looping.
- Voice and speech: text-to-speech models with preset voices, multilingual output, and emotion or pacing controls; some clone a voice from a short reference clip; speech-to-speech re-voices an existing recording.
- Video to audio: models that score a silent video or add synchronized sound effects, taking a video asset as input.
- Utilities: audio cut, split, and extract tools plus speech-to-text transcription; discover with `search` query="audio" or query="tool".

## Worked example: a game sound effect

1. `search` target="models", query="sound effect", public=true. Returns txt2audio models such as `model_elevenlabs-sound-effects-v2` (example only; re-discover every session, catalogs differ per team).
2. `model_schema_get` model_id="model_elevenlabs-sound-effects-v2". Returns the exact fields: prompt plus model-specific controls such as duration or looping.
3. `model_run` model_id="model_elevenlabs-sound-effects-v2", parameters={"prompt": "heavy wooden treasure chest creaking open, single event, dry, no music"}.
4. If the response is status='in_progress', `jobs_wait` job_ids=["job_xxx"]. Timeout is not an error; re-call with the returned pending_job_ids as job_ids.
5. `asset_display` asset_id="asset_xxx" to play it inline.
6. `asset_get` asset_id="asset_xxx", then save its file URL with `curl -L`.

Prompting tips:

- SFX: name the source, material, action, and acoustic space, and say what to exclude ("no music", "no reverb"). One event per clip; generate variations as separate runs.
- Music: give genre, mood, tempo, and instrumentation, and say instrumental or vocal. Lyrics-capable models expect structured sections; check the schema.
- Speech: keep the text field to the words to speak. Voice choice, language, emotion, and pacing live in separate schema fields or inline tags depending on the model; check the schema instead of packing direction into the text.

## Common mistakes

- Hardcoding model IDs: availability differs per team and evolves. Re-discover with `search` each session.
- Skipping `model_schema_get`: one audio model's parameters will not fit another (voices, durations, and lyric fields all differ).
- Polling `job_get` in a loop: music jobs can run minutes. Use `jobs_wait`; on timeout re-call with pending_job_ids.
- Pasting raw asset URLs into chat: use `asset_display` to play audio.
- Saving audio with `asset_download`: image conversion only; take the file URL from `asset_get`.
- Putting voice direction inside TTS text ("say this angrily"): direction can end up spoken. Use the schema's emotion or voice fields.
- Sending image parameters (width, height) to audio models: their schemas do not accept them.
