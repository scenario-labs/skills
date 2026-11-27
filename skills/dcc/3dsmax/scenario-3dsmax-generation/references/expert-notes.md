# Expert notes: generation in 3ds Max work

Principles and judgment by source, with video id and timestamp. URLs and credentials are in
[sources.md](sources.md). Lines marked [added] are this skill's own inference. Model names and tool
versions are as of the source date and will change: the rules matter, not the names.

## 1. Principles by expert

### Arch Viz Artist (elm00WQ03vw, 3D to final image with an open image model and a hosted image-edit model, Corona)

- Building geometry stays under the artist's control and comes from the 3D render; AI supplies mood,
  context, vegetation, atmosphere, "like traditional matte painting" (00:04:05, 00:05:14).
- Render a simple base: clay with simple grass and scattered trees is enough as input (00:01:45).
- Match light direction and intensity in 3D to the chosen AI mood before the final render
  (00:04:05).
- Keep the render's glass and use ID masks for the building over the AI image (00:05:14, 00:07:05).
- Crop detail crops to a common aspect (4:3) before sending them to the model (00:06:02).
- The open model used there holds to about 2 MP and is artifact-free near 1.5 MP;
  scale-to-total-pixels shifts the image, fixed with small local inpaints (00:02:09, 00:08:33). The
  model-specific limit dates fast; the lesson is to know each model's pixel ceiling from its schema.

### Chaos Corona official (2WmOd4C5r7s, Corona plus Veras)

- AI at four moments: concept and mood from a rough render, material tests on the render, texture
  generation, post-render changes; the scene is still built by hand (00:02:10, 00:11:22).
- The prompt forbids geometry change explicitly (00:01:04).
- 1K for ideation, 2K for textures (00:06:38).
- Low-resolution AI images go on a moodboard so the client controls mood without details hard to
  match in 3D (00:02:10).
- Seamless texture, then normal, height and roughness derived from the diffuse (00:06:03 to
  00:07:12).

### Nuno Silva (i3UbOzrAgLk, seamless PBR sets)

- The simplest prompt wins for seamless textures; long prompts produced seams; prompt rewriting
  switched off (00:02:27, frame 00:04:32).
- Height map prompts need "medium contrast" (00:08:36).
- Test tiling with a pattern preview; fix with a half offset plus mask or a low-resolution fill
  (00:05:01, 00:06:05).
- Download from a library when the material exists; generate for the custom or variant case
  (00:10:27).

### renderdrop (1A7uOdk9Sng, video from archviz stills)

- Start frame only to steer a camera move; start plus end frame for a transformation that must hold
  geometry; multi-shot for cuts in one generation (00:00:00).
- Walls and windows must be identical between start and end frames, or the transformation breaks
  (00:02:50, 00:05:50).
- One generation per transition; multi-shot season transitions failed (00:02:35, 00:05:15).
- Crane is the most reliable move for architecture; FPV can switch lens mid-clip (00:00:46,
  00:01:20).
- Insert people in the start frame with an image model before animating; body-to-furniture contact
  is the weak point (00:07:26, 00:09:05).

### Top 3D AI (O6G6taj5M14, fixing AI-generated 3D, Blender)

- Face orientation overlay exposes holes and double shells; inflate then voxel remesh fixes them
  (00:03:35, 00:04:07).
- Parts generated separately give more detail and rig better; whole objects are faster. Deciding
  condition: hero or rigged character versus background prop (00:01:30).
- AI retopology for speed, decimate for props that keep detail, hand retopology for deforming loops
  (00:09:53, 00:11:51).
- AI UVs are the weakest output: quick automatic unwrap, or seams plus unwrap and pack; check
  stretch (00:12:46).
- After any mesh rework, regenerate or rebake the texture with the original UVs and input images
  (00:20:13, 00:20:45).
- Mixamo wants OBJ under about 700k polygons; raw assembled AI characters were 3 to 5 million
  (00:21:37, 00:22:41).

### Matt Hallett (j2qd-kLQY1Q, tyDiffusionTexGen)

- TexGen replaces UV channel 1: move the original mapping to channel 2 first (00:04:49).
- Image-to-image at denoise 0.5 from the textured viewport for unusual subjects; text alone
  misidentifies parts (00:01:36).
- An upscaler adds pixels, not detail (00:09:30).

### Jonas Noell (D-1Vy864PtQ, tyDiffusion basics)

- Depth plus Canny ControlNets at 0.5 each gave better quality than one at 1.0; 1.0 reproduces the
  scene exactly. Deciding condition: faithful match to a fixed camera versus mood exploration
  (00:11:11, 00:12:17).
- Projection of an AI image onto geometry works only for far, view-locked elements (00:16:40).

### VizAcademy UK (zARHVN_XN4U, tyDiffusion live test)

- AI is useful for ideation, backgrounds, people and surface detail; not yet trusted for foreground
  hero detail or delivery without correction (01:02:36).
- Generation resolution is separate from render size: match the aspect (00:26:33).
- Proxies, hidden helpers, glass in windows and edged faces confuse the model: use full geometry
  (00:24:34, 00:28:47).
- Corona wire-color mask plus a white clay render is the control kit; AI fabrics blended into the
  real render at 50 to 60 percent (00:31:19, 00:39:27, 00:40:48).

### Arch Viz Artist (y2-zbS5n8Ps, Chaos AI Enhancer test)

- Low creativity is the reliable setting (00:02:44).
- Pavement responds best; glass, fabric and foggy brick poorly (00:05:07, 00:06:00, 00:06:31).

### Forever Stu (kBo57xFC3ic, agent builds an interior through an MCP bridge)

- Stage-gated agent work: shell, openings, trim, furniture, materials, lights, cameras; moodboard
  only after geometry is approved (00:03:44, 00:06:07).
- Review in orthographic top view with control dimensions, never one perspective (00:08:50).
- Delegating art direction and lighting to the agent failed; technical rules succeeded (00:14:06,
  00:29:50).
- An ornament from one photo through an image-to-3D tool was "quite good for a test", uneven,
  needing more angles (00:19:45 to 00:21:16).

### Arch Viz Artist (UuWmWAvB4Y0, agent drives 3ds Max through Max Ultra MCP)

- The agent is good at setup (materials, scatter, light rig, tools) and wrong on compositions and
  planting (00:03:16, 00:05:29).
- Attach a marked-up screenshot; state "preserve scene, new layer, editable, do not render"; refuse
  claims of verification without viewing (00:04:20).
- The agent built a procedural noise bump where real maps were needed (00:08:11): generated PBR maps
  fill that gap [added].

### Arch Viz Artist (c3acjyR7j7E, agents model from CAD drawings)

- The stated need is accuracy to drawings; generation fits only as a concept layer (00:03:11 to
  00:04:28).
- Client revisions can be previewed by image edit on the final render before the scene changes
  (00:07:13 to 00:08:59).
- State the renderer and material class in every agent prompt, or the agent defaults to Physical
  Material (00:05:02).
- End with a list of assumptions where inputs were missing (00:04:28).

### Autodesk (aPc02tZzj8c, units) and Ghost Pig (z1ws_LOo9AU, FBX axes and pivots)

- Far from the origin, cameras twitch and normals flip; imported models are the usual culprit
  (aPc02tZzj8c 00:08:04). Generated meshes arrive with arbitrary scale and origin [added].
- Pivot and position at 0,0,0 for export; Reset XForm and center pivot as the last step (z1ws_LOo9AU
  00:00:33 to 00:01:06).

### render.camp (64vzHYEWedI) and Eloi Andaluz (I6QPVe8c7jU)

- "As little AI as possible" on final images; more for concepts, test designs and cameras
  (64vzHYEWedI 01:58:53).
- Showing the raw render next to the AI result lets a reviewer judge the AI share (I6QPVe8c7jU 13:43
  to 14:15).

### Color space (Autodesk dlwDiLsPWgI; QuJe2j7SHZ0; aHgu1dwjzSo)

- Base color sRGB; normal, roughness, gloss, metalness, height, masks Raw or None; HDRI linear
  (QuJe2j7SHZ0 00:06:39 to 00:07:11; aHgu1dwjzSo 00:03:59).
- Under OCIO an EXR normal map can be auto-labeled scene-linear: set Raw (dlwDiLsPWgI 00:07:07).
- V-Ray auto-fixes a normal map's space but not a roughness map's (QuJe2j7SHZ0 00:03:12 to
  00:03:45).

## 2. Where generation fits, with the refusal condition

Counts are distinct tutorial videos, among those studied for this team of skills, that show the
manual step; they measure teaching material, not demand.

| Use                                 | Videos | Manual step today                                 | Expert would refuse when                                                        | Evidence                                                |
| ----------------------------------- | ------ | ------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Seamless PBR textures, missing maps | 62     | buying sets, gloss or roughness made in Photoshop | the material exists in a tested library; a supplier sample must match           | i3UbOzrAgLk 00:10:27; aHgu1dwjzSo 00:03:27              |
| Props, furniture, decor             | 30     | buying, merging, unit and pivot fixing            | client-specified catalog product; pieces built from drawings                    | c3acjyR7j7E 00:09:17; mbi-7pTItcU frame 01:24:18        |
| Render enhancement, upscale         | 29     | retouch, long renders                             | glass, reflections, foreground hero detail; lost fine reflections after denoise | elm00WQ03vw 00:07:05; 1bOmROFahXU; zARHVN_XN4U 01:02:36 |
| Concept, mood, references           | 25     | web search, moodboards                            | used as design documentation                                                    | 2WmOd4C5r7s 00:02:10                                    |
| Video from still or playblast       | 19     | camera moves built by hand, farm renders          | geometry differs between start and end frames                                   | 1A7uOdk9Sng 00:02:50                                    |
| Masks, decals, grunge, cutouts      | 18     | Photoshop authoring, downloads                    | [added] none recorded                                                           | 64vzHYEWedI 01:25:36                                    |
| Retopology, UVs, LODs               | 16     | manual reduction and unwrap                       | deforming characters needing loops                                              | O6G6taj5M14 00:11:51                                    |
| Vegetation                          | 15     | species packs                                     | a planting schedule fixes species and growth [added]                            | iIYYzosZ1Mo 00:05:51                                    |
| Client variants by image edit       | 14     | re-render per option, recolor in post             | the change is lighting or geometry: re-render                                   | IuQ7QnwSwL0 00:10:44; c3acjyR7j7E 00:07:13              |
| HDRI, sky, 360                      | 13     | browsing and rotating HDRIs                       | light must be physically exact or measured                                      | [added]                                                 |
| Backplates                          | 13     | stock plates, photo extension                     | real site context must be accurate                                              | iIYYzosZ1Mo 00:00:29                                    |
| People and entourage                | 11     | libraries, compositing                            | near-camera people: hands and contact are weak                                  | 1A7uOdk9Sng 00:09:05                                    |
| Mocap, motion                       | 9      | hand keys, mocap cleanup                          | contact cleanup still needed (about 50 minutes in one test)                     | WUELGPaQu8o 00:20:57                                    |
| Auto-rig, skin                      | 8      | Biped fitting and skinning                        | a Biped or CAT rig is the studio standard                                       | Pgzy2_HxH2w 00:31:12                                    |
| Gaussian splat environments         | 1      | scan shoots                                       | release before 2027.2; site accuracy                                            | YB330UhrdOA 00:34                                       |

Policy signal: Chaos generative features can be switched off by environment variable, and tyFlow's
too; studios may forbid generation on client work. Ask before generating on a client project.

## 3. What Scenario outputs today (read 2026-11-24, re-check each session)

From a read of the Scenario skills and the live catalog through the Scenario MCP (`recommend`,
`search`, `model_schema_get`). Availability differs per team and region; model names rotate.

- 3D: Scenario's own 3D models expose `outputFormat` (glb, fbx, obj, usdz, stl, ply, blend),
  `faceBudget` 1,000 to 2,000,000 triangles, and `topology` triangles or quads; with quads requested
  as GLB the run fails, so ask FBX. Third-party image-to-3D families exposed no output-format field:
  the delivered format is not confirmed by their schemas.
- Retexture, remesh, UV unwrap and rigging are separate `3d23d` steps on a finished mesh
  (`scenario-3d`). Rig output is GLB or FBX and most descriptions do not say which.
- Textures: Scenario's seamless texture model gives a color map only (seam erase, up to 3840 px,
  multiples of 16); other channels authored locally are approximations and must be labeled so
  (`scenario-textures`). A PBR material model generates basecolor, normal, roughness, metalness and
  height, 512 to 2048 px, upscale x2 or x4. Map file type and bit depth: not confirmed.
- Skyboxes: equirectangular 2:1 from dedicated skybox models; generic image models break the wrap. A
  seam-preserving skybox upscaler exists. A skybox-to-HDRI conversion model converts a standard
  skybox into `.exr` and `.hdr` (and optional cubemap layouts); whether the values hold real light
  above 1.0 is not confirmed.
- Worlds: the world model writes `.spz`; one splat model writes an `.spz` preview plus `.ply`; one
  single-object model writes `.ply`. The world model's tiers share inputs and `seed`, so draft
  cheaply, then rerun the same parameters on a higher tier (`scenario-3d-worlds`).
- Images: PNG by default from `asset_download`; webp and jpg on request. Transparency needs a
  background field or a background-removal model (`scenario-image`).
- Video: the video models read outputs mp4 or mov; edit mode takes reference videos. Whether 3ds Max
  plays them as textures or viewport backgrounds is not confirmed.
- Not confirmed for 3ds Max: what the native glTF importer does with a Scenario GLB's units, axis
  and embedded textures; whether 3ds Max reads the world model's SPZ version and Scenario's PLY
  layout. Treat both as checks on the first landing of each type.
