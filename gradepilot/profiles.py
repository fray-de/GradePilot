"""Profile = a saved set of screen regions/coordinates for one question layout.

Stubbed in M1. Full overlay-based selection lands in M2.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Profile:
    name: str
    answer_region: Rect
    score_box: Point
    submit_button: Point
    max_score: float = 0.0
    notes: str = ""


def profile_path(profiles_dir: Path, name: str) -> Path:
    return profiles_dir / f"{name}.json"


def save_profile(profiles_dir: Path, profile: Profile) -> Path:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    p = profile_path(profiles_dir, profile.name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
    return p


def load_profile(profiles_dir: Path, name: str) -> Profile:
    p = profile_path(profiles_dir, name)
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Profile(
        name=data["name"],
        answer_region=Rect(**data["answer_region"]),
        score_box=Point(**data["score_box"]),
        submit_button=Point(**data["submit_button"]),
        max_score=float(data.get("max_score", 0.0)),
        notes=data.get("notes", ""),
    )
