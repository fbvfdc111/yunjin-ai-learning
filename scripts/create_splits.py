from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.metadata import as_bool, load_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Create source-group-aware Level 1 splits.")
    parser.add_argument("--metadata", default=ROOT / "data/metadata/metadata.csv", type=Path)
    parser.add_argument("--output", default=ROOT / "data/splits/splits.csv", type=Path)
    parser.add_argument("--seed", default=20260903, type=int)
    parser.add_argument("--minimum-groups-per-class", default=10, type=int)
    parser.add_argument("--template-on-insufficient", action="store_true")
    args = parser.parse_args()

    rows = [
        row
        for row in load_metadata(args.metadata)
        if as_bool(row["usable_for_training"])
        and row["level1_label"] in {"nanjing_yunjin", "other_brocade"}
    ]
    by_label: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_label[row["level1_label"]][row["source_group_id"] or row["image_id"]].append(row)
    counts = {label: len(groups) for label, groups in by_label.items()}
    ready = all(counts.get(label, 0) >= args.minimum_groups_per_class for label in ("nanjing_yunjin", "other_brocade"))
    if not ready and not args.template_on_insufficient:
        print(f"Split gate failed: independent group counts={counts}. No split was created.", file=sys.stderr)
        return 2

    assignments: list[tuple[dict[str, str], str]] = []
    if ready:
        rng = random.Random(args.seed)
        for label, groups in sorted(by_label.items()):
            group_ids = sorted(groups)
            rng.shuffle(group_ids)
            n = len(group_ids)
            train_end = max(1, int(n * 0.70))
            val_end = max(train_end + 1, int(n * 0.85))
            for index, group_id in enumerate(group_ids):
                split = "train" if index < train_end else "val" if index < val_end else "test"
                assignments.extend((row, split) for row in groups[group_id])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image_id", "source_group_id", "level1_label", "split"])
        for row, split in assignments:
            writer.writerow([row["image_id"], row["source_group_id"], row["level1_label"], split])
    if ready:
        print(f"Created {len(assignments)} group-aware assignments at {args.output}")
    else:
        print(f"Created header-only split template at {args.output}; data gate remains unmet: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

