# The soundtrack and pictures with Scenario

The film's motion is free to render; the soundtrack and pictures are the paid steps. The `scenario`
skill owns the generation loop. What this film adds:

- Price every step with `model_run` and `dry_run: true`, tell the user the total for the whole
  soundtrack and picture set, and wait for a go before the first paid run.
- Choose each model with `recommend`: `txt2audio` for music and sound effects, `txt2img` for
  pictures, `img2img` from the user's own art (uploaded first).
- Read the inputs with `model_schema_get`. Input names below (`bpm`, `instrumental`, `duration`,
  `numOutputs`, `referenceImages`, `aspectRatio`, `resolution`) are authoring-time examples: use the
  names the schema gives.
- Keep the asset ids next to the files (a small text file in `audio/` and `art/`), so a later edit
  can pass a picture back as a reference image without uploading it again.

## 1. Music at the film's tempo

`recommend` with `"capability": "txt2audio"`, the genre, the tempo, the structure and "no vocals",
plus `duration` (a minimum, in seconds). Choose a model whose schema has a **tempo input** (often
`bpm`), an **instrumental** switch and a **duration**: a tempo the model is told beats a tempo you
hope for. `features: ["bpm"]` asks `recommend` for that input by name; an unknown name returns
`no_match` with a hint. In the Kaiju Postal build two takes at 172 BPM both measured 172.0 BPM with
a strong grid.

Prompt pattern (keep it under the schema's length limit):

> High-energy drum and bass for a playful video game trailer, 172 BPM. Eight bars of tense intro
> with filtered drums and a rising synth, then a huge drop: punchy kick on every downbeat, rolling
> breakbeats, growling reese bass, bright brass stabs. Tight, loud, modern. No vocals. Ends on one
> hard final hit.

Ask for 2 takes and about 15 s more than the film (the intro and the outro are spare). Download each
with `asset_download` (no `format` for audio), then measure:

```bash
.venv/bin/python $K/scripts/beat_grid.py audio/music_a.mp3 --bpm 172
```

- It prints the tempo, the first strong downbeat (`offset`), downbeats, drop candidates, and
  `grid_strength`. Each drop gives how much louder the music gets (`rise`) and its film beat from
  that offset.
- Pick the take with the clearest grid and the biggest rise.
- Choose `music.offset` so the drop lands on the beat you planned:
  `offset = drop_seconds - planned_drop_beat * 60 / bpm`, and check it is one of the listed
  downbeats.
- Reported times can run up to about 0.1 s early, an open issue in the tool. Watch the drop in the
  1080p check render, with sound, before the 4K master.
- `--window` fits only the stretch the film uses: generated music can drift, and the film only needs
  that stretch to be exact. Without `--bpm` the fit can lock to half or two thirds of the tempo.
- `music.stopBeat` cuts the music dead on a beat (the logo hit); without it the music fades at the
  end.
- `music.gain` (dB, default -3.5) sets the bed under the effects.

## 2. The sound kit

`recommend` with `"capability": "txt2audio"` and "short isolated sound effects for motion graphics".

- Prefer a dedicated sound-effects model with a duration control and a negative prompt.
- One run per sound, `"wait": false` for all of them, then one `jobs_wait` with every job id (at
  most 32; call it again with `pending_job_ids`).
- Short durations: each second costs.
- A negative prompt such as `music, speech, voice, reverb wash, background noise` keeps one-shots
  clean.

The core kit, each with its length and a prompt that worked:

- **`whoosh_1.wav`, `whoosh_2.wav`** (0.7 s): A fast, airy whoosh as something whips past the
  camera, single pass, clean.
- **`whoosh_big.wav`** (1.3 s): A deep cinematic whoosh with a sub-bass swell, a heavy object
  rushing past the camera.
- **`impact.wav`** (1.2 s): Punchy cinematic impact hit with a tight low end and a short tail,
  single hit.
- **`impact_big.wav`** (2.2 s): Huge movie trailer impact: a deep boom with a metallic crunch and a
  long tail.
- **`hit.wav`** (0.5 s): Snappy percussive hit, a whip crack layered with a tight snare, very short.
- **`slash.wav`** (0.6 s): Sharp sword slash, a fast metallic swipe through the air, single swipe.
- **`key_1.wav`, `key_2.wav`** (0.3 s): One mechanical keyboard key press, close and dry, a single
  click.
- **`pop.wav`** (0.3 s): Short bubbly user interface pop, soft and clean.
- **`tick.wav`** (0.25 s): Tiny crisp user interface tick, a short digital click.
- **`riser.wav`** (2.2 s): Reverse cymbal swell riser building tension, cutting off sharply at the
  very end.
- **`glitch.wav`** (0.6 s): Short digital glitch stutter, a burst of data corruption.
- **`logo_hit.wav`** (3 s): Deep cinematic logo hit: a sub-bass boom with a long shimmering tail.

Those 12 cover every cue the blocks register: a missing `thock` plays `pop`, `drop` plays
`impact_big`, `rewind` plays `whoosh_big`, `scroll` plays `whoosh`.

- Add the film's own sounds and play them with `spec.cues` (`[[beat, 'stomp', gain], ...]`) or as a
  shot's `cue`. Set their level in `spec.sounds` (`{ stomp: -1 }` in dB).
- Kaiju Postal added `stomp` (a giant footstep with debris), `roar`, `bell` (a bicycle bell double
  ring) and `knock` (one firm knock on a wooden door, two variants).
- Save everything in `audio/sfx/`. Variants named `name_1`, `name_2` rotate on repeated cues.

## 3. Mix

```bash
.venv/bin/python $K/scripts/mix.py .            # out/mix.wav, two-pass loudness to -14 LUFS, -1 dBTP
.venv/bin/python $K/scripts/mix.py . --lufs -13 # a louder social master
```

It places every cue from the film's own list, aligned on each sound's attack, peak or end. It ducks
the music under the big hits, lists sounds with no file, and lists hits that sit under the music.
Fix those with `spec.sounds` or `music.gain` and mix again. It cannot judge taste: listen before you
hand the film over.

## 4. Pictures

`recommend` with `"capability": "txt2img"` (or `img2img` from the user's own art). Write the prompt
as an art director: style, shot, subject, light, palette, what is in each third of the frame.

- **Describe composition; never ask for empty space.** "Keep a calm darker band for title text" came
  back as a literal gray band across the image. Darken for type in the film (`tint`).
- **Consistency.** Pass the first picture's asset id as a reference image for every later one ("same
  character, same city as the reference image").
- **Never write "no watermark" when a reference image is attached**: the request was blocked as
  watermark removal. "No text, no logos" is enough, or describe signs as abstract glyphs.
- **Inspect at 100%.** Generated vehicles, clothes and products carry real brand marks (a scooter
  came back with a maker's script logo). Paint them out or regenerate before the film uses the
  picture.
- 16:9 at 2K or more: the Picture block needs at least 2048 px of width. Download with
  `"format": "png"` into `art/`.

The second Kaiju Postal key art, as a dry run:

```json
{
  "model_id": "<id from recommend>",
  "dry_run": true,
  "parameters": {
    "prompt": "Same game, same art style, same courier and same rainy neon city as the reference image. Close-up three-quarter shot of the courier on the yellow scooter, looking up with a determined grin; a puddle on the right reflects one enormous glowing monster eye. Stylized 3D, soft global illumination, crisp rim light.",
    "referenceImages": ["<asset id of picture 1>"],
    "aspectRatio": "16:9",
    "resolution": "2K",
    "numOutputs": 1
  }
}
```
