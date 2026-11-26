# Expert notes (lead)

What practitioners observed when an agent or an assistant drove After Effects, and the operating
rules they state for any project. Format: (expert or channel, video id, time). Video URLs are in
[sources.md](sources.md). Lines marked [added] are this skill's own conclusions.

## Setting up and connecting

- Close every open dialog before a run: a dialog blocks script execution (workflow demo, 3AIZ4FT61aw
  00:04:22).
- A bridge needs the preference "Allow Scripts to Write Files and Access Network", and a panel or
  startup script that stays loaded. Without it commands stay queued (Aidan Stanik, YTOwQj-n7ME
  frames 00:04:41 and 00:05:51).
- Setup time varies from "under 5 minutes" (YTOwQj-n7ME 00:11:09) to "almost an hour" when the first
  requests went to the wrong tool (Jake In Motion, QLZNiwaKqWg 00:02:47).
- A whole stock video given as a reference crashed After Effects. After the restart the agent chose
  a lighter method (3AIZ4FT61aw 00:10:31).
- [added] Test a channel with a harmless read that returns a value, then a create plus a captured
  frame. A status ping proves nothing about the main thread.

## Where agents pay off

- Wiring: sorting the Project panel, renaming 40 layers called "Shape Layer N" by what they are,
  labels by type, trimming layers to content (bEO3z86mtbI 00:03:02).
- "The expression on its own is never the problem. It's the rig built around it." Data-driven
  animation is about 10 percent animation and 90 percent wiring (bEO3z86mtbI 00:04:17).
- Rules over hand keys: asked for a dot with a trail of followers, the agent wrote one follow rule
  with a delay per dot, so editing the leader moves the trail (3AIZ4FT61aw 00:04:22).
- Volume: 375 layers and over 2,500 keyframes for a kinetic type piece, estimated at 2 to 3 days by
  hand, built in under an hour (3AIZ4FT61aw 00:17:49).
- Versioning: 50 variations of one ad from a CSV. "Excellent for small batches"; at hundreds or
  thousands a render service is needed (bEO3z86mtbI 00:05:59).
- Self-check on rendered stills caught a glow clipped by a layer edge and a menu bar cut off by a
  camera push before the person saw them (3AIZ4FT61aw 00:13:12).
- An in-app assistant rendered frames to check its own work and corrected a halo it judged
  "hard-edged and oversized" (Jake In Motion, RcNUE6lg3fE frame 00:00:45).
- Exposing controls: one assistant run on a finished design took about 11 minutes and exposed 39
  Essential Graphics controls (RcNUE6lg3fE 00:01:23).
- Small utility scripts (reverse the stacking order of selected layers) take "no time at all" to
  produce (Jake In Motion, MawgwAWka4w 00:03:00).
- Exact easing can be taught: one expert exported his named curve library with exact values, so a
  prompt naming a curve reproduces his look (bEO3z86mtbI 00:05:38).

## Where agents fail

- Visual reasoning: "Its visual reasoning is terrible" for choosing effects, designing a scene from
  nothing, matching colors and fonts. A reference plus the reason for each effect "makes the
  difference huge" (bEO3z86mtbI 00:02:22).
- Animation judgment: the agent applies principles on paper, but art direction and composition are
  weak (QLZNiwaKqWg 00:01:21, 00:12:39).
- Missing eases: "The first version will look like a corporate slideshow. Linear movement, no
  overshoot, no anticipation" (bEO3z86mtbI 00:04:39).
- Constant motion on every element and odd scene changes. Offsetting elements by frames would have
  fixed it (Vlad Sateev, _k8rOBob6k8 00:04:07).
- Maintainability: stacks of hold keys on opacity, posterized time written as an expression where a
  lower comp frame rate would do, renamed effects (QLZNiwaKqWg 00:09:00 to 00:10:06).
- Layer order: each new layer is added on top, so an agent must resolve indices again before styling
  (bEO3z86mtbI frame 00:02:30).
- Generated plates accepted with defects the person found by looking closely: compression artifacts,
  a logo that shrinks between states, a shadow that rotates with its object (QLZNiwaKqWg 00:08:28).
- Audio: without the voiceover or effects in the comp the agent only guesses where each word lands.
  Put the audio in first (3AIZ4FT61aw 00:18:51).
- 3D "needed far more wrangling than 2D" (3AIZ4FT61aw 00:18:28).
- A style reference folder gave a revision in 10 minutes and the composition was still weak: do not
  promise a style clone (QLZNiwaKqWg 00:13:22).
- An assistant misreported its own abilities, saying it could not create skills or write files
  (_k8rOBob6k8 frame 00:03:48).
- Undo: "Control Z rolls back an entire build, not just one change at a time" (3AIZ4FT61aw
  00:19:25). [added] That is the behavior to design for: one named undo step per stage, so a person
  can step back stage by stage.

## How experts constrain an agent

- Numbers in every request: axis, frequency, amplitude in pixels, start and stop times, padding,
  radius (YTOwQj-n7ME 00:08:01, 00:09:55).
- Restate a duration in frames and flag a frame rate mismatch: "13:22" at 30 fps is 13.733 s, and
  the edit ran at 25 fps (_k8rOBob6k8 frame 00:01:37).
- Ask clarifying questions before beginning when time or credits are at stake: duration, background,
  sound (QLZNiwaKqWg 00:05:56).
- Fence the task: "only use After Effects" forced native work (QLZNiwaKqWg 00:03:29).
- Small, specific steps. Review code before it runs in a professional project (aescripts +
  aeplugins, s6SjIehPGhc frame 00:00:30).
- References beat adjectives: "Whenever possible, feed it a visual reference of what it is that
  you're going after" (3AIZ4FT61aw 00:12:39).
- Hand over a finished design and ask for the rig and the controls, then adjust by hand (RcNUE6lg3fE
  00:02:28).
- One-line notes at the "95 percent there" stage, and options to choose from (top three music picks)
  (3AIZ4FT61aw 00:09:21, 00:13:44).
- A fresh conversation per project keeps cost down, because each action rereads the whole
  conversation (3AIZ4FT61aw 00:21:19).

## What stays human

- "This isn't a replacement for taste." The agent checks stills, not motion, so ease and timing are
  the person's call (3AIZ4FT61aw 00:19:25, 00:18:51).
- "Being efficient at After Effects doesn't make you a better motion designer" (MawgwAWka4w
  00:00:39).
- Judge by playing the result, then by opening the comp: keys (U) and Effect Controls. "If the
  client has any notes, then you're going to be the one who has to dig through this" (QLZNiwaKqWg
  00:09:00).
- Sound taste and the balance between music and effects (3AIZ4FT61aw 00:09:21).
- Whether the style matches the reference (QLZNiwaKqWg 00:12:39).

## Operating rules for any project

- Save the project and make a backup before an agent works (bEO3z86mtbI 00:02:03). Save versions
  while experimenting (3AIZ4FT61aw 00:19:25).
- Keep an original and stay non-destructive: a copy of the source file, a reference PNG, the uncut
  source as a bottom layer (School of Motion, fuDs-WPyAR4 00:01:12).
- Name layers by function. Rename text layers so edited text does not rename them. Put template
  sliders on one Control layer (ECAbrams, EG7m3j1X9hQ 00:02:06, 00:04:24).
- Look properties up by match name (NT Productions, DTBtfFiyjNU 00:31:59).
- Guard first (`instanceof CompItem`), and wrap each run in one undo group (DTBtfFiyjNU 00:27:15,
  00:37:25).
- Check `File.exists` before `importFile` (DTBtfFiyjNU 00:40:09).
- Any effect, closed mask or layer style on a collapsed precomp flattens it again. Disabling is not
  enough (School of Motion, J3ApvB8sqD0 00:14:31).
- Collapse Transformations ignores cameras inside the precomp: add a camera in the parent comp (Jake
  In Motion, Ns41v75th_I 00:06:31).
- Pre-render only what is stable and keep editable layers live (Adobe Video, G8BAjmaVaDg 00:01:32).
- Measure what slows playback. Profiler numbers on cached frames read low: purge for honest numbers,
  in a session the agent owns (G8BAjmaVaDg 00:00:11, 00:01:00).
- Proxy Use in Render Settings defaults to Use No Proxies. Use All Proxies only on purpose (Motion
  Science, y3Qgs2N5z1Y 00:02:53).
- Read the Render Settings and Output Module summary of each queue item before rendering, then open
  the files and compare name and size (SternFX, FZ9yfCeZZMA 00:02:54, 00:11:33).
- Duplicate a built-in template with a suffix instead of editing it (FZ9yfCeZZMA 00:04:19).
- Test a template with extreme inputs, 3 and 303 characters, before queuing renders (School of
  Motion, uo5k4_vu5Vk 00:33:14).
- Render outside the GUI with `aerender` so the artist keeps working (Workbench, vAenMHvAHQI
  00:00:38).
- Get approval at each gate (storyboard, style frames, first animated draft) and lock timing in an
  animatic before animating (MotionXP, Gqr0WrahBBs 00:04:24, 00:08:02).
- Lock the picture before sound design. Audio is its own stage (School of Motion, 1nChUaFL3rc
  00:04:54).
- Check effects at 100 percent: toggle on and off at high zoom and compare (Motion Science,
  M7Ml1KoO4jY 2:10).
