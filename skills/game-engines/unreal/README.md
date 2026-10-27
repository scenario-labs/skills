# Unreal Engine Expert Skills

Agent skills that let Claude (Claude Code) or Codex drive Unreal Engine 5.8 the way the experts in
the best tutorials, conference talks and official documentation do. Built on 2026-09-24 and updated
on 2026-10-22 with the same method as [Blender Expert Skills](../../dcc/blender/README.md),
[Maya Expert Skills](../../dcc/maya/README.md) and
[ZBrush Expert Skills](../../dcc/zbrush/README.md): transcripts of top-rated videos, cited expert
notes, then skills with tools and review rubrics, graded blind against the same model without them.
Start with the lead skill, `scenario-unreal-expert`.

## Skills

| Skill                                 | Use it when                                                                                                                                              |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario-unreal-expert`              | an agent drives Unreal Engine 5.8 on a Mac for any task: editing a project through Epic's Unreal MCP toolsets (list_toolsets, describe_toolset...        |
| `scenario-unreal-animation`           | a UE5 task involves characters in motion: "import FBX from Maya" with a skeleton, "retarget animations", IK Rig, IK Retargeter, batch retarget, feet...  |
| `scenario-unreal-cinematics`          | making a trailer, cutscene, cinematic or short film in Unreal Engine 5.8 with Sequencer: shot lists, master and shot sequences, cameras, lenses...       |
| `scenario-unreal-gameplay`            | building or debugging UE5 gameplay: a character with double jump or dash, abilities with cooldowns, enemy AI that patrols, chases and attacks, a...      |
| `scenario-unreal-lighting-rendering`  | lighting or rendering in Unreal Engine 5.8: physical light units and exposure (EV100, lux, lumens), a sun, sunset or dusk rig, Lumen GI and...           |
| `scenario-unreal-materials`           | a UE5 task involves materials or textures: a master material and instances for a kit, Substrate or legacy, Blendable vs Adaptive GBuffer, glass...       |
| `scenario-unreal-performance`         | an Unreal Engine 5.8 project misses its frame rate or stutters: "optimize to 60 fps", "we run at 38 fps", CPU or GPU bound, game or render thread too... |
| `scenario-unreal-pipeline-automation` | importing FBX, USD, OBJ or glTF from Maya, ZBrush, Blender or an AI generator (Scenario MCP, the Scenario for Unreal plugin) into Unreal Engine 5.8...   |
| `scenario-unreal-vfx`                 | a UE5 task involves Niagara or Chaos destruction: a Niagara fireball, projectile trail, impact explosion, muzzle flash, spell, smoke, sparks, debris...  |
| `scenario-unreal-world-building`      | building or fixing an Unreal Engine 5 level or open world: World Partition, OFPA, Data Layers, Level Instances, Packed Level Actors, HLOD, landscape...  |

## Status

- 10 skills (the lead `scenario-unreal-expert` and 9 specialists) written from 115 expert videos (77
  h) and 82 official documentation pages, each with references and a `ue_<domain>.py` module. The
  lead carries the shared toolkit (`ue_env`, `ue_run`, `ue_remote`, `ue_review`, `ue_audit`,
  `ue_stat`, `ue_mcp`).
- Version 0.2.1 (2026-10-22) was run in Unreal Engine 5.8.3 on macOS, Apple Silicon. The lead
  skill's live runs covered the MCP catalog (52 toolsets, 830 tools), Python Remote Execution, the
  project-local Python toolset, headless and offscreen editor launches, screenshots, Remote Control
  and the job protocol. Each specialist's SKILL.md has a Status line naming what ran and what did
  not, and the procedures mark every block that has not been run in the engine as `[not yet run]`.
- Blind-graded written scenarios on version 0.1 (round 1): 51 % without the skills, 95 % with them
  (69/135 vs 128/135); all 9 scenarios improved. One grader per scenario: a direction, not a
  statistic. These scores were measured on version 0.1, before the live runs.
- Review round (2026-10-27): each claim a 5.8.4 source review disputed was checked against Epic's
  public 5.8 Python and C++ references, Epic's documentation and the Scenario for Unreal plugin's
  public guide. Where none of them settles a claim, the skill now has the agent read the value or
  feature-detect the call instead of asserting either version. Python Remote Execution's bind
  address now follows the OS: `0.0.0.0` on macOS and Linux (socket tests on both), Epic's
  `127.0.0.1` on Windows (not run there). On `0.0.0.0` any host on the local network can run code in
  the editor (shown with a second host), and the skills say so.
- The offline checks that came with the skills run in the build project, not in this repository:
  they use system Python and fake `unreal` modules. Treat any in-engine code path marked
  `[not yet run]` as unverified until a first live run.

## Requirements

Unreal Engine 5.8 on macOS Apple Silicon. The lead skill `scenario-unreal-expert` explains the
execution channels: Epic's experimental Unreal MCP server, Editor Python in a running editor (Python
Remote Execution), headless `UnrealEditor-Cmd -run=pythonscript` jobs, the Remote Control API,
console commands, commandlets and UAT. The offline layers of the modules run with system Python 3.

## Install

```bash
npx skills add scenario-labs/skills --skill scenario-unreal-expert scenario-unreal-animation scenario-unreal-cinematics scenario-unreal-gameplay scenario-unreal-lighting-rendering scenario-unreal-materials scenario-unreal-performance scenario-unreal-pipeline-automation scenario-unreal-vfx scenario-unreal-world-building
```

The installer puts the skills side by side, which the specialists need: they import the lead skill's
`scripts/`. In the installer picker (`npx skills add scenario-labs/skills`), the family is the
"Expert tools: Unreal Engine" group. Update with `npx skills update`.

## Provenance

Ported from [edemaistre/unreal-expert-skills](https://github.com/edemaistre/unreal-expert-skills),
version 0.2.1 (2026-10-22), built from the 2026-09-24 skills, with these changes: the `scenario-`
prefix on every skill name and on every reference to a sibling skill, this repository's frontmatter
(`name`, `description`, `license`), no version line in the skill bodies, the sibling-install line in
each `SKILL.md`, links from each `SKILL.md` to its supporting files, American spelling, unused
imports and variables removed from the scripts (ruff, pyflakes rules), machine model and author name
neutralized, and paths into the build project made relative.

Mentions of v0.1, v0.2, v1 or v2 inside the references and code comments are revision history of the
build project: the internal drafts of 2026-09-24, then the update of 2026-10-21.

Paths such as `tests/code/...`, `tests/arena/...`, `notes/...`, `sources/...` inside the skills
point to the build project (tests, notes, sources) on the author's machine; they are provenance
only.
