# Scene V12 Modification Summary

## What changed

- Replaced the former HTML/CSS pseudo-3D scene with a Three.js WebGL scene embedded in the existing Streamlit iframe.
- Kept Python/Streamlit as the digital-twin state machine and simulation layer.
- Preserved the six-stage simulation loop, simulated tension/lift signals, Human Coordination status, Dots fallback, CLIP-related app structure, AI探锦, and AI文化助手.
- Reduced visual clutter by removing dense floating labels from the 3D model area and moving explanatory text into Streamlit-side panels and compact HUD text.
- Added procedural low-poly volumetric workers with visible heads, torsos, arms, and legs.
- Placed the draw worker on the upper drawloom platform and the weaver in the lower weaving area to make the height difference obvious.
- Added continuous animation mapping:
  - Stages 1-3: separate visible preparation cues for pattern draft, tie-pattern symbols, and warp/shuttle readiness.
  - Stage 4: draw worker pulls cords and warp threads rise smoothly.
  - Stage 5: draw worker holds the shed, weaver presses a treadle cue, shuttle/weft travels across the cloth, and the beater/reed frame pushes forward.
  - Stage 6: warp returns, the shed closes, the take-up roll advances, and the new weft pick joins the continuous cloth.
- Replaced line-only output with a continuous cloth plane textured by a clearly labeled procedural teaching motif.
- Added a moving woven-edge boundary so the viewer can distinguish the unwoven warp zone from the already woven cloth.
- Added a denser overhead cord curtain, seated lower-weaver position, broad front cloth work surface, and clearer worker-to-tool linkage inspired by the user's reference video composition.
- Added V4 loom-function cues: visible shed mouth, treadle/踩障 teaching cue, beater/reed frame teeth, inserted weft pick, and take-up roll rotation cue.
- Added state-to-animation parameters for `loom_cycle_step`, `shed_open_ratio`, `beater_ratio`, `treadle_ratio`, `takeup_ratio`, and `new_pick_ratio`.
- Added V5 grounding fixes for visual harmony:
  - Lower weaver now has a seat contact pad, hip contact marker, and foot-on-treadle contact blocks.
  - Lower weaver's body center is lower and closer to the cloth/beater work area.
  - Lower weaver's legs are posed as a seated working posture instead of hanging under the body.
  - Upper draw worker has explicit foot contact blocks on the upper platform.
  - Worker animation now preserves fixed seat/platform height, reducing the floating effect during motion.
- Added V6 action-readability fixes:
  - Stage-specific cinematic camera targets automatically focus the current action area unless the user drags the camera.
  - Stage 4 has a visible pull-down motion trail.
  - Stage 5 has a visible shuttle-pass trail, treadle press cue, and beater sweep.
  - Stage 6 has a cloth-growth pulse at the woven edge.
  - Pulling, reaching, and beating amplitudes were increased so each stage reads differently at a glance.
- Added V7 continuous-motion fixes:
  - Replaced frame-reset-looking stage poses with a browser-wall-clock motion scheduler inspired by the supplied loom-operation video direction.
  - Added short-lived motion memory in `localStorage` so Streamlit iframe refreshes continue from the last visual pose instead of snapping back to the first frame.
  - Added smooth stage blending (`stageBlend`) so camera focus, warp lift, shed opening, shuttle travel, cloth growth, and worker pose interpolate across updates.
  - Re-timed the visible action chain as one continuous cycle: upper draw pull -> shed opens -> treadle press -> shuttle pass -> beater hit -> take-up/cloth growth.
  - Kept the user's manual camera once they drag or zoom, while automatic cinematic focus remains available before user interaction.
- Added V8 silky-transition fixes:
  - Removed most stage-hard visual switches in the WebGL layer.
  - Added wide cross-fade weights for adjacent stages so pull, shed, shuttle, beater, treadle, and cloth growth overlap during transitions.
  - Replaced sudden cue visibility with opacity fading.
  - Blended worker poses from preparation to pulling to weaving to finishing instead of switching by `stageId`.
  - Blended shuttle/weft and inserted-pick visibility across stages 5 and 6 so the cloth formation does not pop.
- Added V9 video-observation refinements:
  - Opened the user's Bilibili reference in the in-app browser and observed usable frames from the video page.
  - Shifted the movement style from exaggerated demonstration gestures toward smaller, continuous hand-work motions near the loom surface.
  - Added a semi-transparent red warp/cloth reference surface inspired by the observed red weaving-area shots.
  - Increased warp-thread density and made warp lift/shed opening more restrained.
  - Reduced worker arm swing, body bob, treadle press, and beater travel so the action reads more like fine manual work rather than broad theatrical posing.
  - Updated the procedural cloth texture toward a red silk ground with dense fine thread marks while keeping the teaching-motif boundary.
- Added V10 continuous-timeline and articulated-worker refinements:
  - The WebGL scene now runs a self-contained documentary weaving timeline of about 18 seconds.
  - Python/Streamlit six-stage state remains visible as digital-twin context, but the 3D motion no longer hard-switches from those stages.
  - Automatic camera motion is restored as slow documentary-style view changes driven by the continuous timeline.
  - Procedural workers now include visible neck, waist, elbow, and wrist joints so the figures read more like articulated bodies.
  - Draw-worker and weaver hand/torso poses use the timeline phase rather than abrupt stage markers.
  - Shuttle pass, shed opening, beater movement, take-up, cloth growth, and reset overlap in one loop.
- Added V11 procedural humanization refinements:
  - Added hair caps, eye markers, and nose direction markers so the heads read as faces instead of plain blocks.
  - Added robe-front planes and sleeve geometry so the figures feel clothed rather than naked stick forms.
  - Added separate forearm segments and animated them with the upper arms, elbows, wrists, and hands.
  - Added head, neck, waist, sleeve, and robe micro-motion linked to draw/weave actions.
  - Kept the no-external-asset policy while noting that the next true jump in realism requires licensed GLB/GLTF characters.
- Added V12 mechanism-readability and smoother-camera refinements:
  - Replaced discrete documentary camera returns with continuous interpolation between timeline camera anchors.
  - Added draw-cord flow beads so upper draw action is visible even at wider camera angles.
  - Added a shed-opening focus band to make warp separation clearer.
  - Added a shuttle path highlight so the weft pass reads as one clear motion.
  - Added a beater impact edge at the woven edge so beating/settling is visible.
  - Added a take-up roll pulse ring so cloth advancement is visible.
  - Increased cue and motion-trail opacity moderately while keeping the labels out of the model area.

## Boundaries preserved

- The prototype remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching visual inspired by high, multi-layer Nanjing Yunjin drawloom structure.
- It is not a dimensionally accurate or one-to-one mechanical reconstruction.
- The cloth motif is a teaching visual motif, not a real historical Nanjing Yunjin pattern reconstruction.
- The user-provided Xiaohongshu video was used only as visual reference for composition and action readability; it is not downloaded, bundled, copied, or reproduced.
- Public reference materials were used to guide the simplified action chain: shed opening, weft insertion, beating, shed closing, and take-up. These remain teaching simplifications, not a verified mechanical reconstruction.
- The Bilibili reference supplied by the user was used only as visual direction for grounding and loom-worker contact; no video asset is downloaded, bundled, copied, or reproduced.

## Key files

- `src/yunjin_ai/digital_twin_3d.py`: Three.js WebGL renderer and state-to-animation mapping.
- `src/yunjin_ai/digital_twin_page.py`: Live Simulation Mode labels and Streamlit layout text.
- `tests/test_phase66_3d_scene_v2.py`: V12 assertions for WebGL rendering, continuous animation mapping, volumetric workers, continuous cloth, visible shed, treadle cue, beater/reed frame, inserted weft pick, take-up cue, grounded worker contact markers, interpolated documentary camera, visible motion trails, continuous timeline memory, video-inspired scheduling, red warp surface, small hand-work helpers, articulated procedural joints, face markers, forearms, sleeves, robe panels, and mechanism-readability cues.
- `ASSET_LICENSES_V12.md`: asset and license notes.
- `WINDOWS_CMD_START.md`: updated beginner Windows CMD startup steps.

## Verification

- Passed: `tests/test_phase63_live_simulation.py`, `tests/test_phase64_3d_process_twin.py`, `tests/test_phase66_3d_scene_v2.py`
- Passed in full run: 130 of 133 collected tests, with 5 reported failures because one test includes subfailures.
- Remaining failures are in legacy Phase 5/Phase 6 protection and AI assistant interaction tests, including pre-existing hash-manifest differences in the supplied ZIP. The stable source copy shows the same protection-health failure before V3 changes.
