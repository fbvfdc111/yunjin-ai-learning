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
        "历史", "文化", "传承", "艺术", "用途", "当代", "保护", "博物馆",
        "展览", "展示", "宣传", "海报", "文字", "标题", "页面", "截图",
    }
)

KNOWLEDGE_USES = frozenset({"cultural_content", "process/history", "governance/methodology"})
VISUAL_CULTURAL_KNOWLEDGE_USES = frozenset({"cultural_content", "process/history"})
EVIDENCE_SCOPES = frozenset(
    {
        "direct_yunjin",
        "official_object_name",
        "general_cultural_background",
        "governance_methodology",
        "sample_image_metadata",
    }
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
VARIETY_INTENT_TERMS = frozenset({"品种", "种类", "哪几类", "哪几种"})
VARIETY_RELEVANCE_TERMS = frozenset({"品种", "分类", "种类"})
QUESTION_INTENT_EXPANSIONS = (
    (
        ("文化含义", "文化意义", "象征含义", "象征意义", "代表什么"),
        ("寓意",),
    ),
    (
        ("哪一年列入联合国", "何时列入联合国", "什么时候列入联合国"),
        ("2009", "联合国名录"),
    ),
    (
        (
            "妆花为什么能够逐花异色", "妆花为什么能逐花异色", "妆花如何逐花异色",
            "一朵花一个颜色", "一朵花一种颜色", "每朵花不同颜色",
        ),
        ("妆花", "逐花异色"),
    ),
    (
        ("传承保护", "保护传承", "怎么传承", "怎样传承", "怎么保护", "怎样保护", "现在如何传承"),
        ("当代", "传承", "保护"),
    ),
    (
        ("只看照片", "只看图片", "看照片认", "看图片认", "照片认出来", "图片认出来"),
        ("图片", "判断", "南京云锦"),
    ),
    (
        ("网上图片能训练", "网络图片能训练", "公开图片能训练", "图片能训练ai", "图片能训练模型"),
        ("公开图片", "训练模型"),
    ),
    (
        ("实物中有", "实物例子", "实物记录", "藏品中有", "藏品例子"),
        ("对象",),
    ),
    (
        ("制作工艺", "织造工艺", "制作过程", "织造过程", "怎么制作", "如何制作", "怎么织", "如何织", "制作步骤", "有哪些工序"),
        ("南京云锦", "制作", "流程", "主要", "环节", "织造", "工艺"),
    ),
    (
        ("有哪些品种", "有什么品种", "主要品种", "哪些品种", "品种分类", "分为哪几类", "分哪几类", "有哪几种", "哪些种类"),
        ("南京云锦", "主要", "品种", "分类"),
    ),
    (
        ("库锦和库缎怎么区分", "库锦与库缎怎么区分", "库锦和库缎如何区分", "库锦与库缎如何区分"),
        ("库锦", "库缎", "区别"),
    ),
    (
        ("上面的人", "上层的人", "拉线的人", "谁拉线", "谁提经", "拽花工做什么", "拽花工的作用"),
        ("大花楼", "织机", "拽花工", "织手"),
    ),
    (
        ("下面的人", "下层的人", "下面的织手", "织手如何", "织手怎么", "谁控制梭子", "梭子由谁控制", "谁推梭子", "织手做什么", "织手的作用"),
        ("大花楼", "织机", "拽花工", "织手"),
    ),
    (
        ("为什么要手工", "为什么需要手工", "为什么不能机器", "手工织造"),
        ("云锦", "手工", "织造"),
    ),
    (
        ("制作材料", "织造材料", "用什么材料", "使用什么材料", "什么材质", "金线银线", "孔雀羽"),
        ("织造", "材料"),
    ),
    (
        ("南京云锦的历史", "南京云锦历史", "云锦的历史", "云锦历史", "历史文化", "历史沿革", "发展历史", "历史用途", "以前做什么", "以前有什么用途", "过去做什么", "过去有什么用途", "过去主要有什么用途", "当代保护", "如何保护", "传承现状"),
        ("历史", "用途", "当代", "保护"),
    ),
    (
        ("纹样文化", "云锦纹样", "有哪些纹样", "常见纹样", "纹样题材", "图案题材", "怎么构图", "构图形式"),
        ("传统", "纹样", "题材", "构图", "形式"),
    ),
    (
        ("挑花结本有什么用", "挑花结本的作用", "花本有什么用", "花本的作用"),
        ("挑花结本", "作用"),
    ),
)
QUESTION_INTENT_FILTERS = (
    (
        ("龙纹", "龙图案"),
        ("龙纹", "权威", "尊贵"),
    ),
    (
        ("凤纹", "凤凰纹", "凤凰图案"),
        ("凤纹", "权威", "尊贵"),
    ),
    (
        ("牡丹纹", "牡丹图案"),
        ("牡丹", "富贵"),
    ),
    (
        ("只看照片", "只看图片", "看照片认", "看图片认", "照片认出来", "图片认出来"),
        ("视觉观察", "专业鉴定", "南京云锦归属"),
    ),
    (
        ("网上图片能训练", "网络图片能训练", "公开图片能训练", "图片能训练ai", "图片能训练模型"),
        ("公开可访问", "训练授权", "训练集"),
    ),
    (
        ("上面的人", "上层的人", "拉线的人", "谁拉线", "谁提经", "拽花工", "下面的人", "下层的人", "下面的织手", "织手如何", "织手怎么", "谁控制梭子", "梭子由谁控制", "谁推梭子", "织手做什么", "织手的作用"),
        ("花本装机", "双人织造", "拽花工", "织手"),
    ),
    (
        ("制作材料", "织造材料", "用什么材料", "使用什么材料", "什么材质", "金线银线", "孔雀羽"),
        ("织造材料", "材料"),
    ),
    (
        ("南京云锦的历史", "南京云锦历史", "云锦的历史", "云锦历史", "历史文化", "历史沿革", "发展历史", "历史用途", "以前做什么", "以前有什么用途", "过去做什么", "过去有什么用途", "当代保护", "如何保护", "传承现状"),
        ("历史用途", "历史", "用途", "保护"),
    ),
    (
        ("纹样文化", "云锦纹样", "有哪些纹样", "常见纹样", "纹样题材", "图案题材", "怎么构图", "构图形式"),
        ("纹样题材", "纹样题材与构图", "构图"),
    ),
    (
        ("挑花结本有什么用", "挑花结本的作用", "花本有什么用", "花本的作用"),
        ("挑花结本", "纹样转成花本"),
    ),
    (
        ("为什么珍贵", "为何珍贵", "为什么贵", "独特之处", "特别之处", "有什么特点", "有什么特色", "和普通织锦有什么不同", "有什么区别"),
        ("材料", "手工", "工序", "外观", "品种", "逐花异色"),
    ),
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
    expanded_parts = [question]
    if "南京云锦" not in normalized and "云锦" in normalized:
        expanded_parts.append("南京云锦")
    for aliases, canonical_terms in QUESTION_INTENT_EXPANSIONS:
        if any(_normalized_visual_term(alias) in normalized for alias in aliases):
            expanded_parts.extend(canonical_terms)
    return " ".join(dict.fromkeys(part for part in expanded_parts if part))


def _has_process_intent(question: str) -> bool:
    normalized = _normalized_visual_term(question)
    return any(_normalized_visual_term(term) in normalized for term in PROCESS_INTENT_TERMS)


def _item_matches_process_intent(item: KnowledgeItem) -> bool:
    haystack = _normalized_visual_term(" ".join((item.category, item.title, item.fact, *item.keywords)))
    return item.knowledge_use == "process/history" and any(
        _normalized_visual_term(term) in haystack for term in PROCESS_RELEVANCE_TERMS
    )


def _has_variety_intent(question: str) -> bool:
    normalized = _normalized_visual_term(question)
    return any(_normalized_visual_term(term) in normalized for term in VARIETY_INTENT_TERMS)


def _item_matches_variety_intent(item: KnowledgeItem) -> bool:
    haystack = _normalized_visual_term(" ".join((item.category, item.title, *item.keywords)))
    return any(_normalized_visual_term(term) in haystack for term in VARIETY_RELEVANCE_TERMS)


def _item_matches_topic_relevance(item: KnowledgeItem, relevance_terms: tuple[str, ...]) -> bool:
    haystack = _normalized_visual_term(" ".join((item.category, item.title, item.fact, *item.keywords)))
    return any(_normalized_visual_term(term) in haystack for term in relevance_terms)


def _item_relevant_to_question_intent(question: str, item: KnowledgeItem) -> bool:
    if _has_process_intent(question):
        return _item_matches_process_intent(item)
    if _has_variety_intent(question):
        return _item_matches_variety_intent(item)
    normalized = _normalized_visual_term(question)
    for aliases, relevance_terms in QUESTION_INTENT_FILTERS:
        if any(_normalized_visual_term(alias) in normalized for alias in aliases):
            return _item_matches_topic_relevance(item, relevance_terms)
    return True


def _question_contains_term(normalized_question: str, term: str) -> bool:
    normalized_term = _normalized_visual_term(term)
    if normalized_term == "什么":
        return normalized_term in normalized_question.replace("为什么", "")
    return normalized_term in normalized_question


def _answer_group_matches(normalized_question: str, group: tuple[str, ...]) -> bool:
    normalized_group = tuple(_normalized_visual_term(term) for term in group)
    if "什么" in normalized_group:
        subjects = tuple(term for term in normalized_group if term != "什么")
        if not any(
            f"{subject}是什么" in normalized_question or f"什么是{subject}" in normalized_question
            for subject in subjects
        ):
            return False
    return all(_question_contains_term(normalized_question, term) for term in group)


def item_answers_question(question: str, item: KnowledgeItem) -> bool:
    normalized = _normalized_visual_term(normalize_question_for_answering(question))
    heritage_intent = "非物质文化遗产" in normalized or "非遗" in normalized or "联合国名录" in normalized
    if item.id == "KB001" and not heritage_intent:
        definition_intent = normalized in {"南京云锦", "云锦"} or any(
            phrase in normalized
            for phrase in (
                "南京云锦是什么", "云锦是什么", "什么是南京云锦", "什么是云锦",
                "介绍南京云锦", "介绍一下南京云锦", "介绍云锦", "介绍一下云锦",
            )
        )
        if not definition_intent:
            return False
    return bool(normalized) and any(_answer_group_matches(normalized, group) for group in item.answer_terms)


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
                (group for group in item.answer_terms if _answer_group_matches(normalized, group)),
                key=len,
            )
            hits[item.id] = SearchHit(item, 8.0 + len(group), tuple(group))
    return sorted(hits.values(), key=lambda hit: (-hit.score, hit.item.id))[:limit]


YUNJIN_DOMAIN_TERMS = (
    "南京云锦", "云锦", "妆花", "织金", "库锦", "库缎", "金宝地",
    "大花楼", "挑花结本", "花本", "拽花工", "织手", "织机", "织造",
    "纹样", "经线", "纬线", "梭子", "筘框", "非遗",
)
RELATED_QUERY_EXPANSIONS = (
    (
        ("为什么珍贵", "为何珍贵", "为什么贵", "这么珍贵", "如此珍贵", "独特之处", "特别之处", "有什么特点", "有什么特色", "和普通织锦有什么不同", "有什么区别"),
        ("手工", "材料", "工序", "织造", "逐花异色"),
    ),
)


def search_related_knowledge(
    question: str,
    items: Iterable[KnowledgeItem],
    *,
    context_keywords: Iterable[str] = (),
    limit: int = 3,
) -> list[SearchHit]:
    """Return sourced nearby knowledge for new in-domain wording.

    This is deliberately separate from ``search_answerable_knowledge``: the
    caller must present these hits as related context, not as a direct answer.
    """
    normalized = _normalized_visual_term(question)
    if not normalized or not any(_normalized_visual_term(term) in normalized for term in YUNJIN_DOMAIN_TERMS):
        return []
    expanded = normalize_question_for_answering(question)
    related_parts = [expanded]
    matched_supported_expansion = False
    for aliases, related_terms in RELATED_QUERY_EXPANSIONS:
        if any(_normalized_visual_term(alias) in normalized for alias in aliases):
            matched_supported_expansion = True
            related_parts.extend(related_terms)
    if not matched_supported_expansion:
        return []
    candidates = [
        item for item in items
        if item.knowledge_use in {"cultural_content", "process/history"}
        and _item_relevant_to_question_intent(expanded, item)
    ]
    return search_knowledge(
        " ".join([*related_parts, *context_keywords]).strip(),
        candidates,
        limit=limit,
    )


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
