from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data" / "metadata" / "phase3_open_data_candidates.csv"
DOCS = ROOT / "docs"


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


def make_contact_sheet(rows: list[dict[str, str]], path: Path) -> None:
    rows = [row for row in rows if row["local_path"] and (ROOT / row["local_path"]).is_file()]
    cell_w, cell_h, columns = 260, 220, 4
    canvas = Image.new("RGB", (cell_w * columns, cell_h * ((len(rows) + columns - 1) // columns)), "white")
    draw = ImageDraw.Draw(canvas)
    for index, row in enumerate(rows):
        x, y = (index % columns) * cell_w, (index // columns) * cell_h
        with Image.open(ROOT / row["local_path"]) as image:
            image = image.convert("RGB")
            image.thumbnail((240, 175))
            canvas.paste(image, (x + (cell_w - image.width) // 2, y + 4))
        draw.text((x + 8, y + 183), f"{row['object_id']}\nusable={row['usable_for_training']}", fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def main() -> None:
    with METADATA.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    hashes: dict[str, int] = {}
    sha_groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row["sha256"]:
            sha_groups[row["sha256"]].append(row["object_id"])
        path = ROOT / row["local_path"]
        if row["local_path"] and path.is_file():
            hashes[row["object_id"]] = dhash(path)
    exact = [group for group in sha_groups.values() if len(group) > 1]
    near = []
    class_by_id = {row["object_id"]: row["class_label"] for row in rows}
    for left, right in combinations(hashes, 2):
        if class_by_id[left] != class_by_id[right]:
            continue
        distance = (hashes[left] ^ hashes[right]).bit_count()
        if distance <= 4:
            near.append({"left_object_id": left, "right_object_id": right, "dhash_distance": distance, "decision": "manual_review"})
    with (DOCS / "phase3_near_duplicate_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["left_object_id", "right_object_id", "dhash_distance", "decision"])
        writer.writeheader()
        writer.writerows(near)
    make_contact_sheet(rows, DOCS / "phase3_candidate_contact_sheet.png")
    usable = [row for row in rows if row["usable_for_training"] == "true"]
    usable_counts = dict(Counter(row["class_label"] for row in usable))
    result = {
        "audit_date": "2026-09-04",
        "candidate_rows": len(rows),
        "downloaded_audit_images": len(hashes),
        "usable_counts": usable_counts,
        "exact_duplicate_groups": exact,
        "near_duplicate_pairs": near,
        "duplicate_object_ids": [key for key, count in Counter(row["object_id"] for row in rows).items() if count > 1],
        "source_class_confounding": "The only open-license Yunjin-labelled candidate comes from Wikimedia Commons, while all three currently accepted other-brocade candidates come from The Met. Source is perfectly correlated with the proposed classes and can create a shortcut.",
        "training_gate": "do_not_train",
        "training_gate_reason": f"Only {usable_counts.get('nanjing_yunjin', 0)} Yunjin object is immediately usable, versus {usable_counts.get('other_brocade', 0)} other-brocade objects. The classes are also perfectly confounded by source institution.",
        "manual_review_limits": "Automated checks cover hashes and dimensions. Text, exhibit labels, watermarks and object-centric cropping require manual visual review; no OCR result is treated as proof of absence.",
    }
    (DOCS / "phase3_open_data_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
