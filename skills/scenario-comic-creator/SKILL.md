---
name: scenario-comic-creator
description: "Use when a user wants to make their own comic, manga, BD, graphic novel or illustrated book with Scenario: a short personalized story from a photo or an idea, a branded or training comic, an album, or a book of hundreds of pages adapted from a text. Keywords: comic book, manga, graphic novel, personalized comic, book adaptation, comic pages, speech balloons."
license: MIT
---

# Scenario Comic Creator

## Overview

A comic fails when a late decision breaks early work: a style change after the cast sheets, a
character invented on page 20, lettering proofread only at the end. Lock decisions in order: story,
style, cast, script, pages, review, delivery. The size of the book changes how much is locked and
recorded, never the order.

Three lanes cover a three-page gift and a nine-hundred-page adaptation. Connection and the core
loop: `scenario` skill. Identity across pages: `scenario-consistency`. Reference roles:
`scenario-multi-reference`. Exact text: `scenario-text-overlay`. Iteration: `scenario-refine-loop`.
Storyboards and animatics for film, games or ads stay in `scenario-storyboards`. If a sibling skill
named here is missing from your available skills, load it with `skill_get` (Scenario MCP) or ask the
user to install it (https://github.com/scenario-labs/skills#install); unattended, proceed from tool
schemas and flag the gap.

## Pick the lane

- **Quick**: 1 to 12 pages, one hero, one tale. Gift comics, strips, explainers, a branded story.
  Phases 1 to 8, kept lean.
- **Album**: 13 to 120 pages, recurring cast, chapters, places. Adds a written bible, the cast gate,
  full three-tier review, a manifest and a cover.
- **Book**: over 120 pages, adapted from a text, several sessions. Adds a coverage plan and project
  files.

Start in the smallest lane that fits. Move up when the recurring cast passes four characters or the
work will outlive one session.

## Intake: one round

Ask every question in one message, each with a default, then run without asking again: story,
length, format, look, cast, language, deliverable, budget. A number the user gave beats every
default: a title and a dedication fit inside the pages they asked for. Unattended, take the
defaults, pick where the user would pick (style, likeness), and log each choice with two reasons in
the brief card. If the user has no story or no look, propose options instead of asking an open
question.

## Quick reference

| Phase      | Do                                                                   |
| ---------- | -------------------------------------------------------------------- |
| 1. Brief   | Brief card with a priced estimate: lane, pages, format, language     |
| 2. Story   | Logline, beats and one script per page, before any art               |
| 3. Style   | Three to five directions on the same two pages; the user picks       |
| 4. Cast    | One sheet per recurring character, inspected beside the style anchor |
| 5. Pages   | One request per page: nine-section prompt, about five references     |
| 6. Review  | Three tiers on every page, with crops                                |
| 7. Fix     | Redraw only flagged pages, fresh from the originals                  |
| 8. Deliver | Manifest, PDF, collection, print or web variant                      |

## Rules that carry the quality

- Never edit in a chain. Editing an edit melts faces and costumes. Every page and every redraw
  starts from the original sheets and the original prompt.
- Reference by role: style anchor, identity, costume state, prop, place. The prompt says what each
  image sets and what it never sets. The style anchor sets line, color, paper and lettering, never
  characters or compositions.
- Ask for the whole page, not panels, unless the comic scrolls vertically or will be animated.
- Decide the lettering mode by test, never by assumption (next section).
- State is per panel: costume, injuries, held objects, time of day. Write it into each panel.
- Fix through the prompt. A defect traces to one clause: replace that clause, never append a history
  of corrections.
- Cap attempts: the first page plus one fresh alternative. Later rounds hold only pages with a
  confirmed defect.
- Settle style before sheets, and sheets before pages. A late style change reaches everything.
- Keep the model validated on the first pages. Switching mid-book shifts the look.

## Lettering mode

Run the two pages with the most printed words, every word in the prompt, and proofread each balloon
at 100%.

- Every word exact: **integrated** lettering for the whole book, one language.
- Any word breaks, several languages ship, or text will be edited later: **overlay**. Generate art
  with empty balloons, then add exact text with `scenario-text-overlay`.

Record the mode in the brief card. Never switch silently.

## Worked example: a six-page personalized comic from one photo

1. Intake. The user answers: "Mila turns 8, her cat starts talking, French, watercolor, PDF", and
   attaches Mila's photo.
2. `recommend` with capability `img2img` and the user's own words: one complete comic page, several
   panels, readable dialogue, several reference sheets. On `next_step.type` of `ask_user`, show the
   options. `model_schema_get` on the pick for the reference field, its cap and array rule, and page
   sizes.
3. Price a representative page payload with `dry_run: true`: the real size, the real number of
   references, a prompt of realistic length. Write the brief card with the estimate: pages, sheets,
   style round and a redraw margin.
4. Resize the photo to about 2,000 px on its long side and upload it with `upload_asset`.
5. Script: a logline, six beats, six page scripts with the exact French words, accents included.
6. Style round on two script pages, one dialogue page and one establishing page. Draw the hero from
   a written description, not the photo. Four directions, one skeleton. Show them side by side. The
   user picks one. Record its asset IDs as the style anchor.
7. Cast: settle outfit details first (hood, gloves, mask, crown). Draw Mila's sheet from the photo
   in the chosen style, then the cat's. The user approves the likeness. From here pages use the
   sheet, not the photo. With no photo, draw the sheet from the written description.
8. Run the two densest pages together and apply the lettering test. Then submit the other pages with
   `wait: false` and collect them with `jobs_wait`.
9. Review every page in three tiers, with crops of hands, faces and balloons, and counts of repeated
   objects. Redraw each flagged page once by replacing the guilty clause.
10. Build the manifest, then the lossless PDF, a light PDF to send and a contact sheet with
    `scripts/build_book.py`. Read the contact sheet in order. Report where the PDF, the page files
    and the collection are.

## Read next

- [intake.md](references/intake.md): the questions, photos, formats, estimate, brief card.
- [story-and-script.md](references/story-and-script.md): beats, page craft, dialogue, page script
  format, adapting a text.
- [style-and-cast.md](references/style-and-cast.md): style round, sheets, cast gate, places, props,
  state ledger.
- [page-production.md](references/page-production.md): lettering test, prompt anatomy,
  defect-to-clause table, running pages.
- [review-and-fix.md](references/review-and-fix.md): tiers, mechanism checks, redraws, fix rounds.
- [assembly-and-delivery.md](references/assembly-and-delivery.md): manifest, covers, trim, PDF,
  languages, filing. The PDF builder is [scripts/build_book.py](scripts/build_book.py), run by an
  agent.
- [book-scale.md](references/book-scale.md): the Book lane: coverage plan, project files, ledger,
  sessions.
- [personalized-and-branded.md](references/personalized-and-branded.md): gift comics and company
  comics.

## Common mistakes

- Writing "same character as before": runs have no memory. Attach the sheet every time.
- Feeding the raw photo into every page: pages drift toward photographic rendering.
- Judging by score: crop and compare against the sheet.
- Adding a sheet to fix one page: the style drifts everywhere. Fix the clause.
- Skipping the cast gate: unnamed recurring figures get treated as extras and change page to page.
- Reviewing a page alone: check the previous and next page for state and place.
- Keeping printable words only in the prompt: keep them in the script file and paste them unchanged
  into every redraw.
- Calling a finished PDF proof: open it and read pages in order.
