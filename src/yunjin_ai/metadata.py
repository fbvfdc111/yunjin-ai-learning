from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REQUIRED_FIELDS = {
    "source_batch",
    "image_id",
    "raw_filename",
    "asset_type",
    "museum_name_or_code",
    "pattern_labels_supported_by_name",
    "craft_labels_supported_by_name",
    "garment_or_object_type",
    "usable_for_training",
    "usage_scope",
    "level1_label",
    "source_group_id",
    "evidence_text",
    "notes",
    "collection_scope",
    "classification_evidence_source",
    "level1_confidence",
    "label_evidence_available",
    "label_leakage_risk",
}


def as_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"Boolean field must be true/false, got {value!r}")
    return normalized == "true"


def split_labels(value: str) -> list[str]:
    value = str(value).strip()
    if not value or value == "unknown":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def load_metadata(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Metadata missing required fields: {sorted(missing)}")
        rows = list(reader)
    return rows


def validate_metadata(rows: list[dict[str, str]], raw_root: str | Path | None = None) -> list[str]:
    errors: list[str] = []
    ids = [row["image_id"] for row in rows]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate image_id values: {duplicates}")

    allowed_scopes = {"training", "demonstration", "reference"}
    allowed_level1 = {"nanjing_yunjin", "other_brocade", "unknown"}
    for row in rows:
        image_id = row["image_id"]
        try:
            usable = as_bool(row["usable_for_training"])
        except ValueError as exc:
            errors.append(f"{image_id}: {exc}")
            usable = False
        if row["usage_scope"] not in allowed_scopes:
            errors.append(f"{image_id}: invalid usage_scope={row['usage_scope']!r}")
        if row["level1_label"] not in allowed_level1:
            errors.append(f"{image_id}: invalid level1_label={row['level1_label']!r}")
        if usable and row["usage_scope"] != "training":
            errors.append(f"{image_id}: usable rows must have usage_scope=training")
        if raw_root is not None:
            expected = Path(raw_root) / row["source_batch"] / row["raw_filename"]
            if not expected.is_file():
                errors.append(f"{image_id}: missing image {expected}")
    return errors


def summarize(rows: list[dict[str, str]]) -> dict[str, Counter]:
    return {
        "source_batch": Counter(row["source_batch"] for row in rows),
        "asset_type": Counter(row["asset_type"] for row in rows),
        "usage_scope": Counter(row["usage_scope"] for row in rows),
        "level1_label": Counter(row["level1_label"] for row in rows),
        "usable_for_training": Counter(row["usable_for_training"] for row in rows),
        "collection_scope": Counter(row["collection_scope"] for row in rows),
        "level1_confidence": Counter(row["level1_confidence"] for row in rows),
        "label_evidence_available": Counter(row["label_evidence_available"] for row in rows),
        "label_leakage_risk": Counter(row["label_leakage_risk"] for row in rows),
    }
