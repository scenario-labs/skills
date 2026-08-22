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

## Open questions

- How reliably a single-panel reshoot holds the other panels. Verified once: with the approved board
  passed as a third reference and only panel 9's clause changed, panel 9 was corrected and the other
  eleven panels came back unchanged, labels included. One trial is not a guarantee.
- Whether the register finding generalizes to non-photoreal deliveries: an animation-style board for an
  animation-style delivery should follow the same logic, untested.
