"""Crop the answer region from the live screen. Implemented in M3."""
from __future__ import annotations

from ..profiles import Rect


def grab_region(region: Rect):  # -> PIL.Image.Image
    raise NotImplementedError("M3: use mss/ImageGrab to capture `region` and return a PIL Image.")
