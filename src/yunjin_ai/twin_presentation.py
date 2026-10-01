"""Read-only display labels derived from the unchanged teaching state."""
from .digital_twin import MODES, STAGE_IDS, TITLES, TwinState, validate_runtime


def learning_status(state: TwinState) -> dict:
    validate_runtime(state)
    t = state.teaching
    return {
        "当前环节": TITLES[STAGE_IDS.index(state.current_stage)],
        "体验进度": f"{STAGE_IDS.index(state.current_stage) + 1} / 6",
        "已完成教学步骤": f"{len(state.executed_stages)} / 6",
        "当前模式": MODES[state.mode],
        "环节状态": [
            ("图案设计", "已完成" if t.sketch_visible else "待体验"),
            ("挑花结本", "已完成" if t.carrier_visible else "待体验"),
            ("织造准备", "已完成" if t.preparation_ready else "待体验"),
            ("提经示意", "已执行" if t.warp_emphasis != "rest" else "待体验"),
            ("织造示意", "已执行" if t.weft_direction != "rest" else "待体验"),
            ("纹样形成", f"{t.pattern_bands} / 3"),
        ],
    }


def teaching_feedback(state: TwinState) -> str:
    validate_runtime(state)
    if state.last_action == "初始状态":
        return "点击“执行当前步骤”，观察草图出现。"
    if state.current_stage == STAGE_IDS[-1]:
        return f"纹样已显示 {state.teaching.pattern_bands} / 3 段；三段全部显示后，本环节完成。界面分段不代表真实织造次数。"
    if state.current_stage_executed:
        return "本环节已执行。可进入下一步，或再次执行重播示意；重播不会增加完成步骤数。"
    return "当前环节等待执行。选择环节只改变观察位置，不会自动完成教学步骤。"
