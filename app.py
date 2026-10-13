from __future__ import annotations

import base64
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


def show_page_banner(kicker: str, title: str, description: str) -> None:
    """Render the same red-gold title card used by the digital loom page."""
    st.html(
        f"""
        <section class="yunjin-page-banner">
          <div class="yunjin-page-banner__kicker">{kicker}</div>
          <h1>{title}</h1>
          <p>{description}</p>
        </section>
        """
    )


st.set_page_config(
    page_title="南京云锦智能识别与数字化传承",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def apply_yunjin_visual_system() -> None:
    """Apply a restrained brocade-inspired visual language across the app."""
    st.html(
        """
        <style>
        :root {--yj-cinnabar:#962d3e;--yj-lacquer:#321719;--yj-gold:#c9a052;--yj-pale-gold:#ead7a5;--yj-indigo:#315a59;--yj-ink:#2b1b18;--yj-paper:#fbf5e9}
        .stApp {color:var(--yj-ink);background:radial-gradient(circle at 5% 3%,rgba(150,45,62,.13),transparent 27rem),radial-gradient(circle at 94% 18%,rgba(49,90,89,.10),transparent 25rem),repeating-linear-gradient(135deg,rgba(201,160,82,.035) 0 1px,transparent 1px 12px),linear-gradient(180deg,#fffaf1 0%,#f7eddd 100%)}
        .stApp:before {content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.22;background-image:radial-gradient(circle at 16px 16px,transparent 0 10px,rgba(150,45,62,.16) 10.5px 11.5px,transparent 12px),radial-gradient(circle at 48px 48px,transparent 0 10px,rgba(49,90,89,.13) 10.5px 11.5px,transparent 12px);background-size:64px 64px;mask-image:linear-gradient(90deg,rgba(0,0,0,.45),transparent 24%,transparent 76%,rgba(0,0,0,.35))}
        [data-testid="stHeader"] {background:rgba(255,250,241,.83);border-bottom:1px solid rgba(201,160,82,.35);backdrop-filter:blur(14px)}
        .stMainBlockContainer {max-width:1480px;padding-top:4.9rem;padding-bottom:4rem}
        h1,h2,h3 {color:var(--yj-lacquer);letter-spacing:-.025em} h1 {font-weight:800!important;position:relative} h1:after {content:"";display:block;width:4.8rem;height:3px;margin-top:.55rem;border-radius:9px;background:linear-gradient(90deg,var(--yj-cinnabar),var(--yj-gold),transparent)} h2 {font-weight:760!important} h3 {font-weight:720!important} p,li {line-height:1.78} [data-testid="stCaptionContainer"] {color:#79665c}
        [data-testid="stSegmentedControl"] {margin-bottom:.8rem} [data-testid="stSegmentedControl"] > div {padding:.3rem;border:1px solid rgba(201,160,82,.55);border-radius:999px;background:rgba(255,250,241,.76);box-shadow:0 10px 28px rgba(71,34,24,.08);backdrop-filter:blur(10px)} [data-testid="stSegmentedControl"] button {border-radius:999px!important;font-weight:700;letter-spacing:.02em} [data-testid="stSegmentedControl"] button[aria-checked="true"] {color:#fff8e8!important;background:linear-gradient(135deg,#7f2032,#aa3548)!important;box-shadow:inset 0 0 0 1px rgba(239,211,145,.34),0 6px 15px rgba(126,31,48,.22)}
        [data-testid="stVerticalBlockBorderWrapper"] {border-color:rgba(201,160,82,.48)!important;border-radius:18px!important;background:linear-gradient(145deg,rgba(255,252,245,.92),rgba(246,235,218,.78));box-shadow:0 15px 34px rgba(64,34,22,.08),inset 0 1px 0 rgba(255,255,255,.9)}
        [data-testid="stExpander"] {border-color:rgba(201,160,82,.42)!important;border-radius:14px!important;background:rgba(255,251,244,.68);box-shadow:0 8px 24px rgba(61,31,23,.045);overflow:hidden} [data-testid="stExpander"] summary {font-weight:700;color:#4d2726}
        [data-testid="stMetric"] {padding:.8rem 1rem;border-left:3px solid var(--yj-gold);border-radius:4px 14px 14px 4px;background:rgba(255,250,240,.70)}
        .stButton > button {border-color:rgba(150,45,62,.33);border-radius:12px;font-weight:700;transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}.stButton > button:hover {transform:translateY(-2px);border-color:var(--yj-gold);box-shadow:0 10px 24px rgba(88,37,30,.12)}.stButton > button[kind="primary"] {color:#fff8e8;border:1px solid rgba(234,215,165,.40);background:linear-gradient(135deg,#7d1f31 0%,#a63748 62%,#7d1f31 100%);box-shadow:0 10px 24px rgba(125,31,49,.22)}
        [data-testid="stAlert"] {border-radius:14px;border-color:rgba(201,160,82,.46)} [data-testid="stSidebar"] {background:linear-gradient(180deg,#35191b,#241517);color:#f7ead6;border-right:1px solid #a77f43}[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p {color:#f7ead6}
        .yunjin-hero {position:relative;min-height:350px;margin:.35rem 0 1.7rem;padding:clamp(2rem,5vw,4.4rem);overflow:hidden;border:1px solid rgba(231,198,119,.54);border-radius:26px;color:#fff5dc;background:radial-gradient(circle at 77% 30%,rgba(225,190,105,.25),transparent 21%),repeating-linear-gradient(118deg,rgba(255,222,149,.055) 0 1px,transparent 1px 11px),linear-gradient(125deg,#2a1518 0%,#5f1d2a 52%,#8d2b3c 100%);box-shadow:0 28px 70px rgba(59,25,22,.22),inset 0 0 0 7px rgba(255,238,197,.035)}
        .yunjin-hero:before,.yunjin-hero:after {content:"";position:absolute;border:1px solid rgba(235,204,127,.33);border-radius:50%;transform:rotate(-18deg)}.yunjin-hero:before {width:420px;height:190px;right:-70px;top:14px;box-shadow:0 0 0 26px rgba(235,204,127,.045),0 0 0 52px rgba(235,204,127,.025)}.yunjin-hero:after {width:340px;height:150px;right:30px;bottom:-100px}
        .yunjin-hero__eyebrow {font-size:.78rem;font-weight:800;letter-spacing:.24em;color:#efd28e;text-transform:uppercase}.yunjin-hero h1 {max-width:760px;margin:.7rem 0 .75rem;color:#fff7e7;font-size:clamp(2.4rem,5vw,4.8rem);line-height:1.08;letter-spacing:.015em;text-shadow:0 8px 28px rgba(18,7,8,.35)}.yunjin-hero h1:after {display:none}.yunjin-hero p {max-width:700px;margin:0;color:rgba(255,245,220,.84);font-size:1.07rem;line-height:1.85}.yunjin-hero__tags {display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1.35rem}.yunjin-hero__tags span {padding:.42rem .72rem;border:1px solid rgba(239,210,142,.34);border-radius:999px;background:rgba(38,13,18,.28);color:#f4dca3;font-size:.78rem;font-weight:700;backdrop-filter:blur(7px)}.yunjin-seal {position:absolute;right:7.5%;top:33%;display:grid;place-items:center;width:112px;height:112px;border:2px solid rgba(255,226,162,.74);color:#ffe6ae;font:800 2rem/1 serif;letter-spacing:.12em;transform:rotate(5deg);box-shadow:inset 0 0 0 5px rgba(255,226,162,.08)}
        .yunjin-page-banner {position:relative;margin:.2rem 0 1rem;padding:1.55rem 1.8rem 1.4rem 2rem;overflow:hidden;border:1px solid rgba(201,160,82,.55);border-radius:18px;color:#fff3d6;background:linear-gradient(112deg,#2c1818 0%,#6c2330 68%,#315a59 140%);box-shadow:0 18px 42px rgba(66,29,23,.15)}.yunjin-page-banner:after {content:"锦";position:absolute;right:2.2rem;top:-1.15rem;color:rgba(237,208,139,.10);font:800 9rem/1 serif}.yunjin-page-banner__kicker {color:#e6c77e;font-size:.72rem;font-weight:800;letter-spacing:.22em;text-transform:uppercase}.yunjin-page-banner h1 {margin:.38rem 0 .25rem;color:#fff7e6;font-size:clamp(1.8rem,3.2vw,3rem);line-height:1.18}.yunjin-page-banner h1:after {display:none}.yunjin-page-banner p {max-width:920px;margin:0;color:rgba(255,244,218,.78)}
        @media(max-width:760px){.stMainBlockContainer{padding-top:4.4rem}.yunjin-hero{min-height:330px;padding:2rem 1.35rem 2.3rem}.yunjin-seal{display:grid;right:1.2rem;top:1.15rem;width:58px;height:58px;font-size:1rem;border-width:1px;opacity:.82}.yunjin-hero h1{max-width:72%;font-size:2.25rem;margin-top:1.3rem}.yunjin-hero p{font-size:.95rem;line-height:1.65}.yunjin-page-banner{padding:1.25rem 1.15rem}.yunjin-page-banner:after{right:.4rem;font-size:6rem}[data-testid="stSegmentedControl"] [role="radiogroup"]{display:flex;overflow-x:auto;scrollbar-width:none}[data-testid="stSegmentedControl"] label{flex:0 0 auto;white-space:nowrap}}
        @media(max-width:440px){.yunjin-hero h1{max-width:100%;padding-right:54px;font-size:2rem}.yunjin-hero__tags{gap:.36rem}.yunjin-hero__tags span{font-size:.68rem;padding:.35rem .52rem}}
        </style>
        """
    )


apply_yunjin_visual_system()


def apply_yunjin_motion_system() -> None:
    """Add calm exhibition motion without competing with the loom animation."""
    st.html(
        """
        <style>
        @keyframes yj-pattern-drift {to {background-position:64px 32px,-64px -32px}}
        @keyframes yj-hero-breathe {0%,100% {box-shadow:0 28px 70px rgba(59,25,22,.22),inset 0 0 0 7px rgba(255,238,197,.035)}50% {box-shadow:0 34px 86px rgba(112,35,48,.30),inset 0 0 0 7px rgba(255,238,197,.065)}}
        @keyframes yj-cloud-float {0%,100% {transform:translate3d(0,0,0) rotate(-18deg)}50% {transform:translate3d(-24px,-9px,0) rotate(-15deg)}}
        @keyframes yj-gold-sweep {0% {transform:translateX(-155%) skewX(-22deg)}58%,100% {transform:translateX(460%) skewX(-22deg)}}
        @keyframes yj-seal-glow {0%,100% {opacity:.09;transform:scale(.96)}50% {opacity:.16;transform:scale(1.03)}}
        .stApp:before {animation:yj-pattern-drift 30s linear infinite}.yunjin-hero {animation:yj-hero-breathe 6.5s ease-in-out infinite}.yunjin-hero:after {animation:yj-cloud-float 9s ease-in-out infinite}
        .yunjin-page-banner:before {content:"";position:absolute;top:-35%;bottom:-35%;left:-18%;width:11%;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(255,227,155,.23),transparent);animation:yj-gold-sweep 6.8s ease-in-out infinite}.yunjin-page-banner:after {animation:yj-seal-glow 5s ease-in-out infinite}
        [data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"] {transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease}[data-testid="stVerticalBlockBorderWrapper"]:hover {transform:translateY(-1px);border-color:rgba(150,45,62,.40)!important;box-shadow:0 13px 30px rgba(82,34,28,.08),inset 0 1px 0 rgba(255,255,255,.94)}[data-testid="stExpander"]:hover {border-color:rgba(201,160,82,.78)!important;box-shadow:0 11px 28px rgba(81,39,27,.085)}
        [data-testid="stIFrame"] {border-radius:18px;box-shadow:0 20px 48px rgba(50,23,19,.16);transition:box-shadow .35s ease}[data-testid="stIFrame"]:hover {box-shadow:0 25px 64px rgba(101,35,44,.23),0 0 0 1px rgba(201,160,82,.34)}
        @media (prefers-reduced-motion:reduce){.stApp:before,.yunjin-hero,.yunjin-hero:after,.yunjin-page-banner:before,.yunjin-page-banner:after{animation:none!important}[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"],.stButton>button{transition:none!important}}
        </style>
        """
    )


apply_yunjin_motion_system()


def apply_yunjin_home_motion_details() -> None:
    st.html(
        """
        <style>
        @keyframes yj-thread-flow {0% {transform:translateX(-118%);opacity:0}12% {opacity:.85}78% {opacity:.72}100% {transform:translateX(135%);opacity:0}}
        @keyframes yj-tag-rise {0%,18% {transform:translateY(12px);opacity:0}42%,100% {transform:translateY(0);opacity:1}}
        @keyframes yj-seal-drift {0%,100% {transform:rotate(5deg) translateY(0)}50% {transform:rotate(2deg) translateY(-8px)}}
        @keyframes yj-title-glow {0%,100% {text-shadow:0 8px 28px rgba(18,7,8,.35)}50% {text-shadow:0 8px 34px rgba(255,208,114,.20),0 0 2px rgba(255,241,202,.4)}}
        .yunjin-weave-motion {position:absolute;inset:0;overflow:hidden;pointer-events:none;mix-blend-mode:screen}.yunjin-weave-motion span {position:absolute;left:0;width:62%;height:1px;background:linear-gradient(90deg,transparent,rgba(255,225,145,.08),rgba(255,225,145,.78),rgba(255,225,145,.08),transparent);animation:yj-thread-flow 6.2s linear infinite}.yunjin-weave-motion span:nth-child(1){top:24%;animation-delay:-1.2s}.yunjin-weave-motion span:nth-child(2){top:42%;animation-delay:-3.8s;animation-duration:7.4s}.yunjin-weave-motion span:nth-child(3){top:63%;animation-delay:-2.3s;animation-duration:5.8s}.yunjin-weave-motion span:nth-child(4){top:79%;animation-delay:-5.1s;animation-duration:8.2s}
        .yunjin-hero h1 {animation:yj-title-glow 5s ease-in-out infinite}.yunjin-seal {animation:yj-seal-drift 5.8s ease-in-out infinite}.yunjin-hero__tags span {animation:yj-tag-rise 2.4s ease both}.yunjin-hero__tags span:nth-child(2){animation-delay:.16s}.yunjin-hero__tags span:nth-child(3){animation-delay:.32s}.yunjin-hero__tags span:nth-child(4){animation-delay:.48s}
        @media(prefers-reduced-motion:reduce){.yunjin-weave-motion span,.yunjin-hero h1,.yunjin-seal,.yunjin-hero__tags span{animation:none!important}}
        </style>
        """
    )


apply_yunjin_home_motion_details()


def apply_yunjin_spectacle_layer() -> None:
    """Add a stronger, still culturally grounded exhibition atmosphere."""
    st.html(
        """
        <style>
        @keyframes yj-aurora-roam {0%,100% {transform:translate3d(-8%,-5%,0) scale(.92);opacity:.35}48% {transform:translate3d(18%,10%,0) scale(1.14);opacity:.72}72% {transform:translate3d(3%,18%,0) scale(1.02);opacity:.48}}
        @keyframes yj-shuttle-run {0% {left:-8%;opacity:0;filter:blur(1px)}8% {opacity:1}46% {opacity:1}54% {left:103%;opacity:0}55% {left:103%;transform:rotate(180deg);opacity:0}63% {opacity:1}94% {opacity:1}100% {left:-8%;transform:rotate(180deg);opacity:0}}
        @keyframes yj-dust-float {0%,100% {transform:translate3d(0,8px,0) scale(.65);opacity:.16}45% {transform:translate3d(12px,-18px,0) scale(1.15);opacity:.86}72% {transform:translate3d(-7px,-6px,0) scale(.84);opacity:.45}}
        @keyframes yj-nav-glow {0%,100% {box-shadow:inset 0 -2px 0 rgba(201,160,82,.35),0 0 0 rgba(201,160,82,0)}50% {box-shadow:inset 0 -2px 0 #d9b96c,0 0 18px rgba(201,160,82,.28)}}
        @keyframes yj-button-sweep {0%,58% {transform:translateX(-150%) skewX(-24deg)}100% {transform:translateX(360%) skewX(-24deg)}}
        @keyframes yj-frame-aura {0%,100% {box-shadow:0 20px 48px rgba(50,23,19,.16),0 0 0 1px rgba(201,160,82,.10)}50% {box-shadow:0 28px 68px rgba(91,32,42,.24),0 0 0 1px rgba(228,192,104,.44),0 0 34px rgba(201,160,82,.12)}}
        .yunjin-hero > *:not(.yunjin-aurora):not(.yunjin-shuttle-path):not(.yunjin-gold-dust):not(.yunjin-spectacle-corners):not(.yunjin-woven-emblem):not(.yunjin-seal) {position:relative;z-index:3}.yunjin-seal {position:absolute!important;z-index:3}.yunjin-aurora {position:absolute;right:4%;top:2%;width:52%;height:90%;z-index:0;pointer-events:none;background:radial-gradient(ellipse at center,rgba(255,199,98,.26),rgba(195,56,76,.18) 33%,transparent 68%);filter:blur(18px);animation:yj-aurora-roam 8.5s ease-in-out infinite}.yunjin-shuttle-path {position:absolute;left:7%;right:7%;top:70%;height:1px;z-index:1;pointer-events:none;transform:rotate(-2deg);background:linear-gradient(90deg,transparent,rgba(239,204,123,.18),rgba(239,204,123,.56),rgba(239,204,123,.18),transparent);box-shadow:0 0 12px rgba(239,204,123,.22)}.yunjin-shuttle-path i {position:absolute;left:-8%;top:-4px;width:34px;height:9px;border-radius:70% 18% 70% 18%;background:linear-gradient(90deg,#7e2b35,#ffe09a,#9a3543);box-shadow:-18px 0 24px rgba(255,215,123,.62),0 0 14px rgba(255,228,160,.88);animation:yj-shuttle-run 6.2s ease-in-out infinite}
        .yunjin-gold-dust {position:absolute;inset:0;z-index:1;pointer-events:none}.yunjin-gold-dust span {position:absolute;width:4px;height:4px;border-radius:50%;background:#f6d887;box-shadow:0 0 10px #f6c965;animation:yj-dust-float 5s ease-in-out infinite}.yunjin-gold-dust span:nth-child(1){left:58%;top:22%;animation-delay:-1.2s}.yunjin-gold-dust span:nth-child(2){left:72%;top:68%;animation-delay:-3.6s;width:3px;height:3px}.yunjin-gold-dust span:nth-child(3){left:88%;top:32%;animation-delay:-2.4s}.yunjin-gold-dust span:nth-child(4){left:48%;top:78%;animation-delay:-4.3s;width:5px;height:5px}.yunjin-gold-dust span:nth-child(5){left:80%;top:15%;animation-delay:-.4s;width:2px;height:2px}.yunjin-spectacle-corners:before,.yunjin-spectacle-corners:after {content:"";position:absolute;width:72px;height:72px;z-index:2;pointer-events:none;border-color:rgba(239,204,123,.72)}.yunjin-spectacle-corners:before {left:18px;top:18px;border-left:1px solid;border-top:1px solid}.yunjin-spectacle-corners:after {right:18px;bottom:18px;border-right:1px solid;border-bottom:1px solid}
        @keyframes yj-weave-reveal {0%,8%{clip-path:inset(100% 0 0 0);opacity:0}42%,78%{clip-path:inset(0 0 0 0);opacity:.34}100%{clip-path:inset(0 0 100% 0);opacity:0}}
        @keyframes yj-weave-cross {0%{background-position:0 0,0 0;opacity:.08}50%{background-position:28px 0,0 28px;opacity:.34}100%{background-position:56px 0,0 56px;opacity:.08}}
        .yunjin-woven-emblem{position:absolute;right:5.5%;top:21%;z-index:2;width:150px;height:150px;border-radius:18px;pointer-events:none;background:repeating-linear-gradient(90deg,transparent 0 5px,rgba(248,216,137,.22) 5px 6px),repeating-linear-gradient(0deg,transparent 0 5px,rgba(179,48,64,.28) 5px 6px);animation:yj-weave-cross 6.2s linear infinite;mask:radial-gradient(circle,#000 36%,transparent 70%)}.yunjin-woven-emblem:after{content:"云锦";position:absolute;inset:0;display:grid;place-items:center;color:#f8dda1;font:900 2.5rem/1 serif;letter-spacing:.12em;text-shadow:0 0 18px rgba(255,218,128,.55);animation:yj-weave-reveal 6.2s ease-in-out infinite}
        [data-testid="stSegmentedControl"] label:has(input:checked) {animation:yj-nav-glow 2.8s ease-in-out infinite}.stButton>button {position:relative;overflow:hidden}.stButton>button[kind="primary"]:after {content:"";position:absolute;inset:-45% auto -45% -25%;width:18%;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(255,243,203,.52),transparent);animation:yj-button-sweep 4.8s ease-in-out infinite}[data-testid="stIFrame"] {animation:yj-frame-aura 1.35s ease-out 1}
        @media(max-width:760px){.yunjin-woven-emblem{right:.5rem;top:.25rem;width:86px;height:86px;opacity:.42}.yunjin-woven-emblem:after{font-size:1.35rem}}
        @media(prefers-reduced-motion:reduce){.yunjin-aurora,.yunjin-shuttle-path i,.yunjin-gold-dust span,.yunjin-woven-emblem,.yunjin-woven-emblem:after,[data-testid="stSegmentedControl"] label:has(input:checked),.stButton>button[kind="primary"]:after,[data-testid="stIFrame"]{animation:none!important}}
        </style>
        """
    )


apply_yunjin_spectacle_layer()


def apply_yunjin_editorial_refinement() -> None:
    """Restore the final bilingual editorial hierarchy and hero artwork."""
    hero_path = ROOT / "assets" / "yunjin-hero-brocade-v2.webp"
    hero_uri = ""
    if hero_path.exists():
        hero_uri = "data:image/webp;base64," + base64.b64encode(hero_path.read_bytes()).decode("ascii")
    st.html(
        """
        <style>
        :root{--yj-serif:'Noto Serif SC','Source Han Serif SC','Songti SC','STSong',serif;--yj-sans:'Microsoft YaHei','Noto Sans CJK SC',Arial,sans-serif}
        html,body,.stApp{font-family:var(--yj-sans)}
        .material-symbols-rounded,.material-symbols-outlined,[data-testid="stIconMaterial"]{font-family:'Material Symbols Rounded','Material Symbols Outlined'!important;font-weight:normal!important;letter-spacing:normal!important}
        h1,h2,h3,.yunjin-hero h1,.yunjin-page-banner h1{font-family:var(--yj-serif);font-weight:760!important;letter-spacing:.015em}
        .stApp{background:radial-gradient(circle at 92% 3%,rgba(49,90,89,.07),transparent 29rem),linear-gradient(180deg,#fdf9f1 0%,#f7efdf 100%)}.stApp:before{opacity:.11}
        .stMainBlockContainer{max-width:1540px;padding-left:clamp(1rem,4vw,4rem);padding-right:clamp(1rem,4vw,4rem)}
        [data-testid="stSegmentedControl"] button,.stButton>button,[data-testid="stExpander"] summary{font-family:var(--yj-sans)}
        [data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,252,246,.84);border-color:rgba(178,139,71,.34)!important;box-shadow:0 12px 30px rgba(61,34,23,.055),inset 0 1px 0 rgba(255,255,255,.94)}
        [data-testid="stExpander"]{background:rgba(255,252,247,.72);border-color:rgba(178,139,71,.34)!important;box-shadow:none}[data-testid="stExpander"] summary{min-height:3.25rem;color:#432722}
        .yunjin-hero{min-height:440px;padding:clamp(2.4rem,5vw,5rem);background-image:linear-gradient(90deg,rgba(31,7,11,.24) 0%,rgba(49,10,16,.13) 48%,rgba(35,9,10,.03) 100%),url('""" + hero_uri + """');background-size:108% auto;background-position:center;border-radius:28px;box-shadow:0 34px 90px rgba(52,19,17,.24),inset 0 0 0 1px rgba(255,226,151,.18);animation:yj-editorial-drift 13s ease-in-out infinite alternate}
        .yunjin-hero:before{display:block;inset:-38% auto -38% -28%;width:17%;height:auto;border:0;border-radius:0;z-index:2;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(255,234,176,.38),rgba(255,251,222,.14),transparent);mix-blend-mode:screen;animation:yj-silk-glint 8.5s ease-in-out infinite}
        .yunjin-hero:after{opacity:.38}.yunjin-hero__eyebrow{font-family:var(--yj-sans);font-size:.7rem;letter-spacing:.28em}.yunjin-hero h1{max-width:720px;font-size:clamp(2.9rem,5.2vw,5.4rem);line-height:1.02;text-shadow:0 10px 34px rgba(0,0,0,.52)}.yunjin-hero p{max-width:650px;color:rgba(255,248,226,.82);font-size:1rem;line-height:1.75}.yunjin-hero__tags{margin-top:1.6rem}.yunjin-hero__tags span{background:rgba(28,10,11,.42);border-color:rgba(240,208,132,.32);box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}.yunjin-weave-motion{opacity:.34}.yunjin-gold-dust{opacity:.50}.yunjin-seal{right:6.5%;top:18%;width:104px;height:104px;background:rgba(69,15,23,.28);backdrop-filter:blur(3px)}
        .yunjin-page-banner{min-height:128px;display:flex;flex-direction:column;justify-content:center;padding:1.7rem 2.1rem;background:linear-gradient(104deg,#291517 0%,#62222d 64%,#315a59 148%);background-size:180% 180%;border-radius:20px;animation:yj-banner-drift 11s ease-in-out infinite alternate}.yunjin-page-banner__kicker{font-size:.64rem;letter-spacing:.25em}.yunjin-page-banner h1{font-size:clamp(2rem,3.5vw,3.4rem)}
        .yj-editorial-heading{display:flex;align-items:end;justify-content:space-between;gap:2rem;margin:2.5rem 0 1rem;padding-bottom:.8rem;border-bottom:1px solid rgba(166,126,60,.28);animation:yj-content-rise .78s .08s both}.yj-editorial-heading small,.yj-card-kicker{color:#9c7436;font-size:.64rem;font-weight:850;letter-spacing:.20em}.yj-editorial-heading h2{margin:.25rem 0 0;padding:0;font:760 1.85rem/1.15 var(--yj-serif);color:#351c1a}.yj-editorial-heading p{max-width:580px;margin:0;color:#79665c;font-size:.88rem;text-align:right}
        .yj-journey-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0 2.2rem}.yj-journey-card{position:relative;min-height:180px;padding:1.45rem 1.5rem 1.35rem;overflow:hidden;border:1px solid rgba(178,139,71,.34);border-radius:18px;background:#fffaf1;box-shadow:0 14px 34px rgba(69,34,23,.06);transition:transform .35s ease,box-shadow .35s ease,border-color .35s ease;animation:yj-content-rise .72s both}.yj-journey-card:nth-child(1){--card-accent:linear-gradient(90deg,#9a3546,#d19e56);animation-delay:.10s}.yj-journey-card:nth-child(2){--card-accent:linear-gradient(90deg,#b48a43,#e0c783);animation-delay:.22s}.yj-journey-card:nth-child(3){--card-accent:linear-gradient(90deg,#315f5b,#92b5a4);animation-delay:.34s}.yj-journey-card:before{content:'';position:absolute;left:0;right:0;top:0;height:3px;background:var(--card-accent)}.yj-journey-card:after{content:'';position:absolute;z-index:0;top:-45%;bottom:-45%;left:-28%;width:13%;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(218,178,94,.15),transparent);animation:yj-card-lustre 7.5s ease-in-out infinite}.yj-journey-card:nth-child(2):after{animation-delay:-2.4s}.yj-journey-card:nth-child(3):after{animation-delay:-4.8s}.yj-journey-card>*{position:relative;z-index:1}.yj-journey-card small{color:#a0783e;font-size:.62rem;font-weight:850;letter-spacing:.16em}.yj-journey-card h3{margin:.75rem 0 .55rem;padding:0;font:740 1.3rem/1.25 var(--yj-serif)}.yj-journey-card p{margin:0;color:#6d5b50;font-size:.88rem;line-height:1.65}.yj-journey-card b{display:block;margin-top:1.15rem;color:#8b2e3e;font-size:.72rem;letter-spacing:.06em}.yj-journey-card:hover{transform:translateY(-7px);border-color:rgba(161,112,48,.58);box-shadow:0 24px 54px rgba(80,35,25,.14)}
        [data-testid="stIFrame"]{border:1px solid rgba(183,143,72,.32);border-radius:20px;box-shadow:0 26px 72px rgba(54,27,20,.17)}
        @keyframes yj-editorial-drift{0%{background-position:48% 50%;box-shadow:0 28px 72px rgba(52,19,17,.22),inset 0 0 0 1px rgba(255,226,151,.16)}100%{background-position:57% 47%;box-shadow:0 40px 105px rgba(88,27,28,.32),inset 0 0 0 1px rgba(255,226,151,.26)}}
        @keyframes yj-silk-glint{0%,16%{transform:translate3d(-180%,0,0) rotate(14deg);opacity:0}28%{opacity:.44}62%,100%{transform:translate3d(520%,0,0) rotate(14deg);opacity:0}}
        @keyframes yj-corner-pulse{0%,100%{filter:drop-shadow(0 0 0 rgba(242,211,138,0));opacity:.58}50%{filter:drop-shadow(0 0 8px rgba(242,211,138,.58));opacity:1}}
        @keyframes yj-content-rise{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}@keyframes yj-card-lustre{0%,22%{transform:translateX(-150%) skewX(-18deg);opacity:0}38%{opacity:.42}68%,100%{transform:translateX(520%) skewX(-18deg);opacity:0}}@keyframes yj-banner-drift{to{background-position:100% 50%}}
        .yunjin-aurora{display:block;opacity:.34;filter:blur(26px);mix-blend-mode:screen}.yunjin-shuttle-path{display:block;top:76%;opacity:.56}.yunjin-shuttle-path i{animation-duration:5.4s}.yunjin-spectacle-corners:before,.yunjin-spectacle-corners:after{animation:yj-corner-pulse 4.6s ease-in-out infinite}.yunjin-spectacle-corners:after{animation-delay:-2.3s}
        .yunjin-hero__eyebrow{animation:yj-content-rise .75s .05s both}.yunjin-hero h1{animation:yj-content-rise .9s .16s both,yj-title-glow 5s 1.1s ease-in-out infinite}.yunjin-hero p{animation:yj-content-rise .9s .28s both}.yunjin-hero__tags{animation:yj-content-rise .9s .4s both}
        @media(max-width:900px){.yj-journey-grid{grid-template-columns:1fr}.yj-journey-card{min-height:0}.yj-editorial-heading{display:block}.yj-editorial-heading p{margin-top:.5rem;text-align:left}.yunjin-hero{min-height:390px;background-position:62% center}.yunjin-seal{right:1.3rem;top:1.2rem}}
        @media(max-width:560px){.stMainBlockContainer{padding-left:.8rem;padding-right:.8rem}.yunjin-hero{min-height:430px;padding:2rem 1.25rem;background-position:67% center}.yunjin-hero h1{font-size:2.35rem;max-width:82%}.yunjin-hero p{max-width:94%;font-size:.9rem}.yunjin-seal{width:54px;height:54px;font-size:.9rem}.yunjin-page-banner{padding:1.3rem}.yj-editorial-heading h2{font-size:1.5rem}}
        @media(prefers-reduced-motion:reduce){.yunjin-hero,.yunjin-hero:before,.yunjin-aurora,.yunjin-shuttle-path i,.yunjin-spectacle-corners:before,.yunjin-spectacle-corners:after,.yunjin-hero__eyebrow,.yunjin-hero h1,.yunjin-hero p,.yunjin-hero__tags,.yj-editorial-heading,.yj-journey-card,.yj-journey-card:after,.yunjin-page-banner{animation:none!important}.yj-journey-card{transition:none!important}}
        </style>
        """
    )


apply_yunjin_editorial_refinement()


def apply_yunjin_cultural_identity_layer() -> None:
    """Carry recognisable Nanjing Yunjin cues beyond the hero artwork."""
    st.html(
        """
        <style>
        :root{--yj-vermilion:#8f2638;--yj-aged-gold:#b98b3e;--yj-silk:#fff9ec;--yj-patina:#315d58}
        @keyframes yj-border-shimmer{0%,100%{background-position:0 0,0 0;opacity:.45}50%{background-position:0 18px,0 -18px;opacity:.70}}
        @keyframes yj-knot-breathe{0%,100%{transform:rotate(45deg) scale(.88);box-shadow:0 0 0 rgba(188,141,62,0)}50%{transform:rotate(45deg) scale(1.06);box-shadow:0 0 15px rgba(188,141,62,.30)}}
        .stApp:after{content:"";position:fixed;z-index:0;inset:4.2rem 0 0;pointer-events:none;opacity:.50;background:linear-gradient(90deg,rgba(143,38,56,.16) 0 2px,transparent 2px calc(100% - 2px),rgba(143,38,56,.16) calc(100% - 2px)),repeating-linear-gradient(0deg,transparent 0 13px,rgba(185,139,62,.16) 13px 14px,transparent 14px 27px);background-size:100% 100%,5px 28px;background-repeat:no-repeat,repeat-y;animation:yj-border-shimmer 8s ease-in-out infinite}
        .stMainBlockContainer{position:relative;z-index:1}
        .yj-craft-signature{position:relative;display:grid;grid-template-columns:minmax(160px,.75fr) repeat(3,1fr);gap:0;margin:-.35rem 0 2rem;overflow:hidden;border:1px solid rgba(173,126,49,.46);border-radius:18px;background:linear-gradient(110deg,#35191c 0%,#60212d 31%,#fff8e9 31.2%,#fbf2df 100%);box-shadow:0 16px 42px rgba(66,29,23,.10)}
        .yj-craft-signature:before{content:"";position:absolute;left:31%;right:0;top:0;height:3px;background:repeating-linear-gradient(90deg,#8f2638 0 18px,#d1aa58 18px 36px,#315d58 36px 54px)}
        .yj-craft-signature__brand{display:flex;align-items:center;gap:.85rem;padding:1.05rem 1.25rem;color:#f7dfaa}.yj-craft-signature__seal{display:grid;place-items:center;flex:0 0 43px;height:43px;border:1px solid #e9c879;box-shadow:inset 0 0 0 3px rgba(233,200,121,.12);font:800 1.1rem/1 serif;transform:rotate(-3deg)}
        .yj-craft-signature__brand b{display:block;font:750 1rem/1.25 serif;letter-spacing:.08em}.yj-craft-signature__brand small{display:block;margin-top:.22rem;color:rgba(247,223,170,.66);font-size:.56rem;letter-spacing:.16em}
        .yj-craft-signature__item{position:relative;padding:1rem 1.1rem 1rem 1.35rem;border-left:1px solid rgba(173,126,49,.22);background:linear-gradient(145deg,rgba(255,249,235,.98),rgba(248,237,215,.94))}.yj-craft-signature__item:before{content:"";position:absolute;left:.62rem;top:1.25rem;width:6px;height:6px;border:1px solid var(--yj-aged-gold);animation:yj-knot-breathe 4.2s ease-in-out infinite}.yj-craft-signature__item:nth-child(3):before{animation-delay:-1.4s}.yj-craft-signature__item:nth-child(4):before{animation-delay:-2.8s}.yj-craft-signature__item b{display:block;color:#4b2523;font:720 .88rem/1.25 serif}.yj-craft-signature__item span{display:block;margin-top:.25rem;color:#8a7464;font-size:.66rem;letter-spacing:.04em}
        @media(max-width:900px){.yj-craft-signature{grid-template-columns:1fr 1fr;background:linear-gradient(110deg,#35191c 0%,#60212d 50%,#fff8e9 50.2%,#fbf2df 100%)}.yj-craft-signature:before{left:50%}.yj-craft-signature__item:nth-child(3),.yj-craft-signature__item:nth-child(4){border-top:1px solid rgba(173,126,49,.22)}}
        @media(max-width:560px){.yj-craft-signature{grid-template-columns:1fr;background:#fff8e9}.yj-craft-signature:before{left:0}.yj-craft-signature__brand{background:linear-gradient(110deg,#35191c,#60212d)}.yj-craft-signature__item{border-left:0;border-top:1px solid rgba(173,126,49,.22)}}
        @media(prefers-reduced-motion:reduce){.stApp:after,.yj-craft-signature__item:before{animation:none!important}}
        .yj-editorial-heading{position:relative;border-bottom-color:rgba(185,139,62,.38)}.yj-editorial-heading:after{content:"";position:absolute;left:0;bottom:-3px;width:82px;height:5px;background:repeating-linear-gradient(90deg,#8f2638 0 10px,#d5b25e 10px 20px);mask:linear-gradient(90deg,#000,transparent)}
        .yj-journey-card{background:radial-gradient(circle at calc(100% - 24px) 23px,transparent 0 8px,rgba(185,139,62,.14) 8.5px 9.5px,transparent 10px),linear-gradient(145deg,#fffaf1,#fbf1dd)}.yj-journey-card h3:after{content:"◇";float:right;color:rgba(143,38,56,.34);font:.85rem/1 var(--yj-sans)}.yj-journey-card b{display:inline-flex;align-items:center;gap:.42rem}.yj-journey-card b:before{content:"";width:18px;height:1px;background:linear-gradient(90deg,#8f2638,#d0a64f)}
        [data-testid="stMetric"]{position:relative;overflow:hidden;border-left-color:var(--yj-aged-gold);background:linear-gradient(100deg,rgba(255,249,235,.95),rgba(246,234,210,.72))}[data-testid="stMetric"]:after{content:"锦";position:absolute;right:.5rem;bottom:-.45rem;color:rgba(143,38,56,.07);font:800 2.7rem/1 var(--yj-serif)}
        </style>
        """
    )


apply_yunjin_cultural_identity_layer()


def apply_yunjin_unified_finish() -> None:
    """Apply one consistent exhibition finish to every Streamlit surface."""
    st.html(
        """
        <style>
        :root{--yj-ink:#38231f;--yj-muted:#816e63;--yj-paper:#fffaf0;--yj-paper-deep:#f5e8d2;--yj-red:#8f2e40;--yj-red-dark:#5e202b;--yj-gold:#b88a3d;--yj-gold-soft:#e4c77f;--yj-teal:#315f5b;--yj-line:rgba(173,126,49,.34);--yj-radius:18px;--yj-shadow:0 16px 42px rgba(72,34,24,.08)}
        .stApp{color:var(--yj-ink);background:radial-gradient(circle at 8% 2%,rgba(143,46,64,.09),transparent 28rem),radial-gradient(circle at 94% 10%,rgba(49,95,91,.075),transparent 27rem),repeating-linear-gradient(135deg,rgba(184,138,61,.025) 0 1px,transparent 1px 13px),linear-gradient(180deg,#fffaf2 0%,#f7eddd 100%)}
        [data-testid="stHeader"]{border-bottom:1px solid rgba(184,138,61,.30);background:rgba(255,250,242,.88);box-shadow:0 5px 24px rgba(78,38,25,.035);backdrop-filter:blur(16px)}
        .stMainBlockContainer{max-width:1480px;padding-bottom:5rem}
        h1,h2,h3{color:#351b1a}h2{letter-spacing:.006em}h3{letter-spacing:.008em}
        [data-testid="stCaptionContainer"]{color:var(--yj-muted)}
        [data-testid="stSegmentedControl"]>div{padding:.27rem;border:1px solid rgba(184,138,61,.52);border-radius:14px;background:linear-gradient(180deg,rgba(255,252,245,.96),rgba(247,237,218,.86));box-shadow:0 10px 28px rgba(71,34,24,.07)}
        [data-testid="stSegmentedControl"] button{min-height:2.55rem;border-radius:10px!important;color:#49312c;font-weight:720;transition:color .22s ease,background .22s ease,box-shadow .22s ease}
        [data-testid="stSegmentedControl"] button[aria-checked="true"]{color:#fff6df!important;background:linear-gradient(135deg,var(--yj-red-dark),var(--yj-red))!important;box-shadow:inset 0 0 0 1px rgba(241,211,140,.34),0 8px 18px rgba(112,35,51,.20)}
        .stButton>button{min-height:2.65rem;border:1px solid rgba(143,46,64,.25);border-radius:12px;color:#4a2e2a;background:linear-gradient(180deg,rgba(255,253,247,.98),rgba(248,238,220,.92));box-shadow:0 7px 18px rgba(68,33,24,.045),inset 0 1px 0 rgba(255,255,255,.92);font-weight:720}
        .stButton>button:hover{color:#762638;border-color:rgba(184,138,61,.72);background:linear-gradient(180deg,#fffdf7,#f5e3bf);box-shadow:0 12px 28px rgba(87,38,27,.10)}
        .stButton>button[kind="primary"]{color:#fff8e8;background:linear-gradient(135deg,#64212e 0%,#973145 58%,#6d2432 100%);border-color:rgba(229,196,119,.44);box-shadow:0 12px 28px rgba(112,35,51,.22)}
        [data-testid="stVerticalBlockBorderWrapper"]{border:1px solid var(--yj-line)!important;border-radius:var(--yj-radius)!important;background:linear-gradient(145deg,rgba(255,252,245,.94),rgba(248,238,220,.84));box-shadow:var(--yj-shadow),inset 0 1px 0 rgba(255,255,255,.94)}
        [data-testid="stExpander"]{overflow:hidden;border:1px solid var(--yj-line)!important;border-radius:15px!important;background:rgba(255,252,246,.86);box-shadow:0 9px 24px rgba(72,34,24,.045)}[data-testid="stExpander"] summary{min-height:3.25rem;color:#492925;font-weight:730;background:linear-gradient(90deg,rgba(143,46,64,.025),rgba(184,138,61,.045))}
        [data-testid="stExpander"] summary:hover{color:#7f2b3b;background:linear-gradient(90deg,rgba(143,46,64,.055),rgba(184,138,61,.075))}
        [data-testid="stMetric"]{min-height:106px;padding:1rem 1.05rem;border:1px solid rgba(184,138,61,.24);border-left:3px solid var(--yj-gold);border-radius:4px 14px 14px 4px;background:linear-gradient(105deg,rgba(255,251,240,.98),rgba(246,233,207,.76));box-shadow:0 8px 22px rgba(72,34,24,.045)}[data-testid="stMetricValue"]{color:#4a2022;font-family:var(--yj-serif);font-weight:760}
        [data-testid="stFileUploaderDropzone"]{border:1px dashed rgba(143,46,64,.38);border-radius:16px;background:linear-gradient(135deg,rgba(255,251,242,.92),rgba(247,235,213,.78))}[data-testid="stFileUploaderDropzone"]:hover{border-color:rgba(184,138,61,.80);background:linear-gradient(135deg,#fffaf0,#f4dfb9)}
        [data-baseweb="input"]>div,[data-baseweb="textarea"]>div{border-color:rgba(184,138,61,.38)!important;border-radius:12px!important;background:rgba(255,253,248,.94)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.9)}[data-baseweb="input"]>div:focus-within,[data-baseweb="textarea"]>div:focus-within{border-color:var(--yj-red)!important;box-shadow:0 0 0 3px rgba(143,46,64,.08)!important}
        [data-testid="stChatMessage"]{margin:.65rem 0;border:1px solid rgba(184,138,61,.24);border-radius:16px;background:rgba(255,251,243,.82);box-shadow:0 8px 20px rgba(73,35,24,.04)}
        [data-testid="stAlert"]{border:1px solid rgba(184,138,61,.30);border-radius:14px;box-shadow:0 8px 20px rgba(72,34,24,.035)}
        [data-testid="stDataFrame"]{overflow:hidden;border:1px solid rgba(184,138,61,.30);border-radius:14px;box-shadow:0 10px 26px rgba(72,34,24,.05)}
        .yunjin-page-banner{border-color:rgba(228,199,128,.46);box-shadow:0 20px 48px rgba(68,28,27,.16),inset 0 0 0 1px rgba(255,235,184,.05)}.yunjin-page-banner:after{right:2.2rem;color:rgba(240,211,143,.085)}.yunjin-page-banner__kicker{display:flex;align-items:center;gap:.65rem;color:#e5c679}.yunjin-page-banner__kicker:before{content:"";width:28px;height:1px;background:linear-gradient(90deg,#e5c679,transparent)}
        .yj-editorial-heading{margin-top:2.35rem}.yj-editorial-heading small{color:#9c7436}.yj-editorial-heading p{color:#7d6b61}
        .yj-journey-grid{gap:1.05rem}.yj-journey-card{border-color:rgba(173,126,49,.34);box-shadow:0 15px 36px rgba(72,34,24,.07)}.yj-journey-card:nth-child(1) small,.yj-journey-card:nth-child(1) b{color:#8f2e40}.yj-journey-card:nth-child(2) small,.yj-journey-card:nth-child(2) b{color:#9b6f28}.yj-journey-card:nth-child(3) small,.yj-journey-card:nth-child(3) b{color:#315f5b}
        .yj-craft-signature{border-color:rgba(184,138,61,.46);box-shadow:0 16px 42px rgba(66,29,23,.09)}
        hr{border-color:rgba(184,138,61,.22)}
        ::selection{color:#fff9e9;background:#8f2e40}
        @media(max-width:760px){.stMainBlockContainer{padding-left:.85rem;padding-right:.85rem}.yunjin-page-banner{min-height:118px}.yj-craft-signature{margin-bottom:1.5rem}[data-testid="stMetric"]{min-height:92px}}
        @media(prefers-reduced-motion:reduce){.stButton>button,[data-testid="stSegmentedControl"] button,[data-testid="stFileUploaderDropzone"]{transition:none!important}}
        </style>
        """
    )


apply_yunjin_unified_finish()
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
    st.html(
        """
        <section class="yunjin-hero">
          <div class="yunjin-hero__eyebrow">NANJING YUNJIN · DIGITAL HERITAGE</div>
          <h1>一寸锦，一寸金</h1>
          <p>让 AI 看见纹样，让可信知识讲述云锦，也让一架大花楼织机在数字空间重新运转。</p>
          <div class="yunjin-hero__tags"><span>AI 纹样观察</span><span>可信文化知识</span><span>数字织机</span><span>沉浸式学习</span></div>
          <div class="yunjin-weave-motion" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
          <div class="yunjin-aurora" aria-hidden="true"></div>
          <div class="yunjin-shuttle-path" aria-hidden="true"><i></i></div>
          <div class="yunjin-gold-dust" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
          <div class="yunjin-woven-emblem" aria-hidden="true"></div>
          <div class="yunjin-spectacle-corners" aria-hidden="true"></div>
          <div class="yunjin-seal">云锦</div>
        </section>
        """
    )
    st.html(
        """
        <section class="yj-craft-signature" aria-label="南京云锦工艺特征">
          <div class="yj-craft-signature__brand"><span class="yj-craft-signature__seal">宁锦</span><div><b>南京云锦</b><small>NANJING YUNJIN</small></div></div>
          <div class="yj-craft-signature__item"><b>妆花织造</b><span>逐纬挖花 · 多彩换色</span></div>
          <div class="yj-craft-signature__item"><b>挑花结本</b><span>纹样转译 · 提花控制</span></div>
          <div class="yj-craft-signature__item"><b>通经断纬</b><span>经线贯通 · 彩纬显花</span></div>
        </section>
        """
    )
    st.html('''<div class="yj-editorial-heading"><div><small>SEE · UNDERSTAND · EXPERIENCE</small><h2>从看见纹样，到理解织造</h2></div><p>以视觉观察为入口，以可信知识为依据，最终进入可交互的数字织机。</p></div>''')
    st.button("体验云锦织造", key="home_open_twin", type="primary",
              on_click=lambda: st.session_state.update(main_tab="数字织机"))
    st.html('''<section class="yj-journey-grid">
      <article class="yj-journey-card"><small>01 · VISUAL OBSERVATION</small><h3>看见云锦</h3><p>上传织物图片，从纹样、构图和色彩开始观察；结果是文化探索线索，不替代专业鉴定。</p><b>AI 探锦 →</b></article>
      <article class="yj-journey-card"><small>02 · TRUSTED KNOWLEDGE</small><h3>理解云锦</h3><p>连接已核验来源与对象级资料，让每一条文化解释都能回到证据与边界。</p><b>可信文化知识 →</b></article>
      <article class="yj-journey-card"><small>03 · DIGITAL HERITAGE</small><h3>体验织造</h3><p>进入大花楼数字织机，观察踏板、梭口、梭子、筘框与卷布如何协同成锦。</p><b>数字织机 →</b></article>
    </section>''')

    st.html('''<div class="yj-editorial-heading"><div><small>CURATED KNOWLEDGE</small><h2>探索云锦文化</h2></div><p>从知识库中已有可靠来源支持的主题开始。</p></div>''')
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
    show_page_banner(
        "AI VISUAL OBSERVATION",
        "AI 探锦",
        "从纹样、构图与色彩开始观察，把视觉结果转化为可继续查证的文化线索。",
    )
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
    show_page_banner(
        "EVIDENCE-GROUNDED CULTURAL GUIDE",
        "AI 文化助手",
        "以本地可信知识与来源边界为基础，继续理解南京云锦的工艺、纹样与文化语境。",
    )
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
    show_page_banner(
        "DATA PROVENANCE · TRUSTWORTHY AI",
        "数据与可信 AI",
        "说明数据从哪里来、系统能回答什么，以及如何避免把视觉观察误写成文化事实。",
    )

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
