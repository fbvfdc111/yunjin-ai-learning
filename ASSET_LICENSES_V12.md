# 3D Scene V12 Asset and License Notes

This V12 copy does not bundle external GLB/GLTF character, loom, shuttle, cloth, or motif assets.

## Procedural assets

- Low-poly draw worker and lower weaver: generated at runtime with Three.js primitive geometry (`DodecahedronGeometry`, `ConeGeometry`, `CapsuleGeometry`).
- Drawloom frame, posts, rails, rollers, dense overhead cord curtain, warp threads, shuttle and weft: generated at runtime with Three.js primitive geometry.
- Cloth surface and motif: generated at runtime on an HTML canvas and mapped to a Three.js plane.
- Pattern draft board, tie-pattern symbols, warp preparation comb, visible shed opening, treadle cue, beater/reed frame, inserted weft pick, take-up roll cue, woven edge cue, grounded seat/foot contact pads, action arrows, motion trails, beater sweep, cloth-growth pulse, cinematic camera views, continuous motion scheduler, documentary-style continuous timeline, short-lived pose memory, cross-faded action weights, red warp/cloth reference surface, small continuous hand-work motions, articulated procedural worker joints, hair caps, face direction markers, forearms, sleeves, robe-front planes, draw-cord flow beads, shed focus band, shuttle path highlight, beater impact edge, and take-up pulse ring: generated at runtime with Three.js primitive geometry and local JavaScript logic.

These assets are original procedural teaching visuals created for this prototype. The cloth motif is labeled in the app as a teaching visual motif and must not be described as a real historical Nanjing Yunjin pattern or a dimensionally accurate craft reconstruction.

The Xiaohongshu video shared by the user was used only as a visual reference for broad composition cues: dense upper hanging cords, a lower seated weaver close to the cloth surface, and a broad cloth area. The video itself is not downloaded, bundled, copied, or reproduced in this project.

Additional public reference materials were used only to guide the teaching animation sequence: shed opening, weft insertion, beating, shed closing, and take-up. These references inform simplified motion logic; they are not used as copied media assets, and the model is still not a dimensionally accurate mechanical reconstruction.

The Bilibili reference link shared by the user was opened in the in-app browser and observed as visual direction for worker grounding, loom-worker contact, simplified continuous action rhythm, red loom/cloth surface emphasis, dense warp texture, and smaller hand motions near the cloth. No Bilibili video asset is downloaded, bundled, copied, or reproduced in this project.

## Runtime libraries

- Three.js is loaded in the Streamlit iframe from the public Three.js CDN path used in `src/yunjin_ai/digital_twin_3d.py`.
- Camera drag and zoom are implemented locally inside the iframe; no external OrbitControls module is bundled.

No third-party 3D model license is claimed because no third-party 3D model is bundled.
