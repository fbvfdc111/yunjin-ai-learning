from __future__ import annotations

import base64
import colorsys
import io
import ipaddress
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat


@dataclass(frozen=True)
class VisionObservation:
    provider: str
    provider_status: str
    observable_facts: tuple[str, ...]
    tentative_elements: tuple[str, ...]
    retrieval_keywords: tuple[str, ...]
    limitations: tuple[str, ...]
    raw_metrics: dict[str, Any]


COLOR_NAMES = {
    "红": (185, 55, 55),
    "橙": (210, 125, 45),
    "黄/金": (205, 175, 65),
    "绿": (65, 135, 80),
    "青": (55, 145, 145),
    "蓝": (55, 95, 165),
    "紫": (125, 75, 145),
    "黑/深灰": (35, 35, 35),
    "白/浅灰": (220, 220, 215),
    "棕": (120, 80, 50),
}

DOTS_DEFAULT_BASE_URL = "https://note3-prev-api.askdiandian.com"
DOTS_DEFAULT_VISION_MODEL = "dots3-note-prev"
DOTS_IMAGE_URL_REQUIRED = "Dots 当前需要模型服务可访问的图片 URL"
DOTS_MAX_SOURCE_BYTES = 10 * 1024 * 1024
DOTS_MAX_SENT_IMAGE_BYTES = 4 * 1024 * 1024
DOTS_MAX_IMAGE_DIMENSION = 2048
DOTS_ALLOWED_MIME_TYPES = {"image/jpeg": "JPEG", "image/png": "PNG"}
DOTS_SYSTEM_PROMPT = """你是谨慎的视觉观察助手，只进行可观察视觉分析，不进行文物鉴定。
禁止仅凭图片确定：是否为南京云锦；是否为妆花、织金、库缎等具体工艺；年代；文物名称；真伪；作者或制造者。
不要生成文化事实、历史解释、来源信息、概率或置信度。文化事实将由调用方随后从本地证据知识库检索。
只返回有效 JSON，不要 Markdown。JSON 必须包含以下字符串数组字段：
subject_pattern_observations、composition、colors、repetition_symmetry、retrieval_keywords、limitations。
描述必须保持中性、可观察；不确定的视觉元素使用“疑似”“可能”或“视觉上存在”等措辞。
limitations 必须说明该结果不是南京云锦归属、具体工艺、年代、名称、真伪或作者/制造者鉴定。"""


class DotsProviderError(RuntimeError):
    """A user-facing Dots provider failure that is safe to show in the UI."""


def _nearest_color(rgb: tuple[int, int, int]) -> str:
    return min(COLOR_NAMES, key=lambda name: sum((rgb[i] - COLOR_NAMES[name][i]) ** 2 for i in range(3)))


def _dominant_colors(image: Image.Image, count: int = 4) -> list[dict[str, Any]]:
    thumb = image.copy()
    thumb.thumbnail((256, 256))
    quantized = thumb.quantize(colors=count, method=Image.Quantize.MEDIANCUT).convert("RGB")
    colors = quantized.getcolors(maxcolors=256 * 256) or []
    total = sum(pixel_count for pixel_count, _ in colors) or 1
    output = []
    for pixel_count, rgb in sorted(colors, reverse=True)[:count]:
        output.append(
            {
                "name": _nearest_color(rgb),
                "rgb": list(rgb),
                "share": round(pixel_count / total, 3),
            }
        )
    return output


def _similarity(left: Image.Image, right: Image.Image) -> float:
    diff = ImageChops.difference(left, right)
    mean = sum(ImageStat.Stat(diff).mean) / 3
    return max(0.0, min(1.0, 1.0 - mean / 255.0))


def analyze_locally(image: Image.Image) -> VisionObservation:
    rgb = ImageOps.exif_transpose(image).convert("RGB")
    small = rgb.copy()
    small.thumbnail((384, 384))
    colors = _dominant_colors(small)
    resized = small.resize((64, 64))
    get_pixels = getattr(resized, "get_flattened_data", resized.getdata)
    hsv = [colorsys.rgb_to_hsv(*(channel / 255 for channel in pixel)) for pixel in get_pixels()]
    mean_saturation = sum(value[1] for value in hsv) / len(hsv)
    gray = ImageOps.grayscale(small)
    edge_mean = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0] / 255.0
    horizontal_symmetry = _similarity(small, ImageOps.mirror(small))
    vertical_symmetry = _similarity(small, ImageOps.flip(small))

    color_text = "、".join(f"{row['name']}（RGB {tuple(row['rgb'])}）" for row in colors[:3])
    observable = [f"算法提取的主要色群为：{color_text}。"]
    observable.append("画面综合色彩较鲜明。" if mean_saturation >= 0.42 else "画面综合色彩相对克制。")
    symmetry = max(horizontal_symmetry, vertical_symmetry)
    if symmetry >= 0.78:
        observable.append("低分辨率像素比较显示画面具有较明显的镜像相似性，可作为“疑似对称结构”观察。")
    elif symmetry >= 0.62:
        observable.append("低分辨率像素比较显示一定镜像相似性，但不足以断言为严格对称纹样。")
    else:
        observable.append("像素比较未显示强镜像相似性；这不排除局部对称或重复。")
    observable.append("边缘变化较丰富，可能存在较密集的轮廓/纹理。" if edge_mean >= 0.16 else "整体边缘变化较平缓。")

    keywords = [row["name"].split("/")[0] for row in colors[:3]]
    keywords.extend(["纹样", "构图"])
    if symmetry >= 0.62:
        keywords.extend(["对称", "重复"])
    return VisionObservation(
        provider="local_cv",
        provider_status="已实测的本地图像统计 fallback",
        observable_facts=tuple(observable),
        tentative_elements=(),
        retrieval_keywords=tuple(dict.fromkeys(keywords)),
        limitations=(
            "本地 fallback 只做颜色、边缘与镜像相似性统计，不识别动物、植物、工艺、年代或对象名称。",
            "这些数值是图像描述指标，不是分类概率或模型置信度。",
            "分析结果不能证明图片属于南京云锦。",
        ),
        raw_metrics={
            "width": rgb.width,
            "height": rgb.height,
            "dominant_colors": colors,
            "mean_saturation": round(mean_saturation, 3),
            "horizontal_mirror_similarity": round(horizontal_symmetry, 3),
            "vertical_mirror_similarity": round(vertical_symmetry, 3),
            "edge_density_proxy": round(edge_mean, 3),
        },
    )


def dots_is_configured() -> bool:
    return bool(os.getenv("DOTS_API_KEY"))


def _dots_base_url() -> str:
    base_url = os.getenv("DOTS_BASE_URL", DOTS_DEFAULT_BASE_URL).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise DotsProviderError("DOTS_BASE_URL 必须是有效的 HTTPS 地址。")
    return base_url


def _validate_dots_image_url(image_url: str | None) -> str:
    if not image_url:
        raise DotsProviderError(f"{DOTS_IMAGE_URL_REQUIRED}。")
    parsed = urlparse(image_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise DotsProviderError(
            f"{DOTS_IMAGE_URL_REQUIRED}；当前仅接受公网 http/https URL，不发送本地路径或 data URL/base64。"
        )
    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise DotsProviderError(f"{DOTS_IMAGE_URL_REQUIRED}；localhost 无法供模型服务访问。")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise DotsProviderError(f"{DOTS_IMAGE_URL_REQUIRED}；内网或本机 IP 无法供模型服务访问。")
    return image_url.strip()


def _image_bytes_match_mime(image_bytes: bytes, mime_type: str) -> bool:
    if mime_type == "image/jpeg":
        return image_bytes.startswith(b"\xff\xd8\xff")
    if mime_type == "image/png":
        return image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    return False


def _encode_image(image: Image.Image, mime_type: str, *, quality: int = 88) -> bytes:
    output = io.BytesIO()
    normalized = ImageOps.exif_transpose(image)
    if mime_type == "image/jpeg":
        normalized.convert("RGB").save(output, format="JPEG", quality=quality, optimize=True)
    else:
        normalized.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _prepare_dots_data_url(
    image: Image.Image | None,
    mime_type: str | None,
    image_bytes: bytes | None,
) -> tuple[str, dict[str, Any]]:
    normalized_mime = (mime_type or "").lower().strip()
    if normalized_mime == "image/jpg":
        normalized_mime = "image/jpeg"
    if normalized_mime not in DOTS_ALLOWED_MIME_TYPES:
        raise DotsProviderError("Dots Base64 实验仅支持 JPG/JPEG 或 PNG 图片。")
    if image is None:
        raise DotsProviderError("没有可用于 Dots Base64 实验的本地上传图片。")
    if image_bytes is not None and len(image_bytes) > DOTS_MAX_SOURCE_BYTES:
        raise DotsProviderError("本地上传图片超过 10 MB，未发送给 Dots。")

    original_size = len(image_bytes) if image_bytes is not None else None
    can_use_original = bool(
        image_bytes
        and _image_bytes_match_mime(image_bytes, normalized_mime)
        and len(image_bytes) <= DOTS_MAX_SENT_IMAGE_BYTES
        and max(image.size) <= DOTS_MAX_IMAGE_DIMENSION
    )
    if can_use_original:
        encoded_bytes = image_bytes
        compressed = False
    else:
        working = ImageOps.exif_transpose(image).copy()
        working.thumbnail((DOTS_MAX_IMAGE_DIMENSION, DOTS_MAX_IMAGE_DIMENSION))
        quality = 88
        encoded_bytes = _encode_image(working, normalized_mime, quality=quality)
        while len(encoded_bytes) > DOTS_MAX_SENT_IMAGE_BYTES and min(working.size) > 256:
            working = working.resize(
                (max(1, int(working.width * 0.8)), max(1, int(working.height * 0.8))),
                Image.Resampling.LANCZOS,
            )
            quality = max(60, quality - 7)
            encoded_bytes = _encode_image(working, normalized_mime, quality=quality)
        if len(encoded_bytes) > DOTS_MAX_SENT_IMAGE_BYTES:
            raise DotsProviderError("图片压缩后仍超过 Dots 发送上限 4 MB，未发送。")
        compressed = True

    data_url = f"data:{normalized_mime};base64,{base64.b64encode(encoded_bytes).decode('ascii')}"
    return data_url, {
        "source_image_bytes": original_size,
        "sent_image_bytes": len(encoded_bytes),
        "sent_mime_type": normalized_mime,
        "compressed_for_dots": compressed,
    }


def _json_object_from_model_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("response JSON is not an object")
    return payload


def _string_list(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a string array")
    return tuple(item.strip() for item in value if item.strip())


def analyze_with_dots(
    image_url: str | None,
    *,
    image: Image.Image | None = None,
    image_mime_type: str | None = None,
    image_bytes: bytes | None = None,
) -> VisionObservation:
    api_key = os.getenv("DOTS_API_KEY")
    if not api_key:
        raise DotsProviderError("未配置 DOTS_API_KEY。")
    model = os.getenv("DOTS_VISION_MODEL", DOTS_DEFAULT_VISION_MODEL)
    if not model:
        raise DotsProviderError("DOTS_VISION_MODEL 不能为空。")

    image_metadata: dict[str, Any] = {}
    if image_url and image_url.strip():
        dots_image_url = _validate_dots_image_url(image_url)
        image_transport = "public_url"
    else:
        dots_image_url, image_metadata = _prepare_dots_data_url(image, image_mime_type, image_bytes)
        image_transport = "base64_data_url"

    request_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DOTS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请按 system 约束分析这张图片，并返回指定结构的 JSON。",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": dots_image_url, "detail": "medium"},
                    },
                ],
            },
        ],
        "stream": False,
        "max_tokens": 700,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = Request(
        f"{_dots_base_url()}/v1/chat/completions",
        data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
        headers={"api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        content = response_payload["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("message.content is not text")
        payload = _json_object_from_model_text(content)
        sections = (
            ("主体/纹样", _string_list(payload, "subject_pattern_observations")),
            ("构图", _string_list(payload, "composition")),
            ("色彩", _string_list(payload, "colors")),
            ("重复/对称", _string_list(payload, "repetition_symmetry")),
        )
        observable = tuple(f"{label}：{item}" for label, items in sections for item in items)
        keywords = _string_list(payload, "retrieval_keywords")
        limitations = _string_list(payload, "limitations")
        if not observable or not keywords or not limitations:
            raise ValueError("required visual fields are empty")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace").strip()
        if api_key and error_body:
            error_body = error_body.replace(api_key, "[REDACTED]")
        detail = f"：{error_body[:4000]}" if error_body else ""
        raise DotsProviderError(f"Dots API 请求失败（HTTP {exc.code}）{detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise DotsProviderError(f"Dots API 网络调用失败：{exc.reason if isinstance(exc, URLError) else exc}") from exc
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DotsProviderError("Dots API 返回内容无法按预期的结构化视觉结果解析。") from exc

    return VisionObservation(
        provider=f"dots:{model}",
        provider_status="Dots API 调用成功（仅视觉观察；文化事实仍由本地知识库提供）",
        observable_facts=observable,
        tentative_elements=(),
        retrieval_keywords=keywords,
        limitations=limitations + (
            "Dots 输出不是概率意义上的置信度，也不是专业鉴定结论。",
        ),
        raw_metrics={
            "response_id": response_payload.get("id"),
            "requested_provider": "dots",
            "image_transport": image_transport,
            "detail": "medium",
            **image_metadata,
        },
    )


def _local_fallback_after_dots(image: Image.Image, reason: str) -> VisionObservation:
    local = analyze_locally(image)
    return VisionObservation(
        provider=local.provider,
        provider_status=f"Dots 未成功使用，已明确回退 local_cv：{reason}",
        observable_facts=local.observable_facts,
        tentative_elements=local.tentative_elements,
        retrieval_keywords=local.retrieval_keywords,
        limitations=local.limitations + (reason,),
        raw_metrics={
            **local.raw_metrics,
            "requested_provider": "dots",
            "image_transport": "local_cv",
            "fallback_reason": reason,
        },
    )


def openai_is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_VISION_MODEL"))


def analyze_with_openai(image: Image.Image) -> VisionObservation:
    if not openai_is_configured():
        raise RuntimeError("需要同时配置 OPENAI_API_KEY 与 OPENAI_VISION_MODEL。")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai 包；请运行 pip install -r requirements.txt。") from exc

    buffer = io.BytesIO()
    ImageOps.exif_transpose(image).convert("RGB").save(buffer, format="JPEG", quality=90)
    data_url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    prompt = (
        "你是谨慎的织物视觉观察助手。只描述可观察的主色调、图案结构、对称/重复特征、"
        "疑似动物/植物/几何元素和织物视觉特征。禁止断言年代、具体工艺、文物名称、真伪或确定属于南京云锦；"
        "禁止输出概率或置信度。只返回 JSON：observable_facts 字符串数组、tentative_elements 字符串数组、"
        "retrieval_keywords 字符串数组、limitations 字符串数组。推测元素必须使用“疑似/可能/视觉上存在”措辞。"
    )
    response = OpenAI().responses.create(
        model=os.environ["OPENAI_VISION_MODEL"],
        instructions="把图像内容与文化事实严格分离。输出必须是有效 JSON，不要 Markdown。",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": data_url, "detail": "high"},
            ],
        }],
        store=False,
    )
    payload = json.loads(response.output_text)
    return VisionObservation(
        provider=f"openai:{os.environ['OPENAI_VISION_MODEL']}",
        provider_status="API 调用成功（输出仍属待人工复核的模型观察）",
        observable_facts=tuple(payload.get("observable_facts", [])),
        tentative_elements=tuple(payload.get("tentative_elements", [])),
        retrieval_keywords=tuple(payload.get("retrieval_keywords", [])),
        limitations=tuple(payload.get("limitations", [])) + (
            "模型输出不是概率意义上的置信度，也不是专业鉴定结论。",
        ),
        raw_metrics={"response_id": response.id},
    )


def analyze_image(
    image: Image.Image,
    provider: str = "auto",
    image_url: str | None = None,
    image_mime_type: str | None = None,
    image_bytes: bytes | None = None,
) -> VisionObservation:
    if provider == "dots":
        try:
            return analyze_with_dots(
                image_url,
                image=image,
                image_mime_type=image_mime_type,
                image_bytes=image_bytes,
            )
        except DotsProviderError as exc:
            return _local_fallback_after_dots(image, str(exc))
    if provider == "openai" or (provider == "auto" and openai_is_configured()):
        return analyze_with_openai(image)
    return analyze_locally(image)
