from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.models import build_resnet18, default_transforms


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Level 1 inference from a real checkpoint.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--checkpoint", default=ROOT / "artifacts/level1/model.pt", type=Path)
    args = parser.parse_args()
    if not args.checkpoint.is_file():
        print("Checkpoint missing: model status is 待训练/待验证.", file=sys.stderr)
        return 2

    import torch
    from PIL import Image

    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    labels = checkpoint["labels"]
    model = build_resnet18(len(labels), pretrained=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    tensor = default_transforms(train=False)(Image.open(args.image).convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        probabilities = model(tensor).softmax(dim=1)[0]
    result = {label: float(probabilities[index]) for index, label in enumerate(labels)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

