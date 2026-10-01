from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.metadata import as_bool, load_metadata, validate_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Create normalized image copies from metadata-selected rows.")
    parser.add_argument("--metadata", default=ROOT / "data/metadata/metadata.csv", type=Path)
    parser.add_argument("--raw-root", default=ROOT / "data/raw", type=Path)
    parser.add_argument("--output-root", default=ROOT / "data/processed", type=Path)
    parser.add_argument("--size", default=512, type=int)
    parser.add_argument("--include-nontrainable", action="store_true")
    args = parser.parse_args()

    rows = load_metadata(args.metadata)
    errors = validate_metadata(rows, args.raw_root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    selected = [row for row in rows if args.include_nontrainable or as_bool(row["usable_for_training"])]
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest = args.output_root / "processed_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image_id", "output_file", "operation", "warning"])
        for row in selected:
            source = args.raw_root / row["source_batch"] / row["raw_filename"]
            output = args.output_root / f"{row['image_id']}.jpg"
            with Image.open(source) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image = ImageOps.pad(image, (args.size, args.size), color="white")
                image.save(output, quality=95)
            writer.writerow(
                [
                    row["image_id"],
                    output.name,
                    "EXIF transpose + RGB + letterbox only",
                    "Screenshot captions/tags are not removed; do not train unless manually clean-cropped and re-audited",
                ]
            )
    print(f"Prepared {len(selected)} images. Manifest: {manifest}")
    if not selected:
        print("No rows are approved for training; this is the expected evidence-first outcome.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

