from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .dots_runtime import (
    DotsQueueTimeout,
    dots_max_attempts,
    dots_request_slot,
    dots_request_timeout,
    is_retryable_http_status,
    user_facing_http_error,
    wait_before_retry,
)
from .knowledge import (
    Claim,
    SearchHit,
    Source,
    citations_for_hits,
    search_answerable_knowledge,
    search_related_knowledge,
)


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    claims: tuple[Claim, ...]
    hits: tuple[SearchHit, ...]
    source_ids: tuple[str, ...]
    status: str


DOTS_DEFAULT_BASE_URL = "https://note3-prev-api.askdiandian.com"
DOTS_DEFAULT_TEXT_MODEL = "dots3-note-prev"
AI_REFERENCE_STATUS = "AI 辅助参考（待核验）"
AI_SERVICE_UNAVAILABLE_STATUS = "AI 扩展服务暂时繁忙"
ASSISTANT_INFO_STATUS = "助手说明"
OUT_OF_SCOPE_STATUS = "超出助手范围"
YUNJIN_ASSISTANT_TERMS = (
    "南京云锦", "云锦", "妆花", "织金", "库锦", "库缎", "金宝地", "挑花结本",
    "大花楼", "拽花工", "织手", "织机", "纹样", "经线", "纬线", "梭子", "筘框", "非遗",
)
URL_LIKE_PATTERN = re.compile(
    r"(?i)\b(?:https?://)?(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/[^\s，。；！？]*)?"
)


def neutralize_generated_links(text: str) -> str:
    """Keep model-supplied domains readable without turning surrounding prose into links."""
    return URL_LIKE_PATTERN.sub(
        lambda match: match.group(0).replace("://", "\u200b://").replace(".", "\u200b."),
        text,
    )


def _assistant_info_answer(question: str) -> str | None:
    normalized = question.lower().replace(" ", "").strip("？?！!。.")
    if normalized in {"你是谁", "你叫什么", "你是什么", "介绍一下你自己"}:
        return (
            "我是南京云锦文化 AI 助手，主要帮助你了解南京云锦的品种、纹样文化、"
            "制作工艺、传承保护和数字织机。可信文化答案会展示本地资料来源；"
            "知识库暂未覆盖的问题会明确标注为 AI 辅助参考（待核验）。"
        )
    if normalized in {"你好", "您好", "嗨", "hello", "hi"}:
        return "你好！我是南京云锦文化 AI 助手。你可以问我云锦品种、纹样寓意、织造工艺或传承保护。"
    if normalized in {"你能做什么", "你会什么", "怎么使用", "怎么用"}:
        return (
            "我可以回答南京云锦文化问题、展示可追溯资料来源，并把未核验的 AI 扩展内容单独标注；"
            "你也可以前往“AI 探锦”观察图片，或在“数字织机”体验织造步骤。"
        )
    return None


def dots_text_is_configured() -> bool:
    return bool(os.getenv("DOTS_API_KEY"))


def _is_yunjin_question(question: str) -> bool:
    normalized = question.lower().replace(" ", "")
    return any(term.lower() in normalized for term in YUNJIN_ASSISTANT_TERMS)


def _dots_text_base_url() -> str:
    base_url = os.getenv("DOTS_BASE_URL", DOTS_DEFAULT_BASE_URL).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("DOTS_BASE_URL 必须是有效的 HTTPS 地址。")
    return base_url


def _answer_with_dots_reference(question: str) -> str:
    api_key = os.getenv("DOTS_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 DOTS_API_KEY。")
    model = os.getenv("DOTS_TEXT_MODEL") or os.getenv("DOTS_VISION_MODEL") or DOTS_DEFAULT_TEXT_MODEL
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是南京云锦文化学习助手。当前问题未被本地核验知识库覆盖。"
                    "请提供简短、审慎的中文背景参考，不得虚构出处、文物名称、年代、传承人或具体数据；"
                    "不确定时明确说不确定，并建议查阅中国非物质文化遗产网、博物馆或专业研究资料。"
                    "不要声称回答已经过本项目知识库核验，不要输出网址或 Markdown 链接。"
                ),
            },
            {"role": "user", "content": question},
        ],
        "stream": False,
        "max_tokens": 600,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = Request(
        f"{_dots_text_base_url()}/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    last_error: Exception | None = None
    try:
        with dots_request_slot():
            for attempt in range(1, dots_max_attempts() + 1):
                try:
                    with urlopen(request, timeout=dots_request_timeout()) as response:
                        result = json.loads(response.read().decode("utf-8"))
                    content = result["choices"][0]["message"]["content"]
                    if not isinstance(content, str) or not content.strip():
                        raise ValueError("AI 扩展回答为空。")
                    return neutralize_generated_links(content.strip())
                except HTTPError as exc:
                    last_error = exc
                    if is_retryable_http_status(exc.code) and attempt < dots_max_attempts():
                        wait_before_retry(attempt, exc.headers)
                        continue
                    raise RuntimeError(user_facing_http_error(exc.code)) from exc
                except (URLError, TimeoutError, OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    last_error = exc
                    if attempt < dots_max_attempts():
                        wait_before_retry(attempt)
                        continue
                    raise RuntimeError("Dots 扩展回答连接或返回异常，自动重试后仍未成功。") from exc
    except DotsQueueTimeout as exc:
        raise RuntimeError(str(exc)) from exc
    raise RuntimeError("Dots 扩展回答暂时不可用。") from last_error


def answer_from_knowledge(
    question: str,
    items: Iterable,
    sources: dict[str, Source],
    context_keywords: Iterable[str] = (),
    limit: int = 4,
) -> GroundedAnswer:
    items = tuple(items)
    hits = search_answerable_knowledge(
        question,
        items,
        context_keywords=context_keywords,
        limit=limit,
    )
    is_related_fallback = False
    if not hits:
        hits = search_related_knowledge(
            question,
            items,
            context_keywords=context_keywords,
            limit=min(limit, 3),
        )
        is_related_fallback = bool(hits)
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
    if is_related_fallback:
        status = "可信延伸回答"
    elif scopes == {"direct_yunjin"}:
        status = "基于本地知识库"
    elif scopes == {"official_object_name"}:
        status = "仅官方对象名称/目录证据"
    elif scopes == {"general_cultural_background"}:
        status = "一般传统文化背景"
    else:
        status = "分层证据"
    return GroundedAnswer(
        answer=(
            ("根据与问题最相关、且有来源支持的云锦知识作答：\n\n")
            if is_related_fallback else ""
        ) + "\n\n".join(claim.text for claim in claims),
        claims=claims,
        hits=tuple(hits),
        source_ids=citations_for_hits(hits),
        status=status,
    )


def answer_hybrid(
    question: str,
    items: Iterable,
    sources: dict[str, Source],
    context_keywords: Iterable[str] = (),
    limit: int = 4,
) -> GroundedAnswer:
    """Prefer sourced local knowledge, then offer a clearly separated AI reference."""
    assistant_info = _assistant_info_answer(question)
    if assistant_info:
        return GroundedAnswer(
            answer=assistant_info,
            claims=(),
            hits=(),
            source_ids=(),
            status=ASSISTANT_INFO_STATUS,
        )
    local = answer_from_knowledge(
        question,
        items,
        sources,
        context_keywords=context_keywords,
        limit=limit,
    )
    if local.status != "证据不足":
        return local
    if not _is_yunjin_question(question):
        return GroundedAnswer(
            answer=(
                "这个问题超出了南京云锦文化助手的服务范围。"
                "你可以询问云锦的品种、纹样、织造工艺、历史传承或数字织机。"
            ),
            claims=(),
            hits=(),
            source_ids=(),
            status=OUT_OF_SCOPE_STATUS,
        )
    if not dots_text_is_configured():
        return local
    try:
        reference = _answer_with_dots_reference(question)
    except (RuntimeError, ValueError):
        return GroundedAnswer(
            answer=(
                "本地知识库暂未覆盖这个问题，同时 AI 扩展服务当前繁忙或连接异常。"
                "系统没有把接口失败误写成文化答案，请稍后再次尝试。"
            ),
            claims=(),
            hits=(),
            source_ids=(),
            status=AI_SERVICE_UNAVAILABLE_STATUS,
        )
    return GroundedAnswer(
        answer=reference,
        claims=(),
        hits=(),
        source_ids=(),
        status=AI_REFERENCE_STATUS,
    )
