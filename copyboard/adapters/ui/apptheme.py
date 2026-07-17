"""Apply a light/dark colour theme to the Qt application.

Uses the Fusion style plus an explicit :class:`QPalette` so the look is identical on every platform
(Windows, Linux, macOS). ``Theme.SYSTEM`` leaves Qt's native palette untouched. A
:class:`ThemeController` keeps the current choice so the tray can flip it live.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from copyboard.config import Theme

_FUSION_STYLE = "Fusion"


def next_theme(current: Theme) -> Theme:
    """The theme a light/dark toggle switches to (``SYSTEM`` resolves toward dark first)."""
    return Theme.LIGHT if current is Theme.DARK else Theme.DARK


def apply_theme(app: QApplication, theme: Theme) -> None:
    """Switch the whole application to ``theme``; a no-op for ``Theme.SYSTEM``."""
    if theme is Theme.SYSTEM:
        return
    app.setStyle(_FUSION_STYLE)
    app.setPalette(_dark_palette() if theme is Theme.DARK else app.style().standardPalette())


def _dark_palette() -> QPalette:
    window = QColor(30, 30, 30)
    base = QColor(23, 23, 23)
    text = QColor(220, 220, 220)
    disabled = QColor(120, 120, 120)
    accent = QColor(45, 108, 223)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, window)
    palette.setColor(QPalette.ColorRole.ToolTipBase, window)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, window)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 80))
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    return palette


class ThemeController:
    """Holds the active theme and re-applies it to the application when toggled."""

    def __init__(self, app: QApplication, initial_theme: Theme) -> None:
        self._app = app
        self._theme = initial_theme
        apply_theme(app, initial_theme)

    @property
    def theme(self) -> Theme:
        return self._theme

    def toggle(self) -> None:
        self._theme = next_theme(self._theme)
        apply_theme(self._app, self._theme)
