"""Evaluate local image-analysis robustness without claiming classification accuracy."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.vision import analyze_locally


SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def evaluate(input_dir: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    paths = sorted(path for path in input_dir.rglob("*") if path.suffix.lower() in SUPPORTED_SUFFIXES)
    rows: list[dict[str, object]] = []
    started = time.perf_counter()
    for index, path in enumerate(paths, 1):
        row: dict[str, object] = {"index": index, "file": path.name, "status": "failed"}
        item_started = time.perf_counter()
        try:
            with Image.open(path) as image:
                result = analyze_locally(image)
            colors = result.raw_metrics["dominant_colors"]
            row.update(
                status="success",
                width=result.raw_metrics["width"],
                height=result.raw_metrics["height"],
                seconds=round(time.perf_counter() - item_started, 4),
                dominant_color=colors[0]["name"] if colors else "",
                dominant_color_share=colors[0]["share"] if colors else "",
                mean_saturation=result.raw_metrics["mean_saturation"],
                horizontal_mirror_similarity=result.raw_metrics["horizontal_mirror_similarity"],
                vertical_mirror_similarity=result.raw_metrics["vertical_mirror_similarity"],
                edge_density_proxy=result.raw_metrics["edge_density_proxy"],
                observable_facts=" | ".join(result.observable_facts),
                error="",
            )
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            row.update(seconds=round(time.perf_counter() - item_started, 4), error=str(exc))
        rows.append(row)

    successes = [row for row in rows if row["status"] == "success"]
    light_dominant = [row for row in successes if row["dominant_color"] == "白/浅灰"]
    summary = {
        "image_count": len(rows),
        "success_count": len(successes),
        "failure_count": len(rows) - len(successes),
        "pipeline_success_rate": round(len(successes) / len(rows), 4) if rows else 0.0,
        "total_seconds": round(time.perf_counter() - started, 3),
        "mean_seconds_per_image": round(
            sum(float(row["seconds"]) for row in successes) / len(successes), 4
        ) if successes else None,
        "light_background_dominant_count": len(light_dominant),
        "evaluation_scope": (
            "This is a local pipeline robustness and descriptive-output test. "
            "It is not classification accuracy because no expert ground-truth labels were supplied."
        ),
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows, summary = evaluate(args.input_dir)
    fieldnames = sorted({key for row in rows for key in row})
    with (args.output_dir / "image_test_results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (args.output_dir / "image_test_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
