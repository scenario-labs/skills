# Game UI layers

Render each layer with `scenario-text-overlay` as a rich layer on a transparent 1080x1920 canvas,
upload it, then place it as an image layer in `model_scenario-compose-video`. One payload per layer,
every string in `variables`, so a localized or renamed variant edits one value.

## Style recipes

A rich layer takes `html_template` plus `css`. Load the display font from Google Fonts in the
template, and keep `device_scale_factor` at 1.0 when the canvas already matches delivery.

- **Burst word** (FAIL, NICE, LEGENDARY, SO SATISFYING): one heavy rounded display face, a vertical
  gradient fill, a thick dark outline with `-webkit-text-stroke` and `paint-order: stroke fill`,
  then a hard offset shadow plus a soft drop shadow. Warm gold for wins, red for fails.
- **Hook line**: same recipe, two short lines, tilted a few degrees, in the top fifth of the frame
  inside the platform safe zone.
- **Counter pill**: rounded bar, solid color, thick white border, small hard shadow, centered on a
  fixed HUD position. Render one PNG per value.
- **Gate label**: white fill, dark blue outline, sized to the gate it sits on.
- **End card**: game name in white with a heavy outline, a green button below it with the call to
  action. Anchor it to the lower third, above the platform's bottom UI.
- **Hand cursor**: generate once as an isolated glove on a transparent background, upload it, and
  reuse it. Rotate it per layer to point at the target.

## Timing on the compose timeline

- A burst word holds 0.8 to 1.2 seconds. Give it `transitionIn: "zoomin"` with a short
  `transitionDuration` so it pops, and a small `rotation`. The pop grows from the layer's center, so
  it reads as a pop only for centered words. Off-center elements on a full-canvas PNG appear to fly
  in from mid-frame: use `fadeIn` for those.
- A hook line holds the first 2 to 3 seconds and uses `fadeOut`.
- Counter pills sit at one position with consecutive `startTime`/`endTime` windows and no gap, so
  the number appears to climb.
- A hand sits on the target for the first second of a take, then `fadeOut`.
- Counter pills read at phone size only when large: about 130 px type on a 1080 canvas.
- Scale overlays 1:1: canvas size equals the delivery size. Scale the generated clip layers up with
  `fit: "cover"` instead.

## Anchoring

A layer is fixed in screen space. A label attached to an object in a moving shot slides off it.
Either keep the label to the seconds when the object barely moves, or put it on the HUD.
