"""``build_drag_mime_data`` maps a clipping payload to the right Qt drag representation.

Runs headless on the offscreen platform. Text payloads become plain text; image payloads are offered
both as a file URL and as decoded bitmap image data.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from copyboard.adapters.qt.clippingdragdata import build_drag_mime_data
from copyboard.domain.content import ClipboardPayload


def test_text_payload_becomes_plain_text() -> None:
    mime_data = build_drag_mime_data(ClipboardPayload(text="git status"))

    assert mime_data.hasText()
    assert mime_data.text() == "git status"
    assert not mime_data.hasImage()
    assert not mime_data.hasUrls()


def test_image_payload_offers_both_file_url_and_bitmap(
    qt_app: QApplication, tmp_path: Path
) -> None:
    image_file = tmp_path / "clip.png"
    source_image = QImage(4, 3, QImage.Format.Format_RGB32)
    source_image.fill(QColor("red"))
    assert source_image.save(str(image_file))

    mime_data = build_drag_mime_data(ClipboardPayload(image_path=image_file))

    assert mime_data.hasUrls()
    assert Path(mime_data.urls()[0].toLocalFile()) == image_file
    assert mime_data.hasImage()
    assert not QImage(mime_data.imageData()).isNull()


def test_empty_payload_carries_nothing() -> None:
    mime_data = build_drag_mime_data(ClipboardPayload())

    assert not mime_data.hasText()
    assert not mime_data.hasImage()
    assert not mime_data.hasUrls()
