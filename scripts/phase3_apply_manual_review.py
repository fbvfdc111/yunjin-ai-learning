from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "metadata" / "phase3_open_data_candidates.csv"

OVERRIDES = {
    "met_65366": ("false", "high; bottom color scale/accession strip visible; crop required"),
    "met_71026": ("false", "high; accession number and measurement strip visible; crop required"),
    "met_71070": ("false", "high; accession number visible; crop required"),
    "met_71288": ("false", "high; museum reference strip visible at lower edge; crop required"),
}

LABEL_CONFLICTS = {
    "commons_yunjin_qianlong_dragon_robe": {
        "class_label": "unknown",
        "usable_for_training": "false",
        "risk": "critical; Commons Yunjin assertion conflicts with holding museum record (K'ossu/kesi technique)",
        "evidence": (
            "GRASSI Museum official collection record describes 'Drachenrobe' as silk worked in "
            "K'ossu technique and does not identify it as Nanjing Yunjin: "
            "https://www.sammlung.grassimak.de/detail/collection/56429fe3-ab10-422e-ab87-9f369355a8f4"
        ),
    }
}


def main() -> None:
    with PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    for row in rows:
        if row["object_id"] in LABEL_CONFLICTS:
            conflict = LABEL_CONFLICTS[row["object_id"]]
            row["class_label"] = conflict["class_label"]
            row["usable_for_training"] = conflict["usable_for_training"]
            row["text_watermark_exhibit_risk"] = conflict["risk"]
            marker = "Label conflict review: " + conflict["evidence"]
            if marker not in row["notes"]:
                row["notes"] = (row["notes"] + " " + marker).strip()
        if row["object_id"] in OVERRIDES:
            row["usable_for_training"], row["text_watermark_exhibit_risk"] = OVERRIDES[row["object_id"]]
            marker = "Manual contact-sheet review excluded the current image pending a clean crop."
            if marker not in row["notes"]:
                row["notes"] += f" {marker}"
    with PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    usable = Counter(row["class_label"] for row in rows if row["usable_for_training"] == "true")
    reusable = Counter(
        row["class_label"] for row in rows
        if row["class_label"] in {"nanjing_yunjin", "other_brocade"} and row["license"] != "unknown"
    )
    summary = {
        "retrieval_date": "2026-09-04",
        "candidate_rows": len(rows),
        "legally_reusable_yunjin_objects": reusable["nanjing_yunjin"],
        "immediately_usable_yunjin_objects": usable["nanjing_yunjin"],
        "legally_reusable_other_brocade_objects": reusable["other_brocade"],
        "immediately_usable_other_brocade_objects": usable["other_brocade"],
    }
    (ROOT / "docs" / "phase3_counts.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
