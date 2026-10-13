from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.digital_twin import STAGE_IDS
from yunjin_ai.digital_twin_3d import process_explanation, render_process_twin_3d
from yunjin_ai.digital_twin_simulation import (
    SIMULATED_DATA_LABEL,
    SIMULATION_STAGE_SECONDS,
    simulation_sample,
)


def test_3d_scene_reads_existing_simulation_sample_without_hardware_claims():
    sample = simulation_sample(STAGE_IDS.index("warp_lifting") * SIMULATION_STAGE_SECONDS + 1.0)
    html = render_process_twin_3d(sample)
    assert 'data-stage="warp_lifting"' in html
    assert f'data-source="{SIMULATED_DATA_LABEL}"' in html
    assert f'data-lift-mm="{sample.lift_mm}"' in html
    assert "Simulation-driven" in html
    assert "3D Human-Loom Collaborative Digital Twin Prototype" in html
    assert "not a one-to-one mechanical reconstruction" in html
    assert "real_sensor" not in html.lower()
    assert "hardware_connected" not in html


def test_3d_scene_shows_stage_specific_human_loom_collaboration():
    warp = simulation_sample(STAGE_IDS.index("warp_lifting") * SIMULATION_STAGE_SECONDS + 1.0)
    weft = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 2.0)
    pattern = simulation_sample(STAGE_IDS.index("pattern_emergence") * SIMULATION_STAGE_SECONDS + 2.0)

    warp_html = render_process_twin_3d(warp)
    weft_html = render_process_twin_3d(weft)
    pattern_html = render_process_twin_3d(pattern)

    assert 'data-raised="true"' in warp_html
    assert 'data-worker-state="ACTIVE"' in warp_html
    assert "拽花工" in warp_html
    assert "织手" in warp_html
    assert 'class="shuttle" data-active="true"' in weft_html
    assert 'data-worker-state="HOLDING"' in weft_html
    assert weft_html.count("cloth-band") >= 3
    assert pattern_html.count("cloth-band") >= 4
    assert "Human Coordination" in pattern_html
    assert "鼠标拖动旋转，滚轮缩放" in pattern_html


def test_bilingual_whats_happening_copy_tracks_stage():
    warp = simulation_sample(STAGE_IDS.index("warp_lifting") * SIMULATION_STAGE_SECONDS + 1.0)
    weft = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 1.0)
    assert "正在发生什么？" in process_explanation(warp)["title"]
    assert "What's happening?" in process_explanation(warp)["title"]
    assert "lift_mm" in process_explanation(warp)["zh"]
    assert "shuttle" in process_explanation(weft)["en"]
    assert "collaboration cycle" in process_explanation(
        simulation_sample(STAGE_IDS.index("pattern_emergence") * SIMULATION_STAGE_SECONDS + 1.0)
    )["en"]


def test_exhibition_page_makes_3d_process_view_primary():
    with patch.dict(os.environ, {"DOTS_API_KEY": "", "OPENAI_API_KEY": "", "OPENAI_VISION_MODEL": ""}):
        at = AppTest.from_file(ROOT / "app.py", default_timeout=20).run()
        at.segmented_control(key="main_tab").set_value("数字织机").run()
        at.segmented_control(key="twin_experience_mode").set_value("Exhibition Mode / 展示模式").run()
    assert not at.exception
    text = "\n".join(str(e.value) for e in [*at.subheader, *at.markdown, *at.caption, *at.info, *at.warning])
    assert "南京云锦大花楼织机沉浸展示" in at.get("iframe")[0].proto.srcdoc
    assert "正在发生什么？ / What's happening?" in text
    assert "展示动画来自程序化教学重建" in text


def test_exhibition_mode_is_default_and_showcase_first():
    with patch.dict(os.environ, {"DOTS_API_KEY": "", "OPENAI_API_KEY": "", "OPENAI_VISION_MODEL": ""}):
        at = AppTest.from_file(ROOT / "app.py", default_timeout=20).run()
        at.segmented_control(key="main_tab").set_value("数字织机").run()
    assert not at.exception
    assert at.segmented_control(key="twin_experience_mode").value == "Exhibition Mode / 展示模式"
    srcdoc = at.get("iframe")[0].proto.srcdoc
    assert "南京云锦大花楼织机沉浸展示" in srcdoc
    assert "webgl-wrap exhibition" in srcdoc
    assert "v20-exhibition-warm-stage-spotlight-on-cloth" in srcdoc
