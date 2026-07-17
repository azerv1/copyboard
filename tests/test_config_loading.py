"""Loading AppConfig from config.json, with tolerant fallback to defaults."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from copyboard.config import AppConfig
from copyboard.config_loading import load_app_config_from_json


def test_missing_file_yields_defaults(tmp_path: Path) -> None:
    assert load_app_config_from_json(tmp_path / "absent.json") == AppConfig()


def test_full_config_is_loaded(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"retention": {"max_items": 5, "max_age_minutes": 10},'
        ' "hotkey": {"toggle_viewer_hotkey": "ctrl+alt+p"}}',
        encoding="utf-8",
    )

    config = load_app_config_from_json(config_path)

    assert config.retention.max_items == 5
    assert config.retention.max_age == timedelta(minutes=10)
    assert config.hotkey.toggle_viewer_hotkey == "ctrl+alt+p"


def test_partial_config_falls_back_to_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text('{"retention": {"max_items": 7}}', encoding="utf-8")

    config = load_app_config_from_json(config_path)

    assert config.retention.max_items == 7
    assert config.retention.max_age == AppConfig().retention.max_age
    assert config.hotkey == AppConfig().hotkey
