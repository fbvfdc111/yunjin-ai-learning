from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import (
    load_knowledge,
    load_official_objects,
    load_official_relations,
    load_sources,
    search_visual_knowledge,
    validate_knowledge,
    validate_official_relations,
)
from yunjin_ai.vision import analyze_with_dots, analyze_with_openai


PROTECTED_SHA256 = {
    "src/yunjin_ai/vision.py": "F1CCDB58311E63588466431B440235417D6F5595D31E4917C55B55DEC2FDEA09",
    "tests/test_phase4_dots.py": "B18DCE6BA889B5D3B064111A7A1D4A27BBF0F2552FDC5126AF66DC1F1ABDDCF7",
    "data/metadata/official_metadata.csv": "915F8C4C9605D912DA7ED8B8307957B4D000DEAED679BA250D4670BD49788823",
    "data/metadata/official_level2_candidate_labels.csv": "F326EC87F79CEF1E0B474D3515B8954B1460F7C0735A7C2E6750B15A93790C9B",
    "docs/phase2_audit_results.json": "8FDADF9470E85DA063883A55B39F398FDB9D6EF82609647508C94FAAA8052C39",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    kd = ROOT / "data" / "knowledge"
    sources = load_sources(kd / "sources.json")
    items = load_knowledge(kd / "knowledge_base.json")
    official = load_official_objects(ROOT / "data" / "metadata" / "official_metadata.csv")
    relations = load_official_relations(kd / "official_object_knowledge_map.json")
    knowledge_errors = validate_knowledge(items, sources)
    relation_errors = validate_official_relations(relations, official, items)

    counts = Counter(row["level1_label"] for row in official)
    governance_ok = (
        len(official) == 95
        and counts == {"nanjing_yunjin": 47, "other_brocade": 48}
        and all(row["authorization_status"] == "unknown" for row in official)
        and all(row["usable_for_training"] == "false" for row in official)
    )
    required = {"KB008", "KB009", "KB016", "KB017", "KB018", "KB019", "KB020", "KB021", "KB022", "KB023"}
    by_id = {item.id: item for item in items}
    general_ids = {
        item.id for item in items
        if any(claim.evidence_scope == "general_cultural_background" for claim in item.claims)
    }
    protected_actual = {relative: sha256(ROOT / relative) for relative in PROTECTED_SHA256}
    protected_ok = protected_actual == PROTECTED_SHA256
    visual_general_hits = search_visual_knowledge(["八宝", "莲", "松鹤", "寿字"], [], items)
    visual_object_hits = search_visual_knowledge(["鹤", "寿", "灵芝"], [], items)
    questions = {
        "妆花是什么？": "KB008",
        "织金是什么？": "KB009",
        "库锦是什么？": "KB016",
        "库缎是什么？": "KB017",
        "挑花结本是什么，有什么作用？": "KB019",
        "南京云锦官方对象中有鹤纹吗？": "KB021",
    }
    answer_hits = {
        question: [hit.item.id for hit in answer_from_knowledge(question, items, sources).hits]
        for question in questions
    }

    relation_count = sum(len(record["relations"]) for record in relations)
    linked_count = sum(bool(record["relations"]) for record in relations)
    report = {
        "phase": "phase5_round3",
        "knowledge_items": len(items),
        "knowledge_count_is_quota": False,
        "sources": len(sources),
        "knowledge_errors": knowledge_errors,
        "required_core_ids_present": required.issubset(by_id),
        "general_background_ids": sorted(general_ids),
        "general_background_visual_disabled": all(by_id[item_id].visual_retrieval == "disabled" for item_id in general_ids),
        "visual_general_hits": [hit.item.id for hit in visual_general_hits],
        "visual_object_name_hits": [hit.item.id for hit in visual_object_hits],
        "official_objects": len(official),
        "official_label_counts": dict(counts),
        "authorization_unknown": sum(row["authorization_status"] == "unknown" for row in official),
        "usable_for_training_true": sum(row["usable_for_training"] == "true" for row in official),
        "governance_invariants_ok": governance_ok,
        "relation_records": len(relations),
        "objects_with_relations": linked_count,
        "relations": relation_count,
        "relation_errors": relation_errors,
        "answer_hits": answer_hits,
        "protected_sha256": protected_actual,
        "protected_sha256_ok": protected_ok,
        "data_official_files": sum(path.is_file() for path in (ROOT / "data" / "official").rglob("*")),
        "dots_provider_code_retained": callable(analyze_with_dots),
        "openai_provider_code_retained": callable(analyze_with_openai),
        "real_external_api_called": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    checks = (
        not knowledge_errors,
        not relation_errors,
        required.issubset(by_id),
        report["general_background_visual_disabled"],
        not visual_general_hits,
        not visual_object_hits,
        governance_ok,
        len(relations) == 47,
        protected_ok,
        all(expected in answer_hits[question] for question, expected in questions.items()),
        callable(analyze_with_dots),
        callable(analyze_with_openai),
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

