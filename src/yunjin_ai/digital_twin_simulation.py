"""Simulation-only runtime for the digital loom prototype.

No hardware, sensors, camera feeds, or real loom measurements are used here.
The values are deterministic teaching signals for a Streamlit demonstration.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from .digital_twin import STAGE_IDS, TITLES

SIMULATION_STAGE_SECONDS = 4.0
SIMULATION_TOTAL_SECONDS = SIMULATION_STAGE_SECONDS * len(STAGE_IDS)
SIMULATED_DATA_LABEL = "Simulated Data / 仿真数据"
SIMULATION_BOUNDARY = (
    "当前实时仿真只使用程序生成的教学数据，不连接真实织机、真实传感器或真实实验采集数据。"
)


@dataclass(frozen=True)
class SimulationSample:
    elapsed_seconds: float
    stage_id: str
    stage_title: str
    stage_index: int
    stage_progress: float
    tension_n: float
    lift_mm: float
    draw_worker_status: str
    weaver_status: str
    coordination_status: str
    data_source: str = SIMULATED_DATA_LABEL


def _bounded_elapsed(elapsed_seconds: float) -> float:
    if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
        return 0.0
    return elapsed_seconds % SIMULATION_TOTAL_SECONDS


def simulation_sample(elapsed_seconds: float) -> SimulationSample:
    """Return one deterministic simulated state for the six-stage loom loop."""
    loop_time = _bounded_elapsed(elapsed_seconds)
    stage_index_zero = min(int(loop_time // SIMULATION_STAGE_SECONDS), len(STAGE_IDS) - 1)
    stage_id = STAGE_IDS[stage_index_zero]
    stage_progress = (loop_time % SIMULATION_STAGE_SECONDS) / SIMULATION_STAGE_SECONDS
    wave = math.sin((stage_progress * 2.0 + stage_index_zero * 0.35) * math.pi)
    pulse = (1.0 - math.cos(stage_progress * 2.0 * math.pi)) / 2.0

    stage_tension_offsets = {
        "pattern_design": 0.0,
        "pattern_translation": 0.12,
        "weaving_preparation": 0.24,
        "warp_lifting": 0.62,
        "weft_weaving": 0.45,
        "pattern_emergence": 0.28,
    }
    tension_n = 2.9 + stage_tension_offsets[stage_id] + 0.18 * wave

    lift_base = 3.0 + 2.0 * pulse
    if stage_id == "warp_lifting":
        lift_mm = 12.0 + 7.0 * pulse
    elif stage_id == "weft_weaving":
        lift_mm = 8.0 + 3.0 * pulse
    elif stage_id == "pattern_emergence":
        lift_mm = 5.0 + 4.0 * pulse
    else:
        lift_mm = lift_base

    if stage_id == "warp_lifting":
        draw_worker_status, weaver_status, coordination_status = "ACTIVE", "WAITING", "SYNCHRONIZED"
    elif stage_id == "weft_weaving":
        draw_worker_status, weaver_status, coordination_status = "HOLDING", "ACTIVE", "SYNCHRONIZED"
    elif stage_id == "pattern_emergence":
        draw_worker_status, weaver_status, coordination_status = "MONITORING", "ACTIVE", "SYNCHRONIZED"
    elif stage_id == "weaving_preparation":
        draw_worker_status, weaver_status, coordination_status = "READY", "READY", "WAITING"
    else:
        draw_worker_status, weaver_status, coordination_status = "WAITING", "WAITING", "WAITING"

    return SimulationSample(
        elapsed_seconds=round(elapsed_seconds, 2),
        stage_id=stage_id,
        stage_title=TITLES[stage_index_zero],
        stage_index=stage_index_zero + 1,
        stage_progress=round(stage_progress, 3),
        tension_n=round(tension_n, 2),
        lift_mm=round(lift_mm, 1),
        draw_worker_status=draw_worker_status,
        weaver_status=weaver_status,
        coordination_status=coordination_status,
    )


def simulation_series(elapsed_seconds: float, points: int = 36) -> list[dict]:
    """Build a rolling chart window ending at the current simulated second."""
    points = max(6, min(points, 120))
    end = max(0.0, elapsed_seconds)
    start = end - points + 1
    rows = []
    for offset in range(points):
        sample_time = start + offset
        sample = simulation_sample(sample_time)
        row = asdict(sample)
        # A relative x-axis keeps the chart readable while the values move:
        # 0 is now, negative values are seconds in the recent past.
        row["time_s"] = round(sample_time - end, 1)
        rows.append(row)
    return rows
