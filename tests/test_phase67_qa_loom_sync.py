from __future__ import annotations

import json
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
from yunjin_ai.product import FOLLOWUP_QUESTIONS, GENERAL_CULTURE_QUESTIONS, cultural_followup_questions


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

    def test_short_topic_labels_route_to_supported_evidence(self):
        cases = {
            "纹样文化": "KB010",
            "南京云锦纹样": "KB010",
            "历史文化": "KB006",
            "南京云锦的历史": "KB006",
            "织造材料": "KB005",
            "制作工艺": "KB003",
            "品种分类": "KB007",
        }
        for question, expected_id in cases.items():
            with self.subTest(question=question):
                hits = search_answerable_knowledge(question, self.items)
                self.assertTrue(hits, question)
                self.assertEqual(hits[0].item.id, expected_id)
                answer = answer_from_knowledge(question, self.items, self.sources)
                self.assertNotEqual(answer.status, "证据不足")

    def test_new_yunjin_wording_gets_sourced_related_context(self):
        for question in ("为什么南京云锦这么珍贵？", "南京云锦和普通织锦有什么不同？"):
            with self.subTest(question=question):
                answer = answer_from_knowledge(question, self.items, self.sources)
                self.assertEqual(answer.status, "可信延伸回答")
                self.assertTrue(answer.claims)
                self.assertTrue(answer.source_ids)
                self.assertIn("最相关", answer.answer)

        unrelated = answer_from_knowledge("今天南京天气怎么样？", self.items, self.sources)
        self.assertEqual(unrelated.status, "证据不足")
        self.assertFalse(unrelated.claims)

    def test_followups_exclude_current_and_previous_questions(self):
        hits = search_answerable_knowledge("云锦有哪些品种？", self.items)
        questions = cultural_followup_questions(
            hits,
            exclude_questions=("云锦有哪些品种？", "妆花是什么？"),
        )
        self.assertEqual(len(questions), 3)
        self.assertNotIn("南京云锦有哪些主要品种？", questions)
        self.assertNotIn("妆花是什么？", questions)
        self.assertEqual(len(set(questions)), len(questions))

    def test_every_recommended_question_is_answerable(self):
        questions = list(GENERAL_CULTURE_QUESTIONS)
        for values in FOLLOWUP_QUESTIONS.values():
            questions.extend(values)
        for question in dict.fromkeys(questions):
            with self.subTest(question=question):
                answer = answer_from_knowledge(question, self.items, self.sources)
                self.assertNotEqual(answer.status, "证据不足")
                self.assertTrue(answer.claims)
                self.assertTrue(answer.source_ids)

    def test_fifty_core_questions_are_grounded_and_route_to_expected_topics(self):
        rows = json.loads(
            (ROOT / "data" / "knowledge" / "coverage_questions.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(rows), 50)
        for row in rows:
            with self.subTest(question=row["question"]):
                answer = answer_from_knowledge(row["question"], self.items, self.sources)
                hit_ids = {hit.item.id for hit in answer.hits}
                self.assertNotEqual(answer.status, "证据不足")
                self.assertTrue(hit_ids.intersection(row["expected_ids"]), (hit_ids, row["expected_ids"]))
                self.assertTrue(answer.claims)
                self.assertTrue(answer.source_ids)

    def test_cloth_growth_uses_same_pick_timeline_as_people_and_mechanisms(self):
        sample = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 1.0)
        html = render_process_twin_3d(sample, exhibition=True)
        self.assertIn("exhibitionStartCycleIndex", html)
        self.assertIn("completedSessionPicks", html)
        self.assertIn("currentPickFormation", html)
        self.assertIn("timeline.phase < .79", html)
        self.assertIn("timeline.phase < .91", html)
        self.assertNotIn("(elapsed - .6) / 15.5", html)

    def test_exhibition_scene_keeps_visuals_without_unused_payload_or_hidden_updates(self):
        sample = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 1.0)
        html = render_process_twin_3d(sample, exhibition=True)
        self.assertNotIn("data:model/gltf-binary;base64", html)
        self.assertLess(len(html.encode("utf-8")), 500_000)
        self.assertIn("pixelRatioCap", html)
        self.assertIn("targetFrameInterval", html)
        self.assertIn("if (document.hidden) return", html)
        self.assertIn("if (!state.exhibitionMode)", html)
        self.assertIn("textureRefreshThreshold", html)

    def test_mobile_home_and_loom_controls_are_responsive(self):
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("background-size:100% 100%,auto 100%", app_source)
        self.assertIn("background-repeat:no-repeat,no-repeat", app_source)
        self.assertIn("render_guide_turn(guide_history[-1])", app_source)
        self.assertIn("查看历史问答", app_source)
        self.assertIn('answer.status == "可信延伸回答"', app_source)
        self.assertIn("exclude_questions=asked_questions", app_source)
        self.assertIn("flex-wrap:nowrap!important", app_source)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", app_source)

        sample = simulation_sample(STAGE_IDS.index("weft_weaving") * SIMULATION_STAGE_SECONDS + 1.0)
        html = render_process_twin_3d(sample, exhibition=True)
        self.assertIn("yunjin-webgl-v37-mobile-fit-camera", html)
        self.assertIn("const activePointers = new Map()", html)
        self.assertIn("pinchDistance / nextDistance", html)
        self.assertIn("compactViewport ? 32 : 24", html)
        self.assertIn("滚轮/双指缩放", html)


if __name__ == "__main__":
    unittest.main()
