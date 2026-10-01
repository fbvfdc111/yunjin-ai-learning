from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import load_knowledge, load_sources, search_visual_knowledge
from yunjin_ai.vision import analyze_image


def first_file(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return matches[0]


def analyze_case(name: str, image: Image.Image, confirmed_terms: tuple[str, ...] = ()) -> dict:
    result = analyze_image(image, provider="dots")
    items = load_knowledge(ROOT / "data/knowledge/knowledge_base.json")
    hits = search_visual_knowledge(result.retrieval_keywords, confirmed_terms, items, limit=4)
    return {
        "case": name,
        "actual_provider": result.provider,
        "provider_status": result.provider_status,
        "retrieval_keywords": list(result.retrieval_keywords),
        "confirmed_learning_terms": list(confirmed_terms),
        "matched_hit_ids": [hit.item.id for hit in hits],
        "limitations": list(result.limitations),
        "no_identity_claim": not any(
            word in " ".join(result.observable_facts)
            for word in ("属于南京云锦", "确定为南京云锦", "真伪", "年代为")
        ),
    }


def unrelated_image() -> Image.Image:
    image = Image.new("RGB", (180, 120), "#f6f6f6")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 80, 100), fill="#3d6fb6")
    draw.ellipse((105, 25, 160, 85), fill="#d64545")
    return image


def main() -> int:
    sources = load_sources(ROOT / "data/knowledge/sources.json")
    knowledge = load_knowledge(ROOT / "data/knowledge/knowledge_base.json")
    yunjin_path = first_file("data/official/model_images_candidates/nanjing_yunjin/*.png")
    other_path = first_file("data/official/model_images_candidates/other_brocade/*.png")

    with Image.open(yunjin_path) as yunjin, Image.open(other_path) as other:
        cases = [
            analyze_case("nanjing_yunjin_sample", yunjin.convert("RGB"), ("龙",)),
            analyze_case("other_brocade_sample", other.convert("RGB")),
            analyze_case("unrelated_geometric_image", unrelated_image()),
        ]

    boundary = answer_from_knowledge(
        "这张图片能不能证明它就是南京云锦并判断年代真伪？",
        knowledge,
        sources,
    )
    report = {
        "scope": "No external API key is used; Dots falls back to local_cv when not configured.",
        "cases": cases,
        "boundary_question_status": boundary.status,
        "boundary_answer": boundary.answer,
        "ok": all(case["actual_provider"] == "local_cv" and case["no_identity_claim"] for case in cases)
        and boundary.status == "证据不足",
    }
    target = ROOT / "docs" / "phase62_vision_acceptance.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
