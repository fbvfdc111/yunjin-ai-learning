from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.knowledge import load_knowledge, search_visual_knowledge
from yunjin_ai.product import (
    apply_guide_handoff,
    cultural_followup_questions,
    visual_observation_sections,
)
from yunjin_ai.vision import VisionObservation


class Phase5RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = load_knowledge(ROOT / "data" / "knowledge" / "knowledge_base.json")

    def test_generic_visual_terms_do_not_force_specific_culture_match(self):
        hits = search_visual_knowledge(
            ["花卉", "花叶", "红色", "金色光泽", "对称", "构图", "吉祥寓意"], [], self.items
        )
        self.assertEqual(hits, [])

    def test_specific_visual_keyword_passes_threshold(self):
        hits = search_visual_knowledge(["视觉上疑似牡丹"], [], self.items)
        self.assertEqual([hit.item.id for hit in hits], ["KB012"])

    def test_protected_craft_claim_requires_user_confirmed_topic(self):
        automatic = search_visual_knowledge(["疑似妆花工艺"], [], self.items)
        confirmed = search_visual_knowledge([], ["妆花"], self.items)
        self.assertEqual(automatic, [])
        self.assertEqual({hit.item.id for hit in confirmed}, {"KB007", "KB008"})
        self.assertTrue(all(hit.score >= 12.0 for hit in confirmed))

    def test_user_confirmed_topic_outweighs_generic_visual_terms(self):
        hits = search_visual_knowledge(["花卉", "红色"], ["八宝"], self.items)
        self.assertEqual(hits, [])


class Phase5ProductHelpersTests(unittest.TestCase):
    def test_visual_output_is_grouped_for_product_display(self):
        observation = VisionObservation(
            provider="dots:dots3-note-prev",
            provider_status="ok",
            observable_facts=(
                "主体/纹样：视觉上存在花叶状轮廓",
                "构图：主体位于画面中央",
                "色彩：以红色和金色为主",
                "重复/对称：左右存在近似重复",
            ),
            tentative_elements=(),
            retrieval_keywords=("花叶", "对称"),
            limitations=("不能鉴定",),
            raw_metrics={"image_transport": "base64_data_url"},
        )
        sections = visual_observation_sections(observation)
        self.assertEqual(sections["纹样与主体"], ("视觉上存在花叶状轮廓",))
        self.assertEqual(len(sections["构图特征"]), 2)
        self.assertEqual(sections["色彩特征"], ("以红色和金色为主",))

    def test_handoff_prefills_question_and_switches_tab(self):
        state = {"main_tab": "AI识锦", "guide_question": ""}
        apply_guide_handoff(state, "八宝纹有什么文化寓意？")
        self.assertEqual(state["main_tab"], "AI文化助手")
        self.assertEqual(state["guide_question"], "八宝纹有什么文化寓意？")

    def test_followups_are_questions_not_image_identification_claims(self):
        items = load_knowledge(ROOT / "data" / "knowledge" / "knowledge_base.json")
        hits = search_visual_knowledge([], ["妆花"], items)
        questions = cultural_followup_questions(hits)
        self.assertIn("妆花是什么？", questions)
        self.assertFalse(any("这张图片确定" in question for question in questions))


class Phase5StreamlitUITests(unittest.TestCase):
    def run_app(self) -> AppTest:
        with patch.dict(os.environ, {"DOTS_API_KEY": "", "OPENAI_API_KEY": "", "OPENAI_VISION_MODEL": ""}):
            app = AppTest.from_file(ROOT / "app.py", default_timeout=15).run()
        self.assertFalse(app.exception)
        return app

    def test_home_has_product_message_and_governance_metrics(self):
        app = self.run_app()
        rendered = "\n".join(element.value for element in [*app.title, *app.header, *app.markdown, *app.caption])
        self.assertIn("让 AI 看见纹样，让文化知识有据可查。", rendered)
        self.assertIn("Official Evidence Database", rendered)
        self.assertEqual(len(app.metric), 4)
        self.assertIn("妆花工艺", {button.label for button in app.button})

    def test_dots_is_default_provider_and_technical_details_are_folded(self):
        app = self.run_app()
        app.segmented_control(key="main_tab").set_value("AI探锦").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control(key="vision_provider").value, "dots")
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('with st.expander("技术详情 / Technical Details"', source)
        self.assertIn('with st.expander("技术详情 / Technical Details：本次调用"', source)

    def test_culture_assistant_has_quick_questions_and_grounded_copy(self):
        app = self.run_app()
        app.segmented_control(key="main_tab").set_value("AI文化助手").run()
        self.assertFalse(app.exception)
        button_labels = {button.label for button in app.button}
        self.assertTrue(set(("妆花是什么？", "挑花结本是什么，有什么作用？")).issubset(button_labels))
        rendered = "\n".join(element.value for element in [*app.markdown, *app.caption])
        self.assertIn("不会绕过知识库补写文化事实", rendered)


if __name__ == "__main__":
    unittest.main()
