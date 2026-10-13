# Scene V19 Rebuild Modification Summary

## Why V19 is a rebuild

V18 was still trying to improve a scene architecture that had grown too complex. The result was better than earlier versions, but the visual logic still depended on many individual lines and incremental patches. V19 rebuilds the 3D display logic while keeping the Python/Streamlit digital-twin state layer.

## What changed

- Copied V18 into a new V19 rebuild folder; previous versions were not overwritten.
- Rebuilt the loom view as five readable layers:
  - Body/frame layer.
  - Upper flower-tower/operator layer.
  - Warp/shed process layer.
  - Lower weaving/shuttle/beater layer.
  - Cloth take-up/finished-fabric layer.
- Added translucent layer slabs so the viewer can understand the loom hierarchy before reading the fine details.
- Reframed warp as a process layer:
  - Dense warp is represented with transparent warp sheets.
  - Only selected moving warp lines remain visible as action highlights.
- Reframed motion as one collaboration loop:
  - Added a visible collaboration-loop ribbon from upper operator to shed, shed to shuttle, and beater to cloth.
  - Upper draw, shed opening, shuttle motion, beating and take-up overlap in one continuous cycle instead of isolated steps.
- Preserved visible jointed workers and background collaboration workers from V18.
- Preserved the PDF-based Dahua Lou structural cues from V17.

## Boundaries preserved

- The app remains `Simulation-driven / Simulated Data`.
- The 3D drawloom is a teaching reconstruction inspired by Dahua Lou structure, not a dimensionally accurate mechanical reconstruction.
- The cloth motif remains a teaching visual motif, not a historical Nanjing Yunjin pattern reconstruction.
- Reference images/PDF are used only as visual direction; no reference media is bundled or reproduced as an asset.
