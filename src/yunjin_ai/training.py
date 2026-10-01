from __future__ import annotations

from collections import Counter


def assert_level1_ready(rows: list[dict[str, str]], minimum_per_class: int = 30) -> None:
    counts = Counter(
        row["level1_label"]
        for row in rows
        if row["usable_for_training"].lower() == "true"
        and row["level1_label"] in {"nanjing_yunjin", "other_brocade"}
    )
    missing = {label: max(0, minimum_per_class - counts[label]) for label in ("nanjing_yunjin", "other_brocade")}
    if any(missing.values()):
        raise RuntimeError(
            "Level 1 data gate failed. "
            f"Confirmed usable counts={dict(counts)}; minimum={minimum_per_class}; shortfall={missing}. "
            "No training was started."
        )


def assert_level2_ready(
    rows: list[dict[str, str]], minimum_groups_per_label: int = 20
) -> dict[str, int]:
    from .metadata import split_labels

    groups: dict[str, set[str]] = {}
    for row in rows:
        if row["usable_for_training"].lower() != "true":
            continue
        group = row["source_group_id"] or row["image_id"]
        for label in split_labels(row["pattern_labels_supported_by_name"]):
            groups.setdefault(label, set()).add(group)
    counts = {label: len(values) for label, values in groups.items()}
    eligible = {label: count for label, count in counts.items() if count >= minimum_groups_per_label}
    if len(eligible) < 2:
        raise RuntimeError(
            "Level 2 data gate failed. Need at least two labels with "
            f">={minimum_groups_per_label} independent source groups; observed={counts}. "
            "No training was started."
        )
    return eligible

