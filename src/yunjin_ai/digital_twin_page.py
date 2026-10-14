"""Native Streamlit controls around a runtime-state SVG view."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import streamlit as st

from .digital_twin import (
    MISSING_CAPABILITIES, MODES, PROCESS_BOUNDARY,
    STAGE_IDS, STATE_BOUNDARY, TITLES, VISUAL_BOUNDARY, TwinState,
    load_stages, state_snapshot, transition,
)
from .digital_twin_simulation import simulation_sample, simulation_series
from .digital_twin_3d import process_explanation, render_process_twin_3d
from .digital_twin_svg import render_twin_svg
from .learning_quiz import (
    QUIZ_BY_STAGE, anonymous_result_record, append_anonymous_result,
    evaluate_quiz, evaluation_summary,
)
from .twin_presentation import learning_status, teaching_feedback


STAGE_ACTION_LABELS = {
    "pattern_design": "显示设计草图",
    "pattern_translation": "演示挑花结本",
    "weaving_preparation": "完成织造准备",
    "warp_lifting": "提起对应经线",
    "weft_weaving": "推动梭子引纬",
    "pattern_emergence": "显示一段纹样",
}


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


@st.fragment(run_every="2s")
def show_exhibition_runtime() -> None:
    runtime_seconds = time.time()
    elapsed = runtime_seconds % 36.0
    sample = simulation_sample(elapsed)
    chart_data = simulation_series(runtime_seconds, points=24)

    def sparkline(values: list[float], label: str, unit: str, color: str, low: float, high: float) -> str:
        span = max(high - low, 0.001)
        bars = "".join(
            f'<i style="height:{max(8.0, min(100.0, (value - low) * 100.0 / span)):.1f}%;background:{color}"></i>'
            for value in values
        )
        return f'''<div class="yj-spark">
          <div><span>{label}</span><strong>{values[-1]:.1f} {unit}</strong></div>
          <div class="yj-spark-bars" role="img" aria-label="{label}最近24秒动态节奏">{bars}</div>
          <small><span>−24 s</span><span>现在</span></small>
        </div>'''
    st.html(
        f'''<section class="yj-status-strip">
          <div><small>WEAVING LOOP</small><strong>连续织造</strong><span>六步动作循环</span></div>
          <div><small>COLLABORATION</small><strong>上下层协同</strong><span>拽花工 · 织手</span></div>
          <div><small>TENSION</small><strong>{sample.tension_n:.2f} N</strong><span>仿真张力</span></div>
          <div><small>LIFT</small><strong>{sample.lift_mm:.1f} mm</strong><span>仿真位移</span></div>
        </section>'''
    )
    process_col, rhythm_col, boundary_col = st.columns([1.16, 1.0, .84], gap="medium", vertical_alignment="top")
    with process_col.container(border=True):
        st.html('<div class="yj-card-kicker">PROCESS OVERVIEW</div>')
        st.subheader("过程解读")
        st.markdown("**一梭纬线如何成为连续锦面？**")
        st.write("织手踩下踏板，经线分层形成梭口；梭子携带纬线穿过，筘框把它压向织口。新纬线与经线交织后，布面前进并由卷布轴收起。")
        st.caption("One pick becomes cloth through treadling, shedding, shuttle insertion, beating and take-up.")
        st.markdown("**线系关系**  \n红金上行线 · 提花控制绳；  \n前后走向线 · 经线与梭口；  \n左右运动线 · 梭子送入的纬线。")
    with rhythm_col.container(border=True):
        st.html('<div class="yj-card-kicker">PROCESS RHYTHM</div>')
        st.subheader("工艺节奏")
        st.caption("最近 24 秒仿真窗口 · 曲线持续滚动")
        st.html(
            '''<style>
            .yj-spark{margin:.55rem 0 .9rem}.yj-spark>div{display:flex;align-items:baseline;justify-content:space-between;color:#756b65;font-size:.78rem}
            .yj-spark strong{font:600 1rem/1.2 ui-sans-serif,system-ui;color:#352821}
            .yj-spark-bars{height:70px!important;margin:.35rem 0 .2rem;display:flex!important;align-items:flex-end;gap:3px;padding:0!important;border-bottom:1px solid #d9ccb9;background:repeating-linear-gradient(to top,transparent 0,transparent 22px,#e6dccd 23px,#e6dccd 24px)}
            .yj-spark-bars i{display:block!important;flex:1;min-width:2px;border-radius:4px 4px 1px 1px;opacity:.82;box-shadow:0 0 8px rgba(107,39,51,.08)}
            .yj-spark small{display:flex;justify-content:space-between;color:#9a8d82;font-size:.68rem;letter-spacing:.04em}
            </style>'''
            + sparkline([row["tension_n"] for row in chart_data], "仿真张力", "N", "#9a3546", 2.4, 4.1)
            + sparkline([row["lift_mm"] for row in chart_data], "仿真位移", "mm", "#2f6964", 0.0, 21.0)
        )
    with boundary_col.container(border=True):
        st.html('<div class="yj-card-kicker">EXHIBITION BOUNDARY</div>')
        st.subheader("展陈边界")
        st.write("当前画面用于解释结构关系与协同顺序，不是机械复原图纸。")
        st.markdown("**数据来源**")
        st.caption(sample.data_source)
        st.markdown("**展示状态**")
        st.caption("程序化循环 · 自动播放 · 无实体传感器连接")
        st.markdown("**织物说明**")
        st.caption("布面为程序化云锦风格示意，不对应具体历史实物纹样。")
        with st.expander("查看完整说明", expanded=False):
            st.write(VISUAL_BOUNDARY)


def show_exhibition_mode() -> None:
    # Keep the iframe mounted; its browser loop handles the animation.
    sample = simulation_sample(0.0)
    st.html('''<div class="yj-section-heading"><div><small>IMMERSIVE YUNJIN LOOM SHOWCASE</small><h2>沉浸织造</h2></div><p>观察上下层工匠如何协作，让一根纬线最终成为连续锦面。</p></div>''')
    with st.container(key="loom_showcase_frame"):
        st.iframe(render_process_twin_3d(sample, exhibition=True), height=650)
    show_exhibition_runtime()
    return

    with st.expander("过程解读 / Process overview", expanded=False):
        st.markdown("**" + explanation["title"] + "**")
        st.write(explanation["zh"])
        st.caption(explanation["en"])
        metrics = st.columns(4)
        metrics[0].metric("当前阶段 / Current Stage", sample.stage_title, f"{sample.stage_index}/6")
        metrics[1].metric("协同状态 / Human Coordination", sample.coordination_status)
        metrics[2].metric("织口状态", "连续生成")
        metrics[3].metric("展陈循环", "自动播放")

    with st.expander("工艺节奏参考 / Process rhythm", expanded=False):
        chart_left, chart_right = st.columns(2)
        with chart_left:
            st.markdown("**张力-时间 / Tension-Time**")
            st.line_chart(chart_data, x="time_s", y="tension_n", height=150)
        with chart_right:
            st.markdown("**位移-时间 / Lift-Time**")
            st.line_chart(chart_data, x="time_s", y="lift_mm", height=150)

    with st.expander("查看当前展示状态 / Exhibition state", expanded=False):
        st.json({
            "mode": "Exhibition Mode",
            "visualization_layer": "3D Process Digital Twin",
            "data_source": sample.data_source,
            "current_stage": sample.stage_title,
            "current_stage_id": sample.stage_id,
            "simulated_tension_n": sample.tension_n,
            "simulated_lift_mm": sample.lift_mm,
            "draw_worker_status": sample.draw_worker_status,
            "weaver_status": sample.weaver_status,
            "coordination_status": sample.coordination_status,
            "hardware_connected": False,
            "real_sensor_data": False,
        })

    st.caption("说明：以上数值只用于展示和比赛原型演示，不代表真实南京云锦织机测量值，也不是实验数据。")
def show_digital_twin(root: Path, knowledge, sources, open_guide: Callable[[str], None], show_sources: Callable) -> None:
    st.html('''<style>
    .stMainBlockContainer:has(.st-key-twin_state_panel) {padding-top:4rem;padding-bottom:2rem}
    .stMainBlockContainer:has(.st-key-twin_state_panel) [data-testid="stVerticalBlock"] {gap:.55rem}
    .stMainBlockContainer:has(.st-key-twin_state_panel) h1 {font-size:2rem;padding:.3rem 0 .5rem}
    .stMainBlockContainer:has(.st-key-twin_state_panel) h3 {font-size:1.2rem;padding:.2rem 0 .4rem}
    .stMainBlockContainer .stElementContainer{opacity:1!important;transition:opacity 0s!important}
    .yj-section-heading{display:flex;align-items:end;justify-content:space-between;gap:2rem;margin:1.4rem 0 .8rem;padding:0 .15rem}.yj-section-heading small,.yj-card-kicker{display:block;color:#a47730;font-size:.66rem;font-weight:850;letter-spacing:.18em}.yj-section-heading h2{margin:.18rem 0 0;padding:0;color:#321719;font-family:'Noto Serif SC','Source Han Serif SC','Songti SC',serif;font-size:2rem;line-height:1.1}.yj-section-heading p{max-width:620px;margin:0;color:#725d50;font-size:.9rem;text-align:right}
    .yj-status-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin:1rem 0 1.15rem;overflow:hidden;border:1px solid rgba(187,145,72,.35);border-radius:16px;background:rgba(187,145,72,.22);box-shadow:0 12px 32px rgba(72,38,25,.07)}.yj-status-strip>div{position:relative;min-width:0;padding:1rem 1.15rem;background:rgba(255,251,243,.92)}.yj-status-strip>div:before{content:'';position:absolute;left:0;top:22%;bottom:22%;width:2px;background:linear-gradient(#8f2f40,#d4b46b)}.yj-status-strip small{display:block;color:#9b783e;font-size:.58rem;font-weight:850;letter-spacing:.13em}.yj-status-strip strong{display:block;margin:.28rem 0 .08rem;color:#3b211d;font-size:1.08rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.yj-status-strip span{color:#8b786b;font-size:.72rem}
    @keyframes yj-live-sweep{0%{transform:translateX(-135%);opacity:0}18%{opacity:.7}72%{opacity:.45}100%{transform:translateX(520%);opacity:0}}
    @keyframes yj-bar-breathe{0%,100%{filter:saturate(.9);opacity:.72}50%{filter:saturate(1.18);opacity:1}}
    @keyframes yj-panel-rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
    .yj-status-strip:after{content:'';position:absolute;top:0;bottom:0;left:0;width:15%;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(255,225,151,.34),transparent);animation:yj-live-sweep 5.8s ease-in-out infinite}.yj-status-strip{position:relative}
    .yj-status-strip strong{font-variant-numeric:tabular-nums}.yj-spark-bars i{transform-origin:bottom;animation:yj-bar-breathe 2.8s ease-in-out infinite}.yj-spark-bars i:nth-child(3n+2){animation-delay:-.9s}.yj-spark-bars i:nth-child(3n){animation-delay:-1.8s}
    .st-key-loom_showcase_frame{position:relative;width:min(100%,1220px);margin-inline:auto;overflow:hidden;border-radius:20px;animation:yj-panel-rise .75s ease-out both}.st-key-loom_showcase_frame:after{content:'';position:absolute;inset:0;pointer-events:none;border-radius:20px;box-shadow:inset 0 0 0 1px rgba(224,188,103,.32),inset 0 -36px 80px rgba(73,28,29,.10)}
    .st-key-loom_showcase_frame{border:1px solid rgba(184,138,61,.36);background:#2d1c1b;box-shadow:0 24px 64px rgba(58,28,23,.17)}
    .yj-section-heading{padding-bottom:.65rem;border-bottom:1px solid rgba(173,126,49,.28)}.yj-section-heading h2{font-family:'Noto Serif SC','Source Han Serif SC','Songti SC',serif}.yj-section-heading p{color:#7d6b61}
    .yj-status-strip{border-color:rgba(173,126,49,.36);background:rgba(173,126,49,.24);box-shadow:0 14px 34px rgba(72,34,24,.075)}.yj-status-strip>div{background:linear-gradient(145deg,rgba(255,252,245,.97),rgba(248,238,220,.90))}.yj-status-strip>div:before{background:linear-gradient(#8f2e40,#d2ad5d)}
    [data-testid="stVerticalBlockBorderWrapper"]:has(.yj-card-kicker){border-color:rgba(173,126,49,.34)!important;background:linear-gradient(145deg,rgba(255,252,245,.96),rgba(248,238,220,.84));box-shadow:0 15px 36px rgba(72,34,24,.065),inset 0 1px 0 rgba(255,255,255,.94)}
    [data-testid="stVerticalBlockBorderWrapper"]:has(.yj-card-kicker) h3{font-family:'Noto Serif SC','Source Han Serif SC','Songti SC',serif;color:#3d201e}.yj-card-kicker{color:#9b7335}
    .yj-spark-bars{border-bottom-color:#d7c8b3!important}.yj-spark-bars i{background-image:linear-gradient(180deg,rgba(255,255,255,.20),rgba(61,24,27,.10))!important}
    @media(max-width:640px) {
      .stMainBlockContainer:has(.st-key-twin_state_panel) {padding-top:4rem}
      .stMainBlockContainer:has(.st-key-twin_state_panel) h1 {font-size:1.6rem}
      .yj-section-heading{display:block}.yj-section-heading p{margin-top:.55rem;text-align:left}.yj-status-strip{grid-template-columns:1fr 1fr}.yj-status-strip>div{padding:.8rem}
    }
    @media(prefers-reduced-motion:reduce){.yj-status-strip:after,.yj-spark-bars i,.st-key-loom_showcase_frame{animation:none!important}}
    </style>''')
    st.html('''
    <section class="yunjin-page-banner">
      <div class="yunjin-page-banner__kicker">Dahualou Drawloom · Digital Exhibition</div>
      <h1>南京云锦大花楼织机</h1>
      <p>上层拽花、下层织造——在一座可观察、可理解的数字织机中，看见经纬如何协同成锦。</p>
    </section>
    ''')
    st.caption("形制参考斜身式大花楼木织机。展示模式呈现连续协作；六阶段教学用于逐步理解结构关系。")
    try:
        stages = load_stages(root / "data/digital_twin/twin_states.json", knowledge, sources)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error("教学资料校验未通过，当前页面停止渲染，未补写文化事实。")
        st.caption(str(exc))
        return

    st.session_state.setdefault("twin_experience_mode", "Exhibition Mode / 展示模式")
    experience_mode = st.segmented_control(
        "观看方式",
        ["Exhibition Mode / 展示模式", "Teaching Mode / 教学模式"],
        format_func=lambda value: "沉浸展示" if value.startswith("Exhibition") else "六阶段教学",
        key="twin_experience_mode",
        required=True,
    )
    if experience_mode == "Exhibition Mode / 展示模式":
        show_exhibition_mode()
        return

    st.caption("按步骤操作，观察画面与教学状态如何变化；工艺说明均附有知识来源。")
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
    completed_count = len(state.executed_stages)
    st.progress(
        completed_count / 6,
        text=f"当前第 {stage.stage_index} 步：{stage.title} · 完成进度 {completed_count}/6",
    )

    with st.container(horizontal=True):
        st.button("上一步", key="twin_previous", disabled=index == 0,
                  on_click=apply_twin_event, args=("previous",))
        st.button(STAGE_ACTION_LABELS[stage.id], key="twin_execute", type="primary",
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
        st.subheader("教学状态", icon=":material/data_object:")
        st.write(STATE_BOUNDARY)
        st.caption("这里记录的是本次体验中的步骤变化，不是实体织机的实时测量数据。")
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
        with st.expander("查看教学状态技术详情", expanded=False):
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
            index=None,
        )
        if selected is None:
            st.caption("请选择一个答案后提交。")
        st.button(
            "提交答案",
            key=f"quiz_submit_{stage.id}",
            icon=":material/check:",
            on_click=submit_quiz,
            args=(root, stage.id, selected),
            disabled=selected is None,
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
