---
name: scenario-multi-reference
description: "Use when one image must be built from several reference pictures through Scenario, each contributing one thing: the character, the place, the pose, the style, the light, the material, or the palette. Also when a reference leaks into the result (its object, colors, or face showing up where it should not) or is ignored. Keywords: multi-reference, reference roles, give each picture a job, combine references, style reference, pose reference, palette swatch."
license: MIT
---

# Scenario Multi-Reference

## Overview

Given four or five reference pictures and a loose prompt, an image-edit model averages them: the style picture's subject walks into the scene, the pose mannequin shows up in wood, the palette swatch barely recolors anything. The fix is a prompt grammar, not a different model: give **each picture exactly one job**, say what it lends, and name what it must **not** lend. The approved picture can then open a short film whose prompt carries motion, camera, and sound only.

This skill builds one image from many inputs. Holding one look across many images, or animating a character from its references, is `scenario-consistency`; per-family reference caps and sizing live in the model-family skills `scenario-image` lists; the film pass is `scenario-video`; a refused input or output is `scenario-moderation`. Connection and the core loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

Write one line per picture as `Image N (what it is) = JOB. What it lends. Do not ...`, where N is the picture's position in the reference array and the job is in capitals.

| Job        | Lends                            | The "do not" clause names                                                                                     |
| ---------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| WHO        | the character, product, creature | the photo's pose, light, colors, and realism when only the idea should carry ("Use only the idea of a gecko") |
| WHERE      | the place and its layout         | nothing, or "redrawn as woodblock architecture" when the medium differs                                       |
| STYLE      | medium, render, texture          | every object in the style picture: "Do not include the raccoon, the kitchen, the apron or the pot."           |
| POSE       | the body pose                    | the figure that carried it: "Do not show the mannequin or any wood."                                          |
| ANGLE      | the camera position              | the sketch's subject: "Do not include the lighthouse."                                                        |
| LIGHT      | the light only                   | what the light fell on: "Do not include the flowers or vase."                                                 |
| PALETTE    | the only allowed colors          | the banned colors ("No green anywhere."), with each element's color named                                     |
| MATERIAL   | a surface                        | its source: "Do not show any fish, fins or water."                                                            |
| EXPRESSION | a face's mood                    | the anatomy: "No human skin, no nose, no ears, no hair."                                                      |
| WEAR       | clothing or armor, worn as is    | what must stay visible: "The cat's own face stays visible; no human face mask."                               |
| LAYOUT     | grid and composition             | the reference's own words: "Do not copy the word MONDAY."                                                     |

Rarer jobs were tried on these sets but not kept, so treat them as untested: PROP (an object the subject holds), PATTERN (a repeated motif: "There is no creature in the scene"), and SHAPE (a silhouette: "Use only his silhouette ... as one giant solid flat cut-out shape"). WEAR also takes a design idea rather than the object: "a modest couture gown designed from this jellyfish ... Do not show a real jellyfish." Read [references/kept-prompts.md](references/kept-prompts.md) when the requested medium matches one of the eight kept sets (3D animated film, claymation, product photo, ukiyo-e print, fashion editorial, 16-bit pixel art, tilt-shift miniature, two-ink risograph poster), or to model a film prompt.

Rules that held across eight kept sets of four or five references:

- Prompt shape: one sentence naming the medium, then "Each reference picture has exactly one job:", one line per picture, then the framing (shot size, placement, mood).
- Lead with the job most likely to be ignored, usually STYLE, and write "This is the most important job". Line order is free; the image numbers bind to the array order, so moving a line never reorders the references.
- One job per picture: two jobs on one picture blur both. Leave a picture with no job out of the array.
- Clean inputs: plain backgrounds, no text, no logos or readable signs. A street photo with real shop signs was refused as a reference.
- Text in the picture: quote it exactly and add "No extra words, no duplicate text."

## Worked example: a grumpy claymation toaster from four pictures

Four pictures, one job each: a chrome 1950s toaster (WHO), a scowling old man (EXPRESSION), a 1970s kitchen (WHERE), and a clay snail (STYLE).

1. Collect the pictures from the user. A missing one can be generated first (`txt2img` per `scenario-image`) on a plain background with no text.
2. `upload_asset` each one (on the multipart path, then `upload_asset_complete`) and fix the order: `["asset_toaster", "asset_man", "asset_kitchen", "asset_snail"]`. The numbers in the prompt are these positions.
3. `recommend` with `capability="img2img"` and the user's own words ("one claymation still from four reference pictures, each with one role"), handle `next_step` as the `scenario` skill directs, and prefer a ranked entry that takes several references. `model_schema_get` the pick: the reference field must be `array: true` with a cap of at least four, and its sizing and quality fields come from the same schema. Pass the array as is; a bare string is dropped silently and the run succeeds without it.
4. Write the prompt with STYLE first. A first draft with the STYLE line last came back as chrome CG:

   ```text
   A handmade stop-motion claymation film still, everything sculpted from matte plasticine. Each reference picture has exactly one job:
   Image 4 (clay snail) = STYLE. This is the most important job: the whole scene, the toaster, the counter, the cabinets, the tiles and the fridge are all chunky handmade plasticine with visible thumbprints, tool marks and soft rounded edges, slightly lumpy, matte, like a miniature stop-motion set. No photoreal surfaces, no real chrome, no CG. Do not include the snail.
   Image 1 (chrome toaster) = WHO. The character is this 1950s toaster shape, sculpted in silver-gray clay: rounded body, black lever and knob, two bread slots.
   Image 2 (old man) = EXPRESSION only. The toaster has two clay eyes, bushy white clay eyebrows and a mouth with this exact grumpy expression: deep scowl, furrowed brows, pursed lips. No human skin, no nose, no ears, no hair.
   Image 3 (1970s kitchen) = WHERE. This kitchen layout and colors: orange cabinets, mustard flower tiles, avocado fridge, wood paneling, wall clock, all made of clay.
   Wide shot, the toaster on the counter in the foreground, two clay slices of toast half popped up.
   ```

5. `model_run` with `dry_run=true` and `parameters` holding the prompt, the four ids in the schema's reference field, and the sizing (the kept sets ran 3:2 landscape at a high quality tier). Price the film too when one is wanted (step 7), with an uploaded reference standing in for the first frame, and quote the user the total before anything paid runs; re-price the film with the approved picture before running it. Then run with `wait=false` and `jobs_wait`, re-called with `pending_job_ids` as `job_ids` on timeout, never a second `model_run`. `asset_display` the result.
6. Check every picture for a leak: clay everywhere and no chrome, no snail, a scowl with no human nose, ears, or skin, the kitchen's colors and layout. A leak means that picture's line was too loose: tighten that line and run again, never retouch the output.
7. Optional film: `recommend` with `capability="img2video"`, then the approved picture as the first frame in the field `model_schema_get` names, sound on (`scenario-video` for the family contracts). The film prompt describes motion, camera, and sound, because the frame already carries every job: "Stop-motion claymation, choppy handmade frame rate, static camera. The grumpy clay toaster scowls harder, rattles with irritation, then the two slices of toast pop up with a jolt ... Everything stays plasticine with fingerprints. Mechanical toaster clunk, spring ping, a low grumble." Six seconds at 720p carried every kept set.
8. `asset_download` the picture and the film.

## Common mistakes

- **No "do not" clause.** The style picture's subject walks in: the raccoon chef, the snail on the counter, the boats from the wave print. Name every object of the style picture.
- **The main subject copied as is.** A green gecko photo came back as the same green gecko inside a woodblock print. Write "Use only the idea of a gecko ... Do not copy the photo's pose, lighting, colors or realism", lead with STYLE, and mark the palette "strictly".
- **A weak recolor.** "Palette only" barely moved the picture. Name each element's color and the colors that may not appear.
- **An ignored job.** Move its line to the top with "This is the most important job", and state the medium in the opening sentence too ("everything sculpted from matte plasticine").
- **An accidental logo.** Red, white, and blue swooshes on generated billboards read as a soda brand: the image-to-video model refused that first frame, and the image editor then refused it as an input. Say what every sign shows (waves, clouds, cranes) and add "no logos, no text".
- **A refused design or garment.** A famous lounge chair named in a prompt was refused: describe an original design instead. A translucent gown hit the output filter; "opaque, fully covered, high-necked" passed.
- **Film drift.** A bass guitar changed color mid-clip. Run it again "almost static", list what must not change, and move only what should move. Judge the whole clip, not its first frame: a drift can fade in mid-shot.
