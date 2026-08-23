# How this skill was built

Maintainer notes, not runtime instructions. Every rule in `SKILL.md` below is tied to the live run
that produced it, so a future edit can check whether the evidence still holds rather than re-arguing
from taste. All runs used Seedance 2.5 and GPT Image 2 through the Scenario MCP server.

## Why a separate skill

The pose-chain workflow existed nowhere in the repo: the only trace was one sentence in
`scenario-seedance-music-video/references/shots.md`, a supporting file of a different skill. It could
not be folded into `scenario-seedance` either, because that body was already at the top of the house
word target and the combined text would have blown the hard cap. The triggering conditions also
differ: the family skill fires on parameter and conditioning questions, this one fires on a symptom
("limbs teleport", "motion resets at every cut"). A baseline probe with no skill installed had the
agent reconstruct the chaining mechanism itself and flag it as guesswork.

## Decisions and the evidence

### Photoreal panels, not pencil drawings

Initially written the other way round, from a single confounded observation. A 2x2 test on one samurai
script (board style x number placement, sheet held constant) reversed it:

- Photoreal panels returned filmic footage.
- Pencil panels left the model to invent every surface, and it drifted toward posed action-figure
  plastic with odd faces in close-ups.
- Pencil panels paired with a photographic character plate recovered the surfaces but lost the crimson
  armor entirely by the final beat.

The mechanism: the board sets the register of the delivered footage. The first version of this skill
inferred the opposite because the one good pencil-board result came from a board paired with a real
photographic film still, so style and reference quality were never separated.

### Panel numbers: small and low contrast, not "never inside the frame"

An earlier run burned a white panel-number badge into the top-left corner of a 20-second clip, and it
survived an explicit "no panel numbers" negative clause. That looked like proof that numbering must
sit outside the frame. It was not: in the controlled test neither badge-inside board leaked. The
difference was badge prominence, not placement. So the rule is small, low-contrast numbering plus a
check of the delivered corners, and never trusting a negative clause to remove what you drew.

### One plate per character, not a combined sheet

Seedance 2.5 accepts up to 30 `referenceImages` and the prompt binds them by index, so `@image1` can
be one character and `@image2` another. A combined turnaround gives each character an eighth of a
canvas and leaves the model to work out which figure the prompt means. Per-character plates are
unambiguous and full resolution. The earlier grouped sheet was habit, not a constraint.

### The plate's real job is upstream

A photoreal board carried identity with no character plate passed to the video call at all, matching
the best plate-bearing run. The plate's contribution is in making the board's characters consistent
while the board is drawn. It still matters at video time in the chained lane, where the board is never
passed to the model.

### Cinematic labels, not action verbs alone

The first fight boards read as twelve pictures rather than coverage. Labeling every panel with number,
shot size, angle, lens or camera move, then three action verbs, and arranging the panels as real
coverage (master first, hold the axis, climb the size ladder, punctuate with inserts and reactions)
produced boards and videos that read as filmed sequences. The vocabulary itself is standard
cinematography that a model already knows, so `SKILL.md` spends its words on the instruction and the
coverage rules rather than on a glossary.

### Seedance 2.5, discovered but not trusted to rank first

`search` with `query="seedance"` returned 2.5 **last, at relevance score 0**, while 2.0 ranked first
with a 15-second duration cap that cannot deliver a 24-second sequence. So the skill tells the agent to
scan every hit for the newest non-deprecated generation instead of taking the first, and says why 2.5
is the target: the largest reference count in the family and the best identity hold.

### An approval gate before any video run

A board costs a fraction of a video run, so the skill stops for approval on the script, the plates and
the numbered board, and invites a reshoot by panel number. Re-running one panel is a single board call
with that clause changed and the approved board passed as a reference.

### Scripted run versus chained lane

A single scripted run does not deliver a cut per scripted timecode. Against eleven scripted handoffs,
detected hard cuts were 0, 2, 2 and 6 across runs: the model renders most handoffs as camera moves.
That satisfies continuity, which is the point, but it is not editorial control. Twelve discrete shots
require the chained lane.

In the chained lane the pose chain protects motion and nothing else. Boundary stills are independent
generations, so costume detail drifts between them (a mask, a helmet crest, a metal finish) and every
drift lands on a cut. One clean-room run also mirrored two of its seven stills, which would have asked
the fighters to swap sides mid-shot. Hence: pin screen position as well as pose, hold the framing, and
review the stills as a set before spending a video run.

### Why the chained lane lives in a reference file

Body words load on every trigger. After the fixes the body reached the point where the next lesson
would break the 1400-word hard cap, and the chained lane is per-mode detail that only a chained run
needs (four of five live runs used the scripted lane). It moved to
[references/chained-lane.md](references/chained-lane.md); the lane choice, the mutual-exclusion trap
and the cost model stayed in the body.

## What the chained-lane validation added

A clean-room agent was given a 40-second knife duel that had to open on an exact pose, which forces
the chained lane, with only the installed skill as documentation. It picked the lane from the one
sentence about reference mode anchoring frame one, followed the link to the reference, applied all four
disciplines, and verified every join for free from `asset_get`. Frame one was the specified locked-blades
pose and all three joins were the same pose either side of the cut. Four defects came out of it:

- **The board and the image budget could contradict each other.** Two plates, a board and five stills
  hit an eight-image ceiling exactly, leaving nothing to re-render a drifted still, which is the
  dominant failure in this lane. The reference now ranks the board below a reserved repair slot and
  says why: the board is never passed to the video model here.
- **No plate or board model was named at runtime.** The only named one lived in this file, which the
  agent correctly discounted as maintainer notes. `SKILL.md` now carries a hedged authoring-time
  example alongside the selection criteria.
- **A height like 1080 can miss the image model's `step`,** failing as an opaque internal error. Folded
  into the existing canvas sentence.
- **A shot can be refused on its generated audio, not its picture.** `generateAudio: false` clears it.
  Covered in the reference, with the instruction not to leave one shot silent while others carry sound.

## The coherence gate, and why the quality gate alone is not it

Two boards reached a video run carrying frames that break physical sense: an extreme close-up with four
gauntlets for two fighters, an unattached glove and a hilt guard floating with no blade through it; and
a low-angle wheel shot whose car had two different wheels, only one whitewall, no wheel arch, and a
toy-proportioned body. Neither survives a viewer's first glance, and both cost a full video run.

Three measurements shaped the gate that now exists:

- **A board-level verdict hides panel defects.** All three boards scored 88 and `pass` at high
  sensitivity while carrying those frames. Twelve panels average their defects away.
- **Scoring the panel alone does not fix that either.** The broken-car panel, scored in isolation, came
  back 92 and `pass`, and the report praised the "chrome rims" that were the defect. The gate detects
  artifacts; it has never seen the plate, so it cannot know the car should wear matching whitewalls in
  proper arches.
- **The score is a weak signal for a repair.** The corrected wheel panel also scored 92. What changed
  was the flaw list, from praising the rims to naming a taillight housing. Judge a repair on the
  differences checklist and the new `reasons`, not on the number.

So the gate is two passes per panel, and a panel must clear both: `asset_quality_gate_run` for
artifacts (it did find melted finger joints, warped speedometer numerals and doubled blade edges that
the eye skipped), and a spot-the-difference against the plate for anything only wrong beside the
reference. What the two passes found together, across three boards: samurai 4 and 10, cars 2, 3, 8 and
11, dancer 3, 7 and 8.

Repair is by replacement, not by re-rolling the board: slice with `model_scenario-image-slicer`,
regenerate only the failing panel with the plates as references and the correction stated positively,
then recompose with `model_scenario-compose-image` so approved panels are pasted rather than
regenerated. Measured cost of the loop: 1 CU to slice, 1 CU per panel scored, 47 CU per repaired panel,
2 CU to recompose, against 2730 CU for the video run it protects.

One honest side effect: replacing a whole cell replaces its caption too, so a repaired panel's label
renders at a slightly different size from its neighbors. Compositing only the art region over the
original cell would avoid it, at the cost of locating that region per board.

## The full-flow validation, three sequences from scratch

Three new sequences were built end to end through all nine steps: a flamenco courtyard, a staff duel on
a temple terrace, and a 1970s night rally. New cast, new compositions, 8 panels each at 3 seconds, 24
panels generated individually, all 24 gated, 8 repaired, 3 boards composed, 3 videos delivered.

What it proved and changed:

- **Per-panel gating localizes what board scoring hid.** Six panels warned or scored low across the
  three sequences, and every finding was specific: melted fingers on the floreo, warped rally dials, a
  staff broken into two misaligned segments, a driver's hand fused to the wheel. All had passed my own
  eye first.
- **The differences pass caught what the gate never mentions.** In one rally panel the yellow car sat
  ahead of the white, contradicting the brief. Every score on that panel was fine.
- **An intentional annotation reads as a defect.** The gate flagged the small in-frame panel numeral as
  "an unwanted watermark" on every single panel, depressing scores by a design decision. Worth knowing
  before treating per-panel scores as absolute.
- **A composed board must stay inside a 0.4 to 2.5 aspect ratio.** Two 1080p runs failed outright on a
  four-by-two grid of 16:9 panels (3.56). Three-by-three (1.78) passed. Only the job record's `hint`
  names the range.
- **Some panel flaws do not reach the video.** The staff sequence was the worst-scoring board of the
  three, flagged five times for hands merging into wood and staffs bending, and it still delivered a
  clean 24 seconds with rigid staffs and four distinct hands at the bind. Prop geometry gets re-derived;
  burned-in graphics and plan errors do not. That distinction now sits in the reference, because it
  decides how many repair rounds a flaw class deserves.

Also measured: the actual spend for the whole PR came to about 26k CU, against a running estimate of
41k that had been accumulated from per-call arithmetic rather than read from `usage`. Read the meter.

## Open questions

- How reliably a single-panel reshoot holds the other panels. Verified once: with the approved board
  passed as a third reference and only panel 9's clause changed, panel 9 was corrected and the other
  eleven panels came back unchanged, labels included. One trial is not a guarantee.
- Whether the register finding generalizes to non-photoreal deliveries: an animation-style board for an
  animation-style delivery should follow the same logic, untested.
