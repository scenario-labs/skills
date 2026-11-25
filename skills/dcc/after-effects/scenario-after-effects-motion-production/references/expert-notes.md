# Expert notes: commercial motion production

Principles and judgment, by expert, with source and timestamp. Lines marked [added] are this skill's
own additions. Numbers come from the sources or from the live tests (marked "measured").

## Structure and the hook

### Derek Lieu, trailer editor, GDC "Trailer Made" (QWd7F0z1W_Y)

- A trailer is not a montage: two shots cut together make a third meaning, so cause and effect can
  be staged even when the game never shows them in that order [00:03:06].
- Teach, excite, tease. One or two of the three is acceptable [00:01:05].
- Lead with the one or two things only this game can say. Shared genre features waste screen time
  [00:05:37], [00:07:56]. A genre combination can be the hook [00:07:21].
- The friend test: what would someone tell a friend after watching? People remember one small thing
  [00:08:59].
- Put the one piece of context needed to read the rest EARLY, or the earlier footage is wasted
  [00:10:12], [00:13:17].
- Five-act intensity curve: Cold Open (high), Intro (drop, teaches the pieces), Escalation (climb
  with a plateau), Climax, a deep dip for title or call to action, then a short Button [frame
  00:19:44, 00:16:11].
- Rate every clip 1 to 3 stars, order from least to most exciting, then break the ramp into waves
  (1, 2, 3, 1, 2, 3) [00:19:25 to 00:20:05].
- Shot pyramid, bottom to top: clear, interesting, new, pretty. A shot failing a lower level is not
  rescued by a higher one [00:18:06].
- Cut on the beat or put the action on the beat; he prefers the action on the beat [00:22:52].
- An unknown logo does not open the piece; a fade from black wastes the first seconds [00:23:49].
- Turn the HUD off, or keep only the part the shot needs [00:24:46].
- Too many calls to action means none is taken [00:17:18].
- Show the cut to someone who knows nothing about the game [00:26:13]. "More information can be less
  interesting" [00:26:44].
- Do not mix music down to inaudible; if it must be that quiet, it is the wrong music [00:21:51].

### Ad network, high-performing video ads (doc, retrieved 2026-11-24)

- Hook within the first 3 to 5 s. Five hook types: direct problem callout, bold claim, unexpected
  demo, social validation, data or authority.
- Test one variable at a time across hook, problem focus, proof type, offer frame and format.
- Interstitial placements give 5+ s of guaranteed attention; rewarded placements are unskippable up
  to 60 s; most top-spend videos on its network run longer than 30 s. Deciding condition for length:
  placement.
- Captions: an example with 64 % higher Day 0 ROAS than the same video without captions. Bold,
  legible font, benefit keywords highlighted.
- 45 s blueprint for long placements: hook 0 to 4 s, problem 4 to 9, escalation 9 to 14, mechanism
  14 to 22, proof 22 to 27, offer 27 to 36, CTA 36 to 45.

### App marketing study (doc, 2023-10-16)

- An end card that differs from the last video frame: 3x IPM against a repeated frame. Playable end
  cards: 7x IPM, 47 % better CTR than static.
- Hold rate (time engaged before close or skip) is the key creative metric.

## Process and approvals

### Joey Korenman, School of Motion (1nChUaFL3rc)

- Brief, concept, boards or key frames, then animation [00:00:52 to 00:03:30]. Stages can be skipped
  or reordered [00:05:59].
- Design the final frame first, so the animation has a destination [00:02:54 to 00:03:30].
- Audio is its own stage [00:04:54].

### Cameron Shefer-Boswell, MotionXP (Gqr0WrahBBs)

- Cost of change rises per stage: sketch, refined sketch, illustration, animation [00:02:59],
  [00:05:55].
- Lock timing in an animatic when voice-over or music exists: retiming after animation is "difficult
  and frustrating" [00:05:00].
- Get the style approved before illustrating or animating the other scenes [00:08:02].
- Collect review notes as timestamped comments on a first draft [00:09:22].

### School of Motion guide and MotionMedia (docs)

- When a scene's timing changes, track the time borrowed so the total still fits (SOM, "Design your
  rough animation").
- Add compositing, color and sound before export, not after (SOM, "Finalize your animation").
- Resolution, frame rate, aspect ratio and delivery specs are set before final production
  (MotionMedia, challenges list).

## Pacing, cuts and sound

### Josh Noel, SonduckFilm (bYhtddGkVxQ)

- Split layers on the beat for hard cuts; change the palette on a beat before adding title animation
  [00:00:32], [00:01:38].
- A 1-frame scale pulse to 116 % and back on a beat [00:04:49]. Title tracking resolved in 5 frames
  or fewer [00:04:17].

### Ben Marriott (ythBGTLjot8, Ut8bDuNqbLo)

- Match-cut scale ramp: 100 to 105 % before the cut, mirrored after; more is "maybe even overkill"
  [00:01:12 to 00:01:47].
- A 2-frame wipe works as a cut; add a reaction after it (coins bouncing) [00:03:42 to 00:04:15].
- Anticipation before the cut decides whether the match reads [00:07:38].

### Herman Huang (tzfzkTAQsnE)

- Layer hits by frequency (deep, mid, high) instead of searching for one perfect whoosh [00:00:34 to
  00:01:06].
- Commit to one sound style per project [00:03:23].
- Music exit: cut before the next beat, extend the last beat with reverb; entrance: a reversed beat
  as a riser [00:05:17 to 00:06:33].

### AEJuice (doc)

- Discrete hits on beats favor markers and splits; continuous reactivity favors Convert Audio to
  Keyframes and an amplitude expression. Deciding condition: hits or pulse.

### Measured here (live 27.0) [added]

- A percussive stem through `silencedetect` gave every beat within 0.01 frame of the true grid at
  124 bpm. Cuts placed by eye were 2 to 6.4 frames off the beat; snapping brought all ten within 0.5
  frame.
- A whoosh peaks about 0.35 s into the file: it starts before the cut, so the peak lands on it.

## Variants and templates

### Jake Bartlett (HGXP8JHWaSU, -XzXh4E6N5o)

- One normalized 0 to 100 control drives every property of a transition with `linear()` [00:08:35,
  00:11:49].
- One precomp with Essential Properties, duplicated as instances with different values [frames
  00:04:06 to 00:10:36].
- Multi-layer rigs cannot be saved as a preset; save a template or collapse to one layer [00:27:44].

### Evan Abrams (EG7m3j1X9hQ)

- Name layers by function and rename text layers, so edited text does not rename the layer
  [00:02:06].
- Auto-size a box from `sourceRectAtTime()` plus padding [00:03:16 to 00:05:30].
- Arrays (Position, Scale) are exposed through a slider [00:11:35]. Warn on fonts the end user may
  not have [00:12:41].

### Mike Murphy and Adobe Help (5MSoerQYHws, responsive design doc)

- Protected regions keep intro and outro timing when a nested comp or MOGRT is stretched; only the
  middle stretches [00:02:51].
- Create Intro and Create Outro each make a region of 15 % of the comp duration (Adobe Help).
- After editing the source comp, Layer > Markers > Update Markers from Source [00:03:18].

### Video automation company (wqQjvU-2XSg, multi-language doc)

- One data row per output; templates times rows multiplies output (3 templates x 100 rows = 300)
  [00:01:56].
- Captions: 2 lines max, 32 to 40 characters per line, 1 to 7 s on screen, background boxes on busy
  footage. German runs about 30 % longer than English.
- Automation pays from about 4 languages or frequent updates (vendor claim).

## Finishing and restraint

- UI inserts: influence 80 on a stopping key; tap feedback about 10 frames (Cameron Perry,
  wNFHUvtogOE 00:05:35, 00:10:45).
- Product promos: "subtle, smooth, and quick" (NaughtyyJuan, 5j4HmfgPCDI 00:03:13).
- Logo end cards: vector logo converted to shapes, or a native Advanced 3D extrusion with an
  environment light (SonduckFilm, Y2Pb15oR8Nw 00:00:47).

## Where the experts disagree

| Question                              | Positions                                                                 | Deciding condition                                          |
| ------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Length                                | 30+ s for rewarded and interstitial (ad network doc) vs short social cuts | placement and guaranteed attention                          |
| Cut on the beat or action on the beat | Lieu prefers action on the beat; Noel cuts on it                          | cut-driven montage vs a shot with a strong action inside it |
| Sync method                           | markers and splits vs amplitude keyframes                                 | discrete hits vs continuous pulse                           |
| Pre-production depth                  | full boards and styleframes (SOM) vs skip for simple pieces (MotionMedia) | client involvement and scope                                |
| Template engine                       | expression rig inside After Effects vs data-driven automation             | number of outputs and who runs it                           |
