---
name: scenario-after-effects-motion-production
description: "Use when an After Effects job is a commercial piece with a brief: a game UA ad, social cut, trailer, promo, store preview or end card. Triggers: variants for A/B tests, hooks and calls to action, cut to the beat, sound design, LUFS, safe zones for TikTok, Reels or Shorts, 9:16 to 1:1 and 16:9, a shorter cut, review this ad, is this ready to ship."
license: MIT
---

# After Effects Motion Production (creative lead)

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means owning the order of decisions, the edit as data and the verdict. The cut
lives in a beat sheet (JSON in frames), so a variant, a shorter cut or another format is a new sheet
run through one build job, never a hand edit. Every claim about the result is a number read from the
built comp or the rendered file, then a contact sheet, then the short list of things only a person
judges. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

- **Lead with the one thing only this product does.** Shared genre features waste time; the friend
  test is what a viewer would repeat (Derek Lieu, GDC, QWd7F0z1W_Y 00:05:37, 00:08:59). Put the one
  piece of context needed to read the rest first (00:10:12).
- **Frame 0 is the hook.** No fade from black, no unknown logo in the opening (Lieu 00:23:49).
  AppLovin asks for the hook within 3 to 5 s; a feed decides sooner, so the line is on screen by
  frame 3 [added].
- **Shape intensity, not a ramp.** Cold open high, a dip that teaches, climb, climax, a deep dip for
  the call to action, a short button.
- **One variable per test cell.** Hooks change with the CTA fixed, then the CTA changes with the
  best hook (AppLovin doc). A variant that changes three things teaches nothing.
- **Lock timing before animating.** An animatic or beat sheet against the music first; retiming
  animated scenes is "difficult and frustrating" (Cameron Shefer-Boswell, Gqr0WrahBBs 00:05:00).
- **The end card is its own frame.** An end card that differs from the last gameplay frame: 3x IPM
  (AppTweak with Smadex data, 2023). One call to action only (Lieu 00:17:18).
- **Measure sound, then judge it.** Layer hits by frequency (Herman Huang, tzfzkTAQsnE 00:00:34); a
  whoosh peaks on the cut, so it starts before it [added, measured 0.35 s]. Loudness is read from a
  rendered mix: the Audio panel shows peak levels only; After Effects has no loudness (LUFS) meter
  and no master fader.
- **Text is read, not seen.** A line stays on screen for its reading time even if that crosses a cut
  [added]. Caption every game ad: most viewers play muted (AppLovin example: 64 % higher Day 0
  ROAS); bold type, benefit keywords highlighted.

## Establish first

- **Placement and length:** feed (6 to 20 s), interstitial (5+ s guaranteed attention), rewarded
  (unskippable up to 60 s), store preview (Apple: 15 to 30 s, poster frame default 5 s). Length
  follows placement (AppLovin doc).
- **Networks:** each one's safe zone with its source and date (Numbers). Ask for the overlay files
  when a network publishes no numbers.
- **Sizes and rate:** 1080x1920 at the capture's rate, usually 30 fps; durations restated in frames.
  Gameplay at 60 fps into a 30 fps master: decide in the project skill's frame-rate step.
- **Inputs:** captures with the HUD off, or only the HUD part the shot needs (Lieu 00:24:46), and
  their game audio; logo as vector, character art with alpha, store badges from the stores' own
  kits, music with its license, fonts installed (`AEK.text.fontExists`).
- **Test plan:** number of cells, which variable each changes, naming convention.
- **Loudness target:** from the brief; social default -14 LUFS integrated [added], broadcast -23
  LUFS (EBU R 128), true peak -1 dBTP.
- **Channel and session:** bridge by default; a person's open project follows the live-session rules
  of scenario-after-effects-expert.

## Procedure

1. **Brief to beats.** Goal: a beat sheet in frames. Design the end card first, so the cut has a
   destination (Joey Korenman, 1nChUaFL3rc 00:02:54). Rate every clip 1 to 3 stars from its frames
   and order the shots in waves (1, 2, 3, 1, 2, 3), never a straight ramp (Lieu 00:19:25 to
   00:20:05). Write the hook (one unique thing), the intensity curve, one row per shot (clip, source
   frame, text, SFX, level), the end card and a layout row per format. GATE: total frames match the
   placement; the hook line is 7 words or fewer, over a shot that shows the product
   (`product: true`); every text has `frames >= 12 + 9 per word` [added]; key lines captioned; one
   CTA.
2. **Beats from the music.** Goal: cuts on the beat. `adtools.py detect music.wav` fits a tempo and
   a beat grid to the full mix and returns `bpm`, `offset`, `beats` and `confidence`; a `warning`
   means a stem, `--bpm-range` or a known tempo (`grid`) (procedures 3). Then
   `adtools.py snap sheet beats`. GATE: every snapped cut within 1 frame of a beat; no shot under 18
   frames; the payoff on a downbeat (a person picks it by ear).
3. **Build the master.** Goal: one comp from the sheet, one job, one undo step.
   `AEX.ad.build(sheet, items, "9x16", {protect: true})` makes shots, comp markers (protected hook
   and end card), text, SFX at their levels, the end card and the character; then
   `AEX.ad.beatMarkers` on `MUSIC`. A brand or product spot: `sheet.style.preset "brand"` (no
   stroke, no pops, text CTA, scrim under the hook). Procedure 2 in
   [procedures.md](references/procedures.md). Where two gameplay shots match, scale 100 to 105 %
   with anticipation into the cut (Ben Marriott, ythBGTLjot8 00:01:12, 00:07:38); on secondary hits,
   116 % for 1 frame (Josh Noel, bYhtddGkVxQ 00:04:49). GATE: `fits` with no overflow, comp markers
   match the sheet, `AEX.ad.beatOffsets` all within 1 frame; sheet of frames 0, 15, 30 shows the
   hook line readable on moving gameplay.
4. **Safe zones.** Goal: nothing important under platform UI. `AEX.ad.zoneCheck(comp, zones)` on
   every text, logo, CTA and badge layer; `AEX.ad.guides(comp, zones, {render: true})` for review
   frames. GATE: zero violations on every target network; review sheet with the overlay rendered
   shows faces and hero action outside the bands too.
5. **Sound and mix.** Goal: designed sound at the target loudness. Captured game audio muted, SFX
   from the sheet, music under the end-card line. Render the mix to AIFF (`AIFF 48kHz` template),
   `adtools.py loud`, then correct on a bus: nest the master, `ADBE Aud Compressor` on the nested
   layer, Makeup Gain up, Output Limit under the ceiling, measure again. End the music on a cut
   before the next beat with a reverb tail, or enter on a reversed beat as a riser, never a fade
   (Huang, tzfzkTAQsnE 00:05:17 to 00:06:33; ffmpeg recipe in procedures.md). GATE: target plus or
   minus 1 LU, true peak at or under -1 dBTP; a person listens once with picture.
6. **End card.** Goal: a frame that sells one action. Logo, one CTA pill with a slow pulse, badges
   below the CTA and above the bottom band; enters on a beat; differs from the last gameplay frame.
   Logo animation recipes go to scenario-after-effects-shape-layers or scenario-after-effects-3d. A
   playable end card is a separate test cell ([critique.md](references/critique.md)). GATE: hold 75
   frames or more [added], CTA on screen 60 frames or more [added], inside every safe zone.
7. **Variants.** Goal: N test cells from one master. Expose hook text, CTA text and the hook shot
   (media replacement) with `addToMotionGraphicsTemplateAs`; per cell a comp holding one instance
   with overrides; `AEX.ad.lineFor` breaks and measures each override in the master first. Naming:
   [procedures.md](references/procedures.md) section 12. Batch mechanics at scale go to
   scenario-after-effects-scripting. Read the test by hold rate and IPM per cell (AppTweak). GATE:
   every override fits its box (copy that does not fit is rewritten, never shrunk in one cell);
   contact sheet of all first frames and all end cards side by side.
8. **Formats and cuts.** Goal: 1:1, 16:9, shorter cuts from the same data. Other ratios use their
   layout row; a master that is not a gameplay ad (end card, brand spot, product mark) goes through
   `AEX.ad.reformat(master, layouts)`, one comp per layout row with its own texts and zones
   (procedures.md section 7b); shorter cuts are derived sheets (drop shots, re-snap), or Time Remap
   keys that keep hook and end card at speed 1. GATE: text inside the frame at 5 % margins; every
   shot whose cover crop keeps under about 60 % of the capture gets a reframe pass by hand [added];
   a 10 s cut passes the same report.
9. **Review and deliver.** Goal: a verdict per variant. `AEX.ad.report` then
   `adtools.py review --render mix.aif --picture cell.mp4` (adds near-empty stretches and end-card
   content). Render each cell with `H.264 - Match Render Settings - 15 Mbps` (writes `.mp4`;
   measured 18.9 Mbps, so the name is not a cap) from the Render Queue or `aerender`, which exits 0
   on a wrong comp name: gate on the file with `ae.py probe` (procedures.md section 11). Over a
   network's cap, re-encode through scenario-after-effects-color-delivery. GATE: scorecard errors at
   zero, warnings explained; every file matches codec, size, rate, frame count, audio, and the size
   and bit-rate cap from the brief; the person-judged list answered with frame numbers; someone who
   does not know the game watches it once (Lieu 00:26:13). Rubric:
   [critique.md](references/critique.md).

## Numbers

| Value                                  | Meaning                                                                    | Source                                         |
| -------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------- |
| hook text by frame 3                   | at 30 fps                                                                  | [added]                                        |
| 3 to 5 s                               | hook window                                                                | AppLovin doc                                   |
| 12 + 9 frames per word, 30 minimum     | text reading time at 30 fps                                                | 1 s floor Plainly; rate [added]                |
| 2 lines, 32 to 40 characters, 1 to 7 s | caption limits                                                             | Plainly doc                                    |
| 4.5:1, 3:1                             | text contrast on its background, body / large type (`adtools.py contrast`) | WCAG 2.2                                       |
| 4 to 12 cuts per 10 s                  | fast social cut; set per brief                                             | [added]                                        |
| within 1 frame                         | cut to beat after snapping (measured worst 0.49)                           | [added], live                                  |
| 0.35 s                                 | whoosh lead before the cut                                                 | live                                           |
| 75 frames                              | end-card hold minimum at 30 fps                                            | [added]                                        |
| 14 % top, 35 % bottom, 6 % sides       | Meta Reels ads safe zone                                                   | Meta Ads Guide, retrieved 2026-11-25           |
| overlay file                           | TikTok in-feed and Google vertical safe zones (no printed numbers)         | ads.tiktok.com, support.google.com, 2026-11-25 |
| -14 LUFS, -1 dBTP                      | social mix target, true peak ceiling                                       | [added]; EBU R 128 for the peak                |
| -23 LUFS                               | broadcast target                                                           | EBU R 128                                      |
| 15 to 30 s, 886 x 1920 or 1080 x 1920  | App Store preview                                                          | Apple, retrieved 2026-11-24                    |
| 56 % / 32 %                            | share of a 9:16 capture's height kept by cover fit in 1:1 / 16:9           | live                                           |

## Quality gates

- **Measurable:** `AEX.ad.report` shows the hook line at frame 0 to 3, every text over its reading
  time, cuts per window within the brief, logo not before frame 30 unless the brand is known, CTA
  and end-card holds met, beat offsets within 1 frame, zero zone violations. `adtools.py review`
  adds loudness and true peak. `ae.py probe` matches codec, size, frame rate, frame count and an
  audio stream.
- **Visual:** first-second sheet (frames 0, 15, 30 of every variant); one frame per shot (clear,
  interesting, new, pretty, in that order: Lieu 00:18:06); review frames with the safe-zone overlay
  rendered; all end cards side by side; the three formats at the same times.
- **Person-judged, listed with frame numbers:** does frame 0 stop the scroll, does the hook promise
  what the gameplay delivers, do sound hits feel on the picture at full rate, the friend test, a
  first-time viewer's read, brand fit.

## Common mistakes

| Mistake                                   | Symptom                                                                | Fix                                                         |
| ----------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| Cuts placed by eye                        | cuts 2 to 6 frames off the beat (measured)                             | detect beats, `snap` the sheet, check `beatOffsets`         |
| Text stroke over fill                     | white type renders nearly black at 40 px with a 5 px stroke (measured) | `strokeOverFill = false`                                    |
| Shrinking a long line to fit              | 27 px hook at 540 wide                                                 | two balanced lines past 85 % shrink, else rewrite           |
| Override text written as typed            | 500 to 1,037 px in a 400 px box (measured)                             | `AEX.ad.lineFor` in the master first                        |
| Gain on every layer to reach -14 LUFS     | +0.1 dBTP, over the ceiling (measured)                                 | Compressor bus with Output Limit                            |
| `outPoint` or `stretch` for a shorter cut | end card lost, or hook sped up                                         | derived sheet, or Time Remap keys holding hook and end card |
| Trusting the `aerender` exit code         | exit 0, no file (wrong comp name, measured)                            | probe the output file                                       |

More mistakes: [critique.md](references/critique.md), Common mistakes.

## Handoffs

- Receives: the brief and assets; generated clips, art, voice, music and SFX from
  scenario-after-effects-generation (raw input, checked on import); project structure and frame-rate
  decisions from scenario-after-effects-project.
- Delivers the beat sheet, the master comp and the report to scenario-after-effects-animation (pops,
  overshoot, character entry), scenario-after-effects-typography (type looks, localization fit),
  scenario-after-effects-expressions (rigs beyond the variant set), scenario-after-effects-scripting
  (batch rendering, `aerender`), scenario-after-effects-color-delivery (final encode, bit-rate caps,
  color tags).

## Version notes

Essential Properties, track mattes, the Audio Compressor (26.0) and protected regions by version:
[procedures.md](references/procedures.md), Version notes.

## References

- [references/procedures.md](references/procedures.md): every job and command with channel, checked
  line, measured result.
- [references/critique.md](references/critique.md): the scorecard thresholds, contact sheets to
  read, what only a person judges, severity.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps,
  and where they disagree.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same steps.
- [references/sources.md](references/sources.md): every source with URL and retrieval date.
- Helpers: [scripts/adprod.jsx](scripts/adprod.jsx) (`AEX.ad`),
  [scripts/adtools.py](scripts/adtools.py) (beats, snap, loudness, zone from PNG, review).
