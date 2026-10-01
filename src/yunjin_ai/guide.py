from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .knowledge import Claim, SearchHit, Source, citations_for_hits, search_answerable_knowledge


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    claims: tuple[Claim, ...]
    hits: tuple[SearchHit, ...]
    source_ids: tuple[str, ...]
    status: str


def answer_from_knowledge(
    question: str,
    items: Iterable,
    sources: dict[str, Source],
    context_keywords: Iterable[str] = (),
    limit: int = 4,
) -> GroundedAnswer:
    hits = search_answerable_knowledge(
        question,
        items,
        context_keywords=context_keywords,
        limit=limit,
    )
    sources_are_complete = hits and all(
        source_id in sources for hit in hits for source_id in hit.item.source_ids
    )
    if not hits or not sources_are_complete:
        return GroundedAnswer(
            answer=(
                "当前本地知识库没有足够证据直接回答这个问题。"
                "我不会把常识猜测或模型推测补写成南京云锦文化事实；建议补充权威资料或请专家核验。"
            ),
            claims=(),
            hits=(),
            source_ids=(),
            status="证据不足",
        )

    claims = tuple(claim for hit in hits for claim in hit.item.claims)
    scopes = {claim.evidence_scope for claim in claims}
    if scopes == {"direct_yunjin"}:
        status = "基于本地知识库"
    elif scopes == {"official_object_name"}:
        status = "仅官方对象名称/目录证据"
    elif scopes == {"general_cultural_background"}:
        status = "一般传统文化背景"
    else:
        status = "分层证据"
    return GroundedAnswer(
        answer="\n\n".join(claim.text for claim in claims),
        claims=claims,
        hits=tuple(hits),
        source_ids=citations_for_hits(hits),
        status=status,
    )
