# Review and fix

## Who reviews

A strong vision model reads every page with the page prompt, the script and the cast sheets in
context. It writes findings, crops included. The user reads the top two tiers and adds one sentence
where needed. A score proves nothing: crop and compare against the sheet.

## Three tiers

| Tier         | Examples                                                                                         | Who acts                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| Obvious      | Wrong or missing character, extra limbs, broken lettering, a stock verdict from the taste review | Redraw at once                                                                  |
| Worth a look | State drift (a ring, a coat), geography, a doubtful pose                                         | The user decides (unattended: redraw within budget, then keep the best and log) |
| Small detail | A button, a finger count in a small panel, a prop proportion                                     | Batched into a fix round                                                        |

On one 900-page project, 482 pages were reviewed this way: 11 obvious defects, 94 worth a look, 297
small details. The tiers kept the human on the findings that mattered.

## Review order

1. Story: does the page deliver its beat and every "must be visible" item? Then the taste review in
   [art-direction.md](art-direction.md): the stock twin and the seven questions.
2. Identity, anatomy, costume and prop construction against the sheets.
3. State and geography across the previous, current and next page.
4. Lettering: every word once, in order, right speaker, tails pointing at the speaker, accents
   intact.
5. Native fidelity: crop faces, hands, thin lines and lettering at 100%.
6. The assembled sequence, read in order at reading size.

Record each finding with page, panel, the source requirement, the exact asset ID and what is
observed. Mark each check pass, fail or not observable. A hidden or cropped detail is not
observable, not automatically right.

## Mechanism checks

- **Hands**: trace shoulder, elbow, wrist, palm or back, thumb, four fingers. No doubled hands,
  reversed thumbs, hand and face fusion.
- **Grip and weight**: the object is held, not floating, and the load looks real.
- **Joints**: neck, hips, knees, ankles, wing roots. Prefer a readable action phase over an
  acrobatic one.
- **Group staging**: each moving figure has its own stride and gaze. Cloned poses read as marching.
- **Gaze**: name the target. Check pupils, chin, shoulders and seat direction together.
- **Props**: one connected shape, correct length, correct hand, correct side. A held object keeps
  its length when stored.
- **Costume layers**: hems, collars, clasps, beard against hair. Damage starts at its story event.
- **Geography**: doors keep a fixed opening and a swinging leaf. Feet stay outside until the
  crossing.
- **Counts**: candles on a cake, buttons, people in a crowd and fingers drift between panels. Check
  by counting. State the count in each panel, or show it in one panel only.
- **Scale**: a pet, a prop or a child against an adult keeps one size relation across panels.
- **Time and light**: the TIME line is visible in every panel it covers, and the sky outside a
  window matches it.
- **Lettering**: no clipping, no collisions, no new words.

## Redraw only flagged pages

1. Read the page's lineage: exact prompt, exact references, job, asset ID.
2. Replace the clause that caused the defect. Keep the printed words identical.
3. Keep the same references. Add one only where text cannot carry the fact, and say why.
4. Make one fresh generation from the originals. Never edit a rendered page, and never edit an edit.
   Run `jobs_wait` on its job (re-call with `pending_job_ids` while it is `in_progress`) before the
   comparison, so the new asset is the one you compare.
5. Compare old and new at reading scale and at native scale. Keep the new page if the fix landed and
   nothing regressed. A partial fix with no regression is kept, and the residual is recorded. A fix
   that regressed something leaves the old page in place.

Editing an edit melts faces and costumes. Rendered pages are evidence, not references.

## Attempt caps

- Budget per page while the template matures: up to four fresh generations. Once pages pass on the
  first try, the first generation plus one fresh alternative.
- Later rounds contain only pages with a confirmed defect, each with a changed remedy.
- A cap stops paid retries, not diagnosis. Report what is unresolved and what the next attempt
  should change.
- Keep the stronger earlier candidate. No hidden rollback and no budget reset when a label changes.

## Fix rounds

When the user flags pages:

1. Scope the round once: the pages, the finding for each, an attempt budget.
2. Rebuild each page from its exact displayed prompt with only the guilty clauses replaced. Print
   the prompt diff and read it before submitting.
3. Report as a table: page, result ("fixed", "new problem", "not fixed"), one recommendation.
4. Track rounds: pages in, fixed and kept, flagged again.

On the same 900-page project, 314 pages were redrawn. Tries per final page fell from about 3.9 in
the early chapters to 0.6 in the last, as the template, the sheets and the rules improved. One
47-page fix round ended with all 47 fixed and kept.

## Siblings

- `scenario-refine-loop`: when to re-prompt, swap references, inpaint or change model.
- `scenario-quality-gate`: a stored verdict against a brand brief.
- `scenario-asset-analysis`: captions and verdicts per asset.
