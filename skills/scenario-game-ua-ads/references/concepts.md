# Concept beat sheets

Six proven mobile UA concepts. Times fit a 10 to 15 second ad; scale them down for 6 seconds by
dropping the middle beat. Every board is a text-free 9:16 still, and every number, label, button,
and hand in the UI column is a composited layer (see [ui-layers.md](ui-layers.md)).

Invent a fictional game name when the user gives none, and use it on the end card only.

## 1. Rescue with a fail tease (pin-pull puzzle)

- **Board**: stone-wall cutaway with four glass chambers: hazard (lava), treasure (gold), a trapped
  character, an empty bin. Golden pins block golden pipes.
- **Clips**: two from the same still. Fail take: wrong pin slides out, hazard flows down the pipe to
  the character. Win take: other pin slides out, treasure pours into the bin, character cheers.
- **Beats**: 0 to 2.5 s hook line over the board. 0 to 5 s fail take. FAIL burst on the last second.
  Cut back to the same board. 5 to 10 s win take. NICE burst. End card.
- **UI**: hook line, hand on the first pin ring (first second of each take), FAIL, NICE, end card.
- **Notes**: the character reads as worried in the still, so the fail needs no extra acting. The
  other pipe may glow during the fail take; accept it or reroll once.

## 2. Number gates (crowd runner)

- **Board**: wide runway toward a castle, a small crowd of identical characters in the lower third,
  two blank gate panels across the lane. Blank is deliberate: the model cannot hold numbers.
- **Clip**: camera follows the crowd through one gate; the crowd multiplies and spreads.
- **Beats**: 0 to 1 s gate labels over the gates. Counter steps through three values on a fixed HUD
  pill (18, then 115, then 803). Last 1.5 s end card.
- **UI**: two gate labels, three counter pills in sequence, end card.
- **Notes**: the gates move as the camera advances, so labels live only while the gates are nearly
  static (about the first second). The counter pill never moves, so it carries the story.

## 3. Satisfying sort (ASMR)

- **Board**: a shelf or rack of colorful items in rows, a reveal panel above it that fills as items
  land.
- **Clip**: items slide into slots in sequence; the reveal panel fills with a picture.
- **Beats**: 0 to 3 s sorting. Combo badge steps up (x5, then x12) as lines complete. Reveal panel
  completes on the payoff frame, with a short word line over it.
- **UI**: combo badges, word line, end card.
- **Notes**: lead with sound. Real ASMR ads live on the audio bed: tactile clicks and a rising tone
  under each combo step.

## 4. Legendary pull (gacha summon)

- **Board**: summoning circle, five face-down cards in a row, one slightly brighter. Also render the
  payoff still: the hero bursting out of shattered glass.
- **Clip**: one first-and-last-frame clip from the card row to the hero still. Prompt the middle:
  center card flips, flash, burst shatters into shards, hero lands on the last frame.
- **Beats**: 0 to 2 s anticipation, 2 to 3.5 s flip and burst, banner as the burst peaks, 3.5 s to
  end hero hold with end card.
- **UI**: rarity banner, end card.
- **Notes**: pin the last frame, or the model invents a different hero. The flip can show a blank
  card face; the burst hides it.

## 5. Crisis to restore (merge-2 story)

- **Board**: story still (family in a storm) and a merge grid still with a cozy restored room.
- **Clips**: crisis clip, then restore clip, joined by a choice screen.
- **Beats**: 0 to 3 s crisis with two choice buttons and a hand on one. 3 to 7 s merge grid combines
  items, multiplier badge steps up. 7 s to end restored room.
- **UI**: two choice buttons, hand, multiplier badge, end card.
- **Notes**: keep the same characters across stills by generating the room from the story still as a
  reference.

## 6. Only 1% can solve (challenge puzzle)

- **Board**: a close-up puzzle object (screws and holes, tangled ropes, sliding blocks) on a warm
  background.
- **Clip**: the solving move: object moves, a pause on the wrong state, then the right state.
- **Beats**: 0 to 2 s headline over the puzzle with a score meter. Hand shows the move. Challenge
  line ("CAN YOU DO IT?") in the last second before the end card.
- **UI**: headline banner, score meter, hand, challenge line, end card.
- **Notes**: the headline and meter are layers; never ask the model for a score number.
