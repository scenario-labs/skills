# Critique rubric (scenario-3dsmax-fx)

Score each line pass, warn or fail before showing anything. Look at captures, never at settings
alone. Build contact sheets with the lead's `max_review.contact_sheet()`: key frames before impact,
at impact, plus 10, plus 30, and the last frame.

## Scene and setup

| Check                | Pass                                                             | How                   |
| -------------------- | ---------------------------------------------------------------- | --------------------- |
| Units                | read, not changed; recipe numbers converted if not 1 unit = 1 cm | procedure 1           |
| Scale                | hero objects at real size (a car about 400 cm)                   | stats, bounding boxes |
| Stand-ins            | proxy colliders closed, open edges 0                             | procedure 3           |
| One variable per run | the run log names one changed value per preview                  | agent log             |
| Timeline             | sim range covers the shot plus settle frames                     | procedure 1           |

## Destruction

Measurable:

- Frame 0 equals the modeled wall: no particle moves before contact (compare a capture at frame 0
  and one frame before impact).
- Tier counts logged from the editor; the finest tier holds the fewest particles.
- Final colliders are the hero parts, not the proxy.
- Playback with one display color per event shows particles reaching the intended tier; colors
  removed before the render (GZMWapJe7eM 00:19:17).
- Operators copied between tiers were made unique (no tier shares values by accident). Visual:
- Fragment size grows with distance from the impact. Uniform size means the tiers or Voronoi counts
  are wrong.
- Some chunks stay whole (bind breaking works). All-shattered means the force break is too low.
- Debris settles within about one second and does not slide like paper; sliding means friction is
  too low.
- No isolated pieces flying off at frame 1 of activation (degenerate binds: Joint, Max breaks/frame
  1 or 2, more Position Iterations).
- Inner faces carry the cap material, not the outer one.

## Cloth

Measurable:

- Segment count and collide radius logged; radius below vertex spacing.
- Settled frame: vertex motion near zero over the last 10 frames [added: compare two frozen
  snapshots]. Visual (capture from below, at a grazing angle, and from the camera):
- No collider visible through the cloth; no cloth inside the bed or chair.
- Folds at the scale of a real blanket; no high-frequency crumple from an oversized turbulence.
- No black backfaces (shell present); no stretched checker squares on the UVs.
- Reveal: the pinned point does not drag a spike into the mesh.

## Particles, digging, sand

- No particles below the ground plane (count in the editor at the last frame must be 0).
- No voxel islands left after digging; seam between the hole and the ground invisible in a capture.
- Particle count and cache size logged; Alembic exports capped before they reach tens of GB.

## Fire and smoke

- Render not black; a light exists.
- Fire turns to smoke at a plausible height; no gap at colliders.
- Arnold render versus viewport capture: colors and opacity close (use `max_review.compare`); if
  not, OSL ramps, then re-click the preset.
- Render path licensed: ZENITH rendering and VDB export need tyFlow PRO.

## Cache

- Every frame present, no zero-byte file (`sim_budget.py cache`).
- Keep cache in RAM left on for tyCache modifiers.
- Cache plays in a fresh scene through the right loader (tyCache object for Particle Export; tyCache
  modifier for modifier caches).
- Size and sim time recorded in the report.

## Render

- One low-res frame per key moment rendered and looked at before the sequence.
- Motion blur present on fast debris when the shot needs it (subframe tyCache export since 2.000;
  tyCache modifier "Round to nearest frame" off).
- Arnold: no motion blur noise in the alpha channel; if present, raise Camera (AA), not the other
  samples (lighting-rendering__arnold-removing-noise.md).
- Hair: rendered fibers visible; none through the floor.

## Report honesty

- Say which steps were GUI work done by a person, which values came from sources and which were
  tuned by eye.
- Say "not yet run in 3ds Max" for any script whose result was not returned.
