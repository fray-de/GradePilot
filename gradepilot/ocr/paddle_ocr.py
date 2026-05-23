"""Optional local PaddleOCR fallback. Implemented later."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import OcrEngine, OcrResult

if TYPE_CHECKING:
    from PIL.Image import Image


class PaddleOcrEngine(OcrEngine):
    name = "paddle"

    def ocr(self, image: "Image") -> OcrResult:
        raise NotImplementedError(
            "Optional: install with `pip install gradepilot[paddle]`, then use PaddleOCR locally."
        )
