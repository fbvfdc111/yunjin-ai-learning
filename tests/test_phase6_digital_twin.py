from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yunjin_ai.digital_twin import (
    STAGE_IDS, TITLES, TwinState, load_stages, transition, validate_runtime, validate_stages,
)
from yunjin_ai.digital_twin_svg import render_twin_svg
from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import load_knowledge, load_sources


def evidence():
    items = load_knowledge(ROOT / "data/knowledge/knowledge_base.json")
    sources = load_sources(ROOT / "data/knowledge/sources.json")
    stages = load_stages(ROOT / "data/digital_twin/twin_states.json", items, sources)
    return stages, items, sources


def svg_element(state, element_id):
    html = render_twin_svg(state)
    svg = ET.fromstring(html[html.index('<svg '):html.index('</svg>') + 6])
    return next(el for el in svg.iter() if el.get('id') == element_id)


def test_six_states_and_claim_level_sources():
    stages, items, sources = evidence()
    assert validate_stages(stages, items, sources) == []
    assert [s.stage_index for s in stages] == list(range(1, 7))
    assert tuple(s.id for s in stages) == STAGE_IDS
    assert len(set(s.id for s in stages)) == 6
    for stage in stages:
        assert stage.claim_refs and stage.source_ids and stage.ai_question


@pytest.mark.parametrize("change", [
    {"id": STAGE_IDS[1]}, {"stage_index": 8}, {"related_knowledge_ids": ["KB999"]},
    {"source_ids": ["S12"]}, {"claim_refs": [{"knowledge_id": "KB003", "claim_index": 9}]},
    {"claim_refs": [{"knowledge_id": "KB003", "claim_index": -1}]},
    {"claim_refs": []}, {"ai_question": ""}, {"operator": ""},
    {"animation_state": "physical_simulation"}, {"evidence_scope": {"claims": "general_cultural_background"}},
])
def test_invalid_evidence_fails_closed(change):
    stages, items, sources = evidence()
    stages[0] = replace(stages[0], **change)
    assert validate_stages(stages, items, sources)


def test_unsupported_role_names_are_not_invented():
    stages, _, _ = evidence()
    for stage in stages[:3]:
        assert "不足以支持统一岗位名称" in stage.operator


@pytest.mark.parametrize("index,expected", [(0,"KB010"),(1,"KB019"),(2,"KB003"),(3,"KB004"),(4,"KB004"),(5,"KB003")])
def test_learning_questions_are_answered_by_existing_evidence(index, expected):
    stages, items, sources = evidence()
    answer = answer_from_knowledge(stages[index].ai_question, items, sources)
    assert expected in [hit.item.id for hit in answer.hits]
    assert answer.status == "基于本地知识库"


def test_sequential_execution_and_bounds():
    state = TwinState()
    assert transition(state, "previous") == state
    assert transition(state, "next") == state
    for index, sid in enumerate(STAGE_IDS):
        assert state.current_stage == sid
        assert not state.current_stage_executed
        count = 3 if index == 5 else 1
        for _ in range(count):
            state = transition(state, "execute")
        assert state.current_stage_executed
        assert len(state.executed_stages) == index + 1
        state = transition(state, "next")
    assert state.executed_stages == STAGE_IDS
    assert state.current_stage == STAGE_IDS[-1]
    assert state.replay_count == 0


@pytest.mark.parametrize("index,element,attribute,expected", [
    (0,"draft","data-visible","true"), (1,"carrier","data-visible","true"),
    (2,"preparation","data-ready","true"), (3,"warp","data-emphasis","a"),
    (4,"weft","data-direction","right"), (5,"pattern","data-bands","1"),
])
def test_same_stage_has_runtime_driven_visual_change(index, element, attribute, expected):
    before = transition(transition(TwinState(), "mode", "free"), "select", STAGE_IDS[index])
    after = transition(before, "execute")
    assert before.current_stage == after.current_stage
    assert before.teaching != after.teaching
    assert svg_element(before, element).get(attribute) != expected
    assert svg_element(after, element).get(attribute) == expected
    assert not before.executed_stages  # Selecting alone does not execute anything.


def test_free_exploration_does_not_fake_predecessors():
    state = transition(transition(TwinState(), "mode", "free"), "select", STAGE_IDS[4])
    state = transition(state, "execute")
    assert state.executed_stages == (STAGE_IDS[4],)
    assert not state.teaching.preparation_ready
    state = transition(state, "mode", "sequential")
    assert state.current_stage == STAGE_IDS[0]
    assert not state.current_stage_executed
    assert state.teaching.weft_direction == "right"


def test_replay_changes_emphasis_and_preserves_completion():
    state = transition(transition(TwinState(), "mode", "free"), "select", STAGE_IDS[3])
    first = transition(state, "execute")
    replay = transition(first, "execute")
    assert (first.teaching.warp_emphasis, replay.teaching.warp_emphasis) == ("a", "b")
    assert replay.replay_count == 1
    assert replay.executed_stages == first.executed_stages
    assert svg_element(replay, 'warp').get('data-emphasis') == 'b'


def test_partial_pattern_state_is_not_complete_and_navigation_retains_it():
    state = transition(transition(TwinState(), "mode", "free"), "select", STAGE_IDS[5])
    for bands in (1, 2, 3):
        state = transition(state, "execute")
        assert state.teaching.pattern_bands == bands
        assert state.current_stage_executed == (bands == 3)
        assert svg_element(state, 'pattern').get('data-bands') == str(bands)
        state = transition(transition(state, "previous"), "next")
    assert transition(state, 'execute').teaching.pattern_bands == 3
    assert transition(state, 'reset') == TwinState()


def test_invalid_runtime_and_events_are_rejected_server_side():
    with pytest.raises(ValueError):
        transition(TwinState(), 'select', STAGE_IDS[-1])
    with pytest.raises(ValueError):
        transition(TwinState(), 'mode', 'sensor')
    with pytest.raises(ValueError):
        validate_runtime(replace(TwinState(), current_stage_executed=True))
    with pytest.raises(ValueError):
        validate_runtime(replace(TwinState(), executed_stages=(STAGE_IDS[0],)))


def test_svg_is_self_contained_and_reduced_motion_preserves_state():
    state = transition(TwinState(), 'execute')
    html = render_twin_svg(state)
    reduced = render_twin_svg(state, reduced_motion=True)
    assert 'animation:twinPulse' in html
    assert 'animation:twinPulse' not in reduced
    assert 'prefers-reduced-motion' in reduced
    assert 'data-visible="true"' in reduced
    for forbidden in ('<script', '<image', 'href=', 'src=', 'url(', 'foreignObject'):
        assert forbidden not in html
