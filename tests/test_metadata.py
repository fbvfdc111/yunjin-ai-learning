from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.metadata import load_metadata, validate_metadata


class MetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_metadata(ROOT / "data/metadata/metadata.csv")

    def test_inventory_and_files(self):
        self.assertEqual(len(self.rows), 40)
        self.assertEqual(validate_metadata(self.rows, ROOT / "data/raw"), [])

    def test_truthful_level1_counts(self):
        counts = Counter(row["level1_label"] for row in self.rows)
        self.assertEqual(counts["nanjing_yunjin"], 5)
        self.assertEqual(counts["other_brocade"], 7)
        self.assertEqual(counts["unknown"], 28)
        self.assertEqual(sum(row["label_evidence_available"] == "true" for row in self.rows), 12)
        self.assertEqual(sum(row["usable_for_training"] == "true" for row in self.rows), 0)

    def test_source_group_is_preserved_for_record_series(self):
        groups = {row["source_group_id"] for row in self.rows if row["image_id"] in {"b2_030", "b2_031", "b2_032"}}
        self.assertEqual(groups, {"YAABB-00501"})


if __name__ == "__main__":
    unittest.main()
