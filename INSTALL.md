# Install by role

Pick your role. Each command installs the skills behind that role's outcomes plus the sibling skills they hand work to, on top of `scenario` (connection and the core loop) and the troubleshooting skills (`scenario-moderation`, `scenario-report`). Commands can overlap, and installing two roles is fine. To install every Scenario skill at once, or by goal, see the [README](README.md#install). The Scenario skills need the Scenario MCP server connected (setup in the README).

## 2D Artist

Concept art, sprites, and effects in one consistent style. 22 skills.

- **Concept Sketches** (`scenario-inspiration`, `scenario-image`). Try: "Give me four directions for a desert outpost, then a moodboard for the one I pick."
- **Sprites and VFX** (`scenario-sprite-animation`, `scenario-game-assets`). Try: "Make an 8-frame run cycle sprite sheet for this knight, and a matching slash effect."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-inspiration --skill scenario-image --skill scenario-sprite-animation --skill scenario-game-assets --skill scenario-image-editing --skill scenario-text-overlay --skill scenario-3d --skill scenario-video --skill scenario-consistency --skill scenario-model-training --skill scenario-refine-loop --skill scenario-gpt-image --skill scenario-mai-image --skill scenario-seedream --skill scenario-gemini-image --skill scenario-reve --skill scenario-ideogram --skill scenario-grok-imagine-image --skill scenario-luma-image
```

## 3D Artist

Meshes from a picture, rigged and ready to animate. 12 skills.

- **Image to 3D** (`scenario-3d`, `scenario-orbit-views`). Try: "Turn this prop concept into a textured GLB, then show it from the back and from above."
- **Rigging and Retargeting** (`scenario-meshy`). Try: "Rig this character mesh and give me a walk and an idle."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-3d --skill scenario-orbit-views --skill scenario-meshy --skill scenario-skyboxes --skill scenario-patina-retexture --skill scenario-video --skill scenario-rodin --skill scenario-sparc3d --skill scenario-3d-worlds
```

Working in ZBrush, Blender or Maya? Add the expert tools for it: [ZBrush](skills/dcc/zbrush/README.md), [Blender](skills/dcc/blender/README.md), [Maya](skills/dcc/maya/README.md).

## Environment Artist

Surfaces, skies, and worlds a player can walk through. 8 skills.

- **Textures and Skyboxes** (`scenario-textures`, `scenario-skyboxes`). Try: "Make a seamless mossy cobblestone texture set with normal and roughness maps, and a matching overcast skybox."
- **Walkable 3D Worlds** (`scenario-3d-worlds`). Try: "Turn this concept painting into an explorable 3D world."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-textures --skill scenario-skyboxes --skill scenario-3d-worlds --skill scenario-3d --skill scenario-meshy
```

Working in Unreal Engine or Unity? Add the expert tools for it: [Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md).

## Art Director

One look held across every asset, checked before it ships. 15 skills.

- **One Character, Every Shot** (`scenario-consistency`, `scenario-identity-library`). Try: "Keep this heroine identical across these twelve shots, poses and outfits included."
- **Quality Check Before It Ships** (`scenario-quality-gate`, `scenario-asset-analysis`). Try: "Check this batch against the brief and flag anything off-model."
- **Our Style, Trained** (`scenario-model-training`). Try: "Train a model on our 40 approved illustrations and generate new props in that style."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-consistency --skill scenario-identity-library --skill scenario-quality-gate --skill scenario-asset-analysis --skill scenario-model-training --skill scenario-image --skill scenario-image-editing --skill scenario-sprite-animation --skill scenario-video --skill scenario-refine-loop --skill scenario-seedream --skill scenario-gemini-image
```

## Sound Designer

Music, voice, and effects that fit the picture. 9 skills.

- **Music and Score** (`scenario-audio`). Try: "Compose a 90-second tense exploration loop and a victory sting."
- **Sound Effects for Every Action** (`scenario-sonilo`). Try: "Score this gameplay clip with footsteps, a sword clash, and an explosion."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-audio --skill scenario-sonilo --skill scenario-video-assembly --skill scenario-minimax-music --skill scenario-elevenlabs --skill scenario-ace-step
```

## Video Producer

Trailers and clips, storyboarded, generated, cut, and captioned. 27 skills.

- **Cinematic Trailers** (`scenario-video`, `scenario-storyboards`, `scenario-video-assembly`). Try: "Storyboard a 30-second trailer from this script, generate the shots, and cut them to music."
- **Captions for Every Platform** (`scenario-caption-studio`, `scenario-formats`). Try: "Add word-by-word captions to this video and export 9:16, 1:1, and 16:9 versions."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-video --skill scenario-storyboards --skill scenario-video-assembly --skill scenario-caption-studio --skill scenario-formats --skill scenario-image --skill scenario-image-editing --skill scenario-text-overlay --skill scenario-video-editing --skill scenario-seedance-music-video --skill scenario-seedance-storyboard --skill scenario-video-ads --skill scenario-consistency --skill scenario-asset-analysis --skill scenario-minimax-video --skill scenario-gemini-omni --skill scenario-grok-imagine-video --skill scenario-veo --skill scenario-seedance --skill scenario-kling --skill scenario-vidu --skill scenario-wan --skill scenario-runway --skill scenario-luma-video
```

## Marketing Artist

Store art and ads that stay on brand at every size. 22 skills.

- **Store Art for Every Platform** (`scenario-formats`, `scenario-brand-kit`, `scenario-text-overlay`). Try: "Turn this key art into every storefront size, with our logo and the game's title."
- **Ads From One Shot** (`scenario-product-shots`, `scenario-video-ads`, `scenario-ugc`). Try: "From this product shot, make a 15-second video ad and three UGC-style variants."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-formats --skill scenario-brand-kit --skill scenario-text-overlay --skill scenario-product-shots --skill scenario-video-ads --skill scenario-ugc --skill scenario-inspiration --skill scenario-image --skill scenario-image-editing --skill scenario-video --skill scenario-video-editing --skill scenario-audio --skill scenario-video-assembly --skill scenario-consistency --skill scenario-asset-analysis --skill scenario-veo --skill scenario-seedance --skill scenario-kling --skill scenario-elevenlabs
```

## Technical Director

Repeatable pipelines the whole team can run. 5 skills.

- **Workflows Rebuilt From ComfyUI** (`scenario-workflow-authoring`). Try: "Rebuild this ComfyUI graph as a Scenario workflow and publish it as an app."
- **Custom Pipelines** (`scenario-workflows`). Try: "Run our sketch-to-final workflow on these 20 sketches and collect the results."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-workflow-authoring --skill scenario-workflows
```

Working in Unreal Engine or Unity? Add the expert tools for it: [Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md).

## Producer

The right model at the right cost, and spend under control. 8 skills.

- **Model Bake-Offs With Cost** (`scenario-model-comparison`). Try: "Compare three image models on this brief, with quality and credit cost side by side."
- **Team Budgets** (`scenario-admin-analytics`, `scenario-team-admin`). Try: "Show last month's credit use by project, and cap each freelancer's spend."

```bash
npx skills add scenario-labs/skills --skill scenario --skill scenario-moderation --skill scenario-report --skill scenario-model-comparison --skill scenario-admin-analytics --skill scenario-team-admin --skill scenario-video-editing --skill scenario-refine-loop
```

## Game Developer

Gameplay, UI, animation, performance, and mobile or Web builds, driven inside the engine. These are expert tools: each family installs as one set, with its command in the family README: [Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md).

## Expert tools

Teams of skills that drive DCC software and game engines installed on your machine. They need the application, not the Scenario MCP server. Each family installs as one set: [ZBrush](skills/dcc/zbrush/README.md), [Blender](skills/dcc/blender/README.md), [Maya](skills/dcc/maya/README.md), [Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md).
