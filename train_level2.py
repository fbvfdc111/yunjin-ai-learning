from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.metadata import load_metadata
from yunjin_ai.training import assert_level2_ready


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and launch the extensible Level 2 multilabel route.")
    parser.add_argument("--metadata", default=ROOT / "data/metadata/metadata.csv", type=Path)
    parser.add_argument("--minimum-groups-per-label", default=20, type=int)
    args = parser.parse_args()
    rows = load_metadata(args.metadata)
    try:
        eligible = assert_level2_ready(rows, args.minimum_groups_per_label)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    print("Level 2 data gate passed for:", eligible)
    print("Training implementation uses MetadataImageDataset(task='level2'), a sigmoid head, and BCEWithLogitsLoss.")
    print("This repository intentionally does not train until a group-aware split is approved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

