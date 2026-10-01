from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import (
    load_knowledge,
    load_sources,
    search_visual_knowledge,
    validate_knowledge,
)
from yunjin_ai.product import apply_guide_handoff, cultural_followup_questions


class Phase5Round2RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        knowledge_dir = ROOT / "data" / "knowledge"
        cls.items = load_knowledge(knowledge_dir / "knowledge_base.json")
        cls.sources = load_sources(knowledge_dir / "sources.json")

    def test_bird_willow_scene_artifacts_do_not_return_kb015(self):
        keywords = [
            "燕子",
            "柳枝",
            "飞鸟",
            "工笔画",
            "花鸟画",
            "黄色背景",
            "绿色叶片",
            "边框",
            "标签",
            "编号",
        ]
        hits = search_visual_knowledge(keywords, [], self.items)
        self.assertEqual(hits, [])
        self.assertNotIn("KB015", {hit.item.id for hit in hits})

    def test_governance_items_never_fill_visual_culture_results(self):
        hits = search_visual_knowledge(["候选标签", "可信AI"], ["候选标签"], self.items)
        self.assertFalse(any(hit.item.knowledge_use == "governance/methodology" for hit in hits))

    def test_all_items_declare_valid_use_and_answer_scope(self):
        self.assertEqual(validate_knowledge(self.items, self.sources), [])
        self.assertGreaterEqual(len(self.items), 15)
        self.assertEqual(
            {item.knowledge_use for item in self.items},
            {"cultural_content", "process/history", "governance/methodology"},
        )

    def test_no_match_recommendations_stay_in_supported_culture_topics(self):
        questions = cultural_followup_questions(())
        self.assertIn("妆花是什么？", questions)
        self.assertIn("南京云锦有哪些主要品种？", questions)
        self.assertFalse(any("视觉线索" in question or "鉴定结论" in question for question in questions))

    def test_supported_questions_are_directly_answered_by_expected_evidence(self):
        cases = {
            "妆花是什么？": "KB008",
            "南京云锦有哪些主要品种？": "KB007",
            "云锦为什么需要手工织造？": "KB004",
            "八宝纹有什么文化寓意？": "KB013",
        }
        for question, expected_id in cases.items():
            with self.subTest(question=question):
                answer = answer_from_knowledge(question, self.items, self.sources)
                expected_status = "一般传统文化背景" if expected_id == "KB013" else "基于本地知识库"
                self.assertEqual(answer.status, expected_status)
                self.assertEqual([hit.item.id for hit in answer.hits], [expected_id])
                self.assertTrue(answer.source_ids)
                self.assertTrue(all(source_id in self.sources for source_id in answer.source_ids))
                self.assertNotIn("[KB", answer.answer)

    def test_yunjin_shorthand_and_process_intent_are_relevant(self):
        shorthand = answer_from_knowledge("云锦是什么？", self.items, self.sources)
        self.assertEqual(shorthand.status, "基于本地知识库")
        self.assertEqual([hit.item.id for hit in shorthand.hits], ["KB001"])

        process = answer_from_knowledge("南京云锦的传统织造工艺是什么？", self.items, self.sources)
        self.assertEqual(process.status, "基于本地知识库")
        self.assertEqual([hit.item.id for hit in process.hits], ["KB003"])
        self.assertIn("材料准备", process.answer)
        self.assertNotIn("非物质文化遗产代表作名录", process.answer)

    def test_boundary_question_fails_answerability_instead_of_returning_kb015(self):
        answer = answer_from_knowledge(
            "视觉线索与文化知识之间为什么不能等同于鉴定结论？",
            self.items,
            self.sources,
        )
        self.assertEqual(answer.status, "证据不足")
        self.assertEqual(answer.hits, ())
        self.assertIn("没有足够证据直接回答", answer.answer)
        self.assertNotIn("Candidate Knowledge Labels", answer.answer)

    def test_handoff_remains_a_prefill_without_identification_claim(self):
        state = {"main_tab": "AI识锦", "guide_question": ""}
        apply_guide_handoff(state, "妆花是什么？")
        self.assertEqual(state["main_tab"], "AI文化助手")
        self.assertEqual(state["guide_question"], "妆花是什么？")


class Phase5Round2StreamlitTests(unittest.TestCase):
    def run_app(self) -> AppTest:
        with patch.dict(
            os.environ,
            {"DOTS_API_KEY": "", "OPENAI_API_KEY": "", "OPENAI_VISION_MODEL": ""},
        ):
            app = AppTest.from_file(ROOT / "app.py", default_timeout=15).run()
        self.assertFalse(app.exception)
        return app

    @staticmethod
    def submit_question(app: AppTest, question: str) -> None:
        app.text_input(key="guide_question").set_value(question).run()
        submit = next(button for button in app.button if button.label == "获取可信回答")
        submit.click().run()

    def test_repeated_navigation_and_answers_have_no_streamlit_exception(self):
        app = self.run_app()
        questions = ["妆花是什么？", "南京云锦有哪些主要品种？", "八宝纹有什么文化寓意？"]
        for question in questions:
            app.segmented_control(key="main_tab").set_value("AI文化助手").run()
            self.assertFalse(app.exception)
            self.submit_question(app, question)
            self.assertFalse(app.exception)
            rendered = "\n".join(element.value for element in app.markdown)
            self.assertIn(question, rendered)
            app.segmented_control(key="main_tab").set_value("AI探锦").run()
            self.assertFalse(app.exception)

    def test_app_uses_stable_native_navigation_without_custom_dom(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("st.tabs(", source)
        self.assertNotIn("unsafe_allow_html", source)
        self.assertNotIn("components.", source)
        self.assertIn('st.form("guide_question_form"', source)
        self.assertIn('st.container(key="guide_answer_slot")', source)


if __name__ == "__main__":
    unittest.main()
