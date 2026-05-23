"""VLM-based OCR: send the cropped image to a multimodal LLM. Implemented in M3."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import OcrEngine, OcrResult

if TYPE_CHECKING:
    from PIL.Image import Image
    from ..config import AppConfig


class VlmOcrEngine(OcrEngine):
    name = "vlm"

    def __init__(self, cfg: "AppConfig") -> None:
        self.cfg = cfg

    def ocr(self, image: "Image") -> OcrResult:
        raise NotImplementedError(
            "M3: base64-encode `image`, POST to OpenAI-compatible chat endpoint with a "
            "vision content block, return extracted text + any LaTeX blocks."
        )
