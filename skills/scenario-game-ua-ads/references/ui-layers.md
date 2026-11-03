# Game UI layers, effects, and sound

Every overlay is rendered at final size, uploaded, and placed in `model_scenario-compose-video`. Two
kinds:

- **Static layers** (hook, burst words, gate labels, end-card background): one transparent PNG each,
  a rich layer from `scenario-text-overlay`, every string in `variables`.
- **Moving layers** (hand, counter, floaters, rewards, bursts, stars, end-card motion): rendered
  frame by frame at 30 fps and encoded into one transparent video per element. Elements that move
  together, such as the pieces of the end card, may share one video.
- **Scripted gameplay** (a tile-match or sort board animated from cut pieces): one full-frame layer
  needs no alpha. Render it over its background as high-quality H.264: a full-frame ProRes 4444
  gameplay track was 345 MB.

Values below are for a 1080-wide canvas.

## Transparent video

- Encode ProRes 4444 `.mov` with alpha:
  `ffmpeg -framerate 30 -i f%03d.png -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le out.mov`.
  Compose honors its alpha. A VP9 WebM with alpha came out as an opaque black box.
- Rendering the frames is local, like the PNG overlays. Compositing stays a compose run.
- Crop each video to the box its element moves in, and place it with `x`, `y`, `width`, and `height`
  equal to that box, `fit: "fill"`, `mute: true`. An 8 s hand track was 24.5 MB at full canvas and
  6.6 MB cropped to 400x450.
- Uploads go out in 6 MB parts: `upload_asset` returns one presigned URL per part. PUT each chunk to
  its URL in order, then call `upload_asset_complete`.
- Never animate with a run of stepped image layers. Compose can draw the outgoing and the incoming
  layer on one boundary frame, which shows a double hand or two counters.
- An element animated by a video model on a flat color, such as a hero dancing on the end card,
  becomes alpha through a chroma-key tool model (`recommend` one). Ask for its MOV (ProRes 4444)
  output, never WebM.
- Compose reads layer times to the millisecond. Write a frame time (frame n / 30) rounded down: 185
  / 30 written as 6.1667 starts the layer one frame late.
- A track that hands over to a static PNG (an icon pop, then the still icon) ends on the PNG's
  `startTime`, with no overlap: one shared frame draws soft shadows twice and darkens them.
- Give every image layer an explicit `width` and `height` at its natural size. A 750x107 PNG with no
  size was drawn about 2.5 times too large. Pad very small PNGs to about 300 px on the short side.

## Static recipes

- **Burst word** (FAIL, NICE, HUGE!): a heavy rounded display face at 250 px or more, gold for wins,
  red for fails.
  - The working gradient with an outline is a span with a `linear-gradient` background,
    `-webkit-background-clip: text`, `-webkit-text-fill-color: transparent`, `-webkit-text-stroke`
    about 8% of the size, and `paint-order: stroke fill`.
  - Shadows go in `filter: drop-shadow(...)`: a hard offset in the stroke color, then a soft one.
    `text-shadow` shows through the transparent fill and floods the word with the outline color.
  - Crop the PNG tight with 24 px padding, so `transitionIn: "zoomin"` grows from the word's own
    center.
  - Keep it inside the placement's text zone: under 800 px wide on TikTok, clear of the right rail,
    and inside the 6% side margins elsewhere.
  - Put a full-canvas red flash (about 40% alpha, 0.5 s) under FAIL.
- **Hook line**: the same recipe, tilted 2 to 4 degrees, on two lines: the key words at 150 to 190
  px, and a longer second line at 70 px or more ("ONLY 1%" big, "CAN CLEAR THIS BOARD" small). A
  newline in a plain `{{variable}}` is lost, so put `<br>` in the value and use `{{{variable}}}`. It
  shows on frame 0 and is gone by 2.5 s unless the action needs it.
- **Gate label**: white fill, dark outline, sized to the gate it sits on.

## Moving recipes

- **HUD**: a level badge and a counter pill, 120 px tall, with digits at 72 px or more. On 9:16
  social, their top edge is at y 280, under the platform band. The counter is one video for the
  whole ad: each new value pops at 112% for 0.15 s, then rests.
  - The HUD may cover only pieces that never move, and a covered piece still counts. A test ad
    claimed 12 of 12 cars out with a parked car half under the HUD. With a locked camera, a static
    patch cut from the same take removes such a piece for the whole ad.
- **Counter values**: name the unit (coins, size, army) and tie every step to an event the clip
  shows. Use 4 or 5 steps that only climb, with values a viewer can believe: five cars swallowed
  never adds 300 m.
- **Score floater**: "+N" at about 90 px, white with a dark stroke. It rises 120 px from the event
  point over 0.6 s and fades in its last third.
- **Reward fly-to-HUD**: 3 to 10 of the game's own reward icons burst from the event point. They arc
  into the counter icon in about 0.4 s, staggered 45 ms, and the counter pops as the first one
  lands. Rewards fly only from events the clip shows.
- **Impact burst**: radial spikes, a shockwave ring, and sparkles, about 0.4 s. It is centered on
  the 1 to 3 biggest impacts of the ad, never on every event.
- **Win stars**: three slots under the win word fill one by one with a sparkle each, over about 0.9
  s, with the payoff still visible.
- **Hand**: one glove generated once on a transparent background. Measure the fingertip's offset on
  the PNG.
  - A tap presses for 0.15 s at 92% scale.
  - A drag follows the object's position, measured on extracted frames of the take. The fingertip
    stays on the object or just behind it, never ahead of it.
- **Icon pop**: render the pop into an alpha video, at scales 0.4, 0.82, 1.1, 1.05, and 1.0 on five
  frames, ending exactly where the static icon layer takes over. `zoomin` on a rounded app icon
  showed black corners on its first frame.
- **Living end card**: opaque from its first frame, starting the frame the last clip ends.
  - The background is a gradient with slowly turning rays: an H.264 video, or a PNG.
  - The icon pops at +0. The name follows at +0.2 s, and the stars pop one by one, then glint.
  - The hero cut-out bounces in from below, squashes on landing, and hops about every 1.2 s.
  - The call to action breathes (scale 1 to 1.035 over 0.9 s) and takes a light sweep.
  - On social placements it is a label with no button shape, and no hand taps it. On a clickable
    ad-network card it is a button in two states, tapped twice by the hand.
  - Center the content in the safe band, not on the canvas: on 9:16 social, between y 270 and 1248.
- **Anchoring**: a layer is fixed in screen space, so a label on a moving object slides off it. Keep
  such a label to the seconds when the object barely moves, or put the value on the HUD.

## Sound

- One hit per visible event, on its frame within 0.1 s, measured on the extracted frames, not the
  plan.
- Build a kit once: tap, whoosh, counter tick, fail buzz, win sting, end-card chime. Add 2 to 4
  theme hits (crash, gulp, gem burst).
  - Generate each hit with a sound-effect model (`recommend` one).
  - Trim each so its onset sits at 0.0, which makes the cue time the hit time.
  - Each hit's peak sits at least 4 dB over the music's peak in the same 50 ms.
- The music bed comes back at its own length (a 10 s request returned 19 s). Trim it with `trimEnd`
  and measure its energy every 0.1 s.
  - Offset it so its lift lands within 0.3 s of the payoff start.
  - Start it in a section with energy. A quiet intro under a quiet fail left one test's first 5 s 10
    dB under the rest.
  - Duck it about 4 dB under the fail beat, unless it is already that low there.
- Compose adds layers with no limiter, so stacked hits clip: one test master peaked at +1.8 dBTP.
  Before the sound pass, sum the cue sheet locally and trim the master volume and the few hits that
  make the peaks. A test ad reached -14.4 LUFS and -2.0 dBTP this way, and the render matched the
  local sum within 0.3 dB.
- Sound pass: the silent master as the only video layer, plus the music, the video-to-audio track,
  and every hit as audio layers.
  - A test pass took 40 audio layers. Every hit landed within 1 ms, and 0.15 s layers, exact
    volumes, and 10 ms fades all held.
  - Past 49 audio layers, drop the video-to-audio track first.
- Loudness pass, only when the sound pass misses the target: run `model_scenario-audio-extract` on
  the sound pass with `normalizeLoudness: true` and `outputFormat: "wav"`. Then compose the silent
  master with that track as the only audio layer.
  - Measured on two test masters: about -16 LUFS integrated, true peak -1.5 dBTP, no time shift.
  - Check with ffmpeg's `ebur128` filter (`-af ebur128=peak=true`).
