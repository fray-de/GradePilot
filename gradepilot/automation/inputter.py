"""Simulate keyboard/mouse to type the score and click submit.

Implemented in M5. Safety-critical: must respect cfg.automation.dry_run and the
global stop hotkey. NEVER bypass the pre_click_delay.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import AppConfig
    from ..profiles import Profile


def type_score_and_submit(cfg: "AppConfig", profile: "Profile", score: float) -> bool:
    """Return True if submit was actually clicked, False if dry_run/aborted."""
    raise NotImplementedError(
        "M5: respect cfg.automation.dry_run, honor cfg.automation.stop_hotkey via pynput, "
        "wait cfg.automation.pre_click_delay_ms, then pyautogui.click(profile.score_box), "
        "type score, click profile.submit_button. Log every step."
    )
