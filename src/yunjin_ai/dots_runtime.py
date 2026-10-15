from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from typing import Iterator


RETRYABLE_HTTP_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}
_DOTS_REQUEST_GATE = threading.BoundedSemaphore(value=1)


class DotsQueueTimeout(RuntimeError):
    """The shared Dots request slot stayed busy for too long."""


def _bounded_env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def _bounded_env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def dots_request_timeout() -> float:
    return _bounded_env_float("DOTS_REQUEST_TIMEOUT", 35.0, 10.0, 60.0)


def dots_max_attempts() -> int:
    return _bounded_env_int("DOTS_MAX_ATTEMPTS", 3, 1, 4)


@contextmanager
def dots_request_slot() -> Iterator[None]:
    """Serialize Dots calls in one Streamlit process so sessions do not burst one shared key."""
    queue_timeout = _bounded_env_float("DOTS_QUEUE_TIMEOUT", 90.0, 10.0, 180.0)
    acquired = _DOTS_REQUEST_GATE.acquire(timeout=queue_timeout)
    if not acquired:
        raise DotsQueueTimeout("Dots 服务当前请求较多，排队等待超时，请稍后重试。")
    try:
        yield
    finally:
        _DOTS_REQUEST_GATE.release()


def is_retryable_http_status(status_code: int) -> bool:
    return status_code in RETRYABLE_HTTP_STATUSES


def _retry_after_seconds(headers: object | None) -> float | None:
    if headers is None:
        return None
    try:
        raw_value = headers.get("Retry-After")
    except AttributeError:
        return None
    if not raw_value:
        return None
    try:
        return max(0.0, min(float(raw_value), 8.0))
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(str(raw_value))
            now = parsedate_to_datetime(time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
            return max(0.0, min((retry_at - now).total_seconds(), 8.0))
        except (TypeError, ValueError, OverflowError):
            return None


def wait_before_retry(attempt: int, headers: object | None = None) -> None:
    """Use a short exponential backoff and honor a small Retry-After window."""
    retry_after = _retry_after_seconds(headers)
    if retry_after is None:
        base = _bounded_env_float("DOTS_RETRY_BASE_SECONDS", 0.8, 0.0, 3.0)
        retry_after = min(base * (2 ** max(0, attempt - 1)), 6.0)
    if retry_after > 0:
        time.sleep(retry_after)


def user_facing_http_error(status_code: int) -> str:
    if status_code in {401, 403}:
        return "Dots API 认证失败，请检查 API Key 或模型权限。"
    if status_code == 413:
        return "发送给 Dots 的图片数据仍然过大，请换用较小图片后重试。"
    if status_code == 429:
        return "Dots 服务请求过于频繁，已重试但仍处于限流状态。"
    if status_code in {500, 502, 503, 504}:
        return "Dots 服务暂时不可用，已自动重试但仍未恢复。"
    if status_code == 408:
        return "Dots 服务响应超时，已自动重试但仍未恢复。"
    return f"Dots API 请求失败（HTTP {status_code}）。"
