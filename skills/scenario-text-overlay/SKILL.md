---
name: scenario-text-overlay
description: "Use when text must appear letter-perfect on generated media: taglines, CTAs, prices, legal supers, lower thirds, end cards, nameplates, or styled rich cards composited over Scenario images and video. Keywords: text overlay, text card, caption card, CTA, legal super, tagline, end card, lower third, price card, HUD text, transparent PNG."
license: MIT
---

# Scenario Text Overlay

## Overview

Generation models drift on type, so text that must be exact is rendered deterministically here and composited over the media. One JSON payload describes one overlay, in one of two kinds: a text layer (plain styled text in a box) or a rich layer (HTML/CSS typography: gradients, strokes, shadows, card layouts). Both substitute Mustache `{{variables}}` strictly (a missing variable fails the render) on a transparent canvas.

[scripts/overlay.py](scripts/overlay.py) renders the payload to a PNG with an installed Chromium-family browser (both kinds, discovered automatically) or a Pillow fallback (text layers only), embeds the payload JSON into the PNG, and prints the path. Its modules: [scripts/templating.py](scripts/templating.py) (strict Mustache), [scripts/html_render.py](scripts/html_render.py) (browser engine), [scripts/pillow_render.py](scripts/pillow_render.py) (fallback). The field-by-field contract and example payloads live in [references/payloads.md](references/payloads.md). The script needs `pip install chevron pillow`.

Connection and the core MCP loop: see the `scenario` skill. Compositing overlays onto video: `scenario-video-assembly`.

## Quick reference

| Step                    | Detail                                                                                        |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| 1. Write the payload    | Kind by field (`text_template` or `html_template`); every changeable string in `variables`    |
| 2. Render               | `python3 overlay.py --payload card.json --out card.png`                                       |
| 3. Verify               | Open the PNG: glyphs verbatim, box placement right, background transparent                    |
| 4. Upload               | `upload_asset` (kind `image`, multipart path)                                                 |
| 5. Persist the template | `asset_update` sets the description to the payload JSON; `asset_add_tags` adds `text-overlay` |

## Worked example: a localized legal super

1. Payload, with the changeable line as a variable:

```json
{
  "text_template": "{{disclaimer}}",
  "variables": [
    {
      "key": "disclaimer",
      "value": "EPA-estimated 310 mi. Actual range varies."
    }
  ],
  "font_family": "Inter",
  "font_weight": 500,
  "size": 34,
  "color": "#FFFFFF",
  "align": "center",
  "bbox": [{ "x": 86, "y": 1560, "w": 908, "h": 120 }],
  "canvas_width": 1080,
  "canvas_height": 1920,
  "overflow": "shrink"
}
```

2. `python3 overlay.py --payload super.json --out super.png`, then open `super.png`: the line must read exactly as written, shrunk to fit the box.
3. Upload with `upload_asset`, then `asset_update` with the payload JSON as the description and `asset_add_tags` with `["text-overlay"]` (`asset_update`'s own `tags` field replaces the whole set): the template now lives on the platform beside its render, and the PNG itself carries it in a `tEXt` chunk.
4. The French variant is the same payload with one `value` edited, never a new template.

## Common mistakes

- Baking changeable strings into the template: variants and localizations should be edits to `variables`; the uploaded payload is the reproducibility contract.
- Using `{{var}}` for values holding `&`, `<`, or `>`: it HTML-escapes, so they render as literal entity text; `{{{var}}}` is the raw opt-out (and the deliberate way to inject markup in rich layers).
- Leaving images or fonts as remote URLs: inline them as `data:` URIs (Google Fonts links excepted) or the render depends on the network and drifts.
- Skipping the visual check before upload: font resolution differs per machine; open the PNG first.
- Letting a generation model paint the text instead: generated type drifts frame to frame; overlays exist to avoid exactly that.
- Sizing the canvas to something other than the destination: match the target resolution so the overlay composites 1:1 with no post-scale blur.
- Expecting the fallback to match the browser: Pillow draws plain text only; rich layers need a Chromium-family browser installed.
- Trusting `wrap` with a hard box: it lets text spill below; use `shrink` (fits or fails loudly) or `clip` when the box is binding.
