# 3D Scene V13 Asset and License Notes

This V13 copy does not bundle external GLB/GLTF character, loom, shuttle, cloth, video, or motif assets.

## Procedural assets

- Low-poly draw worker and lower weaver: generated at runtime with Three.js primitive geometry.
- Drawloom frame, red/gold jacquard control wall, gold peg rows, dense cord curtain, warp threads, shuttle, weft, beater, treadle cues, cloth bed, cloth roller, and teaching cloth surface: generated at runtime with Three.js primitive geometry and local JavaScript logic.
- Cloth surface and motif: generated at runtime on an HTML canvas and mapped to a Three.js plane.

These assets are original procedural teaching visuals created for this prototype. The cloth motif is labeled in the app as a teaching visual motif and must not be described as a real historical Nanjing Yunjin pattern or a dimensionally accurate craft reconstruction.

The user-provided Xiaohongshu and Bilibili links were used only as visual direction for broad composition cues: red/gold weaving surfaces, dense cords/warp texture, an upper draw worker, a lower seated weaver, and hand work near the cloth. No video is downloaded, bundled, copied, traced frame-by-frame, or reproduced in this project.

## Runtime libraries

- Three.js is loaded in the Streamlit iframe from the public Three.js CDN path used in `src/yunjin_ai/digital_twin_3d.py`.
- Camera drag and zoom are implemented locally inside the iframe; no external OrbitControls module is bundled.

No third-party 3D model license is claimed because no third-party 3D model is bundled.
