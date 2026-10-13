from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.digital_twin import STAGE_IDS
from yunjin_ai.digital_twin_3d import render_process_twin_3d
from yunjin_ai.digital_twin_simulation import SIMULATION_STAGE_SECONDS, simulation_sample
from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import load_knowledge, load_sources, search_answerable_knowledge


class Phase67QaAndLoomSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        knowledge_dir = ROOT / "data" / "knowledge"
        cls.sources = load_sources(knowledge_dir / "sources.json")
        cls.items = load_knowledge(knowledge_dir / "knowledge_base.json")

    def test_variety_intent_returns_variety_evidence_not_overview(self):
        for question in ("南京云锦有什么品种？", "云锦有哪些品种？", "南京云锦分为哪几类？"):
            with self.subTest(question=question):
                hits = search_answerable_knowledge(question, self.items)
                self.assertTrue(hits)
                self.assertEqual(hits[0].item.id, "KB007")
                self.assertNotIn("KB001", {hit.item.id for hit in hits})
                answer = answer_from_knowledge(question, self.items, self.sources)
                self.assertIn("织金", answer.answer)
                self.assertIn("妆花", answer.answer)

    def test_supported_topics_accept_natural_paraphrases(self):
        cases = {
            "南京云锦的制作工艺": "KB003",
            "云锦是怎么制作的？": "KB003",
            "南京云锦有哪些工序？": "KB003",
            "织机上面拉线的人做什么？": "KB004",
            "下面的织手如何操作？": "KB004",
            "云锦为什么需要手工织造？": "KB004",
            "南京云锦使用什么材料？": "KB005",
            "云锦过去有什么用途？": "KB006",
            "南京云锦有哪些常见纹样？": "KB010",
            "挑花结本有什么用？": "KB019",
        }
        for question, expected_id in cases.items():
            with self.subTest(question=question):
                hits = search_answerable_knowledge(question, self.items)
                self.assertTrue(hits, question)
                self.assertEqual(hits[0].item.id, expected_id)
                answer = answer_from_knowledge(question, self.items, self.sources)
                self.assertNotEqual(answer.status, "证据不足")

    def test_cloth_growth_uses_same_pick_timeline_as_people_and_mechanisms(self):
        sample = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 1.0)
        html = render_process_twin_3d(sample, exhibition=True)
        self.assertIn("exhibitionStartCycleIndex", html)
        self.assertIn("completedSessionPicks", html)
        self.assertIn("currentPickFormation", html)
        self.assertIn("timeline.phase < .79", html)
        self.assertIn("timeline.phase < .91", html)
        self.assertNotIn("(elapsed - .6) / 15.5", html)


if __name__ == "__main__":
    unittest.main()
