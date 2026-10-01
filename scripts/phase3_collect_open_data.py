from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "open_training_candidates"
META_DIR = ROOT / "data" / "metadata"
WORK_DIR = ROOT / "work" / "phase3_api_cache"
RETRIEVAL_DATE = "2026-09-04"
UA = "Codex-AIC-Yunjin-Research/1.0 (research metadata audit)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
MET_API = "https://collectionapi.metmuseum.org/public/collection/v1"
MET_LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
MET_POLICY_URL = "https://www.metmuseum.org/hubs/open-access"


def fetch_json(url: str, params: dict[str, object] | None = None, retries: int = 3) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=35) as response:
                return json.load(response)
        except Exception as exc:
            last_error = exc
            time.sleep(1.0 + attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def download(url: str, target: Path) -> bool:
    if target.exists() and target.stat().st_size > 0:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())
        return True
    except Exception:
        return False


def text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value or ""))).strip()


def file_facts(path: Path) -> tuple[str, str, str]:
    with Image.open(path) as image:
        width, height = image.size
        image.verify()
    return f"{width}x{height}", hashlib.sha256(path.read_bytes()).hexdigest(), f"{width}x{height}"


def commons_candidates() -> list[dict[str, str]]:
    payload = fetch_json(
        COMMONS_API,
        {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": "Category:Nanjing_brocade",
            "gcmtype": "file",
            "gcmlimit": 50,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "format": "json",
        },
    )
    selected = {
        "File:Drachenrobe-Qianlong.JPG": {
            "object_id": "commons_yunjin_qianlong_dragon_robe",
            "object_name": "Dragon robe of Chinese Emperor Qianlong",
            "label_evidence": "Wikimedia file description identifies the dragon robe; structured data states depicts Yunjin brocade; file is in Category:Nanjing brocade.",
            "usable": "true",
            "leakage": "low; isolated museum object photograph",
        },
        "File:Yunjin brocade of Bixie on CR400BF-AS-3269 (20260623105816).jpg": {
            "object_id": "commons_yunjin_bixie_train_installation",
            "object_name": "Yunjin brocade of Bixie on CR400BF-AS-3269",
            "label_evidence": "File title explicitly says Yunjin brocade of Bixie and the file is in Category:Nanjing brocade.",
            "usable": "false",
            "leakage": "high; train interior and installation context can become a source shortcut; crop/manual review required",
        },
    }
    rows: list[dict[str, str]] = []
    for page in sorted(payload.get("query", {}).get("pages", {}).values(), key=lambda item: item["title"]):
        info = page["imageinfo"][0]
        meta = info.get("extmetadata", {})
        title = page["title"]
        picked = selected.get(title)
        is_object_candidate = picked is not None
        local_path = ""
        digest = ""
        if is_object_candidate:
            suffix = Path(urllib.parse.urlsplit(info["url"]).path).suffix or ".jpg"
            target = DATA_DIR / "nanjing_yunjin" / f"{picked['object_id']}{suffix}"
            if download(info["url"], target):
                local_path = target.relative_to(ROOT).as_posix()
                digest = hashlib.sha256(target.read_bytes()).hexdigest()
        license_name = meta.get("LicenseShortName", {}).get("value", "unknown")
        license_url = meta.get("LicenseUrl", {}).get("value", "")
        author = text(meta.get("Artist", {}).get("value", ""))
        description = text(meta.get("ImageDescription", {}).get("value", ""))
        rows.append(
            {
                "image_id": f"commons_{page['pageid']}",
                "class_label": "nanjing_yunjin" if is_object_candidate else "unknown",
                "object_id": picked["object_id"] if picked else f"commons_nonobject_{page['pageid']}",
                "source_group_id": picked["object_id"] if picked else f"commons_nonobject_{page['pageid']}",
                "object_name": picked["object_name"] if picked else meta.get("ObjectName", {}).get("value", title.removeprefix("File:")),
                "source": "Wikimedia Commons",
                "original_url": info["descriptionurl"],
                "image_url": info["url"],
                "author_or_institution": author,
                "license": license_name,
                "license_url": license_url,
                "license_evidence": f"File page/API states {license_name}; attribution required={meta.get('AttributionRequired', {}).get('value', 'unknown')}",
                "label_evidence": picked["label_evidence"] if picked else f"Category page association only; description: {description}",
                "retrieval_date": RETRIEVAL_DATE,
                "resolution": f"{info['width']}x{info['height']}",
                "local_path": local_path,
                "sha256": digest,
                "usable_for_training": picked["usable"] if picked and license_name != "unknown" else "false",
                "usable_for_demo": "true" if picked and license_name != "unknown" else "false",
                "text_watermark_exhibit_risk": picked["leakage"] if picked else "not an independent textile object; excluded",
                "notes": "Openly licensed object candidate." if picked else "Openly licensed category file, but it is a loom/building/site image rather than an independent Yunjin textile object.",
            }
        )
    return rows


def met_candidates(limit: int = 12) -> list[dict[str, str]]:
    search = fetch_json(f"{MET_API}/search", {"hasImages": "true", "q": "brocade"})
    ids = search.get("objectIDs") or []
    records: list[dict] = []

    def get_one(object_id: int) -> dict | None:
        try:
            return fetch_json(f"{MET_API}/objects/{object_id}", retries=1)
        except Exception:
            return None

    # Fetch a bounded candidate window; retain only records whose own metadata says brocade.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(get_one, object_id): object_id for object_id in ids[:70]}
        for future in as_completed(futures):
            record = future.result()
            if not record:
                continue
            combined = " ".join(str(record.get(key, "")) for key in ("title", "objectName", "medium", "classification")).lower()
            if record.get("isPublicDomain") and record.get("primaryImage") and "brocad" in combined:
                records.append(record)
    records.sort(key=lambda record: int(record["objectID"]))
    records = records[:limit]
    rows: list[dict[str, str]] = []
    for record in records:
        object_id = f"met_{record['objectID']}"
        image_url = record.get("primaryImageSmall") or record["primaryImage"]
        target = DATA_DIR / "other_brocade" / f"{object_id}.jpg"
        downloaded = download(image_url, target)
        if downloaded:
            with Image.open(target) as image:
                width, height = image.size
                image.verify()
        else:
            width, height = 0, 0
        object_name = str(record.get("objectName", "")).lower()
        title = str(record.get("title", "")).lower()
        classification = str(record.get("classification", "")).lower()
        medium = str(record.get("medium", "")).lower()
        primary_brocade_object = (
            "brocade" in object_name
            or "brocade" in title
            or classification.startswith("textiles")
            or medium.startswith("silk brocade")
            or ("robe" in title and "brocade" in medium)
        )
        quality_pass = downloaded and min(width, height) >= 224
        rows.append(
            {
                "image_id": object_id,
                "class_label": "other_brocade",
                "object_id": object_id,
                "source_group_id": object_id,
                "object_name": record.get("title") or record.get("objectName") or object_id,
                "source": "The Metropolitan Museum of Art Open Access",
                "original_url": record.get("objectURL", ""),
                "image_url": record["primaryImage"],
                "author_or_institution": "The Metropolitan Museum of Art",
                "license": "CC0 / Public Domain",
                "license_url": MET_LICENSE_URL,
                "license_evidence": f"Object API isPublicDomain=true; The Met Open Access policy releases public-domain artwork images under CC0: {MET_POLICY_URL}",
                "label_evidence": f"Official Met record: title={record.get('title','')}; objectName={record.get('objectName','')}; medium={record.get('medium','')}; classification={record.get('classification','')}",
                "retrieval_date": RETRIEVAL_DATE,
                "resolution": f"{width}x{height}",
                "local_path": target.relative_to(ROOT).as_posix() if downloaded else "",
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest() if downloaded else "",
                "usable_for_training": "true" if primary_brocade_object and quality_pass else "false",
                "usable_for_demo": "true",
                "text_watermark_exhibit_risk": "low in API subject image; manual visual review still required",
                "notes": f"Independent Met object; accession {record.get('accessionNumber','')}; culture {record.get('culture','unknown') or 'unknown'}. Primary brocade object={primary_brocade_object}; resolution pass={quality_pass}; audit copy downloaded={downloaded}.",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    rows = commons_candidates() + met_candidates(12)
    write_csv(META_DIR / "phase3_open_data_candidates.csv", rows)
    license_rows = []
    seen = set()
    for row in rows:
        key = (row["source"], row["license"], row["license_url"])
        if key in seen:
            continue
        seen.add(key)
        license_rows.append(
            {
                "source": row["source"],
                "license": row["license"],
                "license_url": row["license_url"],
                "license_evidence": row["license_evidence"],
                "retrieval_date": RETRIEVAL_DATE,
                "training_interpretation": (
                    "Permits reuse subject to attribution/share-alike terms; retain file-level attribution."
                    if "BY-SA" in row["license"]
                    else "Public-domain image released for unrestricted reuse under The Met Open Access CC0 policy."
                    if row["source"].startswith("The Metropolitan")
                    else "Not counted without an object-level license and label."
                ),
            }
        )
    write_csv(META_DIR / "phase3_license_evidence.csv", license_rows)
    summary = {
        "retrieval_date": RETRIEVAL_DATE,
        "candidate_rows": len(rows),
        "legally_reusable_yunjin_objects": len({r["object_id"] for r in rows if r["class_label"] == "nanjing_yunjin" and r["license"] != "unknown"}),
        "immediately_usable_yunjin_objects": len({r["object_id"] for r in rows if r["class_label"] == "nanjing_yunjin" and r["usable_for_training"] == "true"}),
        "legally_reusable_other_brocade_objects": len({r["object_id"] for r in rows if r["class_label"] == "other_brocade" and r["license"] != "unknown"}),
        "immediately_usable_other_brocade_objects": len({r["object_id"] for r in rows if r["class_label"] == "other_brocade" and r["usable_for_training"] == "true"}),
    }
    (ROOT / "docs" / "phase3_counts.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
