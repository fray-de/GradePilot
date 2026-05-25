"""Crop the answer region from the live screen, and save crops for audit."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from ..profiles import Rect


MAX_EDGE_PX = 2048  # Qwen-VL and most OpenAI-compatible vision APIs cap here.


def grab_region(region: Rect) -> Image.Image:
    """Capture the given physical-pixel rectangle and return a PIL RGB image.

    Long edge is downscaled to MAX_EDGE_PX so we don't blow past the VLM's
    input limit; the aspect ratio is preserved.

    `mss` is imported lazily so save_crop / image_to_png_bytes remain usable
    in environments without a display server (CI tests, headless dev boxes).
    """
    import mss

    bbox = {"left": region.x, "top": region.y, "width": region.w, "height": region.h}
    with mss.mss() as sct:
        raw = sct.grab(bbox)
    img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    if max(img.size) > MAX_EDGE_PX:
        img.thumbnail((MAX_EDGE_PX, MAX_EDGE_PX), Image.LANCZOS)
    return img


def _safe_label(label: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:64] or "crop"


def save_crop(image: Image.Image, crops_dir: Path, label: str) -> Path:
    """Persist a crop to <crops_dir>/<ISO-ts>_<label>.png. Returns the path."""
    crops_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = crops_dir / f"{ts}_{_safe_label(label)}.png"
    image.save(path, format="PNG", optimize=True)
    return path


def image_to_png_bytes(image: Image.Image) -> bytes:
    """PNG-encode an image into an in-memory buffer (for API uploads)."""
    from io import BytesIO

    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
