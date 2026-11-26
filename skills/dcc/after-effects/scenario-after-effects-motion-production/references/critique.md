# Critique: how a creative lead judges the result

Run the numbers first (`AEX.ad.report` in After Effects, then `adtools.py review` on the report and
the rendered mix). Then read one contact sheet per question below. Frame numbers assume 30 fps;
`adtools.py review` scales them to the report's frame rate.

## Numbers (scripted, every variant)

| Check                   | Pass                                                                                                                     | Source                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Hook line on screen     | by frame 3                                                                                                               | [added]; AppLovin asks for the hook in the first 3 to 5 s, a feed decides sooner                                  |
| First cut               | by frame 45                                                                                                              | [added]                                                                                                           |
| Text on screen          | at least 30 frames, and at least 12 + 9 frames per word                                                                  | 1 s floor from the caption guide (captions 1 to 7 s); the per-word rate is [added]                                |
| Captions                | key lines captioned, bold, benefit keywords highlighted                                                                  | AppLovin (most viewers play muted)                                                                                |
| Words per line set      | 7 or fewer, 2 lines max, 32 to 40 characters per line                                                                    | caption guide                                                                                                     |
| Cuts per 10 s window    | 4 to 12 for a fast social cut                                                                                            | [added]; set per brief                                                                                            |
| Logo first frame        | not before frame 30, unless the brand is known                                                                           | Derek Lieu [00:23:49]                                                                                             |
| CTA visible             | 60 frames or more                                                                                                        | [added]                                                                                                           |
| End card hold           | 75 frames or more, and different from the last gameplay frame                                                            | hold [added]; different frame: AppTweak (3x IPM)                                                                  |
| Hook over the product   | the shot under the hook line shows the product (`product: true` in the sheet; read `hook_shot` in the report)            | [added]                                                                                                           |
| Near-empty frames       | no run longer than 9 frames with under 3 % of the frame carrying content (`review --picture`)                            | [added]                                                                                                           |
| End-card content        | median 8 % of the frame or more during the hold                                                                          | [added]                                                                                                           |
| Text contrast           | 4.5:1 for body, 3:1 for large type, measured on the frame (`adtools.py contrast`)                                        | WCAG 2.2                                                                                                          |
| Short spot (under 10 s) | end card and CTA 45 frames or more                                                                                       | [added]                                                                                                           |
| Cut to nearest beat     | within 1 frame                                                                                                           | [added]; measured 0.5 frame after snapping                                                                        |
| Safe zones              | zero violations on every target network                                                                                  | Meta Reels ad specs (14 % top, 35 % bottom, 6 % sides, retrieved 2026-11-25); other networks: their template file |
| Text fit                | no override wider than its box, measured in the master                                                                   | measured: a 39-character hook overflowed a 400 px box at 40 px                                                    |
| Integrated loudness     | target of the brief, plus or minus 1 LU; social default -14 LUFS [added]; broadcast -23 LUFS (EBU R 128)                 | EBU R 128                                                                                                         |
| True peak               | -1 dBTP or lower                                                                                                         | EBU R 128                                                                                                         |
| File                    | exists, and codec, size, fps, frame count, audio stream match: `ae.py probe` on the file, never the `aerender` exit code | the brief; `aerender` exits 0 on a wrong comp name (measured)                                                     |
| File size and bit rate  | under each network's cap                                                                                                 | the brief or the network spec (Apple App Store previews: 500 MB)                                                  |

## Contact sheets (what to look for)

1. **First second** (frames 0, 15, 30 of each variant side by side). Frame 0 alone must say what the
   ad is about with the sound off: a readable line over the product, a subject, motion already under
   way. Reject black, a logo, a fade, a title card, or a HUD-covered frame.
2. **Beat frames** (one frame per shot, at its in point plus 4). Each shot passes clear,
   interesting, new, pretty in that order (Derek Lieu). Two neighboring shots that look alike fail
   "new". A visible game HUD fails "clear" unless the shot needs that part of it (Lieu [00:24:46]).
   Where two shots match, the frames before the cut scale 100 to 105 % with anticipation (Ben
   Marriott, ythBGTLjot8 [00:01:12], [00:07:38]).
3. **Intensity curve** (one frame per second). High open, a dip that teaches, climb in waves (clips
   rated 1 to 3 stars, ordered 1, 2, 3, 1, 2, 3: Lieu [00:19:25 to 00:20:05]), peak, then the end
   card. Flat or constantly rising curves fail.
4. **Safe-zone overlay** (review frames with the guide rendered). No text, logo, CTA or badge inside
   a colored band. Faces and the hero action also stay out of the bands.
5. **End cards** (all variants side by side). One call to action, logo legible, badges below the CTA
   and above the bottom band, the card differs from the last gameplay frame. It matches the final
   frame designed first (Joey Korenman, 1nChUaFL3rc [00:02:54]).
6. **Other formats** (9:16, 1:1, 16:9 at the same times). Text reflowed inside the frame; gameplay
   crop keeps the action. A 9:16 capture in 16:9 keeps about a third of its height: that shot needs
   a reframe by hand or a 16:9 capture.

## What only a person judges

- Does frame 0 stop the scroll? (A model can say whether it is readable, not whether it is
  arresting.)
- The friend test: the one thing a viewer would repeat (Derek Lieu [00:08:59]).
- Whether sound hits feel on the picture at full frame rate. Watch with sound, then once muted.
- Whether the music ends on a cut with a reverb tail (or enters on a reversed-beat riser) instead of
  a fade (Herman Huang, tzfzkTAQsnE [00:05:17 to 00:06:33]).
- A first-time read: show the cut to someone who knows nothing about the game and note what they
  repeat (Derek Lieu [00:26:13]).
- Whether the hook promises something the gameplay then delivers (a misleading hook costs retention
  after install).
- Brand fit of the logo animation, colors and the character's pose.
- Whether a variant is a real test cell: one variable changed, everything else identical.

## Severity

- Error (do not deliver): safe-zone violation, text overflow, missing CTA, loudness off target by
  more than 2 LU, wrong size or frame rate, a hook frame that is black or a logo.
- Warning (fix or explain): text under its reading time, a cut 2 or more frames off the beat, cuts
  per window outside the brief, end card identical to the last frame.
- Note: anything only a person judges, listed with the frame numbers to look at.

## After launch

Read each test cell by hold rate (time watched before skip or close) and IPM (AppTweak). A playable
end card (7x IPM, 47 % better CTR than static, AppTweak) is a separate test cell built outside After
Effects.

## Common mistakes

| Mistake                                           | Symptom                                                                    | Fix                                                                                                         |
| ------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Moving only the in point of a still               | logo out point at 36 s in a 20 s comp (measured)                           | set in and out points together                                                                              |
| Pop keys on a scaled layer                        | logo jumps back to 100 %                                                   | keys relative to the current scale                                                                          |
| Guide layer for review frames                     | overlay missing from `saveFrameToPng` frames                               | `guideLayer = false` for review, disabled for delivery                                                      |
| Three things changed per variant                  | test result not attributable                                               | one variable per cell                                                                                       |
| Logo or black in the first frames                 | hook wasted                                                                | logo on the end card only                                                                                   |
| HUD left on in captures                           | score and buttons compete with the hook                                    | HUD off, or only the part the shot needs                                                                    |
| Music faded out at the end                        | the ending brakes                                                          | cut before the next beat, reverb tail                                                                       |
| Hook line over a shot unrelated to the product    | the promise and the picture disagree                                       | the hook shot shows the product, or the line moves to the product shot                                      |
| Cut to the end card before anything is drawn      | 1 to 2 s of an almost empty frame                                          | the logo starts drawing before the cut (precomp start a few frames earlier), or the card enters fully built |
| Many layers reading one live driver in `aerender` | 48 bars: 4 to 5 s live, 2 to 3 s baked                                     | bake the driver first (scenario-after-effects-expressions)                                                  |
| Parent math added on top of `AEK.text.measure`    | a parented CTA reported under the Reels band while it sat in the safe area | the kit measure walks the parent chain: use its box as is                                                   |
