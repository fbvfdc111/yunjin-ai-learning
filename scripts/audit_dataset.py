from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.metadata import as_bool, load_metadata, summarize, validate_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate metadata and inventory raw images.")
    parser.add_argument("--metadata", default=ROOT / "data/metadata/metadata.csv", type=Path)
    parser.add_argument("--raw-root", default=ROOT / "data/raw", type=Path)
    parser.add_argument("--stats-out", default=ROOT / "docs/category_stats.csv", type=Path)
    parser.add_argument("--manifest-out", default=ROOT / "data/metadata/file_manifest.csv", type=Path)
    args = parser.parse_args()

    rows = load_metadata(args.metadata)
    errors = validate_metadata(rows, args.raw_root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest_out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["image_id", "relative_path", "sha256", "width", "height", "bytes"],
        )
        writer.writeheader()
        for row in rows:
            path = args.raw_root / row["source_batch"] / row["raw_filename"]
            with Image.open(path) as image:
                width, height = image.size
            writer.writerow(
                {
                    "image_id": row["image_id"],
                    "relative_path": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "width": width,
                    "height": height,
                    "bytes": path.stat().st_size,
                }
            )

    summaries = summarize(rows)
    pattern_counts = Counter()
    for row in rows:
        for value in row["pattern_labels_supported_by_name"].split(";"):
            if value and value != "unknown":
                pattern_counts[value] += 1

    args.stats_out.parent.mkdir(parents=True, exist_ok=True)
    with args.stats_out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["dimension", "category", "count", "definition"])
        for dimension, counts in summaries.items():
            for category, count in sorted(counts.items()):
                writer.writerow([dimension, category, count, "metadata direct count"])
        writer.writerow(["independent_source_groups", "all", len({row["source_group_id"] for row in rows}), "group-aware count"])
        writer.writerow(["near_duplicate_group", "YAABB-00501", 3, "two near-duplicate views plus one record card"])
        for label, count in sorted(pattern_counts.items()):
            writer.writerow(["name_supported_pattern", label, count, "literal evidence only; not a training class count"])

    print(json.dumps({key: dict(value) for key, value in summaries.items()}, ensure_ascii=False, indent=2))
    print(f"Validated {len(rows)} rows; usable training rows={sum(as_bool(r['usable_for_training']) for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

