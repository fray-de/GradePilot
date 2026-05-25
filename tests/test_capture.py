"""Tests for crop saving + label sanitization. grab_region is not tested
because it needs a display server; mss itself is mature and well-covered.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from gradepilot.capture.screenshot import image_to_png_bytes, save_crop


def test_save_crop_writes_file_with_label(tmp_path: Path):
    img = Image.new("RGB", (16, 16), (200, 200, 200))
    path = save_crop(img, tmp_path, "myexam")

    assert path.exists()
    assert path.parent == tmp_path
    assert path.suffix == ".png"
    assert "myexam" in path.name


def test_save_crop_sanitizes_label(tmp_path: Path):
    img = Image.new("RGB", (4, 4))
    path = save_crop(img, tmp_path, "a/b\\c?d:e")

    # Every disallowed char must have been replaced.
    for bad in "/\\?:":
        assert bad not in path.name


def test_save_crop_creates_missing_dir(tmp_path: Path):
    target = tmp_path / "nested" / "crops"
    assert not target.exists()
    save_crop(Image.new("RGB", (2, 2)), target, "x")
    assert target.is_dir()


def test_image_to_png_bytes_roundtrip():
    img = Image.new("RGB", (10, 5), (255, 0, 0))
    data = image_to_png_bytes(img)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    # Should re-decode to the same dimensions.
    from io import BytesIO

    decoded = Image.open(BytesIO(data))
    assert decoded.size == (10, 5)
