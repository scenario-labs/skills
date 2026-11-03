# Game UI layers

Render each layer with `scenario-text-overlay` as a rich layer on a transparent 1080x1920 canvas,
upload it, then place it as an image layer in `model_scenario-compose-video`. One payload per layer,
every string in `variables`, so a localized or renamed variant edits one value.

## Style recipes

A rich layer takes `html_template` plus `css`. Load the display font from Google Fonts in the
template, and keep `device_scale_factor` at 1.0 when the canvas already matches delivery.

- **Burst word** (FAIL, NICE, LEGENDARY): one heavy rounded display face at 300 px or more, a
  vertical gradient fill, a thick dark outline with `-webkit-text-stroke` and
  `paint-order: stroke fill`, then a hard offset shadow plus a soft drop shadow. Gold for wins, red
  for fails. Add a full-canvas red flash layer (about 40% alpha) for 0.5 s under FAIL.
- **Hook line**: same recipe, about 190 px, two short lines, tilted a few degrees. A newline in a
  plain `{{variable}}` is lost: put `<br>` in the value and use `{{{variable}}}`.
- **HUD**: a level badge top-left and a coin counter top-right at 60 to 70 px type, about 190 px
  from the top of the render and moved to the top of frame with a negative `y` in the compose run.
  Keep the hook below the HUD so they never overlap.
- **Counter pill**: render one PNG per value (0, 120, 480, 1,250, 2,400), each at the same position,
  so the number appears to climb.
- **Gate label**: white fill, dark blue outline, sized to the gate it sits on.
- **Hand cursor**: generate once as an isolated glove on a transparent background and reuse it. The
  fingertip sits near the image's top-left corner, so place the layer at the target minus about 15%
  of its width.
- **End card**: one opaque full-canvas PNG: warm radial background, rounded app icon (about 640 px,
  white border), game name in two lines, five stars, a green button below. Embed the icon as a data
  URI in the template.

## Timing on the compose timeline

- Compose has no keyframes. A hand drag is two or three copies of the hand layer at stepped
  positions, each held 0.3 to 0.5 s, the last one with `fadeOut`.
- A burst word holds 1.0 to 1.2 seconds with `transitionIn: "zoomin"` and a short
  `transitionDuration`. Zoom grows from the layer center, so use it only for centered words. Use
  `fadeIn` for everything else.
- A hook line holds the first 3 seconds with `fadeIn` and `fadeOut`.
- Counter pills use consecutive `startTime`/`endTime` windows with no gap.
- The end card starts at the exact second the last clip ends, with no fade: a fade over an empty
  canvas shows a black frame.
- Scale overlays 1:1. Scale the generated clip layers up with `fit: "cover"` instead.

## Anchoring

A layer is fixed in screen space. A label attached to an object in a moving shot slides off it.
Either keep the label to the seconds when the object barely moves, or put it on the HUD.
