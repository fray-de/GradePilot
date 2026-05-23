"""Tests for profile save/load/list and schema versioning."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gradepilot.profiles import (
    PROFILE_SCHEMA_VERSION,
    Point,
    Profile,
    Rect,
    ScreenInfo,
    list_profiles,
    load_profile,
    profile_path,
    save_profile,
)


def _make_profile(name: str = "demo") -> Profile:
    return Profile(
        name=name,
        answer_region=Rect(100, 200, 800, 400),
        score_box=Rect(950, 600, 120, 32),
        submit_button=Point(1100, 600),
        next_button=Point(1200, 600),
        screen=ScreenInfo(width=1920, height=1080),
        max_score=10.0,
        notes="hand-written answers",
    )


def test_rect_center():
    r = Rect(10, 20, 100, 60)
    assert r.center == Point(60, 50)


def test_save_load_roundtrip(tmp_path: Path):
    profile = _make_profile("p1")
    written = save_profile(tmp_path, profile)
    assert written == profile_path(tmp_path, "p1")

    loaded = load_profile(tmp_path, "p1")
    assert loaded == profile


def test_save_writes_valid_json_with_version(tmp_path: Path):
    save_profile(tmp_path, _make_profile("p1"))
    with open(profile_path(tmp_path, "p1"), encoding="utf-8") as f:
        raw = json.load(f)
    assert raw["version"] == PROFILE_SCHEMA_VERSION
    assert raw["answer_region"] == {"x": 100, "y": 200, "w": 800, "h": 400}
    assert raw["next_button"] == {"x": 1200, "y": 600}
    assert raw["screen"] == {"width": 1920, "height": 1080}
    assert "created_at" in raw


def test_load_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_profile(tmp_path, "nope")


def test_load_rejects_wrong_version(tmp_path: Path):
    save_profile(tmp_path, _make_profile("p1"))
    p = profile_path(tmp_path, "p1")
    data = json.loads(p.read_text(encoding="utf-8"))
    data["version"] = 999
    p.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="schema version"):
        load_profile(tmp_path, "p1")


def test_list_profiles_sorted(tmp_path: Path):
    save_profile(tmp_path, _make_profile("zebra"))
    save_profile(tmp_path, _make_profile("apple"))
    save_profile(tmp_path, _make_profile("mango"))
    # Stray non-JSON file should be ignored.
    (tmp_path / "ignore.txt").write_text("x")

    assert list_profiles(tmp_path) == ["apple", "mango", "zebra"]


def test_list_profiles_empty_or_missing(tmp_path: Path):
    assert list_profiles(tmp_path) == []
    assert list_profiles(tmp_path / "does-not-exist") == []
