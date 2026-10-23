---
name: scenario-photoshop-generative-edit
description: "Use when changing only part of an image open in Photoshop with a Scenario model: inpainting or replacing an object inside a selection, removing a person, object or text, recoloring, swapping clothing or a product from a reference image, extending the canvas (expand, outpaint, uncrop, a new aspect ratio), filling a large area in tiles, turning an object to a new angle, markup or annotation-driven edits, or our style from a trained model or LoRA applied inside a selection. Also when a generative fill shows a seam, a soft low-resolution patch or a halo, changes pixels outside the selection, grows past what was selected, comes back stretched or shifted, or when choosing between Photoshop's Generative Fill or Remove tool and a Scenario model."
license: MIT
---

# Generative edits inside a selection (Photoshop 2026)

Expert generative editing changes exactly the pixels the brief names. The selection is the footprint
of the result, context goes around it, and the prompt says what to change and what to keep. The
result comes back through the mask, is measured at the seam and outside it, and is judged at 100%.
Photoshop draws the selection and protects the rest; a Scenario model supplies the pixels. If a
sibling skill named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-photoshop-expert (execution channel, round trip, gates).

**Status (2026-10-19):** every call in [`scripts/ps_generative.py`](scripts/ps_generative.py)
(`capture` in four mask polarities, `check`, `place_edit`, `verify`, `expand`, `tile_plan`) is
verified live on Photoshop 27.11 (macOS) by `test_generative_live.py` (9 tests, two on a real
Scenario inpaint, one placing out of a hidden markup group). Not tested: reference images
(procedures P4), new angles (P7), a tile loop end to end, where an expand model puts the source,
trained-model alignment, annotation edits, gray (partial) selections, Windows.

## Stance (the expert delta)

- **Context and mask are two inputs: send context wide, draw the mask tight.** Photoshop's partner
  models "only see a square crop around your selection" (Ramirez [Ot_h4s1mXas 01:36]). So experts
  select the whole subject to give them context (Marsh [ZCTPo7M8Eyg 10:27]; Kost [1bFcFVbbzjc
  07:46]), which also enlarges the edit. `capture` separates the two: the margin carries context,
  the mask stays on the change.
- **The model fills the mask, so the selection is the footprint of the result.** Measured on a real
  Scenario inpaint: an ellipse wider than an owl's iris grew the new iris over the eyelid rim. The
  same rule widens a selection: new sleeves need room, because the fill "can't generate outside of
  it" (Smith [pgBjkr2X6wI 02:45]). A removal includes the shadow and a few pixels around the object
  (Williams [SB60EQG2HyE 03:49]).
- **The model re-renders the whole frame; the layer mask is the protection.** Measured on the same
  job: mean difference 17 to 18 outside the mask on an aligned result, maximum 0 after `place_edit`.
  Experts saw the leak in Photoshop too: a global prompt changed a bumper (Adobe Live [jXpi5NJANXg
  02:04]); distraction removal swapped an unselected car (White [seXzZzjG9HI 14:11]). Never place a
  result unmasked; run `verify` after every placement.
- **A seam comes from tone or alignment, not texture.** Measured: a raw ring difference (mean 17)
  failed both good takes. On images blurred by 4 px, the good takes scored tone bias 6.4 and 7.3,
  residual 3.5 and 3.4; a 3 px shift gave residual 8.8, a +20 tint bias 20.6. The other seam is
  resolution: a generated area coarser than the photo shows as a softness cliff (Smith [mGV_jkmPjcY
  05:26]; Dinda [CyJgXBJVHkU 00:00]).
- **Say what to change and what to keep, in words.** Instruction models work best with "detailed
  instructional text prompts describing what you want the model to do" (Kost [1bFcFVbbzjc 02:13]);
  "tell the model what you want to keep" (Ramirez [Ot_h4s1mXas 07:01]). Quote text to replace (Kost
  [1bFcFVbbzjc 03:19]); add "still looking like themselves" for people (Smith [qeeAa8pnICc 04:13]).
- **Big areas go in pieces, and a piece never gets an object prompt.** One side at a time puts more
  pixels on each area (Ramirez [fR0CI04XBpM 09:16]). A prompted object in a tiled fill appears "in
  every single box" (Dinda [CyJgXBJVHkU 09:47]). Each piece overlaps real pixels or a seam shows
  (Patterson [S-03awqbtqs 01:40]; 2023, kept because the rule does not depend on the model).
- **Repair on the mask and in layers, not by re-rolling everything.** Paint the mask black over
  spill (Kost [1bFcFVbbzjc 01:38]). Make a clean plate first when the object touches a subject
  (Ramirez [MvxUcebxhRc 04:42]). Keep each edit its own layer: generating again on a generative
  layer replaces it (Smith [f-7wkNmAtDk 02:05]).
- **Photoshop's own tool first when it wins.** The Remove tool spends no generative credits (Nace
  [nmvewzc6MG4 00:13]); Photoshop's own fill model reads context outside the selection (Ramirez
  [fR0CI04XBpM 08:12]), masks to it and returns three variations (White [MsX4_p_BbSQ 01:40]).
  Partner models there return one. Scenario earns the job with more references, a trained style
  inside a selection, the measured outside check, and agent access [added: the toolkit has no
  Generative Fill call].

## Establish first

| Input                 | Changes                                                       | Default when silent                                                  |
| --------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------- |
| Edit type             | capability for `recommend`: inpaint, instruction edit, expand | read from the brief                                                  |
| What must not change  | keep-clauses in the prompt; hair and edges subtracted         | everything outside the selection                                     |
| Selection             | footprint of the result                                       | the active one; none: ask, or Select Subject when the brief names it |
| Engine                | Scenario model, or Photoshop's own tool run by the user       | Scenario; suggest the Remove tool for small cleanups                 |
| References            | layers or files sent beside the capture                       | none; each pre-cut to one object                                     |
| Takes per run         | how many results to compare                                   | 1; 3 when the user wants a choice, quoted as such                    |
| Mask polarity         | `capture(polarity=...)`                                       | from the model's `mask` field (`scenario-image`)                     |
| Model sizes           | `max_px`, tiles                                               | from the schema; capture box no larger than the output               |
| Master depth, profile | nothing in the master                                         | capture writes sRGB 8-bit; the master keeps its own                  |

## Workflow

`sys.path.insert(0, "<this skill>/scripts")`, then `import ps_generative as GE` (it puts the lead's
`scripts/` on the path) and `import ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A`. Each
call is one `ps_run` job; after one raises or times out, recover as the lead's Quality gates say.
Code: [procedures](references/procedures.md).

**Scenario for Photoshop.** When the plugin's tools are connected and signed in, run this skill's
image, edit, upscale, expand and background-removal steps through them, as the lead's Live channel
maps them, gates included; other Scenario steps stay on hosted Scenario MCP. Not tested end to end.
There, `capture_reference` (`purpose: "edit"`) replaces `GE.capture`, and `edit_selection` with kept
`takes` replaces `GE.place_edit`. `inspect_result_previews` replaces stage 5's code gates,
`polarity_suspect` included: keep a take when `aspect_ok` and `edited` are true and no badge reads
"May be misaligned" (width gate: `resolution_ratio` at least 1). The Live channel's outside gate is
stage 7's `v["untouched"]`. `GE.check` and `GE.verify` need a toolkit capture.

1. **Intake.** `A.doc_state()`: name, size, mode, bits, profile, active layer, selection bounds.
   Write the brief as one line to change and one line to keep, then route (last Stance bullet).
   GATE: document read by name; change and keep written.
2. **Selection.** Accept or build it as the result's footprint: Select Subject (`autoCutout`), a
   marquee by script, Object Selection or Selection Brush by the user
   ([gui-paths](references/gui-paths.md)). Subtract hair that must stay in front (Smith [pgBjkr2X6wI
   11:04]); add the shadow for a removal. GATE: `IO.selection()["bounds"]` is set.
3. **Capture.** `cap = GE.capture(out_dir, polarity=p, max_px=n)`. Margin: half the selection's long
   side, at least 64 px, clipped to the canvas. Writes `context.png`, `mask_edit.png` (white =
   edit), the model's `input` and `mask_model`, and `capture.json`; the active History state stays.
   GATE: open `context.png` and `mask_edit.png`: the change sits inside the white, nothing else
   does; box long side no larger than the model's output, else stage 8.
4. **Generate.** Scenario MCP steps: `scenario` for the connection, the price quote and the user's
   yes before the run; `scenario-image` for the member (`recommend` with the capability and the
   user's words), its mask field and references. Upload `cap["input"]`, `cap["mask_model"]` and
   references, ask for the agreed number of outputs, download them. GATE: quote approved; every
   output on disk.
5. **Check each take.** `r = GE.check(cap, path)`. GATE: `aspect_ok`, `edited`, not
   `polarity_suspect`, `seam_ok` (bias under 12, residual under 6), and result width at least the
   box width. Then open each passing take and judge it inside the mask at 100% with
   [critique](references/critique.md). A take that fails a code gate is never placed.
6. **Place.** `h0 = A.history()`, then
   `GE.place_edit(cap, path, "Iris ice blue, take 2", feather=2, xmp={...})`: embedded smart object
   on the capture box, a layer mask rebuilt from `mask_edit.png`, model, asset id and prompt in the
   layer's XMP. A target inside a hidden group (a markup group) is moved out of it first
   (`moved_out_of`). GATE: returned bounds equal `cap["bounds"]`;
   `A.history_gate(h0, "Scenario: Generative edit") == []` (one new named state).
7. **Verify and look.** `v = GE.verify(cap)`; `R.preview(path)` of the canvas and
   `R.preview(path, crop=box_plus_32, max_px=0)` of the seam. On a borderline residual,
   `R.overlay(out, layer, base, crop=box)`. GATE: `v["untouched"]` (outside max 2 or less) and
   `v["edited"]`; no seam at 100% and 200%; grain and sharpness continuous across the edge.
8. **Large areas (not tested end to end).** `GE.tile_plan(box, tile, overlap=64)` with `tile` the
   model's output side minus twice the margin. Count the tiles that touch the edit area; price tiles
   times takes and get one yes. Per tile, nearest the real pixels first: the stored edit selection
   intersected with the tile, then stages 3 to 7. Tile 1 passes stages 5 and 7 before any other tile
   runs. Prompt: empty or a texture description, never an object. GATE: every tile passes stages 5
   and 7; no repeat at fit-to-screen.
9. **Expand.** `cap = GE.expand(out_dir, right=400, overlap=32)`: Canvas Size as one History state,
   whole-canvas capture, the new area plus a 32 px band of real pixels as the edit. `input.png` is
   transparent there; `original.png` serves models that take an image and a target size. Run an
   expand tool model (`scenario-image-editing`) or an inpaint member, then stages 5 to 7; a moved or
   rescaled source fails `check`. GATE: stages 5 to 7; light direction and shadows continue
   (Patterson [S-03awqbtqs 03:14]).
10. **Deliver.** `A.deliverable(profile)` returns `[]`. GATE: the report names takes, gate numbers
    and what was not verified.

## Numbers

| Value                                                   | Relative to                   | Source                       |
| ------------------------------------------------------- | ----------------------------- | ---------------------------- |
| Margin: half the long side, at least 64 px              | selection bounds              | toolkit default              |
| Layer-mask feather 2 px                                 | mask edge                     | toolkit default              |
| `edited`: inside mean 3 or more                         | 0 to 255, context vs result   | toolkit                      |
| Seam: blur 4 px, ring 12 px past a 2 px gap             | outside the mask              | measured, two real takes     |
| Seam pass: bias under 12, residual under 6              | 0 to 255                      | measured, two real takes     |
| Re-render outside the mask: mean 17 to 18               | aligned result vs context     | measured, one real job       |
| `untouched`: max 2 or less, past 2 x feather + 2 px     | composite after placement     | measured 0 after placement   |
| One inpaint returned 1254 px for a 222 px box           | capture box                   | measured                     |
| Expand band 32 px; tile overlap 64 px                   | real pixels                   | toolkit defaults             |
| Photoshop's own fill: up to 2K per generation           | one generation (January 2026) | Smith [mGV_jkmPjcY 06:38]    |
| Tiled fill boxes 500, 1000, 2000 px; smaller is sharper | one generation                | Dinda [CyJgXBJVHkU 02:08]    |
| Gray selection near 25% acts as strength                | selection density             | Williams [0h8lwK-shOY 01:03] |

Toolkit thresholds are authoring-time: check them on your own images.

## Quality gates

- **Code:** `check` flags (`aspect_ok`, `edited`, not `polarity_suspect`, `seam_ok`); result width
  at least the capture box width; stage 6's bounds and History gates; `verify()["untouched"]`;
  `A.deliverable(profile)` returns `[]`.
- **Visual:** each take inside the mask at 100% (anatomy, hands, text, reference fidelity, nothing
  grown past the intended object); the seam at 100% and 200%; the canvas preview for light direction
  and grain; for people, likeness against the original. Rubric: [critique](references/critique.md).

## Common mistakes

| Mistake                               | Looks like                                       | Fix                                                          |
| ------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------ |
| Selection wider than the change       | the new object grows into its neighbors          | redraw on the footprint; subtract what must stay             |
| Bigger mask to give the model context | more of the image regenerated than asked         | keep the mask tight; raise `margin`                          |
| Wrong mask polarity                   | outside changed, inside not (`polarity_suspect`) | re-read the `mask` field; recapture                          |
| Result placed without its mask        | whole box shifts 17 to 18 levels                 | `place_edit` only; `verify` after                            |
| Fixed-aspect output on a long box     | stretched or shifted fill (`aspect_ok` false)    | recapture with a margin that fits a supported ratio          |
| Output smaller than the capture box   | soft patch, grain mismatch                       | tiles, a larger-output member, or upscale the take           |
| Object prompt on every tile           | the object repeats in each box                   | empty or texture-only prompt per tile                        |
| No keep-clause                        | pose, scale or a neighbor changes                | "Keep the same scale and pose" (Ramirez [Ot_h4s1mXas 07:01]) |
| Reference with extra objects          | the hand in the photo comes along                | pre-cut to one object (PHLEARN [7zE6s7_nmIs 11:25])          |

## Handoffs

- **Receives** from scenario-photoshop-expert: document state and round-trip rules; from
  scenario-photoshop-compositing: placed plates that need a local fix; from the user: the brief,
  references, which takes to keep.
- **Delivers** a named, masked smart-object layer per accepted take, with XMP provenance, over an
  untouched original, plus the check and verify numbers. Soft takes go to
  scenario-photoshop-upscale-restore; tone and grain on a large edit to
  scenario-photoshop-compositing, which also takes faces and skin.
- **Scenario siblings:** `scenario` (connection, `recommend`, quote, Scenario job waiting),
  `scenario-image` (inpaint, instruction edit, mask field), `scenario-image-editing` (expand and
  reframe only), `scenario-consistency` (references and identities), `scenario-orbit-views` (new
  angles of a whole subject), `scenario-refine-loop` (re-prompt, swap references or change member).

## Photoshop 2026 notes

- Generative Fill, Generative Expand, the Remove tool and Prompt to edit: Adobe documents no script
  call (Generative Upscale is the one generative call in the scripting DOM, since 27.2). These stay
  manual alternatives for the user ([gui-paths](references/gui-paths.md), not tested here).
- Photoshop's newest fill model uses the selection as a native mask (Adobe help, 2026-08), so
  protection outside the selection is parity, not a Scenario edge. The partner-model lineup changes
  between releases: never route by a Photoshop model name.
- `place_edit` refuses when the canvas size changed since the capture.
- A gray selection shows no marching ants, and Photoshop warns that no pixels are more than 50%
  selected (Williams [0h8lwK-shOY 01:34]); `capture` still exports its density.
- Experts move to 8-bit before partner edits because 16-bit shifted colors (Smith [qeeAa8pnICc
  04:47]); `capture` sends sRGB 8-bit.

## References

- [`references/expert-notes.md`](references/expert-notes.md): each expert's method, the measured
  round trip, disagreements and deciders. Load when a case is not covered above.
- [`references/procedures.md`](references/procedures.md): code per edit type. Load before writing a
  job.
- [`references/critique.md`](references/critique.md): the rubric. Load at stages 5 and 7.
- [`references/gui-paths.md`](references/gui-paths.md): selections and Photoshop's own generative
  tools by menu, for the user or a computer-use agent.
- [`references/sources.md`](references/sources.md): videos, credentials, URLs, docs.
- [`scripts/ps_generative.py`](scripts/ps_generative.py): the toolkit (docstring lists every call),
  on top of the lead's scripts.
