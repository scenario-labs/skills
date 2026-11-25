# After Effects Expert Skills

Agent skills that let Claude (Claude Code) or Codex drive Adobe After Effects 27.0 and 2026 the way
the experts in the best tutorials, studio talks and official documentation do. Built on 2026-11-24
and 2026-11-25 with the same method as [Maya Expert Skills](../maya/README.md): transcripts and key
frames of expert videos, cited notes, then skills with tools and review rubrics, graded blind
against the same model without them. Start with the lead skill, `scenario-after-effects-expert`.

## Skills

| Skill                                      | Use it when                                                                                                                                              |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario-after-effects-expert`            | an agent must connect to, inspect, change or render from Adobe After Effects (27.0, 2026) by script, or route a request that spans crafts. Triggers...   |
| `scenario-after-effects-3d`                | building 3D in After Effects: importing a GLB or FBX model, fitting it, product orbits, HDRI environment light, shadow catcher, floor and reflection...  |
| `scenario-after-effects-animation`         | keyframing in After Effects: slide-ins, pops, product and UI moves, overshoot, bounce, anticipation, overlap, stagger, parenting to nulls, motion...     |
| `scenario-after-effects-character-rigging` | rigging or animating a 2D cut-out character in After Effects: layered art, anchor points, parenting, IK, controllers, walk cycles that loop or stop...   |
| `scenario-after-effects-color-delivery`    | finishing or delivering from After Effects: color management, OCIO or ACES, log footage, LUTs, grade order, bit depth, banding, grain, safe zones...     |
| `scenario-after-effects-compositing`       | keying a green or blue screen, cleaning a matte, roto or Object Matte, a cutout with no screen, removing a logo, wire or object, a clean plate, track... |
| `scenario-after-effects-expressions`       | writing, fixing or speeding up After Effects expressions or rigs: a box that fits its text, delay from one controller, a loop that jumps, inertial...    |
| `scenario-after-effects-generation`        | an After Effects project needs generated media from the Scenario MCP: style frames, transparent cutouts, parallax planes, depth maps, video plates...    |
| `scenario-after-effects-motion-production` | an After Effects job is a commercial piece with a brief: a game UA ad, social cut, trailer, promo, store preview or end card. Triggers: variants for...  |
| `scenario-after-effects-project`           | an After Effects project must be set up, inherited, cleaned or handed over: comps named Comp 1, missing footage, fonts or effects, mixed frame rates...  |
| `scenario-after-effects-scripting`         | an After Effects task needs a script or a pipeline: versions from a CSV, JSON or sheet, localized end cards in many ratios, a comp built from a data...  |
| `scenario-after-effects-shape-layers`      | building or fixing shape layers in After Effects: line icons, logo reveals from Illustrator or SVG, Trim Paths draw-ons, Repeater bursts, ripples and... |
| `scenario-after-effects-tracking`          | footage in After Effects must be tracked, stabilized or matchmoved: the track slips or drifts, the insert swims, replace a screen, corner pin a sign...  |
| `scenario-after-effects-typography`        | animating text in After Effects: kinetic type, captions or lyrics synced to a voiceover, text animators and range or expression selectors, per-letter... |
| `scenario-after-effects-vfx`               | building effects in After Effects with built-in tools: glow, sparks, bursts, embers, dust, smoke, flame, shockwave rings, light rays, lightning, heat... |

## Status

- 15 skills written from 206 expert videos and 100 documentation pages and articles, each listed in
  the skill's `references/sources.md`. Each skill has references, a review rubric, and scripts.
- Each code block names its channel and how it was checked on a header line.
  - `checked: live 27.0`: run in After Effects 27.0 on macOS through the mailbox bridge.
  - `checked: doc`: taken from the documentation, with the source named.
- Offline checks (`tests/scenario-after-effects-expert/`) need no After Effects:
  - every shipped Python script imports with system Python;
  - the host-side helpers run against planted inputs: runner, mailbox job files, offline
    ExtendScript checker, ffprobe summary, delivery, timing, beat, layout, seat and effects
    measuring tools;
  - each effects builder returns what its comment documents.

## Requirements

After Effects 27.0 or 2026 (26.x) on macOS or Windows, with Settings > Scripting & Expressions >
"Allow Scripts to Write Files and Access Network" on. Python 3 for the runner, ffmpeg and ffprobe
for contact sheets and file checks. The lead skill `scenario-after-effects-expert` explains the
execution channels: a mailbox bridge script that After Effects loads at startup (the default),
`osascript` on macOS, `AfterFX.exe -r` on Windows, `aerender` for saved projects, or a handoff
script the user runs.

## Install

```bash
npx skills add scenario-labs/skills --skill scenario-after-effects-expert scenario-after-effects-3d scenario-after-effects-animation scenario-after-effects-character-rigging scenario-after-effects-color-delivery scenario-after-effects-compositing scenario-after-effects-expressions scenario-after-effects-generation scenario-after-effects-motion-production scenario-after-effects-project scenario-after-effects-scripting scenario-after-effects-shape-layers scenario-after-effects-tracking scenario-after-effects-typography scenario-after-effects-vfx
```

The installer puts the skills side by side, which the specialists need: they load the lead skill's
`scripts/` (runner, bridge, `aekit/` helpers). In the installer picker
(`npx skills add scenario-labs/skills`), the family is the "Expert tools: After Effects" group.
Update with `npx skills update`.

## Provenance

Written for this repository: the names, frontmatter (`name`, `description`, `license`) and
sibling-install line follow its conventions. The scripts in each `scripts/` folder are ExtendScript
(ES3) as After Effects runs it, so prettier skips them and the markdown code blocks keep their
formatting.

Experts and vendors whose public videos or articles are cited are named in each `sources.md`. No
generative platform other than Scenario is named. Video sources carry their YouTube id and
timestamps, so each claim can be checked against the video. Sources cited as saved documentation
file names (`scripting-automation__...`) point to the build project on the author's machine; they
are provenance only.
