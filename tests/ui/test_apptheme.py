"""Theme selection: the palettes look the part, and toggling cycles dark → light → glass → mono."""

from __future__ import annotations

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from copyboard.adapters.ui.apptheme import (
    ThemeController,
    _dark_palette,
    _mono_palette,
    next_theme,
)
from copyboard.config import Theme

_ALL_COLOUR_ROLES = [role for role in QPalette.ColorRole if role != QPalette.ColorRole.NColorRoles]


def test_dark_palette_uses_a_dark_window_colour(qt_app: QApplication) -> None:
    palette = _dark_palette()
    assert palette.color(QPalette.ColorRole.Window).lightness() < 128


def test_mono_palette_uses_a_dark_window_colour(qt_app: QApplication) -> None:
    palette = _mono_palette()
    assert palette.color(QPalette.ColorRole.Window).lightness() < 128


def test_mono_palette_is_fully_desaturated(qt_app: QApplication) -> None:
    palette = _mono_palette()
    # "Monochrome" is the whole point of this theme: no role may carry a hue.
    assert all(palette.color(role).saturation() == 0 for role in _ALL_COLOUR_ROLES)


def test_next_theme_cycles_dark_light_glass_mono() -> None:
    assert next_theme(Theme.DARK) is Theme.LIGHT
    assert next_theme(Theme.LIGHT) is Theme.GLASS
    assert next_theme(Theme.GLASS) is Theme.MONO
    assert next_theme(Theme.MONO) is Theme.DARK
    assert next_theme(Theme.SYSTEM) is Theme.DARK


def test_controller_cycles_through_all_non_system_themes(qt_app: QApplication) -> None:
    controller = ThemeController(qt_app, Theme.DARK)
    assert controller.theme is Theme.DARK

    controller.toggle()
    assert controller.theme is Theme.LIGHT

    controller.toggle()
    assert controller.theme is Theme.GLASS

    controller.toggle()
    assert controller.theme is Theme.MONO

    controller.toggle()
    assert controller.theme is Theme.DARK
