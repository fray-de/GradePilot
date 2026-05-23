"""GradePilot CLI entry.

M1: --version / --check-config / --init-db
M2: --define-profile / --list-profiles / --show-profile
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .config import AppConfig, ConfigError, ensure_dirs, load_config
from .logging_setup import setup_logging
from .profiles import list_profiles, load_profile
from .session.store import init_db


def _print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def _do_define_profile(cfg: AppConfig, name: str, log) -> int:
    # Lazy import — pulls in PyQt6 only when the user actually defines a profile.
    from .ui.overlay import UserCancelled
    from .ui.profile_capture import capture_profile

    try:
        profile = capture_profile(name, cfg.paths.profiles_dir)
    except UserCancelled as e:
        log.warning("profile capture cancelled: %s", e)
        print(f"cancelled: {e}", file=sys.stderr)
        return 130
    log.info("profile '%s' saved", profile.name)
    return 0


def _do_list_profiles(cfg: AppConfig) -> int:
    names = list_profiles(cfg.paths.profiles_dir)
    if not names:
        print(f"(no profiles in {cfg.paths.profiles_dir})")
        return 0
    for n in names:
        print(n)
    return 0


def _do_show_profile(cfg: AppConfig, name: str) -> int:
    try:
        profile = load_profile(cfg.paths.profiles_dir, name)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    _print_json(asdict(profile))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gradepilot",
        description="Human-in-the-loop grading assistant.",
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="path to config.yaml (default: ./config.yaml or next to the exe)",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="load + validate config and print (key masked)",
    )
    parser.add_argument(
        "--init-db", action="store_true", help="create SQLite schema if missing"
    )
    parser.add_argument(
        "--define-profile",
        metavar="NAME",
        default=None,
        help="interactively capture screen regions and save as profiles/NAME.json",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="list saved profile names",
    )
    parser.add_argument(
        "--show-profile",
        metavar="NAME",
        default=None,
        help="print the JSON of a saved profile",
    )
    args = parser.parse_args(argv)

    if args.version:
        print(f"gradepilot {__version__}")
        return 0

    needs_config = (
        args.check_config
        or args.init_db
        or args.define_profile
        or args.list_profiles
        or args.show_profile
    )
    if not needs_config:
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
        _print_json(cfg.redacted())
        return 0

    if args.init_db:
        init_db(cfg.paths.db_path)
        log.info("initialized SQLite db at %s", cfg.paths.db_path)
        print(f"db ready: {cfg.paths.db_path}")
        return 0

    if args.define_profile:
        return _do_define_profile(cfg, args.define_profile, log)

    if args.list_profiles:
        return _do_list_profiles(cfg)

    if args.show_profile:
        return _do_show_profile(cfg, args.show_profile)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
