"""``build_drag_mime_data`` maps a clipping payload to the right Qt drag representation.

Text payloads become plain text; image payloads become a single file URL, so a drop target inserts
the clipping exactly once.
"""

from __future__ import annotations

from pathlib import Path

from copyboard.adapters.qt.clippingdragdata import build_drag_mime_data
from copyboard.domain.content import ClipboardPayload


def test_text_payload_becomes_plain_text() -> None:
    mime_data = build_drag_mime_data(ClipboardPayload(text="git status"))

    assert mime_data.hasText()
    assert mime_data.text() == "git status"
    assert not mime_data.hasImage()
    assert not mime_data.hasUrls()


def test_image_payload_becomes_a_single_file_url(tmp_path: Path) -> None:
    image_file = tmp_path / "clip.png"

    mime_data = build_drag_mime_data(ClipboardPayload(image_path=image_file))

    assert mime_data.hasUrls()
    assert Path(mime_data.urls()[0].toLocalFile()) == image_file
    # No bitmap representation: that's what made rich targets paste the image twice. (Qt still
    # synthesises text/plain from the URL, but a drop target picks one format, so it inserts once.)
    assert not mime_data.hasImage()


def test_empty_payload_carries_nothing() -> None:
    mime_data = build_drag_mime_data(ClipboardPayload())

    assert not mime_data.hasText()
    assert not mime_data.hasImage()
    assert not mime_data.hasUrls()
