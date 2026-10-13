# Scene V14 Modification Summary

## What changed

- Copied V13 into a new V14 folder; earlier stable versions were not overwritten.
- Added a licensed CC0 rigged human GLB body base:
  - `assets/models/human-base-rigged.cc0.glb`
  - 53-bone rig, GLB format, SHA256 recorded.
- Added runtime GLTF loading in the Streamlit-embedded Three.js scene.
- Added V14 licensed-worker rigs for the upper draw worker and lower weaver.
- Kept the V13 procedural worker bodies as fallback if the GLB loader or browser module import fails.
- Added procedural craft clothing overlays on top of the neutral CC0 human body: robe/apron forms and head wraps.
- Added authored bone-pose controls for the licensed models:
  - Upper worker: larger pull-down arms, forearms, hands, torso lean and head response.
  - Lower weaver: seated forward reach, side shift, treadle foot motion, beater-follow body motion and head response.
- Added `docs/YUNJIN_VIDEO_STORYBOARD_V14.md`, a five-beat storyboard for continuous weaving: setup, upper draw, weft insertion, beating, and take-up.
- Preserved the red/gold video-reference loom layer from V13.

## Boundaries preserved

- The app remains `Simulation-driven / Simulated Data`.
- The 3D scene is a teaching reconstruction inspired by Nanjing Yunjin drawloom structure.
- It is not a one-to-one mechanical reconstruction and not craft-verified.
- The cloth motif remains a teaching visual motif, not a real historical Yunjin pattern reconstruction.
- User videos were used only for visual direction and action decomposition; no video asset is bundled or copied.

## Verification

- Added V14 tests for the licensed CC0 GLB marker, model file name, license, SHA256, GLTFLoader integration, and storyboard beats.
