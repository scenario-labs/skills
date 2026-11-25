# After Effects Expert Skills

Agent skills that let Claude (Claude Code) or Codex drive Adobe After Effects 27.0 and 2026 the way
the experts in the best tutorials, studio talks and official documentation do. Built on 2026-11-24
and 2026-11-25 with the same method as [Maya Expert Skills](../maya/README.md): transcripts and key
frames of expert videos, cited notes, then skills with tools and review rubrics, graded blind
against the same model without them. Start with the lead skill, `scenario-after-effects-expert`.

## Skills

| Skill                                      | Use it when                                                                       |
| ------------------------------------------ | --------------------------------------------------------------------------------- |
| `scenario-after-effects-expert`            | connecting to After Effects, running a job in the open project, routing a request |
| `scenario-after-effects-3d`                | models, cameras, environment lights, shadows, extruded text, 2.5D parallax        |
| `scenario-after-effects-animation`         | keyframes, easing, overshoot, overlap, arcs, motion blur, retiming                |
| `scenario-after-effects-character-rigging` | 2D cut-out characters: joints, IK, walk cycles, Puppet pins, lip sync             |
| `scenario-after-effects-color-delivery`    | color management, banding, render settings, transparent exports, platform specs   |
| `scenario-after-effects-compositing`       | keying, mattes, roto, cleanup, light wrap, grain match                            |
| `scenario-after-effects-expressions`       | expressions and expression rigs: controllers, loops, delays, counters             |
| `scenario-after-effects-generation`        | generated images, video, 3D, voice and music from the Scenario MCP, landed in AE  |
| `scenario-after-effects-motion-production` | ads and commercial pieces: hooks, pacing to music, end cards, variants            |
| `scenario-after-effects-project`           | setting up, cleaning or handing over a project: naming, footage, fonts, precomps  |
| `scenario-after-effects-scripting`         | versions from a spreadsheet, batch renders, templates, ExtendScript tools         |
| `scenario-after-effects-shape-layers`      | icons, Trim Paths, Repeater, path morphs, SVG intake, Lottie                      |
| `scenario-after-effects-tracking`          | point and planar tracks, screen replacement, stabilizing, camera solves           |
| `scenario-after-effects-typography`        | kinetic type, text animators, captions synced to audio, text that must fit        |
| `scenario-after-effects-vfx`               | glow, sparks, shockwaves, light rays, lightning, smoke and flame, built-in only   |

## Status

- 15 skills written from 209 expert videos and 88 documentation pages and articles, each with
  references, a review rubric, and scripts.
- Each code block names its channel and how it was checked on a header line.
  - `checked: live 27.0`: run in After Effects 27.0 on macOS through the mailbox bridge.
  - `checked: doc` or `checked: note`: taken from the documentation or an expert video, with the
    source named.
- Offline checks (`tests/scenario-after-effects-expert/`): every shipped Python script imports with
  system Python, and the host-side helpers (runner, mailbox job files, offline ExtendScript checker,
  ffprobe summary, delivery and timing tools) run against planted inputs with no After Effects
  installed.
- Blind-graded written plans (15 briefs, one grader each): 50 % without the skills, 90 % with them.

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
