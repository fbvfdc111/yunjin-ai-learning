from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pdfplumber
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data" / "official"
PDF_DIR = OFFICIAL / "evidence" / "source_pdfs"
PAGE_EVIDENCE_DIR = OFFICIAL / "evidence" / "catalog_pages"
MODEL_DIR = OFFICIAL / "model_images_candidates"
METADATA_DIR = ROOT / "data" / "metadata"
COLLECTED_ON = "2026-09-03"
COPYRIGHT_TEXT = (
    "Copyright1990-2024 www.71nc.com 版权所有：南京云锦研究所有限公司 "
    "苏ICP备12069451号"
)

YUNJIN_URL = (
    "http://www.yjmuseum.com/cpwx/"
    "%E5%8D%97%E4%BA%AC%E5%8E%86%E4%BB%A3%E4%BA%91%E9%94%A6%E5%8D%9A%E7%89%A9%E9%A6%86%E8%97%8F%E5%93%81%E5%AE%A4%EF%BC%9A"
    "%E4%BA%91%E9%94%A6%E7%B1%BB1%EF%BC%9A540%E5%A5%97.pdf"
)
NON_YUNJIN_URL = (
    "http://www.yjmuseum.com/cpwx/"
    "%E5%8D%97%E4%BA%AC%E5%8E%86%E4%BB%A3%E4%BA%91%E9%94%A6%E5%8D%9A%E7%89%A9%E9%A6%86%E8%97%8F%E5%93%81%E5%AE%A4%EF%BC%9A"
    "%E9%9D%9E%E4%BA%91%E9%94%A6%E7%B1%BB1%EF%BC%9A1028%E5%A5%97.pdf"
)

WEB_POSITIVE = [
    ("web_fine_art_001", "万寿中华屏风", "20240305014129.png"),
    ("web_fine_art_002", "南都繁绘图", "20240305014138.png"),
    ("web_fine_art_003", "三世佛", "20240305014149.png"),
    ("web_fine_art_004", "蒙娜丽莎", "20240305014158.png"),
    ("web_fine_art_005", "鸿雁", "20240308121701.png"),
    ("web_fine_art_006", "松龄鹤寿（金宝地）", "20240308121739.jpg"),
    ("web_fine_art_007", "从北京到巴黎-中法交流特别荣誉《海屋朝鹤》", "20241012023355.png"),
]
WEB_NEGATIVE = [
    ("web_world_001", "泰国锦片01", "Top_20240205044032.png"),
    ("web_world_002", "泰国锦片02", "Top_20240205044145.png"),
    ("web_world_003", "泰国锦片03", "Top_20240205044303.png"),
    ("web_world_004", "泰国锦片04", "Top_20240205044416.png"),
    ("web_world_005", "绿地埃及织锦靠垫", "Top_20240205044649.png"),
    ("web_world_006", "黑地埃及织锦靠垫", "Top_20240205044746.png"),
    ("web_world_007", "埃及织锦骆驼挂毯", "Top_20240205044906.png"),
    ("web_world_008", "土耳其人物织锦靠垫", "Top_20240205045021.png"),
]

CRAFT_TERMS = ["妆花", "织金", "缂丝", "织彩", "花罗", "库缎"]
PATTERN_TERMS = ["缠枝牡丹", "牡丹", "八宝", "宝灯", "灵芝", "龙", "凤", "鹤", "寿", "莲"]


def clean(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip()


def as_int(value: object) -> int | None:
    match = re.search(r"\d+", clean(value))
    return int(match.group()) if match else None


def parse_catalog(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables():
                for row_position, row in enumerate(table or []):
                    if not row or len(row) < 3:
                        continue
                    sequence = as_int(row[0])
                    catalog_number = clean(row[1])
                    name = clean(row[2])
                    if sequence is None or not catalog_number or not name or name == "名称":
                        continue
                    records.append(
                        {
                            "sequence": sequence,
                            "catalog_number": catalog_number,
                            "official_name": name,
                            "page_number": page_number,
                            "row_position": row_position,
                            "raw_row": " | ".join(clean(cell) for cell in row),
                        }
                    )
    deduped = {str(record["catalog_number"]): record for record in records}
    return sorted(deduped.values(), key=lambda item: int(item["sequence"]))


def locate_pdftoppm() -> str | None:
    direct = shutil.which("pdftoppm")
    if direct:
        return direct
    bundled = Path(
        r"C:\Users\cyj\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"
    )
    return str(bundled) if bundled.exists() else None


def render_evidence_pages(pdf_path: Path, pages: set[int], prefix: str) -> None:
    tool = locate_pdftoppm()
    if not tool:
        return
    PAGE_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    for page_number in sorted(pages):
        target = PAGE_EVIDENCE_DIR / f"{prefix}_page_{page_number:03d}"
        output = target.with_suffix(".png")
        if output.exists():
            continue
        subprocess.run(
            [tool, "-png", "-r", "150", "-f", str(page_number), "-l", str(page_number), "-singlefile", str(pdf_path), str(target)],
            check=True,
            capture_output=True,
        )


def extract_page_images(
    pdf_path: Path,
    records: list[dict[str, object]],
    all_records: list[dict[str, object]],
    class_name: str,
    prefix: str,
) -> None:
    reader = PdfReader(pdf_path)
    by_page: dict[int, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        by_page[int(record["page_number"])].append(record)
    destination = MODEL_DIR / class_name
    destination.mkdir(parents=True, exist_ok=True)
    for page_number, selected in by_page.items():
        all_images = list(reader.pages[page_number - 1].images)
        page_rows = sorted(
            [r for r in all_records if int(r["page_number"]) == page_number],
            key=lambda item: int(item["sequence"]),
        )
        if len(all_images) != len(page_rows):
            for record in selected:
                record["image_note"] = f"该页表格对象数{len(page_rows)}与内嵌图片数{len(all_images)}不一致，未自动配对"
            continue
        image_by_catalog = {
            str(row["catalog_number"]): image for row, image in zip(page_rows, all_images, strict=True)
        }
        for record in selected:
            embedded = image_by_catalog.get(str(record["catalog_number"]))
            if not embedded:
                continue
            target = destination / f"{prefix}_{record['catalog_number']}.png"
            try:
                embedded.image.convert("RGB").save(target, format="PNG")
            except Exception as exc:  # keep evidence even when a thumbnail cannot be decoded
                record["image_note"] = f"内嵌图提取失败：{exc}"
                continue
            record["model_image_file"] = target.relative_to(ROOT).as_posix()


def image_facts(relative_path: str) -> tuple[int, int, bool, str]:
    if not relative_path:
        return 0, 0, False, ""
    path = ROOT / relative_path
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return width, height, True, digest
    except Exception:
        return 0, 0, False, ""


def labels_from_name(name: str) -> tuple[str, str]:
    crafts = [term for term in CRAFT_TERMS if term in name]
    patterns = [term for term in PATTERN_TERMS if term in name]
    return ";".join(crafts), ";".join(patterns)


def catalog_row(record: dict[str, object], *, level1: str, pdf_url: str, pdf_title: str, prefix: str) -> dict[str, str]:
    name = str(record["official_name"])
    model_path = str(record.get("model_image_file", ""))
    width, height, valid, digest = image_facts(model_path)
    craft, pattern = labels_from_name(name)
    positive = level1 == "nanjing_yunjin"
    category_text = (
        "南京历代云锦博物馆藏品室：云锦类1：540套；PDF清册标题/页眉为“南京云锦 博物馆藏品清册（云锦类）”"
        if positive
        else "南京历代云锦博物馆藏品室：非云锦类1：1028套；本对象官网原始名称明确含“锦”"
    )
    evidence_file = f"data/official/evidence/catalog_pages/{prefix}_page_{int(record['page_number']):03d}.png"
    resolution_pass = valid and min(width, height) >= 224
    return {
        "object_id": f"official_{prefix}_{record['catalog_number']}",
        "source_group_id": f"official_{prefix}_{record['catalog_number']}",
        "source_type": "official_catalog_pdf",
        "source_catalog": pdf_title,
        "source_url": pdf_url,
        "page_url": f"{pdf_url}#page={record['page_number']}",
        "page_title": pdf_title,
        "official_name": name,
        "catalog_number": str(record["catalog_number"]),
        "official_category_text": category_text,
        "category_evidence_text": f"{category_text}；清册原始行：{record['raw_row']}",
        "collection_date": COLLECTED_ON,
        "is_explicit_nanjing_yunjin": "true" if positive else "false",
        "level1_label": level1,
        "level1_confidence": "high",
        "craft_name": craft,
        "pattern_name": pattern,
        "image_filename": Path(model_path).name if model_path else "",
        "evidence_file": evidence_file,
        "model_image_file": model_path,
        "authorization_status": "unknown",
        "website_copyright_statement": COPYRIGHT_TEXT,
        "width": str(width),
        "height": str(height),
        "image_valid": str(valid).lower(),
        "resolution_pass": str(resolution_pass).lower(),
        "label_leakage_risk": "low_for_extracted_thumbnail;manual_review_required",
        "label_evidence_available": "true",
        "usable_for_training": "false",
        "usage_scope": "reference",
        "sha256": digest,
        "notes": str(record.get("image_note", "")) or "官网清册提供可靠类别证据；授权未确认，因此不进入训练集。",
    }


def web_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    groups = [
        (
            WEB_POSITIVE,
            "nanjing_yunjin",
            "data/official/web_images/fine_art",
            "data/official/evidence/webpage_screenshots/fine_art.png",
            "http://www.yjmuseum.com/ysjp/ysjp.html",
            "艺术精品-国礼典藏-南京云锦博物馆",
            "艺术精品栏目说明明确称南京云锦研究所出品的云锦艺术品，并逐项列出作品名。",
        ),
        (
            WEB_NEGATIVE,
            "other_brocade",
            "data/official/web_images/world_tapestry",
            "data/official/evidence/webpage_screenshots/world_tapestry.png",
            "http://www.yjmuseum.com/cpwx/detail2.html",
            "藏品文修-世界织锦-南京云锦博物馆",
            "“世界织锦”栏目逐项原名明确标注泰国锦、埃及织锦或土耳其织锦。",
        ),
    ]
    for items, level1, folder, evidence, url, title, proof in groups:
        for object_id, name, filename in items:
            relative = f"{folder}/{filename}"
            width, height, valid, digest = image_facts(relative)
            craft, pattern = labels_from_name(name)
            resolution_pass = valid and min(width, height) >= 224
            rows.append(
                {
                    "object_id": object_id,
                    "source_group_id": object_id,
                    "source_type": "official_webpage",
                    "source_catalog": "官网网页栏目",
                    "source_url": url,
                    "page_url": url,
                    "page_title": title,
                    "official_name": name,
                    "catalog_number": "",
                    "official_category_text": proof,
                    "category_evidence_text": f"{proof} 官网原始名称：{name}",
                    "collection_date": COLLECTED_ON,
                    "is_explicit_nanjing_yunjin": "true" if level1 == "nanjing_yunjin" else "false",
                    "level1_label": level1,
                    "level1_confidence": "high",
                    "craft_name": craft,
                    "pattern_name": pattern,
                    "image_filename": filename,
                    "evidence_file": evidence,
                    "model_image_file": relative,
                    "authorization_status": "unknown",
                    "website_copyright_statement": COPYRIGHT_TEXT,
                    "width": str(width),
                    "height": str(height),
                    "image_valid": str(valid).lower(),
                    "resolution_pass": str(resolution_pass).lower(),
                    "label_leakage_risk": (
                        "low_content_inscription_present;manual_review_required"
                        if level1 == "nanjing_yunjin"
                        else "medium_source_card_or_inventory_mark_visible;manual_review_required"
                    ),
                    "label_evidence_available": "true",
                    "usable_for_training": "false",
                    "usage_scope": "reference",
                    "sha256": digest,
                    "notes": "主体图与网页证据分离保存；授权未确认，因此不进入训练集。",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_level2(rows: list[dict[str, str]]) -> None:
    selected = [row for row in rows if row["level1_label"] == "nanjing_yunjin"]
    output: list[dict[str, str]] = []
    for label_type, field in (("craft", "craft_name"), ("pattern", "pattern_name")):
        buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in selected:
            for label in filter(None, row[field].split(";")):
                buckets[label].append(row)
        for label, matches in sorted(buckets.items()):
            output.append(
                {
                    "label_name": label,
                    "label_type": label_type,
                    "source_url": matches[0]["page_url"],
                    "official_text": "；".join(row["official_name"] for row in matches[:5]),
                    "object_count": str(len({row["object_id"] for row in matches})),
                    "confidence": "high_name_text_match",
                    "example_object_ids": ";".join(row["object_id"] for row in matches[:5]),
                    "training_decision": "待补足每标签独立对象并进行专家复核，不启动Level 2训练",
                }
            )
    write_csv(METADATA_DIR / "official_level2_candidate_labels.csv", output)


def write_stats(rows: list[dict[str, str]]) -> None:
    counter = Counter(row["level1_label"] for row in rows)
    label_evidence = sum(row["label_evidence_available"] == "true" for row in rows)
    valid = sum(row["image_valid"] == "true" for row in rows)
    resolution = sum(row["resolution_pass"] == "true" for row in rows)
    direct = sum(row["usable_for_training"] == "true" for row in rows)
    stats = [
        {"metric": "confirmed_nanjing_yunjin_objects", "count": str(counter["nanjing_yunjin"]), "definition": "官网清册类别或明确栏目文字证明的独立对象"},
        {"metric": "confirmed_other_brocade_objects", "count": str(counter["other_brocade"]), "definition": "官网非云锦类且原名含锦，或世界织锦明确命名的独立对象"},
        {"metric": "unknown_objects", "count": str(counter["unknown"]), "definition": "本轮正式metadata不纳入证据不足对象"},
        {"metric": "objects_with_label_evidence", "count": str(label_evidence), "definition": "存在可追溯官网类别证据"},
        {"metric": "decodable_model_images", "count": str(valid), "definition": "候选主体图可被Pillow解码"},
        {"metric": "images_min_dimension_ge_224", "count": str(resolution), "definition": "候选主体图最短边至少224像素"},
        {"metric": "direct_training_eligible", "count": str(direct), "definition": "同时满足标签、质量、授权与泄漏要求"},
    ]
    write_csv(ROOT / "docs" / "phase2_official_stats.csv", stats)


def main() -> None:
    y_path = PDF_DIR / "official_yunjin_catalog_1.pdf"
    n_path = PDF_DIR / "official_non_yunjin_catalog_1.pdf"
    y_all = parse_catalog(y_path)
    n_all = parse_catalog(n_path)
    y_selected = y_all[:40]
    n_selected = [record for record in n_all if "锦" in str(record["official_name"])][:40]
    if len(y_selected) < 40 or len(n_selected) < 40:
        raise RuntimeError(f"清册对象不足：云锦{len(y_selected)}，其他织锦{len(n_selected)}")

    render_evidence_pages(y_path, {int(r["page_number"]) for r in y_selected}, "yunjin")
    render_evidence_pages(n_path, {int(r["page_number"]) for r in n_selected}, "non_yunjin")
    extract_page_images(y_path, y_selected, y_all, "nanjing_yunjin", "yunjin")
    extract_page_images(n_path, n_selected, n_all, "other_brocade", "other_brocade")

    rows = [
        catalog_row(
            record,
            level1="nanjing_yunjin",
            pdf_url=YUNJIN_URL,
            pdf_title="南京历代云锦博物馆藏品室：云锦类1：540套",
            prefix="yunjin",
        )
        for record in y_selected
    ]
    rows.extend(
        catalog_row(
            record,
            level1="other_brocade",
            pdf_url=NON_YUNJIN_URL,
            pdf_title="南京历代云锦博物馆藏品室：非云锦类1：1028套",
            prefix="non_yunjin",
        )
        for record in n_selected
    )
    rows.extend(web_rows())
    write_csv(METADATA_DIR / "official_metadata.csv", rows)
    write_level2(rows)
    write_stats(rows)
    print(f"official objects={len(rows)} yunjin={sum(r['level1_label']=='nanjing_yunjin' for r in rows)} other={sum(r['level1_label']=='other_brocade' for r in rows)}")


if __name__ == "__main__":
    main()
