"""Native Streamlit controls around a runtime-state SVG view."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st

from .digital_twin import (
    MISSING_CAPABILITIES, MODES, PROCESS_BOUNDARY,
    STAGE_IDS, STATE_BOUNDARY, TITLES, VISUAL_BOUNDARY, TwinState,
    load_stages, state_snapshot, transition,
)
from .digital_twin_svg import render_twin_svg
from .learning_quiz import (
    QUIZ_BY_STAGE, anonymous_result_record, append_anonymous_result,
    evaluate_quiz, evaluation_summary,
)
from .twin_presentation import learning_status, teaching_feedback


def apply_twin_event(action: str, value: str | None = None) -> None:
    # This callback finishes before the next render; widgets never render a
    # guessed animation directly. The session owns the immutable state object.
    state = st.session_state["twin_state"]
    st.session_state["twin_state"] = transition(state, action, value)


def change_mode() -> None:
    apply_twin_event("mode", st.session_state["twin_mode_widget"])


def submit_quiz(root: Path, stage_id: str, selected_index: int) -> None:
    evaluation = evaluate_quiz(stage_id, selected_index)
    st.session_state.setdefault("quiz_evaluations", {})
    st.session_state["quiz_evaluations"][stage_id] = evaluation
    st.session_state.setdefault("quiz_anonymous_session", f"session-{id(st.session_state) & 0xfffffff:x}")
    record = anonymous_result_record(
        evaluation,
        st.session_state["twin_state"],
        session_token=st.session_state["quiz_anonymous_session"],
    )
    append_anonymous_result(root / "data" / "learning_results" / "anonymous_quiz_results.ndjson", record)


def show_digital_twin(root: Path, knowledge, sources, open_guide: Callable[[str], None], show_sources: Callable) -> None:
    st.html('''<style>
    .stMainBlockContainer:has(.st-key-twin_state_panel) {padding-top:4rem;padding-bottom:2rem}
    .stMainBlockContainer:has(.st-key-twin_state_panel) [data-testid="stVerticalBlock"] {gap:.55rem}
    .stMainBlockContainer:has(.st-key-twin_state_panel) h1 {font-size:2rem;padding:.3rem 0 .5rem}
    .stMainBlockContainer:has(.st-key-twin_state_panel) h3 {font-size:1.2rem;padding:.2rem 0 .4rem}
    @media(max-width:640px) {
      .stMainBlockContainer:has(.st-key-twin_state_panel) {padding-top:4rem}
      .stMainBlockContainer:has(.st-key-twin_state_panel) h1 {font-size:1.6rem}
    }
    </style>''')
    st.title("南京云锦织造教学型数字孪生原型")
    st.write("从图案到织物，亲手体验六个教学环节。")
    st.caption("执行步骤 → 更新 Twin State → 驱动 SVG 教学画面 · 工艺解释有可信来源，可继续向AI文化助手提问。")
    st.info(VISUAL_BOUNDARY, icon=":material/info:")
    st.caption("教学状态由用户交互驱动，并非实体织机实时数据。" + PROCESS_BOUNDARY)
    try:
        stages = load_stages(root / "data/digital_twin/twin_states.json", knowledge, sources)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error("教学资料校验未通过，当前页面停止渲染，未补写文化事实。")
        st.caption(str(exc))
        return
    st.session_state.setdefault("twin_state", TwinState())
    state = st.session_state["twin_state"]
    index = STAGE_IDS.index(state.current_stage)
    stage = stages[index]
    st.session_state["twin_mode_widget"] = state.mode
    st.segmented_control("体验模式", list(MODES), format_func=MODES.get,
                         key="twin_mode_widget", required=True, on_change=change_mode)
    if state.mode == "free":
        st.caption("自由探索可单独体验任一状态；跳转不会自动执行前置步骤。画面保留本会话已操作的教学标记。")
    else:
        st.caption("按教学顺序执行当前步骤，再进入下一步。此顺序不是完整工艺操作规程。")
    with st.container(horizontal=True):
        for lesson in stages:
            done = lesson.id in state.executed_stages
            st.button(f"{lesson.stage_index} {lesson.title}{' ✓' if done else ''}",
                      key=f"twin_select_{lesson.id}", type="primary" if lesson.id == state.current_stage else "secondary",
                      disabled=state.mode != "free", on_click=apply_twin_event, args=("select", lesson.id))
    st.progress(stage.stage_index / 6, text=f"当前位置 {stage.stage_index}/6 · 已执行教学步骤 {len(state.executed_stages)}/6")

    with st.container(horizontal=True):
        st.button("上一步", key="twin_previous", disabled=index == 0,
                  on_click=apply_twin_event, args=("previous",))
        st.button("执行当前步骤", key="twin_execute", type="primary",
                  on_click=apply_twin_event, args=("execute",))
        st.button("下一步", key="twin_next", disabled=index == 5 or (state.mode == "sequential" and not state.current_stage_executed),
                  on_click=apply_twin_event, args=("next",))
        st.button("重新开始体验", key="twin_reset", on_click=apply_twin_event, args=("reset",))
    if state.current_stage_executed:
        st.caption("当前教学步骤已执行；再次执行可重播示意，不增加已执行步骤数。")
    if state.current_stage == "pattern_emergence" and not state.current_stage_executed:
        st.caption("每次执行显示一段，共三段；这是界面分段，不是实际织造次数。")
    if len(state.executed_stages) == 6:
        st.success("六个教学步骤已执行。此记录不代表掌握真实织造技能。")


    left, right = st.columns([1.6, 1], gap="large")
    with left:
        reduced = st.checkbox("减少动态效果", key="twin_reduced_motion", persist_state="session")
        # st.html's HTML sanitizer strips inline SVG in Streamlit 1.63.
        # Only our validated, self-drawn document enters this native iframe;
        # no user HTML, scripts, uploads, external URLs, or knowledge text.
        st.iframe(render_twin_svg(state, reduced_motion=reduced), height="content")
        st.caption(stage.teaching_note)
    with right:
        st.subheader(f"当前步骤 · {stage.stage_index}/6 {stage.title}")
        st.markdown("**当前操作者**")
        st.write(stage.operator)
        st.markdown("**教学操作**")
        st.write(stage.description)
        st.markdown("**工艺说明 · 已有知识证据**")
        by_id = {item.id: item for item in knowledge}
        for ref in stage.claim_refs:
            item = by_id[ref["knowledge_id"]]
            claim = item.claims[ref["claim_index"]]
            st.write(claim.text)
            st.caption(f"{item.id} · 事实 {ref['claim_index'] + 1} · 南京云锦直接资料 · " + "、".join(claim.source_ids))

    with st.container(border=True, key="twin_state_panel"):
        st.subheader("数字孪生状态", icon=":material/data_object:")
        st.write(STATE_BOUNDARY)
        st.caption("当前为教学状态，并非实体织机传感器实时数据。")
        summary = learning_status(state)
        st.write(f"当前环节：{summary['当前环节']} · 体验进度：{summary['体验进度']}")
        st.caption(f"当前模式：{summary['当前模式']} · 已完成教学步骤：{summary['已完成教学步骤']} · 状态驱动：用户交互")
        for row_start in (0, 3):
            status_columns = st.columns(3)
            for column, (label, value) in zip(status_columns, summary['环节状态'][row_start:row_start + 3]):
                with column.container(border=True):
                    st.markdown(f"**{label}**")
                    st.write(value)
        st.caption(teaching_feedback(state))
        with st.expander("查看运行时 Twin State", expanded=False):
            st.json(state_snapshot(state))
            st.caption("以下是用于核验的原始状态变化，非实体测量值。")
            for change in state.last_changes:
                st.write(change)

    st.subheader("当前知识来源", icon=":material/source:")
    st.caption("证据范围：工艺事实为南京云锦直接资料；图形、分组、运动节奏和显示段数均为教学示意。")
    with st.expander("查看来源与原有核验状态", expanded=False):
        show_sources(stage.source_ids, sources)
    st.warning(stage.evidence_gaps)
    st.caption(stage.disclaimer)
    st.write(MISSING_CAPABILITIES)

    with st.container(border=True, key="twin_quiz_panel"):
        st.subheader("知识测验", icon=":material/quiz:")
        st.caption("用于现场学习反馈；结果只以匿名本地记录保存，不记录姓名、联系方式、上传图片、API内容或IP。")
        quiz = QUIZ_BY_STAGE[stage.id]
        selected = st.radio(
            quiz.question,
            list(range(len(quiz.options))),
            format_func=lambda index: quiz.options[index],
            key=f"quiz_choice_{stage.id}",
            horizontal=False,
        )
        st.button(
            "提交答案",
            key=f"quiz_submit_{stage.id}",
            icon=":material/check:",
            on_click=submit_quiz,
            args=(root, stage.id, selected),
        )
        evaluation = st.session_state.get("quiz_evaluations", {}).get(stage.id)
        if evaluation:
            if evaluation.is_correct:
                st.success("回答正确。")
            else:
                st.warning(f"这题还可以再看一遍。正确答案：{quiz.options[evaluation.correct_index]}")
            st.write(evaluation.explanation)
            st.caption("证据说明：" + evaluation.evidence_note)
        summary = evaluation_summary(st.session_state.get("quiz_evaluations", {}).values())
        st.caption(
            f"本会话已提交 {summary['answered']} 题，答对 {summary['correct']} 题。"
            "该统计仅用于小范围试用反馈，不能夸大为长期学习成效。"
        )

    st.button("向AI文化助手继续提问", key="twin_ask_guide", icon=":material/chat:",
              on_click=open_guide, args=(stage.ai_question,))
    st.caption("带入问题：" + stage.ai_question + "（跳转后由您提交，沿用现有证据约束回答。）")
