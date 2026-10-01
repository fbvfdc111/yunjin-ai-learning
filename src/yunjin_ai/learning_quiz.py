from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .digital_twin import STAGE_IDS, TwinState, validate_runtime


@dataclass(frozen=True)
class QuizItem:
    stage_id: str
    question: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str
    evidence_note: str


QUIZ_ITEMS: tuple[QuizItem, ...] = (
    QuizItem(
        stage_id="pattern_design",
        question="在本原型中，图案设计环节的草图显示代表什么？",
        options=("教学示意中的图案观察起点", "系统已经鉴定出文物真伪", "实体织机传感器实时数据"),
        correct_index=0,
        explanation="草图只是学习路径的起点，帮助用户从图案观察进入后续工艺理解。",
        evidence_note="数字织机页面明确标注为交互示意，不构成专业鉴定或实体测量。",
    ),
    QuizItem(
        stage_id="pattern_translation",
        question="挑花结本在学习链路中更接近哪种作用？",
        options=("把纹样信息转化为织造可用的信息载体", "自动训练图像分类模型", "判断上传图片年代"),
        correct_index=0,
        explanation="本阶段强调纹样信息如何进入织造准备，而不是训练模型或鉴定年代。",
        evidence_note="页面中的工艺说明来自本地南京云锦知识条目与来源引用。",
    ),
    QuizItem(
        stage_id="weaving_preparation",
        question="织造准备步骤完成后，系统记录的是什么？",
        options=("本会话中的教学状态", "真实织机的物理参数", "用户身份信息"),
        correct_index=0,
        explanation="当前只记录用户交互驱动的教学状态，用于驱动画面和学习反馈。",
        evidence_note="系统声明当前没有实体传感器、实时同步或物理参数仿真。",
    ),
    QuizItem(
        stage_id="warp_lifting",
        question="拽花工提经的页面动画应该怎样理解？",
        options=("经线强调组的教学示意", "经过专家验证的机械结构仿真", "模型识别准确率展示"),
        correct_index=0,
        explanation="经线强调组用于帮助理解分工与动作关系，不代表机械结构精确仿真。",
        evidence_note="数字织机始终显示“非织机机械结构精确仿真”的边界。",
    ),
    QuizItem(
        stage_id="weft_weaving",
        question="织手织造环节中的纬向提示说明了什么？",
        options=("当前教学动作方向", "上传图片一定属于南京云锦", "官网图片可直接用于训练"),
        correct_index=0,
        explanation="纬向提示只对应当前交互步骤的画面反馈，不推断上传图片身份或数据授权。",
        evidence_note="项目把视觉观察、文化知识和训练授权分开处理。",
    ),
    QuizItem(
        stage_id="pattern_emergence",
        question="“织造成纹”分三段显示意味着什么？",
        options=("界面分段，用于展示纹样逐步出现", "真实织造必须分三次完成", "学习者已经掌握真实织造技能"),
        correct_index=0,
        explanation="三段显示只是界面设计，帮助用户观察结果逐步出现。",
        evidence_note="页面说明完成六步也不代表掌握真实织造技能。",
    ),
)

QUIZ_BY_STAGE = {item.stage_id: item for item in QUIZ_ITEMS}


@dataclass(frozen=True)
class QuizEvaluation:
    stage_id: str
    question: str
    selected_index: int
    correct_index: int
    is_correct: bool
    explanation: str
    evidence_note: str


def validate_quiz_items(items: Iterable[QuizItem] = QUIZ_ITEMS) -> list[str]:
    errors: list[str] = []
    items = tuple(items)
    if tuple(item.stage_id for item in items) != STAGE_IDS:
        errors.append("quiz items must follow the six digital loom stages")
    for item in items:
        if not item.question.strip() or not item.explanation.strip() or not item.evidence_note.strip():
            errors.append(f"{item.stage_id}: missing quiz text")
        if len(item.options) < 2 or len(set(item.options)) != len(item.options):
            errors.append(f"{item.stage_id}: invalid options")
        if type(item.correct_index) is not int or not 0 <= item.correct_index < len(item.options):
            errors.append(f"{item.stage_id}: invalid correct index")
    return errors


def evaluate_quiz(stage_id: str, selected_index: int) -> QuizEvaluation:
    if stage_id not in QUIZ_BY_STAGE:
        raise ValueError("unknown quiz stage")
    item = QUIZ_BY_STAGE[stage_id]
    if type(selected_index) is not int or not 0 <= selected_index < len(item.options):
        raise ValueError("invalid selected option")
    return QuizEvaluation(
        stage_id=stage_id,
        question=item.question,
        selected_index=selected_index,
        correct_index=item.correct_index,
        is_correct=selected_index == item.correct_index,
        explanation=item.explanation,
        evidence_note=item.evidence_note,
    )


def anonymous_result_record(
    evaluation: QuizEvaluation,
    state: TwinState,
    *,
    session_token: str,
    created_at: datetime | None = None,
) -> dict:
    validate_runtime(state)
    timestamp = (created_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    return {
        "created_at_utc": timestamp,
        "anonymous_session": session_token,
        "stage_id": evaluation.stage_id,
        "selected_index": evaluation.selected_index,
        "correct_index": evaluation.correct_index,
        "is_correct": evaluation.is_correct,
        "completed_stage_count": len(state.executed_stages),
        "current_stage_executed": state.current_stage_executed,
        "privacy_note": "anonymous local learning record; no name, image, API payload, IP, or contact data",
    }


def append_anonymous_result(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    allowed = {
        "created_at_utc",
        "anonymous_session",
        "stage_id",
        "selected_index",
        "correct_index",
        "is_correct",
        "completed_stage_count",
        "current_stage_executed",
        "privacy_note",
    }
    sanitized = {key: record[key] for key in allowed if key in record}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sanitized, ensure_ascii=False) + "\n")


def evaluation_summary(evaluations: Iterable[QuizEvaluation]) -> dict[str, int]:
    rows = tuple(evaluations)
    return {
        "answered": len(rows),
        "correct": sum(row.is_correct for row in rows),
    }
