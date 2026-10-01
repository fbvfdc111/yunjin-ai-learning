from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data" / "metadata" / "official_metadata.csv"
AUDIT_JSON = ROOT / "docs" / "phase2_audit_results.json"
DUPLICATES_CSV = ROOT / "docs" / "phase2_duplicate_review.csv"


def dhash(path: Path, size: int = 8) -> int:
    with Image.open(path) as image:
        gray = image.convert("L").resize((size + 1, size))
        pixels = list(gray.getdata())
    value = 0
    for row in range(size):
        offset = row * (size + 1)
        for column in range(size):
            value = (value << 1) | int(pixels[offset + column] > pixels[offset + column + 1])
    return value


def distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def main() -> None:
    with METADATA.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    missing_source = [row["object_id"] for row in rows if not row["source_url"] or not row["evidence_file"]]
    missing_label_evidence = [row["object_id"] for row in rows if row["label_evidence_available"] != "true"]
    damaged = [row["object_id"] for row in rows if row["image_valid"] != "true"]
    low_resolution = [row["object_id"] for row in rows if row["resolution_pass"] != "true"]
    unknown_authorization = [row["object_id"] for row in rows if row["authorization_status"] == "unknown"]

    sha_groups: dict[str, list[str]] = defaultdict(list)
    hashes: dict[str, int] = {}
    for row in rows:
        if row["sha256"]:
            sha_groups[row["sha256"]].append(row["object_id"])
        image_path = ROOT / row["model_image_file"]
        if image_path.is_file():
            hashes[row["object_id"]] = dhash(image_path)
    exact = [group for group in sha_groups.values() if len(group) > 1]

    # dHash is only a review signal. Compare within each class and never auto-delete.
    level_by_id = {row["object_id"]: row["level1_label"] for row in rows}
    near: list[dict[str, str]] = []
    for left, right in combinations(hashes, 2):
        if level_by_id[left] != level_by_id[right]:
            continue
        delta = distance(hashes[left], hashes[right])
        if delta <= 4:
            near.append({"left_object_id": left, "right_object_id": right, "dhash_distance": str(delta), "decision": "manual_review"})

    object_ids = [row["object_id"] for row in rows]
    duplicate_object_ids = [key for key, count in Counter(object_ids).items() if count > 1]
    names: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        names[(row["level1_label"], row["official_name"])].append(row["object_id"])
    duplicate_names = [group for group in names.values() if len(group) > 1]

    result = {
        "audit_date": "2026-09-03",
        "object_count": len(rows),
        "by_class": dict(Counter(row["level1_label"] for row in rows)),
        "by_source_type": dict(Counter(row["source_type"] for row in rows)),
        "image_valid_count": len(rows) - len(damaged),
        "resolution_pass_count": len(rows) - len(low_resolution),
        "resolution_pass_by_class": dict(Counter(row["level1_label"] for row in rows if row["resolution_pass"] == "true")),
        "direct_training_eligible_count": sum(row["usable_for_training"] == "true" for row in rows),
        "missing_source_count": len(missing_source),
        "missing_label_evidence_count": len(missing_label_evidence),
        "damaged_image_count": len(damaged),
        "low_resolution_count": len(low_resolution),
        "unknown_authorization_count": len(unknown_authorization),
        "duplicate_object_ids": duplicate_object_ids,
        "exact_duplicate_groups": exact,
        "same_class_exact_name_groups": duplicate_names,
        "near_duplicate_review_pairs": len(near),
        "label_leakage_review": dict(Counter(row["label_leakage_risk"] for row in rows)),
        "training_gate": {
            "minimum_independent_objects_per_class": 30,
            "requires_authorized_reuse": True,
            "requires_resolution_pass": True,
            "requires_manual_leakage_review": True,
            "decision": "do_not_train",
            "reason": "两类可追溯标签数量已达门槛，但授权状态均为unknown；清册缩略图81张未通过224像素门槛；网页主体图仅14张通过分辨率，且仍需人工泄漏复核。",
        },
        "lists": {
            "missing_source": missing_source,
            "missing_label_evidence": missing_label_evidence,
            "damaged": damaged,
            "low_resolution": low_resolution,
            "unknown_authorization": unknown_authorization,
        },
    }
    AUDIT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with DUPLICATES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["left_object_id", "right_object_id", "dhash_distance", "decision"])
        writer.writeheader()
        writer.writerows(near)
    print(json.dumps({key: value for key, value in result.items() if key != "lists"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
