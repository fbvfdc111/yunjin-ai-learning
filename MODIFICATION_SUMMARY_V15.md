# Scene V15 Modification Summary

## Why V15 was needed

V14 introduced a licensed CC0 rigged human GLB, but the GLB was scaled as if its real-world meter units were millimeters. That made the actual human body nearly invisible, so the procedural clothing overlay dominated the silhouette and could read like a kettle-shaped object. V14 also kept several action beats too short for teaching demonstration.

## What changed

- Copied V14 into a new V15 folder; previous versions were not overwritten.
- Fixed licensed GLB worker scale:
  - Upper draw worker GLB scale changed from `.00066` to `.66`.
  - Lower weaver GLB scale changed from `.00058` to `.58`.
- Reduced the procedural robe/apron/head-wrap overlay size so it reads as clothing on a human body rather than the main body shape.
- Extended the continuous storyboard loop from about 20 seconds to about 33 seconds.
- Added `heldActionWindow`, giving each action a clear rise, hold and exit period.
- Lengthened the visible action beats:
  - Setup/readable posture hold.
  - Upper draw worker pull and warp lift hold.
  - Lower weaver shuttle/weft insertion hold.
  - Beater compression hold.
  - Take-up/cloth-growth hold.
- Kept the V14 licensed GLB asset, CC0 license record, SHA256 verification, procedural loom, red/gold loom visual layer and digital-twin simulation boundaries.

## Boundaries preserved

- The app remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching reconstruction, not a dimensionally accurate mechanical reconstruction.
- The cloth motif remains a teaching visual motif, not a historical Nanjing Yunjin pattern reconstruction.
- User videos are used only for visual direction and action decomposition; no video asset is bundled or copied.
