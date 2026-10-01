from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable

from PIL import Image

from .metadata import as_bool, load_metadata, split_labels


class MetadataImageDataset:
    """Torch-compatible dataset whose samples are selected only by metadata."""

    def __init__(
        self,
        metadata_csv: str | Path,
        image_root: str | Path,
        task: str = "level1",
        transform: Callable | None = None,
        include_nontrainable: bool = False,
        label_vocabulary: list[str] | None = None,
    ) -> None:
        if task not in {"level1", "level2"}:
            raise ValueError("task must be level1 or level2")
        rows = load_metadata(metadata_csv)
        self.rows = [
            row for row in rows if include_nontrainable or as_bool(row["usable_for_training"])
        ]
        self.image_root = Path(image_root)
        self.task = task
        self.transform = transform
        if task == "level1":
            self.label_vocabulary = ["nanjing_yunjin", "other_brocade"]
        else:
            discovered = sorted(
                {label for row in self.rows for label in split_labels(row["pattern_labels_supported_by_name"])}
            )
            self.label_vocabulary = label_vocabulary or discovered
        self.label_to_index = {label: index for index, label in enumerate(self.label_vocabulary)}

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        path = self.image_root / row["source_batch"] / row["raw_filename"]
        image = Image.open(path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        if self.task == "level1":
            label = row["level1_label"]
            if label not in self.label_to_index:
                raise ValueError(f"{row['image_id']} has no confirmed Level 1 label")
            target = self.label_to_index[label]
        else:
            try:
                import torch
            except ImportError as exc:
                raise RuntimeError("Level 2 tensor targets require torch") from exc
            target = torch.zeros(len(self.label_vocabulary), dtype=torch.float32)
            for label in split_labels(row["pattern_labels_supported_by_name"]):
                if label in self.label_to_index:
                    target[self.label_to_index[label]] = 1.0
        return image, target, row


class OfficialMetadataImageDataset:
    """Torch-compatible loader for object-level official metadata."""

    label_vocabulary = ["nanjing_yunjin", "other_brocade"]

    def __init__(self, metadata_csv: str | Path, project_root: str | Path, transform: Callable | None = None) -> None:
        with Path(metadata_csv).open("r", encoding="utf-8-sig", newline="") as handle:
            self.rows = [row for row in csv.DictReader(handle) if row["usable_for_training"] == "true"]
        self.project_root = Path(project_root)
        self.transform = transform
        self.label_to_index = {label: index for index, label in enumerate(self.label_vocabulary)}

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        image = Image.open(self.project_root / row["model_image_file"]).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, self.label_to_index[row["level1_label"]], row
