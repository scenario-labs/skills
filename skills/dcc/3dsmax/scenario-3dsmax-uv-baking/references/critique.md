# Critique rubric: judge your own UVs, mapping and bakes

Score each line pass, warn or fail, and report the numbers. A fail blocks delivery; a warn needs a
sentence of reason in the report. Thresholds marked [added] are this skill's defaults; replace them
with the project's numbers when given.

## 1. UV layout (from P1 `uv_audit`)

| Check                                              | Pass                                                                            | Fail                                              | Source                                   |
| -------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------- |
| UVs exist on every channel a material or bake uses | `uv.missing` absent                                                             | any node without support                          | UVW Map doc ("Missing Map Coordinates")  |
| Cross-shell overlap on a bake channel              | 0%                                                                              | > 0% not explained by mirrored halves offset on W | TS doc, 2IhYmRsKZ4Q 00:00:00             |
| Flipped faces                                      | 0, or only inside intended mirrored shells                                      | scattered flipped faces                           | TS doc (tangent flares)                  |
| Texel density spread                               | all shells within ±15% of target [added], hero areas above by choice            | unexplained outliers                              | sR1sAWWT2x8 00:09:13                     |
| Target matches camera class                        | 20.48 / 10.24 / 5.12 / 2.56 px/cm                                               | no target stated                                  | sR1sAWWT2x8 00:12:28                     |
| Min gap between shells                             | ≥ 8 px at 2048 (scale with size)                                                | < 4 px at 2048                                    | 2gv1jYDAoJc 00:14:46                     |
| UV coverage                                        | ≥ 75% shipped game asset                                                        | < 50% with no plan (non-square, atlas, soft TD)   | sR1sAWWT2x8 00:16:44                     |
| Outside 0-1                                        | none on single-tile assets                                                      | samples outside without UDIM                      | BTT doc (UDIM)                           |
| Lightmap channel                                   | 0 overlap, 0 mirrored; absent and import generation off for Lumen-only lighting | any overlap                                       | game-assets digest; qsV4k09kPV8 00:03:32 |
| Node scale before measuring                        | 1, 1, 1                                                                         | other (areas wrong)                               | [added]                                  |

## 2. Checker capture (P2)

Look at the contact sheet of persp, front, left and top:

- Squares are square on every part (no stretch). Fail: rectangles or fans.
- Square size matches across parts. Fail: one part visibly coarser, unless it is hidden or
  deliberately lower.
- Rows are straight on panels and bands. Warn: wavy rows on grid-like shells: Straighten Selection
  works there (Unwrap UVW doc).
- Seams sit on hidden edges or real breaks (sewing lines, panel gaps). Warn: a seam across a visible
  flat face.
- Checker letters read upright on shells where orientation matters (decals, text, wood grain). Warn
  otherwise.

## 3. Bake setup (before baking)

| Check                                            | Pass                                                                                                  | Source                   |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ------------------------ |
| Every queued map `bakeable` true, `frozen` false | all                                                                                                   | MBT                      |
| Image Size equals the planned texture size       | equal                                                                                                 | 2gv1jYDAoJc 00:21:12     |
| edgePadding                                      | ≥ 2 (BTT default); 8 at 2K for engine maps [added from the 8 px rule]                                 | 2IhYmRsKZ4Q, 2gv1jYDAoJc |
| Projection method fits alignment                 | Raytrace when aligned, Cage when not, UV Match when not overlapping in space                          | BTT doc                  |
| Max Ray Distance                                 | measured or 10.0 checked by a diagnostic pass                                                         | -SMLc0od_5Y 00:01:38     |
| Normal options                                   | Tangent, MikkT on, per-pixel set for the target, Output into Normal Bump off for PBR                  | HL doc, BTT doc          |
| Viewport Normal Bump Mode                        | equals the bake options                                                                               | -SMLc0od_5Y 00:03:19     |
| Low poly stack                                   | no Edit Normals modifier                                                                              | TS doc                   |
| One material on the low poly per texture set     | yes                                                                                                   | 2gv1jYDAoJc 00:20:39     |
| Output To                                        | Create New Material or Duplicate Original (non-destructive)                                           | BTT doc                  |
| Color handling                                   | normals, roughness, metalness, AO, masks as Data Image (Raw)                                          | BTT doc                  |
| Renderer                                         | Arnold for albedo, metalness, roughness and AO; Scanline for legacy Height or Lighting                | BTT doc                  |
| Ray Depth and Sampling                           | minimum needed; renderer filter checked                                                               | BTT doc                  |
| Per-pixel bitangent                              | set from the target's doc, or both variants compared on a test bevel (no source gives Unreal's value) | BTT doc, HL doc          |
| Several high sources in one map                  | `projectionHitOnlyMatchingMatID` true with matching IDs                                               | BTT doc, MBT             |

## 4. Bake result (P9 numbers plus a lit capture)

| Check                                      | Pass                                                                  | Fail                            |
| ------------------------------------------ | --------------------------------------------------------------------- | ------------------------------- |
| Diagnostic color pixels (`diag_color_pct`) | 0 on the final                                                        | any                             |
| Tangent normal mean                        | near (0.5, 0.5, 1.0)                                                  | off by more than 0.08 in R or G |
| Negative-Z pixels (`neg_z_pct`)            | < 0.5%                                                                | more (misses or inversion)      |
| File set                                   | every planned map, planned size, PNG or TIFF at the planned bit depth | missing or resized              |

In the lit capture of the low poly with the baked material, rotate the light or view through 2 or 3
angles:

- No reddish or bluish flare on one side of a seam. A flare means flipped tangent UVs.
- No visible line along UV seams or hard edges.
- Cylinder ends keep their detail. Lost detail means parallel rays.
- No neighbor parts printed in, and no doubled edges. Either means the cage is too far.
- Bevels catch light on the same side as the high poly. Otherwise the green channel convention is
  wrong.
- AO has no contact shadows from parts that are not there in the game.
- A hard line where two separate parts intersect is expected to survive the bake: report it, or
  merge and soften (2gv1jYDAoJc 00:23:26).

## 5. Archviz mapping (P5, P10)

- Real-World Map Size is on in both the modifier and the bitmap, or off in both.
- A 1 m reference box next to the surface matches plank and course size in a render.
- No recognizable repeat in a top-down orthographic render and in a grazing view along the longest
  wall [added].
- No visible triplanar seams on corners. Raise blend if needed, but too much blurs (CTP doc).
- Normal and bump follow the base color: same randomizer or linked master on every channel.
- No rotation on the normal-map path unless the render shows correct lighting (6FalgHWkhKE
  00:07:43).
- Judged in an interactive render, never in the viewport (CMR, CTP docs).
- Step values set for the renderer in use: Corona Step is an increment, V-Ray Step a number of steps
  (CMR, VUR docs).
- Linked VRayBitmaps: blur lowered on the normal bitmap (6FalgHWkhKE 00:13:02).

## 6. Report

A finished report lists:

- Strategy chosen and why.
- Per-node numbers (shells, density target and spread, coverage, min gap, overlap).
- Bake settings.
- Files with sizes.
- For Unreal FBX: which maps need wiring by hand (only Color and Normal connect; AO is not imported,
  Unreal FBX doc).
- Captures read.
- Every `[verify]` name used and whether P0 confirmed it.
- What stays GUI work for a human.
