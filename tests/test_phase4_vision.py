from __future__ import annotations

import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.vision import analyze_image


class Phase4VisionTests(unittest.TestCase):
    def test_local_fallback_runs_without_api(self):
        image = Image.new("RGB", (160, 120), "#8f1838")
        draw = ImageDraw.Draw(image)
        draw.rectangle((20, 20, 60, 100), fill="#d5aa3a")
        draw.rectangle((100, 20, 140, 100), fill="#d5aa3a")
        result = analyze_image(image, provider="local")
        self.assertEqual(result.provider, "local_cv")
        self.assertTrue(result.observable_facts)
        self.assertIn("dominant_colors", result.raw_metrics)
        self.assertFalse(result.tentative_elements)
        self.assertTrue(any("不是分类概率" in line for line in result.limitations))


if __name__ == "__main__":
    unittest.main()
