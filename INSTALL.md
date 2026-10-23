# Install by role or goal

Pick your role, or the outcome you are after. Each command installs the lead skills for those
outcomes plus the sibling skills they hand work to, on top of `scenario` (connection and the core
loop); role commands also add the troubleshooting skills (`scenario-moderation`, `scenario-report`).
Commands can overlap, and installing two is fine. To install every Scenario skill at once, see the
[README](README.md#install). The Scenario skills need the Scenario MCP server connected (setup in
the README).

## By role

### 2D Artist

Concept art, sprites, and effects in one consistent style. 28 skills.

- **Concept Sketches** (`scenario-inspiration`, `scenario-image`). Try: "Give me four directions for
  a desert outpost, then a moodboard for the one I pick."
- **Sprites and VFX** (`scenario-sprite-animation`, `scenario-game-assets`). Try: "Make an 8-frame
  run cycle sprite sheet for this knight, and a matching slash effect."
- **Side-Scroller Kit** (`scenario-side-view-game-kit`). Try: "Make the sprites for my platformer's
  fox knight and a mole miner enemy, plus the layers for a mushroom forest level."
- **Side-Scroller Shots in Blender** (`scenario-blender-2d-animation`). Try: "Make a 10-second
  platformer shot of a red panda running through a jungle, animated in Blender, then the same shot
  in a snowy look."
- **One Image From Many References** (`scenario-multi-reference`). Try: "Put the knight from this
  sheet in the tavern from this painting, lit like this third image."
- **ChatGPT and Codex Pets** (`scenario-chatgpt-pet-create`, `scenario-chatgpt-pet-update`). Try:
  "Hatch a pet from our mascot, then give it a winter scarf."
- **Scenario for Photoshop** (`scenario-photoshop`). Try: "Replace the kite I selected in Photoshop
  with a red paper lantern, two options, as layers I can compare."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-inspiration scenario-image scenario-sprite-animation scenario-side-view-game-kit scenario-blender-2d-animation scenario-game-assets scenario-image-editing scenario-text-overlay scenario-3d scenario-video scenario-consistency scenario-model-training scenario-refine-loop scenario-gpt-image scenario-mai-image scenario-seedream scenario-gemini-image scenario-reve scenario-ideogram scenario-grok-imagine-image scenario-luma-image scenario-multi-reference scenario-chatgpt-pet-create scenario-chatgpt-pet-update scenario-photoshop
```

Working in Photoshop? Add the expert tools for it: [Photoshop](skills/dcc/photoshop/README.md).

### 3D Artist

Meshes from a picture, rigged and ready to animate. 13 skills.

- **Image to 3D** (`scenario-3d`, `scenario-orbit-views`). Try: "Turn this prop concept into a
  textured GLB, then show it from the back and from above."
- **Rigging and Retargeting** (`scenario-meshy`). Try: "Rig this character mesh and give me a walk
  and an idle."
- **Scenario for Blender** (`scenario-blender`). Try: "Turn what I see in the viewport into a 3D
  prop and put it at my 3D cursor."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-3d scenario-orbit-views scenario-meshy scenario-blender scenario-skyboxes scenario-patina-retexture scenario-video scenario-rodin scenario-sparc3d scenario-3d-worlds
```

Working in ZBrush, Blender, Maya or Photoshop? Add the expert tools for it:
[ZBrush](skills/dcc/zbrush/README.md), [Blender](skills/dcc/blender/README.md),
[Maya](skills/dcc/maya/README.md), [Photoshop](skills/dcc/photoshop/README.md).

### Environment Artist

Surfaces, skies, and worlds a player can walk through. 13 skills.

- **Textures and Skyboxes** (`scenario-textures`, `scenario-skyboxes`). Try: "Make a seamless mossy
  cobblestone texture set with normal and roughness maps, and a matching overcast skybox."
- **Walkable 3D Worlds** (`scenario-3d-worlds`). Try: "Turn this concept painting into an explorable
  3D world."
- **A Room to Walk Into** (`scenario-walkable-room`). Try: "Turn this photo of my living room into a
  room I can walk around in the browser and throw the cushions."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-textures scenario-skyboxes scenario-3d-worlds scenario-walkable-room scenario-3d scenario-meshy scenario-image scenario-gemini-image scenario-audio scenario-sonilo
```

Working in Unreal Engine, Unity, or Godot? Add the expert tools for it:
[Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md),
[Godot](skills/game-engines/godot/README.md).

### Art Director

One look held across every asset, checked before it ships. 15 skills.

- **One Character, Every Shot** (`scenario-consistency`, `scenario-identity-library`). Try: "Keep
  this heroine identical across these twelve shots, poses and outfits included."
- **Quality Check Before It Ships** (`scenario-quality-gate`, `scenario-asset-analysis`). Try:
  "Check this batch against the brief and flag anything off-model."
- **Our Style, Trained** (`scenario-model-training`). Try: "Train a model on our 40 approved
  illustrations and generate new props in that style."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-consistency scenario-identity-library scenario-quality-gate scenario-asset-analysis scenario-model-training scenario-image scenario-image-editing scenario-sprite-animation scenario-video scenario-refine-loop scenario-seedream scenario-gemini-image
```

### Sound Designer

Music, voice, and effects that fit the picture. 9 skills.

- **Music and Score** (`scenario-audio`). Try: "Compose a 90-second tense exploration loop and a
  victory sting."
- **Sound Effects for Every Action** (`scenario-sonilo`). Try: "Score this gameplay clip with
  footsteps, a sword clash, and an explosion."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-audio scenario-sonilo scenario-video-assembly scenario-minimax-music scenario-elevenlabs scenario-ace-step
```

### Video Producer

Trailers and clips, storyboarded, generated, cut, and captioned. 33 skills.

- **Cinematic Trailers** (`scenario-video`, `scenario-storyboards`, `scenario-video-assembly`). Try:
  "Storyboard a 30-second trailer from this script, generate the shots, and cut them to music."
- **Captions for Every Platform** (`scenario-caption-studio`, `scenario-formats`). Try: "Add
  word-by-word captions to this video and export 9:16, 1:1, and 16:9 versions."
- **Lyric Videos** (`scenario-kinetic-music-video`). Try: "Turn this song into a vertical
  kinetic-typography lyric video."
- **Takes Before Finals** (`scenario-seedance-drafts`). Try: "Draft five takes of this shot cheaply,
  review them, and finish only the best one at 1080p."
- **Trend Reel Recasts** (`scenario-reel-recast`). Try: "Recreate this trending dance reel with our
  character from her sheet, same moves and song, in a redecorated room."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-video scenario-storyboards scenario-video-assembly scenario-caption-studio scenario-formats scenario-image scenario-image-editing scenario-text-overlay scenario-video-editing scenario-seedance-music-video scenario-seedance-storyboard scenario-seedance-drafts scenario-reel-recast scenario-video-ads scenario-consistency scenario-asset-analysis scenario-minimax-video scenario-gemini-omni scenario-grok-imagine-video scenario-veo scenario-seedance scenario-kling scenario-vidu scenario-wan scenario-runway scenario-luma-video scenario-ad-variants scenario-thumbnails scenario-kinetic-music-video scenario-ace-step
```

### Marketing Artist

Store art and ads that stay on brand at every size. 26 skills.

- **Store Art for Every Platform** (`scenario-formats`, `scenario-brand-kit`,
  `scenario-text-overlay`). Try: "Turn this key art into every storefront size, with our logo and
  the game's title."
- **Ads From One Shot** (`scenario-product-shots`, `scenario-video-ads`, `scenario-ugc`). Try: "From
  this product shot, make a 15-second video ad and three UGC-style variants."
- **Campaign Variants** (`scenario-ad-variants`). Try: "Make three hook-copy variants from this
  gameplay clip, preserving its action and audio."
- **Video Thumbnails** (`scenario-thumbnails`). Try: "Make a readable boss-fight thumbnail with this
  character reference and the exact headline ONE HIT LEFT."
- **Fan-Cam Moments** (`scenario-fan-cam`). Try: "Put the person in this photo on the stadium
  jumbotron, cheering, then animate it."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-formats scenario-brand-kit scenario-text-overlay scenario-product-shots scenario-video-ads scenario-ugc scenario-inspiration scenario-image scenario-image-editing scenario-video scenario-video-editing scenario-audio scenario-video-assembly scenario-consistency scenario-asset-analysis scenario-veo scenario-seedance scenario-kling scenario-elevenlabs scenario-ad-variants scenario-thumbnails scenario-fan-cam scenario-photoshop
```

Working in Photoshop? Add the expert tools for it: [Photoshop](skills/dcc/photoshop/README.md).

### Technical Director

Repeatable pipelines the whole team can run. 5 skills.

- **Workflows Rebuilt From ComfyUI** (`scenario-workflow-authoring`). Try: "Rebuild this ComfyUI
  graph as a Scenario workflow and publish it as an app."
- **Custom Pipelines** (`scenario-workflows`). Try: "Run our sketch-to-final workflow on these 20
  sketches and collect the results."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-workflow-authoring scenario-workflows
```

Working in Unreal Engine, Unity, or Godot? Add the expert tools for it:
[Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md),
[Godot](skills/game-engines/godot/README.md).

### Producer

The right model at the right cost, and spend under control. 8 skills.

- **Model Bake-Offs With Cost** (`scenario-model-comparison`). Try: "Compare three image models on
  this brief, with quality and credit cost side by side."
- **Team Budgets** (`scenario-admin-analytics`, `scenario-team-admin`). Try: "Show last month's
  credit use by project, and cap each freelancer's spend."

```bash
npx skills add scenario-labs/skills --skill scenario scenario-moderation scenario-report scenario-model-comparison scenario-admin-analytics scenario-team-admin scenario-video-editing scenario-refine-loop
```

### Game Developer

Gameplay, UI, animation, performance, and mobile or Web builds, driven inside the engine. These are
expert tools: each family installs as one set, with its command in the family README:
[Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md),
[Godot](skills/game-engines/godot/README.md).

## By goal

### Game art and 3D

Sprites, tilesets, textures, skyboxes, 3D props, and walkable spaces in one consistent style. 23
skills.

```bash
npx skills add scenario-labs/skills --skill scenario scenario-game-assets scenario-sprite-animation scenario-side-view-game-kit scenario-blender-2d-animation scenario-textures scenario-skyboxes scenario-3d scenario-image scenario-patina-retexture scenario-walkable-room scenario-video scenario-consistency scenario-model-training scenario-refine-loop scenario-moderation scenario-meshy scenario-rodin scenario-sparc3d scenario-3d-worlds scenario-gemini-image scenario-audio scenario-sonilo
```

### Marketing and brand visuals

One product shot and a brief turned into on-brand stills, ads, UGC videos, and every placement size.
23 skills.

```bash
npx skills add scenario-labs/skills --skill scenario scenario-product-shots scenario-brand-kit scenario-video-ads scenario-ugc scenario-formats scenario-inspiration scenario-image scenario-image-editing scenario-text-overlay scenario-video scenario-video-editing scenario-audio scenario-video-assembly scenario-consistency scenario-asset-analysis scenario-veo scenario-seedance scenario-kling scenario-elevenlabs scenario-ad-variants scenario-thumbnails scenario-photoshop
```

### Video, music video, and audio

Video made, edited, and scored, from a single clip to a whole-song music video, with voice, music,
and sound effects. 26 skills.

```bash
npx skills add scenario-labs/skills --skill scenario scenario-video scenario-video-editing scenario-audio scenario-video-assembly scenario-image-editing scenario-text-overlay scenario-seedance-music-video scenario-seedance-drafts scenario-reel-recast scenario-image scenario-kinetic-music-video scenario-minimax-video scenario-gemini-omni scenario-grok-imagine-video scenario-veo scenario-seedance scenario-kling scenario-vidu scenario-wan scenario-runway scenario-luma-video scenario-minimax-music scenario-elevenlabs scenario-ace-step scenario-sonilo
```

### Consistent characters and custom models

One character, product, or style held across a whole set, and a model trained on your own art. 11
skills.

```bash
npx skills add scenario-labs/skills --skill scenario scenario-consistency scenario-identity-library scenario-model-training scenario-image-editing scenario-sprite-animation scenario-video scenario-asset-analysis scenario-quality-gate scenario-seedream scenario-gemini-image
```

### Images and editing

Images generated and edited, exact text overlays, and a sequence storyboarded. 27 skills.

```bash
npx skills add scenario-labs/skills --skill scenario scenario-image scenario-multi-reference scenario-image-editing scenario-text-overlay scenario-storyboards scenario-game-assets scenario-textures scenario-skyboxes scenario-video scenario-video-editing scenario-seedance-storyboard scenario-video-ads scenario-video-assembly scenario-consistency scenario-asset-analysis scenario-gpt-image scenario-mai-image scenario-seedream scenario-gemini-image scenario-reve scenario-ideogram scenario-grok-imagine-image scenario-luma-image scenario-ad-variants scenario-thumbnails scenario-photoshop
```

### ChatGPT and Codex pets

An animated pet hatched from an idea or a photo, or an existing one fixed or restyled, delivered as
a sprite sheet, a GIF, and a Codex package. 3 skills.

```bash
npx skills add scenario-labs/skills --skill scenario scenario-chatgpt-pet-create scenario-chatgpt-pet-update
```

## Expert tools

Teams of skills that drive DCC software and game engines installed on your machine. They need the
application. The Photoshop family and the Blender blockout skill also call the Scenario MCP server;
a few Godot and Unity skills take assets made through it by the Scenario skills. Each family
installs as one set: [ZBrush](skills/dcc/zbrush/README.md), [Blender](skills/dcc/blender/README.md),
[Maya](skills/dcc/maya/README.md), [Photoshop](skills/dcc/photoshop/README.md),
[Unreal Engine](skills/game-engines/unreal/README.md), [Unity](skills/game-engines/unity/README.md),
[Godot](skills/game-engines/godot/README.md).
