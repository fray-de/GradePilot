"""OpenAI-compatible chat client. Implemented in M4."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import GradingResult, LlmClient

if TYPE_CHECKING:
    from PIL.Image import Image
    from ..config import AppConfig


class OpenAiCompatibleClient(LlmClient):
    def __init__(self, cfg: "AppConfig") -> None:
        self.cfg = cfg

    def grade(self, *, prompt: str, image: "Image | None" = None) -> GradingResult:
        raise NotImplementedError(
            "M4: POST chat/completions to cfg.llm.base_url with Authorization: Bearer ${api_key}, "
            "request strict JSON response, parse into GradingResult, validate 0<=score<=max_score."
        )
