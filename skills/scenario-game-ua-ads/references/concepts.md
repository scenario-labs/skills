# Concept beat sheets

Six proven mobile UA concepts, each planned as a 15 second ad: a setup or tease take, a payoff take,
and a 4 second end card. Every board is a text-free still at the delivery ratio, and every number,
label, button, and hand in the UI column is a composited layer (see [ui-layers.md](ui-layers.md)).
Shorter ads drop the setup take's second half, never the end card.

Invent a fictional game name when the user gives none, and use it on the end card only. Generate a
square app icon of the hero for every end card.

## 1. Rescue with a fail tease (pin-pull puzzle)

- **Board**: two tall glass shafts side by side in a stone frame. Left: hazard (lava) above the
  trapped character. Right: treasure (gold) above an empty cart. One golden pin is the floor of each
  top compartment, so a pull drops the contents straight down. No pipes, bends, or second pins: the
  model routes contents outside a pipe and pours through a closed pin. Keep the top 15% free for the
  HUD and hook.
- **End still**: for the payoff, edit the board into its solved state with the same gold amount in
  the cart, the lava still held, the character cheering.
- **Clips**: two from the same still. Fail take 5 s: wrong pin slides out, hazard drops onto the
  character. Payoff take 10 s, first and last frame pinned to the end still: the other pin slides
  out, treasure drops into the cart.
- **Timeline**: 0 to 3 s hook. 0 to 5.2 s fail take, FAIL and red flash at 3.7 s. 5.2 to 11.1 s
  payoff take, counter climbing, NICE at 9 s. 11.1 to 15 s end card.
- **UI**: hook, level badge, coin counter (5 values), hand on each pin ring, FAIL, red flash, NICE,
  end card.
- **Notes**: the character reads as worried in the still, so the fail needs no extra acting. Pinning
  the last frame also locks the camera; an unpinned payoff take drifted into a push-in even when
  told not to.

## 2. Number gates (crowd runner)

- **Board**: wide runway toward a castle, a small identical crowd in the lower third, two blank gate
  panels across the lane. Blank is deliberate: the model cannot hold numbers.
- **Clips**: setup take 5 s with the camera still on the gates. Payoff take 8 s: the crowd runs
  through one gate and multiplies.
- **Timeline**: 0 to 3 s gate labels over the gates. 0 to 5 s setup. 5 to 11 s payoff, counter steps
  through 4 values (18, 115, 480, 803). 11 to 15 s end card.
- **UI**: two gate labels, four counter pills, a hand choosing a gate, end card.
- **Notes**: gates move when the camera advances, so labels live only while the gates are nearly
  static. The counter never moves, so it carries the story.

## 3. Satisfying sort (ASMR)

- **Board**: a shelf or rack of colorful items in rows, a reveal panel that fills as items land.
- **Clips**: sorting take 7 s, items slide into slots in sequence. Reveal take 5 s, the panel
  completes into a picture.
- **Timeline**: 0 to 7 s sorting, combo badge steps x3, x8, x15, x25. 7 to 11 s reveal with a short
  word line. 11 to 15 s end card.
- **UI**: combo badges, word line, end card.
- **Notes**: lead with sound. Tactile clicks and a rising tone under each combo step carry the ad.

## 4. Legendary pull (gacha summon)

- **Board**: summoning circle, five face-down cards in a row, one slightly brighter. Also render the
  payoff still: the hero bursting out of shattered glass.
- **Clips**: anticipation take 5 s from the card row. Burst take 6 s, first-and-last-frame from the
  card row to the hero still: flip, flash, shatter, hero lands.
- **Timeline**: 0 to 5 s anticipation with a hook line. 5 to 8 s burst, rarity banner at the peak. 8
  to 11 s hero hold. 11 to 15 s end card.
- **UI**: hook line, rarity banner, end card.
- **Notes**: pin the last frame or the model invents a different hero. A blank card face can show
  during the flip; the burst hides it.

## 5. Crisis to restore (merge-2 story)

- **Board**: story still (family in a storm) and a merge grid still with a cozy restored room.
- **Clips**: crisis take 5 s, merge take 6 s, joined by a choice screen layer.
- **Timeline**: 0 to 5 s crisis, two choice buttons, hand on one. 5 to 11 s merge grid combines
  items, multiplier badge steps up. 11 to 15 s restored room with the end card.
- **UI**: two choice buttons, hand, multiplier badge, end card.
- **Notes**: keep the same characters across stills by generating the room from the story still as a
  reference.

## 6. Only 1% can solve (challenge puzzle)

- **Board**: a close-up puzzle object (screws and holes, tangled ropes, sliding blocks) on a warm
  background.
- **Clips**: wrong-state take 5 s with a pause on the mistake, solving take 6 s to the right state.
- **Timeline**: 0 to 5 s headline over the puzzle with a score meter, hand showing the move. 5 to 11
  s solving take. 9 to 11 s challenge line ("CAN YOU DO IT?"). 11 to 15 s end card.
- **UI**: headline banner, score meter, hand, challenge line, end card.
- **Notes**: the headline and meter are layers; never ask the model for a score number.
