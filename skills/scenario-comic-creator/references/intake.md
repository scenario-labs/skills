# Intake: the guided interview

Ask once, at the start, as one numbered message. Give a default for every question so the user can
answer "go". Then run without further questions. An unattended run takes the defaults and writes
each assumption into the brief card.

## The questions

1. **Story**: a premise in one sentence, or a source text. Who is it for, and what should the last
   page leave them feeling? Default: write five loglines, cut the ones the average would write, and
   offer the best three.
2. **Length**: story pages, plus cover and extras. Default: Quick lane, 8 story pages and a cover.
3. **Format**: trim, reading direction, color or black and white, panels per page. Default:
   portrait, left to right, color, four to six panels.
4. **Look**: one comic, film or painting they love and one they dislike, or "show me options".
   Default: a style round with four directions that differ by concept.
5. **Cast**: who appears, and a photo or a description for each. Default: invent the cast from the
   premise.
6. **Language**: the language of the printed words, and whether other languages follow. Default: the
   user's language, one edition.
7. **Deliverable**: reading PDF, print file, web strip. Default: reading PDF.
8. **Budget**: a ceiling on spend and time. Default: price the plan, state the number, proceed.

A number the user gave beats every default. A dedication, cover or back cover is an extra: offer it,
and add it only when the user asks or the page budget allows. Unattended, where the user would pick
(a style, a likeness), pick and log the choice with two reasons.

Album and Book lanes add:

- The recurring cast and how each character changes over the story.
- The chapter plan.
- The source edition and what may be cut.
- Who reviews pages, and how often.
- How sessions hand over to each other.

## Propose options, never a blank page

- No story: write three loglines of one line each. Each names the hero, the want and the obstacle,
  and they differ in genre or tone.
- No look: name four directions in concrete terms (line, tone, palette, lighting, lettering), never
  "make it nice".
- A story that is only a mood: restate it as a five-line beat sketch and ask for corrections once.

## Style references from the user

- Images the user supplies steer the style round only. The approved style anchor replaces them from
  then on.
- A named comic, film or era: name the artists in the prompt and add the traits and one hard rule
  ([art-direction.md](art-direction.md)). The name sets the family and the traits do the work. If a
  team has IP detection on artist styles, or a model refuses a name, keep the traits and drop the
  name (`scenario-moderation`). For a commercial deliverable, the buyer decides whether to name
  living artists. Movements and long-published masters give the same families.
- For published or commercial work, the user confirms they hold the rights to any art they upload as
  a reference.

## Characters from photos

- Ask for one clear front photo in good light with the face unobstructed. A three-quarter photo
  helps. Add a full-body photo when the outfit matters.
- Use only photos the user has the right to use. For a child, the user is the parent or guardian.
- Ask how faithful the likeness should be: recognizable but stylized (default) or near photographic.
- Judge likeness on the hero sheet, after the style is chosen. The style round draws a provisional
  hero from words, because a photo as the only identity reference pulls every direction toward
  photographic rendering.
- No photo: write the hero's age, hair, build and outfit, and draw the sheet from that.
- Resize a phone photo to about 2,000 px on the long side before uploading.
- The photo sets face, hair and build. It never sets clothes, pose or background unless the user
  says so.

## Format choices

| Format                  | Page ratio (w:h) | Panels per page |
| ----------------------- | ---------------- | --------------- |
| Franco-Belgian album    | about 3:4        | 4 to 6          |
| US comic                | about 2:3        | 4 to 6          |
| Manga volume            | about 5:7        | 4 to 7          |
| Picture book            | square or 4:3    | 1 to 3          |
| Vertical-scroll webtoon | one tall strip   | 1 per image     |

- Pick the closest portrait size the model's schema allows and trim at assembly.
- Size by deliverable: about 1,500 px wide for screen reading, about 2,500 px wide for A4 print at
  300 dpi. Larger sizes cost more and make heavy PDFs.
- Young readers: three to five panels, large lettering, clear shapes. Teens and adults: five to
  seven panels.
- Right-to-left reading: write it into the script and every page prompt. Page files stay in reading
  order, and the printer is told the binding is on the right.

## Estimate before starting

1. `model_schema_get` on the chosen page model, then `model_run` with `dry_run: true` on a
   representative page payload: the real size, the real number of references, a placeholder prompt
   of realistic length. Real references change the price slightly.
2. Estimate = pages x per-page price x (1 + redraw share), plus sheets and the style round.
3. Plan one extra attempt on about a third of the pages in a first book. A mature prompt template
   needs fewer.
4. Tell the user the number and the page count it buys.

## Brief card

Write it to a file. Every later phase reads it.

```
Title (working):
Lane: Quick | Album | Book
Logline:
Audience and tone:
Ending feeling:
Pages: story __ + cover __ + extras __
Format: trim __, direction __, color __, panels per page __
Language(s): __ ; lettering mode: integrated | overlay (set after the lettering test)
Look: direction chosen __ ; style anchor asset IDs __
Cast: name, role, photo or description, sheet asset ID
Places:
Source text (Book): edition, chapters in scope, what may be cut
Deliverables:
Budget and estimate:
Assumptions made without asking:
```
