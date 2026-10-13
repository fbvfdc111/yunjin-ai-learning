# Scene V16 Modification Summary

## Why V16 was needed

The V15 licensed human model was correctly scaled, but the body still read wrong in close-up: the anatomical base could appear unclothed from the rear, and the upper operator posture did not match a Dahua Lou loom operator seated on the upper platform. The continuous loop also still felt segmented because action windows were too isolated.

## What changed

- Copied V15 into a new V16 folder; earlier versions were not overwritten.
- Reworked the licensed workers as clothed teaching figures:
  - The GLB body material is now robe/worker-clothing colored instead of skin colored.
  - Added full robe, front apron, back apron, sleeves and head wrap overlays.
  - Added an explicit no-nude rear silhouette marker and coverage geometry.
- Changed the upper worker into a seated upper pattern operator:
  - Added upper side seat, foot board and guard rails.
  - Posed upper legs as seated instead of standing.
  - Rotated the licensed body to face the loom rather than present a rear-facing pose.
- Revised the loom toward the user's reference image:
  - Added taller outer tower posts.
  - Added upper pattern tower side posts.
  - Added an upper pattern-control block bank.
  - Added a full-height vertical warp curtain.
- Smoothed the action timeline:
  - Extended the loop to about 45 seconds.
  - Increased overlap between draw, shed, shuttle, beater and take-up.
  - Added a persistent browser animation epoch so iframe refreshes continue the same timeline instead of visually restarting.

## Boundaries preserved

- The app remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching reconstruction inspired by Dahua Lou structure, not a dimensionally accurate mechanical reconstruction.
- The cloth motif remains a teaching visual motif, not a historical Nanjing Yunjin pattern reconstruction.
- User images/videos are used only as visual direction; no reference media is bundled or copied.
