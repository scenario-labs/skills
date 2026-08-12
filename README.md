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

Skills need the Scenario MCP server connected:

```bash
claude mcp add --transport http scenario https://mcp.scenario.com/mcp
```

Or add `https://mcp.scenario.com/mcp` to any MCP client and sign in with a Scenario account (OAuth), or use an [API key](https://app.scenario.com/settings/api). Full setup lives in the `scenario` skill.

## Skills

| Skill                                                              | Use it for                                                                                                        |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| [scenario](skills/scenario/SKILL.md)                               | Connecting to the Scenario MCP and the core generation loop: discover, schema, run, wait, display, download       |
| [scenario-game-assets](skills/scenario-game-assets/SKILL.md)       | Sprites, icons, props, tilesets, pixel art, concept art, transparent backgrounds, style-consistent batches        |
| [scenario-textures](skills/scenario-textures/SKILL.md)             | Seamless and tileable textures, PBR materials, tiling-safe upscaling, engine-ready sizing                         |
| [scenario-skyboxes](skills/scenario-skyboxes/SKILL.md)             | 360 equirectangular panoramas and skyboxes, seam-safe upscaling, engine export                                    |
| [scenario-3d](skills/scenario-3d/SKILL.md)                         | Text or image to 3D meshes, multi-view reconstruction, retexture and remesh, inline 3D preview, GLB/FBX download  |
| [scenario-video](skills/scenario-video/SKILL.md)                   | Text-to-video and image-to-video, motion prompting, lipsync, video editing, upscaling, cut/split/concat utilities |
| [scenario-audio](skills/scenario-audio/SKILL.md)                   | Music, sound effects, voice and speech generation, video scoring, audio utilities                                 |
| [scenario-model-training](skills/scenario-model-training/SKILL.md) | Training custom models for style, character, or product consistency, and generating with them                     |

## Example prompts

Once the skills are installed and the MCP server is connected, ask your agent things like:

- "Generate four style-matched potion icons with transparent backgrounds for my RPG inventory"
- "Make a seamless brick texture, then upscale it to 2048 without breaking the tiling"
- "Turn this concept sketch into a 3D prop and let me preview it before I export the GLB"

## What is an Agent Skill?

A skill is a `SKILL.md` file with procedural knowledge an agent loads on demand, defined by the open [Agent Skills specification](https://agentskills.io/specification). The `skills` CLI installs these files into 70+ agents, and the ecosystem directory lives at [skills.sh](https://www.skills.sh).

## Contributing

See [AGENTS.md](AGENTS.md) for the authoring contract, the public-content policy, validation, and the application-testing bar. One-time setup after cloning: `pnpm install` (installs commitlint, cspell, and the husky git hooks). `pnpm run validate` runs the same content checks CI runs; commit messages and the PR title are linted separately with commitlint. PRs welcome; PR titles follow Conventional Commits since they become the squash commit header on `main`.

Every script shipped with a skill has a test suite in `tests/<name>/`; `./scripts/test-skill-scripts.sh` runs them all (CI does too). Suites need Python 3.11+ with any `tests/<name>/requirements.txt` dependencies installed, plus ffmpeg on PATH where a suite uses it. Python suites use stdlib `unittest`, TypeScript suites use vitest.

## License

[MIT](LICENSE)
