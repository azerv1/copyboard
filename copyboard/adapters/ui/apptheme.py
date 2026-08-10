"""Apply a light/dark/glass/mono colour theme to the Qt application.

Uses the Fusion style plus an explicit :class:`QPalette` so the look is identical on every platform
(Windows, Linux, macOS). ``Theme.SYSTEM`` leaves Qt's native palette untouched. ``Theme.GLASS``
additionally sets ``WA_TranslucentBackground`` on the viewer window and applies an RGBA stylesheet
so the desktop shows through the window background. ``Theme.MONO`` is a flat, fully desaturated
grey theme with no accent hue. A :class:`ThemeController` keeps the current choice so the tray can
flip it live.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from copyboard.config import Theme

_FUSION_STYLE = "Fusion"

# Glass theme stylesheet applied to the viewer window.
#
# The illusion rests on three layers:
#   1. Window gradient — a blue-white glint at the very top rim that transitions into a frosted-
#      white body, making the window visible even when the list is empty.
#   2. Directional borders — bright on top/left (light source), dim on right/bottom (shadow side).
#   3. Row tiles — each ClippingWidget uses a more opaque frosted gradient so it floats above the
#      window body with its own bright top-edge highlight.
_GLASS_STYLESHEET = (
    "MainWindow {"
    "  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
    "    stop:0.000 rgba(160, 200, 255, 100),"  # sky-blue glint — top rim in full light
    "    stop:0.040 rgba(100, 145, 235,  55),"  # glow fades
    "    stop:0.085 rgba(255, 255, 255,  28),"  # transitions to frosted-white body
    "    stop:0.500 rgba(255, 255, 255,  18),"  # mid-body
    "    stop:1.000 rgba(255, 255, 255,  10));"  # slight lift toward the bottom (reflected table)
    "  border-top:    1px solid rgba(200, 225, 255, 160);"  # lit rim
    "  border-left:   1px solid rgba(150, 185, 255,  90);"
    "  border-right:  1px solid rgba( 80, 115, 210,  60);"
    "  border-bottom: 1px solid rgba( 55,  85, 185,  55);"
    "  border-radius: 7px;"
    "}"
    "QScrollArea { background: transparent; border: none; }"
    "QScrollArea > QWidget > QWidget { background: transparent; }"
    # Row tiles — more opaque than the window body so they visibly float above it.
    "ClippingWidget {"
    "  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
    "    stop:0.0 rgba(255, 255, 255, 42),"
    "    stop:0.4 rgba(255, 255, 255, 22),"
    "    stop:1.0 rgba(255, 255, 255, 10));"
    "  border-top:    1px solid rgba(255, 255, 255, 70);"  # top highlight — catches light
    "  border-left:   1px solid rgba(255, 255, 255, 35);"
    "  border-right:  1px solid rgba(0,   0,   0,   20);"
    "  border-bottom: 1px solid rgba(0,   0,   0,   28);"
    "  border-radius: 4px;"
    "  margin: 1px 2px;"
    "}"
)

# The viewer marks whichever clipping is currently on the system clipboard. DARK and LIGHT carry no
# stylesheet of their own, so this rule is all they get; GLASS and MONO restate it in their own
# palette below.
_CURRENT_CLIPPING_STYLESHEET = (
    "ClippingWidget#currentClipboardClipping {"
    "  border: 2px solid rgba(90, 150, 240, 255);"
    "  border-radius: 3px;"
    "}"
)

# Monochrome theme — flat greys only, no accent hue and no gradients. Unlike DARK/LIGHT this gives
# each card a visible surface and border, so a card is no longer the same colour as the empty space
# around it.
_MONO_STYLESHEET = (
    "MainWindow { background: #0d0d0d; }"
    "QScrollArea { background: transparent; border: none; }"
    "QScrollArea > QWidget > QWidget { background: transparent; }"
    "ClippingWidget {"
    "  background: #161616;"
    "  border: 1px solid #2a2a2a;"
    "  border-radius: 4px;"
    "}"
    "ClippingWidget:hover { background: #1f1f1f; border: 1px solid #3a3a3a; }"
    "ClippingWidget#currentClipboardClipping {"
    "  background: #1f1f1f;"
    "  border: 1px solid #2a2a2a;"
    "  border-left: 3px solid #f0f0f0;"
    "}"
    "QLabel { background: transparent; color: #e0e0e0; }"
    "QLabel#clippingTimestamp { color: #7a7a7a; font-size: 11px; }"
    "QPushButton {"
    "  background: #1f1f1f;"
    "  border: 1px solid #2a2a2a;"
    "  border-radius: 3px;"
    "  color: #e0e0e0;"
    "  padding: 3px 10px;"
    "}"
    "QPushButton:hover { background: #2a2a2a; }"
    "QPushButton:checked { background: #3a3a3a; border: 1px solid #4a4a4a; }"
    "QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }"
    "QScrollBar::handle:vertical { background: #3a3a3a; border-radius: 4px; min-height: 24px; }"
    "QScrollBar::handle:vertical:hover { background: #4a4a4a; }"
    "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
    "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
)

_THEME_CYCLE: dict[Theme, Theme] = {
    Theme.DARK: Theme.LIGHT,
    Theme.LIGHT: Theme.GLASS,
    Theme.GLASS: Theme.MONO,
    Theme.MONO: Theme.DARK,
}


def next_theme(current: Theme) -> Theme:
    """The theme a toggle switches to; ``SYSTEM`` resolves toward dark first."""
    return _THEME_CYCLE.get(current, Theme.DARK)


def apply_theme(app: QApplication, theme: Theme) -> None:
    """Switch the whole application colour palette to ``theme``; a no-op for ``Theme.SYSTEM``."""
    if theme is Theme.SYSTEM:
        return
    app.setStyle(_FUSION_STYLE)
    if theme is Theme.LIGHT:
        app.setPalette(app.style().standardPalette())
    elif theme is Theme.MONO:
        app.setPalette(_mono_palette())
    else:
        # DARK and GLASS share the same dark palette; GLASS adds window-level transparency.
        app.setPalette(_dark_palette())


def apply_window_theme(window: QWidget, theme: Theme) -> None:
    """Apply ``theme``'s window-level stylesheet and translucency to the viewer window.

    This is the single owner of ``window.setStyleSheet``. ``GLASS`` additionally sets
    ``WA_TranslucentBackground`` so the compositor can show what's beneath the window, and its RGBA
    stylesheet draws a semi-opaque tint instead of a solid fill; every other theme clears that
    attribute to restore normal opaque rendering.

    Note: on X11 without a compositor the transparency will not show through — the window will
    simply look darker than normal because the attribute is set but not composited.
    """
    is_glass = theme is Theme.GLASS
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, is_glass)
    window.setStyleSheet(_build_window_stylesheet(theme))


def _build_window_stylesheet(theme: Theme) -> str:
    if theme is Theme.GLASS:
        return _GLASS_STYLESHEET + _CURRENT_CLIPPING_STYLESHEET
    if theme is Theme.MONO:
        return _MONO_STYLESHEET
    return _CURRENT_CLIPPING_STYLESHEET


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


def _mono_palette() -> QPalette:
    """A fully desaturated dark palette — every colour is a pure grey (zero saturation)."""
    window = QColor(13, 13, 13)
    base = QColor(22, 22, 22)
    surface = QColor(31, 31, 31)
    text = QColor(224, 224, 224)
    disabled = QColor(122, 122, 122)
    highlight = QColor(58, 58, 58)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, surface)
    palette.setColor(QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, text)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
    # Left at Qt's defaults these two stay coloured — LinkVisited magenta, and Accent the blue
    # Fusion paints focus rings and checkboxes with, which would defeat the whole theme.
    palette.setColor(QPalette.ColorRole.LinkVisited, disabled)
    palette.setColor(QPalette.ColorRole.Accent, highlight)
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    return palette


class ThemeController:
    """Holds the active theme and re-applies it to the application when toggled.

    If a ``window`` is provided, each change also swaps that window's theme stylesheet and, for
    ``Theme.GLASS``, its translucent-background effect.
    """

    def __init__(
        self,
        app: QApplication,
        initial_theme: Theme,
        window: QWidget | None = None,
    ) -> None:
        self._app = app
        self._theme = initial_theme
        self._window = window
        apply_theme(app, initial_theme)
        if window is not None:
            apply_window_theme(window, initial_theme)

    @property
    def theme(self) -> Theme:
        return self._theme

    def toggle(self) -> None:
        self._theme = next_theme(self._theme)
        apply_theme(self._app, self._theme)
        if self._window is not None:
            apply_window_theme(self._window, self._theme)
