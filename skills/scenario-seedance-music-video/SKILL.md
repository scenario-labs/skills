---
name: scenario-seedance-music-video
description: "Use when turning a song, track, or audio master into a finished music video with Scenario and Seedance: planning shots against beats and sections, transcribing lyrics, generating clips that cut to music, assembling a delivery over the untouched master soundtrack, or verifying the final cut. Keywords: music video, beat sync, shot list, lyric transcription, reference frames, ffmpeg assembly, Seedance."
license: MIT
---

# Scenario Seedance Music Video

## Overview

Five steps: song, lyrics, story, frames, video. The supplied master is the soundtrack and is never re-encoded: every Seedance call sets `generateAudio: false`, and [scripts/build.py](scripts/build.py) muxes the master once, at the end, proving it untouched by hash. [scripts/song.py](scripts/song.py) reads the master so cuts land on its structure. The scripts need ffmpeg and ffprobe on PATH, and numpy for song.py.

Connection and the core generation loop: see the `scenario` skill in this repo. The Seedance parameter contract and conditioning traps: see the `scenario-seedance` skill in this repo.

## Quick reference

| Step      | Call                                              | Notes                                                             |
| --------- | ------------------------------------------------- | ----------------------------------------------------------------- |
| 1. Song   | `python3 scripts/song.py master.mp3 -o song.json` | hash, duration, loudness, tempo, sections, cut candidates         |
| 2. Lyrics | `search` query `"audio to text"`, `model_run`     | supplied lyrics win; sung-vocal transcription is a draft          |
| 3. Story  | one page, shown to the user first                 | the cheapest place to be wrong; name what must not drift          |
| 4. Frames | image model at the delivery aspect ratio          | reference stills, one per look to hold                            |
| 5. Shots  | Seedance `model_run`, `generateAudio: false`      | `dry_run` first; `wait=false`; `jobs_wait` with `pending_job_ids` |
| 6. Cut    | `python3 scripts/build.py edit.json out.mp4`      | one ffmpeg pass: conform, concatenate, mux master, verify         |

Ask once before starting: team and project, track clearance, aspect ratio and length, what must and must not appear, spend ceiling. Then run without stopping.

## Worked example: one verse, three shots

1. `python3 scripts/song.py master.mp3 -o song.json`. Sections are shot boundaries, cut candidates are cut points; listen before trusting them. The master stays read-only.
2. Upload the master: multipart `upload_asset`, then `upload_asset_complete` (see the `scenario` skill). `search` a transcription model (query `"audio to text"`), `model_schema_get`, `model_run`, `jobs_wait`. Instrumental track: say so and move on.
3. Write one page: what happens, where, how it turns across the sections; name the closing image. Show it to the user before spending anything.
4. Generate reference stills with an image model (via `search`) at the delivery aspect ratio, one per look. Look at them: they set identity and palette downstream.
5. Per shot, decide the conditioning: opening state matters, pass a first-frame `image`; only identity and world matter, pass `referenceImages` (see [references/shots.md](references/shots.md)). Generate each shot one or two seconds longer than its slot for a trim handle.
6. Write `edit.json` and run `python3 scripts/build.py edit.json out.mp4`:

```json
{
  "master": "master.mp3",
  "fps": 24,
  "width": 1280,
  "height": 720,
  "shots": [
    { "clip": "clips/01.mp4", "at": 0.0 },
    { "clip": "clips/02.mp4", "at": 12.5, "in": 1.0 }
  ]
}
```

Each shot runs until the next starts and the last to the master's end, so gaps are impossible. `in` is an optional head trim. The build fails loudly when a clip is too short or the delivered audio is not the master.

## Common mistakes

- Leaving `generateAudio` at its default (true): the master is the only soundtrack, muxed once by build.py.
- Trimming, normalizing, fading, or re-encoding the master: build.py stream-copies it whenever MP4 allows and verifies by hash.
- Prompting an opening state in reference mode: it will not appear; pass a first-frame `image`.
- Judging a clip from a sparse contact sheet: a continuous camera move looks like a hard cut; measure first (see [references/shots.md](references/shots.md)).
- Trusting the beat grid: sections and cut candidates are suggestions; check them against what you hear.
- Downloading clips with `asset_download`: image conversion only; take each file URL from `asset_get` and `curl -L` it.
- Calling it done without watching the delivery with sound, then muted.
