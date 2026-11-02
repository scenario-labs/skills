# Clock, budget and gates

A short comic is about an hour of work. It becomes three hours through sequential steps, one review
round per page, a fourth try chasing a verdict, and a wait nobody checks. The gates below keep a
short comic short. Every number is an authoring-time default, and a number the user gave wins.

## Defaults for the Quick lane

| Item        | Default                                                                |
| ----------- | ---------------------------------------------------------------------- |
| Wall clock  | About 75 minutes for 6 to 8 pages, plus about 4 minutes per page after |
| Hard stop   | 1.5 times the target, then ship what exists and list the gaps          |
| Generations | At most 4 per page across the job, style round and sheets included     |
| Style round | 3 directions (2 in clear-first mode), one image each, run at once      |
| Sheets      | All at once, one try each, one redo for a sheet that fails its gate    |
| Page tries  | The first generation plus one fresh alternative                        |
| Review      | One pass over all pages, one fix round                                 |

Album and Book lanes take the maturing-template caps in [review-and-fix.md](review-and-fix.md) and
add a gate per chapter.

## Start the clock

Write the start time in the brief card and keep a short log: gate, time, elapsed, result. Print the
elapsed time at every gate. Tell the user the expected duration with the estimate.

## Run independent work at once

- The style directions run together.
- All character sheets run together.
- Every page that does not wait on a representative page runs together, up to the team's concurrency
  limit. Never review page 1 while pages 2 to 8 wait to be submitted.
- The reviewers of one pass run together, one per page, plus one cold reader for the sequence.
- Check a delegated agent or a background step that has been silent for about ten minutes before
  waiting longer. A crashed one looks the same as a slow one.

## Gates

Each gate has a pass condition, a time box and a fallback. A gate that fails takes its fallback
once, then the run moves on and logs the gap.

| Gate     | Elapsed | Passes when                                                     | If it fails                                       |
| -------- | ------- | --------------------------------------------------------------- | ------------------------------------------------- |
| Brief    | 10 min  | Brief card holds mode, reader, takeaways, lane, pages, estimate | Take the defaults and log them                    |
| Script   | 20 min  | Script check and the cover-the-art test pass                    | One rewrite, then go on                           |
| Style    | 30 min  | One direction chosen, anchor page lettering readable at 100%    | Rewrite the direction once, keep the stronger     |
| Cast     | 45 min  | Sheets exist, faces differ, costumes read at thumbnail size     | Keep the better sheet and log it                  |
| Pages    | 65 min  | Every page generated once, all in parallel                      | Submit the late pages now, review the rest        |
| Review   | 75 min  | One pass done: defects, cold read, flagged pages listed         | Skip the taste detail, keep defects and cold read |
| Fix      | 90 min  | One round done, flagged pages kept or reverted                  | Ship the strongest with a residual list           |
| Delivery | 95 min  | PDF opens, pages read in order, paths reported                  | Never skipped                                     |

Elapsed times fit 6 to 8 pages.

## When a gate runs late

A gate more than a third over its box triggers the cuts, in this order:

1. The stock twin and per-page taste rounds.
2. The alternative try for pages that already read well.
3. Cover, dedication and other extras.
4. The fix round, narrowed to pages the cold read could not follow or that show a wrong character.

Never cut the lettering proofread, the cold read or the reading of the finished PDF.

## Why each cap exists

- A style round of five directions on two pages is ten images and one long wait. Three images on one
  page tell the same story.
- A review round per page in sequence is one round per page of waiting. One pass in parallel gives
  the same findings.
- A fourth try rarely beats the second. When the second fails the same way, the clause is wrong:
  rewrite it ([page-production.md](page-production.md)) instead of drawing again.
- A verdict chase has no end. The cap exits in [review-and-fix.md](review-and-fix.md) end it.

## Close the log

The final report lists each gate with its elapsed time, the deliverable paths and the known gaps.
