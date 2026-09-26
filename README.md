<p align="center">
  <a href="https://scenario.com" target="_blank" rel="noopener noreferrer">
    <img src="./resources/scenario-logo.png" height="84" alt="Scenario" />
  </a>
  <br />
</p>
<div align="center">
  <h1>
    Scenario Agent Skills
  </h1>
  <a href="https://skills.sh/scenario-labs/skills">
    <img alt="skills.sh" src="https://skills.sh/b/scenario-labs/skills" />
  </a>
  <a href="https://mcp.scenario.com/docs">
    <img alt="MCP documentation" src="https://img.shields.io/badge/documentation-mcp-black.svg" />
  </a>
  <a href="https://docs.scenario.com">
    <img alt="API documentation" src="https://img.shields.io/badge/documentation-api-black.svg" />
  </a>
  <a href="https://help.scenario.com">
    <img alt="App documentation" src="https://img.shields.io/badge/documentation-app-black.svg" />
  </a>
  <a href="https://x.com/scenario_gg">
    <img alt="Follow on X" src="https://img.shields.io/twitter/url.svg?label=%40scenario_gg&style=social&url=https%3A%2F%2Fx.com%2Fscenario_gg" />
  </a>
  <br />
  <br />
</div>

Agent Skills that teach AI coding agents (Claude Code, Cursor, Codex, Copilot, and 70+ others) how to create production-ready content with [Scenario](https://scenario.com) through the [Scenario MCP server](https://mcp.scenario.com): images, video, audio, textures, skyboxes, 3D assets, and custom-trained models, for games, entertainment, and any creative vertical.

The expert tools at the bottom of the list work differently: teams of skills that drive DCC (digital content creation) software and game engines installed on your machine (ZBrush, Blender, Maya, Unreal Engine, Unity), distilled from expert tutorials, conference talks, and official documentation. They need the application, not the Scenario MCP server, and each family folder's README records how it was built and how far it was verified.

Skills follow the [Agent Skills](https://agentskills.io) format.

## Install

**Everything for Scenario.** All 65 Scenario skills, without the expert tools: the default for working through the Scenario MCP.

```bash
# Every Scenario skill, without the expert tools
npx skills add scenario-labs/skills --skill scenario --skill scenario-inspiration --skill scenario-image --skill scenario-product-shots --skill scenario-brand-kit --skill scenario-image-editing --skill scenario-text-overlay --skill scenario-storyboards --skill scenario-game-assets --skill scenario-sprite-animation --skill scenario-textures --skill scenario-skyboxes --skill scenario-3d --skill scenario-patina-retexture --skill scenario-orbit-views --skill scenario-video --skill scenario-video-editing --skill scenario-seedance-music-video --skill scenario-seedance-storyboard --skill scenario-video-ads --skill scenario-ugc --skill scenario-fan-cam --skill scenario-audio --skill scenario-video-assembly --skill scenario-caption-studio --skill scenario-consistency --skill scenario-identity-library --skill scenario-model-training --skill scenario-asset-analysis --skill scenario-quality-gate --skill scenario-refine-loop --skill scenario-model-comparison --skill scenario-formats --skill scenario-workflows --skill scenario-workflow-authoring --skill scenario-moderation --skill scenario-report --skill scenario-team-admin --skill scenario-admin-analytics --skill scenario-gpt-image --skill scenario-mai-image --skill scenario-seedream --skill scenario-gemini-image --skill scenario-reve --skill scenario-ideogram --skill scenario-grok-imagine-image --skill scenario-luma-image --skill scenario-minimax-video --skill scenario-gemini-omni --skill scenario-grok-imagine-video --skill scenario-veo --skill scenario-seedance --skill scenario-kling --skill scenario-vidu --skill scenario-wan --skill scenario-runway --skill scenario-luma-video --skill scenario-minimax-music --skill scenario-elevenlabs --skill scenario-ace-step --skill scenario-sonilo --skill scenario-meshy --skill scenario-rodin --skill scenario-sparc3d --skill scenario-3d-worlds
```

**By role.** [INSTALL.md](INSTALL.md) groups the skills by job, from 2D artist to producer, with the outcomes each role gets and one command per role.

**By goal.** Each command installs the lead skills for one outcome plus the sibling skills they hand work to.

**Game art and environments** (17 skills). Game-ready sprites, tilesets, textures, skyboxes, and 3D props in one consistent style.

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-game-assets --skill scenario-sprite-animation --skill scenario-textures --skill scenario-skyboxes --skill scenario-3d --skill scenario-image --skill scenario-patina-retexture --skill scenario-video --skill scenario-consistency --skill scenario-model-training --skill scenario-refine-loop --skill scenario-moderation --skill scenario-meshy --skill scenario-rodin --skill scenario-sparc3d --skill scenario-3d-worlds
```

**Marketing and brand visuals** (20 skills). One product shot and a brief turned into on-brand stills, ads, UGC videos, and every placement size.

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-product-shots --skill scenario-brand-kit --skill scenario-video-ads --skill scenario-ugc --skill scenario-formats --skill scenario-inspiration --skill scenario-image --skill scenario-image-editing --skill scenario-text-overlay --skill scenario-video --skill scenario-video-editing --skill scenario-audio --skill scenario-video-assembly --skill scenario-consistency --skill scenario-asset-analysis --skill scenario-veo --skill scenario-seedance --skill scenario-kling --skill scenario-elevenlabs
```

**Video, music video, and audio** (22 skills). Video made, edited, and scored, from a single clip to a whole-song music video, with voice, music, and sound effects.

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-video --skill scenario-video-editing --skill scenario-audio --skill scenario-video-assembly --skill scenario-image-editing --skill scenario-text-overlay --skill scenario-seedance-music-video --skill scenario-minimax-video --skill scenario-gemini-omni --skill scenario-grok-imagine-video --skill scenario-veo --skill scenario-seedance --skill scenario-kling --skill scenario-vidu --skill scenario-wan --skill scenario-runway --skill scenario-luma-video --skill scenario-minimax-music --skill scenario-elevenlabs --skill scenario-ace-step --skill scenario-sonilo
```

**Consistent characters and custom models** (11 skills). One character, product, or style held across a whole set, and a model trained on your own art.

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-consistency --skill scenario-identity-library --skill scenario-model-training --skill scenario-image-editing --skill scenario-sprite-animation --skill scenario-video --skill scenario-asset-analysis --skill scenario-quality-gate --skill scenario-seedream --skill scenario-gemini-image
```

**Images and editing** (23 skills). Images generated and edited, exact text overlays, and a sequence storyboarded.

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-image --skill scenario-image-editing --skill scenario-text-overlay --skill scenario-storyboards --skill scenario-game-assets --skill scenario-textures --skill scenario-skyboxes --skill scenario-video --skill scenario-video-editing --skill scenario-seedance-storyboard --skill scenario-video-ads --skill scenario-video-assembly --skill scenario-consistency --skill scenario-asset-analysis --skill scenario-gpt-image --skill scenario-mai-image --skill scenario-seedream --skill scenario-gemini-image --skill scenario-reve --skill scenario-ideogram --skill scenario-grok-imagine-image --skill scenario-luma-image
```

**Expert tools.** A family installs as one set, since its specialists import the lead skill's scripts; the command is in each family README ([ZBrush](skills/dcc/zbrush/README.md), [Blender](skills/dcc/blender/README.md), [Maya](skills/dcc/maya/README.md), [Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md)).

**Pick, or install one skill.**

```bash
# Pick from the installer menu, grouped by topic (it opens with nothing preselected: select before pressing enter)
npx skills add scenario-labs/skills

# A single skill
npx skills add scenario-labs/skills --skill scenario
```

The Scenario skills need the Scenario MCP server connected:

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
```

Or add `https://mcp.scenario.com/mcp` to any MCP client and sign in with a Scenario account (OAuth), or use an [API key](https://app.scenario.com/settings/api). Full setup lives in the `scenario` skill.

## Staying up to date

Installs always fetch the latest copy of each skill from `main`; there is no version pinning. Releases are how changes become visible: every feature, fix, and documentation change merged to `main` lands in the next release, staged by release-please as an open release PR. Merging that PR tags a version, updates `CHANGELOG.md` in this repository, publishes a [GitHub release](https://github.com/scenario-labs/skills/releases), and posts the notes to the [Scenario changelog](https://www.scenario.com/changelog).

- To learn that a skill changed, watch this repository's releases (Watch, then Custom, then Releases on GitHub) or check any of the changelog pages above. An entry scoped to a single skill carries that skill's name; changes spanning several skills appear under broader scopes such as `skills`.
- To pull the changes, run `npx skills update` where you installed, or re-run your original `npx skills add` command.

## Skills

### Getting started

Connect the Scenario MCP server and learn the core generation loop every other skill builds on.

| Skill                                | Use it for                                                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| [scenario](skills/scenario/SKILL.md) | Connecting to the Scenario MCP and the core generation loop: discover, schema, run, wait, display, download |

### Finding a direction

Turn a blank brief into references, options someone can choose between, and a moodboard the next batch runs from.

| Skill                                                        | Use it for                                                                                                            |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| [scenario-inspiration](skills/scenario-inspiration/SKILL.md) | Finding a direction before generating: serendipity, reference hunting, A/B/C/D concept options, moodboard collections |

### Images

Generate and edit images: model choice, sizing, references, masked edits, post-processing tools, and letter-perfect text overlay cards.

| Skill                                                            | Use it for                                                                                                            |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| [scenario-image](skills/scenario-image/SKILL.md)                 | Text-to-image and image editing: model choice, sizing fields, prompt limits, reference images, masked inpainting      |
| [scenario-product-shots](skills/scenario-product-shots/SKILL.md) | Product photography from a real photo: packshots, lifestyle scenes, relighting, label-fidelity gates                  |
| [scenario-brand-kit](skills/scenario-brand-kit/SKILL.md)         | Visual identities: SVG logos and wordmarks, palette and type specs, gated variants and applications, the filed kit    |
| [scenario-image-editing](skills/scenario-image-editing/SKILL.md) | Tool-model image edits: 3D LUT grades, effects, expand and reframe, resize, slicing, layers, background removal       |
| [scenario-text-overlay](skills/scenario-text-overlay/SKILL.md)   | Letter-perfect text overlays: templated transparent PNG cards (taglines, CTAs, legal supers, rich cards) to composite |
| [scenario-storyboards](skills/scenario-storyboards/SKILL.md)     | Comic pages, storybooks, and pre-viz storyboards: script first, one run per panel, a locked cast, lettering in post   |

### Game art and environments

Sprites, icons, tilesets, textures, skyboxes, and 3D assets ready for game engines.

| Skill                                                                  | Use it for                                                                                                                                                      |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-game-assets](skills/scenario-game-assets/SKILL.md)           | Sprites, icons, props, tilesets, pixel art, concept art, transparent backgrounds, style-consistent batches                                                      |
| [scenario-sprite-animation](skills/scenario-sprite-animation/SKILL.md) | Walk cycles, idle loops, VFX sprites, and animation sheets from one prompt: GIF vs sprite sheet output, frame slicing, pixel cleanup                            |
| [scenario-textures](skills/scenario-textures/SKILL.md)                 | Seamless and tileable textures, PBR materials, tiling-safe upscaling, engine-ready sizing                                                                       |
| [scenario-skyboxes](skills/scenario-skyboxes/SKILL.md)                 | 360 equirectangular panoramas and skyboxes, seam-safe upscaling, engine export                                                                                  |
| [scenario-3d](skills/scenario-3d/SKILL.md)                             | Text or image to 3D meshes, multi-view reconstruction, retexture and remesh, inline 3D preview, GLB/FBX download                                                |
| [scenario-patina-retexture](skills/scenario-patina-retexture/SKILL.md) | PATINA PBR retexture of a finished mesh: material families, one map set per family, Blender apply with geometry untouched, matched before/after comparison film |
| [scenario-orbit-views](skills/scenario-orbit-views/SKILL.md)           | New camera angles of one picture through a 3D intermediary: clay layouts in a grounded panorama, repaint per camera, matched transparent set                    |

### Video and audio

Video generation and editing, music, sound effects, voice, and speech.

| Skill                                                                          | Use it for                                                                                                                            |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-video](skills/scenario-video/SKILL.md)                               | Text-to-video and image-to-video, motion prompting, lipsync, video editing, upscaling, cut/split/concat utilities                     |
| [scenario-video-editing](skills/scenario-video-editing/SKILL.md)               | Tool-model footage edits: LUT grades and effects, trim, split, resize, reverse, frames, masks, layers                                 |
| [scenario-seedance-music-video](skills/scenario-seedance-music-video/SKILL.md) | Turning a song into a music video: beat-aligned shots, lyric transcription, shot sound under the master, assembly                     |
| [scenario-seedance-storyboard](skills/scenario-seedance-storyboard/SKILL.md)   | Movement that holds across cuts: timecoded shot scripts, character sheets and boards, pose-chained shots that play as one performance |
| [scenario-video-ads](skills/scenario-video-ads/SKILL.md)                       | Producing a video ad from a product shot: brief, storyboard, cinematic grammar, fidelity gates, budget, delivery                      |
| [scenario-ugc](skills/scenario-ugc/SKILL.md)                                   | UGC-style creator video: talking-head and avatar ads, demos, faceless voiceover, spoken-register scripts, claim safety                |
| [scenario-fan-cam](skills/scenario-fan-cam/SKILL.md)                           | Personalized fan-cam clips: identity edit into a broadcast still, reaction beats to video, graphics composited in post                |
| [scenario-audio](skills/scenario-audio/SKILL.md)                               | Music, sound effects, voice and speech generation, video scoring, audio utilities                                                     |
| [scenario-video-assembly](skills/scenario-video-assembly/SKILL.md)             | Assembling clips into a finished video: timeline composition, concat with transitions, overlays, music, captions                      |
| [scenario-caption-studio](skills/scenario-caption-studio/SKILL.md)             | Captioning a finished video per destination: styled burn-in or SRT, transcription hints, translation, per-platform placement          |

### Consistency and custom models

Hold one character, product, or style across a whole set, and train custom models on your own art.

| Skill                                                                  | Use it for                                                                                                                  |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [scenario-consistency](skills/scenario-consistency/SKILL.md)           | Holding one character, product, or style across a set: baseline-plus-delta prompts, reference images, control maps          |
| [scenario-identity-library](skills/scenario-identity-library/SKILL.md) | Creating named characters and props as reusable identities: interview to brief, gated collections, Grid Maker sheets, reuse |
| [scenario-model-training](skills/scenario-model-training/SKILL.md)     | Training custom models for style, character, or product consistency, and generating with them                               |

### Reviewing and organizing output

Read finished assets back: caption them, extract a style or a control map, check a batch against a brief or the Quality Gate, compare candidate models on one brief, and file the keepers.

| Skill                                                                  | Use it for                                                                                                                                                  |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-asset-analysis](skills/scenario-asset-analysis/SKILL.md)     | Reading assets back: captions, style descriptions, batch review against a brief, control maps, collections, tags                                            |
| [scenario-quality-gate](skills/scenario-quality-gate/SKILL.md)         | Pass/warn/fail image verdicts from the Quality Gate: free stored reads, dry-run pricing, feeding suggestions back into the next run                         |
| [scenario-refine-loop](skills/scenario-refine-loop/SKILL.md)           | Iterating until output matches the brief: rubric first, batched critique verdicts, cheapest targeted fix, round caps                                        |
| [scenario-model-comparison](skills/scenario-model-comparison/SKILL.md) | Bake-offs between candidate models on one brief: normalized inputs, a dry-run cost matrix, billed cost and latency, contact sheets, pre-registered criteria |

### Formats and placements

Ship one approved master, image or video, to every placement: ratios, safe zones, and platform specs from social feeds to shops, storefronts, and print.

| Skill                                                | Use it for                                                                                                                   |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| [scenario-formats](skills/scenario-formats/SKILL.md) | Deriving every placement from one master, image or video: crop vs resize vs expand vs reframe, platform specs and safe areas |

### Workflows and apps

Discover, run, build, and publish Scenario workflows (apps), and migrate graphs from Weavy, ComfyUI, or other node editors.

| Skill                                                                      | Use it for                                                                                                                                               |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-workflows](skills/scenario-workflows/SKILL.md)                   | Running saved workflows (apps): building the run inputs, dry-run pricing, unsticking approval gates                                                      |
| [scenario-workflow-authoring](skills/scenario-workflow-authoring/SKILL.md) | Creating and editing workflow graphs: editor_info grammar, node wiring, publishing apps, and migrating graphs from Weavy, ComfyUI, or other node editors |

### Troubleshooting

Get past a blocked generation, and turn a stuck session into a reproducible public issue.

| Skill                                                      | Use it for                                                                                                       |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| [scenario-moderation](skills/scenario-moderation/SKILL.md) | Recovering a blocked generation: provider-side filters, model switching, proportional wording, look-alike errors |
| [scenario-report](skills/scenario-report/SKILL.md)         | Reporting a bug or change request as a reproducible, redacted issue on this repository's public tracker          |

### Team administration

Govern a team from the agent: which models it can run, who is on it and in which projects, per-member spend caps, API key roles, and who spent what.

| Skill                                                                | Use it for                                                                                                             |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| [scenario-team-admin](skills/scenario-team-admin/SKILL.md)           | Model access control, team and project membership, per-member Creative Unit caps, API key roles, and spend attribution |
| [scenario-admin-analytics](skills/scenario-admin-analytics/SKILL.md) | Cached MCP usage analytics, model and user rankings, CSV exports, adoption PDFs, and a local dashboard                 |

### Image model families

The top image families in depth: generation and editing modes, reference rules, and the caps that differ per member.

| Skill                                                                      | Use it for                                                                                                                                                                                         |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-gpt-image](skills/scenario-gpt-image/SKILL.md)                   | GPT Image 2.5 Flare and Sunburst, GPT Image 2 and 1.5: member routing, the quality tiers up to max and their price ladder, alpha masks, transparent cutouts, in-image text, pixel sizing           |
| [scenario-mai-image](skills/scenario-mai-image/SKILL.md)                   | MAI Image: in-image typography, quoted copy prompts, instruction editing (preserve first, one change), per-editor source input shapes, edit cost split                                             |
| [scenario-seedream](skills/scenario-seedream/SKILL.md)                     | Seedream images: member selection (Pro, Lite, 4.5, Layerize), per-member sizing contracts, in-image text, sequence sets, layer splits, cost                                                        |
| [scenario-gemini-image](skills/scenario-gemini-image/SKILL.md)             | Gemini image (Nano Banana): member choice (Flash, Pro, Lite), instruction editing, reference roles, video stills, Search grounding, cost                                                           |
| [scenario-reve](skills/scenario-reve/SKILL.md)                             | Reve image: v2.1 vs Remix selection, frame-tag reference wiring, maskless instruction edits, per-member caps and cost                                                                              |
| [scenario-ideogram](skills/scenario-ideogram/SKILL.md)                     | Ideogram images: member selection (V4 typography, native transparency, layerize text, character, remove background), expansion off for exact copy, transparency routes, per-member parameter drift |
| [scenario-grok-imagine-image](skills/scenario-grok-imagine-image/SKILL.md) | Grok Imagine images: text-to-image and instruction editing, exact in-image typography, quoted copy rules, aspect ratio traps, quality and cost tiers                                               |
| [scenario-luma-image](skills/scenario-luma-image/SKILL.md)                 | Luma Uni-1 images: create vs edit mode, role-labeled references, web search grounding, rendered text, cost                                                                                         |

### Video model families

The top video families in depth: conditioning modes, native audio, editing and extension, and per-member caps and costs.

| Skill                                                                      | Use it for                                                                                                                                                 |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-minimax-video](skills/scenario-minimax-video/SKILL.md)           | MiniMax Hailuo video: H3 keyframe vs reference modes, bracketed camera commands, native audio prompting, 2.3 duration coupling, cost                       |
| [scenario-gemini-omni](skills/scenario-gemini-omni/SKILL.md)               | Gemini Omni video: member selection (first frame, references, edit, extend), prompted native audio, identity from references, motion-locked restyles       |
| [scenario-grok-imagine-video](skills/scenario-grok-imagine-video/SKILL.md) | Grok Imagine video: one member per mode (first frame, @image references, edit, extend), prompted audio and dialogue, resolution and preprocessing caps     |
| [scenario-veo](skills/scenario-veo/SKILL.md)                               | Veo video: mode selection (first frame, transitions, references, extend), asset or style references, prompt-directed native audio, tier costs              |
| [scenario-seedance](skills/scenario-seedance/SKILL.md)                     | Seedance video: mode selection (first frame, references, edit, extend), conditioning traps, native sound, cost                                             |
| [scenario-kling](skills/scenario-kling/SKILL.md)                           | Kling video: picking a member across V3, O1, and 2.6 (multi-shot, elements, editing, motion control, lipsync, avatar), audio exclusivity, tier cost        |
| [scenario-vidu](skills/scenario-vidu/SKILL.md)                             | Vidu video: tier and mode selection (text, image, start/end frames, references), per-tier caps, two prompt shapes, music toggle traps                      |
| [scenario-wan](skills/scenario-wan/SKILL.md)                               | Wan video: member-per-job selection (T2V, I2V, edit, Animate, reframe, outpainting), parameter drift across generations, multi-shot prompts, audio sources |
| [scenario-runway](skills/scenario-runway/SKILL.md)                         | Runway video: Gen4.5 generation (text, first frame), Aleph 2 footage edits (swap, remove, restyle), keyframe pinning, aspect ratio traps, cost             |
| [scenario-luma-video](skills/scenario-luma-video/SKILL.md)                 | Luma Ray video: member routing (generate, edit, reframe, modify), option vetoes (10s, loop, HDR, anchors), twin editor ladders, cost                       |

### Audio model families

The top audio families in depth: music, covers and stems, sound effects, speech, dubbing, and video scoring.

| Skill                                                            | Use it for                                                                                                                              |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-minimax-music](skills/scenario-minimax-music/SKILL.md) | MiniMax music: vocal songs from a tagged lyric sheet, auto lyrics, instrumental mode, melody-keeping covers, character-count cost       |
| [scenario-elevenlabs](skills/scenario-elevenlabs/SKILL.md)       | ElevenLabs audio: picking the member (TTS, music, SFX, dubbing, re-voicing, isolation), voice and tag rules, song section grammar, cost |
| [scenario-ace-step](skills/scenario-ace-step/SKILL.md)           | ACE-Step music: one member per mode, Turbo vs Quality lanes, lyric sheet tags, cover strength, repaint windows, stem edits              |
| [scenario-sonilo](skills/scenario-sonilo/SKILL.md)               | Sonilo audio: SFX and music from text or video, standalone track vs muxed clip, segment prompts, keep-speech scoring, cost              |

### 3D model families

The top 3D families in depth: mesh generation, retexture and rigging toolchains, portraits, and explorable worlds and splats.

| Skill                                                    | Use it for                                                                                                                                                                              |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-meshy](skills/scenario-meshy/SKILL.md)         | Meshy 3D: generate from image, multi-view, or text, then retexture, remesh, UV unwrap, rig, or animate; texture precedence, Ultra mode, polycount traps                                 |
| [scenario-rodin](skills/scenario-rodin/SKILL.md)         | Rodin 3D: member selection (image-to-3D, text-to-3D, Fast lanes, Bang! mesh splitting), full versus Fast parameter dialects, topology and tier traps, cost                              |
| [scenario-sparc3d](skills/scenario-sparc3d/SKILL.md)     | Sparc3D image-to-3D: ordered multi-view input, mesh vs textured output, per-member resolution spellings, face budgets, long-job waits                                                   |
| [scenario-3d-worlds](skills/scenario-3d-worlds/SKILL.md) | 3D worlds and splats: member choice by input (text, image, pano, multi-view, video, object), Marble draft-then-upgrade seed reuse, HY World skybox-to-splat pipeline, long-job patience |

### Expert tools: ZBrush

DCC software. A lead and eight specialists that drive Maxon ZBrush 2026 through its agent bridge: sculpting, characters and creatures, stylized work, hard surface, polypaint and renders, posing and 3D print, retopology and export, automation. The bridge was proven live; full live tests of every skill are still pending.

| Skill                                                                                               | Use it for                                                                                                                                                       |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-zbrush-expert](skills/dcc/zbrush/scenario-zbrush-expert/SKILL.md)                         | ZBrush lead: the agent bridge (launch, scripted strokes, dialog-free export), ZBrush Python and ZScript, review renders, 2026 traps, handoffs to the specialists |
| [scenario-zbrush-automation](skills/dcc/zbrush/scenario-zbrush-automation/SKILL.md)                 | ZBrush automation: batch jobs over OBJ or ZTL folders, ZBrush Python and ZScript, macros, UV Master, Decimation Master, Multi Map Exporter, GoZ round trips      |
| [scenario-zbrush-character-creature](skills/dcc/zbrush/scenario-zbrush-character-creature/SKILL.md) | Realistic heads, bodies, and creatures in ZBrush: anatomy and landmarks, skin, pores, wrinkles and scales, subdivision and HD Geometry planning                  |
| [scenario-zbrush-hard-surface](skills/dcc/zbrush/scenario-zbrush-hard-surface/SKILL.md)             | Hard surface in ZBrush: ZModeler, Dynamic Subdivision and creasing, Live Boolean, Knife and Slice curves, IMM, ArrayMesh, NanoMesh, Panel Loops                  |
| [scenario-zbrush-paint-render](skills/dcc/zbrush/scenario-zbrush-paint-render/SKILL.md)             | Polypaint and renders in ZBrush: color zones, cavity and AO passes, Spotlight, baking to texture or vertex color, BPR or Redshift, turntables                    |
| [scenario-zbrush-pose-print](skills/dcc/zbrush/scenario-zbrush-pose-print/SKILL.md)                 | Posing and 3D print in ZBrush: Transpose Master, Gizmo posing with masks, ZSphere rigs, print scale, hollowing, wall thickness, drain holes                      |
| [scenario-zbrush-retopology-export](skills/dcc/zbrush/scenario-zbrush-retopology-export/SKILL.md)   | Sculpt, scan, or AI mesh to production topology and files in ZBrush: ZRemesher and guides, Retopo brush, Project All, UVs, normal and displacement maps, export  |
| [scenario-zbrush-sculpting](skills/dcc/zbrush/scenario-zbrush-sculpting/SKILL.md)                   | Organic sculpting in ZBrush: primary and secondary forms, DynaMesh, Sculptris Pro or subdivision levels, core brushes, masks and polygroups                      |
| [scenario-zbrush-stylized](skills/dcc/zbrush/scenario-zbrush-stylized/SKILL.md)                     | Stylized characters, collectibles, and toys in ZBrush: shape language, deliberate exaggeration, crisp planes through subdivision, silhouette reads               |

### Expert tools: Blender

DCC software. A lead and twelve specialists that drive Blender 5.2 through Python, headless or in a live session: sculpting, retopology, UVs and baking, shading, hair, rigging, animation, previs, Geometry Nodes, lighting, Grease Pencil, hard surface. Test suites pass headless on Blender 5.2.1.

| Skill                                                                                                  | Use it for                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-blender-expert](skills/dcc/blender/scenario-blender-expert/SKILL.md)                         | Blender lead: Python headless or through a live MCP bridge, the expert review loop, the shared review and mesh-audit toolkit, Blender 5.2 API traps            |
| [scenario-blender-animation](skills/dcc/blender/scenario-blender-animation/SKILL.md)                   | Blender animation: cycles, jumps, acting and lip sync, stepped blocking to spline and polish, timing and spacing, graph editor, slotted actions and NLA        |
| [scenario-blender-geometry-nodes](skills/dcc/blender/scenario-blender-geometry-nodes/SKILL.md)         | Geometry Nodes: procedural modeling, scattering, curves and loops, simulation zones, 5.2 physics, closures and bundles, node-group assets                      |
| [scenario-blender-grease-pencil](skills/dcc/blender/scenario-blender-grease-pencil/SKILL.md)           | Grease Pencil in Blender 5.x: 2D and 2.5D illustration, frame-by-frame and cutout animation, fills, interpolation, Line Art, strokes on meshes                 |
| [scenario-blender-hair](skills/dcc/blender/scenario-blender-hair/SKILL.md)                             | Hair and fur with hair curves: hairstyles, animal fur, Essentials hair nodes, density masks and partings, hair cards and mesh hair for games                   |
| [scenario-blender-hard-surface](skills/dcc/blender/scenario-blender-hard-surface/SKILL.md)             | Hard surface in Blender: booleans and cutters, bevels, weighted normals, support loops and creases, fixing smeared or pinched shading                          |
| [scenario-blender-lighting-rendering](skills/dcc/blender/scenario-blender-lighting-rendering/SKILL.md) | Blender lighting and rendering: motivated and three-point setups, HDRI and sun, EEVEE vs Cycles, noise and leaks, AgX color management, passes and compositing |
| [scenario-blender-previs-storyboard](skills/dcc/blender/scenario-blender-previs-storyboard/SKILL.md)   | Script to previs in Blender: beats to shot list, cameras and lenses, staging and screen direction, cuts and camera moves, storyboards and animatics            |
| [scenario-blender-retopology](skills/dcc/blender/scenario-blender-retopology/SKILL.md)                 | Retopology in Blender: dense sculpt, scan, or AI mesh to clean topology for animation, subdivision, or a game low poly, loop and pole placement                |
| [scenario-blender-rigging](skills/dcc/blender/scenario-blender-rigging/SKILL.md)                       | Rigging in Blender: Rigify metarigs, automatic weights and weight fixes, IK/FK, foot roll, twist bones, drivers and custom properties                          |
| [scenario-blender-sculpting](skills/dcc/blender/scenario-blender-sculpting/SKILL.md)                   | Sculpting heads and characters in Blender: blockout from primitives, planes and landmarks, stylized and realistic faces, remesh or multires resolution         |
| [scenario-blender-texturing-shading](skills/dcc/blender/scenario-blender-texturing-shading/SKILL.md)   | Texturing and shading in Blender: PBR from texture sets, procedural materials, wear and grime, triplanar mapping, skin and eyes, stylized looks                |
| [scenario-blender-uv-baking](skills/dcc/blender/scenario-blender-uv-baking/SKILL.md)                   | UVs and baking in Blender: seams, packing, texel density, UDIMs, normal, AO, curvature, and ID bakes from high poly or Multires, fixing bad bakes              |

### Expert tools: Maya

DCC software. A lead and ten specialists that drive Autodesk Maya 2027 through Python, batch or live: modeling, retopology and UVs, rigging, skinning, animation, groom, FX, look dev, Arnold lighting and rendering, pipeline scripting. Tested offline only; not yet run inside Maya.

| Skill                                                                                         | Use it for                                                                                                                                                   |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [scenario-maya-expert](skills/dcc/maya/scenario-maya-expert/SKILL.md)                         | Maya lead: maya.cmds and OpenMaya 2.0, mayapy batch jobs, a commandPort or MCP bridge into a live Maya, scene validation, Maya 2027 traps                    |
| [scenario-maya-animation](skills/dcc/maya/scenario-maya-animation/SKILL.md)                   | Maya animation: cycles, jumps, heavy lifts, acting and lip sync, stepped blocking to spline and polish, Graph Editor, layers, mocap cleanup, game clips      |
| [scenario-maya-deformation](skills/dcc/maya/scenario-maya-deformation/SKILL.md)               | Skinning in Maya: binding and weight painting, Skin Tools or ngSkinTools layers, fixing pinching and volume loss, weights for Unreal or Unity                |
| [scenario-maya-fx](skills/dcc/maya/scenario-maya-fx/SKILL.md)                                 | Maya FX: nCloth and Nucleus, nParticles, Bifrost smoke, fire, liquids, and MPM, MASH scattering                                                              |
| [scenario-maya-groom](skills/dcc/maya/scenario-maya-groom/SKILL.md)                           | Grooming with XGen: scalp hair, brows, lashes, and fur, guides, clumps, and density maps, aiStandardHair, hair that moves                                    |
| [scenario-maya-lighting-rendering](skills/dcc/maya/scenario-maya-lighting-rendering/SKILL.md) | Maya lighting and rendering with Arnold: hero, character, and sequence lighting, noise and fireflies, AOVs and light groups, denoising, color management     |
| [scenario-maya-lookdev](skills/dcc/maya/scenario-maya-lookdev/SKILL.md)                       | Look dev in Maya with Arnold: OpenPBR or aiStandardSurface, Substance and UDIM texture sets, color spaces, normal and displacement fixes, skin, metal, glass |
| [scenario-maya-modeling](skills/dcc/maya/scenario-maya-modeling/SKILL.md)                     | Maya modeling: hard-surface props and vehicles, game-ready or SubD models, base meshes, support loops vs bevels vs creases, scene cleanup                    |
| [scenario-maya-pipeline-scripting](skills/dcc/maya/scenario-maya-pipeline-scripting/SKILL.md) | Maya pipeline code: mayapy batch jobs, scene validation and fixes, FBX for Unreal or Unity, Alembic, USD, references, PySide6 tools                          |
| [scenario-maya-retopology-uv](skills/dcc/maya/scenario-maya-retopology-uv/SKILL.md)           | Retopology and UVs in Maya: sculpt, scan, or AI mesh to animation-ready or game-ready topology, Quad Draw, deformation tests, UV layout                      |
| [scenario-maya-rigging](skills/dcc/maya/scenario-maya-rigging/SKILL.md)                       | Rigging in Maya: joint placement and orientation, IK/FK switching and matching, space switching, foot roll, spline spines, matrix rigging, controls          |

### Expert tools: Unreal Engine

Game engine. A lead and nine specialists that drive Unreal Engine 5.8 on macOS through Editor Python, headless jobs, and Epic's Unreal MCP server: world building, materials, lighting and rendering, gameplay, animation, cinematics, VFX, pipeline automation, performance. Tested offline only; not yet run inside the engine.

| Skill                                                                                                          | Use it for                                                                                                                                                   |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [scenario-unreal-expert](skills/game-engines/unreal/scenario-unreal-expert/SKILL.md)                           | Unreal lead: Editor Python, headless UnrealEditor-Cmd jobs, Epic's Unreal MCP server, the Remote Control API, console commands, 5.8 traps                    |
| [scenario-unreal-animation](skills/game-engines/unreal/scenario-unreal-animation/SKILL.md)                     | Unreal animation: skeletal import, IK Rig and Retargeter, Motion Matching and Pose Search, root motion, foot IK, Control Rig                                 |
| [scenario-unreal-cinematics](skills/game-engines/unreal/scenario-unreal-cinematics/SKILL.md)                   | Unreal cinematics with Sequencer: shot lists, master and shot sequences, cameras and lenses, per-shot lighting, Movie Render Graph output                    |
| [scenario-unreal-gameplay](skills/game-engines/unreal/scenario-unreal-gameplay/SKILL.md)                       | Unreal gameplay: characters and abilities, enemy AI, HUD, Blueprint vs C++, GAS, StateTree vs Behavior Tree, Enhanced Input, replication                     |
| [scenario-unreal-lighting-rendering](skills/game-engines/unreal/scenario-unreal-lighting-rendering/SKILL.md)   | Unreal lighting and rendering: physical units and exposure, Lumen, MegaLights, virtual shadow maps, sky and fog, post process, path tracer                   |
| [scenario-unreal-materials](skills/game-engines/unreal/scenario-unreal-materials/SKILL.md)                     | Unreal materials: master materials and instances, Substrate, glass and emissives, decals, landscape layers and RVT, toon shading, shader permutations        |
| [scenario-unreal-performance](skills/game-engines/unreal/scenario-unreal-performance/SKILL.md)                 | Unreal performance: frame budgets, CPU vs GPU bound, hitches and PSO stutter, GC spikes, Lumen, Nanite, VSM, and Niagara cost, profiling                     |
| [scenario-unreal-pipeline-automation](skills/game-engines/unreal/scenario-unreal-pipeline-automation/SKILL.md) | Unreal pipeline: bulk FBX, USD, OBJ, or glTF import from Maya, ZBrush, or Blender, Editor Python tools, Interchange, naming and validation, cook and package |
| [scenario-unreal-vfx](skills/game-engines/unreal/scenario-unreal-vfx/SKILL.md)                                 | Unreal VFX: Niagara systems (fireballs, trails, impacts, smoke, sparks), Niagara fluids, scalability and pooling, Chaos destruction                          |
| [scenario-unreal-world-building](skills/game-engines/unreal/scenario-unreal-world-building/SKILL.md)           | Unreal levels and open worlds: World Partition, Data Layers, Level Instances, HLOD, landscape, foliage, PCG scatter, Nanite                                  |

### Expert tools: Unity

Game engine. A lead and thirteen specialists that drive Unity 6.3 LTS on macOS through batch mode, a live editor, and command-line builds: architecture, gameplay, 2D, animation, UI, VFX, shaders, rendering and lighting, world building, performance, mobile, Web, pipeline automation. Every procedure was run live in Unity 6.3.

| Skill                                                                                                       | Use it for                                                                                                                                                      |
| ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-unity-expert](skills/game-engines/unity/scenario-unity-expert/SKILL.md)                           | Unity lead: batch mode and -executeMethod jobs, a live editor over the Unity CLI, MCP servers, the Test Framework, command-line builds, proof by capture        |
| [scenario-unity-2d](skills/game-engines/unity/scenario-unity-2d/SKILL.md)                                   | Unity 2D in URP: sprite import and PPU, atlases, Tilemaps and Rule Tiles, 2D lights, 2D animation, platformer and top-down controllers                          |
| [scenario-unity-animation](skills/game-engines/unity/scenario-unity-animation/SKILL.md)                     | Unity animation and cameras: humanoid import and retargeting, Animator Controllers and blend trees, root motion, Animation Rigging, Timeline, Cinemachine 3     |
| [scenario-unity-architecture](skills/game-engines/unity/scenario-unity-architecture/SKILL.md)               | Unity C# architecture: ScriptableObject data, events and services, inventory, health, save and load, Input System, Awaitable, assembly definitions, Git and LFS |
| [scenario-unity-gameplay](skills/game-engines/unity/scenario-unity-gameplay/SKILL.md)                       | Unity gameplay: enemy AI, NavMesh and agents, state machines and behavior trees, projectile physics, collision layers, CharacterController vs Rigidbody         |
| [scenario-unity-mobile](skills/game-engines/unity/scenario-unity-mobile/SKILL.md)                           | Unity on Android and iOS: frame and thermal budgets, texture compression, touch controls and safe areas, startup time, AAB and signing                          |
| [scenario-unity-performance](skills/game-engines/unity/scenario-unity-performance/SKILL.md)                 | Unity performance: frame spikes and hitches, GC, draw and SetPass calls, CPU vs GPU bound, Profiler, Memory Profiler, Frame Debugger, GPU Resident Drawer       |
| [scenario-unity-pipeline-automation](skills/game-engines/unity/scenario-unity-pipeline-automation/SKILL.md) | Unity content pipeline: AssetPostprocessor import rules, prefab and scene generation from script, Addressables, content-validation tests, CI builds             |
| [scenario-unity-rendering-lighting](skills/game-engines/unity/scenario-unity-rendering-lighting/SKILL.md)   | Unity rendering and lighting: URP setup and quality tiers, sun and sky, lightmaps and Adaptive Probe Volumes, reflection probes, shadow and bake fixes          |
| [scenario-unity-shaders](skills/game-engines/unity/scenario-unity-shaders/SKILL.md)                         | Unity shaders in URP: HLSL, Shader Graph water, toon, dissolve, and outline, renderer features on Render Graph, compute shaders, variants and stripping         |
| [scenario-unity-ui](skills/game-engines/unity/scenario-unity-ui/SKILL.md)                                   | Unity game UI: menus, settings, HUD and health bars, uGUI vs UI Toolkit, scaling from phone to 4K, layout groups, UXML and USS                                  |
| [scenario-unity-vfx](skills/game-engines/unity/scenario-unity-vfx/SKILL.md)                                 | Unity VFX: explosions, projectiles, spells, and smoke with the Particle System or VFX Graph, overdraw and mobile cost                                           |
| [scenario-unity-web](skills/game-engines/unity/scenario-unity-web/SKILL.md)                                 | Unity on the Web: WebGL and Web build settings, compression and server headers, build size and load time, portal limits, Addressables on the Web                |
| [scenario-unity-world-building](skills/game-engines/unity/scenario-unity-world-building/SKILL.md)           | Unity levels and open worlds: terrain from code or heightmaps, procedural islands, foliage rules, ProBuilder graybox, modular kits, landmarks, spline roads     |

## Example prompts

Once the skills are installed and the MCP server is connected, ask your agent things like:

- "Generate four style-matched potion icons with transparent backgrounds for my RPG inventory"
- "Make a seamless brick texture, then upscale it to 2048 without breaking the tiling"
- "Turn this concept sketch into a 3D prop and let me preview it before I export the GLB"

## What is an Agent Skill?

A skill is a `SKILL.md` file with procedural knowledge an agent loads on demand, defined by the open [Agent Skills specification](https://agentskills.io/specification). The `skills` CLI installs these files into 70+ agents, and the ecosystem directory lives at [skills.sh](https://www.skills.sh).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow, and [AGENTS.md](AGENTS.md) for the authoring contract, the public-content policy, validation, and the application-testing bar. One-time setup after cloning: `pnpm install` (installs commitlint, cspell, prettier, and the husky git hooks). `pnpm run validate` runs the same content checks CI runs; commit messages and the PR title are linted separately with commitlint. PRs welcome; PR titles follow Conventional Commits since they become the squash commit header on `main`.

Every script shipped with a skill has a test suite in `tests/<name>/`; `pnpm test` runs them all (CI does too). Suites need Python 3.11+ with any `tests/<name>/requirements.txt` dependencies installed, plus ffmpeg on PATH where a suite uses it. Python suites use stdlib `unittest`, TypeScript suites use vitest.

## License

[MIT](LICENSE)
