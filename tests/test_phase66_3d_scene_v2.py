from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.digital_twin import STAGE_IDS
from yunjin_ai.digital_twin_3d import (
    ASSET_POLICY,
    BOUNDARY_COPY,
    RENDERING_LAYER,
    animation_mapping,
    process_explanation,
    render_process_twin_3d,
)
from yunjin_ai.digital_twin_simulation import SIMULATION_STAGE_SECONDS, simulation_sample


def _sample(stage_id: str, progress_seconds: float = 1.0):
    return simulation_sample(STAGE_IDS.index(stage_id) * SIMULATION_STAGE_SECONDS + progress_seconds)


def _html_for(stage_id: str) -> str:
    return render_process_twin_3d(_sample(stage_id))


def test_v3_uses_threejs_webgl_not_plotly_or_css_figure_people():
    html = _html_for("warp_lifting")
    assert RENDERING_LAYER == "Three.js WebGL embedded in Streamlit iframe"
    assert 'data-renderer="threejs-webgl"' in html
    assert "THREE.WebGLRenderer" in html
    assert "function updateCamera" in html
    assert "yunjin-webgl-v13-camera" in html
    assert "yunjin-webgl-v13-continuous-timeline-state" in html
    assert "cinematicViews" in html
    assert "applyCinematicCamera" in html
    assert "videoInspiredMotionScheduler" in html
    assert "documentaryWeavingTimeline" in html
    assert "documentaryViewFromTimeline" in html
    assert "blendTimelineViews" in html
    assert "stageBlend" in html
    assert "crossfadeWeight" in html
    assert "setCueOpacity" in html
    assert "smallContinuousHandWork" in html
    assert "video-observed-red-warp-surface-v9" in html
    assert "articulated-skeleton-v11-humanized" in html
    assert "left-elbow-joint-v11" in html
    assert "right-wrist-joint-v11" in html
    assert "hair-cap-humanized-v11" in html
    assert "face-direction-nose-v11" in html
    assert "left-forearm-humanized-v11" in html
    assert "front-robe-plane-humanized-v11" in html
    assert "v12-draw-cord-flow-bead-continuous-step" in html
    assert "v12-shed-opening-focus-band-clear-step" in html
    assert "v12-shuttle-path-highlight-clear-step" in html
    assert "v12-beater-impact-edge-clear-step" in html
    assert "v12-takeup-roll-pulse-ring-clear-step" in html
    assert "v13-video-reference-red-gold-jacquard-control-wall" in html
    assert "v13-video-reference-red-jacquard-panel" in html
    assert "v13-video-reference-gold-pegs-on-red-panel" in html
    assert "v13-video-like-dense-cord-curtain" in html
    assert "v13-larger-human-motion-profile-video-inspired" in html
    assert "v19-scene-rebuild-structured-digital-twin-view" in html
    assert "v19-single-continuous-collaboration-loop-not-stage-demo" in html
    assert "v19-five-layer-dahua-lou-loom-rebuild" in html
    assert "human-base-rigged.cc0.glb" in html
    assert "CC0-1.0" in html
    assert "7135e03b6259e970458deff3e0458610914d7c35164cae12611101361e4a5749" in html
    assert "GLTFLoader" in html
    assert "videoStoryboardBeats" in html
    assert "smoothstep" in html
    assert "Date.now() / 1000" in html
    assert "pointermove" in html
    assert "Plotly" not in html
    assert "low-poly-worker worker" not in html


def test_v3_preserves_boundaries_and_simulated_data_copy():
    html = _html_for("weft_weaving")
    assert BOUNDARY_COPY in html
    assert "not a dimensionally accurate mechanical reconstruction" in html
    assert "Simulation-driven / Simulated Data" in html
    assert "真实传感器、真实机械参数或工匠验证" in html
    assert "hardware" not in html.lower() or "hardware" in html


def test_v3_has_clear_multilevel_loom_and_reduced_labels():
    html = _html_for("warp_lifting")
    for marker in (
        "top-drawloom-frame",
        "pattern-control-bank",
        "upper-draw-worker-platform",
        "overhead-golden-cord-curtain-reference-inspired",
        "warp-roller",
        "lower-weaving-bench",
        "front-cloth-work-surface-broad",
        "v13-video-reference-red-silk-cloth-bed",
        "v16-dahua-lou-tower-tall-outer-post",
        "v18-layered-dahua-lou-warp-curtain-reduced-line-clutter",
        "v18-structural-warp-layer-sheet-front-not-individual-lines",
        "v18-highlighted-moving-warp-reference-line",
        "v16-upper-pattern-operator-side-seat",
        "v16-pattern-tower-jacquard-block-bank",
        "v17-pdf-real-loom-diagonal-pattern-control-cords",
        "v17-pdf-real-loom-rooflike-upper-truss",
        "v19-layer-1-body-frame-solid-wood-zone",
        "v19-layer-2-upper-flower-tower-operator-zone",
        "v19-layer-3-warp-shed-transparent-process-zone",
        "v19-single-continuous-collaboration-loop-visible-ribbon",
        "cloth-roller-finished-area",
        "shed-opening-v4-visible-warp-mouth",
        "lower-weaver-treadle-cue-v4",
        "takeup-roll-rotation-cue-v4",
    ):
        assert marker in html
    assert html.count("minimal-layer-label") == 1
    assert "Upper Platform" not in html
    assert "Warp Shed" not in html


def test_v3_workers_are_procedural_volumetric_3d_figures_with_height_difference():
    html = _html_for("weft_weaving")
    assert "function createWorker" in html
    assert "DodecahedronGeometry" in html
    assert "CapsuleGeometry" in html
    assert "left-hand-targeting-tool" in html
    assert "draw-worker-hand-control-bar-linked-to-cords" in html
    assert "weaver-beater-reed-frame-linked-to-shuttle-v4" in html
    assert "reed-tooth-for-beating-weft-v4" in html
    assert "new-weft-pick-inserted-then-beaten-v4" in html
    assert "stage-4-obvious-pull-down-cue" in html
    assert "stage-5-obvious-shuttle-travel-cue" in html
    assert "stage-5-beater-forward-cue-v4" in html
    assert "stage-5-treadle-press-cue-v4" in html
    assert "stage-6-obvious-cloth-advance-cue" in html
    assert "v6-visible-motion-trail-draw-pull" in html
    assert "v6-visible-motion-trail-shuttle-pass" in html
    assert "v6-visible-motion-sweep-beater" in html
    assert "v6-visible-cloth-growth-pulse-at-woven-edge" in html
    assert "lower-weaver-seat-stool" in html
    assert "lower-weaver-seat-contact-pad-v5" in html
    assert "upper-worker-foot-contact-platform-v5" in html
    assert "grounded-seated-contact-rig-v5" in html
    assert "hip-on-seat-contact-v5" in html
    assert "foot-on-treadle-contact-v5" in html
    assert "foot-on-upper-platform-v5" in html
    assert "'-low-poly-3d-worker-volume-articulated-skeleton-v11-humanized'" in html
    assert "createWorker('upper-draw-worker'" in html
    assert "createWorker('lower-weaver'" in html
    assert "drawWorker.position.set(-2.74, 3.22, .68)" in html
    assert "weaver.position.set(-2.86, .58, 2.03)" in html
    assert "weaver.position.y = .58" in html
    assert "drawWorker.position.y = 3.22" in html
    assert "const pull = setupPull + action.draw * (.28 + timeline.drawPull * .78)" in html
    assert "const handThrow = Math.sin(timeline.phase * Math.PI * 8) * .66" in html
    assert "beaterForward = action.beater * timeline.beaterHit * 1.08" in html
    assert "upper-pattern-operator-v19-jointed-seated-worker" in html
    assert "lower-weaver-v19-jointed-seated-worker" in html
    assert "v19-jointed-seated-primary-worker-stable-animation" in html
    assert "v19-visible-articulation-joint" in html
    assert "v19-background-collaboration-worker" in html
    assert "support-pattern-prep-worker-v18" in html
    assert "support-cloth-check-worker-v18" in html
    assert "v17-back-cloth-panel-no-nude-model" in html
    assert "licensedHumanRig.failed = true" in html
    assert "heldActionWindow" in html
    assert "About a 45 second loop" in html
    assert "continuousAnimationSeconds" in html
    assert "poseLicensedHumanWorker" in html
    assert ASSET_POLICY in html


def test_v3_stage_to_animation_mapping_is_continuous_and_state_driven():
    warp = animation_mapping(_sample("warp_lifting"))
    weft = animation_mapping(_sample("weft_weaving"))
    pattern = animation_mapping(_sample("pattern_emergence"))
    assert warp["continuous_clock"] is True
    assert animation_mapping(_sample("pattern_design"))["setup_focus"] == "pattern_draft_board"
    assert animation_mapping(_sample("pattern_translation"))["setup_focus"] == "tie_pattern_symbols"
    assert animation_mapping(_sample("weaving_preparation"))["setup_focus"] == "warp_and_shuttle_ready"
    assert warp["loom_cycle_step"] == "shed_opening"
    assert weft["loom_cycle_step"] == "weft_insertion_and_beating"
    assert pattern["loom_cycle_step"] == "shed_close_and_takeup"
    assert weft["beater_ratio"] > 0
    assert weft["treadle_ratio"] > 0
    assert pattern["takeup_ratio"] > 0
    assert warp["draw_worker_motion"] == "pulling"
    assert warp["weaver_motion"] == "waiting"
    assert warp["warp_lift_ratio"] > 0.5
    assert weft["draw_worker_motion"] == "holding"
    assert weft["weaver_motion"] == "weaving"
    assert 0 < weft["shuttle_travel_ratio"] < 1
    assert pattern["draw_worker_motion"] == "resetting"
    assert pattern["weaver_motion"] == "finishing"
    assert pattern["woven_cloth_ratio"] > warp["woven_cloth_ratio"]


def test_v3_continuous_cloth_is_labeled_as_teaching_visual_not_real_pattern():
    html = _html_for("pattern_emergence")
    assert "continuous-cloth-plane-procedural-teaching-motif" in html
    assert "paintTeachingCloth" in html
    assert "woven-edge-moving-boundary-between-warp-and-cloth" in html
    assert "new-weft-pick-inserted-then-beaten-v4" in html
    assert "织口 / woven edge" in html
    assert "pattern-draft-board-stage-1" in html
    assert "tie-pattern-symbols-stage-2" in html
    assert "warp-preparation-comb-stage-3" in html
    assert "教学视觉示意 / teaching visual motif" in html
    assert "不是历史实物纹样复原" in html
    assert "真实历史云锦纹样" not in html
    assert "collaboration cycle" in process_explanation(_sample("pattern_emergence"))["en"]


if __name__ == "__main__":
    test_v3_uses_threejs_webgl_not_plotly_or_css_figure_people()
    test_v3_preserves_boundaries_and_simulated_data_copy()
    test_v3_has_clear_multilevel_loom_and_reduced_labels()
    test_v3_workers_are_procedural_volumetric_3d_figures_with_height_difference()
    test_v3_stage_to_animation_mapping_is_continuous_and_state_driven()
    test_v3_continuous_cloth_is_labeled_as_teaching_visual_not_real_pattern()
    print("phase66 3D Scene V3 assertions passed")
