# GUI paths: archviz production

For a human or a computer-use agent. Paths are from the sources' UI (3ds Max 2022 to 2025, V-Ray 6
and 7, Corona 9 to 13); 2027 layouts may differ, so search by name (X key search) when a menu moved.

## Intake link presets (P0)

| Step                          | Path                                                                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Link a Revit, FBX or DWG file | File > Import > Link Revit, Link FBX or Link AutoCAD                                                                          |
| Edit a Revit or FBX preset    | File > References > Manage Links > Presets tab > select preset > Modify                                                       |
| Reload with options           | Manage Links > Files tab > select file > Show Reload Options > Reload                                                         |
| Preset fields                 | Combine Entities (preset only); Objects: Lights, Daylight System, Cameras; Material: Use Scene Material Assignments on Reload |
| DWG units                     | Link AutoCAD > Rescale on, Incoming File Units                                                                                |

## Cameras and composition

| Step                            | Path                                                                                         |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| Create a Physical camera        | Create > Cameras > Physical                                                                  |
| Create a Corona or V-Ray camera | Create > Cameras > Corona Camera; V-Ray toolbar camera icon                                  |
| Camera view                     | select camera, press C                                                                       |
| Focal length instead of FOV     | camera Modify panel > lens: Specify FOV off, Focal Length (mm) [verify]                      |
| Two-point perspective           | camera Modify panel > Perspective Control > Auto Vertical Tilt Correction [verify]           |
| Safe frame                      | Shift+F                                                                                      |
| Composition overlay             | Image Comp Helper or a composition script (JmmgSQp6FYI); Vantage: composition guides overlay |
| Camera Lister (V-Ray)           | V-Ray toolbar > Camera Lister                                                                |
| Lock IPR to camera              | Render Setup > Common > lock the view before steering the sun                                |

## Light and look (detail in the sibling skills)

| Step                           | Path                                                                             |
| ------------------------------ | -------------------------------------------------------------------------------- |
| HDRI in environment            | Rendering > Environment > Environment Map slot (Corona Bitmap or VRayBitmap)     |
| Separate visible background    | Render Setup > Scene > Direct visibility override, Reflections override (Corona) |
| Light Mix                      | Corona VFB > LightMix tab; V-Ray VFB > Layers                                    |
| Tone mapping                   | Corona VFB > Post; V-Ray VFB > Layers                                            |
| White override for light tests | Render Setup > Scene > Material override, exclude glass                          |

## Scatter

| Step                   | Path                                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Chaos Scatter          | Create > Geometry > Chaos (or Chaos Scatter) > ChaosScatter; Modify > Objects, Scattering, Areas, Camera clipping |
| Chaos Scatter Lister   | Chaos Scatter toolbar, second icon (right-click main toolbar to show it)                                          |
| Cosmos scatter presets | Chaos Cosmos browser > Presets; select the target spline or surface, then Import                                  |
| Forest Pack            | Create > Geometry > iToo Software > Forest Pack Pro; Library Browser button                                       |
| Forest Pack edge       | Areas rollout > Boundary Checking > Edge; Ctrl+click Edge previews in Points-Cloud mode                           |
| Forest Lister          | iToo toolbar or Forest object > Forest Lister [verify]                                                            |
| Forest material        | Geometry rollout > Material Override                                                                              |
| Forest viewport cap    | Display > Viewport > Max Items                                                                                    |
| RailClone              | Create > Geometry > iToo Software > RailClone Pro; Style Editor                                                   |
| Closed spline test     | add Edit Poly on the spline: closed becomes a polygon, open vanishes                                              |
| Pivot to base          | Hierarchy > Affect Pivot Only; Align (Alt+A), X and Y off, minimum Z                                              |

## Assets and people

| Step               | Path                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Chaos Cosmos       | V-Ray toolbar > Chaos Cosmos; or V-Ray menu > Chaos Cosmos browser; drag to viewport, Import places at 0,0,0                            |
| Connecter          | Connecter window > drag asset to viewport > merge in place, XRef, proxy; Replace Target                                                 |
| Anima              | Anima menu > Import project; Anima helper modifier > Background > Add > Send to Anima; Synchronize in Anima; Apply materials in 3ds Max |
| Time Configuration | button near playback controls > Custom fps                                                                                              |

## Aerial

| Step                       | Path                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------- |
| Photo as background        | Views > Viewport Background > Configure Viewport Background > Use File                |
| Horizon line               | camera Modify > Show Horizon Line [verify]                                            |
| Daylight location and time | Daylight System > Motion panel > location, date, time; north direction on the compass |
| Shadow-only object         | right-click > Object Properties > Visible to Camera off, Cast Shadows on              |

## Animation

| Step                 | Path                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Walkthrough          | Animation > Walkthrough Assistant > Pick Path; Normalize Spline modifier on the path                                |
| Rotation easing      | Graph Editors > Curve Editor > Rotation > Set Tangents to Auto                                                      |
| Vantage in viewport  | Render Setup > Common > Assign Renderer > ActiveShade: V-Ray GPU (Vantage build); viewport shading menu: same entry |
| Vantage Live Link    | Vantage toolbar > first icon dropdown > Initiate a Live-Link                                                        |
| Corona to V-Ray      | V-Ray menu > Converters > V-Ray Scene Converter                                                                     |
| Corona 13 to Vantage | Render Setup > System > Vantage Animation Export                                                                    |
| Vantage shots        | Vantage > Video Editor (timeline icon) > Shot Mode; right-click a transition > Linear                               |
| Vantage states       | Vantage right panel: Environment, Lighting, Color corrections > save sub-state; Scene States panel                  |
| Vantage render       | Vantage > Render Setup > Sequence                                                                                   |

## Delivery

| Step            | Path                                                                                                           |
| --------------- | -------------------------------------------------------------------------------------------------------------- |
| Render elements | Render Setup > Render Elements > Add (Cryptomatte, Wire Color, Z-Depth, LightSelect, AI Enhancer in Corona 13) |
| Batch render    | Rendering > Batch Render > Add; set each view's camera here                                                    |
| Missing files   | File > Reference > Asset Tracking                                                                              |
| Archive         | File > Archive [verify]                                                                                        |
