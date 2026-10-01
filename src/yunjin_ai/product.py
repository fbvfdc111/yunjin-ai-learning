from __future__ import annotations

from collections.abc import Iterable, MutableMapping
from typing import Any

from .knowledge import SearchHit
from .vision import VisionObservation


GUIDE_TAB_LABEL = "AI文化助手"


def visual_observation_sections(observation: VisionObservation) -> dict[str, tuple[str, ...]]:
    """Group provider output into stable, audience-facing visual sections."""
    sections: dict[str, list[str]] = {
        "纹样与主体": [],
        "构图特征": [],
        "色彩特征": [],
    }
    for raw_fact in observation.observable_facts:
        fact = raw_fact.strip()
        if not fact:
            continue
        prefix, separator, content = fact.partition("：")
        content = content.strip() if separator else fact
        if prefix in {"主体/纹样", "纹样与主体"}:
            sections["纹样与主体"].append(content)
        elif prefix in {"构图", "重复/对称"}:
            sections["构图特征"].append(content)
        elif prefix == "色彩" or any(token in fact for token in ("色群", "色彩", "饱和")):
            sections["色彩特征"].append(content)
        elif any(token in fact for token in ("对称", "镜像", "边缘", "轮廓", "纹理")):
            sections["构图特征"].append(content)
        else:
            sections["纹样与主体"].append(content)
    return {name: tuple(values) for name, values in sections.items()}


FOLLOWUP_QUESTIONS = {
    "KB001": ("南京云锦为什么被列入非物质文化遗产？",),
    "KB003": ("南京云锦的制作流程有哪些主要环节？",),
    "KB004": ("云锦为什么需要手工织造？",),
    "KB007": ("南京云锦有哪些主要品种？",),
    "KB008": ("妆花是什么？",),
    "KB009": ("织金是什么？", "四大品种有哪些有证据的区别？"),
    "KB010": ("传统织物中常见哪些纹样题材与构图形式？",),
    "KB011": ("南京云锦官方对象中有龙纹吗？",),
    "KB012": ("南京云锦官方对象中有牡丹吗？",),
    "KB016": ("库锦是什么？",),
    "KB017": ("库缎是什么？",),
    "KB018": ("四大品种有哪些有证据的区别？",),
    "KB019": ("挑花结本是什么，有什么作用？",),
    "KB020": ("南京云锦官方对象中有凤纹吗？",),
    "KB021": ("松鹤组合有哪些一般传统文化背景？",),
    "KB022": ("寿字有哪些一般传统文化背景？",),
}

GENERAL_CULTURE_QUESTIONS = (
    "南京云锦是什么？",
    "妆花是什么？",
    "南京云锦有哪些主要品种？",
    "挑花结本是什么，有什么作用？",
    "云锦为什么需要手工织造？",
)


def cultural_followup_questions(hits: Iterable[SearchHit], limit: int = 3) -> tuple[str, ...]:
    questions: list[str] = []
    for hit in hits:
        questions.extend(FOLLOWUP_QUESTIONS.get(hit.item.id, ()))
    if not questions:
        questions.extend(GENERAL_CULTURE_QUESTIONS)
    return tuple(dict.fromkeys(questions))[:limit]


def apply_guide_handoff(state: MutableMapping[str, Any], question: str) -> None:
    """Open the culture assistant tab and prefill a question without asserting image identity."""
    state["guide_question"] = question
    state["main_tab"] = GUIDE_TAB_LABEL
