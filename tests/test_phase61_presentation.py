import sys
from pathlib import Path
from unittest.mock import patch
import os
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from yunjin_ai.digital_twin import STAGE_IDS, TwinState, transition
from yunjin_ai.twin_presentation import learning_status


def test_partial_progress_and_free_exploration_are_not_reported_as_complete():
    state = transition(transition(TwinState(), 'mode', 'free'), 'select', STAGE_IDS[-1])
    for bands in (1, 2, 3):
        state = transition(state, 'execute')
        summary = learning_status(state)
        assert summary['体验进度'] == '6 / 6'
        assert summary['已完成教学步骤'] == ('1 / 6' if bands == 3 else '0 / 6')
        assert dict(summary['环节状态'])['纹样形成'] == f'{bands} / 3'
        assert dict(summary['环节状态'])['图案设计'] == '待体验'
    assert learning_status(transition(state, 'reset'))['已完成教学步骤'] == '0 / 6'


def test_home_entry_and_raw_state_is_only_inside_collapsed_expander():
    with patch.dict(os.environ, {'DOTS_API_KEY': '', 'OPENAI_API_KEY': ''}):
        at = AppTest.from_file(ROOT / 'app.py', default_timeout=20).run()
        at.button(key='home_open_twin').click().run()
        assert not at.exception
        assert at.segmented_control(key='main_tab').value == '数字织机'
        raw = next(e for e in at.expander if e.label == '查看运行时 Twin State')
        assert raw.proto.expanded is False
        assert len(raw.get('json')) == 1
        assert len(at.get('json')) == 1
        text = '\n'.join(e.value for e in [*at.markdown, *at.caption])
        assert '当前为教学状态，并非实体织机传感器实时数据。' in text
        assert '当前环节：图案设计' in text
        assert 'pattern_design' not in text
        at.button(key='twin_execute').click().run()
        assert '已完成教学步骤：1 / 6' in '\n'.join(e.value for e in at.caption)


@pytest.mark.parametrize('sid', STAGE_IDS)
def test_readable_panel_tracks_live_state_across_execute_replay_and_reset(sid):
    state = transition(transition(TwinState(), 'mode', 'free'), 'select', sid)
    before = learning_status(state)
    state = transition(state, 'execute')
    after = learning_status(state)
    assert before['环节状态'] != after['环节状态']
    if sid != STAGE_IDS[-1]:
        assert learning_status(transition(state, 'execute')) == after
    assert learning_status(transition(state, 'reset')) == learning_status(TwinState())
