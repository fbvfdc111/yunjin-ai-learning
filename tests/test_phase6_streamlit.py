from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from yunjin_ai.digital_twin import STAGE_IDS, TwinState, VISUAL_BOUNDARY, STATE_BOUNDARY
from yunjin_ai.digital_twin_svg import render_twin_svg


def app():
    with patch.dict(os.environ, {'DOTS_API_KEY':'','OPENAI_API_KEY':'','OPENAI_VISION_MODEL':''}):
        at = AppTest.from_file(ROOT / 'app.py', default_timeout=20).run()
        at.segmented_control(key='main_tab').set_value('数字织机').run()
    assert not at.exception
    return at


def rendered(at):
    return '\n'.join(str(e.value) for e in [
        *at.title, *at.subheader, *at.markdown, *at.caption, *at.info, *at.warning, *at.success, *at.error
    ])


def test_navigation_visible_state_and_sequential_buttons():
    at = app()
    assert at.segmented_control(key='main_tab').options == ['首页','AI探锦','数字织机','AI文化助手','数据与可信AI']
    assert at.session_state['twin_state'] == TwinState()
    assert at.button(key='twin_previous').disabled
    assert at.button(key='twin_next').disabled
    text = rendered(at)
    assert VISUAL_BOUNDARY in text and STATE_BOUNDARY in text
    assert '数字孪生状态' in text
    for sid in STAGE_IDS:
        assert at.session_state['twin_state'].current_stage == sid
        for _ in range(3 if sid == STAGE_IDS[-1] else 1):
            at.button(key='twin_execute').click().run()
            assert not at.exception
        assert at.session_state['twin_state'].current_stage_executed
        if sid != STAGE_IDS[-1]:
            at.button(key='twin_next').click().run()
            assert not at.exception
    assert at.session_state['twin_state'].executed_stages == STAGE_IDS
    assert at.button(key='twin_next').disabled


def test_free_mode_replay_return_and_reset():
    at = app()
    at.segmented_control(key='twin_mode_widget').set_value('free').run()
    at.button(key=f'twin_select_{STAGE_IDS[3]}').click().run()
    at.button(key='twin_execute').click().run()
    at.button(key='twin_execute').click().run()
    state = at.session_state['twin_state']
    assert state.replay_count == 1 and state.teaching.warp_emphasis == 'b'
    assert 'a → b' in rendered(at)
    at.segmented_control(key='main_tab').set_value('首页').run()
    at.segmented_control(key='main_tab').set_value('数字织机').run()
    assert at.session_state['twin_state'] == state
    at.segmented_control(key='twin_mode_widget').set_value('sequential').run()
    assert at.session_state['twin_state'].current_stage == STAGE_IDS[0]
    at.button(key='twin_reset').click().run()
    assert at.session_state['twin_state'] == TwinState()
    assert not at.exception


@pytest.mark.parametrize('sid', STAGE_IDS)
def test_every_stage_handoff_uses_existing_assistant(sid):
    at = app()
    at.segmented_control(key='twin_mode_widget').set_value('free').run()
    at.button(key=f'twin_select_{sid}').click().run()
    before = at.session_state['twin_state']
    at.session_state['last_answer'] = 'old answer sentinel'
    at.session_state['last_question'] = 'old question sentinel'
    at.button(key='twin_ask_guide').click().run()
    assert not at.exception
    assert at.segmented_control(key='main_tab').value == 'AI文化助手'
    question = at.text_input(key='guide_question').value
    assert question and question.endswith('？')
    assert 'last_answer' not in at.session_state and 'last_question' not in at.session_state
    next(b for b in at.button if b.label == '获取可信回答').click().run()
    assert not at.exception
    assert question in rendered(at)
    assert 'old answer sentinel' not in rendered(at)
    assert at.session_state['last_answer'].hits
    at.segmented_control(key='main_tab').set_value('数字织机').run()
    assert at.session_state['twin_state'] == before


def test_twin_page_never_calls_vision_or_loads_an_official_image():
    with patch('yunjin_ai.vision.analyze_image', side_effect=AssertionError('unexpected vision call')), \
         patch('PIL.Image.open', side_effect=AssertionError('unexpected image read')):
        at = app()
        at.segmented_control(key='twin_mode_widget').set_value('free').run()
        for sid in STAGE_IDS:
            at.button(key=f'twin_select_{sid}').click().run()
            at.button(key='twin_execute').click().run()
            assert not at.exception


def test_svg_document_reaches_iframe_and_matches_runtime_state():
    at = app()
    initial = at.get('iframe')[0].proto.srcdoc
    assert '<svg ' in initial and 'data-visible="false"' in initial
    at.button(key='twin_execute').click().run()
    document = at.get('iframe')[0].proto.srcdoc
    assert document == render_twin_svg(at.session_state['twin_state'])
    assert document != initial
    assert 'id="draft" data-visible="true"' in document
    at.checkbox(key='twin_reduced_motion').check().run()
    assert 'animation:twinPulse' not in at.get('iframe')[0].proto.srcdoc


def test_digital_twin_quiz_shows_explanation_and_anonymous_scope():
    at = app()
    at.radio(key='quiz_choice_pattern_design').set_value(0).run()
    at.button(key='quiz_submit_pattern_design').click().run()
    assert not at.exception
    text = rendered(at)
    assert '知识测验' in text
    assert '回答正确' in text
    assert '草图只是学习路径的起点' in text
    assert '匿名本地记录' in text
    assert '不能夸大为长期学习成效' in text
    assert at.session_state['quiz_evaluations']['pattern_design'].is_correct
