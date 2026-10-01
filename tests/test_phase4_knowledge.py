from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import load_knowledge, load_sources, search_knowledge, validate_knowledge


class Phase4KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT / "data" / "knowledge"
        cls.sources = load_sources(directory / "sources.json")
        cls.items = load_knowledge(directory / "knowledge_base.json")

    def test_every_fact_has_valid_source(self):
        self.assertEqual(validate_knowledge(self.items, self.sources), [])
        self.assertTrue(all(item.source_ids for item in self.items))

    def test_required_topics_are_retrievable(self):
        for query in ["南京云锦", "制作流程", "妆花", "织金", "库缎", "龙纹", "凤纹", "莲", "寿", "八宝"]:
            with self.subTest(query=query):
                self.assertTrue(search_knowledge(query, self.items), query)

    def test_grounded_answer_and_refusal(self):
        answer = answer_from_knowledge("妆花是什么？", self.items, self.sources)
        self.assertEqual(answer.status, "基于本地知识库")
        self.assertTrue(answer.source_ids)
        refusal = answer_from_knowledge("请评价今天南京天气", self.items, self.sources)
        self.assertEqual(refusal.status, "证据不足")
        self.assertFalse(refusal.source_ids)


if __name__ == "__main__":
    unittest.main()
