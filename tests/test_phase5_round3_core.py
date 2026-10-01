from __future__ import annotations

import hashlib
import os
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import (
    EVIDENCE_SCOPES,
    load_knowledge,
    load_official_objects,
    load_official_relations,
    load_sources,
    related_official_objects,
    search_answerable_knowledge,
    search_visual_knowledge,
    validate_knowledge,
    validate_official_relations,
)


class Round3KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kd = ROOT / "data" / "knowledge"
        cls.sources = load_sources(kd / "sources.json")
        cls.items = load_knowledge(kd / "knowledge_base.json")
        cls.official = load_official_objects(ROOT / "data" / "metadata" / "official_metadata.csv")
        cls.relations = load_official_relations(kd / "official_object_knowledge_map.json")
        cls.by_id = {item.id: item for item in cls.items}

    def test_required_core_topics_exist_without_count_quota(self):
        required = {
            "KB008", "KB009", "KB016", "KB017", "KB018", "KB019",
            "KB020", "KB021", "KB022", "KB023", "KB024", "KB025",
        }
        self.assertTrue(required.issubset(self.by_id))
        self.assertEqual(validate_knowledge(self.items, self.sources), [])

    def test_claims_have_explicit_sources_and_scopes(self):
        for item in self.items:
            for claim in item.claims:
                self.assertIn(claim.evidence_scope, EVIDENCE_SCOPES)
                self.assertTrue(claim.source_ids)
                self.assertTrue(all(source_id in self.sources for source_id in claim.source_ids))

    def test_general_background_is_disabled_for_visual_retrieval(self):
        general = [
            item for item in self.items
            if any(claim.evidence_scope == "general_cultural_background" for claim in item.claims)
        ]
        self.assertTrue(general)
        self.assertTrue(all(item.visual_retrieval == "disabled" for item in general))
        self.assertEqual(search_visual_knowledge(["八宝", "莲", "松鹤", "寿字"], [], self.items), [])

    def test_official_name_only_requires_user_selected_topic(self):
        self.assertEqual(search_visual_knowledge(["鹤"], [], self.items), [])
        selected = search_visual_knowledge([], ["鹤"], self.items)
        self.assertEqual([hit.item.id for hit in selected], ["KB021"])
        self.assertEqual(set(selected[0].item.evidence_scopes), {"official_object_name"})

    def test_core_questions_return_expected_evidence(self):
        cases = {
            "妆花是什么？": "KB008",
            "织金是什么？": "KB009",
            "库锦是什么？": "KB016",
            "库缎是什么？": "KB017",
            "挑花结本是什么，有什么作用？": "KB019",
            "南京云锦官方对象中有凤纹吗？": "KB020",
            "南京云锦官方对象中有鹤纹吗？": "KB021",
            "南京云锦官方对象中有灵芝吗？": "KB023",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                answer = answer_from_knowledge(question, self.items, self.sources)
                self.assertIn(expected, [hit.item.id for hit in answer.hits])
                self.assertTrue(answer.claims)
                self.assertNotEqual(answer.status, "证据不足")

    def test_classification_differences_are_preserved(self):
        answer = answer_from_knowledge("四大品种有哪些有证据的区别？", self.items, self.sources)
        self.assertIn("KB018", [hit.item.id for hit in answer.hits])
        text = answer.answer
        self.assertIn("三类、四类", text)
        self.assertIn("金宝地", text)
        self.assertIn("不把四类包装成唯一国家分类标准", text)

    def test_general_background_is_labeled_and_limited(self):
        answer = answer_from_knowledge("八宝纹有什么文化寓意？", self.items, self.sources)
        self.assertEqual(answer.status, "一般传统文化背景")
        self.assertTrue(all(claim.evidence_scope == "general_cultural_background" for claim in answer.claims))
        self.assertIn("跨媒介文化背景", answer.answer)


class Round3OfficialRelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kd = ROOT / "data" / "knowledge"
        cls.items = load_knowledge(kd / "knowledge_base.json")
        cls.official = load_official_objects(ROOT / "data" / "metadata" / "official_metadata.csv")
        cls.relations = load_official_relations(kd / "official_object_knowledge_map.json")

    def test_relation_map_covers_exactly_47_yunjin_objects(self):
        self.assertEqual(validate_official_relations(self.relations, self.official, self.items), [])
        self.assertEqual(len(self.relations), 47)
        self.assertTrue(all(record.get("relations") or record.get("unlinked_reason") for record in self.relations))

    def test_every_relation_is_name_only_and_literal(self):
        name_by_id = {row["object_id"]: row["official_name"] for row in self.official}
        for record in self.relations:
            for relation in record["relations"]:
                self.assertEqual(relation["relation_type"], "official_name_mentions")
                self.assertEqual(relation["evidence_scope"], "official_object_name")
                self.assertIn(relation["matched_term"], name_by_id[record["object_id"]])
                self.assertIn("不证明图像内容", relation["claim_limit"])

    def test_related_objects_use_explicit_map(self):
        hits = search_answerable_knowledge("南京云锦官方对象中有牡丹吗？", self.items)
        related = related_official_objects(hits, self.official, self.relations)
        self.assertTrue(related)
        self.assertTrue(all("牡丹" in row["official_name"] for row in related))
        self.assertTrue(all(row["_relation_scope"] == "official_object_name" for row in related))

    def test_authorization_governance_invariants(self):
        counts = Counter(row["level1_label"] for row in self.official)
        self.assertEqual(len(self.official), 95)
        self.assertEqual(counts, {"nanjing_yunjin": 47, "other_brocade": 48})
        self.assertTrue(all(row["authorization_status"] == "unknown" for row in self.official))
        self.assertTrue(all(row["usable_for_training"] == "false" for row in self.official))


class Round3ProtectedFilesTests(unittest.TestCase):
    EXPECTED = {
        "src/yunjin_ai/vision.py": "F1CCDB58311E63588466431B440235417D6F5595D31E4917C55B55DEC2FDEA09",
        "tests/test_phase4_dots.py": "B18DCE6BA889B5D3B064111A7A1D4A27BBF0F2552FDC5126AF66DC1F1ABDDCF7",
        "data/metadata/official_metadata.csv": "915F8C4C9605D912DA7ED8B8307957B4D000DEAED679BA250D4670BD49788823",
        "data/metadata/official_level2_candidate_labels.csv": "F326EC87F79CEF1E0B474D3515B8954B1460F7C0735A7C2E6750B15A93790C9B",
        "docs/phase2_audit_results.json": "8FDADF9470E85DA063883A55B39F398FDB9D6EF82609647508C94FAAA8052C39",
    }

    def test_protected_files_match_round2_sha256(self):
        for relative, expected in self.EXPECTED.items():
            with self.subTest(path=relative):
                digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()
                self.assertEqual(digest, expected)


class Round3StreamlitTests(unittest.TestCase):
    def run_app(self) -> AppTest:
        with patch.dict(os.environ, {"DOTS_API_KEY": "", "OPENAI_API_KEY": "", "OPENAI_VISION_MODEL": ""}):
            app = AppTest.from_file(ROOT / "app.py", default_timeout=15).run()
        self.assertFalse(app.exception)
        return app

    def test_navigation_and_evidence_copy(self):
        app = self.run_app()
        self.assertIn("AI探锦", app.segmented_control(key="main_tab").options)
        app.segmented_control(key="main_tab").set_value("AI文化助手").run()
        rendered = "\n".join(element.value for element in [*app.markdown, *app.caption])
        self.assertIn("不会绕过知识库补写文化事实", rendered)
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("一般传统文化背景", source)
        self.assertIn("不是图像鉴定、模型分类或训练标签", source)
        self.assertIn("希望继续探索的文化主题（可选）", source)


if __name__ == "__main__":
    unittest.main()
