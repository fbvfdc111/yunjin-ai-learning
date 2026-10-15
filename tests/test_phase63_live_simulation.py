from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.digital_twin import STAGE_IDS, TITLES
from yunjin_ai.digital_twin_simulation import (
    SIMULATED_DATA_LABEL, SIMULATION_BOUNDARY, SIMULATION_STAGE_SECONDS,
    simulation_sample, simulation_series,
)


def app():
    with patch.dict(os.environ, {"DOTS_API_KEY": ""}):
        at = AppTest.from_file(ROOT / "app.py", default_timeout=20).run()
        at.segmented_control(key="main_tab").set_value("数字织机").run()
    assert not at.exception
    return at


def rendered(at):
    return "\n".join(str(e.value) for e in [
        *at.title, *at.subheader, *at.markdown, *at.caption, *at.info, *at.warning, *at.success, *at.error
    ])


def test_simulation_state_machine_cycles_through_six_stages_without_hardware_claims():
    for index, sid in enumerate(STAGE_IDS):
        sample = simulation_sample(index * SIMULATION_STAGE_SECONDS + 0.5)
        assert sample.stage_id == sid
        assert sample.stage_title == TITLES[index]
        assert sample.data_source == SIMULATED_DATA_LABEL
        assert 2.5 <= sample.tension_n <= 4.0
        assert 3.0 <= sample.lift_mm <= 19.5
    assert simulation_sample(99999).stage_id in STAGE_IDS


def test_simulation_worker_coordination_statuses_are_explicit():
    warp = simulation_sample(STAGE_IDS.index("warp_lifting") * SIMULATION_STAGE_SECONDS + 1)
    weft = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 1)
    assert (warp.draw_worker_status, warp.weaver_status, warp.coordination_status) == (
        "ACTIVE", "WAITING", "SYNCHRONIZED",
    )
    assert (weft.draw_worker_status, weft.weaver_status, weft.coordination_status) == (
        "HOLDING", "ACTIVE", "SYNCHRONIZED",
    )


def test_simulation_series_is_chart_ready_and_labeled_simulated_data():
    rows = simulation_series(12, points=12)
    assert len(rows) == 12
    assert rows == sorted(rows, key=lambda row: row["time_s"])
    assert {row["data_source"] for row in rows} == {SIMULATED_DATA_LABEL}
    assert {"time_s", "tension_n", "lift_mm", "coordination_status"}.issubset(rows[0])


def test_only_exhibition_and_teaching_modes_are_visible():
    at = app()
    options = at.segmented_control(key="twin_experience_mode").options
    assert not at.exception
    assert options == ["Exhibition Mode / 展示模式", "Teaching Mode / 教学模式"]
    assert "Live Simulation Mode / 实时仿真模式" not in rendered(at)
