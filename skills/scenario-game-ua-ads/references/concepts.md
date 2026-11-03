# Concept beat sheets

Sixteen mobile UA concepts, each planned as a 15 second ad: a setup or tease take, a payoff take,
and an end card of about 4 seconds. Every board is a text-free still at the delivery ratio, and
every number, label, button, and hand in the UI column is a composited layer (see
[ui-layers.md](ui-layers.md)). Shorter ads drop the setup take's second half, never the end card.

Concepts 1 and 7 to 16 were produced and reviewed as 15 second ads. Their Notes record the faults
that review caught and the rule that avoids each.

Each concept's **Fun** line names the player fantasy, the input a viewer must read within 2 s, the
motions the clips must show, and the limit the player overcomes. Plan the clips from it.

Invent a fictional game name when the user gives none, and use it on the end card only. Generate a
square app icon of the hero for every end card.

| #   | Concept                  | Group                  | Core mechanic                 | Hook                  |
| --- | ------------------------ | ---------------------- | ----------------------------- | --------------------- |
| 1   | Rescue with a fail tease | Puzzle and logic       | Pull the right pin            | CAN YOU SAVE HIM?     |
| 6   | Only 1% can solve        |                        | Fix a wrong state             | ONLY 1% CAN SOLVE     |
| 7   | Draw to protect          |                        | Draw a shield line            | PROTECT THE DOG!      |
| 8   | Find the odd one         |                        | Tap the one that differs      | FIND THE ODD CAT!     |
| 9   | Parking jam escape       |                        | Free the blocker first        | ONLY 1 WAY OUT!       |
| 3   | Satisfying sort          | Satisfying and ASMR    | Items click into slots        | Tactile sound first   |
| 10  | Excavation reveal        |                        | Brush sand off a fossil       | WHAT'S INSIDE?        |
| 11  | Cascade combo            |                        | One swap sets off a chain     | ONE SWAP CHANGES ALL  |
| 2   | Number gates             | Growth and progression | Run through the better gate   | Two labeled gates     |
| 4   | Legendary pull           |                        | Flip the glowing card         | One card glows        |
| 5   | Crisis to restore        |                        | Merge to rebuild a room       | A crisis and a choice |
| 12  | Broke to cozy            |                        | Tap upgrade, the room changes | FROM BROKE TO RICH?   |
| 13  | Swallow and grow         |                        | A hole eats ever bigger items | EAT THE WHOLE CITY    |
| 14  | Evolve and smash         |                        | Collect, evolve, smash a wall | HOW BIG CAN HE GET?   |
| 15  | Perfect stack            | Skill shots            | Time each drop                | STACK IT PERFECTLY    |
| 16  | Trick shot               |                        | Bank one shot off bumpers     | ONE SHOT. 3 ROBOTS.   |

## 1. Rescue with a fail tease (pin-pull puzzle)

- **Fun**: rescue through cleverness. One finger pulls one pin, the pin slides free, and gold pours
  and piles into the cart. The wrong pin dropping lava is the limit the right pull overcomes.
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

- **Fun**: growth. A finger picks one of two gates, and the crowd pours through, multiplies into a
  flood, and ripples as it runs. The castle is the limit only the multiplied crowd can overrun.
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

- **Fun**: order. A finger drags one item to a slot, items wobble on a slot's edge and click in, and
  rows fill. One item jams at first, then turns and drops in.
- **Board**: a shelf or rack of colorful items in rows, a reveal panel that fills as items land.
- **Clips**: sorting take 7 s, items slide into slots in sequence. Reveal take 5 s, the panel
  completes into a picture.
- **Timeline**: 0 to 7 s sorting, combo badge steps x3, x8, x15, x25. 7 to 11 s reveal with a short
  word line. 11 to 15 s end card.
- **UI**: combo badges, word line, end card.
- **Notes**: lead with sound. Tactile clicks and a rising tone under each combo step carry the ad.

## 4. Legendary pull (gacha summon)

- **Fun**: power. A tap lands on the one glowing card, which trembles, cracks, and shatters, and the
  hero lands with a shockwave. The card resisting through two cracks is the limit before the burst.
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

- **Fun**: rescue. A tap picks one choice, a drag joins two matching items, and they pop into a
  bigger one as the room repairs. The storm is the limit each merge pushes back.
- **Board**: story still (family in a storm) and a merge grid still with a cozy restored room.
- **Clips**: crisis take 5 s, merge take 6 s, joined by a choice screen layer.
- **Timeline**: 0 to 5 s crisis, two choice buttons, hand on one. 5 to 11 s merge grid combines
  items, multiplier badge steps up. 11 to 15 s restored room with the end card.
- **UI**: two choice buttons, hand, multiplier badge, end card.
- **Notes**: keep the same characters across stills by generating the room from the story still as a
  reference.

## 6. Only 1% can solve (challenge puzzle)

- **Fun**: cleverness. One finger moves one piece, which jams and rattles in the wrong state, then
  slides and locks in the right one. The pause on the mistake is the limit the solve overcomes.
- **Board**: a close-up puzzle object (screws and holes, tangled ropes, sliding blocks) on a warm
  background.
- **Clips**: wrong-state take 5 s with a pause on the mistake, solving take 6 s to the right state.
- **Timeline**: 0 to 5 s headline over the puzzle with a score meter, hand showing the move. 5 to 11
  s solving take. 9 to 11 s challenge line ("CAN YOU DO IT?"). 11 to 15 s end card.
- **UI**: headline banner, score meter, hand, challenge line, end card.
- **Notes**: the headline and meter are layers; never ask the model for a score number.

## 7. Draw to protect (line-drawing puzzle)

- **Fun**: rescue. A finger draws one arc, bees slam into it and bounce off in sparks, and the pet
  stays calm underneath. The fail take's sting is the limit the line beats.
- **Board**: a pet in open ground, a beehive in a top corner. A second still is an edit adding "only
  ONE new element": a glowing line arcing over the pet.
- **Clips**: two of 6 s, first frame only. Fail take: the swarm stings the pet. Payoff take from the
  line still: every bee "hits the OUTSIDE of the glowing blue line and bounces back".
- **Timeline**: 0 to 3.8 s fail take, FAIL on the sting. 3.8 to 4.6 s the line draws. 4.6 to 11.1 s
  payoff take, a 5 s countdown to SAFE!. 11.1 to 15 s end card.
- **UI**: hook, line reveal, hand, countdown, FAIL, bounce sparks, SAFE!, end card.
- **Notes**:
  - Count real seconds. A timer reaching 10 in 5 s read as a lie.
  - Reveal the line along its path, the fingertip on its head. A wipe between the stills read as a
    wipe.
  - Scan payoff frames for bee color inside the arc.

## 8. Find the odd one (spot-the-difference grid)

- **Fun**: cleverness. A tapped wrong cat puffs up and hisses, and the tapped odd one leaps off its
  cushion. The hiss is the limit a sharper second look overcomes.
- **Board**: a 4 by 5 grid of cats on cushions, "perfect identical copies", with "Exactly ONE"
  different by one color cue. Top 30% empty. The odd one sits in the middle band, clear of the
  bottom unsafe band.
- **Clips**: two from the same still, first frame only. Wrong-tap take 6 s: one cat hisses. Payoff
  take 8 s: only the odd one jumps.
- **Timeline**: 2.3 s wrong tap, FAIL. 3.6 to 4.4 s a magnifier finds the odd one. 5 to 11 s payoff
  take, FOUND IT! on the jump, counter to 3/3. 11 to 15 s end card.
- **UI**: hook, found counter, hand, tap rings, FAIL, magnifier, FOUND IT!, end card.
- **Notes**:
  - Put the hand on the cell that reacts on frames. The model made a different cat hiss than the one
    named.
  - Prompt "every other cat stays perfectly still in its idle pose". Every cat celebrated in unison.
  - Show a timer only in real time.
  - A ring follows a jumping cat, or it circles an empty cushion.

## 9. Parking jam escape (car puzzle)

- **Fun**: order. A tap frees the one blocker, it pulls away, and the cars stream out in a chain
  until the lot is empty. The wrong car's crash is the limit the right tap unlocks.
- **Board**: a top-down lot built for the rule: one straight aisle to one exit, six cars a side
  nosed toward it, a blocker in the aisle. A tangled first layout was unsolvable.
- **End still**: the lot edited to empty.
- **Clips**: fail take 6 s, first frame only: a side car bumps the blocker. Payoff take 7 s, first
  and last frame pinned: the blocker leaves, then the rest, nearest the exit first.
- **Timeline**: 2.4 s crash, FAIL. 3.7 s cut, tap on the blocker. 4.5 to 9.9 s exits, the counter
  steps as cars cross the exit. 10 s CLEARED!. 11.1 to 15 s end card.
- **UI**: hook, cars-out counter, hand, crash burst, FAIL, CLEARED!, end card.
- **Notes**:
  - Count cars on the board, not in the plan. CLEARED 12/12 shipped with a car under the HUD.
  - State "no car fades, vanishes or teleports".
  - Plan a retime: 12 exits took 9.5 s and were sped up 1.5 times.
  - Give cars a readable front, or the blocker seems to reverse.

## 10. Excavation reveal (dig ASMR)

- **Fun**: order. A hand brushes sand off in sheets, a chisel cracks a hard crust, and the bones
  gleam as they appear. The crust the brush cannot move is the limit.
- **Board**: a top-down tray of packed sand, no bone visible, a brush and a chisel below.
- **End still**: the tray edited to a complete skeleton, nothing else changed.
- **Clips**: generate the payoff first: 8 s, first and last frame pinned, the brush working top to
  bottom. Then the setup take, 6 s, its last frame pinned to the payoff's frame at 2 s.
- **Timeline**: 0.4 to 5.5 s setup take. 5.5 to 11.1 s payoff take, progress steps on visible bone,
  burst at 100%. 11.1 to 15 s end card.
- **UI**: hook, progress pill, hand on the tool, dust puffs, win burst, end card.
- **Notes**:
  - Hit at 0.0 and on every tool contact. The opening averaged -31 dB over 5 s.
  - Pin the setup's last frame. Unpinned, it uncovered a bone missing from the skeleton.
  - State "sand never disappears by itself" and "bones are only uncovered, they never move, grow, or
    change shape".
  - Glue the hand to the tool: tools move on their own.

## 11. Cascade combo (match-3)

- **Fun**: cleverness that turns into power. A swipe swaps two gems, three burst, and the column
  drops and bounces into place. The small first clear is the limit the chain breaks.
- **Board**: an 8 by 8 grid of five gem types, each with its own color and cut, a locked front
  camera.
- **Clips**: swaps are layers drawn from the still. No take swapped two gems cleanly: rows shifted,
  gems doubled. Generate each take from the post-swap board. Setup take 5 s, first frame only: three
  gems burst, the column falls. Payoff take 7 s, first and last frame pinned to a fresh full board:
  chain clears, then a rainbow wave.
- **Timeline**: 0.3 to 3.2 s first swap, burst, refill. 3.7 to 4.4 s second swap. 4.4 to 7.9 s
  cascade, combo x2 to x32. 8.1 s MEGA COMBO!. 11.1 to 15 s end card.
- **UI**: hook, score, combo badge, swap layers, hand, MEGA COMBO!, end card.
- **Notes**:
  - State "A gem either stays in its cell, slides straight down its own column, or bursts in place."
  - Cut a hang over a gap to under 0.3 s. Gems hung 1.3 s.
  - Step the combo only on a visible clear. Trim beams that clear nothing.

## 12. Broke to cozy (idle tycoon makeover)

- **Fun**: growth. A tap on UPGRADE pops decor in with a bounce, customers stream in and sit, and
  coins fly up. The customer walking out is the limit the upgrade fixes.
- **Board**: a shabby isometric room cutaway: one table, a bored worker, a door.
- **End still**: walls, door, counter, and worker at the same pixel positions, decor upgraded, five
  full tables. Count them: the first edit had four.
- **Clips**: setup take 6 s, first frame only: a customer enters, waits, and leaves. Payoff take 7
  s, first and last frame pinned: upgrades pop in, customers sit.
- **Timeline**: 2.6 s NO SALE!. 4.5 s tap on UPGRADE. 4.9 s cut. Cash steps on each seated customer,
  SO COZY! at 10.3 s. 11.2 to 15 s end card.
- **UI**: hook, cash counter, NO SALE!, UPGRADE button, hand, coins, SO COZY!, end card.
- **Notes**:
  - Land the music lift on the tap. It came 4 s late.
  - Time the setup prompt second by second. Without timecodes, it spread over 8 s.
  - State that customers use "only the open floor" and the door.
  - Seat customers early. Cash held at zero, then crammed four steps into 1 s.

## 13. Swallow and grow (hole game)

- **Fun**: growth into power. A finger drags the hole, objects teeter on the rim and tip in, and the
  rim wobbles. A too-big object rattles across the rim until the hole grows and takes it.
- **Board**: a toy city block, high three-quarter view, a black hole about 13% of the frame width. A
  tinier hole made the camera push in. A second still: a bigger hole, cars and houses at its rim,
  each narrower than the hole.
- **Clips**: two, first frame only. Setup take 7 s: the hole glides a short path, growing after each
  prop. Payoff take 8 s: it grows in place through cars, houses, and a tower.
- **Timeline**: 2 s cut on a white flash. 2 to 11 s payoff, SIZE steps after each swallow, HUGE! at
  8.9 s. 11 to 15 s end card.
- **UI**: hook, SIZE counter, hand on the rim, HUGE!, end card.
- **Notes**:
  - The produced ad failed its Fun line: objects vanished, but the drag, the rim wobble, and the
    too-big-then-fits beat were missing.
  - Keep the hole's on-screen size growing across the cut. It fell from 60% to 34% of the frame
    width; zooming the payoff in and easing out fixed it.
  - Step SIZE only after an object is inside. The hole swelled with nothing eaten.
  - State "exactly ONE black hole" that "never splits, never duplicates". Sideways travel duplicated
    it.

## 14. Evolve and smash (evolution runner)

- **Fun**: growth into power. A swipe changes lanes, and the creature snatches orbs, swells in an
  evolve burst, and blasts the wall to rubble. The wall is the limit only the final form breaks.
- **Board**: a three-lane runway from behind, a small creature in the center lane, orbs zigzagging
  across lanes. A second still: the creature as the setup ends it, a hurdle with an orb above its
  bar, a stone wall at the end.
- **Clips**: two, first frame only, a chase camera. Setup take 6 s: two lane pickups, evolve. Payoff
  take 10 s: a jump, pickups, a huge evolve, the smash.
- **Timeline**: 0.3 to 2.8 s swipes, pickups, evolve. 3.5 s cut under a white wipe. 9 to 10.7 s
  SMASH IT! taps, then impact. 11.5 to 15 s end card.
- **UI**: hook, level bar, hand, evolve bursts, SMASH IT!, end card.
- **Notes**:
  - Spread collectibles across lanes. Orbs in a row gave the swipes no reason.
  - End on the last solid frame before impact, flash opaque, resume on rubble. The creature ghosted
    through the wall.
  - One swipe per lane change, none on straight runs. The hand led the creature by 0.5 s.
  - Step the level evenly per pickup. One hidden orb jumped it from 30 to 99.

## 15. Perfect stack (timing tower)

- **Fun**: order through timing. A tap releases the swinging block, it thuds down, and the tower
  sways and settles. The off-center block that teeters and falls is the limit the timed drops
  overcome.
- **Board**: a toy skyline, a three-block tower low in the frame, a block hanging from a crane hook.
- **Clips**: two from the same still, first frame only. Fail take 6 s: the block lands on a corner,
  tips, and crashes. Payoff take 10 s: blocks land centered, the camera rising with the tower.
- **Timeline**: 0.45 s release, 3.6 s crash and FAIL. 4.4 s cut. Landings near 5, 7.1, 8.9, and 10.7
  s, each with a counter step. 11.1 to 15 s end card.
- **UI**: hook, height counter, tap per release, FAIL, PERFECT!, shockwaves, end card.
- **Notes**:
  - Write the same release in both prompts. The fail hook dropped the block; the payoff crane
    lowered blocks and let go.
  - Speed up or trim a teeter: one block balanced 2.4 s.
  - Trim before any morph. The fallen block turned into a ghost, and a block appeared from nowhere.
  - Add the same height per block. 10 to 250 m in four blocks is not believable.

## 16. Trick shot (ricochet puzzle)

- **Fun**: cleverness. A finger aims along a dotted line, the ball banks off each bumper in a spark,
  and robots pop into bolts. The missed direct shot is the limit the bank shot gets around.
- **Board**: a top-down corridor loop around one solid block, 45 degree bumpers in three corners,
  the hero in the bottom corridor, a robot target in each other corridor. Give positions in percent.
  Free-form angled walls gave no clear path.
- **Clips**: two from the same still, first frame only. Miss take 5 s. Payoff take 10 s, its path as
  numbered steps: bumper, then target, three times.
- **Timeline**: 0.65 s shot, 3.4 s FAIL. 4.6 s cut. 5.1 s shot, hits near 6.6, 8.5, and 10.1 s. 10.3
  s TRICK SHOT!. 11.5 to 15 s end card.
- **UI**: hook, target counter, aim line, hand, FAIL, impact bursts, TRICK SHOT!, end card.
- **Notes**:
  - State "The ball always skims flat along the floor and can never fly over anything". Four miss
    takes flew over the block.
  - Start the aim line at the nozzle, along the real path.
  - Put the burst and counter on the contact frame, and state "Each robot reacts only at the exact
    moment the ball touches it". Targets burst 0.3 s late.
