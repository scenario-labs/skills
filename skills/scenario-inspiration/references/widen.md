# Prime, then widen

## Prime: four lines before any search

Chance favors a prepared mind, and an unprimed search returns whatever the brief's own words already contain. Write these down first, in the conversation, so later finds have something to bind to.

1. **Locked**: the constraints that cannot move (ratio, engine budget, existing characters, legibility floor).
2. **Open**: the one axis actually up for decision. Name it. Everything downstream varies along it.
3. **Hit**: what a good find looks like, in a sentence that could be checked. "Regions read apart in grayscale" is checkable; "feels premium" is not.
4. **Both reflexes**: the obvious answer for this brief, and the answer of someone who is merely avoiding the obvious answer. Rule out both. An agent told to be original converges on the second-obvious answer, so it has to be named to be dodged.

Then run the literal, obvious query once and keep the result. That baseline is not a candidate set; it is the control. Anything the widening produces has to include things the baseline did not, or the widening did nothing and you should say so instead of claiming variety.

## Four words that are not synonyms

| Word           | Means                                                     |
| -------------- | --------------------------------------------------------- |
| Novelty        | The item is unknown to this user or this team             |
| Diversity      | The items in the set are unlike each other                |
| Unexpectedness | The item is unlike what the obvious approach would return |
| Serendipity    | Unexpected and relevant, at the same time                 |

Asking for diversity when you mean unexpectedness gets you a well-spread set of obvious things. Aim for maximum distance from the reference subject to a hard relevance floor, not a free blend of the two.

## Operators, not adjectives

"Explore broadly" produces variations. These are moves with an input and an output.

Randomize the operator, never the subject. The subject stays exactly what the brief asked for; what varies is the transformation applied to it. A random subject is noise, and it is the reason agent "creativity" usually reads as irrelevance.

| Operator             | The move                                                                                                                                                    |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Constraint inversion | Write the brief's 3 to 6 unstated rules ("lighting is naturalistic", "the camera is at eye level"), then drop or negate exactly one per variant             |
| Constraint injection | Add an arbitrary obligatory element the brief never asked for; a required constraint reliably raises rated creativity over a free hand                      |
| Bisociation          | Collide the subject with a second frame that is internally rule-rich and rarely co-occurs. If the connection is immediately visible, the frame is too close |
| Blend                | List A's elements, list B's, name the structure they share, project a chosen subset of each, then run the blend to see what it implies                      |
| Purpose over surface | State the brief's function ("move heavy things up a shaft safely"), hold it fixed, and find domains that solve it by a different mechanism                  |
| Nth association      | Ban the top three obvious associates by name before generating, which forces the flat end of the associative hierarchy instead of the strongest link        |
| Cross-brief          | Retrieve assets that score well against two distinct earlier briefs in this session at once                                                                 |

The test that separates a real analogy from a decorative one: do the mechanisms map, or only the labels? Cross-brief is the one operator that cannot return something irrelevant, because every candidate is already relevant to something the user asked for.

## The dial: three stops, not a slider

| Stop      | When                      | Settings                                                                          |
| --------- | ------------------------- | --------------------------------------------------------------------------------- |
| **Tight** | Executing a decided brief | One query, no wildcards, keep the closest hits                                    |
| **Open**  | Default                   | Two or three queries on different axes, one wildcard card, both semantic settings |
| **Wide**  | Nothing decided yet       | Four or more queries, four wildcard cards, a wander chain, far rung included      |

Pure randomness earns about one slot in twenty, and it belongs in its own labeled lane rather than mixed into the main results. An unexpected item that turns out to be irrelevant costs more satisfaction than it buys.

## The distance ladder

Sample near, middle, and far, then let evaluation pick. Do not commit to "as far as possible": the evidence is split, with lab studies finding far-field examples raise novelty and a large field study finding conceptually closer sources more useful. The reconciliation that fits both is that structural analogy helps and arbitrary unrelatedness does not, so measure distance in mechanism, not in surface topic.

Far sampling raises variance rather than the average: more hits and more misses. Generate more candidates on the far rung and expect to discard most of them.

## Query craft

- **Two or three queries on different axes**, never one. One query returns near-duplicates of a single template. Vary subject, treatment, and graphic language across the set.
- **Search the feeling, not the category.** Querying the category name returns the category reflex delivered to your desk.
- **Check the anchor noun is not half a fixed compound.** "Light bulb", "hard surface", and "brass instrument" hijack a query toward the compound.
- **Anchor an abstract treatment with a concrete noun**, or the results turn into stock abstraction.
- **Never search a brand you intend to resemble.** You will get a knockoff of it and so will the output.

## The Scenario search dials

`search` is free, so run several. The dials that change what comes back:

| Dial                     | Behavior                                                                                                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `query_semantic_ratio`   | 0 (default) is keyword and matches an asset's stored caption text, so a concept word can return nothing while an image of exactly that thing sits in the project. 0.8 searches meaning. Run both |
| `public`                 | Omitted or false searches the team's own assets; `true` searches the public catalog                                                                                                              |
| `images: {like, unlike}` | Steer by example in both directions. Seeds may reappear in their own results                                                                                                                     |
| `filters`                | `kind`, `tags`, `created_after`, `collection_ids`, `model_id`, `privacy`                                                                                                                         |
| `sort_by`                | Ignored while semantic search is active                                                                                                                                                          |
| `target: "models"`       | Keyword beats semantic for named styles. Each hit carries `shortDescription`, `tags`, and `exampleAssetIds`                                                                                      |

Run the same brief at both ends of `query_semantic_ratio` and look at what only one of them found. The keyword pass surfaces literal but odd matches, the semantic pass surfaces conceptual ones, and the difference between the two lists is where the surprises are. Running one setting and calling it a search is the most common way to miss them.

Keep `unlike` short. Negative examples deserve much less weight than positives, and a query stacked with them stops pointing at a chosen region of the space and starts pointing at an arbitrary one, which is the mechanical cause of results that are random but irrelevant.

Two payloads make public search worth more than a normal image search. Public asset hits carry `metadata.prompt`, the exact wording that produced them, which is style research you can read rather than guess at. Public model hits carry `exampleAssetIds`, a ready-made board for that look: `asset_display` a handful before deciding anything.

`estimatedTotalHits` is not a result count. It comes back large next to an empty `assets` array, so never report it as "found N".

## The wander chain

A deterministic walk that reaches places no direct query does, using nothing but similarity search:

1. `search` your best query, take the top hit.
2. `search` again with `images: {like: [that hit]}` and take the fifth or so result, not the first.
3. Repeat three or four times.

Each hop is small, the accumulation is not, and every step lands on a real asset rather than an invented idea. It is fully reproducible, so a chain that found something good can be written down and re-run.

## Wildcard draws

[../scripts/wildcard.py](../scripts/wildcard.py) draws far-domain cards from a curated corpus with a real RNG, spread so no two cards in a draw share a facet value or a domain cluster.

```bash
python3 scripts/wildcard.py --count 4                 # four cards, fresh seed, printed
python3 scripts/wildcard.py --count 4 --seed 20260816 # replay an earlier draw
python3 scripts/wildcard.py --count 6 --facets domain,strategy --json
python3 scripts/wildcard.py --list # facets, pool sizes, clusters
```

A card is a lens over the fixed subject, not a replacement for it: a card reading "shipbreaking beaches" applied to a potion icon asks what a potion icon looks like when it borrows that world's scale, corrosion, and labor, not for a picture of a shipyard. Run the domain as its own `search`, apply the strategy and constraint to what comes back, and discard the cards that go nowhere; that is expected, not failure.

Name the card you drew alongside the result it produced, so the user can pin it or ask for a re-draw. The printed seed matters twice: it replays a draw that worked, and it is the record of what a session was given, so two sessions with the same brief can be checked for having received different starting points.

## What goes wrong, and the counter

- **The first reference anchors everything.** Shown one example, people reproduce its features even when told its flaws. Counting ideas will not detect this; compare features against the seed instead. For depth, seed with exactly one uncommon reference up front. For breadth, withhold references until after a first blind pass, or supply several from distinct categories.
- **The first three ideas are warmup.** Serial position is real. Generate past them before presenting anything.
- **Every user converges.** Assistance that raises one person's novelty also makes everyone's output more similar to everyone else's. Vary the wildcard seed per session and the operators per round so two people with the same brief do not receive the same four directions.
- **Round two restates round one.** Keep a running list of what this session already proposed and reject a candidate that sits too close to it. Novelty measured against an archive beats novelty asserted.
- **Strangeness is not serendipity.** An unexpected find qualifies only when all three hold: it was unexpected, you can articulate the connection to the task, and you can state its concrete value. Two out of three is noise. Park the near misses in a short list the user can return to instead of arguing for them.

## Audit the set before presenting it

Score the candidate set on four axes: fluency (how many distinct ideas), flexibility (how many distinct categories they span), originality (how rare each is), elaboration (detail per idea). The failure signature is high fluency with low flexibility: ten ideas, one category. The fix is a category coverage requirement, not "generate more".

Then two checks you can actually run. Does the set contain anything the baseline query did not return? And is each item far from its nearest reference, rather than the set being far on average? A set can look spread out while hiding a cluster of near-duplicates, and the nearest one is what gives that away.
