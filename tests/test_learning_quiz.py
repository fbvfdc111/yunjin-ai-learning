from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.digital_twin import STAGE_IDS, TwinState, transition
from yunjin_ai.learning_quiz import (
    QUIZ_ITEMS,
    anonymous_result_record,
    append_anonymous_result,
    evaluate_quiz,
    evaluation_summary,
    validate_quiz_items,
)


def test_quiz_items_cover_six_stages_with_explanations():
    assert validate_quiz_items() == []
    assert tuple(item.stage_id for item in QUIZ_ITEMS) == STAGE_IDS
    for item in QUIZ_ITEMS:
        assert item.explanation
        assert item.evidence_note
        assert not any(word in item.question + item.explanation for word in ("准确率", "F1", "真实同步实体织机"))


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_evaluate_quiz_returns_correct_answer_explanation(stage_id):
    evaluation = evaluate_quiz(stage_id, 0)
    assert evaluation.stage_id == stage_id
    assert evaluation.is_correct
    assert evaluation.correct_index == 0
    assert evaluation.explanation
    assert evaluation.evidence_note


def test_invalid_quiz_answer_is_rejected():
    with pytest.raises(ValueError):
        evaluate_quiz(STAGE_IDS[0], 99)
    with pytest.raises(ValueError):
        evaluate_quiz("unknown", 0)


def test_anonymous_result_record_contains_no_private_payload(tmp_path):
    state = transition(TwinState(), "execute")
    evaluation = evaluate_quiz(STAGE_IDS[0], 0)
    record = anonymous_result_record(
        evaluation,
        state,
        session_token="session-demo",
        created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    assert record["anonymous_session"] == "session-demo"
    assert record["is_correct"] is True
    forbidden = {"name", "phone", "email", "ip", "image", "api_payload", "question_text"}
    assert not (forbidden & set(record))

    target = tmp_path / "anonymous_quiz_results.ndjson"
    append_anonymous_result(target, {**record, "name": "must not be saved", "image": "must not be saved"})
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["stage_id"] == STAGE_IDS[0]
    assert "name" not in saved
    assert "image" not in saved


def test_evaluation_summary_counts_only_submitted_answers():
    rows = [evaluate_quiz(STAGE_IDS[0], 0), evaluate_quiz(STAGE_IDS[1], 1)]
    assert evaluation_summary(rows) == {"answered": 2, "correct": 1}
