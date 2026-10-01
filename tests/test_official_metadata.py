from __future__ import annotations

import csv
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OfficialMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "data" / "metadata" / "official_metadata.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_object_counts_and_unique_ids(self) -> None:
        self.assertEqual(len(self.rows), 95)
        self.assertEqual(len({row["object_id"] for row in self.rows}), 95)
        counts = Counter(row["level1_label"] for row in self.rows)
        self.assertEqual(counts, {"nanjing_yunjin": 47, "other_brocade": 48})

    def test_all_evidence_and_images_exist(self) -> None:
        for row in self.rows:
            self.assertTrue(row["source_url"])
            self.assertTrue((ROOT / row["evidence_file"]).is_file(), row["object_id"])
            self.assertTrue((ROOT / row["model_image_file"]).is_file(), row["object_id"])
            self.assertEqual(row["label_evidence_available"], "true")

    def test_training_is_blocked(self) -> None:
        self.assertTrue(all(row["authorization_status"] == "unknown" for row in self.rows))
        self.assertTrue(all(row["usable_for_training"] == "false" for row in self.rows))
        audit = json.loads((ROOT / "docs" / "phase2_audit_results.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["training_gate"]["decision"], "do_not_train")
        self.assertEqual(audit["direct_training_eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()
