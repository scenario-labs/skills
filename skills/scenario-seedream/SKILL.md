---
name: scenario-seedream
description: "Use when generating or editing images with Seedream models on Scenario via MCP: text-to-image, reference-image editing, posters or packaging with exact in-image text, transparent PNG output, keeping a cutout's alpha through an edit, sets of related images in one run, splitting an image into transparent PNG layers with Layerize, or replacing a retired Seedream version. Keywords: Seedream 5.5, 5.0 Pro, Lite, Flash, 4.5, 4.0, Layerize, ByteDance, txt2img, img2img, layer extraction."
license: MIT
---

# Scenario Seedream Images

## Overview

Seedream, ByteDance's image family on Scenario, spans generation, reference-driven editing, and
Layerize members that only take images apart. The members agree on little else, so discover them
with `search` and read `model_schema_get` before every run.

Connection and the core loop: see the `scenario` skill; model-agnostic image work: the
`scenario-image` skill. If a sibling skill named here is missing from your available skills, load it
with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

## Route to a current member

Seedream retires whole generations. Read each `search` hit's `tags` before routing:

- `Deprecated` marks a retired member: never route new work to it, even when `recommend` still ranks
  it or the user names it.
- `deprecated:<model id>` names the successor: switch to that id and read its schema, since fields
  differ.
- A bare `Deprecated` names none: pick the current member by lane below.
- `sc:featured` marks the current flagship.

At authoring time, 5.5 replaced 5.0 Flash, 5.5 Layerize replaced 5.0 Flash Layerize, and 4.0 and
Dreamina 3.1 point to 5.0 Pro. 4.5 carries a bare tag: its edits go to 5.5, its sequence sets to
Lite. Tell the user which member runs instead of the one they named; unattended, run it and report
the swap.

## Quick reference

At authoring time (fields and caps are per member, read the live schema):

| Member           | References                  | Sizing                                         | Notes                                                  |
| ---------------- | --------------------------- | ---------------------------------------------- | ------------------------------------------------------ |
| 5.5              | `referenceImages`, up to 10 | exact `width` and `height`, 672 to 4368, by 16 | default; `background`: auto, opaque, transparent       |
| 5.0 Pro          | `referenceImages`, up to 10 | exact `width` and `height`, 672 to 3136, by 16 | `optimizePromptMode`; `background` keeps alpha         |
| 5.0 Lite         | `referenceImages`, up to 14 | `width` and `height`, 1024 to 6240, by 16      | the only sequence member; 2048-char prompt             |
| 5.5 Layerize     | one `image`, required       | `size` tier: auto, 1K, 1.5K, 2K                | `maxImages` 3 to 100, billed in full; text recognition |
| 5.0 Pro Layerize | one `image`, required       | `size` tier: auto, 1K, 1.5K, 2K                | up to 16 cutouts; `optimizePromptMode`                 |

- **5.5**: the default for generation and edits, 3500-char prompt. `recommend` modeled a 2K square
  at about 6 CU and 30 s, against 9 CU and 86 s on 5.0 Pro, at authoring time.
- **5.5 pixels**: the schema caps the total near 8.3 MP, but the catalog card says about 4.2 MP
  (2048x2048, 2560x1440). Treat 4.2 MP as the ceiling until a run confirms more.
- **5.0 Pro**: when the user asks for it, or to keep an existing cutout's alpha through an edit.
  `optimizePromptMode` `standard` (default) reasons about the prompt first and is slower; `fast`
  costs the same and is usually enough when a reference sets the composition.
- **5.0 Lite**: past 10 references, or a related set in one run: `sequentialImageGeneration: "auto"`
  plus `maxImages`, input plus generated capped at 15.
- **Size fields**: the 5.5, Pro, and Lite schemas say `width` and `height` apply only under a Custom
  resolution or size, yet none exposes that field. Send the pixels and check the delivered size on
  the first output.

On the generators, mode follows from the inputs. Empty `referenceImages` is text-to-image; one or
more is an edit or a multi-reference generation, where the prompt gives each reference a role by
position. The array shape holds even for one asset. `dry_run` before every batch: the estimate
prices the run exactly as submitted, a whole sequence included.

## Transparent output

Two contracts, read from the schemas and not run-tested at authoring time:

- **5.5**: `background: "transparent"` asks for a transparent PNG from the prompt. The default
  `auto` lets the prompt decide, so set it on every run that must come back transparent, or opaque.
  Whether it keeps a reference's alpha was not tested.
- **5.0 Pro**: `background: "transparent"` keeps an existing cutout transparent through an edit; it
  does not cut a subject out. It applies only with exactly one reference that already carries an
  alpha channel, and is ignored otherwise. It defaults to `opaque`, so a restyle that omits it
  flattens the cutout.

Check the alpha on the downloaded file, since `asset_display` composites transparency away. With
Pillow (`uv run --with pillow` when it is missing), `Image.open(path).getchannel("A").getextrema()`
should start at 0 (fully transparent pixels exist), and an image with no `A` channel was flattened.
When the alpha is missing, generate on a plain field and run background removal (the
`scenario-image-editing` skill), or split the image with Layerize.

## Write the exact copy into the prompt

5.5 and Pro render legible in-image text; Pro's catalog card also names non-Latin scripts. Quote the
exact strings in the prompt instead of paraphrasing them, and give each a position and a size rank
(headline across the top, date line small at the foot). Keep to a few elements at one or two sizes:
letters are drawn, not typeset, so paragraphs and many small labels turn to shapes. Copy past that
budget (tour dates, credits) is composited in post from the start. Proofread with `asset_display`; a
word that garbles is spelled out letter by letter after the quoted string on the rerun, and one that
still garbles goes to post. To swap copy on a reference, quote the new string, pin its position, and
require the original typeface, size and color with everything else unchanged.

## Layerize: one image in, an editable stack out

Layerize returns a base layer plus transparent PNG cutouts, rebuilding the background behind
whatever it lifts.

- **5.5 Layerize**: `maxImages` (3 to 100, base included, default 10) caps the split. Higher usually
  splits finer, and the run is billed for `maxImages` even when fewer come back.
- **Text recognition**: `textRecognition: true` on 5.5 Layerize also returns the text, font, and
  style of printed-text layers. It works best with no prompt and a high `maxImages`, and never reads
  artistic or handwritten text.
- **5.0 Pro Layerize**: up to 16 cutouts; `optimizePromptMode` `fast` trades some split fidelity for
  speed.

The prompt picks the mode: empty runs a full automatic split, and an enumerated list of parts
("Separate this poster into transparent layers: headline, product, shadow, background") cuts better
than "all layers". On the 5.0 members, `<bbox>x1 y1 x2 y2</bbox>` (0 to 1000 grid, origin top left)
confined the split to one region; 5.5's card names only full and named-part splits. Set `size`
explicitly, since auto inherits the source's tier and the tier moves the price. On the 5.0 members,
layers came back cropped to their own bounds with bbox and z-index metadata, with no PSD export:
read 5.5's output metadata before compositing.

## Worked example: a poster, then its layers

1. `search` with `target="models"`, `query="seedream"`, `public=true`. Skip hits tagged `Deprecated`
   and prefer the `sc:featured` generator, e.g. `model_bytedance-seedream-5-5` (a live hit at
   authoring time: re-discover each session).
2. `model_schema_get` with that id: sizing fields, caps, defaults.
3. `model_run` with that id, `dry_run=true`, and
   `parameters={"prompt": "Concert poster, teal and cream, screen-print grain. Headline \"MIDNIGHT ORBIT\" across the top, date line \"Nov 14, Union Hall\" small at the foot.", "width": 1600, "height": 2368, "background": "opaque"}`;
   both sizing fields move price. Unattended, continue only inside the task's budget; otherwise
   report the price and stop.
4. Rerun `model_run` with `wait=false`, then `jobs_wait` with the returned job id, re-called with
   `pending_job_ids` on timeout, never a second `model_run`.
5. `asset_display` and proofread the rendered text.
6. `model_schema_get` on the 5.5 Layerize hit, then `model_run` with that id, `dry_run=true`, and
   `parameters={"image": "<poster asset id>", "prompt": "Separate this poster into transparent layers: the headline text, the date line, and the background. Clean edges, complete transparency.", "size": "2K", "maxImages": 4}`.
   Rerun without `dry_run` under the same budget rule.
7. `jobs_wait`, then `asset_display` each layer and `asset_download` the keepers.

## Common mistakes

- Running a member tagged `Deprecated` because `recommend`, an old note, or the user named it:
  follow its `deprecated:` successor, or the lanes above.
- Reusing one member's parameter block on another: 5.5's 4368 px side is past Pro's 3136 cap, and
  Layerize takes tier enums, not pixels.
- Passing `referenceImages` to Layerize or `image` to the generators: the input field's name and
  shape differ per member.
- Expecting Layerize layers to overlay the source directly: reposition with the returned metadata.
- Asking 5.5 or Pro for a sequence: only Lite has the sequence fields.
- Moving a 3000-character prompt from 5.5 or Pro to Lite: prompt caps are per member.
- Setting Pro's `background` to `transparent` on a text-only run or a flattened reference: it is
  ignored, and the image comes back opaque.
