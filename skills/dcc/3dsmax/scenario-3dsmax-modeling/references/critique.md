# Self-review rubric for modeled parts

Run P9 (procedures.md) first: it returns the numbers and the captures this rubric reads. Score each
part, not the scene. A part passes when every "must" line passes; "should" lines go into the report
to the user with the reason.

Units: distances assume centimeters. Scale them with the system unit.

## 1. Numbers (from `mesh_checks` and `stack_audit`)

| Check                                              | Must                                                                    | Should                                                | Source                                                                    |
| -------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------- |
| Open edges                                         | 0, unless the part is meant open (Cookie, a shell edge left for a seam) | report each open border by count                      | boolean doc (Cookie yields open mesh); Todd D yx-lpHy8yPs 00:05:30        |
| Weldable verts at 0.001 cm                         | 0                                                                       |                                                       | Tim Bergholz tP7FD4l-qus 00:25:57 ("always make sure to weld your verts") |
| N-gons on a subdivided part                        | 0                                                                       | at most a few deliberate poles off the highlight path | Todd D 00:03:19 (one pentagon tolerated)                                  |
| Triangles on curved dense areas                    | allowed                                                                 | none on flats that catch highlights                   | Arrimus fXI2MJ7Bw2k 00:14:25                                              |
| Crease or CreaseSet position                       | below OpenSubdiv                                                        |                                                       | Jake Denham QIPOLr4j3lM 00:12:41                                          |
| FFD position                                       | below TurboSmooth or OpenSubdiv                                         |                                                       | Adam Z 75_n7o0u8sw 00:07:25                                               |
| Poly Select between Chamfer and the next Boolean   | present                                                                 |                                                       | Changsoo TEz7tBiRrXc 00:04:40                                             |
| Chamfer straight on a Boolean (2027)               |                                                                         | Smart Bevel above the Boolean instead                 | Colton lDpcfhxP3qU 00:00:42                                               |
| Chamfer Mitering under subdivision                 | not Tri                                                                 | Quad, Uniform, Patch or Radial                        | chamfer doc (Tri may cause smoothing issues)                              |
| Chamfer from a pre-2023.2 file                     | `SetVersion #VerLatest` applied                                         |                                                       | chamfer doc                                                               |
| Chamfer Limit Effect and amount type               | Limit Effect on; not Legacy on a new model                              |                                                       | chamfer doc (Legacy "not recommended for use with new models")            |
| Hole integrity after a push-through or floater cut | weldable verts 0, open edges 0, no doubled edges around the ring        | Ctrl-double-click ring gives a full circle (GUI)      | Todd D yx-lpHy8yPs 00:04:23, 00:04:55                                     |
| Shell part                                         | open edges 0 after Shell; Shell below the smoother                      |                                                       | QIPOLr4j3lM frame 00:12:40 (stack order)                                  |
| OpenSubdiv viewport iterations                     | at most 2                                                               | 1 while editing                                       | Igor Mota 0jXxaGKuW6Y 00:07:04; opensubdiv doc                            |
| OpenVDB voxel ratio (largest side / voxel)         | 50 to 500 [added]                                                       | near 100 to start                                     | uDfhmKCdR0U 00:12:03; boolean doc                                         |
| Retopology source faces / target                   | at least 2 [added]                                                      |                                                       | Arrimus fXI2MJ7Bw2k 00:17:00                                              |
| Retopology result faces                            | within about 10 percent of target [added]                               |                                                       | Pg2Nm-fwyME frames                                                        |
| Retopology status line                             | no "Calculation failed"                                                 |                                                       | sKEu2Gs3G_U frame 00:01:21                                                |
| Symmetry seam                                      | `mirror_seam_check` returns 0                                           | weld threshold 0.01 cm                                | Tim Bergholz 01:05:28                                                     |
| Dimensions                                         | bounding box within 1 percent of the known real size [added]            |                                                       | Tim Bergholz 00:02:46                                                     |
| Disabled modifiers                                 | none left, or listed in the report                                      |                                                       | fundamentals-scene digest batch2                                          |
| Conform on a heavy mesh (over 500k verts)          |                                                                         | Cache on before saving                                | Changsoo sRLKiz4HSgA 00:05:10                                             |

## 2. Captures (one contact sheet: persp, front, left, top, at subdivision 1 and 2, Edged Faces on)

Look for these, in this order. Each item names the fix.

1. **Silhouette against the reference** (front and left captures beside the reference image). A band
   along one edge means a proportion is off: fix the cage or the FFD, never the subdivided mesh.
2. **Loop continuity around cuts.** Loops should circle each hole; a fan of thin triangles at a
   Boolean seam means retopologize before beveling (Martin Coven HhUMdy-0kSI 00:00:37) or use Smart
   Bevel.
3. **Bevel width.** Even along each edge and at corners. Pinch or width jumps at a corner: Chamfer
   is following topology; switch to Smart Bevel (lDpcfhxP3qU 00:00:42).
4. **Stretching on flats at iteration 2.** A "squashed sphere" look on a creased box means too
   little geometry: add a loop, recrease (Adam Z UpBbEXkqeuw 00:01:42).
5. **Soft corners that should be crisp.** Missing crease or crease above OpenSubdiv; or support
   loops too far from the edge.
6. **Hard ridges that should be soft.** Extra edges added for noise or seams (Adam Z 75_n7o0u8sw
   00:06:52); relax or remove them.
7. **Splotchy shading after Retopology.** The source was too simple (Arrimus 00:17:32). Use a
   high-contrast shaded capture to see it.
8. **Holes or melted detail after OpenVDB.** Voxel too large, or a gap in the source: fix the base
   primitive (Todd D 00:13:46).
9. **Wrinkles (Displace stacks).** No straight outlines at gizmo borders; wrinkles follow the form;
   no obvious repetition across copies (RenderRam ALiGLb6TsS4). Judge on a test render, not the
   viewport.
10. **Spline tubes.** Bends read round at the hero distance; no visible facets from low
    interpolation steps or few sides.
11. **Round openings.** A spout, aerator or ear-cup hole reads as a true circle at iteration 2. A
    lumpy ring means the face loop was not regularized: Loop Regularizer, then Set Flow (Igor Mota
    0jXxaGKuW6Y 00:03:30).
12. **Reflection check on glossy parts.** The sources give no zebra or striped-reflection procedure
    and no threshold. If the part is chrome or lacquer, render it under a striped environment and
    judge stripe continuity by eye [added]; report it as a visual check, not a measured one.

## 3. Non-destructive state

- The stack is readable: each modifier has a purpose you can name. Rename modifiers when a stack has
  several of the same class.
- Anything collapsed was collapsed on a copy, and the copy is in a versioned file (`_v002`).
- The report to the user lists what stays live (splines, Booleans, Symmetry, Chamfer or Smart Bevel,
  OpenSubdiv) and what was frozen (Conform Cache, collapsed copies).

## 4. Report format

One short table per part: check, value, pass or fail, fix applied. Then the contact sheet path.
Never write "verified in 3ds Max" for a code path that has not run there; say which checks ran on
numbers and which on captures.
