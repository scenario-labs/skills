# Critique: judging a composite

Run this before showing any key, cutout or cleanup. Numbers first (`scripts/matte_metrics.py`, the
job results), then one contact sheet per shot read once. If a number fails, fix and rerun; do not
show the frame.

## Numbers

| Check                     | How                                                                                                 | Pass                                                                                                                                               |
| ------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Chain order               | effect match names on the keyed layer                                                               | `Keylight 906`, then `ADBE KeyCleaner`, then `ADBE Spill2`                                                                                         |
| Keylight View at delivery | `Keylight 906-0002`                                                                                 | 10 (Intermediate Result) with the suppressor, 11 (Final Result) without; never 5 (Screen Matte) or 9 (Status)                                      |
| Despill controls by View  | `Keylight 906-0019` Replace Method, `-0007` Despill Bias, `-0052` Edge Colour Correction            | changed only on a Keylight-only key at View 11; at View 10 they have no effect, so a change there fixes nothing                                    |
| Keyed keying properties   | interpolation of keys on Keylight and suppressor properties                                         | Hold when several interacting properties are keyed; Linear for a single one                                                                        |
| Screen color              | `Keylight 906-0004`                                                                                 | sampled from the plate, one dominant channel; not the default                                                                                      |
| Screen Gain               | `Keylight 906-0005`                                                                                 | 100 unless justified; above 110 is a red flag for holes                                                                                            |
| Screen Pre-blur           | `Keylight 906-0010`                                                                                 | 0 when the shot has hair finer than 2 px                                                                                                           |
| Screen left               | `levels` on a screen box of the alpha view                                                          | 99th percentile 0                                                                                                                                  |
| Core holes                | `holes` on alpha at first, middle, last frame (no reference needed); or `alpha` against a reference | holes under 1 %; stray alpha outside under 0.01 %                                                                                                  |
| Edge rim                  | `rim` on the key over black and over white, before light layers                                     | median 0.85 to 1.15                                                                                                                                |
| Core blur                 | alpha view of the core with and without its blur                                                    | no alpha outside the unblurred core edge (procedure 2b)                                                                                            |
| Hair and veils            | `alpha --labels` or a crop, against the previous version                                            | gray kept: coverage not lower than the previous version                                                                                            |
| Spill                     | `spill` on a white or light-gray garment                                                            | green (or blue) excess within 0.005 of 0; luma within 1 % of the plate                                                                             |
| Garbage matte             | mask keys on the keyed layer                                                                        | keyed when subject or camera moves; feather 10 to 30 px at 1280 wide                                                                               |
| Track mattes              | `hasTrackMatte`, `trackMatteLayer`, matte `enabled`                                                 | resolved; matte hidden; no matte of a matte                                                                                                        |
| External matte            | frame counts and fps of matte and plate                                                             | equal; alpha on first, middle, last frame lines up                                                                                                 |
| Alpha interpretation      | procedure 10                                                                                        | renders and generator outputs on black read `PREMULTIPLIED`                                                                                        |
| Levels match              | per channel with a neutral pair: `sampleColor` on both layers; with none: `light` luma percentiles  | within 2/255 per channel; or p1 within 0.03, p99 at most 0.02 above the plate near the subject                                                     |
| Light match               | `light` on the foreground alone and the plate (procedure 6b)                                        | source in frame: `key_strength` at least 0.3; rim facing at least 1.15 and 0.1 above away. Key direction and rim hue reported, judged on the frame |
| Grain                     | `grain` on flat areas of the same tone; `tgrain` on static areas only                               | within 10 % per channel; Add Grain Viewing Mode 3                                                                                                  |
| Light wrap                | `wrapbins` with and without the wrap                                                                | darkest background bin under half the brightest; 0 outside the subject                                                                             |
| Cleanup patch             | `diff` against the plate's clean area                                                               | inside the patch near the grain floor; no ring at the feather                                                                                      |
| Pre-render                | `diff` live against pre-rendered alpha                                                              | 0; `replacedLayers` equals the uses                                                                                                                |
| Project color             | `app.project.bitsPerChannel`, `workingSpace`, `linearBlending`                                      | what the owner set; luma mattes re-read if it changed                                                                                              |

## Contact sheet

One sheet per shot (`ae.py sheet`), at least: Status view, alpha view at first, middle and last
frame, the final over the real background, the final over flat gray, and a 200 to 400 % crop of the
hardest edge.

Look for, in this order:

1. Background: gray specks or a ghost of a stand in the alpha view. Fix with the garbage matte or
   Clip Black.
2. Core: dark pinholes in the body. Fix with the core matte, not by raising Screen Gain.
3. Hair and semi-transparent cloth: strands present as gray, not cut off at the core edge, not
   speckled. Fix with a holdout on the core.
4. Edge color: green or magenta rim over gray; dark rim over white (premultiplied read as straight);
   bright rim over black.
5. Edge softness: the edge as soft as the plate's own edges; motion-blurred edges still blurred.
6. Levels: the foreground's darkest shadow no darker or lighter than the background's.
7. Grain: grain on both layers, the same size and color; check in shadows, mids and highlights.
8. Light wrap: visible only where the background is bright; no glow on dark edges.
9. Light direction: highlights and shadows on the same side as the background's light, a rim on the
   edge facing the source. Fix with procedure 6b; what it cannot fix, report with the `light`
   numbers.
10. Cleanup: no smear, no repeated pattern that jumps, no ring, the patch moving with the fabric on
    every frame; a hero-frame patch mask lines up on the hero frame only, so read the first and last
    frames.
11. Motion: look at three frames spread over the shot; chatter or a matte that slips shows only
    across frames.

## Severity

- Blocking: screen left in the background, holes in the core, a ring at the edge, a patch missing on
  some frames, a slipped external matte, the wrong alpha interpretation.
- Fix before delivery: spill above tolerance, grain or levels outside tolerance, a visible wrap
  glow, edge harder than the plate.
- Note to the user: light direction mismatch, plate problems a key cannot fix (motion blur through
  the screen color, a compressed 4:2:0 source).
