from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import load_knowledge, load_sources, validate_knowledge
from yunjin_ai.vision import analyze_image, dots_is_configured, openai_is_configured


def main() -> int:
    knowledge_dir = ROOT / "data" / "knowledge"
    sources = load_sources(knowledge_dir / "sources.json")
    items = load_knowledge(knowledge_dir / "knowledge_base.json")
    errors = validate_knowledge(items, sources)
    with (ROOT / "data" / "metadata" / "official_metadata.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        official = list(csv.DictReader(handle))
    image = Image.new("RGB", (64, 64), (160, 30, 55))
    vision = analyze_image(image, provider="local")
    answer = answer_from_knowledge("妆花是什么？", items, sources)
    report = {
        "knowledge_items": len(items),
        "sources": len(sources),
        "knowledge_errors": errors,
        "official_objects": len(official),
        "official_unknown_authorization": sum(row["authorization_status"] == "unknown" for row in official),
        "official_training_eligible": sum(row["usable_for_training"] == "true" for row in official),
        "local_vision_provider": vision.provider,
        "local_vision_observation_count": len(vision.observable_facts),
        "grounded_answer_status": answer.status,
        "openai_provider_configured": openai_is_configured(),
        "dots_provider_configured": dots_is_configured(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
