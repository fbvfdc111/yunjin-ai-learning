# 3D Scene V14 Asset and License Notes

## Bundled GLB asset

- File: `assets/models/human-base-rigged.cc0.glb`
- Source page: `https://www.innerscene.com/tools/library/3d-parts/human-base-mesh-with-editable-53-bone-rig-8e7c8ab1`
- Download endpoint used: `https://www.innerscene.com/api/library/human-base-mesh-with-editable-53-bone-rig-8e7c8ab1/download`
- Source name: Innerscene - original model
- License: CC0-1.0 / public domain dedication
- SHA256: `7135e03b6259e970458deff3e0458610914d7c35164cae12611101361e4a5749`
- Page notes: the GLB preserves skin weights and skeleton, includes a 53-bone rig, and contains no animation.

Innerscene's part page states that the model is public domain CC0 and free to use, modify and redistribute for any purpose, including commercially, with no credit required. Its library terms state that library parts may be copied, modified, distributed and used for any purpose, including commercially, without asking permission and without credit.

## Procedural assets

- Worker clothing overlays, head wraps, loom, red/gold jacquard control wall, cord curtain, warp threads, shuttle, weft, beater, treadle cues, cloth bed, cloth roller, motion cues and teaching cloth surface are generated at runtime with Three.js primitives and local JavaScript.
- The continuous cloth motif is a teaching visual motif and must not be described as a real historical Nanjing Yunjin pattern.

## Video references

The user-provided Xiaohongshu and Bilibili links were used only as visual direction for action decomposition and broad composition cues. No video is downloaded, bundled, copied, traced frame-by-frame, or reproduced in this project.

## Runtime libraries

- Three.js is loaded from the public Three.js CDN path used in `src/yunjin_ai/digital_twin_3d.py`.
- `GLTFLoader` is imported from the Three.js examples module CDN to load the bundled GLB data URI inside the Streamlit iframe.

This prototype remains `Simulation-driven / Simulated Data` and is not a dimensionally accurate mechanical reconstruction.
