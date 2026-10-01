from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create object/source-group-safe splits for official Level 1 data.")
    parser.add_argument("--metadata", type=Path, default=ROOT / "data" / "metadata" / "official_metadata.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "splits" / "official_splits.csv")
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--minimum-groups-per-class", type=int, default=30)
    parser.add_argument("--template-on-insufficient", action="store_true")
    args = parser.parse_args()

    with args.metadata.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if row["usable_for_training"] == "true"
            and row["authorization_status"] != "unknown"
            and row["resolution_pass"] == "true"
            and row["level1_label"] in {"nanjing_yunjin", "other_brocade"}
        ]
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["level1_label"]][row["source_group_id"]].append(row)
    counts = {label: len(groups) for label, groups in grouped.items()}
    ready = all(counts.get(label, 0) >= args.minimum_groups_per_class for label in ("nanjing_yunjin", "other_brocade"))
    if not ready and not args.template_on_insufficient:
        print(f"Official split gate failed: eligible independent groups={counts}; no split created.")
        return 2

    assignments: list[tuple[dict[str, str], str]] = []
    if ready:
        rng = random.Random(args.seed)
        for label, groups in sorted(grouped.items()):
            ids = sorted(groups)
            rng.shuffle(ids)
            train_end = max(1, int(len(ids) * 0.70))
            val_end = max(train_end + 1, int(len(ids) * 0.85))
            for index, group_id in enumerate(ids):
                split = "train" if index < train_end else "val" if index < val_end else "test"
                assignments.extend((row, split) for row in groups[group_id])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["object_id", "source_group_id", "level1_label", "split"])
        for row, split in assignments:
            writer.writerow([row["object_id"], row["source_group_id"], row["level1_label"], split])
    print(f"Official split rows={len(assignments)}; eligible independent groups={counts}")
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
