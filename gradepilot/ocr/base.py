"""OCR engine interface. Backends live alongside this file."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image


@dataclass
class OcrResult:
    text: str
    latex_blocks: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class OcrEngine(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def ocr(self, image: "Image") -> OcrResult: ...
