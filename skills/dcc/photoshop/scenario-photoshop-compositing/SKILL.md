---
name: scenario-photoshop-compositing
description: "Use when placing a person, product or generated element into a new scene in Photoshop, or when a composite looks pasted on: hard, white or dark fringed cutout edges, hair, trees or sky to separate, Blend If or a channel mask, missing contact or cast shadows, light from the wrong side, a color cast that does not match the scene or brightness to grade by eye, a generated patch smoother than the photo, Harmonize or a relight that changed the subject, or a flat image to split into editable layers. Also when skin on a generated, edited or upscaled face looks plastic, waxy or smoothed, a face or eyes changed after an edit, or generated skin turned orange, magenta or green and needs frequency separation, dodge and burn or a High Pass smoother."
license: MIT
---

# Compositing and skin after a generative edit (Photoshop 2026)

Expert compositing makes an element look photographed in the scene: one light, one shadow logic, one
tone, one grain. The cutout is judged on several backgrounds, shadows come in two layers, and tone
and grain are matched to the ring of scene around the element, with numbers before and after. Skin
after a generative edit gets the same discipline: texture is measured against the original, the hue
is checked against the skin line, and repairs go on their own layers. Photoshop masks, matches and
measures; Scenario models supply plates, elements, relights and layer splits. If a sibling skill
named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-photoshop-expert (execution channel, round trip, gates).

**Status (2026-10-19):** every call in [`scripts/ps_composite.py`](scripts/ps_composite.py)
(`subject_mask`, `channel_pick`, `blend_if`, `fix_halo`, `shadows`, `match_tone`, `match_grain`) is
verified live on Photoshop 27.11 (macOS) by `test_composite_live.py` (10 tests on a sample photo and
a fringed disc). [`scripts/ps_retouch.py`](scripts/ps_retouch.py) is verified by
`test_retouch_live.py` (frequency separation at 8 and 16 bits, radius pick, smoother, dodge and
burn). `skin_tone` is not run live; the `G.stats` skin line it wraps is, on a flat patch. Not
tested: a real portrait, hair through `subject_mask`, Harmonize, any Scenario step, layer-split
placement, Windows.

## Stance (the expert delta)

- **Harmonize and relighting regenerate the subject; keep the original under the result.** Harmonize
  generated the whole layer and masked what changed, at 1024 px in 2025 (Smith [dWiOA5YZXwc 03:19]);
  a hat lost detail at 200% (Smith [dWiOA5YZXwc 05:05]). New textures, edges and hair appear between
  variations (Kloskowski [JGbvUOytwX0 02:46]). A Scenario image-edit job measured the same
  (Numbers). Mask the original back over faces, logos and fine edges.
- **Take the light, control the color.** Smith sets a copy of the harmonized layer to Luminosity,
  which keeps the original color, then brings the full result back only partway (Smith [C2lo7ew8lHY
  06:33, 07:06]). When every variation is too dark, a clipped Levels layer fixes it, shadow included
  (White [seXzZzjG9HI 04:57, 05:29]). Natural scenes work; painted, stylized light does not survive
  (Smith [dWiOA5YZXwc 12:25]).
- **Cut by what separates subject from background.** For trees, sky and smoke, find the channel with
  the most contrast and use Blend If (Ramirez [mectUNmeOz8 02:04]); split a slider for a soft edge
  (Ramirez [Wkti_IX3Qzk 02:44]). A smart object then freezes the transparency (Ramirez [mectUNmeOz8
  03:38]). Remove Background on the same tree lost the ground, thickened branches and left a sky
  halo (Ramirez [mectUNmeOz8 04:09]).
- **Judge a cutout on black, white and gray; fix the halo on the mask.** An edge that looks clean on
  white can fail on black (PHLEARN [p36McKBhQe8 02:03]); Ramirez checks on a gray fill (Ramirez
  [mectUNmeOz8 02:36]). A remaining outline goes with Minimum, roundness on, applied to the mask
  (Ramirez [\_PNUQDm6lrA 12:07]). Edge softness matches the plate's depth of field (Ramirez
  [\_PNUQDm6lrA 11:34]).
- **Two shadows from the key light: dense contact, then the cast.** Contact first, densest where
  surfaces touch, then a lighter cast shadow (Nour [INmkd2ztW4c 35:10, 35:44]). The cast is the
  silhouette on Multiply, transformed onto the ground (Nour [BrMuLGNoPhs 31:00]). Its angle follows
  the scene (Kost [bMXJwZuzP14 19:58]); its edge is sharp in direct sun (Nour [INmkd2ztW4c 50:23])
  and soft in shade.
- **Add grain where generated pixels are smoother, and only there.** Generated fills read smoother
  than the photo at 100% and 200%; Kost clips grain to those layers alone (Kost [YaTBt6nLOd0 03:50,
  04:24]). Gress lays one Overlay noise layer over the whole composite (Gress [aawE1ZFxl78 16:56];
  2023, technique unchanged). The toolkit measures the scene's grain and stops when the element
  reaches it.
- **Generated skin loses texture and can change the face; measure it, keep the original eyes.** A
  generative upscaler smoothed acne bumps away and altered the face around the eyes (Smith
  [UorIb_rGZuc 11:00, 11:33]). After a generative blemish pass, Toma paints his original eyes back
  (Toma [3eURUBIrhRY 05:28]); Badis puts the original face under an upscaled one (Badis [0cjjRoQ9M4E
  08:02]). Moles and freckles are identity: fade them, do not erase (Kloskowski [1zdowFXxtac
  03:11]).
- **Tone on low frequency, texture on high, hue on the skin line.** Choose the blur radius where
  pores just disappear (Ramirez [REt264jFvqE 01:40]; Williams [l2h3J0VDqDE 03:17]); paint the tone
  layer in Lighten to keep texture (Ramirez [REt264jFvqE 08:16]). All skin shares one hue angle, the
  123 degree line (Kost [Aj_xqQI3gs0 07:24]; Ramirez [oZAC8R6zL8A 01:44]); saturation stays below
  the vectorscope's midpoint (Ramirez [oZAC8R6zL8A 03:58]).

## Establish first

| Input               | Changes                                          | Default when silent                                    |
| ------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| Element and plate   | which layer gets masked, shadowed and matched    | the active layer over the layer below it               |
| Key light direction | `shadows(angle=...)`, relight prompt             | read from the plate's shadows; ask if none show        |
| Light quality       | cast shadow blur                                 | soft (shade, overcast); sharp when the plate is in sun |
| Must not change     | what gets masked back after any regeneration     | faces, eyes, logos, text, product shape                |
| Look                | natural match, or a stylized grade on top        | natural; grade after the match                         |
| Engine for light    | Photoshop Harmonize run by the user, or Scenario | Scenario relight when the user wants agent control     |
| Skin brief          | repair texture only, or retouch                  | restore texture and identity; no extra smoothing       |
| Bit depth           | frequency separation recipe                      | the master's own (8 or 16); 32-bit refused             |

## Workflow

`sys.path.insert(0, "<this skill>/scripts")`, then `import ps_composite as C` and
`import ps_retouch as RT` (they put the lead's `scripts/` on the path) and
`import ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A`. Each call is one `ps_run` job;
after one raises or times out, recover as the lead's Quality gates say. Code:
[procedures](references/procedures.md).

1. **Intake.** `A.doc_state()`; name the element layer and the plate; write the key light, the
   must-not-change list and the look in one line each. GATE: document read by name; three lines
   written.
2. **Plates and elements (paid).** Scenario MCP steps: `scenario` for the connection, the price
   quote and the user's yes; `scenario-image` for a plate or subject, with the plate's light in the
   prompt; `scenario-product-shots` for packshots; `scenario-consistency` for a recurring character.
   Land each with `IO.place(path, name, bounds, fit="contain", xmp={...})`. GATE: quote approved;
   scale and horizon read right in `R.preview`.
3. **Cutout.** People and products: `C.subject_mask(layer)`. Trees, sky, smoke:
   `C.channel_pick(keep, drop)`, then `C.blend_if(layer, best, this=...)`, then a smart object. Hard
   cases: a segmentation model named in words (`scenario-image`, step 4; procedures P2), a
   background-removal tool model (`scenario-image-editing`), each quoted, or Select and Mask by the
   user ([gui-paths](references/gui-paths.md)). GATE: `G.halo(layer)` rims at 8 or less, else
   `C.fix_halo(layer, px=1)` and again; edges seen at 100% on black, white and gray (procedures P4).
4. **Light.** Choose one route: Harmonize run by the user on a pixel copy; a relight tool model
   through `scenario-image-editing` (quoted), placed over the original; or clipped Curves by hand.
   Then a Luminosity copy, the color copy partway, and the original masked back. GATE: `G.texture`
   ratio at least 0.6 against the original; identity and edges at 100%.
5. **Shadows.** `C.shadows(layer, angle=a)`: contact and cast Multiply layers under the element.
   Sharp sun: lower `cast_blur`. The silhouette follows the layer mask. GATE: ground under the
   contact darker than before; cast direction matches the plate's shadows at fit-to-screen; contact
   densest where the element touches.
6. **Tone.** `t = C.match_tone(layer, strength=0.5)`: clipped Curves toward the scene ring,
   luminance kept. Contrast or brightness off: a clipped Levels by hand. GATE: `cast_after` closer
   to `cast_scene` than `cast_before`; luminance within 12%; no new cast at fit-to-screen.
7. **Grain.** `g = C.match_grain(layer)` on the element and on each generated patch; each gets its
   own clipped layer, `"Grain match: <layer>"` (`name=` to change it). GATE: `end` within 50% of
   `target` (or `action` none); 100% and 200% crops across the edge match.
8. **Skin after a generative edit.** Same region before and after: texture ratio and
   `RT.skin_tone(region)`. Lost identity: mask the original eyes, teeth and marks back. Lost
   texture: the original's High Pass in Linear Light over aligned skin, or `C.match_grain`.
   Blotches: `RT.frequency_separation(RT.suggest_radius(box)["pick"])`, then `RT.verify_fs()`.
   Shape: `RT.dodge_burn()`; quick smoothing: `RT.highpass_smoother()`; the user paints the masks.
   GATE: ratio at least 0.6; `skin_line_delta` within 10; `verify_fs` max 2 or less (8-bit).
9. **Split into layers (not tested).** The split-into-layers capability in `scenario-image-editing`,
   quoted. Place each piece with `IO.place` on the source bounds, named, in a group above the hidden
   source. GATE: `G.diff(group, source)` small; holes behind objects seen at 100%.
10. **Deliver.** `A.deliverable("psd-handoff")` returns `[]`; canvas preview plus 100% crops of
    edges, contact and skin. GATE: the report names layers, gate numbers and what was not verified.

## Numbers

| Value                                                  | Relative to                    | Source                                                              |
| ------------------------------------------------------ | ------------------------------ | ------------------------------------------------------------------- |
| Halo rim 8 or less                                     | `G.halo`, 2 px band            | authoring-time (lead gate)                                          |
| Texture ratio at least 0.6                             | after over before, same region | authoring-time                                                      |
| Skin line 123 degrees, within 10                       | vectorscope hue angle          | Kost (123) [Aj_xqQI3gs0 07:24]; toolkit, authoring-time (within 10) |
| Frequency separation verify: max 2 or less             | 8-bit; 0 to 1 at 16-bit        | measured live                                                       |
| Radius default: short side / 600, 2 to 12 px           | document pixels                | toolkit; always look                                                |
| Radius pick: 25% of fine detail left                   | `suggest_radius` energy curve  | toolkit                                                             |
| Around 10 px blur for a close portrait                 | one image                      | Williams [l2h3J0VDqDE 03:17]                                        |
| Smoother: High Pass short side / 100 (min 8), blur / 8 | document pixels                | toolkit; Geller 40 then 5 px                                        |
| Tone-layer brush flow 25%, built up                    | retouch layer in Lighten       | Ramirez [REt264jFvqE 07:07]                                         |
| Cast shadow: 35% height, blur 3%, opacity 45           | element height                 | toolkit defaults                                                    |
| Contact shadow: blur 0.8%, opacity 80                  | element height                 | toolkit defaults                                                    |
| Tone match strength 0.5; ring 40 px past a 4 px gap    | element alpha                  | toolkit defaults                                                    |
| Grain tries: amount 1.5, 3, 5, 8, 12; Gaussian, mono   | Overlay 50% gray               | toolkit                                                             |
| Harmonize: 3 variations, 5 credits per generation      | one generation                 | Smith [dWiOA5YZXwc 02:09]; Adobe                                    |
| Re-render outside an edit: mean 17 to 18               | aligned result vs source       | measured, one job, two takes                                        |

Toolkit thresholds are authoring-time: check them on your own images.

## Quality gates

- **Code:** `G.halo` rims; `match_tone` cast distances and luminance; `match_grain` end against
  target; texture ratio and `skin_line_delta` on skin; `verify_fs`; `A.history_gate(h0, undo) == []`
  per call; `A.deliverable("psd-handoff")` returns `[]`.
- **Visual:** edges at 100% on black, white and gray; contact and cast against the plate's own
  shadows; light direction and tone at fit-to-screen; grain at 100% and 200%; eyes, teeth, hair and
  marks against the original. Rubric: [critique](references/critique.md).

## Common mistakes

| Mistake                            | Looks like                                 | Fix                                                                   |
| ---------------------------------- | ------------------------------------------ | --------------------------------------------------------------------- |
| Cutout judged on one background    | white rim on dark plates                   | check on black, white, gray; `fix_halo`                               |
| Remove Background on fine branches | thick branches, filled gaps, sky halo      | `channel_pick` and `blend_if`, then a smart object                    |
| Minimum on hair or fur             | strands thinned or cut                     | clipped color fill in the hair's color (Williams [2Z0CFC7rg8U 04:24]) |
| One shadow layer                   | element floats                             | `shadows`: contact plus cast                                          |
| Cast angle guessed                 | shadow against the plate's shadows         | read the angle from the plate                                         |
| Harmonized layer at full strength  | new face, hair or logo; colors drift       | Luminosity copy; mask the original back                               |
| Moving the subject after Harmonize | baked shadow slides with it                | regenerate after the move                                             |
| Grain on the whole frame           | the photo gets noisier                     | clip to the element or generated patch                                |
| Saturation on skin                 | orange faces                               | Vibrance (PHLEARN [H7HqYscQdpQ 06:28])                                |
| Smoothing generated skin further   | plastic face, texture ratio under 0.6      | restore texture before any smoothing                                  |
| Every mole removed                 | the person no longer looks like themselves | fade marks; keep the original's                                       |

## Handoffs

- **Receives** from scenario-photoshop-expert: document state and round-trip rules; from
  scenario-photoshop-generative-edit: large edits that need tone and grain; from the user: the
  inputs under Establish first.
- **Delivers** a layered PSD: masked element smart objects, named shadow and match layers clipped or
  grouped, retouch scaffolds with black masks, gate numbers. Local fixes inside a plate go to
  scenario-photoshop-generative-edit; soft or small elements to scenario-photoshop-upscale-restore;
  sizes and type to scenario-photoshop-key-art; a design on a product to scenario-photoshop-mockups.
- **Scenario siblings:** `scenario` (connection, `recommend`, quote, Scenario job waiting),
  `scenario-image` (plates, subjects, instruction edits), `scenario-image-editing` (background
  removal, relight, split into layers), `scenario-product-shots`, `scenario-consistency`,
  `scenario-quality-gate` (scoring takes, an Enterprise add-on; otherwise scenario-asset-analysis),
  `scenario-refine-loop` (re-prompting after a failed gate).

## Photoshop 2026 notes

- Harmonize is run on a pixel layer here (on a smart object it is not tested) and has no script
  call: the user runs it ([gui-paths](references/gui-paths.md), not tested).
- Blend If set through `blendRange` works, but `executeActionGet` never reports it: test by effect.
  A layer inserted between a base and its first clipped layer releases the whole chain; the toolkit
  adds directly above the chain's top clipped layer (lead traps, section 4).
- Adjustment layers: Curves points refused at creation, a white mask at birth (lead traps, section
  4).
- Grain, Dehaze, Color Grading and Vignette adjustment layers could not be made by script, so
  `match_grain` uses Overlay noise. The Light adjustment layer (27.10) pauses while layers below it
  are edited (Rudis [m6nSl2-t-iQ 07:19]).
- Relight Layer (September 2026 beta) spends credits only on Done (Smith [P0OsXyEeuvM 04:05]).

## References

- [`references/expert-notes.md`](references/expert-notes.md): each expert's method, disagreements
  and deciders. Load when a case is not covered above.
- [`references/procedures.md`](references/procedures.md): code per stage. Load before writing a job.
- [`references/critique.md`](references/critique.md): the rubric. Load at stages 3 to 8.
- [`references/gui-paths.md`](references/gui-paths.md): Select and Mask, Harmonize, brush work on
  masks, for the user or a computer-use agent.
- [`references/sources.md`](references/sources.md): videos, credentials, URLs, docs.
- [`scripts/ps_composite.py`](scripts/ps_composite.py): mask, Blend If, halo, shadows, tone and
  grain match.
- [`scripts/ps_retouch.py`](scripts/ps_retouch.py): frequency separation, smoother, dodge and burn,
  skin line.
