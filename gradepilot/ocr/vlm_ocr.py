"""VLM-based OCR.

Sends the cropped image to an OpenAI-compatible /chat/completions endpoint
with a vision content block and asks for a faithful transcription. Returns
the text in OcrResult. Works with any provider that mimics OpenAI's vision
schema — Qwen-VL via DashScope, GLM-4V, Doubao Vision, OpenAI gpt-4o, etc.
"""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import TYPE_CHECKING

import httpx
from PIL.Image import Image

from .base import OcrEngine, OcrResult

if TYPE_CHECKING:
    from ..config import AppConfig


log = logging.getLogger("gradepilot.ocr.vlm")


OCR_SYSTEM_PROMPT = (
    "你是一名严谨的中文 OCR 转录助手。\n"
    "- 准确转录图中全部文字、数字、公式、符号。\n"
    "- 保留原始换行和段落结构。\n"
    "- 数学公式用行内 LaTeX（$...$）表示，独立公式用 $$...$$。\n"
    "- 无法辨认的字符以 [?] 占位。\n"
    "- 不要输出任何解释、前言或后缀，只输出转录结果本身。"
)


class VlmOcrEngine(OcrEngine):
    name = "vlm"

    def __init__(
        self,
        cfg: "AppConfig",
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.cfg = cfg
        self._model = cfg.ocr.vlm.override_model or cfg.llm.model
        self._client = httpx.Client(
            base_url=cfg.llm.base_url.rstrip("/"),
            timeout=cfg.llm.timeout_seconds,
            headers={
                "Authorization": f"Bearer {cfg.llm.api_key}",
                "Content-Type": "application/json",
            },
            transport=transport,
        )

    def ocr(self, image: Image) -> OcrResult:
        if not self.cfg.llm.api_key:
            raise RuntimeError(
                f"LLM API key is empty; set env var {self.cfg.llm.api_key_env} in .env"
            )
        buf = BytesIO()
        image.save(buf, format="PNG", optimize=True)
        png_bytes = buf.getvalue()
        data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")

        payload = {
            "model": self._model,
            "temperature": self.cfg.llm.temperature,
            "max_tokens": self.cfg.llm.max_tokens,
            "messages": [
                {"role": "system", "content": OCR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": "请按要求转录这张答题区图片。"},
                    ],
                },
            ],
        }
        log.info(
            "VLM OCR request model=%s image_size=%s png_bytes=%d",
            self._model,
            image.size,
            len(png_bytes),
        )
        resp = self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        body = resp.json()
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"unexpected VLM response shape: {body!r}") from e

        text = (text or "").strip()
        log.info("VLM OCR response chars=%d", len(text))
        return OcrResult(text=text, raw={"model": self._model, "response": body})
