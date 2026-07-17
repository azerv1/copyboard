"""Friendly hotkey combos convert to pynput's ``<modifier>+key`` format."""

from __future__ import annotations

from copyboard.adapters.pynputhotkeybinder import to_pynput_hotkey_format


def test_converts_a_simple_combo() -> None:
    assert to_pynput_hotkey_format("ctrl+shift+h") == "<ctrl>+<shift>+h"


def test_normalizes_aliases_case_and_whitespace() -> None:
    assert to_pynput_hotkey_format("  Win + Alt + P ") == "<cmd>+<alt>+p"
