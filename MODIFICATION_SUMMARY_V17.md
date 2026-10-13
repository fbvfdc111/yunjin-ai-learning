# Scene V17 Modification Summary

## Why V17 was needed

V16 still showed two problems in the user's screenshot:

- The moving character could flicker because the browser loaded the GLB asynchronously and swapped visibility after load.
- The worker silhouette still read as a covered blob rather than a clearly articulated person.

The user also provided a PDF containing a real Dahua Lou loom photo. Page 7 shows a high multi-level wooden structure, upper operator platform, dense vertical warp curtain, and diagonal upper pattern-control cords.

## What changed

- Copied V16 into a new V17 folder; previous versions were not overwritten.
- Stopped using the asynchronous GLB worker as the visible animated character.
  - The CC0 GLB asset remains bundled and licensed.
  - Visible workers now use stable procedural articulated bodies to avoid flicker.
- Reworked both workers as clothed, segmented teaching figures:
  - Added front/back cloth panels, visible sleeves and no-nude rear silhouette coverage.
  - Kept visible head, torso, arms, forearms, wrists, hands, legs and feet.
  - Upper pattern operator is seated on the upper platform and faces the loom.
- Added PDF-based loom structure cues:
  - Diagonal pattern-control cords from the upper pattern tower.
  - Rooflike upper truss lines.
  - Taller outer frame and full-height vertical warp curtain retained from V16.
- Kept the persistent animation clock and overlapped 45-second timeline to reduce hard cuts and iframe refresh jumps.

## Boundaries preserved

- The app remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching reconstruction inspired by a real Dahua Lou loom image, not a dimensionally accurate mechanical reconstruction.
- The cloth motif remains a teaching visual motif, not a historical Nanjing Yunjin pattern reconstruction.
- The PDF image is used only as visual reference; no image from the PDF is bundled, copied into the app, or reproduced as an asset.
