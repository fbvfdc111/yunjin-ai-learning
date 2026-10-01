from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.digital_twin_page import show_digital_twin
from yunjin_ai.knowledge import (
    load_knowledge,
    load_official_objects,
    load_official_relations,
    load_sources,
    related_official_objects,
    search_visual_knowledge,
)
from yunjin_ai.product import apply_guide_handoff, cultural_followup_questions, visual_observation_sections
from yunjin_ai.vision import analyze_image, dots_is_configured, openai_is_configured


DISCLAIMER = "本系统用于文化学习与数字化传承，不构成文物、工艺、年代或真伪专业鉴定。"
VISION_BOUNDARY = (
    "以上内容属于视觉观察与文化探索线索，不构成对南京云锦归属、具体工艺、年代、"
    "真伪或文物身份的专业鉴定。"
)
KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
TAB_LABELS = ["首页", "AI探锦", "数字织机", "AI文化助手", "数据与可信AI"]
EVIDENCE_SCOPE_LABELS = {
    "direct_yunjin": "南京云锦直接资料",
    "official_object_name": "官方对象名称/目录资料",
    "general_cultural_background": "一般传统文化背景",
    "governance_methodology": "数据治理说明",
}
QUICK_QUESTIONS = [
    "妆花是什么？",
    "四大品种有哪些有证据的区别？",
    "挑花结本是什么，有什么作用？",
    "南京云锦官方对象中有鹤纹吗？",
]
HOME_TOPICS = [
    ("云锦是什么？", "南京云锦是什么？", ":material/auto_stories:"),
    ("妆花工艺", "妆花是什么？", ":material/texture:"),
    ("主要品种", "南京云锦有哪些主要品种？", ":material/category:"),
    ("制作流程", "南京云锦的制作流程有哪些主要环节？", ":material/account_tree:"),
    ("传统纹样", "传统织物中常见哪些纹样题材与构图形式？", ":material/filter_vintage:"),
]


@st.cache_data
def load_data():
    sources = load_sources(KNOWLEDGE_DIR / "sources.json")
    knowledge = load_knowledge(KNOWLEDGE_DIR / "knowledge_base.json")
    official = load_official_objects(ROOT / "data" / "metadata" / "official_metadata.csv")
    relations = load_official_relations(KNOWLEDGE_DIR / "official_object_knowledge_map.json")
    return sources, knowledge, official, relations


def show_sources(source_ids, sources):
    for source_id in source_ids:
        source = sources[source_id]
        if source.url.startswith("http"):
            st.markdown(
                f"- **[{source_id}] [{source.title}]({source.url})** — {source.publisher}；"
                f"证据等级 {source.evidence_level}；访问日期 {source.accessed_at}"
            )
        else:
            st.markdown(
                f"- **[{source_id}] {source.title}** — {source.publisher}；"
                f"证据等级 {source.evidence_level}；本地路径 `{source.url}`"
            )
        if source.locator:
            st.caption(f"定位：{source.locator}；核验状态：{source.verification_status or '未注明'}")


def show_hits(hits, sources):
    for hit in hits:
        with st.container(border=True):
            st.caption(f"{hit.item.category} · {hit.item.id} · 证据等级 {hit.item.evidence_level}")
            st.subheader(hit.item.title)
            for claim in hit.item.claims:
                st.caption(EVIDENCE_SCOPE_LABELS[claim.evidence_scope])
                st.write(claim.text)
                st.caption("该事实来源：" + "、".join(f"[{source_id}]" for source_id in claim.source_ids))
    source_ids = tuple(dict.fromkeys(sid for hit in hits for sid in hit.item.source_ids))
    with st.expander("知识来源", expanded=True, icon=":material/source:"):
        show_sources(source_ids, sources)


def show_official_objects(rows):
    if not rows:
        st.caption("本次检索没有匹配到对象级名称记录。")
        return
    display = [
        {
            "对象编号": row["catalog_number"],
            "官网名称": row["official_name"],
            "名称中出现": row.get("_relation_terms", "—"),
            "关系依据": EVIDENCE_SCOPE_LABELS.get(row.get("_relation_scope", ""), "—"),
            "目录核验": row.get("_relation_verification", "—"),
            "授权状态": row["authorization_status"],
        }
        for row in rows
    ]
    st.dataframe(display, hide_index=True, width="stretch")
    st.caption(
        "关系只表示官方名称或目录资料中出现该词，不是图像鉴定、模型分类或训练标签。"
        "授权状态 unknown 的官网图片不展示，也不进入训练数据。"
    )


def open_cultural_guide(question: str) -> None:
    apply_guide_handoff(st.session_state, question)
    st.session_state.pop("last_answer", None)
    st.session_state.pop("last_question", None)


def set_guide_question(question: str) -> None:
    st.session_state["guide_question"] = question
    st.session_state.pop("last_answer", None)
    st.session_state.pop("last_question", None)


st.set_page_config(
    page_title="南京云锦智能识别与数字化传承",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed",
)
sources, knowledge, official_rows, official_relations = load_data()
st.session_state.setdefault("guide_question", "")
st.session_state.setdefault("main_tab", "首页")
st.session_state.setdefault("guide_history", [])
if st.session_state["main_tab"] == "AI识锦":
    st.session_state["main_tab"] = "AI探锦"

with st.sidebar:
    st.header("系统状态", icon=":material/monitor_heart:")
    st.success("本地知识库与可信检索：可用")
    st.success("本地图像统计 fallback：可用")
    st.write("Dots Studio：" + ("已配置" if dots_is_configured() else "未配置，将回退 local_cv"))
    st.write("OpenAI provider：" + ("已配置" if openai_is_configured() else "保留，当前未配置"))
    st.caption("未训练监督分类模型，不生成 Accuracy、F1、Loss、混淆矩阵或模型权重。")

active_tab = st.segmented_control(
    "主导航",
    TAB_LABELS,
    key="main_tab",
    selection_mode="single",
    required=True,
    label_visibility="collapsed",
)

if active_tab == "首页":
    st.title("南京云锦智能识别与数字化传承")
    st.header("让 AI 看见纹样，让文化知识有据可查。")
    st.write(
        "上传传统织锦图片，AI观察纹样、构图与色彩，并连接可信文化知识来源，"
        "帮助用户探索南京云锦背后的纹样文化与传统工艺。"
    )
    st.markdown("**看见云锦 → 理解云锦 → 体验云锦**")
    st.caption("从 AI探锦的视觉线索出发，在可信文化知识与AI文化助手中理解，再到数字织机交互体验。")
    st.button("体验云锦织造", key="home_open_twin", type="primary",
              on_click=lambda: st.session_state.update(main_tab="数字织机"))

    capability_columns = st.columns(3)
    capabilities = [
        ("看见云锦 · AI探锦", "上传图片，观察纹样、构图与色彩，获得文化探索线索。", ":material/visibility:"),
        ("理解云锦 · 可信知识", "连接可信来源，在AI文化助手中继续获得证据约束解释。", ":material/menu_book:"),
        ("体验云锦 · 数字织机", "亲手执行六个教学步骤，观察交互状态如何驱动画面。", ":material/verified:"),
    ]
    for column, (title, text, icon) in zip(capability_columns, capabilities):
        with column.container(border=True, height="stretch"):
            st.subheader(title, icon=icon)
            st.write(text)

    st.subheader("探索云锦文化", icon=":material/auto_stories:")
    st.caption("从知识库已经有可靠来源支持的主题开始了解。")
    topic_columns = st.columns(3)
    for index, (label, question, icon) in enumerate(HOME_TOPICS):
        topic_columns[index % 3].button(
            label,
            icon=icon,
            key=f"home_topic_{index}",
            on_click=open_cultural_guide,
            args=(question,),
            width="stretch",
        )

    with st.expander("项目数据基础", icon=":material/database:"):
        data_columns = st.columns(4)
        data_columns[0].metric("官网证据对象", len(official_rows))
        data_columns[1].metric("南京云锦对象", sum(r["level1_label"] == "nanjing_yunjin" for r in official_rows))
        data_columns[2].metric("其他织锦对象", sum(r["level1_label"] == "other_brocade" for r in official_rows))
        data_columns[3].metric("可直接训练南京云锦对象", 0)
        st.caption(
            "95 个官网对象仅作为 Official Evidence Database；authorization_status 均为 unknown，"
            "usable_for_training 均为 false。该事实不会因产品展示需要而隐藏。"
        )

    st.subheader("长期生态框架", icon=":material/account_tree:")
    st.write("AI + Digital Twin + Immersive Learning + Community Participation")
    st.caption(
        "当前 MVP 实现 AI视觉理解、文化知识库、evidence-grounded RAG，"
        "以及知识驱动、状态驱动的南京云锦织造教学型数字孪生原型（数字织机）。"
        "数字状态由用户交互驱动；实体织机实时双向同步、Immersive Learning、Community Participation 属于后续工作。"
    )

if active_tab == "AI探锦":
    st.header("AI探锦", icon=":material/image_search:")
    st.subheader("上传一张织锦图片")
    st.write("AI 将从纹样、构图与色彩等可观察特征出发，为你连接相关文化知识。")

    with st.expander("技术详情 / Technical Details", icon=":material/tune:"):
        st.caption("默认使用 Dots；未配置 API Key 或调用失败时会明确回退到 local_cv。")
        provider_label = st.segmented_control(
            "视觉 provider",
            ["dots", "local_cv", "openai"],
            default="dots",
            required=True,
            key="vision_provider",
        )
        dots_image_url = None
        if provider_label == "dots":
            dots_image_url = st.text_input(
                "Dots 图片公网 URL（高级选项，可留空）",
                placeholder="https://example.org/path/image.jpg",
                help="填写后优先使用公网 URL；留空则把本地上传图片在内存中编码为 Base64 data URL。",
                key="dots_image_url",
            )
            st.caption(
                "本地 JPG/JPEG/PNG 通过内存 Base64 data URL 发送，不发送本地文件路径，也不上传第三方图床。"
                "原始上传最大 10 MB；发送前必要时压缩至不超过 4 MB、最长边不超过 2048 px。"
            )
            st.code("https://note3-prev-api.askdiandian.com/v1/chat/completions", language=None)
        st.write("Dots 配置状态：" + ("已配置" if dots_is_configured() else "未配置"))
        st.write("OpenAI 配置状态：" + ("已配置" if openai_is_configured() else "未配置"))

    uploaded = st.file_uploader(
        "选择图片", type=["jpg", "jpeg", "png"], help="支持 JPG、JPEG、PNG，最大 10 MB。", key="vision_upload"
    )
    if uploaded:
        image_bytes = uploaded.getvalue()
        digest = hashlib.sha256(image_bytes).hexdigest()
        if len(image_bytes) > 10 * 1024 * 1024:
            st.error("文件超过 10 MB，未处理。")
        else:
            try:
                image = Image.open(uploaded)
                image_mime_type = {"JPEG": "image/jpeg", "PNG": "image/png"}.get((image.format or "").upper())
                image.load()
                image = image.convert("RGB")
                st.image(image, caption=f"用户上传图片 · SHA-256 {digest[:12]}…", width=520)
            except (UnidentifiedImageError, OSError) as exc:
                st.error(f"无法解码该图片：{exc}")
                image = None

            if image is not None and st.button(
                "开始 AI 分析", type="primary", icon=":material/auto_awesome:", key="analyze_image"
            ):
                requested = provider_label or "dots"
                with st.spinner("AI 正在观察图片并提取文化检索线索……"):
                    try:
                        result = analyze_image(
                            image,
                            provider=requested,
                            image_url=dots_image_url,
                            image_mime_type=image_mime_type,
                            image_bytes=image_bytes,
                        )
                        st.session_state["vision_result"] = result
                        st.session_state["vision_signature"] = (digest, requested, dots_image_url or "")
                        if requested == "dots" and result.provider == "local_cv":
                            st.warning("Dots 未成功调用，已明确回退到本地图像统计。详情见技术折叠区。")
                    except Exception as exc:
                        st.error(f"所选 provider 未成功调用：{exc}")
                        st.info("未把失败包装成成功结果。你可以在技术详情中选择 local_cv 继续。")

            result = st.session_state.get("vision_result")
            signature = (digest, provider_label or "dots", dots_image_url or "")
            if result and st.session_state.get("vision_signature") == signature:
                st.header("AI视觉观察")
                sections = visual_observation_sections(result)
                section_columns = st.columns(3)
                for column, section_name in zip(section_columns, ("纹样与主体", "构图特征", "色彩特征")):
                    with column.container(border=True, height="stretch"):
                        st.subheader(section_name)
                        facts = sections[section_name]
                        if facts:
                            for fact in facts:
                                st.write(fact)
                        else:
                            st.caption("本次分析未给出这一类明确观察。")

                with st.container(border=True):
                    st.subheader("视觉关键词")
                    if result.retrieval_keywords:
                        st.write(" · ".join(result.retrieval_keywords))
                    else:
                        st.caption("本次分析未提取到可用视觉关键词。")

                st.subheader("AI分析边界")
                st.warning(VISION_BOUNDARY, icon=":material/gpp_maybe:")

                requested_provider = signature[1]
                image_transport = result.raw_metrics.get("image_transport")
                if not image_transport:
                    image_transport = "local_cv" if result.provider == "local_cv" else "base64_data_url"
                fallback_reason = result.raw_metrics.get("fallback_reason", "无")
                with st.expander("技术详情 / Technical Details：本次调用", icon=":material/code:"):
                    st.write(f"Requested provider：`{requested_provider}`")
                    st.write(f"Actual provider：`{result.provider}`")
                    st.write(f"Image transport：`{image_transport}`")
                    st.write(f"Fallback reason：{fallback_reason}")
                    st.caption(result.provider_status)
                    st.json(result.raw_metrics)
                    st.markdown("**Provider 输出限制**")
                    for limitation in result.limitations:
                        st.write("- " + limitation)

                candidate_labels = ["龙", "凤", "鹤", "莲", "寿", "八宝", "宝灯", "灵芝", "牡丹", "织金", "妆花", "库锦", "库缎"]
                verified = st.multiselect(
                    "希望继续探索的文化主题（可选）",
                    candidate_labels,
                    help="这里选择的是学习主题，不表示你或系统确认了图片中的纹样、工艺或对象身份。",
                    key="confirmed_visual_topics",
                )
                hits = search_visual_knowledge(
                    [*result.retrieval_keywords, *result.tentative_elements], verified, knowledge, limit=4
                )
                st.header("相关文化知识")
                st.caption(
                    "仅展示达到最低相关门槛的本地知识条目。以下是文化探索线索，"
                    "不能反向证明上传图片包含某种纹样或属于某种工艺。"
                )
                if hits:
                    show_hits(hits, sources)
                    with st.expander("相关官方对象 metadata", icon=":material/table_view:"):
                        show_official_objects(related_official_objects(hits, official_rows, official_relations))

                    st.subheader("继续向 AI 文化助手提问", icon=":material/chat:")
                    st.caption("建议问题来自已检索到的文化主题，不代表对图片内容作出鉴定。")
                    with st.container(horizontal=True):
                        for index, question in enumerate(cultural_followup_questions(hits)):
                            st.button(
                                question,
                                key=f"vision_followup_{index}",
                                on_click=open_cultural_guide,
                                args=(question,),
                            )
                else:
                    st.info("当前视觉线索不足以匹配到高可信度的文化知识。")
                    st.caption(
                        "当前还没有足够的文化知识匹配。你仍可以进入 AI文化助手，"
                        "了解南京云锦的制作工艺、主要品种与传统纹样文化。"
                    )
                    st.subheader("从这些文化主题继续")
                    with st.container(horizontal=True):
                        for index, question in enumerate(cultural_followup_questions(())):
                            st.button(
                                question,
                                key=f"vision_general_followup_{index}",
                                on_click=open_cultural_guide,
                                args=(question,),
                            )

if active_tab == "数字织机":
    show_digital_twin(ROOT, knowledge, sources, open_cultural_guide, show_sources)

if active_tab == "AI文化助手":
    st.header("AI文化助手", icon=":material/chat:")
    st.write(
        "你好，我是云锦文化 AI 助手。你可以向我了解南京云锦的品种、纹样文化、制作工艺与传承知识。"
        "每次回答都先检查本地知识库是否有证据能够直接回答。"
    )
    st.caption("本助手不会绕过知识库补写文化事实；证据不足时会明确说明。")

    st.subheader("快捷问题")
    quick_columns = st.columns(2)
    for index, question in enumerate(QUICK_QUESTIONS):
        quick_columns[index % 2].button(
            question, key=f"quick_question_{index}", on_click=set_guide_question, args=(question,)
        )

    with st.form("guide_question_form", border=False):
        question = st.text_input("你想了解什么？", key="guide_question", placeholder="例如：妆花是什么？")
        submitted = st.form_submit_button(
            "获取可信回答", type="primary", icon=":material/search:", width="stretch"
        )

    if submitted and question.strip():
        clean_question = question.strip()
        answer = answer_from_knowledge(clean_question, knowledge, sources)
        st.session_state["last_question"] = clean_question
        st.session_state["last_answer"] = answer
        st.session_state["guide_history"].append({"question": clean_question, "answer": answer})

    answer_slot = st.container(key="guide_answer_slot")
    with answer_slot:
        for turn_index, turn in enumerate(st.session_state["guide_history"]):
            answer = turn["answer"]
            with st.chat_message("user"):
                st.write(turn["question"])
            with st.chat_message("assistant", avatar=":material/auto_awesome:"):
                st.caption(answer.status)
                for claim in answer.claims:
                    st.caption(EVIDENCE_SCOPE_LABELS[claim.evidence_scope])
                    st.write(claim.text)
                    st.caption("该事实来源：" + "、".join(f"[{source_id}]" for source_id in claim.source_ids))

                if answer.source_ids:
                    levels = tuple(
                        dict.fromkeys(sources[source_id].evidence_level for source_id in answer.source_ids)
                    )
                    with st.expander("查看知识来源与证据", icon=":material/source:"):
                        show_sources(answer.source_ids, sources)
                        st.markdown("**证据等级：** " + "、".join(levels))
                    with st.expander("相关官方对象 metadata", icon=":material/table_view:"):
                        show_official_objects(
                            related_official_objects(answer.hits, official_rows, official_relations)
                        )
                else:
                    st.warning("本地知识库证据不足，系统没有调用大模型补写文化事实。")

        if st.session_state["guide_history"]:
            latest_answer = st.session_state["guide_history"][-1]["answer"]
            st.subheader("继续了解")
            with st.container(horizontal=True):
                for index, followup in enumerate(cultural_followup_questions(latest_answer.hits)):
                    st.button(
                        followup,
                        key=f"guide_followup_{index}",
                        on_click=set_guide_question,
                        args=(followup,),
                    )

if active_tab == "数据与可信AI":
    st.header("数据与可信AI", icon=":material/verified_user:")

    st.subheader("① 数据从哪里来？")
    st.write(
        "项目整理了 95 个带对象级来源记录的官网对象，作为 Official Evidence Database："
        "南京云锦 47 个、其他织锦 48 个。它们用于证据核验、知识组织和数据治理，不等于训练集。"
    )
    trust_metrics = st.columns(4)
    trust_metrics[0].metric("Official Evidence Database", 95)
    trust_metrics[1].metric("南京云锦", 47)
    trust_metrics[2].metric("其他织锦", 48)
    trust_metrics[3].metric("南京云锦可直接训练", 0)

    st.subheader("② 为什么没有训练分类器？")
    st.write(
        "95 个官网对象的 authorization_status 均为 unknown，usable_for_training 均为 false。"
        "公开可访问不等于获得监督训练授权，因此当前没有训练监督分类器。"
    )
    st.warning(
        "当前没有 Accuracy、Precision、Recall、F1、Loss、confusion matrix 或模型权重；"
        "页面不会把多模态模型的一次成功调用包装成分类准确率或系统性能验证。"
    )

    st.subheader("③ AI 怎样降低误判和文化幻觉？")
    st.markdown(
        """
- 视觉 provider 只负责可观察特征和检索关键词，不直接提供可信文化事实。
- 文化事实只从本地知识库检索，并展示来源与证据等级。
- 泛化视觉词不会单独触发具体纹样知识；没有足够相关证据时明确拒绝强行匹配。
- 视觉观察、人工选择和来源支持事实分层展示，不能互相反向证明。
- 一般传统文化背景与南京云锦直接资料分开存储、检索和展示；跨媒介寓意不用于判断具体对象。
- 官方对象关系只来自名称或目录文字，不是图像鉴定、模型分类或训练标签。
- 对归属、具体工艺、年代、真伪和文物身份始终保留专业鉴定边界。
        """
    )

    with st.expander("查看技术与数据治理详情", icon=":material/data_table:"):
        st.markdown(
            """
- Official Evidence Database = 95
- 南京云锦 = 47；其他织锦 = 48
- 95 个 `authorization_status = unknown`
- 95 个 `usable_for_training = false`
- 南京云锦可直接训练对象 = 0
- 12 个 Level 2 名称仅作 Candidate Knowledge Labels
- 未训练监督分类器；无 Accuracy / Precision / Recall / F1 / Loss / confusion matrix / weights
            """
        )
        show_official_objects(official_rows)

    with st.expander("Provider 与外部传输", icon=":material/cloud:"):
        st.write(
            "Dots 是当前默认视觉 provider。本地上传图片可在内存中编码为 Base64 data URL 后直接发送。"
            "缺少 Key、调用失败或响应无法解析时明确回退 local_cv，并在技术详情中披露实际 provider、传输方式和原因。"
        )
        st.write("local_cv 不上传图片；OpenAI provider 仍保留但不是当前默认 provider。")
        st.write(
            "Dots Base64 已由用户在实际运行环境完成一次真实成功调用验证；自动化测试仍使用 mock，"
            "这项验证仅证明调用链可运行，不代表识别准确率或系统性能。"
        )

    with st.expander("全部知识来源与证据等级", icon=":material/source:"):
        st.write("A：联合国/国家级官方非遗资料；B：官方文化机构研究或解读；C：本项目可追溯的数据治理记录。")
        show_sources(tuple(sources), sources)

    st.subheader("Future Work / 后续阶段")
    st.write(
        "数字织机已实现知识驱动、状态驱动的南京云锦织造教学型数字孪生原型，数字状态由用户交互驱动。"
        "当前没有实体传感器、实体织机实时数据同步、物理参数仿真和专家级机械结构验证；"
        "物理实体—数字模型的实时双向同步、Immersive Learning、Community Participation 属于后续工作。"
    )
    st.error(DISCLAIMER)
