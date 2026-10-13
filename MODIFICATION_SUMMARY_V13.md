# Scene V13 Modification Summary

## What changed

- Copied the previous stable V12 WebGL prototype into a new V13 folder; older versions were not overwritten.
- Kept Python/Streamlit as the digital-twin state machine and simulation layer.
- Preserved the six-stage simulation loop, simulated tension/lift signals, Human Coordination status, Dots fallback, CLIP-related app structure, AI探锦, and AI文化助手.
- Reworked the loom visual direction toward the user's video references:
  - Added a red/gold jacquard control wall behind the weaving area.
  - Added rows of gold peg-like nodes and a dense red/gold cord curtain.
  - Added a stronger red silk cloth bed so the weaving area no longer reads as bare wood and loose lines.
- Increased human action readability:
  - The upper draw worker now pulls downward with larger arm, forearm, wrist, head, torso, and body-lean motion.
  - The lower weaver now reaches farther into the cloth area, shifts more visibly side-to-side, presses the treadle more clearly, and leans into the beater/shuttle work.
  - The beater/reed travel, shed opening, cord lift, warp split, shuttle path, and cloth-bed response all have larger visual motion.
- Retimed the WebGL continuous loop from about 18 seconds to about 20 seconds to reduce the feeling of hard jumps between steps.
- Kept V12's continuous documentary camera interpolation, motion memory, action cues, draw-cord flow beads, shed focus band, shuttle path highlight, beater impact edge, and take-up pulse ring.
- Added V13 regression assertions for the new red/gold video-reference loom layer and larger human-motion profile.

## Boundaries preserved

- The prototype remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching visual inspired by high, multi-layer Nanjing Yunjin drawloom structure.
- It is not a dimensionally accurate or one-to-one mechanical reconstruction.
- The cloth motif is a teaching visual motif, not a real historical Nanjing Yunjin pattern reconstruction.
- The user-provided videos were used only as visual reference for composition and action readability; no video asset is downloaded, bundled, copied, or reproduced.

## Key files

- `src/yunjin_ai/digital_twin_3d.py`: Three.js WebGL renderer and state-to-animation mapping.
- `tests/test_phase66_3d_scene_v2.py`: V13 assertions for the WebGL rendering layer, red/gold reference loom features, larger continuous worker motion, continuous cloth, and teaching-boundary labels.
- `ASSET_LICENSES_V13.md`: asset and license notes.
- `WINDOWS_CMD_START.md`: beginner Windows CMD startup steps.

## Verification

- Passed syntax check for `src/yunjin_ai/digital_twin_3d.py`.
- Passed related tests: `tests/test_phase63_live_simulation.py`, `tests/test_phase64_3d_process_twin.py`, `tests/test_phase66_3d_scene_v2.py`.
- Full test run may still report the legacy protected-file/hash and old AI-assistant interaction failures already present in the supplied project history.
