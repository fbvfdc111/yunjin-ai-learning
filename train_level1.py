from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.datasets import MetadataImageDataset, OfficialMetadataImageDataset
from yunjin_ai.metadata import load_metadata
from yunjin_ai.models import build_resnet18, default_transforms
from yunjin_ai.training import assert_level1_ready


def read_split_ids(path: Path) -> dict[str, set[str]]:
    result = {"train": set(), "val": set(), "test": set()}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["split"] in result:
                result[row["split"]].add(row.get("object_id") or row.get("image_id", ""))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Level 1: Nanjing Yunjin vs other brocade.")
    parser.add_argument("--metadata", default=ROOT / "data/metadata/metadata.csv", type=Path)
    parser.add_argument("--schema", choices=["phase1", "official"], default="phase1")
    parser.add_argument("--raw-root", default=ROOT / "data/raw", type=Path)
    parser.add_argument("--splits", default=ROOT / "data/splits/splits.csv", type=Path)
    parser.add_argument("--output-dir", default=ROOT / "artifacts/level1", type=Path)
    parser.add_argument("--minimum-per-class", default=30, type=int)
    parser.add_argument("--epochs", default=10, type=int)
    parser.add_argument("--batch-size", default=16, type=int)
    parser.add_argument("--learning-rate", default=3e-4, type=float)
    args = parser.parse_args()

    if args.schema == "official":
        with args.metadata.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        rows = load_metadata(args.metadata)
    try:
        assert_level1_ready(rows, args.minimum_per_class)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    if not args.splits.is_file():
        print("Missing split file; run scripts/create_splits.py first.", file=sys.stderr)
        return 2

    import torch
    from torch import nn
    from torch.optim import AdamW
    from torch.utils.data import DataLoader

    split_ids = read_split_ids(args.splits)
    datasets = {}
    for split in ("train", "val", "test"):
        if args.schema == "official":
            dataset = OfficialMetadataImageDataset(
                args.metadata,
                ROOT,
                transform=default_transforms(train=split == "train"),
            )
            dataset.rows = [row for row in dataset.rows if row["object_id"] in split_ids[split]]
        else:
            dataset = MetadataImageDataset(
                args.metadata,
                args.raw_root,
                task="level1",
                transform=default_transforms(train=split == "train"),
            )
            dataset.rows = [row for row in dataset.rows if row["image_id"] in split_ids[split]]
        datasets[split] = dataset
    if any(len(datasets[name]) == 0 for name in datasets):
        print("Every split must contain samples. No training was started.", file=sys.stderr)
        return 2

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_resnet18(2).to(device)
    optimizer = AdamW(model.parameters(), lr=args.learning_rate)
    criterion = nn.CrossEntropyLoss()
    loaders = {
        split: DataLoader(dataset, batch_size=args.batch_size, shuffle=split == "train")
        for split, dataset in datasets.items()
    }

    history = []
    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        seen = 0
        for images, targets, _ in loaders["train"]:
            images, targets = images.to(device), targets.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)
            seen += images.size(0)
        history.append({"epoch": epoch + 1, "train_loss": running_loss / max(1, seen)})

    def evaluate(loader):
        model.eval()
        matrix = [[0, 0], [0, 0]]
        with torch.no_grad():
            for images, targets, _ in loader:
                predictions = model(images.to(device)).argmax(dim=1).cpu()
                for truth, predicted in zip(targets.tolist(), predictions.tolist()):
                    matrix[int(truth)][int(predicted)] += 1
        total = sum(sum(row) for row in matrix)
        accuracy = sum(matrix[i][i] for i in range(2)) / total if total else None
        per_class = {}
        for index, label in enumerate(datasets["train"].label_vocabulary):
            tp = matrix[index][index]
            fp = sum(matrix[row][index] for row in range(2) if row != index)
            fn = sum(matrix[index][col] for col in range(2) if col != index)
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            per_class[label] = {"precision": precision, "recall": recall, "f1": f1}
        macro_f1 = sum(item["f1"] for item in per_class.values()) / len(per_class)
        return {"accuracy": accuracy, "macro_f1": macro_f1, "per_class": per_class, "confusion_matrix": matrix}

    validation_metrics = evaluate(loaders["val"])
    test_metrics = evaluate(loaders["test"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"state_dict": model.state_dict(), "labels": datasets["train"].label_vocabulary},
        args.output_dir / "model.pt",
    )
    metrics = {"history": history, "validation": validation_metrics, "test": test_metrics}
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
