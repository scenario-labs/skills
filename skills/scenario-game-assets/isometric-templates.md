# Isometric templates

These neutral bases separate grid geometry from art direction. Build them with `uv run --with pillow python scripts/build_isometric_templates.py <output-directory>` from this skill directory. Each PNG is 1024 by 1024 pixels. The placement anchor is the ground center at (512, 704), not the image center or bottom edge.

| Template            | Projection                          | Use                             |
| ------------------- | ----------------------------------- | ------------------------------- |
| `diamond-ground-v1` | 2:1 diamond                         | Continuous terrain and paths    |
| `diamond-slab-v1`   | 2:1 diamond, 32 px side             | Raised plots and building bases |
| `hex-ground-v1`     | Regular hex projected at 30 degrees | Hex terrain maps                |
| `hex-slab-v1`       | Same hex, 32 px side                | Raised hex plots                |

The manifest records the ground polygon, two lattice step vectors, anchor, thickness, and file hashes. Do not mix projections in one map. Slab variants are raised objects: continuous flat maps should use ground variants to avoid exposed sides between neighbors.

- `reference`: neutral RGBA base. Composite onto the plain canvas required by the chosen model, preserving size and position.
- `ground-region`: white ground footprint, black outside.
- `side-region`: white visible sides, black elsewhere. Flat templates share one all-black `empty-side-region-v1.png`: no side faces means no editable pixels.
- `object-region`: ground and sides plus 448 px of vertical editing space. This is not an object silhouette or an alpha matte.

Region files describe geometry, not model mask polarity. Convert to the mask convention in the selected model's schema. Retain an unmodified source canvas for measuring edits outside the allowed region. Never feed the labeled contact sheet as a generation reference.

For a small test, generate terrain, a connecting path, and a tree using the same base and a separate style reference. Assemble neighbors with the manifest's step vectors, sorted by ground-anchor Y for simple upright sprites. Check edges and path endpoints at native resolution, the tree's anchor and unobstructed crown, and the whole map at game scale. Bridges and multi-cell objects need their own engine sorting rules. Record camera or silhouette drift before any corrective crop; reject outputs that only look correct after hiding the defect.
