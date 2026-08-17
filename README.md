# Scenario Agent Skills

Agent Skills that teach AI coding agents (Claude Code, Cursor, Codex, Copilot, and 70+ others) how to create production-ready content with [Scenario](https://scenario.com) through the [Scenario MCP server](https://mcp.scenario.com): images, video, audio, textures, skyboxes, 3D assets, and custom-trained models, for games, entertainment, and any creative vertical.

Skills follow the [Agent Skills](https://agentskills.io) format.

[![skills.sh](https://skills.sh/b/scenario-labs/skills)](https://skills.sh/scenario-labs/skills)

## Install

```bash
# All skills
npx skills add scenario-labs/skills

# A single skill
npx skills add scenario-labs/skills -s scenario
```

Some skills direct sibling skills per stage, so installing one of them alone leaves its references unfilled. Install a composed pipeline together:

```bash
# Video ads (director skill plus the siblings it delegates to)
npx skills add scenario-labs/skills -s scenario -s scenario-video-ads -s scenario-image -s scenario-video -s scenario-seedance -s scenario-audio -s scenario-video-assembly -s scenario-text-overlay -s scenario-consistency -s scenario-asset-analysis

# Seedance music video
npx skills add scenario-labs/skills -s scenario -s scenario-seedance-music-video -s scenario-seedance -s scenario-consistency
```

Skills need the Scenario MCP server connected:

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
```

Or add `https://mcp.scenario.com/mcp` to any MCP client and sign in with a Scenario account (OAuth), or use an [API key](https://app.scenario.com/settings/api). Full setup lives in the `scenario` skill.

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
| [scenario-image-editing](skills/scenario-image-editing/SKILL.md) | Tool-model image edits: 3D LUT grades, effects, expand and reframe, resize, slicing, layers, background removal       |
| [scenario-text-overlay](skills/scenario-text-overlay/SKILL.md)   | Letter-perfect text overlays: templated transparent PNG cards (taglines, CTAs, legal supers, rich cards) to composite |
| [scenario-storyboards](skills/scenario-storyboards/SKILL.md)     | Comic pages, storybooks, and pre-viz storyboards: script first, one run per panel, a locked cast, lettering in post   |

### Image model families

The top image families in depth: generation and editing modes, reference rules, and the caps that differ per member.

| Skill                                                                      | Use it for                                                                                                                                                                                         |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-gpt-image](skills/scenario-gpt-image/SKILL.md)                   | GPT Image generation and editing: member routing (mask, pixel sizing, transparency, input fidelity), in-image text, preservation prompts, cost                                                     |
| [scenario-mai-image](skills/scenario-mai-image/SKILL.md)                   | MAI Image: in-image typography, quoted copy prompts, instruction editing (preserve first, one change), per-editor source input shapes, edit cost split                                             |
| [scenario-seedream](skills/scenario-seedream/SKILL.md)                     | Seedream images: member selection (Pro, Lite, 4.5, Layerize), per-member sizing contracts, in-image text, sequence sets, layer splits, cost                                                        |
| [scenario-gemini-image](skills/scenario-gemini-image/SKILL.md)             | Gemini image (Nano Banana): member choice (Flash, Pro, Lite), instruction editing, reference roles, video stills, Search grounding, cost                                                           |
| [scenario-reve](skills/scenario-reve/SKILL.md)                             | Reve image: v2.1 vs Remix selection, frame-tag reference wiring, maskless instruction edits, per-member caps and cost                                                                              |
| [scenario-ideogram](skills/scenario-ideogram/SKILL.md)                     | Ideogram images: member selection (V4 typography, native transparency, layerize text, character, remove background), expansion off for exact copy, transparency routes, per-member parameter drift |
| [scenario-grok-imagine-image](skills/scenario-grok-imagine-image/SKILL.md) | Grok Imagine images: text-to-image and instruction editing, exact in-image typography, quoted copy rules, aspect ratio traps, quality and cost tiers                                               |
| [scenario-luma-image](skills/scenario-luma-image/SKILL.md)                 | Luma Uni-1 images: create vs edit mode, role-labeled references, web search grounding, rendered text, cost                                                                                         |

### Game art and environments

Sprites, icons, tilesets, textures, skyboxes, and 3D assets ready for game engines.

| Skill                                                        | Use it for                                                                                                       |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| [scenario-game-assets](skills/scenario-game-assets/SKILL.md) | Sprites, icons, props, tilesets, pixel art, concept art, transparent backgrounds, style-consistent batches       |
| [scenario-textures](skills/scenario-textures/SKILL.md)       | Seamless and tileable textures, PBR materials, tiling-safe upscaling, engine-ready sizing                        |
| [scenario-skyboxes](skills/scenario-skyboxes/SKILL.md)       | 360 equirectangular panoramas and skyboxes, seam-safe upscaling, engine export                                   |
| [scenario-3d](skills/scenario-3d/SKILL.md)                   | Text or image to 3D meshes, multi-view reconstruction, retexture and remesh, inline 3D preview, GLB/FBX download |

### 3D model families

The top 3D families in depth: mesh generation, retexture and rigging toolchains, portraits, and explorable worlds and splats.

| Skill                                                    | Use it for                                                                                                                                                                              |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-meshy](skills/scenario-meshy/SKILL.md)         | Meshy 3D: generate from image, multi-view, or text, then retexture, remesh, UV unwrap, rig, or animate; texture precedence, Ultra mode, polycount traps                                 |
| [scenario-rodin](skills/scenario-rodin/SKILL.md)         | Rodin 3D: member selection (image-to-3D, text-to-3D, Fast lanes, Bang! mesh splitting), full versus Fast parameter dialects, topology and tier traps, cost                              |
| [scenario-sparc3d](skills/scenario-sparc3d/SKILL.md)     | Sparc3D image-to-3D: ordered multi-view input, mesh vs textured output, per-member resolution spellings, face budgets, long-job waits                                                   |
| [scenario-3d-worlds](skills/scenario-3d-worlds/SKILL.md) | 3D worlds and splats: member choice by input (text, image, pano, multi-view, video, object), Marble draft-then-upgrade seed reuse, HY World skybox-to-splat pipeline, long-job patience |

### Video and audio

Video generation and editing, music, sound effects, voice, and speech.

| Skill                                                                          | Use it for                                                                                                        |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| [scenario-video](skills/scenario-video/SKILL.md)                               | Text-to-video and image-to-video, motion prompting, lipsync, video editing, upscaling, cut/split/concat utilities |
| [scenario-video-editing](skills/scenario-video-editing/SKILL.md)               | Tool-model footage edits: LUT grades and effects, trim, split, resize, reverse, frames, masks, layers             |
| [scenario-seedance-music-video](skills/scenario-seedance-music-video/SKILL.md) | Turning a song into a music video: beat-aligned shots, lyric transcription, shot sound under the master, assembly |
| [scenario-video-ads](skills/scenario-video-ads/SKILL.md)                       | Producing a video ad from a product shot: brief, storyboard, cinematic grammar, fidelity gates, budget, delivery  |
| [scenario-audio](skills/scenario-audio/SKILL.md)                               | Music, sound effects, voice and speech generation, video scoring, audio utilities                                 |
| [scenario-video-assembly](skills/scenario-video-assembly/SKILL.md)             | Assembling clips into a finished video: timeline composition, concat with transitions, overlays, music, captions  |

### Video model families

The top video families in depth: conditioning modes, native audio, editing and extension, and per-member caps and costs.

| Skill                                                                      | Use it for                                                                                                                                                 |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-minimax-video](skills/scenario-minimax-video/SKILL.md)           | MiniMax Hailuo video: H3 keyframe vs reference modes, bracketed camera commands, native audio prompting, 2.3 duration coupling, cost                       |
| [scenario-gemini-omni](skills/scenario-gemini-omni/SKILL.md)               | Gemini Omni video: member selection (first frame, references, edit), prompted native audio, identity from references, motion-locked restyles               |
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

### Consistency and custom models

Hold one character, product, or style across a whole set, and train custom models on your own art.

| Skill                                                                  | Use it for                                                                                                                  |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [scenario-consistency](skills/scenario-consistency/SKILL.md)           | Holding one character, product, or style across a set: baseline-plus-delta prompts, reference images, control maps          |
| [scenario-identity-library](skills/scenario-identity-library/SKILL.md) | Creating named characters and props as reusable identities: interview to brief, gated collections, Grid Maker sheets, reuse |
| [scenario-model-training](skills/scenario-model-training/SKILL.md)     | Training custom models for style, character, or product consistency, and generating with them                               |

### Reviewing and organizing output

Read finished assets back: caption them, extract a style or a control map, check a batch against a brief or the Quality Gate, and file the keepers.

| Skill                                                              | Use it for                                                                                                                          |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| [scenario-asset-analysis](skills/scenario-asset-analysis/SKILL.md) | Reading assets back: captions, style descriptions, batch review against a brief, control maps, collections, tags                    |
| [scenario-quality-gate](skills/scenario-quality-gate/SKILL.md)     | Pass/warn/fail image verdicts from the Quality Gate: free stored reads, dry-run pricing, feeding suggestions back into the next run |
| [scenario-refine-loop](skills/scenario-refine-loop/SKILL.md)       | Iterating until output matches the brief: rubric first, batched critique verdicts, cheapest targeted fix, round caps                |

### Formats and placements

Ship one approved master, image or video, to every placement: ratios, safe zones, and platform specs from social feeds to shops, storefronts, and print.

| Skill                                                | Use it for                                                                                                                   |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| [scenario-formats](skills/scenario-formats/SKILL.md) | Deriving every placement from one master, image or video: crop vs resize vs expand vs reframe, platform specs and safe areas |

### Workflows and apps

Discover, run, build, and publish Scenario workflows, the multi-step pipelines users call apps.

| Skill                                                                      | Use it for                                                                                                       |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| [scenario-workflows](skills/scenario-workflows/SKILL.md)                   | Running saved workflows (apps): building the run inputs, dry-run pricing, unsticking approval gates              |
| [scenario-workflow-authoring](skills/scenario-workflow-authoring/SKILL.md) | Creating and editing workflow graphs: the editor_info grammar, node wiring, publishing drafts into runnable apps |

### Troubleshooting

Get past a blocked generation, and turn a stuck session into a reproducible public issue.

| Skill                                                      | Use it for                                                                                                       |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| [scenario-moderation](skills/scenario-moderation/SKILL.md) | Recovering a blocked generation: provider-side filters, model switching, proportional wording, look-alike errors |
| [scenario-report](skills/scenario-report/SKILL.md)         | Reporting a bug or change request as a reproducible, redacted issue on this repository's public tracker          |

## Example prompts

Once the skills are installed and the MCP server is connected, ask your agent things like:

- "Generate four style-matched potion icons with transparent backgrounds for my RPG inventory"
- "Make a seamless brick texture, then upscale it to 2048 without breaking the tiling"
- "Turn this concept sketch into a 3D prop and let me preview it before I export the GLB"

## What is an Agent Skill?

A skill is a `SKILL.md` file with procedural knowledge an agent loads on demand, defined by the open [Agent Skills specification](https://agentskills.io/specification). The `skills` CLI installs these files into 70+ agents, and the ecosystem directory lives at [skills.sh](https://www.skills.sh).

## Contributing

See [AGENTS.md](AGENTS.md) for the authoring contract, the public-content policy, validation, and the application-testing bar. One-time setup after cloning: `pnpm install` (installs commitlint, cspell, prettier, and the husky git hooks). `pnpm run validate` runs the same content checks CI runs; commit messages and the PR title are linted separately with commitlint. PRs welcome; PR titles follow Conventional Commits since they become the squash commit header on `main`.

Every script shipped with a skill has a test suite in `tests/<name>/`; `pnpm test` runs them all (CI does too). Suites need Python 3.11+ with any `tests/<name>/requirements.txt` dependencies installed, plus ffmpeg on PATH where a suite uses it. Python suites use stdlib `unittest`, TypeScript suites use vitest.

## License

[MIT](LICENSE)
