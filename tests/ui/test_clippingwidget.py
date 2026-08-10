"""Card rendering: uniform height for every kind, and a fixed-pitch font for structured content."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QLabel

from copyboard.adapters.ui.clippingwidget import ClippingWidget
from copyboard.domain.clipping import (
    Clipping,
    ImageClipping,
    JsonClipping,
    TextClipping,
)

_MOMENT = datetime(2026, 1, 1, 12, 0, 0)
# Never written to disk, so the widget takes its text-fallback path instead of loading a pixmap.
_MISSING_IMAGE_PATH = Path("/nonexistent/shot.png")


def _build_card(clipping: Clipping) -> ClippingWidget:
    return ClippingWidget(clipping, lambda _id: None, lambda _id: None)


def _find_preview_label(card: ClippingWidget) -> QLabel:
    # The content column is [timestamp, preview]; the preview is the second label.
    return card.findChildren(QLabel)[1]


def _build_text_card() -> ClippingWidget:
    return _build_card(TextClipping(created_at=_MOMENT, size_bytes=5, text="hello"))


def _build_json_card() -> ClippingWidget:
    payload = '{"a": 1}'
    return _build_card(JsonClipping(created_at=_MOMENT, size_bytes=len(payload), text=payload))


def _build_image_card() -> ClippingWidget:
    return _build_card(
        ImageClipping(
            created_at=_MOMENT, size_bytes=10, path=_MISSING_IMAGE_PATH, image_format="png"
        )
    )


def test_json_preview_asks_for_the_platform_fixed_pitch_font(qt_app: QApplication) -> None:
    card = _build_json_card()
    expected = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
    # Asserting on the requested family rather than QFontInfo.fixedPitch(): the offscreen platform
    # used by the test suite ships no fonts, so Qt cannot resolve the request to a real face.
    assert _find_preview_label(card).font().family() == expected


def test_plain_text_preview_keeps_the_proportional_ui_font(qt_app: QApplication) -> None:
    card = _build_text_card()
    assert _find_preview_label(card).font().family() == qt_app.font().family()


def test_every_kind_of_card_has_the_same_height(qt_app: QApplication) -> None:
    # Uniform card heights are what keep the grid rows aligned instead of ragged.
    heights = {
        card.height() for card in (_build_text_card(), _build_json_card(), _build_image_card())
    }
    assert len(heights) == 1


def test_preview_shows_multiple_lines_of_the_original_text(qt_app: QApplication) -> None:
    text = "alpha\nbeta\ngamma"
    card = _build_card(TextClipping(created_at=_MOMENT, size_bytes=15, text=text))
    assert _find_preview_label(card).text() == text


def test_card_tooltip_carries_a_summary_of_the_content(qt_app: QApplication) -> None:
    card = _build_card(TextClipping(created_at=_MOMENT, size_bytes=200, text="z" * 200))
    assert card.toolTip().endswith("…")
