"""GradePilot CLI entry. M1 supports: --version / --check-config / --init-db."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, ensure_dirs, load_config
from .logging_setup import setup_logging
from .session.store import init_db


def _print_config(redacted: dict) -> None:
    print(json.dumps(redacted, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gradepilot", description="Human-in-the-loop grading assistant.")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--config", type=Path, default=None, help="path to config.yaml (default: ./config.yaml)")
    parser.add_argument("--check-config", action="store_true", help="load + validate config and print (key masked)")
    parser.add_argument("--init-db", action="store_true", help="create SQLite schema if missing")
    args = parser.parse_args(argv)

    if args.version:
        print(f"gradepilot {__version__}")
        return 0

    if not (args.check_config or args.init_db):
        parser.print_help()
        return 0

    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    ensure_dirs(cfg)
    log = setup_logging(cfg)
    log.info("gradepilot %s starting (config=%s)", __version__, args.config or "default")

    if args.check_config:
        if not cfg.llm.api_key:
            log.warning(
                "env var %s is unset; LLM calls in later milestones will fail until you set it.",
                cfg.llm.api_key_env,
            )
        _print_config(cfg.redacted())
        return 0

    if args.init_db:
        init_db(cfg.paths.db_path)
        log.info("initialized SQLite db at %s", cfg.paths.db_path)
        print(f"db ready: {cfg.paths.db_path}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
