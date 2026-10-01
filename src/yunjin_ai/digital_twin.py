"""Knowledge-bound lessons and user-driven teaching state. No device I/O."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable

from .knowledge import KnowledgeItem, Source

STAGE_IDS = (
    "pattern_design", "pattern_translation", "weaving_preparation",
    "warp_lifting", "weft_weaving", "pattern_emergence",
)
TITLES = ("图案设计", "挑花结本", "织造准备", "拽花工提经", "织手织造", "织造成纹")
MODES = {"sequential": "按顺序体验", "free": "自由探索"}
VISUAL_BOUNDARY = "交互示意｜非织机机械结构精确仿真"
STATE_BOUNDARY = "数字状态由用户交互驱动，是教学状态，不是实体织机传感器实时数据。"
PROCESS_BOUNDARY = "六个状态为教学抽取，不代表南京云锦百余道工序的完整流程。"
MISSING_CAPABILITIES = "当前没有实体传感器、实体织机实时数据同步、物理参数仿真和专家级机械结构验证。物理实体—数字模型的实时双向同步属于后续工作。"


@dataclass(frozen=True)
class Stage:
    id: str
    title: str
    stage_index: int
    operator: str
    description: str
    animation_state: str
    related_knowledge_ids: list[str]
    evidence_scope: dict
    source_ids: list[str]
    ai_question: str
    disclaimer: str
    claim_refs: list[dict]
    teaching_note: str
    evidence_gaps: str


def validate_stages(stages: list[Stage], knowledge: Iterable[KnowledgeItem], sources: dict[str, Source]) -> list[str]:
    errors: list[str] = []
    by_id = {item.id: item for item in knowledge}
    if tuple(s.id for s in stages) != STAGE_IDS:
        errors.append("Expected exactly six unique, ordered stage IDs")
    if [s.stage_index for s in stages] != list(range(1, 7)):
        errors.append("stage_index must be 1..6")
    if tuple(s.title for s in stages) != TITLES:
        errors.append("Unexpected lesson titles")
    for stage in stages:
        for name in ("operator", "description", "ai_question", "disclaimer", "teaching_note", "evidence_gaps"):
            if not isinstance(getattr(stage, name), str) or not getattr(stage, name).strip():
                errors.append(f"{stage.id}: missing {name}")
        if stage.animation_state != stage.id:
            errors.append(f"{stage.id}: unknown animation state")
        if stage.evidence_scope != {"claims": "direct_yunjin", "visualization": "teaching_illustration"}:
            errors.append(f"{stage.id}: invalid evidence scope")
        if not stage.related_knowledge_ids or any(k not in by_id for k in stage.related_knowledge_ids):
            errors.append(f"{stage.id}: unknown or missing knowledge ID")
        refs_ids, refs_sources = set(), set()
        if not stage.claim_refs:
            errors.append(f"{stage.id}: missing claim references")
        for ref in stage.claim_refs:
            kid, index = ref.get("knowledge_id"), ref.get("claim_index")
            item = by_id.get(kid)
            if item is None or type(index) is not int or not 0 <= index < len(item.claims):
                errors.append(f"{stage.id}: invalid claim reference")
                continue
            claim = item.claims[index]
            refs_ids.add(kid)
            refs_sources.update(claim.source_ids)
            if claim.evidence_scope != "direct_yunjin":
                errors.append(f"{stage.id}: process explanation needs direct Yunjin evidence")
        if refs_ids != set(stage.related_knowledge_ids):
            errors.append(f"{stage.id}: knowledge references disagree")
        if refs_sources != set(stage.source_ids) or not refs_sources.issubset(sources):
            errors.append(f"{stage.id}: sources disagree with referenced claims")
        if VISUAL_BOUNDARY not in stage.disclaimer:
            errors.append(f"{stage.id}: missing visual boundary")
    return errors


def load_stages(path: Path, knowledge: Iterable[KnowledgeItem], sources: dict[str, Source]) -> list[Stage]:
    stages = [Stage(**row) for row in json.loads(path.read_text(encoding="utf-8"))]
    errors = validate_stages(stages, knowledge, sources)
    if errors:
        raise ValueError("; ".join(errors))
    return stages


@dataclass(frozen=True)
class TeachingState:
    sketch_visible: bool = False
    carrier_visible: bool = False
    preparation_ready: bool = False
    warp_emphasis: str = "rest"
    weft_direction: str = "rest"
    pattern_bands: int = 0


@dataclass(frozen=True)
class TwinState:
    current_stage: str = STAGE_IDS[0]
    executed_stages: tuple[str, ...] = ()
    mode: str = "sequential"
    current_stage_executed: bool = False
    replay_count: int = 0
    teaching: TeachingState = TeachingState()
    revision: int = 0
    last_action: str = "初始状态"
    last_changes: tuple[str, ...] = ()


FIELD_LABELS = {
    "sketch_visible": "草图显示", "carrier_visible": "信息载体符号显示",
    "preparation_ready": "准备示意标记", "warp_emphasis": "经线示意强调组",
    "weft_direction": "纬向示意方向", "pattern_bands": "纹样显示段数（界面分段）",
}
STAGE_FIELDS = dict(zip(STAGE_IDS, FIELD_LABELS))


def validate_runtime(state: TwinState) -> None:
    if state.current_stage not in STAGE_IDS or state.mode not in MODES:
        raise ValueError("Invalid stage or mode")
    if len(set(state.executed_stages)) != len(state.executed_stages) or not set(state.executed_stages).issubset(STAGE_IDS):
        raise ValueError("Invalid executed stages")
    if state.current_stage_executed != (state.current_stage in state.executed_stages):
        raise ValueError("Inconsistent completion state")
    if type(state.replay_count) is not int or state.replay_count < 0 or type(state.revision) is not int or state.revision < 0:
        raise ValueError("Invalid event counts")
    t = state.teaching
    if any(type(getattr(t, key)) is not bool for key in ("sketch_visible", "carrier_visible", "preparation_ready")):
        raise ValueError("Invalid teaching flag")
    if t.warp_emphasis not in {"rest", "a", "b"} or t.weft_direction not in {"rest", "left", "right"}:
        raise ValueError("Invalid teaching symbol")
    if type(t.pattern_bands) is not int or not 0 <= t.pattern_bands <= 3:
        raise ValueError("Invalid display bands")
    completed = (t.sketch_visible, t.carrier_visible, t.preparation_ready,
                 t.warp_emphasis != "rest", t.weft_direction != "rest", t.pattern_bands == 3)
    if set(state.executed_stages) != {sid for sid, done in zip(STAGE_IDS, completed) if done}:
        raise ValueError("Teaching values and completion record disagree")


def transition(state: TwinState, action: str, value: str | None = None) -> TwinState:
    """Event -> validated new state -> view. Display bands are UI partitions."""
    validate_runtime(state)
    result = state
    if action == "reset":
        return TwinState()
    if action == "mode":
        if value not in MODES:
            raise ValueError("Invalid mode")
        stage = state.current_stage
        if value == "sequential":
            stage = next((sid for sid in STAGE_IDS if sid not in state.executed_stages), STAGE_IDS[-1])
        result = replace(state, mode=value, current_stage=stage, current_stage_executed=stage in state.executed_stages)
    elif action in {"previous", "next", "select"}:
        index = STAGE_IDS.index(state.current_stage)
        if action == "select":
            if state.mode != "free" or value not in STAGE_IDS:
                raise ValueError("Direct selection requires free exploration")
            target = value
        else:
            if action == "previous" and index == 0 or action == "next" and index == 5:
                return state
            if action == "next" and state.mode == "sequential" and not state.current_stage_executed:
                return state
            target = STAGE_IDS[index + (-1 if action == "previous" else 1)]
        result = replace(state, current_stage=target, current_stage_executed=target in state.executed_stages)
    elif action == "execute":
        t, sid = state.teaching, state.current_stage
        if sid == "pattern_design":
            t = replace(t, sketch_visible=True)
        elif sid == "pattern_translation":
            t = replace(t, carrier_visible=True)
        elif sid == "weaving_preparation":
            t = replace(t, preparation_ready=True)
        elif sid == "warp_lifting":
            t = replace(t, warp_emphasis="b" if t.warp_emphasis == "a" else "a")
        elif sid == "weft_weaving":
            t = replace(t, weft_direction="left" if t.weft_direction == "right" else "right")
        elif sid == "pattern_emergence":
            t = replace(t, pattern_bands=min(3, t.pattern_bands + 1))
        done = sid != "pattern_emergence" or t.pattern_bands == 3
        executed = set(state.executed_stages) | ({sid} if done else set())
        result = replace(state, teaching=t, executed_stages=tuple(s for s in STAGE_IDS if s in executed),
                         current_stage_executed=done, replay_count=state.replay_count + int(state.current_stage_executed))
    else:
        raise ValueError(f"Unknown event: {action}")
    changes = []
    for field, label in FIELD_LABELS.items():
        before, after = getattr(state.teaching, field), getattr(result.teaching, field)
        if before != after:
            changes.append(f"{label}：{before} → {after}")
    if result.replay_count != state.replay_count:
        changes.append(f"重播次数：{state.replay_count} → {result.replay_count}")
    if result.current_stage != state.current_stage:
        changes.append(f"当前阶段：{TITLES[STAGE_IDS.index(state.current_stage)]} → {TITLES[STAGE_IDS.index(result.current_stage)]}")
    if result.mode != state.mode:
        changes.append(f"模式：{MODES[state.mode]} → {MODES[result.mode]}")
    result = replace(result, revision=state.revision + 1, last_action=action, last_changes=tuple(changes))
    validate_runtime(result)
    return result


def state_snapshot(state: TwinState) -> dict:
    validate_runtime(state)
    return asdict(state)
