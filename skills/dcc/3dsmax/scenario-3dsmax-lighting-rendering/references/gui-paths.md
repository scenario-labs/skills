# GUI paths: lighting and rendering

For a human, or for an agent driving the interface. Paths come from the videos and docs named; UI
labels change between renderer versions, so read the panel before clicking. Shortcut F10 opens
Render Setup.

## Renderer and color

| Task                                          | Path                                                                                                       | Source                   |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------ |
| See or choose the renderer                    | Render Setup (F10) > Common tab > Assign Renderer, or the Renderer dropdown at the top                     | vray7-render-settings.md |
| Color management mode, rendering space, views | Rendering menu > Color Management, or Customize > Preferences > Color Management                           | dlwDiLsPWgI 00:00:34     |
| Tag one bitmap's color space                  | Bitmap parameters > Color Management group > Color Space, or the Data Image button for Raw                 | dlwDiLsPWgI 00:07:06     |
| Stop OCIO tone-mapping the material editor    | Color Management > Advanced, untick the automatic material editor option                                   | QuJe2j7SHZ0 00:14:10     |
| V-Ray frame buffer OCIO display               | VFB Layers > Display correction > OCIO: input ACEScg, display sRGB, view ACES 1.0 SDR-video; Save in image | qt7FB4UU0qg 00:02:12     |
| Arnold RenderView save with view              | RenderView > Save Image Options > Apply Color Management, View Transform                                   | dlwDiLsPWgI 00:08:54     |

## Lighting pass

| Task                                                 | Path                                                                                                          | Source                                      |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| V-Ray material override                              | Render Setup > V-Ray tab > Global switches > Override mtl; material settings: preserve refraction and opacity | x8H1CNNFPgc 00:02:58                        |
| Arnold shader override and feature switches          | Render Setup > Arnold > Diagnostics tab > Feature Overrides, Shader Override                                  | ZUEnTb6QnD4 frame 00:08:10                  |
| Lock the render view                                 | Render Setup > Common tab, padlock next to View to render                                                     | x8H1CNNFPgc 00:02:26                        |
| Corona lock camera view                              | Render Setup, lock the view before moving the sun                                                             | JmmgSQp6FYI 00:01:15                        |
| V-Ray camera, sun, dome lights                       | V-Ray toolbar icons (physical camera, sun with sky map prompt, dome light)                                    | x8H1CNNFPgc 00:00:15 to 00:01:54            |
| List and switch all lights                           | Light Lister (Tools menu; V-Ray Light Lister on the V-Ray toolbar)                                            | 4MeUNMFxiPE 00:05:16                        |
| HDRI rotation                                        | Material Editor > VRayBitmap > Spherical, Horiz. rotation; or dome light Lock texture to icon and rotate on Z | x8H1CNNFPgc 00:12:10 to 00:13:53            |
| Hide dome from the window view                       | Dome light > Invisible; Environment and Effects (8) > background map                                          | 4MeUNMFxiPE 00:04:02                        |
| Corona: different sky lighting and window background | Render Setup > Scene tab > Scene Environment > override for direct visibility (also reflections, refractions) | _biqhqTpW5c 00:09:29                        |
| Isolate one light (Arnold)                           | Rendering > Arnold RenderView > toolbar Isolate Selected                                                      | ZUEnTb6QnD4 00:06:07                        |
| Interactive Arnold in a viewport (2027.3)            | viewport label menu > Arnold Viewport; flyout for quality, resolution (1/2 default), device                   | lighting-rendering__arnold-viewport-2027.md |

## Sampling and denoise

| Task                                       | Path                                                                                                              | Source                            |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| Corona noise limit, time limit, denoise    | Render Setup > Scene tab > Render stop conditions; Denoising mode and amount                                      | _biqhqTpW5c 00:03:13; 1bOmROFahXU |
| Corona image filter                        | Render Setup > System tab > Image filter (Tent with AI denoise)                                                   | 1bOmROFahXU frame                 |
| Corona advanced sampling                   | Render Setup > Performance tab (leave defaults)                                                                   | corona-performance-tab.md         |
| Corona memory for large finals             | Render Setup > Performance tab > Conserve memory, Automated out-of-core textures; Displacement > Screen size (px) | corona-performance-tab.md         |
| V-Ray image sampler and noise threshold    | Render Setup > V-Ray tab > Image sampler (Bucket or Progressive), Noise threshold                                 | 7Q3GqtJ56OQ 00:01:22              |
| V-Ray light cache                          | Render Setup > GI tab > Light cache subdivs, Mode                                                                 | x8H1CNNFPgc 00:08:39              |
| V-Ray auto exposure, white balance         | Render Setup > V-Ray tab > Camera rollout (needs light cache secondary GI)                                        | x8H1CNNFPgc 00:05:13              |
| Arnold samples, ray depth, GLS, time limit | Render Setup > Arnold Renderer tab > Sampling and Ray Depth; Render Time Limit (Production) > Frame Time Limit    | arnold-sampling-ray-depth.md      |
| Arnold flags per object                    | Modify panel > Arnold Properties modifier (not Object Properties)                                                 | ZUEnTb6QnD4 00:18:23              |
| Arnold Live Report                         | Arnold RenderView toolbar > Log icon > Live Report tab                                                            | maxtoa-5-9-whats-new-2027.md      |

## Elements and post

| Task                                                        | Path                                                                                                                            | Source                                          |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Add render elements                                         | Render Setup > Render Elements tab > Add (VRayLightMix, VRayCryptomatte, VRayDenoiser; CShading_LightMix, CShading_LightSelect) | x8H1CNNFPgc 00:08:07; corona-lightmix.md        |
| Corona LightMix in one step                                 | Render Setup > Scene tab > General Settings > Setup (Interactive) LightMix                                                      | _biqhqTpW5c 00:01:18                            |
| Arnold AOVs and light groups                                | Arnold menu > AOV Manager (Render Setup > AOVs tab)                                                                             | ZUEnTb6QnD4                                     |
| V-Ray LightMix sliders, solo, Kelvin                        | VFB > Layers > Source: LightMix; Alt-click a light to solo; To Scene after render stops                                         | 4MeUNMFxiPE 00:06:07; vray7-vraylightmix.md     |
| Corona LightMix                                             | Corona VFB right panel > LightMix tab                                                                                           | corona-lightmix.md                              |
| Corona LightMix to scene lights (V-Ray To Scene equivalent) | Corona VFB > LightMix tab > button below the light list that bakes current colors and intensities into the scene lights         | corona-lightmix.md, Usage Workflow              |
| Corona resume a stopped render                              | Corona VFB settings: untick Clear VFB between renders before stopping                                                           | _biqhqTpW5c 00:13:34                            |
| Cryptomatte-masked correction                               | VFB layer > mask from Cryptomatte click                                                                                         | x8H1CNNFPgc 00:10:15                            |
| Lens effects                                                | VFB > Lens Effects layer (bloom, glare, threshold, scratches)                                                                   | 4MeUNMFxiPE 00:06:53                            |
| VFB history and A/B compare                                 | VFB History (H), enable in settings (S); up to four compare slots                                                               | x8H1CNNFPgc 00:11:24; vray7-vfb-frame-buffer.md |
| Save the light mix look                                     | VFB > save .vfbl (all layers) or light mix preset only                                                                          | 4MeUNMFxiPE 00:07:35                            |
| Set DOF focus                                               | VFB right-click > Set Focus                                                                                                     | dB4975f2yRc 00:05:28                            |
| Save at half size                                           | Corona VFB > Save dropdown > Save 50% (Corona 14 preview label)                                                                 | 1bOmROFahXU                                     |
| Separate render channels to EXR                             | Render Setup > V-Ray tab > Frame buffer > V-Ray raw image file or Separate render channels, OpenEXR                             | 7Q3GqtJ56OQ 00:06:18                            |

## Animation

| Task                            | Path                                                                                                                                                | Source                    |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Frame range                     | Render Setup > Common > Time Output > Active Time Segment or Range                                                                                  | 7Q3GqtJ56OQ 00:00:49      |
| V-Ray pre-pass                  | Global switches (advanced) > Don't render final image; Irradiance map Mode Multiframe incremental, Auto save; Light cache Mode Animation, Auto save | 7Q3GqtJ56OQ 00:04:13      |
| V-Ray final from cache          | Irradiance map Mode From file; Light cache Mode From file; untick Don't render final image                                                          | 7Q3GqtJ56OQ 00:06:18      |
| Corona flicker-free cache       | Performance tab > UHD Cache preset Animation (flicker-free)                                                                                         | corona-performance-tab.md |
| Batch several cameras or states | Rendering > Batch Render                                                                                                                            | hz07nIgm7EA               |
