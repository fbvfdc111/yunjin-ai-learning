from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import AI_REFERENCE_STATUS, ASSISTANT_INFO_STATUS, answer_hybrid
from yunjin_ai.knowledge import load_knowledge, load_sources
from yunjin_ai.vision import analyze_locally


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(
            {"choices": [{"message": {"content": "这是一条需要进一步核验的云锦学习参考。"}}]},
            ensure_ascii=False,
        ).encode("utf-8")


class HybridGuideAndCropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        knowledge_dir = ROOT / "data" / "knowledge"
        cls.sources = load_sources(knowledge_dir / "sources.json")
        cls.items = load_knowledge(knowledge_dir / "knowledge_base.json")

    def test_hybrid_uses_marked_ai_reference_only_for_uncovered_yunjin_question(self):
        env = {
            "DOTS_API_KEY": "test-key",
            "DOTS_BASE_URL": "https://example.test",
            "DOTS_TEXT_MODEL": "test-model",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "yunjin_ai.guide.urlopen", return_value=_FakeResponse()
        ):
            answer = answer_hybrid(
                "南京云锦在国外有哪些当代展览案例？",
                self.items,
                self.sources,
            )
        self.assertEqual(answer.status, AI_REFERENCE_STATUS)
        self.assertIn("进一步核验", answer.answer)
        self.assertFalse(answer.source_ids)
        self.assertFalse(answer.claims)

    def test_hybrid_does_not_use_ai_for_out_of_domain_question(self):
        with patch.dict(os.environ, {"DOTS_API_KEY": "test-key"}, clear=False), patch(
            "yunjin_ai.guide.urlopen"
        ) as mocked_urlopen:
            answer = answer_hybrid("今天南京天气怎么样？", self.items, self.sources)
        self.assertEqual(answer.status, "证据不足")
        mocked_urlopen.assert_not_called()

    def test_identity_question_is_answered_without_spending_api_call(self):
        with patch.dict(os.environ, {"DOTS_API_KEY": "test-key"}, clear=False), patch(
            "yunjin_ai.guide.urlopen"
        ) as mocked_urlopen:
            answer = answer_hybrid("你是谁", self.items, self.sources)
        self.assertEqual(answer.status, ASSISTANT_INFO_STATUS)
        self.assertIn("南京云锦文化 AI 助手", answer.answer)
        mocked_urlopen.assert_not_called()

    def test_large_light_screenshot_border_is_cropped_before_local_analysis(self):
        image = Image.new("RGB", (900, 1200), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((110, 120, 790, 650), fill=(145, 34, 48))
        draw.ellipse((260, 250, 640, 570), fill=(201, 163, 67))

        observation = analyze_locally(image)

        self.assertTrue(observation.raw_metrics["auto_crop_applied"])
        self.assertLess(observation.raw_metrics["analysis_height"], 800)
        self.assertNotEqual(observation.raw_metrics["dominant_colors"][0]["name"], "白色/浅色")

    def test_full_frame_photo_is_not_cropped(self):
        image = Image.new("RGB", (640, 480), (120, 42, 52))
        observation = analyze_locally(image)
        self.assertFalse(observation.raw_metrics["auto_crop_applied"])
        self.assertEqual(observation.raw_metrics["analysis_width"], 640)
        self.assertEqual(observation.raw_metrics["analysis_height"], 480)


if __name__ == "__main__":
    unittest.main()
