"""Profile = a saved set of screen regions/coordinates for one question layout.

Each profile captures, for one exam UI on one screen resolution:
  - answer_region: where the student's answer is drawn (bbox to OCR)
  - score_box   : the score input field on the grading UI (bbox; we click center)
  - submit_button, next_button: pixel-precise click targets

Profiles live as JSON under <paths.profiles_dir>/<name>.json.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


PROFILE_SCHEMA_VERSION = 1


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> "Point":
        return Point(self.x + self.w // 2, self.y + self.h // 2)


@dataclass
class Point:
    x: int
    y: int


@dataclass
class ScreenInfo:
    width: int
    height: int


@dataclass
class Profile:
    name: str
    answer_region: Rect
    score_box: Rect
    submit_button: Point
    next_button: Point
    screen: ScreenInfo
    version: int = PROFILE_SCHEMA_VERSION
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
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
    if not p.exists():
        raise FileNotFoundError(f"profile not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    version = int(data.get("version", 0))
    if version != PROFILE_SCHEMA_VERSION:
        raise ValueError(
            f"profile '{name}' has schema version {version}; this build expects "
            f"{PROFILE_SCHEMA_VERSION}. Re-run --define-profile to regenerate."
        )
    return Profile(
        name=data["name"],
        answer_region=Rect(**data["answer_region"]),
        score_box=Rect(**data["score_box"]),
        submit_button=Point(**data["submit_button"]),
        next_button=Point(**data["next_button"]),
        screen=ScreenInfo(**data["screen"]),
        version=version,
        created_at=data.get("created_at", ""),
        max_score=float(data.get("max_score", 0.0)),
        notes=data.get("notes", ""),
    )


def list_profiles(profiles_dir: Path) -> list[str]:
    if not profiles_dir.exists():
        return []
    return sorted(p.stem for p in profiles_dir.glob("*.json") if p.is_file())
