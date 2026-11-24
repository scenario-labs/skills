# AI tools that already live inside 3ds Max

Facts as the saved sources describe them, read on 2026-11-24. No ranking: the right tool is the one
the user already has and that fits the step. Vendor features change often; confirm versions on the
vendor page before quoting one to a user.

Rule for the agent: ask what the user has installed and licensed before proposing a route. If an
in-Max tool already covers the step and the user is used to it, use it and land its output with the
same checks as a Scenario output (scale, color space, provenance). Use the Scenario MCP when the
step needs a model, format or asset type the installed tool does not offer, or when the work runs
outside an open 3ds Max session.

How the agent can drive each one matters as much as what it does: most are GUI panels with no
documented script interface.

## Autodesk

| Tool                                               | What it does in 3ds Max                                                                                                                                     | Agent access                                              | Source                                                                                                                        |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Autodesk Assistant (Tech Preview)                  | 2027: documentation help. 2027.3: "Analyze my scene" and "Do work for me", which runs MAXScript with script preview, one undo step per action, Safe Mode on | Its own chat window; Autodesk's skills run only inside it | `ai-workflows__autodesk-faq-assistant-and-mcp-maya-3dsmax.md`, `ai-workflows__autodesk-assistant-3dsmax-2027.md`, BtqU78NM-yg |
| Autodesk 3ds Max MCP server (Tech Preview, 2027.3) | Lets an external MCP client read the scene and propose MAXScript; off by default; local HTTP with a token; no generation of its own                         | The `mcp-safe` channel in this team                       | `scripting-pipeline__max-mcp-*.md`                                                                                            |
| Connect to Flow Studio button (2027.2)             | Link to Autodesk's cloud toolset; direction and file types through the button not confirmed                                                                 | GUI                                                       | Autodesk 2027.2 what's new                                                                                                    |

Facts that change procedures:

- The Assistant is a cloud service: sign-in and internet required, prompts kept 45 days for
  debugging and service optimization, not used to train third-party models (Autodesk FAQ).
- The Assistant stops after 25 tool steps and checks in after 10 (Autodesk FAQ).
- Neither the Assistant nor the MCP server generates images, textures or 3D.

## Chaos (V-Ray and Corona for 3ds Max)

| Tool                                                        | What it does                                                                                                | Where                                                  | Agent access                                                                                                                                                 |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AI Enhancer                                                 | Cloud pass on a finished render: people, vegetation, large surfaces; per-surface choice; creativity setting | V-Ray Frame Buffer and Corona VFB, through Chaos Cloud | GUI; the render needs its VFB data. V-Ray 7.2 adds a `VRayEnhancerData` render element (MaterialID, ObjectID, depth) that the agent can add before rendering |
| AI Material Generator                                       | Photo of a surface to a tileable PBR material, saved in the Cosmos browser                                  | Chaos Cosmos browser                                   | GUI; options Make tileable and Preserve colors                                                                                                               |
| AI Upscaler                                                 | Render enlargement                                                                                          | Chaos Cloud from the VFB                               | GUI                                                                                                                                                          |
| Veras                                                       | Concept variants, material swaps, people, relight and short video from a VFB capture                        | Corona VFB (Corona 15), V-Ray                          | GUI, cloud                                                                                                                                                   |
| Cosmos AI 3D generation (beta)                              | One image to a 3D asset; image search                                                                       | Cosmos browser                                         | GUI                                                                                                                                                          |
| AI Assistant, Sky Match, Render Critique (V-Ray 7 Update 5) | Settings help, lighting matched to a reference image, render feedback                                       | V-Ray                                                  | GUI                                                                                                                                                          |

Facts that change procedures:

- `CHAOS_DISABLE_GEN_AI=1` disables Chaos generative features on a machine; studios with an AI
  policy may set it (`ai-workflows__cosmos-ai-materials.md`,
  `ai-workflows__vray7-vrayenhancerdata.md`, `ai-workflows__chaos-ai-assistant-3dsmax.md`).
- Chaos features draw on Chaos Credits from the user's Chaos plan.
- Expert test of the Enhancer: low creativity is the reliable setting; pavement responds best, glass
  and fabric poorly (Arch Viz Artist, y2-zbS5n8Ps 00:02:44, 00:06:00).
- Before an Enhancer pass on a scattered scene, give scatter instances unique ObjectIDs (YIPU6qfz8OE
  00:01:19).

## tyFlow: tyDiffusion

| What it does                                                                                                                                                                                                                           | How it runs                                                                                        | Agent access                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Open diffusion image and animation generation driven by the viewport color and depth or the render VFB; ControlNet, IP-Adapter, IC-Light, detailers, upscalers; the tyDiffusionTexGen modifier projects generated images onto geometry | Local: its own node-graph engine on the user's GPU, installed by tyFlow; models downloaded locally | A documented MAXScript interface (`ai-workflows__tydiffusion-maxscript.md`); property names to check against that doc |

Facts that change procedures:

- `TYFLOW_NO_AI=1` disables tyFlow AI features on a machine
  (`ai-workflows__tyflow-faq-ai-tydiffusion.md`).
- Generation resolution is separate from render output size: match the aspect or VRAM goes to unused
  area (VizAcademy UK, zARHVN_XN4U 00:26:33).
- Without the depth ControlNet the model ignores the scene (zARHVN_XN4U 01:00:00); depth plus Canny
  at weight 0.5 each gave better quality than one at 1.0 (Jonas Noell, D-1Vy864PtQ 00:12:17).
- TexGen replaces UV channel 1 with its own unwrap: move the original mapping to channel 2 first
  (Matt Hallett, j2qd-kLQY1Q 00:04:49).
- Local install downloads tens of gigabytes of models; an SSD is recommended (D-1Vy864PtQ 00:04:05).

## Third-party bridges and plugins (from the vendor pages)

| Tool                                                         | What the source says                                                                                                                                  | Landing                                                                                                                                             |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Generation panels docked in 3ds Max                          | Image, video, 3D model, PBR materials and HDRI, retexture, rig, upscale or relight from a panel; typically Windows and recent 3ds Max releases only   | 3D usually lands as FBX; the material class is often not stated on the vendor page                                                                  |
| Web-app bridges for generated 3D                             | Receive models sent from a vendor's web app; no generation inside 3ds Max                                                                             | FBX with a vendor name prefix on objects and a Physical Material built from the textures, when the vendor documents it; a local port on the machine |
| Substance 3D plugin and Connector                            | Sampler sends materials to 3ds Max; plugin 3.1.1 in 2027.3 adds OpenPBR                                                                               | Substance material (Adobe release notes)                                                                                                            |
| Community AI scripts                                         | Photos or text to PBR materials in the material editor, render edits, or a live viewport restyle, each through a cloud model under the user's own key | Materials for the active renderer, or images                                                                                                        |
| Community MCP bridges (3dsmax-mcp, Max Ultra MCP and others) | Run MAXScript or pymxs in a live session for an MCP client; viewport capture                                                                          | The `bridge` channel in this team                                                                                                                   |

When the user already receives assets through a vendor bridge, land them with P4 like a Scenario
file: the bridge imports the file, it does not measure it against a known dimension or record
provenance.
