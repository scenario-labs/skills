# Expert notes (the lead's sources, in depth)

What each source teaches the agent protocol, with timestamps checked against the transcripts.
Credentials come from each video's channel and description. The craft of each domain (masks, skin,
type, textures) sits in the specialists' own notes; these are the protocol-level lessons: safe
document handling, non-destructive structure, measuring, judging, batch.

## Agents driving Photoshop

**Glyn Dewis** (photographer and retoucher), "ChatGPT Can Now ACTUALLY Use Photoshop", 2026-10-01.
The clearest record of a general agent editing in Photoshop 2026.

- His prompt states the constraint up front: "Make it non-destructive so you can edit it later, but
  don't save it. Just leave it as layers" [ZGsgdObKOZA 02:05].
- The agent fixed a color cast with a Curves adjustment layer in Color blend mode and left the
  Background intact [ZGsgdObKOZA 03:30].
- On the next task it tried to save and he stopped it [ZGsgdObKOZA 06:20]. A constraint stated in a
  prompt did not hold, so the lead enforces it in code (`ps_run.lint`).
- The agent put the sky on its own layer and converted it to a smart object, so the Radial Blur
  stayed editable [ZGsgdObKOZA 06:51].
- He tests a cutout on a solid color fill layer below it, which exposes halos and see-through fur
  [ZGsgdObKOZA 11:44]; he notes the agent renamed its layer at the end [ZGsgdObKOZA 11:13].

**Jared Verdi** (developer, author of an open-source agent bridge for Photoshop), "Automate
Photoshop w/Codex & Claude Code", 2026-02-27. Interface design for an agent, not Photoshop craft.

- Every operation describes itself: arguments, aliases and an example payload in its help
  [ojOTkInaZIk 02:48]. The lead's scripts follow this: each docstring lists its calls.
- He prefers a CLI with rich help to a long tool list in the agent's context [ojOTkInaZIk 03:19].
- The help was redesigned around the commands the agent guessed: "meet it where it already is"
  [ojOTkInaZIk 07:47].
- Each phase is a JSON file applied as one transaction; keep the files and they are a recipe
  [ojOTkInaZIk 10:02]. The lead keeps job bodies as files for the same reason (procedures P10).
- The agent renders the canvas to PNG and reads it: "it has vision into what it's creating"
  [ojOTkInaZIk 11:08]. It then fixed a shape bleeding out of a banner [ojOTkInaZIk 11:42].
- Its first pass left text touching button edges, to fix by hand [ojOTkInaZIk 12:15].

## Undo, Actions and batch

**Unmesh Dinda** (PiXimperfect, Photoshop educator), "Photoshop Actions Just Got a BRAIN",
2025-05-09, on the then-beta Actions panel.

- One undo after a long action, and the Playback Options setting that controls it: Create single
  history state [6vsnsS92gKc 10:18], [6vsnsS92gKc 11:24].
- His complaint: many built-in actions are destructive, "burned into the pixels", with no way to
  change noise or contrast afterwards [6vsnsS92gKc 11:57].
- Some actions need a pixel layer and fail on a smart object or adjustment layer; he stamps visible
  first [6vsnsS92gKc 11:57].

**Ted Chin with host Jacob Paris** (Adobe Live; surrealist photographer and compositor), "Feature
Friday: How to Use Modernized Actions", 2026-07-25. Captions are a garbled translation; the point
survives: an action run inside a smart object may merge its layers [0OUJ49Fqs1w 26:48], so they
duplicate the layer, run, and restore [0OUJ49Fqs1w 29:58].

**Tunde Victor** (Teelens Visual, portrait and studio photographer), "Batch Editing in Photoshop",
2026-10-11. The classic batch pipeline end to end.

- Inside the recorded action he renames and groups every layer, so each file comes out with the same
  readable stack [4oAcuL0Q7Ec 04:45].
- In File > Automate > Batch he sets Errors to Stop For Errors [4oAcuL0Q7Ec 06:52] and turns on
  Override Action "Save As" Commands [4oAcuL0Q7Ec 07:25].

**Art, Life & Photography channel** (portrait painter and retoucher; host's name not verified),
"Rewriting and Writing a Photoshop Action", 2026-02-23.

- Rename the copy, or duplicates pile up as "copy, copy, copy" [MQDF-UW5-Uk 06:06].
- Rename every layer an action makes; new layers fall back to "Layer 1" [MQDF-UW5-Uk 06:38].
- Playing from a step inside an action starts it midway [MQDF-UW5-Uk 07:42].

## Layer hygiene

**Colin Smith** (photoshopCAFE, Photoshop trainer) shows unnamed layers being named by content on
Photoshop on the web [eT_muXSPkeo 01:09]. **Brandon Woelfel** (photographer, Adobe Live guest) runs
Layer Cleanup on the desktop: delete empty layers, rename by content, for the document or a
selection [7U4GERm0HnU 20:30]. Before that he says "maybe it's worth naming them first, because
things are starting to get a little confusing" [7U4GERm0HnU 19:59].

## Selections, context and what a model sees

**Julieanne Kost** (Adobe Principal Digital Imaging Evangelist), "Partner Models Added To Generative
Fill", 2025-09-26.

- With Select All and a local prompt, Adobe's model "fills the entire selection" with the subject; a
  generous selection around the area works instead [1bFcFVbbzjc 07:13].
- Partner models received only the selected area and failed for lack of context; with the whole
  image selected they succeeded [1bFcFVbbzjc 07:46].

**Jesús Ramirez** (Photoshop Training Channel, key art designer), Adobe's "How Pros Retouch and
Composite with Generative Fill", 2026-07-20: Adobe's models look at the entire image for context,
while partner models "only see a square crop around your selection" [Ot_h4s1mXas 01:36].

**Colin Smith** on the same question: Generative Fill "can't generate outside" the selection, but
"doesn't necessarily fill that area" [pgBjkr2X6wI 02:45]. And of Harmonize: "it's actually
generating the entire image and just masking out the parts that have changed", at a capped
resolution, so at 100% the generated area is soft [dWiOA5YZXwc 03:19]. Applying it to a smaller
region restored the detail [dWiOA5YZXwc 08:27]. Generating again on a generated layer replaces it;
make another selection to keep both [f-7wkNmAtDk 02:05].

## Measuring and judging

- **Ramirez:** "Always work at 100% so you can accurately judge the details and sharpness. Any other
  zoom level can be misleading" [a7E4HlrAc3w 01:05].
- **Colin Smith:** a generated join still faintly visible at 256% cannot be seen at 100%
  [mGV_jkmPjcY 06:38]. Judge at 100%, not above it.
- **Dinda, alignment by difference:** set the result's blend mode to Difference; lines show wherever
  it is not aligned [mSgSaisb6Kg 04:55]. **Colin Smith** nudges a layer until the Difference view
  goes black [iy0IxTpT4OY 03:47].
- **Dinda, on bad takes:** a failed take still "counts against your limits" [mSgSaisb6Kg 08:44].

## Disagreements and how to decide

| Question                       | Positions                                                                                  | Decision for an agent                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| Does the model fill the mask?  | Kost: it fills the whole selection. Colin Smith: not necessarily, only never outside it.   | Measured with Scenario image-edit models: it fills. Select tight.           |
| How much context?              | Ramirez and Kost: partner models see only the crop, so give them more or the whole image.  | Capture selection plus 32 px or more; whole canvas for whole-image edits.   |
| Is destructive editing fine?   | Woelfel: "sometimes we like destructive change" [7U4GERm0HnU 19:27]. Dinda: baked presets. | On the user's file, never. Destructive steps go on duplicates the job owns. |
| One undo or many?              | Dinda: one state per action by default, steps on demand.                                   | One named state per job; split work into jobs the user can undo one by one. |
| Align by eye or by Auto-Align? | Dinda runs Auto-Align [mSgSaisb6Kg 08:12]; Colin Smith nudges by eye on Difference.        | Measure: keep Auto-Align only when the structure score drops 10% or more.   |
| What zoom to judge at?         | Ramirez: 100%. Colin Smith: above 100% exaggerates.                                        | 100% crops for defects, plus a whole-canvas preview at viewing size.        |

## What the agent adds that no source does

- Save, close and quit refused in code, since a prompt constraint did not hold [ZGsgdObKOZA 06:20].
- Numbers for each look: outside difference, texture ratio, halo rim, skin line, structure score,
  identity at a small size.
- A quote and the user's yes before every paid run, and one quote for a whole batch.
- Provenance in the layer's metadata, so a generated layer can be traced after a save.
