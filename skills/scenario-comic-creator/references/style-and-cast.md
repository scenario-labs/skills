# Style and cast

Settle the style on sample pages first. Sheets come second, page art third. A late style change
reaches every sheet and page.

## Style round

1. Pick two pages from the script: one dialogue page and one establishing or action page.
2. Write one prompt skeleton for each page. Only the style paragraph changes between directions.
   Draw the hero from a written description, not from the user's photo.
3. Draw three to five directions on those two pages. They come from
   [style-library.md](style-library.md) or the same formula, each with two named influences, hard
   rules and a FORBIDDEN list. Add a plain-prompt stock twin of the same page and run the taste
   review in [art-direction.md](art-direction.md). Run them on the model the book will use. A
   different model changes the look, so when two models rank close, draw the round on both.
4. Show every direction side by side on a contact sheet and let the user pick.
5. Record the winning pages' asset IDs. That page set is the style anchor, and it is reference 1 on
   every later page. Each page prompt says it sets line, color, paper and lettering only, never its
   characters, poses or compositions.
6. Never reference a page from a rejected direction.

A direction is written in concrete terms, never as a genre name:

- Line: weight, continuity, ink or pencil or none.
- Tone: flat color, painted, screentone, watercolor, grain.
- Palette: named colors, or "black and white with purposeful blacks".
- Light: soft, hard, time of day.
- Lettering: capitals or mixed case, hand-lettered feel, balloon shape.

## Character sheets

One sheet per recurring character. Each shows:

- A calm face.
- Full body, front and back.
- One expressive pose.
- Signature props, and costume layers named.

Procedure:

1. Settle the outfit details first: hood, gloves, mask, hair, glasses, and every costume state (day
   clothes, disguise). Give each state its own row. Then generate the sheet in the approved style,
   from the brief or from the photo.
2. Inspect it beside the style anchor and beside the other sheets. Drop a sheet that changes the
   style.
3. When two characters look alike, check they stay distinguishable on one page.
4. File each sheet with its asset ID and a name.

Rules:

- A reference pose is not an instruction. Acting is assigned per panel.
- State age with a build cue on the sheet, such as head height against body. A child drawn too young
  reads as a younger character on every page.
- A lasting change (aging, a new outfit) gets a second sheet beside the original, never a
  replacement.
- Count unnamed recurring figures too: the guard captain, the two sailors. If the reader must
  recognize them across pages, they get a sheet.
- One-off extras stay generic and unnamed.

## Cast gate

Before page 1, reconcile the script with the cast list. Every principal and every recurring figure
has an inspected sheet. A gap found after page 20 costs those pages.

## Photos as identity

- Derive the stylized sheet from the photo once, check the likeness at crop size, and get the user's
  approval.
- Use the approved sheet, not the raw photo, as the identity reference on pages. A photo pulls pages
  toward photographic rendering.
- Say what the reference sets: "sets face, hair and build, never pose, clothes or background".

## Places

- Keep one plan per recurring location: named walls and doors, furniture footprints, fixed
  landmarks, scale.
- Derive each camera from the plan. A reverse shot flips screen sides and the depth order of
  landmarks. It does not move people through walls.
- Write architecture, not cast, into the shared setting text.
- When prose keeps failing on geometry, use a plain diagram or a simple blockout as a reference, and
  name which parts to take from it.

## Props

- A handled prop needs grip and support views, and its length stated against the body: "blade about
  as long as his leg".
- Track removable items as single objects with states: worn, held, hung.
- A sheet for a prop or mechanism is justified only when text cannot carry the fact.

## State ledger

For every character, one line per page: costume layers, held objects, injuries, location. Write the
state into each panel prompt. Drop references that contradict it.

## Expression board

Useful for leads in a long book: neutral, courtesy, puzzlement, recognition, wonder, enthusiasm,
self-correction, alarm. Compare the faces side by side. Keep adult proportions on adult characters.

## Reference discipline

- About five references per page: the style anchor, the cast on the page, one place or prop.
- Each extra sheet can shift the style. Add one only where text cannot carry the fact, and note why.
- Give every reference a role in the prompt and number them in attachment order.
- Read the reference field's name, limit and array rule from `model_schema_get`. A bare value where
  `array: true` is silently dropped.
- Siblings: `scenario-multi-reference` for roles and leaks, `scenario-consistency` for identity and
  trained-model decisions, `scenario-identity-library` for filing a character as a collection.
