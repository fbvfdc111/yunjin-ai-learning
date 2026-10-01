from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import (
    load_knowledge,
    load_sources,
    search_visual_knowledge,
    validate_knowledge,
)
from yunjin_ai.product import cultural_followup_questions
from yunjin_ai.vision import analyze_with_dots, analyze_with_openai


def main() -> int:
    knowledge_dir = ROOT / "data" / "knowledge"
    sources = load_sources(knowledge_dir / "sources.json")
    items = load_knowledge(knowledge_dir / "knowledge_base.json")
    errors = validate_knowledge(items, sources)
    with (ROOT / "data" / "metadata" / "official_metadata.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        official = list(csv.DictReader(handle))

    counts = Counter(row["level1_label"] for row in official)
    governance_ok = (
        len(official) == 95
        and counts == {"nanjing_yunjin": 47, "other_brocade": 48}
        and all(row["authorization_status"] == "unknown" for row in official)
        and all(row["usable_for_training"] == "false" for row in official)
    )
    scene_keywords = [
        "燕子", "柳枝", "飞鸟", "工笔画", "花鸟画", "黄色背景",
        "绿色叶片", "边框", "标签", "编号",
    ]
    scene_hits = search_visual_knowledge(scene_keywords, [], items)
    questions = {
        "妆花是什么？": "KB008",
        "南京云锦有哪些主要品种？": "KB007",
        "云锦为什么需要手工织造？": "KB004",
        "八宝纹有什么文化寓意？": "KB013",
    }
    answers = {
        question: answer_from_knowledge(question, items, sources)
        for question in questions
    }
    boundary = answer_from_knowledge(
        "视觉线索与文化知识之间为什么不能等同于鉴定结论？",
        items,
        sources,
    )
    report = {
        "phase": "phase5_round2",
        "knowledge_items": len(items),
        "sources": len(sources),
        "knowledge_errors": errors,
        "knowledge_uses": sorted({item.knowledge_use for item in items}),
        "official_objects": len(official),
        "official_label_counts": counts,
        "governance_invariants_ok": governance_ok,
        "bird_willow_visual_hits": [hit.item.id for hit in scene_hits],
        "answer_hits": {
            question: [hit.item.id for hit in answer.hits]
            for question, answer in answers.items()
        },
        "boundary_question_status": boundary.status,
        "boundary_question_hits": [hit.item.id for hit in boundary.hits],
        "fallback_questions": cultural_followup_questions(()),
        "dots_provider_code_retained": callable(analyze_with_dots),
        "openai_provider_code_retained": callable(analyze_with_openai),
        "real_external_api_called": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=dict))
    expected_uses = {"cultural_content", "process/history", "governance/methodology"}
    checks = (
        not errors,
        governance_ok,
        not scene_hits,
        {item.knowledge_use for item in items} == expected_uses,
        all([hit.item.id for hit in answers[q].hits] == [expected] for q, expected in questions.items()),
        boundary.status == "证据不足" and not boundary.hits,
        all("视觉线索" not in question for question in cultural_followup_questions(())),
        callable(analyze_with_dots),
        callable(analyze_with_openai),
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
