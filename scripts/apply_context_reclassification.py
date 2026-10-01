"""Apply the user-confirmed collection context without converting it into blanket labels.

This migration is intentionally explicit and auditable. It separates the scope in
which an asset was collected from the evidence required for a Level 1 label.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data/metadata/metadata.csv"

POSITIVE_EVIDENCE = {
    "b2_001": "用户确认的南京云锦项目采集背景 + 标题中的“织金缎、妆花”",
    "b2_003": "用户确认的南京云锦项目采集背景 + 标题中的“织金、妆花”",
    "b2_004": "用户确认的南京云锦项目采集背景 + 标题中的“妆花缎”",
    "b2_007": "用户确认的南京云锦项目采集背景 + 标题中的“织金、妆花缎”",
    "b2_011": "用户确认的南京云锦项目采集背景 + 标题中的“织金、妆花”",
}

OTHER_EVIDENCE = {
    "b2_012": "截图标题明确写有“泰国锦片”",
    "b2_013": "截图标题明确写有“泰国锦片”",
    "b2_014": "截图标题明确写有“泰国锦片”",
    "b2_015": "截图标题明确写有“埃及织锦”",
    "b2_016": "截图标题明确写有“埃及织锦”",
    "b2_017": "截图标题明确写有“埃及织锦”",
    "b2_018": "截图标题明确写有“土耳其人物织锦”",
}

ADDITIONAL_FIELDS = [
    "collection_scope",
    "classification_evidence_source",
    "level1_confidence",
    "label_evidence_available",
    "label_leakage_risk",
]


def main() -> None:
    with METADATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for field in ADDITIONAL_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)

    for row in rows:
        image_id = row["image_id"]
        row["collection_scope"] = "nanjing_yunjin_project_related_materials"
        row["label_leakage_risk"] = "high"
        row["usable_for_training"] = "false"
        row["usage_scope"] = "reference"
        if image_id in POSITIVE_EVIDENCE:
            row["level1_label"] = "nanjing_yunjin"
            row["classification_evidence_source"] = POSITIVE_EVIDENCE[image_id]
            row["level1_confidence"] = "medium"
            row["label_evidence_available"] = "true"
            row["notes"] = (
                "采集背景与标题中的云锦工艺语义共同支持南京云锦正类；"
                "截图含类别/工艺文字且来源授权未确认，不可直接作为最终视觉训练样本"
            )
        elif image_id in OTHER_EVIDENCE:
            row["level1_label"] = "other_brocade"
            row["classification_evidence_source"] = OTHER_EVIDENCE[image_id]
            row["level1_confidence"] = "high"
            row["label_evidence_available"] = "true"
            row["notes"] = (
                "标题明确为其他国家/地区织锦；南京云锦项目采集背景不覆盖该直接证据；"
                "截图含类别文字且来源授权未确认，不可直接训练"
            )
        else:
            row["level1_label"] = "unknown"
            row["classification_evidence_source"] = "用户确认的南京云锦项目相关素材采集背景；缺少足以确定Level 1类别的直接或组合证据"
            row["level1_confidence"] = "insufficient"
            row["label_evidence_available"] = "false"
            suffix = "采集范围只证明项目相关性，不自动等同于南京云锦监督正类"
            existing_notes = row.get("notes") or ""
            if suffix not in existing_notes:
                row["notes"] = f"{existing_notes}；{suffix}".lstrip("；")

    with METADATA.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
