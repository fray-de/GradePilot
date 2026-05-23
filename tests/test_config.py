from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from gradepilot.config import ConfigError, load_config


MINIMAL = {
    "llm": {
        "base_url": "https://example.com/v1",
        "model": "gpt-4o-mini",
        "api_key_env": "TEST_LLM_KEY",
    },
    "ocr": {"engine": "vlm"},
    "automation": {"dry_run": True},
    "session": {"mode": "trial", "require_confirmation": "always"},
    "paths": {"data_dir": "data", "log_dir": "data/logs", "crops_dir": "data/crops", "profiles_dir": "profiles"},
}


def _write_yaml(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_load_minimal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_LLM_KEY", "sk-secret-abc")
    cfg_path = _write_yaml(tmp_path, MINIMAL)
    cfg = load_config(cfg_path)
    assert cfg.llm.base_url == "https://example.com/v1"
    assert cfg.llm.model == "gpt-4o-mini"
    assert cfg.llm.api_key == "sk-secret-abc"
    assert cfg.ocr.engine == "vlm"
    assert cfg.session.mode == "trial"
    assert cfg.paths.data_dir.is_absolute()


def test_redacted_masks_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_LLM_KEY", "sk-secret-abc")
    cfg = load_config(_write_yaml(tmp_path, MINIMAL))
    out = cfg.redacted()
    assert out["llm"]["api_key"] == "***"
    assert "sk-secret-abc" not in str(out)


def test_missing_llm_block(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad = dict(MINIMAL)
    bad.pop("llm")
    with pytest.raises(ConfigError):
        load_config(_write_yaml(tmp_path, bad))


def test_bad_engine_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad = {**MINIMAL, "ocr": {"engine": "tesseract"}}
    with pytest.raises(ConfigError):
        load_config(_write_yaml(tmp_path, bad))


def test_bad_mode_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad = {**MINIMAL, "session": {"mode": "ludicrous", "require_confirmation": "always"}}
    with pytest.raises(ConfigError):
        load_config(_write_yaml(tmp_path, bad))


def test_missing_key_envvar_is_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TEST_LLM_KEY", raising=False)
    cfg = load_config(_write_yaml(tmp_path, MINIMAL))
    assert cfg.llm.api_key == ""
