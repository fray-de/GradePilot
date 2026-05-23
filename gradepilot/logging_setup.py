"""Logging setup with a redaction filter to prevent leaking API keys."""
from __future__ import annotations

import logging
import logging.handlers
import re
from pathlib import Path

from .config import AppConfig

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]+"),
    re.compile(r"(?i)(api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]+['\"]?"),
    re.compile(r"(?i)(authorization)\s*:\s*[^\s,}]+"),
]


class RedactingFilter(logging.Filter):
    """Replace anything that looks like an API key or bearer token with ***."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        redacted = msg
        for pat in _SECRET_PATTERNS:
            redacted = pat.sub("***", redacted)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True


def setup_logging(cfg: AppConfig) -> logging.Logger:
    cfg.paths.log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    redactor = RedactingFilter()

    console = logging.StreamHandler()
    console.setLevel(cfg.logging.console_level.upper())
    console.setFormatter(fmt)
    console.addFilter(redactor)
    root.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        cfg.paths.log_path,
        maxBytes=cfg.logging.file_max_bytes,
        backupCount=cfg.logging.file_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(cfg.logging.file_level.upper())
    file_handler.setFormatter(fmt)
    file_handler.addFilter(redactor)
    root.addHandler(file_handler)

    logging.getLogger("gradepilot").debug("logging initialized; file=%s", cfg.paths.log_path)
    return logging.getLogger("gradepilot")
