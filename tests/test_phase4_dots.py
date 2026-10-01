from __future__ import annotations

import base64
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yunjin_ai.vision import analyze_image, dots_is_configured


class FakeHTTPResponse:
    def __init__(self, payload: dict):
        self.body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self.body


class Phase4DotsTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (64, 64), "#8f1838")
        self.dots_env = {
            "DOTS_API_KEY": "fake-test-key",
            "DOTS_BASE_URL": "https://note3-prev-api.askdiandian.com",
            "DOTS_VISION_MODEL": "dots3-note-prev",
        }

    @staticmethod
    def successful_response() -> FakeHTTPResponse:
        model_result = {
            "subject_pattern_observations": ["视觉上存在花叶状轮廓"],
            "composition": ["主体位于画面中央"],
            "colors": ["以红色和金色为主"],
            "repetition_symmetry": ["左右存在近似重复"],
            "retrieval_keywords": ["花叶", "对称", "红色", "金色"],
            "limitations": ["不能据此确定工艺、年代、名称、真伪或归属"],
        }
        return FakeHTTPResponse(
            {
                "id": "mock-dots-response",
                "choices": [{"message": {"content": json.dumps(model_result, ensure_ascii=False)}}],
            }
        )

    def test_dots_configuration_requires_key(self):
        with patch.dict(os.environ, {"DOTS_API_KEY": ""}, clear=False):
            self.assertFalse(dots_is_configured())

    def test_dots_posts_documented_chat_completions_shape(self):
        response = self.successful_response()
        with patch.dict(os.environ, self.dots_env, clear=False), patch(
            "yunjin_ai.vision.urlopen", return_value=response
        ) as mocked_urlopen:
            result = analyze_image(
                self.image,
                provider="dots",
                image_url="https://images.example.org/yunjin-demo.jpg",
                image_mime_type="image/png",
                image_bytes=b"local-bytes-must-not-be-used",
            )

        self.assertEqual(result.provider, "dots:dots3-note-prev")
        self.assertEqual(result.raw_metrics["response_id"], "mock-dots-response")
        self.assertTrue(any(item.startswith("构图：") for item in result.observable_facts))
        self.assertEqual(result.tentative_elements, ())

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://note3-prev-api.askdiandian.com/v1/chat/completions")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Api-key"), "fake-test-key")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "dots3-note-prev")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["max_tokens"], 700)
        self.assertEqual(payload["chat_template_kwargs"], {"enable_thinking": False})
        image_part = payload["messages"][1]["content"][1]
        self.assertEqual(image_part["type"], "image_url")
        self.assertEqual(image_part["image_url"]["detail"], "medium")
        self.assertEqual(image_part["image_url"]["url"], "https://images.example.org/yunjin-demo.jpg")
        self.assertEqual(result.raw_metrics["image_transport"], "public_url")
        system_prompt = payload["messages"][0]["content"]
        for forbidden_claim in ("南京云锦", "妆花", "织金", "库缎", "年代", "真伪", "制造者"):
            self.assertIn(forbidden_claim, system_prompt)

    def test_local_jpeg_and_png_use_correct_base64_data_urls(self):
        cases = (("JPEG", "image/jpeg"), ("PNG", "image/png"))
        for image_format, mime_type in cases:
            with self.subTest(image_format=image_format):
                buffer = io.BytesIO()
                self.image.save(buffer, format=image_format)
                original_bytes = buffer.getvalue()
                with patch.dict(os.environ, self.dots_env, clear=False), patch(
                    "yunjin_ai.vision.urlopen", return_value=self.successful_response()
                ) as mocked_urlopen:
                    result = analyze_image(
                        self.image,
                        provider="dots",
                        image_url=None,
                        image_mime_type=mime_type,
                        image_bytes=original_bytes,
                    )

                request = mocked_urlopen.call_args.args[0]
                payload = json.loads(request.data.decode("utf-8"))
                data_url = payload["messages"][1]["content"][1]["image_url"]["url"]
                prefix, encoded = data_url.split(",", 1)
                self.assertEqual(prefix, f"data:{mime_type};base64")
                self.assertEqual(base64.b64decode(encoded, validate=True), original_bytes)
                self.assertNotIn("C:\\", data_url)
                self.assertEqual(result.provider, "dots:dots3-note-prev")
                self.assertEqual(result.raw_metrics["image_transport"], "base64_data_url")
                self.assertEqual(result.raw_metrics["sent_mime_type"], mime_type)
                self.assertFalse(result.raw_metrics["compressed_for_dots"])

    def test_missing_key_falls_back_to_local_cv(self):
        with patch.dict(os.environ, {"DOTS_API_KEY": ""}, clear=False), patch(
            "yunjin_ai.vision.urlopen"
        ) as mocked_urlopen:
            result = analyze_image(
                self.image,
                provider="dots",
                image_url="https://images.example.org/yunjin-demo.jpg",
            )

        mocked_urlopen.assert_not_called()
        self.assertEqual(result.provider, "local_cv")
        self.assertIn("未配置 DOTS_API_KEY", result.provider_status)

    def test_oversized_dimensions_are_compressed_in_memory(self):
        large_image = Image.new("RGB", (3000, 24), "#8f1838")
        buffer = io.BytesIO()
        large_image.save(buffer, format="PNG")
        original_bytes = buffer.getvalue()
        original_size = large_image.size

        with patch.dict(os.environ, self.dots_env, clear=False), patch(
            "yunjin_ai.vision.urlopen", return_value=self.successful_response()
        ) as mocked_urlopen:
            result = analyze_image(
                large_image,
                provider="dots",
                image_mime_type="image/png",
                image_bytes=original_bytes,
            )

        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        data_url = payload["messages"][1]["content"][1]["image_url"]["url"]
        sent_bytes = base64.b64decode(data_url.split(",", 1)[1], validate=True)
        with Image.open(io.BytesIO(sent_bytes)) as sent_image:
            self.assertLessEqual(max(sent_image.size), 2048)
        self.assertEqual(large_image.size, original_size)
        self.assertEqual(buffer.getvalue(), original_bytes)
        self.assertTrue(result.raw_metrics["compressed_for_dots"])

    def test_http_failure_falls_back_to_local_cv(self):
        with patch.dict(os.environ, self.dots_env, clear=False), patch(
            "yunjin_ai.vision.urlopen", side_effect=URLError("mock offline")
        ):
            result = analyze_image(
                self.image,
                provider="dots",
                image_url="https://images.example.org/yunjin-demo.jpg",
            )

        self.assertEqual(result.provider, "local_cv")
        self.assertIn("mock offline", result.provider_status)
        self.assertTrue(result.observable_facts)

    def test_http_error_body_is_preserved_in_fallback_reason(self):
        error_body = b'{"error":{"message":"invalid image URL: data URL is not supported"}}'
        http_error = HTTPError(
            "https://note3-prev-api.askdiandian.com/v1/chat/completions",
            400,
            "Bad Request",
            hdrs=None,
            fp=io.BytesIO(error_body),
        )
        with patch.dict(os.environ, self.dots_env, clear=False), patch(
            "yunjin_ai.vision.urlopen", side_effect=http_error
        ):
            result = analyze_image(
                self.image,
                provider="dots",
                image_mime_type="image/png",
                image_bytes=b"\x89PNG\r\n\x1a\nmock",
            )

        self.assertEqual(result.provider, "local_cv")
        self.assertEqual(result.raw_metrics["image_transport"], "local_cv")
        self.assertIn("invalid image URL: data URL is not supported", result.raw_metrics["fallback_reason"])


if __name__ == "__main__":
    unittest.main()
