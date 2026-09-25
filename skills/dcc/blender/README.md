# Blender Expert Skills

Agent skills that make Claude (Claude Code) or Codex work in Blender 5.2 like the experts in about 200 Blender videos (Blender Studio, Blender Conference, top instructors). Start with `scenario-blender-expert/SKILL.md` (the router).

## Status

- 13 skills, distilled from about 200 expert videos (Blender Studio, Blender Conference 2019 to 2026, top instructors): `scenario-blender-expert` (router: execution channel, expert loop, review sheets `bx_review`, mesh audit `bx_audit`, live brushes `bx_gui`, Blender 5 API traps, bpy reliability) and `scenario-blender-sculpting`, `scenario-blender-retopology`, `scenario-blender-uv-baking`, `scenario-blender-texturing-shading`, `scenario-blender-hair`, `scenario-blender-rigging`, `scenario-blender-animation`, `scenario-blender-previs-storyboard`, `scenario-blender-geometry-nodes`, `scenario-blender-lighting-rendering`, `scenario-blender-grease-pencil`, `scenario-blender-hard-surface`, each with a tested `bx_<domain>.py`.
- Evidence: blind-graded written scenarios, with skills won 7 of 7 against the same model without them; execution tests better on retopology and bake + material, on par or better on sculpting after refactor, on par on a bouncing ball; all 12 test suites pass headless on Blender 5.2.1.
- Known limits: headless sculpting reaches concept quality (finished surfaces need real brushes in a live session); hair-curve and Grease Pencil draw strokes cannot be scripted; procedural retopology still needs a human pass on the finest face loops.

## Install

```bash
npx skills add scenario-labs/skills --skill scenario-blender-expert --skill scenario-blender-animation --skill scenario-blender-geometry-nodes --skill scenario-blender-grease-pencil --skill scenario-blender-hair --skill scenario-blender-hard-surface --skill scenario-blender-lighting-rendering --skill scenario-blender-previs-storyboard --skill scenario-blender-retopology --skill scenario-blender-rigging --skill scenario-blender-sculpting --skill scenario-blender-texturing-shading --skill scenario-blender-uv-baking
```

The installer puts the skills side by side, which the specialists need: they import the lead skill's `scripts/`. In the installer picker (`npx skills add scenario-labs/skills`), the family is the "Expert tools: Blender" group. Update with `npx skills update`.

## Requirements

- Blender 5.2 LTS (tested on 5.2.1). Python tools live in each skill's `scripts/` (`bx_*.py`); the router's `scripts/` (`bx_audit`, `bx_review`, `bx_gui`) are shared by the others, so keep all folders side by side.
- Headless runs: `blender --background --factory-startup --python-exit-code 1 --python script.py`. Real sculpt/paint brushes need a live Blender window (e.g. through an MCP bridge).

## Provenance

Ported from [edemaistre/blender-expert-skills](https://github.com/edemaistre/blender-expert-skills/tree/v0.1), built on 2026-09-24, with these changes: the `scenario-` prefix on every skill name, this repository's frontmatter (`name`, `description`, `license`), no version line in the skill bodies, the sibling-install line in each `SKILL.md`, and paths into the build project made relative.

Paths such as `tests/...` inside the references point to the test evidence on the build machine. They are provenance only; the skills do not need them to run.
