"""Tests for the VLM OCR backend.

httpx MockTransport lets us assert what we send and stub what we receive
without hitting a real API.
"""
from __future__ import annotations

import base64
import json
from io import BytesIO

import httpx
import pytest
from PIL import Image

from gradepilot.config import AppConfig, AutomationConfig, LlmConfig, LoggingConfig, OcrConfig, PathsConfig, SessionConfig, VlmConfig
from gradepilot.ocr import make_engine
from gradepilot.ocr.vlm_ocr import VlmOcrEngine


def _cfg(model: str = "qwen-vl-max", override: str | None = None, api_key: str = "sk-test", engine: str = "vlm") -> AppConfig:
    return AppConfig(
        llm=LlmConfig(
            base_url="https://api.test/v1",
            model=model,
            api_key_env="LLM_API_KEY",
            temperature=0.0,
            max_tokens=512,
            timeout_seconds=10,
            api_key=api_key,
        ),
        ocr=OcrConfig(engine=engine, vlm=VlmConfig(override_model=override)),
        automation=AutomationConfig(),
        session=SessionConfig(),
        paths=PathsConfig(
            data_dir=__import__("pathlib").Path("/tmp/d"),
            log_dir=__import__("pathlib").Path("/tmp/d/logs"),
            crops_dir=__import__("pathlib").Path("/tmp/d/crops"),
            profiles_dir=__import__("pathlib").Path("/tmp/d/profiles"),
        ),
        logging=LoggingConfig(),
        project_root=__import__("pathlib").Path("/tmp/d"),
    )


def _tiny_image() -> Image.Image:
    img = Image.new("RGB", (8, 8), (255, 255, 255))
    return img


def test_vlm_ocr_sends_image_and_parses_text():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "解：x = 2  \n答：x = 2"}}]},
        )

    cfg = _cfg()
    engine = VlmOcrEngine(cfg, transport=httpx.MockTransport(handler))
    result = engine.ocr(_tiny_image())

    assert result.text == "解：x = 2  \n答：x = 2"
    assert captured["url"].endswith("/chat/completions")
    assert captured["auth"] == "Bearer sk-test"

    body = captured["body"]
    assert body["model"] == "qwen-vl-max"
    assert body["temperature"] == 0.0
    assert body["max_tokens"] == 512
    assert body["messages"][0]["role"] == "system"

    user_content = body["messages"][1]["content"]
    assert isinstance(user_content, list)
    image_part = next(c for c in user_content if c["type"] == "image_url")
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    # The base64 part should decode back to non-empty PNG bytes.
    b64 = image_part["image_url"]["url"].split(",", 1)[1]
    decoded = base64.b64decode(b64)
    assert decoded.startswith(b"\x89PNG")


def test_vlm_ocr_uses_override_model():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    cfg = _cfg(model="qwen-vl-max", override="qwen-vl-ocr")
    engine = VlmOcrEngine(cfg, transport=httpx.MockTransport(handler))
    engine.ocr(_tiny_image())

    assert captured["body"]["model"] == "qwen-vl-ocr"


def test_vlm_ocr_missing_api_key_raises():
    cfg = _cfg(api_key="")
    engine = VlmOcrEngine(cfg)
    with pytest.raises(RuntimeError, match="API key"):
        engine.ocr(_tiny_image())


def test_vlm_ocr_unexpected_response_shape_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"weird": "shape"})

    cfg = _cfg()
    engine = VlmOcrEngine(cfg, transport=httpx.MockTransport(handler))
    with pytest.raises(RuntimeError, match="unexpected VLM response"):
        engine.ocr(_tiny_image())


def test_vlm_ocr_http_error_propagates():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad key"})

    cfg = _cfg()
    engine = VlmOcrEngine(cfg, transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        engine.ocr(_tiny_image())


def test_make_engine_vlm():
    engine = make_engine(_cfg())
    assert isinstance(engine, VlmOcrEngine)


def test_make_engine_paddle_raises_on_use():
    # Factory returns the stub; calling .ocr is what raises NotImplementedError.
    engine = make_engine(_cfg(engine="paddle"))
    with pytest.raises(NotImplementedError):
        engine.ocr(_tiny_image())


def test_make_engine_unknown_raises():
    with pytest.raises(ValueError, match="unknown ocr.engine"):
        make_engine(_cfg(engine="bogus"))
