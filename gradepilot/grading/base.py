"""LLM grading client interface + result dataclasses."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image


@dataclass
class GradingBreakdownItem:
    clause: str
    awarded: float
    reason: str


@dataclass
class GradingResult:
    score: float
    max_score: float
    breakdown: list[GradingBreakdownItem] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""
    raw_json: str = ""


class LlmClient(abc.ABC):
    """Pluggable LLM backend. M1 stub; concrete impl in M4."""

    @abc.abstractmethod
    def grade(
        self,
        *,
        prompt: str,
        image: "Image | None" = None,
    ) -> GradingResult: ...
