from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


VISUAL_RETRIEVAL_STOP_TERMS = frozenset(
    {
        "主体", "纹样", "图案", "构图", "重复", "对称", "连续", "色彩", "颜色",
        "红色", "橙色", "黄色", "金色", "绿色", "青色", "蓝色", "紫色", "黑色",
        "白色", "灰色", "棕色", "动物", "植物", "人物", "器物", "抽象", "花卉",
        "花叶", "几何", "中心", "左右", "上下", "传统", "织物", "织锦", "视觉",
        "观察", "分类", "训练", "证据", "候选", "可信ai", "光泽", "寓意", "吉祥",
        "富贵", "平安", "祥和", "佛教", "权威", "尊贵", "标签", "编号", "边框",
        "背景", "工笔画", "花鸟画",
    }
)

KNOWLEDGE_USES = frozenset({"cultural_content", "process/history", "governance/methodology"})
VISUAL_CULTURAL_KNOWLEDGE_USES = frozenset({"cultural_content", "process/history"})
EVIDENCE_SCOPES = frozenset(
    {"direct_yunjin", "official_object_name", "general_cultural_background", "governance_methodology"}
)
VISUAL_RETRIEVAL_MODES = frozenset({"direct", "object_name_only", "disabled"})
AUTOMATIC_VISUAL_BLOCKED_TERMS = frozenset(
    {"南京云锦", "云锦", "妆花", "织金", "库锦", "库缎", "工艺", "品种", "年代", "真伪", "蚕丝", "金线", "孔雀羽", "龙袍"}
)
PROCESS_INTENT_TERMS = frozenset(
    {
        "传统织造",
        "手工织造",
        "织造工艺",
        "制作工艺",
        "工艺流程",
        "制作流程",
        "主要环节",
        "百余道工序",
        "工序",
        "流程",
        "环节",
    }
)
PROCESS_RELEVANCE_TERMS = frozenset(
    {
        "材料准备",
        "纹样设计",
        "意匠",
        "挑花结本",
        "造机",
        "织造",
        "大花楼",
        "木织机",
        "拽花工",
        "织手",
        "提经",
        "穿纬",
        "工序",
        "流程",
    }
)


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    publisher: str
    url: str
    accessed_at: str
    source_type: str
    evidence_level: str
    notes: str
    locator: str = ""
    verification_status: str = ""


@dataclass(frozen=True)
class Claim:
    text: str
    source_ids: tuple[str, ...]
    evidence_scope: str


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    category: str
    title: str
    claims: tuple[Claim, ...]
    keywords: tuple[str, ...]
    evidence_level: str
    knowledge_use: str
    answer_terms: tuple[tuple[str, ...], ...]
    visual_retrieval: str

    @property
    def fact(self) -> str:
        return "\n\n".join(claim.text for claim in self.claims)

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(source_id for claim in self.claims for source_id in claim.source_ids))

    @property
    def evidence_scopes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(claim.evidence_scope for claim in self.claims))


@dataclass(frozen=True)
class SearchHit:
    item: KnowledgeItem
    score: float
    matched_terms: tuple[str, ...]


def load_sources(path: Path) -> dict[str, Source]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["source_id"]: Source(**row) for row in data}


def load_knowledge(path: Path) -> list[KnowledgeItem]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        KnowledgeItem(
            id=row["id"],
            category=row["category"],
            title=row["title"],
            claims=tuple(
                Claim(
                    text=claim["text"],
                    source_ids=tuple(claim["source_ids"]),
                    evidence_scope=claim["evidence_scope"],
                )
                for claim in row["claims"]
            ),
            keywords=tuple(row["keywords"]),
            evidence_level=row["evidence_level"],
            knowledge_use=row.get("knowledge_use", "cultural_content"),
            answer_terms=tuple(tuple(group) for group in row.get("answer_terms", [])),
            visual_retrieval=row.get("visual_retrieval", "disabled"),
        )
        for row in data
    ]


def validate_knowledge(items: Iterable[KnowledgeItem], sources: dict[str, Source]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            errors.append(f"duplicate knowledge id: {item.id}")
        seen.add(item.id)
        if not item.claims:
            errors.append(f"missing claims: {item.id}")
        if item.knowledge_use not in KNOWLEDGE_USES:
            errors.append(f"unknown knowledge use {item.knowledge_use}: {item.id}")
        if item.visual_retrieval not in VISUAL_RETRIEVAL_MODES:
            errors.append(f"unknown visual retrieval mode {item.visual_retrieval}: {item.id}")
        if not item.answer_terms or any(not group or any(not term.strip() for term in group) for group in item.answer_terms):
            errors.append(f"missing or invalid answer terms: {item.id}")
        for claim in item.claims:
            if not claim.text.strip():
                errors.append(f"empty claim: {item.id}")
            if not claim.source_ids:
                errors.append(f"missing claim source: {item.id}")
            if claim.evidence_scope not in EVIDENCE_SCOPES:
                errors.append(f"unknown evidence scope {claim.evidence_scope}: {item.id}")
            if claim.evidence_scope in {"general_cultural_background", "governance_methodology"} and item.visual_retrieval != "disabled":
                errors.append(f"non-direct claim enabled for visual retrieval: {item.id}")
            for source_id in claim.source_ids:
                if source_id not in sources:
                    errors.append(f"unknown source {source_id}: {item.id}")
    return errors


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"\s+", "", text.lower())
    latin = set(re.findall(r"[a-z0-9_]+", normalized))
    chinese = re.findall(r"[\u4e00-\u9fff]", normalized)
    grams = {"".join(chinese[i : i + 2]) for i in range(max(0, len(chinese) - 1))}
    return latin | grams


def search_knowledge(query: str, items: Iterable[KnowledgeItem], limit: int = 5) -> list[SearchHit]:
    query = query.strip()
    if not query:
        return []
    query_tokens = _tokens(query)
    hits: list[SearchHit] = []
    for item in items:
        haystack = " ".join((item.title, item.fact, item.category, *item.keywords)).lower()
        exact = tuple(keyword for keyword in item.keywords if keyword.lower() in query.lower())
        overlap = query_tokens & _tokens(haystack)
        score = len(exact) * 5.0 + len(overlap) / max(1, len(query_tokens))
        if item.title.lower() in query.lower() or query.lower() in item.title.lower():
            score += 4.0
        if score > 0.15:
            hits.append(SearchHit(item=item, score=score, matched_terms=tuple(sorted(set(exact) | overlap))))
    return sorted(hits, key=lambda hit: (-hit.score, hit.item.id))[:limit]


def _normalized_visual_term(term: str) -> str:
    return re.sub(r"[^a-z0-9_\u4e00-\u9fff]+", "", term.lower())


def normalize_question_for_answering(question: str) -> str:
    normalized = _normalized_visual_term(question)
    if "南京云锦" not in normalized and "云锦" in normalized:
        return f"南京{question}"
    return question


def _has_process_intent(question: str) -> bool:
    normalized = _normalized_visual_term(question)
    return any(_normalized_visual_term(term) in normalized for term in PROCESS_INTENT_TERMS)


def _item_matches_process_intent(item: KnowledgeItem) -> bool:
    haystack = _normalized_visual_term(" ".join((item.category, item.title, item.fact, *item.keywords)))
    return item.knowledge_use == "process/history" and any(
        _normalized_visual_term(term) in haystack for term in PROCESS_RELEVANCE_TERMS
    )


def _item_relevant_to_question_intent(question: str, item: KnowledgeItem) -> bool:
    return not _has_process_intent(question) or _item_matches_process_intent(item)


def item_answers_question(question: str, item: KnowledgeItem) -> bool:
    normalized = _normalized_visual_term(normalize_question_for_answering(question))
    return bool(normalized) and any(
        all(_normalized_visual_term(term) in normalized for term in group) for group in item.answer_terms
    )


def search_answerable_knowledge(
    question: str,
    items: Iterable[KnowledgeItem],
    *,
    context_keywords: Iterable[str] = (),
    limit: int = 4,
) -> list[SearchHit]:
    expanded_question = normalize_question_for_answering(question)
    answerable = [
        item for item in items
        if item_answers_question(expanded_question, item) and _item_relevant_to_question_intent(expanded_question, item)
    ]
    if not answerable:
        return []
    lexical = search_knowledge(" ".join([expanded_question, *context_keywords]).strip(), answerable, limit=len(answerable))
    hits = {hit.item.id: hit for hit in lexical}
    normalized = _normalized_visual_term(expanded_question)
    for item in answerable:
        if item.id not in hits:
            group = max(
                (group for group in item.answer_terms if all(_normalized_visual_term(term) in normalized for term in group)),
                key=len,
            )
            hits[item.id] = SearchHit(item, 8.0 + len(group), tuple(group))
    return sorted(hits.values(), key=lambda hit: (-hit.score, hit.item.id))[:limit]


def _is_automatic_visual_term_allowed(term: str) -> bool:
    normalized = _normalized_visual_term(term)
    return bool(normalized) and normalized not in VISUAL_RETRIEVAL_STOP_TERMS and not any(
        blocked in normalized for blocked in AUTOMATIC_VISUAL_BLOCKED_TERMS
    )


def _matched_item_keywords(term: str, item: KnowledgeItem) -> set[str]:
    normalized_term = _normalized_visual_term(term)
    matches: set[str] = set()
    for keyword in item.keywords:
        normalized_keyword = _normalized_visual_term(keyword)
        if not normalized_keyword or normalized_keyword in VISUAL_RETRIEVAL_STOP_TERMS:
            continue
        if normalized_term == normalized_keyword or (len(normalized_keyword) >= 2 and normalized_keyword in normalized_term):
            matches.add(keyword)
    return matches


def search_visual_knowledge(
    visual_keywords: Iterable[str],
    confirmed_keywords: Iterable[str],
    items: Iterable[KnowledgeItem],
    limit: int = 5,
    min_score: float = 6.0,
) -> list[SearchHit]:
    visual_terms = tuple(dict.fromkeys(term.strip() for term in visual_keywords if term.strip() and _is_automatic_visual_term_allowed(term)))
    confirmed_terms = tuple(dict.fromkeys(term.strip() for term in confirmed_keywords if term.strip()))
    hits: list[SearchHit] = []
    for item in items:
        if item.knowledge_use not in VISUAL_CULTURAL_KNOWLEDGE_USES or item.visual_retrieval == "disabled":
            continue
        visual_matches = {keyword for term in visual_terms for keyword in _matched_item_keywords(term, item)}
        confirmed_matches = {keyword for term in confirmed_terms for keyword in _matched_item_keywords(term, item)}
        if item.visual_retrieval == "object_name_only":
            visual_matches = set()
        score = len(visual_matches) * 6.0 + len(confirmed_matches) * 12.0
        if score >= min_score:
            hits.append(SearchHit(item, score, tuple(sorted(visual_matches | confirmed_matches))))
    return sorted(hits, key=lambda hit: (-hit.score, hit.item.id))[:limit]


def load_official_objects(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_official_relations(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_official_relations(
    records: Iterable[dict], rows: Iterable[dict[str, str]], knowledge: Iterable[KnowledgeItem]
) -> list[str]:
    errors: list[str] = []
    records = list(records)
    row_ids = {row["object_id"] for row in rows if row.get("level1_label") == "nanjing_yunjin"}
    knowledge_ids = {item.id for item in knowledge}
    record_ids = [record.get("object_id") for record in records]
    if len(record_ids) != len(set(record_ids)):
        errors.append("duplicate official relation catalog number")
    if set(record_ids) != row_ids:
        errors.append("official relation map must cover exactly the 47 Yunjin objects")
    for record in records:
        for relation in record.get("relations", []):
            if relation.get("knowledge_id") not in knowledge_ids:
                errors.append(f"unknown relation knowledge id: {relation.get('knowledge_id')}")
            if relation.get("evidence_scope") != "official_object_name":
                errors.append(f"invalid relation evidence scope: {record.get('object_id')}")
            if relation.get("relation_type") != "official_name_mentions":
                errors.append(f"invalid relation type: {record.get('object_id')}")
        if not record.get("relations") and not record.get("unlinked_reason"):
            errors.append(f"unlinked object missing reason: {record.get('object_id')}")
    return errors


def related_official_objects(
    hits: Iterable[SearchHit],
    rows: Iterable[dict[str, str]],
    relations: Iterable[dict],
    limit: int = 8,
) -> list[dict[str, str]]:
    hit_ids = {hit.item.id for hit in hits}
    relation_by_id = {record["object_id"]: record for record in relations}
    result: list[dict[str, str]] = []
    for row in rows:
        record = relation_by_id.get(row.get("object_id", ""))
        matched = [relation for relation in (record or {}).get("relations", []) if relation.get("knowledge_id") in hit_ids]
        if not matched:
            continue
        enriched = dict(row)
        enriched["_relation_terms"] = "、".join(dict.fromkeys(relation["matched_term"] for relation in matched))
        enriched["_relation_scope"] = "official_object_name"
        enriched["_relation_verification"] = record.get("verification_status", "")
        result.append(enriched)
        if len(result) >= limit:
            break
    return result


def citations_for_hits(hits: Iterable[SearchHit]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(source_id for hit in hits for source_id in hit.item.source_ids))
