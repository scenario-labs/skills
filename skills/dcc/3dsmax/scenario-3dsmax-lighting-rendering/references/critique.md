# Critique rubric: judge your own render

Judge from saved files, never from the frame buffer alone: the frame buffer may show layers
(exposure, LightMix, lens effects) that the saved file does not carry, or the reverse. Thresholds
marked [added] are this skill's starting points, not expert numbers; tighten them to the user's
reference.

## 1. Settings (measurable, from the inspect JSON)

| Check                                   | Pass                                                                                                                      | Source                                     |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Renderer family                         | unchanged from the inspect baseline unless the user asked                                                                 | [added]                                    |
| Material override                       | off for the final                                                                                                         | 4MeUNMFxiPE 00:05:50                       |
| Render hidden lights, render only masks | off for the final                                                                                                         | _biqhqTpW5c 00:04:29, 00:04:51             |
| Stop criterion                          | Corona noise limit 2 to 5 (or 15 to 30 with 2x render and AI denoise); V-Ray threshold set; Arnold AA set or a time limit | _biqhqTpW5c, 1bOmROFahXU, 7Q3GqtJ56OQ      |
| Corona AI denoiser                      | image filter is not High Quality                                                                                          | 1bOmROFahXU frame                          |
| Corona Max Sample Intensity             | not 0 for production                                                                                                      | corona-performance-tab.md                  |
| Arnold depth vs samples                 | no type with depth 0 and samples above 0 unless deliberate                                                                | ZUEnTb6QnD4 frame 00:18:02                 |
| V-Ray quality preset                    | not High Plus                                                                                                             | 3IZ44a70BPw 00:03:25                       |
| Elements                                | light mix and Cryptomatte present when post or variants are expected                                                      | x8H1CNNFPgc 00:08:07                       |
| Light groups                            | every light in a group or deliberately in Rest                                                                            | corona-lightmix.md, vray7-vraylightmix.md  |
| Color                                   | OCIO view with no tone-map or exposure layer stacked; data maps Raw                                                       | qt7FB4UU0qg 00:07:35, dlwDiLsPWgI 00:07:07 |
| Output                                  | new versioned path, EXR when post follows, layers saved through the renderer's own output                                 | vray7-vfb-frame-buffer.md                  |
| Estimate                                | logged before launch and within budget                                                                                    | [added]                                    |
| Camera exposure                         | one entry mode: EV, or ISO, f-number and shutter; if both are shown, EV100 = log2(N^2 / t) agrees within 0.5 [added]      | x8H1CNNFPgc frames; arithmetic [added]     |
| Corona resumable final                  | Clear VFB between renders off before a time-budgeted final                                                                | _biqhqTpW5c 00:13:34                       |
| Memory, large or 2x finals              | peak measured on a short test below installed RAM; Conserve memory or out-of-core textures on if close                    | corona-performance-tab.md; method [added]  |
| Several looks in one render             | each sun or environment in its own LightSelect or group; no look needs a channel above 1.0                                | corona-lightmix.md; x8H1CNNFPgc 00:15:39   |

## 2. Image numbers (runner side, `scripts/render_metrics.py`)

| Metric            | Command             | Pass [added]                                    | Read it as                                                  |
| ----------------- | ------------------- | ----------------------------------------------- | ----------------------------------------------------------- |
| Clipped percent   | `exposure IMG`      | under 1 outside windows, lamps and the sun disc | above: exposure too high or a light too hot                 |
| Crushed percent   | `exposure IMG`      | under 2                                         | above: dark corners; add a motivated light or lift exposure |
| Median luminance  | `exposure IMG`      | 0.18 to 0.45 for a day interior display image   | night scenes sit lower by design                            |
| Noise sigma       | `noise IMG`         | worst tile under 1.5x the median tile           | a hot tile locates the noise source; crop it                |
| Detail ratio      | `detail TEST REF`   | at least 0.85 on wall, wood and fabric crops    | below: denoiser smear; lower the noise limit                |
| Flicker           | `flicker FRAMES...` | `jumps` empty                                   | jumps: GI cache or sampling change between frames           |
| Seconds per frame | test render timing  | estimate within budget                          | report hours total before launching                         |

Noise sigma compares renders of the same view and size only; it is not an absolute quality scale.

## 3. What to look at (100 percent crops from `crops IMG OUTDIR`)

Open the corner, center and brightest crops, then the full image downscaled. Name each finding with
its crop.

- **Noise:** grain in soft shadows and dark corners; blotches on walls and ceilings (GI); grain in
  blurry reflections and frosted glass; noise only inside DOF blur (needs AA).
- **Fireflies:** single bright pixels near glossy metal, chrome, water or lights touching geometry.
- **Denoiser damage:** smeared wood grain, fabric weave or tile grout; reflections on walls gone
  flat; waxy faces or plants.
- **Exposure and tone:** blown window frames, flat white sky through glass, crushed blacks,
  highlights that clip hard instead of rolling off (double tone mapping shows as crushed highlights
  and shadows together).
- **Color:** whites neutral on walls and ceilings; sky blue against warm practicals at night; no
  yellow or red cast on whites (a gamma-mode symptom, qt7FB4UU0qg 00:06:55).
- **Light design:** one shadow direction in studio work; fill without its own shadow; rim card not
  visible; backdrop even; sun patch where the brief wants it; light shapes plausible in reflections.
- **Composition basics** (owned by scenario-3dsmax-archviz): verticals straight, horizon level.

## 4. Sequences

Contact sheet of every 10th frame (lead toolkit `max_review.contact_sheet`), then the locked flicker
test. Look for crawling blotches on large flat surfaces, brightness pumping, noise pattern swimming
over textures, and moving objects smearing GI.

## 5. Report format

One line per finding: severity (blocker, fix, note), crop or metric, cause, the setting or light
changed, before and after numbers. End with render time, the estimate it was checked against, and
the files written.
