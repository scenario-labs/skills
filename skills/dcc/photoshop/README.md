# Photoshop Expert Skills

Agent skills that let Claude (Claude Code) or Codex drive Adobe Photoshop the way the experts in the
best recent tutorials do, with Scenario models for the generative steps. Built on 2026-10-19 with
the same method as [Blender Expert Skills](../blender/README.md): transcripts of top-rated videos,
cited expert notes, then skills with toolkits, review rubrics and live test suites. Start with the
lead skill, `scenario-photoshop-expert`.

## Skills

| Skill                                | Use it when                                                                                                                                              |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario-photoshop-compositing`     | placing a person, product or generated element into a new scene in Photoshop, or when a composite looks pasted on: hard, white or dark fringed cutout... |
| `scenario-photoshop-expert`          | an agent drives Adobe Photoshop on macOS for any task: running ExtendScript or Action Manager code in a live Photoshop 2026 (27.x), sending a...         |
| `scenario-photoshop-game-art`        | making or finishing game art in Photoshop with Scenario: a seamless or tileable texture that shows a seam, a grid or repeating blotches when tiled, a... |
| `scenario-photoshop-generative-edit` | changing only part of an image open in Photoshop with a Scenario model: inpainting or replacing an object inside a selection, removing a person...       |
| `scenario-photoshop-key-art`         | building key art, ads, YouTube thumbnails, Steam store capsules, social posts, posters or campaign files in Adobe Photoshop around a Scenario image...   |
| `scenario-photoshop-mockups`         | putting a design, logo, label, pattern or Scenario result onto a product photo in Photoshop: a print, packaging or merchandise mockup on a tote...       |
| `scenario-photoshop-upscale-restore` | enlarging or repairing an image open in Photoshop with a Scenario model: upscaling a small photo, crop, scan or generated image for print or a larger... |

## Status

- 7 skills written from 208 transcribed videos (80.8% from 2025 to 2026) and Adobe documentation,
  each with cited references and a Python toolkit.
- Every toolkit has a live suite run against Photoshop 27.11 on macOS: 98 tests across 12 suites,
  several on real Scenario outputs (inpaint, upscale, restore, seamless texture repair), one that
  fills History to its limit. All passed on 2026-10-19. Last run of each suite, Paris time: mockup
  13:41, History 13:42, upscale 13:44 and restore 13:45, after the last toolkit change; composite
  12:17, generative-edit 12:21, io 10:49, audit 10:42, retouch and game-art tiling 09:25, gates
  06:39, key-art 06:36 and game-art export 06:35, each after the last change to the code it runs
  (since then, the io and gates toolkits changed in docstrings only, and the composite, mockup and
  upscale changes add no DOM constant to the io suite's enum sweep). Steps no script reaches are
  listed as GUI paths and marked not tested.
- Blind grading on seven briefs, one per skill: the same model answered with the skills and from
  memory alone, and a separate grader scored the shuffled pairs without knowing which was which. On
  the final skills: 103 of 105 with the skills (four briefs won, three ties), 95 without. The gain
  is mostly Photoshop traps and runnable code, with no wrong claim against one. A first run on the
  draft gave 102 against 91 from the same memory-only answers, so a few points are grader variance.
  Seven briefs and one grader are a small sample.

## Requirements

Adobe Photoshop 2026 (27.x) on macOS, Python 3 with Pillow, and the Scenario MCP server for the
generative steps. Placing a vector logo in a mockup needs an SVG renderer, such as librsvg's
`rsvg-convert`. The lead skill explains the execution channel: ExtendScript jobs sent through
AppleScript `do javascript`, each wrapped in one named History state, with Photoshop left in the
background.

## Install

```bash
npx skills add scenario-labs/skills --skill scenario-photoshop-expert scenario-photoshop-compositing scenario-photoshop-game-art scenario-photoshop-generative-edit scenario-photoshop-key-art scenario-photoshop-mockups scenario-photoshop-upscale-restore
```

The installer puts the skills side by side, which the specialists need: they import the lead skill's
`scripts/`. In the installer picker (`npx skills add scenario-labs/skills`), the family is the
"Expert tools: Photoshop" group. Update with `npx skills update`.

## Provenance

- **Research:** 208 videos with transcripts and frame sheets, analyzed into cited notes by theme,
  plus Adobe's Photoshop and UXP documentation. Use cases were ranked by how often experts do them,
  how painful they are, and where Scenario adds something Photoshop's built-in generative features
  do not. A specialist exists only where at least 10 notes back it, so retouching folded into
  compositing.
- **Split by Scenario use case:** the specialists follow the steps where a Scenario model does the
  work (local edits, upscale and restore, compositing, key art, mockups, game art), not Photoshop's
  domains as the other expert families do. Batch runs and the user's Actions stay in the lead: the
  sources teach them too thinly for a specialist, unlike the five families with an automation or
  pipeline specialist (Blender has none).
- **One skeleton for the family:** the lead uses the specialists' sections (Stance, Establish first,
  Workflow, Numbers, gates) rather than the numbered sections of the Maya, Blender and ZBrush leads,
  so every skill in the family reads the same way.
- **Toolkits first:** each specialist's script was written and run live before its skill body, so
  the skill teaches calls that work on 27.11. Traps found that way (a layer mask ignored by Load
  Transparency, histograms on hidden channels, warp quirks) are in the lead's
  `references/photoshop-2026-traps.md`.
- **Reviews:** fresh reviewer agents (skeptic, QA, consistency, product) score each phase on a
  rubric; a phase passes when no blocking issue remains and every criterion scores 4 of 5 or more.
