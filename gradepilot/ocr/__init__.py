"""OCR backends + factory."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import OcrEngine, OcrResult

if TYPE_CHECKING:
    from ..config import AppConfig


def make_engine(cfg: "AppConfig") -> OcrEngine:
    """Return the OCR engine selected by config.ocr.engine."""
    engine = cfg.ocr.engine
    if engine == "vlm":
        from .vlm_ocr import VlmOcrEngine

        return VlmOcrEngine(cfg)
    if engine == "paddle":
        from .paddle_ocr import PaddleOcrEngine

        return PaddleOcrEngine()
    raise ValueError(f"unknown ocr.engine: {engine!r}")


__all__ = ["OcrEngine", "OcrResult", "make_engine"]
