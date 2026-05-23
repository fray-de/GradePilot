"""Load and validate config.yaml + .env into typed dataclasses."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigError(ValueError):
    pass


def _frozen() -> bool:
    """True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    """Where to look for config.yaml / .env / data/ at runtime.

    Frozen builds anchor next to the exe (the user's stable install dir).
    Source runs anchor at the current working directory.
    """
    if _frozen():
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def _bundled_resource(name: str) -> Path | None:
    """Path to a file bundled via PyInstaller --add-data, if any."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = Path(base) / name
        if p.exists():
            return p
    return None


@dataclass
class LlmConfig:
    base_url: str
    model: str
    api_key_env: str
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_seconds: int = 60
    api_key: str = field(default="", repr=False)


@dataclass
class VlmConfig:
    override_model: str | None = None


@dataclass
class OcrConfig:
    engine: str = "vlm"
    vlm: VlmConfig = field(default_factory=VlmConfig)


@dataclass
class AutomationConfig:
    pre_click_delay_ms: int = 800
    stop_hotkey: str = "esc"
    dry_run: bool = True
    pyautogui_failsafe: bool = True


@dataclass
class SessionConfig:
    mode: str = "trial"
    trial_paper_limit: int = 100
    require_confirmation: str = "always"
    auto_confirm_min_confidence: float = 0.9


@dataclass
class PathsConfig:
    data_dir: Path
    log_dir: Path
    crops_dir: Path
    profiles_dir: Path
    db_filename: str = "gradepilot.db"
    log_filename: str = "gradepilot.log"

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_filename

    @property
    def log_path(self) -> Path:
        return self.log_dir / self.log_filename


@dataclass
class LoggingConfig:
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    file_max_bytes: int = 5 * 1024 * 1024
    file_backup_count: int = 3


@dataclass
class AppConfig:
    llm: LlmConfig
    ocr: OcrConfig
    automation: AutomationConfig
    session: SessionConfig
    paths: PathsConfig
    logging: LoggingConfig
    project_root: Path

    def redacted(self) -> dict[str, Any]:
        """Return a dict copy safe for printing (API key masked)."""
        return {
            "llm": {
                "base_url": self.llm.base_url,
                "model": self.llm.model,
                "api_key_env": self.llm.api_key_env,
                "api_key": "***" if self.llm.api_key else "(unset)",
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout_seconds": self.llm.timeout_seconds,
            },
            "ocr": {
                "engine": self.ocr.engine,
                "vlm": {"override_model": self.ocr.vlm.override_model},
            },
            "automation": vars(self.automation),
            "session": vars(self.session),
            "paths": {
                "data_dir": str(self.paths.data_dir),
                "log_dir": str(self.paths.log_dir),
                "crops_dir": str(self.paths.crops_dir),
                "profiles_dir": str(self.paths.profiles_dir),
                "db_path": str(self.paths.db_path),
                "log_path": str(self.paths.log_path),
            },
            "logging": vars(self.logging),
            "project_root": str(self.project_root),
        }


def _resolve(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (root / p).resolve()


def _require(d: dict, key: str, ctx: str) -> Any:
    if key not in d:
        raise ConfigError(f"missing required key '{ctx}.{key}' in config")
    return d[key]


def load_config(
    config_path: Path | str | None = None,
    env_path: Path | str | None = None,
) -> AppConfig:
    """Load config.yaml (defaults to <app_root>/config.yaml) and merge .env.

    When running as a frozen exe and no config.yaml is found next to the exe,
    drop the bundled config.example.yaml next to the exe and raise a friendly
    error pointing the user there.
    """
    project_root = app_root()

    if config_path is None:
        candidate = project_root / "config.yaml"
        if not candidate.exists():
            example = project_root / "config.example.yaml"
            if _frozen():
                # First-run UX for the exe: drop the bundled example next to the
                # exe and tell the user what to do, instead of silently loading
                # the example (which has no API key).
                if not example.exists():
                    bundled = _bundled_resource("config.example.yaml")
                    if bundled is not None:
                        example.write_bytes(bundled.read_bytes())
                raise ConfigError(
                    f"no config.yaml found next to the exe.\n"
                    f"  exe dir : {project_root}\n"
                    f"  example : {example} (wrote it for you)\n"
                    f"  next    : copy it to config.yaml, edit it,\n"
                    f"            and create a .env with your API key (e.g. LLM_API_KEY=sk-...)"
                )
            # Source run: keep the historical fallback so dev workflow works.
            candidate = example
        config_path = candidate
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise ConfigError(f"config file not found: {config_path}")

    if env_path is None:
        env_path = project_root / ".env"
    if Path(env_path).exists():
        load_dotenv(env_path)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    llm_raw = _require(raw, "llm", "")
    llm = LlmConfig(
        base_url=_require(llm_raw, "base_url", "llm"),
        model=_require(llm_raw, "model", "llm"),
        api_key_env=_require(llm_raw, "api_key_env", "llm"),
        temperature=float(llm_raw.get("temperature", 0.0)),
        max_tokens=int(llm_raw.get("max_tokens", 1024)),
        timeout_seconds=int(llm_raw.get("timeout_seconds", 60)),
    )
    llm.api_key = os.environ.get(llm.api_key_env, "")

    ocr_raw = raw.get("ocr") or {}
    ocr = OcrConfig(
        engine=ocr_raw.get("engine", "vlm"),
        vlm=VlmConfig(override_model=(ocr_raw.get("vlm") or {}).get("override_model")),
    )
    if ocr.engine not in {"vlm", "paddle"}:
        raise ConfigError(f"ocr.engine must be 'vlm' or 'paddle', got {ocr.engine!r}")

    auto_raw = raw.get("automation") or {}
    automation = AutomationConfig(
        pre_click_delay_ms=int(auto_raw.get("pre_click_delay_ms", 800)),
        stop_hotkey=str(auto_raw.get("stop_hotkey", "esc")),
        dry_run=bool(auto_raw.get("dry_run", True)),
        pyautogui_failsafe=bool(auto_raw.get("pyautogui_failsafe", True)),
    )

    sess_raw = raw.get("session") or {}
    session = SessionConfig(
        mode=sess_raw.get("mode", "trial"),
        trial_paper_limit=int(sess_raw.get("trial_paper_limit", 100)),
        require_confirmation=sess_raw.get("require_confirmation", "always"),
        auto_confirm_min_confidence=float(sess_raw.get("auto_confirm_min_confidence", 0.9)),
    )
    if session.mode not in {"trial", "batch"}:
        raise ConfigError(f"session.mode must be 'trial' or 'batch', got {session.mode!r}")
    if session.require_confirmation not in {"always", "threshold", "never"}:
        raise ConfigError(
            f"session.require_confirmation must be 'always'|'threshold'|'never', got {session.require_confirmation!r}"
        )

    paths_raw = raw.get("paths") or {}
    paths = PathsConfig(
        data_dir=_resolve(project_root, paths_raw.get("data_dir", "data")),
        log_dir=_resolve(project_root, paths_raw.get("log_dir", "data/logs")),
        crops_dir=_resolve(project_root, paths_raw.get("crops_dir", "data/crops")),
        profiles_dir=_resolve(project_root, paths_raw.get("profiles_dir", "profiles")),
        db_filename=paths_raw.get("db_filename", "gradepilot.db"),
        log_filename=paths_raw.get("log_filename", "gradepilot.log"),
    )

    log_raw = raw.get("logging") or {}
    logging_cfg = LoggingConfig(
        console_level=log_raw.get("console_level", "INFO"),
        file_level=log_raw.get("file_level", "DEBUG"),
        file_max_bytes=int(log_raw.get("file_max_bytes", 5 * 1024 * 1024)),
        file_backup_count=int(log_raw.get("file_backup_count", 3)),
    )

    return AppConfig(
        llm=llm,
        ocr=ocr,
        automation=automation,
        session=session,
        paths=paths,
        logging=logging_cfg,
        project_root=project_root,
    )


def ensure_dirs(cfg: AppConfig) -> None:
    for p in (cfg.paths.data_dir, cfg.paths.log_dir, cfg.paths.crops_dir, cfg.paths.profiles_dir):
        p.mkdir(parents=True, exist_ok=True)
