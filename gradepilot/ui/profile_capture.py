"""Interactive profile capture: 4-step rect/point selection -> JSON profile."""
from __future__ import annotations

import logging
from pathlib import Path

from gradepilot.profiles import (
    Point,
    Profile,
    Rect,
    ScreenInfo,
    save_profile,
)
from gradepilot.ui.overlay import UserCancelled, pick_point, pick_region, screen_size


log = logging.getLogger("gradepilot.capture")


_STEPS = [
    ("answer_region", "rect", "Step 1/4 — drag a rectangle around the ANSWER REGION"),
    ("score_box",     "rect", "Step 2/4 — drag a rectangle around the SCORE INPUT BOX"),
    ("submit_button", "point", "Step 3/4 — click the SUBMIT button"),
    ("next_button",   "point", "Step 4/4 — click the NEXT QUESTION button"),
]


def capture_profile(name: str, profiles_dir: Path) -> Profile:
    """Walk the user through the 4 selection steps and save the profile.

    Raises UserCancelled if the user hits Esc at any step.
    """
    sw, sh = screen_size()
    log.info("starting profile capture: name=%s screen=%dx%d", name, sw, sh)

    collected: dict[str, Rect | Point] = {}
    for key, mode, prompt in _STEPS:
        print(f"\n{prompt}")
        result = pick_region(prompt) if mode == "rect" else pick_point(prompt)
        if result is None:
            log.info("user cancelled at step %s", key)
            raise UserCancelled(f"cancelled at {key}")
        collected[key] = result
        if isinstance(result, Rect):
            print(f"  captured rect: x={result.x} y={result.y} w={result.w} h={result.h}")
        else:
            print(f"  captured point: x={result.x} y={result.y}")

    profile = Profile(
        name=name,
        answer_region=collected["answer_region"],  # type: ignore[arg-type]
        score_box=collected["score_box"],          # type: ignore[arg-type]
        submit_button=collected["submit_button"],  # type: ignore[arg-type]
        next_button=collected["next_button"],      # type: ignore[arg-type]
        screen=ScreenInfo(width=sw, height=sh),
    )
    path = save_profile(profiles_dir, profile)
    log.info("saved profile to %s", path)
    print(f"\nsaved profile: {path}")
    return profile
