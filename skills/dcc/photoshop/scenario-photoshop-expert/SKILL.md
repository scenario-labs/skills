---
name: scenario-photoshop-expert
description: 'Use when an agent drives Adobe Photoshop on macOS for any task: running ExtendScript or Action Manager code in a live Photoshop 2026 (27.x), sending a selection, layer or canvas from an open PSD to a Scenario model and bringing the result back as a layer, checking a generated edit with numbers (pixels changed outside the mask, texture loss, edge halo, skin tone) or 100% crops, auditing a PSD before delivery (web, print, social, game texture, layered handoff), running one edit or a recorded Action over many files, turning a Photoshop frame into a video, or routing a Photoshop brief to a specialist. Also when a Photoshop script fails silently or oddly: a transform that does nothing, an interpolation name accepted but ignored, a reserved word, a layer kind that throws, error 8800, or an agent that saved or closed the user''s file.'
license: MIT
---

# Photoshop expert (router and agent protocol)

Expert Photoshop work with generated images is a round trip: capture pixels, generate with a
Scenario model, land the result as a non-destructive layer, measure it, look at it at 100%, deliver
a copy. This skill is that protocol, the shared toolkit the other scenario-photoshop-\* skills
import, and the map to them. If a sibling skill named here is missing from your available skills,
ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended,
proceed from tool schemas and flag the gap.

**Status (2026-10-23):** every toolkit call in the stages is verified live on Photoshop 27.11
(macOS) by the live suites. The Live channel is verified live in part (a paid selection edit
2026-10-20, free steps 2026-10-23). Not tested: toolkit gates after a plugin landing,
`inspect_result_previews` on an edit, a masked proposal-card landing, the upload card, a
specialist's pipeline through the plugin, the `social` profile, `app.doAction`, the batch loop, and
Windows.

## Stance (the expert delta)

- **Never save, close or flatten the user's file; every output is a copy.** Glyn Dewis told his
  agent "don't save it" [ZGsgdObKOZA 02:05]; on a later task it tried to save and he stopped it
  [ZGsgdObKOZA 06:20]. So the rule lives in code: `ps_run` refuses save, close and quit in a job
  body.
- **Every result lands as a new named smart object over the untouched original.** Dewis's agent made
  the sky a smart object so its blur stayed editable [ZGsgdObKOZA 06:51]; Unmesh Dinda's complaint
  about built-in actions is effects "burned into the pixels" [6vsnsS92gKc 11:57].
- **One job, one named History state, one named layer.** Dinda plays long actions as a single
  History state [6vsnsS92gKc 11:24]; the Art, Life & Photography channel calls renaming an action's
  layers good practice [MQDF-UW5-Uk 06:38].
- **Select tight, capture with padding.** The model fills the selection it gets: Julieanne Kost
  [1bFcFVbbzjc 07:13]. A model shown only the crop lacks context: Jesús Ramirez [Ot_h4s1mXas 01:36],
  Kost [1bFcFVbbzjc 07:46].
- **The mask in Photoshop, not the model, keeps the outside exact.** Colin Smith shows Harmonize
  regenerating the whole image and masking it [dWiOA5YZXwc 03:19]. Measured on one Scenario
  image-edit job, two takes: outside mean difference 17 to 18 before masking, max 0 after masked
  placement.
- **Measure before trusting a call or a take.** Dinda and Colin Smith check alignment with the
  Difference blend mode [mSgSaisb6Kg 04:55] [iy0IxTpT4OY 03:47]. [added] On 27.11 a transform, a
  warp or an interpolation name can return success and change nothing, so each new descriptor gets a
  gate or a preview.
- **Judge at 100%, then at viewing size.** Ramirez: "Any other zoom level can be misleading"
  [a7E4HlrAc3w 01:05]. Jared Verdi's agent renders the canvas and reads it before finishing
  [ojOTkInaZIk 11:08].
- **Quote before every paid run; one yes for a batch.** A bad take still "counts against your
  limits": Dinda [mSgSaisb6Kg 08:44]. [added] The user owns the spend.

## Establish first

| Input                | Changes                                 | Default when the user is silent                |
| -------------------- | --------------------------------------- | ---------------------------------------------- |
| Which document       | every job edits the active document     | the frontmost one, confirmed by name           |
| What must not change | the mask, the gates, the prompt         | faces, products, logos, text                   |
| Scope                | selection, one layer, or the canvas     | the active selection; none: ask                |
| Deliverable          | the audit profile and the export format | `psd-handoff` at the document's size and depth |
| Takes and budget     | how many paid runs to quote             | one take; 2 or 3 when the user wants a choice  |
| One file or many     | one round trip, or the batch procedure  | one file                                       |
| Work folder          | where captures, results and copies go   | a new folder, never the PSD's own folder       |

## Workflow

Import once: `sys.path.insert(0, "<this skill>/scripts")`, then
`import ps_run, ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A`. Each call is one
ExtendScript job ("job" below; a paid run is a Scenario job). A library call raises `RuntimeError`
on failure (`ValueError` for a bad argument, before any job); a raw `ps_run.run` returns `ok`,
`error` and `exit`. The user keeps working meanwhile: never bring Photoshop to the front, click the
screen, or open a modal dialog.

**Live channel: Scenario for Photoshop.** When the `scenario-photoshop` tools return `connected` and
`signed_in` true, stages 3 to 5 of a step in the plugin's lanes go through them, as the
`scenario-photoshop` skill teaches, with its take checks, warnings and card stops. Never mix the two
routes' Scenario calls inside one stage.

- Stage 3: `capture_reference` replaces `IO.export_region` and `IO.export_mask`.
- Stage 4: `list_models` and `model_schema` replace `recommend`; `upload_reference`,
  `estimate_cost`, `generate`, `wait_for_job` and `inspect_result_previews`.
- Stage 5: `prepare_result_application` with the kept `takes`, then `apply_result_application`,
  replace `IO.place`. Gate on the returned `history_state` ("Scenario agent: <action>") and an
  edit's `outside_check`. Switch off, neither returns: once `job_status` reads `committed`, gate on
  its `history_state` and run stage 6's `G.diff` outside.
- They replace a specialist's capture and History gates. Stages 6 to 8 run as written.

1. **Connect and read.** `ps_run.find_photoshop()`, `ps_run.run("return app.version;")` (exit 3:
   `ps_run.py --launch`; exit 6: the user allows automation), then `A.doc_state()`. GATE: exit 0;
   the document name matches the brief; `saved`, bits and profile recorded.
2. **Route.** Pick the owner in Handoffs and write down any chain. GATE: one owner per brief before
   the first edit.
3. **Capture.** `sel = IO.selection()["bounds"]`, `cap = IO.export_region(out, pad=32)`,
   `IO.export_mask(out_mask, bounds=cap["bounds"])`. Whole-image edits capture the canvas with no
   mask. GATE: both files share `cap["bounds"]`; the selection covers only what should change.
4. **Quote and generate** through the Scenario MCP with the `scenario` skill (or the Live channel):
   `recommend` for the capability, upload, price the exact payload, get the user's yes, run, wait,
   download. A saved Scenario workflow runs through `scenario-workflows`. GATE: the user approved
   this payload's price; the result has the capture's aspect.
5. **Land.** `h0 = A.history()` right before, then
   `IO.place(result, name, bounds=cap["bounds"], mask_selection=True, xmp={...}, undo="Scenario: <action>")`:
   an embedded smart object, fitted, masked, with provenance; the selection stays active for
   stage 6. One layer per take. GATE: returned `bounds` equal the capture's;
   `A.history_gate(h0, "Scenario: <action>") == []`; the original is visible underneath.
6. **Gate.** `G.diff(None, base, region="outside")`, `G.texture`, `G.halo`, `G.stats`, and
   `G.structure` after a tone change. GATE: the numbers in Quality gates.
7. **Look.** `R.preview(path)` for the whole canvas, `R.preview(path, crop=box, max_px=0)` for each
   seam, face, edge and line of text, `R.sheet` for takes, `R.overlay` after a tone change. Judge
   with [critique.md](references/critique.md). GATE: every crop opened; verdict pass, fix or reject.
8. **Deliver.** `A.deliverable(profile)`, `A.histogram_clip()`, then `R.preview(out, max_px=0)` or
   `psr_export` for copies (png, jpg, tif, psd, tga). GATE: `deliverable` returns `[]`; `saved` is
   unchanged by the agent.

**Many files.** Prove stages 1 to 8 on one file, get one yes for the batch, then run one job per
file that opens it, registers it, applies the recipe, exports and closes it. Skip files the user has
open; stop at the first failure ([procedures](references/procedures.md) P10). **The user's
Actions:** read the steps first, then `app.doAction` (P11).

## Numbers

| Value                   | Relative to                                   | Source                                                         |
| ----------------------- | --------------------------------------------- | -------------------------------------------------------------- |
| `pad` 32 px or more     | capture around a selection                    | [added], model context                                         |
| diff max <= 2           | outside the mask, composite against the base  | measured                                                       |
| mean 17 to 18           | outside the mask, model output before masking | measured, one Scenario job, 2 takes                            |
| bias < 12, residual < 6 | seam ring just outside the mask               | measured, generative-edit                                      |
| texture ratio >= 0.6    | after over before, same region                | authoring-time                                                 |
| rim <= 8                | `light_rim`, `dark_rim` of a cut-out          | authoring-time                                                 |
| 123 degrees, +-10       | vectorscope skin line, `skin_line_delta`      | Kost (123) [Aj_xqQI3gs0 07:24]; toolkit, authoring-time (+-10) |
| drop >= 10%             | structure score, to keep an Auto-Align        | measured, restore                                              |
| mean < 6 at 256 px      | upscale against its baseline (identity)       | measured, upscale-restore                                      |
| 1600 px, sRGB 8-bit     | preview long edge                             | toolkit default                                                |
| 120 to 300 s            | `ps_run.run` timeout per job                  | toolkit defaults                                               |

Authoring-time thresholds: check them on your own images.

## Quality gates

Code gates, in order:

- Document name equals the brief at every editing job.
- Capture and mask bounds equal; placed bounds equal the capture.
- One History state per named edit: `A.history_gate(h0, undo) == []`, with `h0 = A.history()` taken
  right before the call. The gate reads the active state: its name, and that it is a new state on
  top of `h0`. Never the list length (captures leave redo states); the index only below the History
  limit, where it stops moving. To undo one edit, `A.step_back(h0, undo)`. No job without `undo=`
  edits pixels.
- A take equal to its input (`edited` false) is still billed. Check the mask field and its polarity
  first; if both are right, change the member, not the prompt, and quote again.
- **After a call raises or times out**, decide from History. A timed-out job ("timed out" in the
  error, exit 4 from a raw run) may still finish: read `A.history()` a few seconds apart until it
  stops moving, and ask the user to close any modal dialog. Then `p = A.history_gate(h0, undo)`:
  - `[]`: the call left its state. `A.step_back(h0, undo)`, then compare `IO.selection()["bounds"]`
    with `sel`.
  - "no new History state" in `p`: nothing changed. Fix what the error names; run it again.
  - Anything else: stop and tell the user. Never retry on top of a partial state.
- Outside the mask: `G.diff(...)["worst"]["max"]` <= 2. On a stack with adjustments above the base,
  compare captured files instead.
- Texture ratio, halo rims and skin line within Numbers; structure compared between candidates,
  never against a fixed value.
- `A.deliverable(profile) == []`; `saved` and the file's modification time unchanged by the agent.

Visual gates:

- Whole canvas at viewing size: composition, nothing new that jumps out.
- 100% crops: no seam, tone step, halo, soft or smeared patch, grain mismatch.
- Must-keep elements unchanged; hands, eyes, text and logos intact.
- Losing takes hidden and named in a group named "Takes", never deleted (`A.deliverable` accepts
  them there); every agent layer named.

## Common mistakes

| Mistake                             | Looks like                                       | Fix                                                 |
| ----------------------------------- | ------------------------------------------------ | --------------------------------------------------- |
| Saving or closing the user's PSD    | the file changes on disk; unsaved work lost      | `psr_export` copies; `psr_close` only own documents |
| Whole canvas sent for a local edit  | soft patch, drift outside the edit               | capture the selection with `pad`, place in that box |
| Loose selection                     | subject grows, extra objects at the mask edge    | select only what should change                      |
| Trusting a silent success           | a transform or resample that did nothing         | a gate or a preview after each new descriptor       |
| Judging the downscaled preview      | seams and halos found by the client              | 100% crops of every seam and edge                   |
| Editing whatever document is active | the edit lands in another file                   | check `app.activeDocument.name` in every job        |
| Playing a user's Action blind       | it saves, flattens, or merges a smart object     | read its steps; play it on a duplicate              |
| Reading layer kinds from the DOM    | a shape reads `SOLIDFILL`; Clarity throws        | `ps_audit` (Action Manager `layerKind`)             |
| Skipping the audit                  | a 16-bit or wide-gamut master shipped to the web | `A.deliverable("web")` on the exported copy's specs |

## Handoffs

Receives any Photoshop brief. Routes it:

| Brief                                                                         | Owner                                                     |
| ----------------------------------------------------------------------------- | --------------------------------------------------------- |
| Remove, replace, recolor or add inside a selection; extend the canvas; angles | scenario-photoshop-generative-edit                        |
| Our trained style (trained model, LoRA) inside a selection                    | scenario-photoshop-generative-edit                        |
| Our trained style as a new layer: game asset, texture, campaign art           | scenario-photoshop-game-art or scenario-photoshop-key-art |
| Upscale for print, restore or colorize an old photo                           | scenario-photoshop-upscale-restore                        |
| Subject into a scene, cut-out edges, split into layers, skin after an edit    | scenario-photoshop-compositing                            |
| Campaign files, live type, sizes per channel, template variants               | scenario-photoshop-key-art                                |
| Design or logo onto a product photo, one export per design                    | scenario-photoshop-mockups                                |
| Seamless textures, sprites, icons, UI, paintover of a 3D render               | scenario-photoshop-game-art                               |
| The same edit over many files; the user's Actions                             | this skill (P10, P11)                                     |
| Layers for parallax or a background plate (animation, learning)               | scenario-photoshop-compositing, stage 9                   |
| One character across a series of frames (animation, learning)                 | `scenario-consistency`, outside Photoshop                 |
| Image to video                                                                | `scenario-video`, outside Photoshop                       |

Connection, model choice and quoting go to `scenario`, or to `scenario-photoshop` on the Live
channel. A brief can chain: a packshot campaign is compositing (product into a generated scene),
then mockups (label per variant), then key-art (sizes and type), then the audit per channel.

**Handoff contract:** the receiving skill gets the document name, the layers made and their History
state names, the gate numbers, the crops looked at, and the list of what was not verified.

## Photoshop 2026 notes

- Measured on 27.11. Read `app.version` every session: descriptors are undocumented and move.
- Photoshop's generative tools have no toolkit call and no documented script call (traps, section
  1). Offer them to the user as manual steps, and play no Action that holds one.
- AppleScript given a file alias fails with error 8800; `ps_run` inlines `$.evalFile`.
- ExtendScript is ES3, and Java keywords are reserved: `{native: 1}` fails to compile.
- Free Transform by Action Manager needs `freeTransformCenterState`, or it can change nothing.
- Image Size accepts any interpolation name silently; `deepUpscale` is likely Preserve Details 2.0,
  not proven. Check the output by its effect.
- Histograms count the selection on the active layer only; Replace Contents renames the layer;
  deleting the active History snapshot reverts the document.

## References

- [references/procedures.md](references/procedures.md): P1 to P12, the calls in order with their
  test status. Load before the first job.
- [references/photoshop-2026-traps.md](references/photoshop-2026-traps.md): capability matrix,
  channel limits, Action Manager traps, measured generated-pixel facts, version notes. Load before
  writing a job body of your own.
- [references/critique.md](references/critique.md): the rubric for every gate. Load at stage 7.
- [references/gui-paths.md](references/gui-paths.md): menu paths for steps the user does (automation
  consent, Actions, Batch, Layer Cleanup). Load when a step has no script.
- [references/expert-notes.md](references/expert-notes.md): what each source teaches and where they
  disagree. Load when a rule needs its reason.
- [references/sources.md](references/sources.md): every video and document behind this skill.

Scripts (each docstring lists every call and its return):

- [scripts/ps_run.py](scripts/ps_run.py): runs one job; the guard, exit codes, prelude helpers
  (`psr_new_doc`, `psr_dup`, `psr_export`, `psr_close`, `psr_owned`, `psr_log`).
- [scripts/ps_io.py](scripts/ps_io.py): `selection`, `export_region`, `export_mask`, `place`,
  `replace`, `layer_xmp`.
- [scripts/ps_gates.py](scripts/ps_gates.py): `diff`, `stats`, `texture`, `halo`, `structure`.
- [scripts/ps_review.py](scripts/ps_review.py): `preview`, `sheet`, `before_after`, `overlay`.
- [scripts/ps_audit.py](scripts/ps_audit.py): `doc_state`, `history`, `history_gate`, `step_back`,
  `layer_find`, `histogram_clip`, `deliverable`.
