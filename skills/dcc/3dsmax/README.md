# 3ds Max Expert Skills

Agent skills that let Claude (Claude Code) or Codex drive Autodesk 3ds Max 2027 the way the experts
in the best tutorials, studio talks and official documentation do. Built on 2026-11-24 with the same
method as [Maya Expert Skills](../maya/README.md): transcripts and key frames of expert videos,
cited notes, then skills with tools and review rubrics, graded blind against the same model without
them. Start with the lead skill, `scenario-3dsmax-expert`.

## Skills

| Skill                                | Use it when                                                                               |
| ------------------------------------ | ----------------------------------------------------------------------------------------- |
| `scenario-3dsmax-expert`             | driving 3ds Max through pymxs, MAXScript, Autodesk's MCP server, a bridge, or 3dsmaxbatch |
| `scenario-3dsmax-animation-rigging`  | keys, curves, camera paths, constraints, CAT, Biped, Skin, FBX clips for engines          |
| `scenario-3dsmax-archviz`            | an architect's model must become delivered stills or animation                            |
| `scenario-3dsmax-fx`                 | tyFlow, PhysX, cloth, scatter, caches, simulation budgets                                 |
| `scenario-3dsmax-game-assets`        | a model must become a game engine asset: low poly, normals, LODs, collision, FBX          |
| `scenario-3dsmax-generation`         | generated assets from Scenario must land in a scene, or a scene must feed a generator     |
| `scenario-3dsmax-lighting-rendering` | lighting or rendering with Arnold, V-Ray 7, or Corona                                     |
| `scenario-3dsmax-materials`          | building, fixing, or judging materials and texture sets                                   |
| `scenario-3dsmax-modeling`           | Editable Poly, the modifier stack, Booleans, chamfers, subdivision, splines               |
| `scenario-3dsmax-scene`              | units and scale, imports and merges, layers, naming, XRefs, CAD cleanup                   |
| `scenario-3dsmax-scripting`          | writing, fixing, or shipping pymxs and MAXScript tools                                    |
| `scenario-3dsmax-uv-baking`          | unwrapping, packing, texel density, lightmap channels, baking                             |

## Status

- 12 skills written from 148 expert videos and 130 documentation pages, each with references, a
  review rubric, and scripts.
- Offline checks (`tests/scenario-3dsmax-expert/`): every Python block compiles, every MAXScript
  block and file balances, every code block names its source and channel, and blocks for Autodesk's
  MCP channel avoid the calls Safe Scene Script Execution blocks. The family suite runs 181 tests
  offline, 63 of them on the lead's toolkit against a simulated `pymxs`.
- API names the saved documentation does not confirm are marked `[verify]`: the agent confirms each
  in the live session before relying on it.
- Blind-graded written plans (12 briefs, one grader each, graded before a final edit pass): 62 %
  without the skills, 94 % with them; all 12 briefs improved.

## Requirements

3ds Max 2027 (2027.3 for Autodesk's MCP server) on Windows. The lead skill `scenario-3dsmax-expert`
explains the execution channels: Autodesk's MCP server with Safe Scene Script Execution, a community
MCP bridge into a live session, `3dsmaxbatch`, or a handoff script the user runs.

## Install

```bash
npx skills add scenario-labs/skills --skill scenario-3dsmax-expert scenario-3dsmax-animation-rigging scenario-3dsmax-archviz scenario-3dsmax-fx scenario-3dsmax-game-assets scenario-3dsmax-generation scenario-3dsmax-lighting-rendering scenario-3dsmax-materials scenario-3dsmax-modeling scenario-3dsmax-scene scenario-3dsmax-scripting scenario-3dsmax-uv-baking
```

The installer puts the skills side by side, which the specialists need: they import the lead skill's
`scripts/`. In the installer picker (`npx skills add scenario-labs/skills`), the family is the
"Expert tools: 3ds Max" group. Update with `npx skills update`.

## Provenance

Written for this repository: the names, frontmatter (`name`, `description`, `license`) and
sibling-install line follow its conventions. Third-party AI tools inside 3ds Max are described by
capability; Autodesk, Chaos, and tyFlow features are named because they ship with the application
and renderers the skills drive.

Sources cited as `notes/...`, digests, or saved documentation files (`ai-workflows__...md`) inside
the references point to the build project on the author's machine; they are provenance only. Video
sources carry their YouTube id and timestamps, so each claim can be checked against the video.
