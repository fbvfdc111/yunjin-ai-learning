from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.knowledge import load_knowledge, load_sources, search_visual_knowledge, validate_knowledge
from yunjin_ai.product import apply_guide_handoff, visual_observation_sections
from yunjin_ai.vision import analyze_image, analyze_with_dots, analyze_with_openai


def main() -> int:
    knowledge_dir = ROOT / "data" / "knowledge"
    sources = load_sources(knowledge_dir / "sources.json")
    items = load_knowledge(knowledge_dir / "knowledge_base.json")
    errors = validate_knowledge(items, sources)
    with (ROOT / "data" / "metadata" / "official_metadata.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        official = list(csv.DictReader(handle))

    labels = Counter(row["level1_label"] for row in official)
    governance_ok = (
        len(official) == 95
        and labels == {"nanjing_yunjin": 47, "other_brocade": 48}
        and all(row["authorization_status"] == "unknown" for row in official)
        and all(row["usable_for_training"] == "false" for row in official)
    )
    generic_hits = search_visual_knowledge(["花卉", "红色", "对称", "构图"], [], items)
    specific_hits = search_visual_knowledge(["牡丹"], [], items)
    confirmed_hits = search_visual_knowledge([], ["妆花"], items)

    local_result = analyze_image(Image.new("RGB", (64, 64), (160, 30, 55)), provider="local")
    sections = visual_observation_sections(local_result)
    handoff_state: dict[str, str] = {}
    apply_guide_handoff(handoff_state, "八宝纹有什么文化寓意？")

    report = {
        "phase": "phase5_round1",
        "knowledge_items": len(items),
        "sources": len(sources),
        "knowledge_errors": errors,
        "official_objects": len(official),
        "official_label_counts": labels,
        "governance_invariants_ok": governance_ok,
        "generic_visual_hits": [hit.item.id for hit in generic_hits],
        "specific_visual_hits": [hit.item.id for hit in specific_hits],
        "confirmed_topic_hits": [hit.item.id for hit in confirmed_hits],
        "visual_retrieval_threshold_ok": not generic_hits and [hit.item.id for hit in specific_hits] == ["KB012"],
        "local_cv_provider": local_result.provider,
        "visual_sections_present": all(name in sections for name in ("纹样与主体", "构图特征", "色彩特征")),
        "dots_provider_code_retained": callable(analyze_with_dots),
        "openai_provider_code_retained": callable(analyze_with_openai),
        "guide_handoff_ok": handoff_state
        == {"guide_question": "八宝纹有什么文化寓意？", "main_tab": "AI文化助手"},
        "real_external_api_called": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=dict))
    checks = (
        not errors,
        governance_ok,
        report["visual_retrieval_threshold_ok"],
        local_result.provider == "local_cv",
        report["visual_sections_present"],
        report["dots_provider_code_retained"],
        report["openai_provider_code_retained"],
        report["guide_handoff_ok"],
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
