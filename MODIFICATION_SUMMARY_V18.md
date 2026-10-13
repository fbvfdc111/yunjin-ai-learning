# Scene V18 Modification Summary

## Why V18 was needed

The user correctly identified that V17 still felt strange:

- The visible worker joints were not readable enough.
- The weaving motion still felt like separated teaching steps instead of a shared continuous operation.
- The loom was visually noisy because too many individual lines competed for attention.
- The scene implied only two isolated people, while the broader craft process is collaborative.

## What changed

- Copied V17 into a new V18 folder; previous versions were not overwritten.
- Reworked the loom hierarchy for readability:
  - Dense warp is now represented by semi-transparent warp-layer sheets.
  - Only selected moving warp lines remain highlighted.
  - This reduces line clutter while preserving the idea of dense warp structure.
- Made articulation visible:
  - Elbows, wrists, hands, head and waist are explicitly marked as visible joints.
  - Primary workers now carry V18 visible-jointed markers.
- Changed the action model from step demonstration to simultaneous collaboration:
  - Upper draw action, shed opening, shuttle movement, beating and take-up overlap through the same 45-second cycle.
  - Draw and shed now keep a baseline motion instead of dropping completely to zero between phases.
- Added background collaborative workers:
  - A pattern-preparation/support figure near the pattern side.
  - A cloth-check/support figure near the cloth side.
  - These are deliberately secondary so they add collaboration context without crowding the main weaving action.
- Preserved the PDF-based Dahua Lou structure cues from V17.

## Boundaries preserved

- The app remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching reconstruction inspired by Dahua Lou structure, not a dimensionally accurate mechanical reconstruction.
- The cloth motif remains a teaching visual motif, not a historical Nanjing Yunjin pattern reconstruction.
- Reference images/PDF are used only as visual direction; no reference media is bundled or reproduced as an asset.
