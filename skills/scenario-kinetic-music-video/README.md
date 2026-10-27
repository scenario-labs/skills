# scenario-kinetic-music-video (maintainer notes, not packaged)

## Origin

Sara Nemati own `kinetic-music-video` skill, built from the production of the Every Scenario music
video (and the kinetic music video it grew out of) and rewritten to be generic: any subject or none,
any looks, no project examples. Brought into this repository from the ZIP she exported on
2026-10-02.

## Edits for this repository

- Frontmatter reduced to `name`, `description` ("Use when", under 500 characters) and `license`; the
  name carries the `scenario-` prefix.
- Generative model names and ids removed (availability differs per team): lanes are named by
  capability and found with `recommend`. Parameter names are the ones that held at authoring time,
  with the schema as the authority.
- Credit amounts stated as relative costs, with `dry_run` before paid steps.
- En and em dashes replaced, scripts print usage when called without arguments, and the
  output-writing scripts refuse to replace an existing file without `--force`.
- Sibling references and the install invitation added; connection setup points to `scenario`.

## Portrait canvas

Added after import so the skill can serve vertical feeds. One canvas per project (`CANVAS` in the
timeline), with `--canvas` for a second ratio. `assets/engine/canvas.js` holds the presets, the 9:16
safe band (derived from the band `scenario-formats` and `scenario-video-ads` compose to, reading
their 6 to 13% per side as 6% left and 13% right, where the action rail sits), the per-canvas
timeline filter and `plateFit`. The HUD, the house subtitle and the scene template lay out inside
`E.SAFE`; every portrait-only behavior is gated off landscape.

Verified headless (Playwright's Chromium, software WebGL) with synthetic audio, lyrics and a
synthetic footage clip (frames, matte, tracking): landscape stills of both template branches
(footage and 3D) and the HUD, including a 150-character lyric line, are pixel-identical to the
pre-change engine at scales 1 and 0.5. Portrait and square stills were checked by eye with the safe
band outlined, and the error paths (bad canvas, bad timeline tag, an `--only` with nothing to
render) fail fast. `canvas.js` has a unit suite. Two plan-only application tests (portrait only;
both ratios) passed with notes.

A live application test then produced a full 1080p60 portrait video end to end (a 2:14 song, 24
style frames, 27 clips, 9 section agents, about 15k CU) and passed with notes. It found the portrait
subtitle running into the HUD counters, a `crop` that stretched plates, a `--chant` window with no
end, transcription passes overwriting each other, `still.mjs` keeping a stale sheet, and the doc
gaps behind a mic-covered lip-sync retake, the 720p-only cost anchors and a rejected reference crop.
All are fixed; `motion_library.md` §10 notes one production behind its portrait rules.

## Dynamism gate

Added so a render is held to numbers per section, not to an eye that adapts after a few watches.
`scripts/dynamism_check.py` gates a render and measures references; `scripts/rectify_screen.py`
flattens a phone-filmed screen first, since a reference often arrives as a phone filming a TV or a
laptop, and motion read off that raw video measures the hand.

How the measurement was chosen, all on synthetic clips encoded with libx264:

- **A 60 fps clock and distinct frames.** Each picture of 24 fps footage repeats 2 or 3 times in a
  60 fps render, so frame-to-frame differences read a live clip as mostly still. A first design
  compared frames 0.1 s apart. It fixed the repeats, but its flow saturated near 12 px per frame and
  then fell as speed rose: pans at 18 to 96 px per frame all read 4 to 6. A 1-frame toggle or a
  3-frame shake also compared identical phases and read fully still. The script now runs optical
  flow between consecutive distinct frames, skips repeats, and averages 0.5 s windows (whole 24, 25
  and 30 fps cycles).
- **Flow range.** OpenCV's dense flow pyramid stops at 32 rows, which capped it near 16 px at the
  320 px analysis size. A 1/8-size pass seeds it, and a whole-frame shift catches whip pans beyond
  that. Constant pans from 3 to 192 px per frame read strictly increasing, within 7% of true at
  native 60 fps and within 8% as 24 fps footage.
- **Still runs at frame resolution.** Fixed 0.1 s steps read a 0.60 s hold as 0.5 s, which passed
  the high limit. Runs now end on the frame, and a 0.60 s hold reads 0.60 s. The still test uses a
  gray difference of 12, not 24: at 24, a 6 px per frame pan of 24 fps footage over soft texture
  read 44% still.
- **Slow moves add up.** A still run first ended only on per-pair flow of 1 px or a pixel change.
  Sub-pixel drifts at the calm (0.5) and mid (1.0) motion floors then split into short runs that all
  read 100% still, and a 10% push-in over 2 s read 97% still. A run now also ends once the flow from
  its first frame reaches 0.25 px at 320.
  - The limit was 0.4 first. 24 or 25 fps footage shows only 2 new pictures in a 0.1 s run, about
    0.4 px at the calm floor, so a calm drift and a 10% push-in read 12 to 93% still there.
  - At 0.25, both read 0% still at 15, 23.976, 24, 25, 29.97, 30 and 60 fps drawn at twice the
    analysis size, and at 24, 25 and 60 fps rendered at 1920 x 1080. Drawn at 320 itself, a drift
    still read up to 23% still at 24 and 25 fps (53% at 15): libx264 holds some of its sub-pixel
    steps.
  - Gaussian grain of sigma 1 to 3 gray levels on a hold measured 0.01 to 0.17 px from the run's
    first frame and reads 100% still. CRF 23 smooths grain past the pixel test: there, sigma 3.4 to
    4 read 70 to 100% still at 0.25, and sigma 3.4 only 70 to 83% at 0.2, so the limit stops at
    0.25. At CRF 12, the pixel test breaks a hold from sigma 3.8, as before.
  - That flow call runs only once the per-pair steps since the run began sum to half the limit, so a
    clean hold or a fast move never pays for it.
- **Decoded size.** ffprobe reports a phone clip's coded size, before its rotation tag. A portrait
  clip stored landscape read as a landscape canvas, with 45% less motion. The size now comes from a
  decoded frame, as in `rectify_screen.py`.
- **A flash is one cut.** Cut frames within 3 frames of each other merged, so a white flash of 4 or
  more frames (2 in a 30 fps preview) read as two cuts. A cut back to the previous shot within 0.15
  s now ends the same cut; a strobe counts one cut per flash.
- **Flashes follow WCAG 2.x general flashes:** a pair of opposing changes of 10% relative luminance,
  the darker state under 0.80, on the frame mean, at most 3 per second everywhere. Counting each
  change as a flip would have failed a white flash on every beat at 120 BPM; the pair reading allows
  it and still fails full-frame 8ths.
- **Speed.** Flow runs on every distinct pair, in 4 threads. A 10 s 1080p60 test pattern measured in
  about 1 s (3 s on one thread) on an M-series Mac at authoring time.

Default targets are uncalibrated: they were checked on synthetic fixtures only, never on a real
render. Calm allows a 1.0 s hold, not more, because the quality bar says no static frames.
Calibration is pre-registered for the next live `/skills:validate` run, which gates every section of
its render:

- An approved section that fails: loosen that energy's default to its measured value with the
  `--write-targets` margins (still + 0.10, hold × 1.25, motion × 0.7).
- A section the grader calls static that passes: tighten that energy's default to its measured
  value.
- Approved sections pass and static ones fail: keep the defaults, and drop the "uncalibrated" hedge
  once a second production agrees.
- A flash failure is never loosened: the limit is a safety rule, not taste.

`rectify_screen.py` on a synthetic handheld clip (zoom 3%, drift 14 x 9 px, a caption band):

- manual corners: mean error 1.3 of 255 against the true screen content;
- auto detection: corners within 5 px, error 2.8 of 255, 100% of frames tracked;
- median motion: 4.7 on the true content, 6.5 off the flattened screen, 1.4 off the raw phone clip.

Known limits:

- The numbers are frame-wide. Frozen footage under moving type passes, and a lip-sync close-up where
  only the mouth moves reads still; `freezedetect`, the contact sheets and dynamism.md §7 cover
  them.
- Flashes on part of the frame are not measured.
- Auto screen detection needs a screen brighter than the room. A live `/skills:validate` run filmed
  black bars around a vertical video: the room outscored the screen, and its outline filled the
  frame. Such an outline now exits "no screen found", after writing the `--check` frame. Quadding
  the video itself tracked 100% of frames.
- The same clip inside black bars (a landscape recording posted as a vertical video) outlined the
  whole recording and failed on texture, with no `--quad` hint. Detection now crops the bars first,
  and the clip exits "no screen found" as it does without them.
- `--write-targets` takes span energies as given. Labeling spans by how busy they look once held a
  calm section to more motion than a mid one, so `measure` warns when targets run out of order. It
  checks the targets the gate will use: a calm-and-high file still meets the default mid.
- Sections come from `node` evaluating `engine/timeline.js` as a `data:` URL module. A timeline with
  relative imports falls back to a file URL, which needs a Node that detects ES modules in the
  project's typeless `package.json` (20.19+ or 22.7+).
- `scaffold.sh` copies the scripts into `tools/` on every run, but its `cp -n` keeps an existing
  project's `ENGINE_API.md` and `AGENTS_BRIEF.md`, and rerunning it reinstalls the environment. So
  SKILL.md step 6 tells a revision of an older project what to copy by hand: the brief is filled in
  per project, so only its dynamism check is added.

## What the record does not cover

- The skill is the creator's own document, not distilled here, so it does not follow the house
  layout for recipe skills: its `references/lessons.md` plays the Common mistakes role.
- Costs are the production's observed relative prices, not live quotes.
- The engine and scripts need Node with Playwright, ffmpeg and a Python environment
  (`scripts/scaffold.sh` builds it); the matte tool needs macOS (Apple Vision).
- Tests cover the dependency-light scripts, the dynamism and rectify scripts on synthetic clips, and
  `canvas.js`; the rest need the full environment and generated footage.
